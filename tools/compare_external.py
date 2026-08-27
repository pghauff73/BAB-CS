from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from babcs import BoundedAdamsBashforthIntegrator, Simulator
from babcs.io import load_case, summary_data
from tests.support.metrics import error_metrics, interpolate_trace
from tools.compare_methods import environment_metadata, source_metadata


class ExternalComparisonError(RuntimeError):
    pass


def generate_ngspice_netlist(case_data: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    elements = case_data.get("elements")
    simulation = case_data.get("simulation")
    if not isinstance(elements, list) or not isinstance(simulation, dict):
        raise ExternalComparisonError("case requires elements and simulation objects")
    stop_time = float(simulation["stop_time"])
    nominal_step = float(simulation["nominal_step"])
    start_time = float(simulation.get("start_time", 0.0))
    if start_time != 0.0:
        raise ExternalComparisonError("external adapter currently requires start_time = 0")

    lines = ["BAB-CS external comparison", ".options numdgt=15"]
    model_lines: list[str] = []
    capacitor_state_expressions: list[str] = []
    capacitor_state_names: list[str] = []
    inductor_state_expressions: list[str] = []
    inductor_state_names: list[str] = []

    for raw_element in elements:
        if not isinstance(raw_element, dict):
            raise ExternalComparisonError("each element must be an object")
        kind = str(raw_element["type"]).lower()
        name = str(raw_element["name"])
        positive = _node(raw_element["positive"])
        negative = _node(raw_element["negative"])
        if kind in {"r", "resistor"}:
            lines.append(f"R{name} {positive} {negative} {_number(raw_element['resistance'])}")
        elif kind in {"c", "capacitor"}:
            initial = float(raw_element.get("initial_voltage", 0.0))
            lines.append(
                f"C{name} {positive} {negative} {_number(raw_element['capacitance'])} IC={_number(initial)}"
            )
            if negative == "0":
                capacitor_state_expressions.append(f"v({positive})")
            elif positive == "0":
                capacitor_state_expressions.append(f"-v({negative})")
            else:
                capacitor_state_expressions.append(f"v({positive})-v({negative})")
            capacitor_state_names.append(f"v({name})")
        elif kind in {"l", "inductor"}:
            initial = float(raw_element.get("initial_current", 0.0))
            lines.append(
                f"L{name} {positive} {negative} {_number(raw_element['inductance'])} IC={_number(initial)}"
            )
            inductor_state_expressions.append(f"i(L{name})")
            inductor_state_names.append(f"i({name})")
        elif kind in {"v", "voltage_source"}:
            lines.append(
                f"V{name} {positive} {negative} {_waveform(raw_element['waveform'], stop_time)}"
            )
        elif kind in {"i", "current_source"}:
            lines.append(
                f"I{name} {positive} {negative} {_waveform(raw_element['waveform'], stop_time)}"
            )
        elif kind in {"d", "diode"}:
            saturation_current = float(raw_element.get("saturation_current", 1.0e-12))
            thermal_voltage = float(raw_element.get("thermal_voltage", 0.02585))
            if not math.isfinite(saturation_current) or saturation_current <= 0.0:
                raise ExternalComparisonError(f"{name}: saturation_current must be positive and finite")
            if not math.isfinite(thermal_voltage) or thermal_voltage <= 0.0:
                raise ExternalComparisonError(f"{name}: thermal_voltage must be positive and finite")
            model_name = f"BABD_{name}"
            ideality = thermal_voltage / 0.02585
            lines.append(f"D{name} {positive} {negative} {model_name}")
            model_lines.append(
                f".model {model_name} D(Is={_number(saturation_current)} N={_number(ideality)})"
            )
        elif kind in {"s", "switch"}:
            control_node = f"bab_ctrl_{name.lower()}"
            model_name = f"BABSW_{name}"
            lines.append(
                f"VCTRL_{name} {control_node} 0 {_waveform(raw_element['control'], stop_time)}"
            )
            lines.append(f"S{name} {positive} {negative} {control_node} 0 {model_name}")
            model_lines.append(
                f".model {model_name} SW(Ron={_number(raw_element.get('on_resistance', 1.0e-3))} "
                f"Roff={_number(raw_element.get('off_resistance', 1.0e9))} "
                f"Vt={_number(raw_element.get('threshold', 0.5))} Vh=0)"
            )
        else:
            raise ExternalComparisonError(f"unsupported external element type: {kind}")

    state_expressions = capacitor_state_expressions + inductor_state_expressions
    state_names = capacitor_state_names + inductor_state_names
    if not state_expressions:
        raise ExternalComparisonError("external comparison requires at least one dynamic state")
    vector_names = [f"bab_state_{index}" for index in range(len(state_expressions))]
    lines.extend(model_lines)
    lines.extend(
        [
            ".control",
            "set wr_singlescale",
            "set wr_vecnames",
            f"tran {_number(nominal_step)} {_number(stop_time)} 0 {_number(nominal_step)} uic",
            *(
                f"let {name} = {expression}"
                for name, expression in zip(vector_names, state_expressions, strict=True)
            ),
            f"wrdata external.dat {' '.join(vector_names)}",
            "quit",
            ".endc",
            ".end",
            "",
        ]
    )
    return "\n".join(lines), tuple(state_names)


def parse_ngspice_wrdata(text: str, expected_states: int) -> tuple[tuple[float, ...], ...]:
    rows = [line.split() for line in text.splitlines() if line.strip()]
    if len(rows) < 2:
        raise ExternalComparisonError("ngspice output contains no data rows")
    header = rows[0]
    numeric_rows = rows[1:]
    expected_columns = expected_states + 1
    if len(header) != expected_columns:
        raise ExternalComparisonError(
            f"ngspice output has {len(header)} columns, expected {expected_columns}"
        )
    parsed: list[tuple[float, ...]] = []
    for row in numeric_rows:
        if len(row) != expected_columns:
            raise ExternalComparisonError("ngspice output row has an inconsistent column count")
        try:
            values = tuple(float(value) for value in row)
        except ValueError as error:
            raise ExternalComparisonError("ngspice output contains a non-numeric data row") from error
        if any(not math.isfinite(value) for value in values):
            raise ExternalComparisonError("ngspice output contains a non-finite value")
        parsed.append(values)
    if any(right[0] <= left[0] for left, right in zip(parsed, parsed[1:])):
        raise ExternalComparisonError("ngspice output times are not strictly increasing")
    return tuple(parsed)


def run_external_comparison(
    case_path: str | Path,
    *,
    executable: str = "ngspice",
    mode: str = "active",
) -> tuple[dict[str, Any], str, str, str]:
    resolved = shutil.which(executable)
    if resolved is None:
        raise ExternalComparisonError(f"external simulator executable not found: {executable}")
    input_path = Path(case_path)
    case_data = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(case_data, dict):
        raise ExternalComparisonError("external comparison input must be an object")
    netlist, state_names = generate_ngspice_netlist(case_data)

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        netlist_path = root / "case.cir"
        log_path = root / "ngspice.log"
        data_path = root / "external.dat"
        netlist_path.write_text(netlist, encoding="utf-8")
        command = [resolved, "-b", "-o", log_path.name, netlist_path.name]
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
            raise ExternalComparisonError(
                f"external simulator failed with exit code {completed.returncode}: {log.strip()}"
            )
        if not data_path.is_file():
            raise ExternalComparisonError("external simulator did not produce external.dat")
        raw_output = data_path.read_text(encoding="utf-8")
        external_log = log_path.read_text(encoding="utf-8", errors="replace")
        external_rows = parse_ngspice_wrdata(raw_output, len(state_names))
        version = _tool_version(resolved)

    circuit, simulation, config = load_case(input_path)
    if circuit.dynamic_size != len(state_names):
        raise ExternalComparisonError("external state dimension does not match BAB-CS")
    run_config = replace(config, rollout_mode=mode)
    babcs_result = Simulator(BoundedAdamsBashforthIntegrator(run_config)).run(
        circuit,
        simulation["stop_time"],
        simulation["nominal_step"],
        start_time=simulation["start_time"],
    )
    times = tuple(row[0] for row in external_rows)
    per_state = {}
    for index, state_name in enumerate(state_names):
        babcs_values = tuple(interpolate_trace(babcs_result.dynamic_trace(index), time) for time in times)
        external_values = tuple(row[index + 1] for row in external_rows)
        per_state[state_name] = error_metrics(babcs_values, external_values)

    report = {
        "schema_version": 1,
        "source": source_metadata(REPOSITORY_ROOT),
        "environment": environment_metadata(),
        "case_sha256": _sha256(input_path.read_bytes()),
        "netlist_sha256": _sha256(netlist.encode()),
        "raw_output_sha256": _sha256(raw_output.encode()),
        "external_log_sha256": _sha256(external_log.encode()),
        "external_tool": {
            "name": "ngspice",
            "version": version,
            "command": [Path(resolved).name, "-b", "-o", "ngspice.log", "case.cir"],
        },
        "state_names": state_names,
        "sample_count": len(external_rows),
        "accuracy": per_state,
        "configuration": {
            "mode": mode,
            "simulation": simulation,
            "babcs": asdict(run_config),
        },
        "babcs_summary": summary_data(babcs_result),
        "claim_boundary": (
            "This is cross-implementation evidence for the generated semantic mapping, not proof of "
            "exact physical trajectory error."
        ),
    }
    return report, netlist, raw_output, external_log


def _waveform(data: Any, stop_time: float) -> str:
    if isinstance(data, (int, float)):
        return f"DC {_number(data)}"
    if not isinstance(data, dict):
        raise ExternalComparisonError("waveform must be numeric or an object")
    kind = str(data.get("type", "constant")).lower()
    if kind == "constant":
        return f"DC {_number(data['value'])}"
    if kind == "sine":
        phase_degrees = math.degrees(float(data.get("phase_radians", 0.0)))
        return (
            f"SIN({_number(data.get('offset', 0.0))} {_number(data['amplitude'])} "
            f"{_number(data['frequency'])} {_number(data.get('delay', 0.0))} 0 "
            f"{_number(phase_degrees)})"
        )
    if kind == "pulse":
        period = float(data.get("period", 0.0))
        if period <= 0.0:
            period = max(stop_time * 2.0, float(data.get("width", 0.0)) + 1.0)
        return (
            f"PULSE({_number(data.get('low', 0.0))} {_number(data['high'])} "
            f"{_number(data.get('delay', 0.0))} {_number(data.get('rise', 0.0))} "
            f"{_number(data.get('fall', 0.0))} {_number(data['width'])} {_number(period)})"
        )
    if kind in {"pwl", "piecewise_linear"}:
        points = data.get("points")
        if not isinstance(points, list) or not points:
            raise ExternalComparisonError("piecewise-linear waveform requires points")
        values = " ".join(f"{_number(point[0])} {_number(point[1])}" for point in points)
        return f"PWL({values})"
    raise ExternalComparisonError(f"unsupported external waveform type: {kind}")


def _node(value: Any) -> str:
    node = str(value).strip()
    return "0" if node.lower() in {"0", "gnd", "ground"} else node


def _number(value: Any) -> str:
    number = float(value)
    if not math.isfinite(number):
        raise ExternalComparisonError("external netlist values must be finite")
    return format(number, ".17g")


def _tool_version(executable: str) -> str:
    completed = subprocess.run(
        [executable, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    text = (completed.stdout or completed.stderr).strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if "ngspice-" in line.lower():
            return line.strip("* ")
    for line in lines:
        candidate = line.strip("* ")
        if candidate:
            return candidate
    return "unknown"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: str | Path, content: str, *, overwrite: bool) -> None:
    output = Path(path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite external comparison evidence: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare BAB-CS with ngspice")
    parser.add_argument("case")
    parser.add_argument("--executable", default="ngspice")
    parser.add_argument("--mode", choices=("disabled", "shadow", "active"), default="active")
    parser.add_argument("--output", required=True)
    parser.add_argument("--netlist-output")
    parser.add_argument("--raw-output")
    parser.add_argument("--log-output")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    report, netlist, raw_output, external_log = run_external_comparison(
        arguments.case,
        executable=arguments.executable,
        mode=arguments.mode,
    )
    _write(
        arguments.output,
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        overwrite=arguments.overwrite,
    )
    if arguments.netlist_output:
        _write(arguments.netlist_output, netlist, overwrite=arguments.overwrite)
    if arguments.raw_output:
        _write(arguments.raw_output, raw_output, overwrite=arguments.overwrite)
    if arguments.log_output:
        _write(arguments.log_output, external_log, overwrite=arguments.overwrite)
    print(json.dumps({"output": arguments.output, "samples": report["sample_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
