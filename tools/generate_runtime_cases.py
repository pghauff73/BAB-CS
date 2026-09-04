from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from tools.compare_external import generate_ngspice_netlist
except ModuleNotFoundError:
    from compare_external import generate_ngspice_netlist

from babcs import BABCSConfig
from babcs.io import load_case


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPOSITORY_ROOT / "benchmarks" / "runtime" / "manifest.json"
DEFAULT_OUTPUT_ROOT = REPOSITORY_ROOT / "benchmarks" / "runtime" / "cases"


class RuntimeCaseGenerationError(RuntimeError):
    pass


def load_runtime_manifest(path: str | Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest_path = Path(path)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise RuntimeCaseGenerationError("runtime manifest must be a schema-version 1 object")
    families = data.get("families")
    if not isinstance(families, list) or not families:
        raise RuntimeCaseGenerationError("runtime manifest requires a non-empty families list")
    babcs_profiles = data.get("babcs_profiles")
    if not isinstance(babcs_profiles, dict) or not babcs_profiles:
        raise RuntimeCaseGenerationError(
            "runtime manifest requires named BAB-CS operating profiles"
        )
    for profile_id, profile in babcs_profiles.items():
        if not isinstance(profile_id, str) or not profile_id:
            raise RuntimeCaseGenerationError("BAB-CS profile ids must be non-empty strings")
        if not isinstance(profile, dict) or not isinstance(
            profile.get("description"), str
        ):
            raise RuntimeCaseGenerationError(
                f"{profile_id}: BAB-CS profile requires a description"
            )
        config = profile.get("config")
        if not isinstance(config, dict):
            raise RuntimeCaseGenerationError(
                f"{profile_id}: BAB-CS profile requires a config object"
            )
        try:
            validated_config = BABCSConfig(**config)
        except (TypeError, ValueError) as error:
            raise RuntimeCaseGenerationError(
                f"{profile_id}: invalid BAB-CS profile: {error}"
            ) from error
        if validated_config.rollout_mode != "active":
            raise RuntimeCaseGenerationError(
                f"{profile_id}: runtime headline profiles must use active rollout"
            )
    identifiers: set[str] = set()
    for family in families:
        if not isinstance(family, dict):
            raise RuntimeCaseGenerationError("runtime families must be objects")
        required = {
            "id",
            "sizes",
            "simulation",
            "parameters",
            "authority",
            "babcs_profile",
        }
        if not required.issubset(family):
            raise RuntimeCaseGenerationError("runtime family is missing required fields")
        family_id = str(family["id"])
        if family_id in identifiers:
            raise RuntimeCaseGenerationError(f"duplicate runtime family id: {family_id}")
        identifiers.add(family_id)
        profile_id = family["babcs_profile"]
        if not isinstance(profile_id, str) or profile_id not in babcs_profiles:
            raise RuntimeCaseGenerationError(
                f"{family_id}: unknown BAB-CS profile: {profile_id}"
            )
        sizes = family["sizes"]
        if not isinstance(sizes, list) or sizes != [1, 2, 4, 8, 16, 32, 64]:
            raise RuntimeCaseGenerationError(
                f"{family_id}: required sizes must be 1, 2, 4, 8, 16, 32, and 64"
            )
        dynamic_states_per_size = family.get("dynamic_states_per_size", 1)
        if (
            not isinstance(dynamic_states_per_size, int)
            or isinstance(dynamic_states_per_size, bool)
            or dynamic_states_per_size < 1
        ):
            raise RuntimeCaseGenerationError(
                f"{family_id}: dynamic_states_per_size must be a positive integer"
            )
    return data


def runtime_case_filename(family_id: str, size: int) -> str:
    return f"{family_id}-n{size:03d}.json"


def generate_runtime_case(
    family: dict[str, Any],
    size: int,
    babcs_profiles: dict[str, Any],
) -> dict[str, Any]:
    family_id = str(family["id"])
    parameters = dict(family["parameters"])
    simulation = dict(family["simulation"])
    if size <= 0:
        raise RuntimeCaseGenerationError("runtime case size must be positive")
    if family_id == "rc_bank":
        elements = _rc_bank(size, parameters)
    elif family_id == "coupled_rc_ring":
        elements = _coupled_rc_ring(size, parameters)
    elif family_id == "coupled_rlc_ring":
        elements = _coupled_rlc_ring(size, parameters)
    elif family_id == "rl_bank":
        elements = _rl_bank(size, parameters)
    elif family_id == "diode_rc_bank":
        elements = _diode_rc_bank(size, parameters)
    elif family_id == "switched_rc_bank":
        elements = _switched_rc_bank(size, parameters)
    else:
        raise RuntimeCaseGenerationError(f"unsupported runtime family: {family_id}")
    profile_id = str(family["babcs_profile"])
    try:
        profile = babcs_profiles[profile_id]
    except KeyError as error:
        raise RuntimeCaseGenerationError(
            f"{family_id}: unknown BAB-CS profile: {profile_id}"
        ) from error
    return {
        "linear_backend": "dense",
        "elements": elements,
        "simulation": simulation,
        "babcs": dict(profile["config"]),
        "runtime_benchmark": {
            "family_id": family_id,
            "size": size,
            "size_parameter": str(family.get("size_parameter", "channels")),
            "authority": family["authority"],
            "babcs_profile_id": profile_id,
            "babcs_profile_description": str(profile["description"]),
        }
    }


def render_runtime_case(case: dict[str, Any]) -> bytes:
    return (json.dumps(case, indent=2, allow_nan=False) + "\n").encode("utf-8")


def generate_runtime_cases(
    manifest_path: str | Path = DEFAULT_MANIFEST,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    *,
    check: bool = False,
) -> dict[str, Any]:
    manifest = load_runtime_manifest(manifest_path)
    root = Path(output_root)
    generated: dict[str, bytes] = {}
    metadata: list[dict[str, Any]] = []
    for family in manifest["families"]:
        family_id = str(family["id"])
        dynamic_states_per_size = int(family.get("dynamic_states_per_size", 1))
        for size_value in family["sizes"]:
            size = int(size_value)
            filename = runtime_case_filename(family_id, size)
            content = render_runtime_case(
                generate_runtime_case(family, size, manifest["babcs_profiles"])
            )
            generated[filename] = content
            metadata.append(
                _validate_generated_case(
                    root / filename,
                    content,
                    family_id,
                    size,
                    size * dynamic_states_per_size,
                )
            )
    if check:
        existing = {path.name for path in root.glob("*.json")}
        if existing != set(generated):
            missing = sorted(set(generated) - existing)
            extra = sorted(existing - set(generated))
            raise RuntimeCaseGenerationError(
                f"runtime case inventory drifted: missing={missing}, extra={extra}"
            )
        for filename, content in generated.items():
            if (root / filename).read_bytes() != content:
                raise RuntimeCaseGenerationError(f"runtime case is stale: {filename}")
    else:
        root.mkdir(parents=True, exist_ok=True)
        for filename, content in generated.items():
            (root / filename).write_bytes(content)
    return {"cases": len(generated), "families": len(manifest["families"]), "metadata": metadata}


def _validate_generated_case(
    path: Path,
    content: bytes,
    family_id: str,
    size: int,
    expected_dynamic_state_count: int,
) -> dict[str, Any]:
    temporary = path.with_suffix(".validation.json")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_bytes(content)
    try:
        circuit, simulation, _ = load_case(temporary)
        data = json.loads(content)
        netlist, state_names = generate_ngspice_netlist(data)
    finally:
        temporary.unlink(missing_ok=True)
    if (
        circuit.dynamic_size != expected_dynamic_state_count
        or len(state_names) != expected_dynamic_state_count
    ):
        raise RuntimeCaseGenerationError(
            f"{family_id} size {size}: dynamic state count does not match "
            f"expected count {expected_dynamic_state_count}"
        )
    return {
        "family_id": family_id,
        "size": size,
        "element_count": len(circuit.elements),
        "node_count": len(circuit.nodes),
        "dynamic_state_count": circuit.dynamic_size,
        "algebraic_unknown_count": circuit.algebraic_size,
        "declared_mna_unknowns": circuit.dynamic_size + circuit.algebraic_size,
        "stop_time": simulation["stop_time"],
        "nominal_step": simulation["nominal_step"],
        "netlist_lines": len(netlist.splitlines()),
    }


def _rc_bank(size: int, parameters: dict[str, Any]) -> list[dict[str, Any]]:
    elements = [_voltage_source(float(parameters["source_voltage"]))]
    for index in range(1, size + 1):
        output = f"out{index}"
        elements.extend(
            [
                {"type": "resistor", "name": f"R{index}", "positive": "vin", "negative": output, "resistance": float(parameters["resistance"])},
                {"type": "capacitor", "name": f"C{index}", "positive": output, "negative": "0", "capacitance": float(parameters["capacitance"]), "initial_voltage": float(parameters["initial_voltage"])}
            ]
        )
    return elements


def _coupled_rc_ring(size: int, parameters: dict[str, Any]) -> list[dict[str, Any]]:
    elements = [_voltage_source(float(parameters["source_voltage"]))]
    for index in range(1, size + 1):
        output = f"out{index}"
        if index == 1:
            elements.append(
                {
                    "type": "resistor",
                    "name": "RIN",
                    "positive": "vin",
                    "negative": output,
                    "resistance": float(parameters["input_resistance"]),
                }
            )
        elements.extend(
            [
                {
                    "type": "resistor",
                    "name": f"RSH{index}",
                    "positive": output,
                    "negative": "0",
                    "resistance": float(parameters["shunt_resistance"]),
                },
                {
                    "type": "capacitor",
                    "name": f"C{index}",
                    "positive": output,
                    "negative": "0",
                    "capacitance": float(parameters["capacitance"]),
                    "initial_voltage": float(parameters["initial_voltage"]),
                },
            ]
        )
    elements.extend(_ring_coupling_resistors(size, parameters))
    return elements


def _coupled_rlc_ring(size: int, parameters: dict[str, Any]) -> list[dict[str, Any]]:
    elements = [
        _voltage_source(float(parameters["source_voltage"])),
        {
            "type": "resistor",
            "name": "RIN",
            "positive": "vin",
            "negative": "out1",
            "resistance": float(parameters["input_resistance"]),
        },
    ]
    for index in range(1, size + 1):
        output = f"out{index}"
        elements.extend(
            [
                {
                    "type": "resistor",
                    "name": f"RSH{index}",
                    "positive": output,
                    "negative": "0",
                    "resistance": float(parameters["shunt_resistance"]),
                },
                {
                    "type": "capacitor",
                    "name": f"C{index}",
                    "positive": output,
                    "negative": "0",
                    "capacitance": float(parameters["capacitance"]),
                    "initial_voltage": float(parameters["initial_voltage"]),
                },
                {
                    "type": "inductor",
                    "name": f"L{index}",
                    "positive": output,
                    "negative": "0",
                    "inductance": float(parameters["inductance"]),
                    "initial_current": float(parameters["initial_current"]),
                },
            ]
        )
    elements.extend(_ring_coupling_resistors(size, parameters))
    return elements


def _ring_coupling_resistors(
    size: int,
    parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    elements = []
    for index in range(1, size):
        elements.append(
            {
                "type": "resistor",
                "name": f"RC{index}_{index + 1}",
                "positive": f"out{index}",
                "negative": f"out{index + 1}",
                "resistance": float(parameters["coupling_resistance"]),
            }
        )
    if size > 2:
        elements.append(
            {
                "type": "resistor",
                "name": f"RC{size}_1",
                "positive": f"out{size}",
                "negative": "out1",
                "resistance": float(parameters["coupling_resistance"]),
            }
        )
    return elements


def _rl_bank(size: int, parameters: dict[str, Any]) -> list[dict[str, Any]]:
    elements = [_voltage_source(float(parameters["source_voltage"]))]
    for index in range(1, size + 1):
        middle = f"mid{index}"
        elements.extend(
            [
                {"type": "resistor", "name": f"R{index}", "positive": "vin", "negative": middle, "resistance": float(parameters["resistance"])},
                {"type": "inductor", "name": f"L{index}", "positive": middle, "negative": "0", "inductance": float(parameters["inductance"]), "initial_current": float(parameters["initial_current"])}
            ]
        )
    return elements


def _diode_rc_bank(size: int, parameters: dict[str, Any]) -> list[dict[str, Any]]:
    elements = [
        {
            "type": "voltage_source",
            "name": "VIN",
            "positive": "vin",
            "negative": "0",
            "waveform": {"type": "sine", "offset": 0.0, "amplitude": float(parameters["amplitude"]), "frequency": float(parameters["frequency"])}
        }
    ]
    for index in range(1, size + 1):
        output = f"out{index}"
        elements.extend(
            [
                {"type": "resistor", "name": f"R{index}", "positive": "vin", "negative": output, "resistance": float(parameters["resistance"])},
                {"type": "capacitor", "name": f"C{index}", "positive": output, "negative": "0", "capacitance": float(parameters["capacitance"]), "initial_voltage": float(parameters["initial_voltage"])},
                {"type": "diode", "name": f"D{index}", "positive": output, "negative": "0", "saturation_current": float(parameters["saturation_current"]), "thermal_voltage": float(parameters["thermal_voltage"])}
            ]
        )
    return elements


def _switched_rc_bank(size: int, parameters: dict[str, Any]) -> list[dict[str, Any]]:
    elements = [_voltage_source(float(parameters["source_voltage"]))]
    control = {
        "type": "pulse",
        "low": 0.0,
        "high": 1.0,
        "delay": float(parameters["delay"]),
        "rise": 0.0,
        "fall": 0.0,
        "width": float(parameters["width"]),
        "period": float(parameters["period"])
    }
    for index in range(1, size + 1):
        switched = f"sw{index}"
        output = f"out{index}"
        elements.extend(
            [
                {"type": "switch", "name": f"S{index}", "positive": "vin", "negative": switched, "control": control, "threshold": float(parameters["threshold"]), "on_resistance": float(parameters["on_resistance"]), "off_resistance": float(parameters["off_resistance"])},
                {"type": "resistor", "name": f"R{index}", "positive": switched, "negative": output, "resistance": float(parameters["resistance"])},
                {"type": "capacitor", "name": f"C{index}", "positive": output, "negative": "0", "capacitance": float(parameters["capacitance"]), "initial_voltage": float(parameters["initial_voltage"])}
            ]
        )
    return elements


def _voltage_source(value: float) -> dict[str, Any]:
    return {"type": "voltage_source", "name": "VIN", "positive": "vin", "negative": "0", "waveform": value}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate deterministic BAB-CS runtime scaling cases")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    result = generate_runtime_cases(arguments.manifest, arguments.output_root, check=arguments.check)
    print(json.dumps({"cases": result["cases"], "families": result["families"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
