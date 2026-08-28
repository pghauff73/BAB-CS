from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import venv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from babcs import BoundedIntegrator, Circuit, Simulator
from babcs.io import load_case
from tools.compare_external import generate_ngspice_netlist, parse_ngspice_wrdata
from tools.generate_runtime_cases import (
    DEFAULT_MANIFEST,
    DEFAULT_OUTPUT_ROOT,
    generate_runtime_cases,
    load_runtime_manifest,
    runtime_case_filename,
)
from tools.run_external_suite import load_external_manifest
from tools.runtime_benchmark import (
    BOOTSTRAP_ITERATIONS,
    BOOTSTRAP_SEED,
    DEFAULT_EXTERNAL_MANIFEST,
    RuntimeBenchmarkError,
    analytic_authority,
    canonical_row_id,
    common_grid,
    environment_metadata,
    external_analytic_authority,
    interpolate_rows,
    oscillator_metrics,
    parse_ngspice_rusage,
    percentile,
    refined_authority,
    sha256_bytes,
    sha256_file,
    summarize_samples,
    trajectory_error,
    trace_time_tolerance,
    validate_runtime_report,
    write_json,
    write_markdown_report,
    write_matched_csv,
    write_memory_csv,
    write_memory_svg,
    write_points_work_svg,
    write_solver_work_csv,
    write_speed_accuracy_svg,
)


DEFAULT_OUTPUT = REPOSITORY_ROOT / "artifacts" / "runtime"
WORKER = REPOSITORY_ROOT / "tools" / "runtime_babcs_worker.py"
HYBRID_SPARSE_MINIMUM_DECLARED_MNA_UNKNOWNS = 18


@dataclass(frozen=True)
class CaseSpec:
    row_id: str
    inventory: str
    case_id: str
    title: str
    path: Path
    family_id: str | None
    size: int | None
    family: dict[str, Any] | None


def build_isolated_wheel_environment(
    root: Path,
    *,
    linear_backend: str = "dense",
) -> tuple[Path, dict[str, Any]]:
    if linear_backend not in {"dense", "scipy", "hybrid"}:
        raise RuntimeBenchmarkError(
            f"unsupported runtime BAB-CS backend: {linear_backend}"
        )
    wheel_root = root / "wheel"
    environment_root = root / "venv"
    wheel_root.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            ".",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(wheel_root),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeBenchmarkError(f"wheel build failed: {(completed.stderr or completed.stdout).strip()}")
    wheels = sorted(wheel_root.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeBenchmarkError(f"expected exactly one built wheel, found {len(wheels)}")
    venv.EnvBuilder(
        with_pip=True,
        clear=True,
        system_site_packages=linear_backend in {"scipy", "hybrid"},
    ).create(environment_root)
    python_path = environment_root / "bin" / "python"
    install = subprocess.run(
        [str(python_path), "-m", "pip", "install", "--no-deps", str(wheels[0])],
        capture_output=True,
        text=True,
        check=False,
    )
    if install.returncode != 0:
        raise RuntimeBenchmarkError(f"wheel installation failed: {(install.stderr or install.stdout).strip()}")
    probe_script = (
        "import json, pathlib, babcs; "
        "payload={'babcs_path': str(pathlib.Path(babcs.__file__).resolve()), "
        "'dependencies': {}}; "
    )
    if linear_backend in {"scipy", "hybrid"}:
        probe_script += (
            "import numpy, scipy; "
            "payload['dependencies']={'numpy': {'version': numpy.__version__, "
            "'path': str(pathlib.Path(numpy.__file__).resolve())}, "
            "'scipy': {'version': scipy.__version__, "
            "'path': str(pathlib.Path(scipy.__file__).resolve())}}; "
        )
    probe_script += "print(json.dumps(payload, sort_keys=True))"
    probe = subprocess.run(
        [str(python_path), "-c", probe_script],
        cwd=root,
        env={**os.environ, "PYTHONPATH": ""},
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        raise RuntimeBenchmarkError(f"installed-wheel import probe failed: {probe.stderr.strip()}")
    try:
        probe_payload = json.loads(probe.stdout)
        module_path = Path(probe_payload["babcs_path"]).resolve()
        dependencies = dict(probe_payload["dependencies"])
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeBenchmarkError(
            f"installed-wheel import probe returned invalid metadata: {probe.stdout.strip()}"
        ) from error
    try:
        module_path.relative_to(REPOSITORY_ROOT)
    except ValueError:
        source_tree_excluded = True
    else:
        source_tree_excluded = False
    if not source_tree_excluded:
        raise RuntimeBenchmarkError(f"isolated environment imported BAB-CS from source tree: {module_path}")
    return python_path, {
        "path": str(wheels[0]),
        "sha256": sha256_file(wheels[0]),
        "installed_module_path": str(module_path),
        "source_tree_excluded": True,
        "linear_backend": linear_backend,
        "system_site_packages": linear_backend in {"scipy", "hybrid"},
        "dependencies": dependencies,
    }


def run_with_rss(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    cpu: int | None,
    timeout: float,
) -> dict[str, Any]:
    time_executable = "/usr/bin/time"
    if not Path(time_executable).is_file():
        raise RuntimeBenchmarkError("GNU Time is required at /usr/bin/time")
    rss_path = cwd / "maximum-rss.txt"
    child_command = list(command)
    if cpu is not None:
        allowed = os.sched_getaffinity(0) if hasattr(os, "sched_getaffinity") else None
        if allowed is not None and cpu not in allowed:
            raise RuntimeBenchmarkError(f"requested CPU {cpu} is not in allowed affinity {sorted(allowed)}")
        taskset = shutil.which("taskset")
        if taskset is None:
            raise RuntimeBenchmarkError("CPU affinity was requested but taskset is unavailable")
        child_command = [taskset, "--cpu-list", str(cpu), *child_command]
    timed_command = [time_executable, "-f", "%M", "-o", str(rss_path), *child_command]
    started = time.perf_counter_ns()
    try:
        completed = subprocess.run(
            timed_command,
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        timed_out = False
    except subprocess.TimeoutExpired as error:
        completed = None
        timed_out = True
        stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
    finished = time.perf_counter_ns()
    maximum_rss_kib = None
    if rss_path.is_file():
        raw_rss = rss_path.read_text(encoding="utf-8").strip()
        numeric_lines = [
            line.strip()
            for line in raw_rss.splitlines()
            if line.strip().isdigit()
        ]
        if numeric_lines:
            maximum_rss_kib = int(numeric_lines[-1])
    if completed is not None:
        stdout = completed.stdout
        stderr = completed.stderr
        returncode = completed.returncode
    else:
        returncode = None
    return {
        "command": child_command,
        "process_seconds": (finished - started) / 1.0e9,
        "maximum_rss_kib": maximum_rss_kib,
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
    }


def _child_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "PYTHONPATH": "",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
    )
    return environment


def _case_specs(
    runtime_manifest_path: Path,
    external_manifest_path: Path,
    profile_name: str,
    babcs_backend: str,
    accuracy_mode: str,
    selected_case: str | None,
    inventory: str = "all",
) -> tuple[dict[str, Any], list[CaseSpec]]:
    runtime_manifest = load_runtime_manifest(runtime_manifest_path)
    profiles = runtime_manifest.get("profiles")
    if not isinstance(profiles, dict) or profile_name not in profiles:
        raise RuntimeBenchmarkError(f"unknown runtime profile: {profile_name}")
    profile = profiles[profile_name]
    sizes = {int(value) for value in profile["sizes"]}
    specs: list[CaseSpec] = []
    if inventory in {"all", "size_scaling"}:
        for family in runtime_manifest["families"]:
            family_id = str(family["id"])
            for size in (int(value) for value in family["sizes"] if int(value) in sizes):
                case_id = f"{family_id}-n{size:03d}"
                if selected_case and selected_case not in {family_id, case_id}:
                    continue
                path = DEFAULT_OUTPUT_ROOT / runtime_case_filename(family_id, size)
                row_id = canonical_row_id(
                    {
                        "inventory": "size_scaling",
                        "case_id": case_id,
                        "profile": profile_name,
                        "babcs_backend": babcs_backend,
                        "accuracy_mode": accuracy_mode,
                    }
                )
                specs.append(
                    CaseSpec(
                        row_id=row_id,
                        inventory="size_scaling",
                        case_id=case_id,
                        title=str(family["title"]),
                        path=path,
                        family_id=family_id,
                        size=size,
                        family=family,
                    )
                )
    external_manifest = load_external_manifest(external_manifest_path)
    external_selection = profile.get("external_cases", "all")
    allowed_external = None if external_selection == "all" else {str(value) for value in external_selection}
    if inventory in {"all", "semantic_breadth"}:
        for case in external_manifest["cases"]:
            case_id = str(case["id"])
            if allowed_external is not None and case_id not in allowed_external:
                continue
            if selected_case and selected_case != case_id:
                continue
            path = (external_manifest_path.parent / str(case["input"])).resolve()
            row_id = canonical_row_id(
                {
                    "inventory": "semantic_breadth",
                    "case_id": case_id,
                    "profile": profile_name,
                    "babcs_backend": babcs_backend,
                    "accuracy_mode": accuracy_mode,
                }
            )
            specs.append(
                CaseSpec(
                    row_id=row_id,
                    inventory="semantic_breadth",
                    case_id=case_id,
                    title=str(case["title"]),
                    path=path,
                    family_id=None,
                    size=None,
                    family=None,
                )
            )
    if selected_case and not specs:
        raise RuntimeBenchmarkError(f"selected case or family was not found in profile: {selected_case}")
    return runtime_manifest, specs


def resolve_case_babcs_backend(
    spec: CaseSpec,
    requested_backend: str,
    *,
    sparse_minimum_declared_mna_unknowns: int = HYBRID_SPARSE_MINIMUM_DECLARED_MNA_UNKNOWNS,
) -> str:
    if requested_backend != "hybrid":
        return requested_backend
    circuit, _, _ = load_case(spec.path)
    declared_mna_unknowns = circuit.dynamic_size + circuit.algebraic_size
    return (
        "scipy"
        if declared_mna_unknowns >= sparse_minimum_declared_mna_unknowns
        else "dense"
    )


def _run_babcs_sample(
    spec: CaseSpec,
    *,
    python_path: Path,
    linear_backend: str,
    nominal_step: float | None,
    cpu: int | None,
    timeout: float,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    with tempfile.TemporaryDirectory(prefix="babcs-runtime-babcs-") as directory:
        root = Path(directory)
        output_path = root / "babcs.json"
        command = [
            str(python_path),
            str(WORKER),
            str(spec.path),
            "--output",
            str(output_path),
            "--forbidden-root",
            str(REPOSITORY_ROOT),
            "--linear-backend",
            linear_backend,
        ]
        if nominal_step is not None:
            command.extend(("--nominal-step", format(nominal_step, ".17g")))
        process = run_with_rss(
            command,
            cwd=root,
            environment=_child_environment(),
            cpu=cpu,
            timeout=timeout,
        )
        payload = None
        error = None
        if process["returncode"] == 0 and output_path.is_file():
            try:
                payload = json.loads(output_path.read_text(encoding="utf-8"))
            except (ValueError, OSError) as parse_error:
                error = f"invalid BAB-CS worker output: {parse_error}"
        elif process["timed_out"]:
            error = "BAB-CS worker timed out"
        else:
            error = f"BAB-CS worker failed: {process['stderr'].strip()}"
        sample = {
            "tool": "babcs",
            "status": "success" if payload is not None else "failed",
            "failure_reason": error,
            "analysis_seconds": payload["timing"]["analysis_seconds"] if payload else None,
            "process_seconds": process["process_seconds"],
            "maximum_rss_kib": process["maximum_rss_kib"],
            "returncode": process["returncode"],
            "timed_out": process["timed_out"],
            "command": process["command"],
            "accepted_points": (
                int(payload["summary"]["accepted_steps"]) + 1 if payload else None
            ),
            "rejected_points": int(payload["summary"]["rejected_steps"]) if payload else None,
            "output_points": int(payload["output_points"]) if payload else None,
            "stop_time": float(payload["summary"]["stop_time"]) if payload else None,
            "solver_work": payload["summary"] if payload else None,
        }
        return sample, payload


def _run_ngspice_sample(
    spec: CaseSpec,
    *,
    executable: str,
    netlist: str,
    expected_states: int,
    cpu: int | None,
    timeout: float,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    with tempfile.TemporaryDirectory(prefix="babcs-runtime-ngspice-") as directory:
        root = Path(directory)
        (root / "case.cir").write_text(netlist, encoding="utf-8")
        process = run_with_rss(
            [executable, "-b", "-o", "ngspice.log", "case.cir"],
            cwd=root,
            environment=_child_environment(),
            cpu=cpu,
            timeout=timeout,
        )
        payload = None
        error = None
        log_path = root / "ngspice.log"
        data_path = root / "external.dat"
        if process["returncode"] == 0 and log_path.is_file() and data_path.is_file():
            try:
                log = log_path.read_text(encoding="utf-8", errors="replace")
                raw = data_path.read_text(encoding="utf-8")
                rusage = parse_ngspice_rusage(log)
                rows = parse_ngspice_wrdata(raw, expected_states)
                payload = {"log": log, "raw": raw, "rusage": rusage, "trace_rows": rows}
            except (RuntimeBenchmarkError, ValueError, OSError) as parse_error:
                error = f"invalid ngspice evidence: {parse_error}"
        elif process["timed_out"]:
            error = "ngspice timed out"
        else:
            error = f"ngspice failed: {process['stderr'].strip()}"
        sample = {
            "tool": "ngspice",
            "status": "success" if payload is not None else "failed",
            "failure_reason": error,
            "analysis_seconds": payload["rusage"]["counters"]["total_analysis_seconds"] if payload else None,
            "process_seconds": process["process_seconds"],
            "maximum_rss_kib": process["maximum_rss_kib"],
            "returncode": process["returncode"],
            "timed_out": process["timed_out"],
            "command": process["command"],
            "accepted_points": (
                int(payload["rusage"]["counters"]["accepted_timepoints"])
                if payload
                else None
            ),
            "rejected_points": (
                int(payload["rusage"]["counters"]["rejected_timepoints"])
                if payload
                else None
            ),
            "output_points": len(payload["trace_rows"]) if payload else None,
            "stop_time": float(payload["trace_rows"][-1][0]) if payload else None,
            "solver_work": payload["rusage"] if payload else None,
        }
        return sample, payload


def _source_trace(
    spec: CaseSpec,
    *,
    linear_backend: str,
    nominal_step: float | None = None,
) -> tuple[list[list[float]], list[str]]:
    circuit, simulation, config = load_case(spec.path)
    circuit = Circuit(circuit.elements, linear_backend=linear_backend)
    if nominal_step is not None:
        simulation = {**simulation, "nominal_step": nominal_step}
    result = Simulator(BoundedIntegrator(config)).run(circuit, **simulation)
    return (
        [[point.time, *point.state.evaluation.dynamic_state] for point in result.points],
        list(circuit.dynamic_names),
    )


def _speedup_bootstrap(babcs: list[float], ngspice: list[float]) -> dict[str, float] | None:
    if len(babcs) < 11 or len(ngspice) < 11:
        return None
    import random

    generator = random.Random(BOOTSTRAP_SEED)
    ratios = []
    for _ in range(BOOTSTRAP_ITERATIONS):
        bab_sample = generator.choices(babcs, k=len(babcs))
        ng_sample = generator.choices(ngspice, k=len(ngspice))
        ratios.append(statistics.median(ng_sample) / statistics.median(bab_sample))
    return {"lower": percentile(ratios, 0.025), "upper": percentile(ratios, 0.975)}


def _babcs_native_work(summary: dict[str, Any]) -> int:
    names = (
        "accepted_steps",
        "candidate_circuit_evaluations",
        "candidate_algebraic_iterations",
        "reference_circuit_evaluations",
        "reference_algebraic_iterations",
        "predictor_projection_iterations",
        "corrected_projection_iterations",
        "differential_jacobian_evaluations",
        "replay_steps",
        "replay_circuit_evaluations",
        "replay_algebraic_iterations",
    )
    return sum(int(summary.get(name, 0)) for name in names)


def select_fixed_accuracy_attempt(
    attempts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    eligible = [attempt for attempt in attempts if attempt["qualifies"]]
    return min(
        eligible,
        key=lambda attempt: (
            int(attempt["native_work"]),
            float(attempt["maximum_scaled_trajectory_error"]),
            float(attempt["nominal_step"]),
            int(attempt["step_divisor"]),
        ),
        default=None,
    )


def _payload_accuracy_grid(
    tool: str,
    payload: dict[str, Any],
    *,
    circuit: Circuit,
    simulation: dict[str, float],
    grid: tuple[float, ...],
) -> tuple[tuple[tuple[float, ...], ...], bool]:
    rows = [list(row) for row in payload["trace_rows"]]
    initial_point_injected = False
    if tool == "ngspice" and float(rows[0][0]) > float(simulation["start_time"]):
        rows.insert(
            0,
            [float(simulation["start_time"]), *circuit.initial_dynamic_state()],
        )
        initial_point_injected = True
    return interpolate_rows(rows, circuit.dynamic_size, grid), initial_point_injected


def _case_authority(
    spec: CaseSpec,
    *,
    case_data: dict[str, Any],
    circuit: Circuit,
    grid: tuple[float, ...],
    runtime_manifest: dict[str, Any],
    accuracy_mode: str,
    linear_backend: str,
) -> tuple[tuple[tuple[float, ...], ...], dict[str, Any]]:
    if spec.family and str(spec.family["authority"]["type"]).startswith("analytic_"):
        authority_grid = analytic_authority(spec.family, circuit.dynamic_size, grid)
        return authority_grid, {
            "type": spec.family["authority"]["type"],
            "qualified": True,
            "convergence": {"type": "analytic_exact", "maximum_scaled_error": 0.0},
            "trace_sha256": sha256_bytes(
                json.dumps(authority_grid, separators=(",", ":")).encode()
            ),
        }
    if spec.family is None:
        external_authority = external_analytic_authority(spec.case_id, case_data, grid)
        if external_authority is not None:
            authority_grid, metadata = external_authority
            return authority_grid, {
                **metadata,
                "qualified": True,
                "convergence": {
                    "type": "analytic_exact",
                    "maximum_scaled_error": 0.0,
                },
            }
    if accuracy_mode == "fixed_accuracy":
        fixed_accuracy = runtime_manifest["fixed_accuracy"]
        requested_refinement_factor = int(
            fixed_accuracy["authority_refinement_factor"]
        )
        refinement_factor = requested_refinement_factor
        maximum_divisor = max(_fixed_accuracy_step_divisors(spec, runtime_manifest))
        maximum_authority_trace_values = int(
            fixed_accuracy["maximum_estimated_authority_trace_values"]
        )
        _, simulation, _ = load_case(spec.path)
        duration = float(simulation["stop_time"]) - float(simulation["start_time"])
        baseline_step = float(simulation["nominal_step"])
        requested_points = math.ceil(
            duration / (baseline_step / requested_refinement_factor)
        ) + 1
        requested_trace_values = requested_points * (circuit.dynamic_size + 1)
        authority_budget_exceeded = (
            requested_trace_values > maximum_authority_trace_values
        )
        if authority_budget_exceeded:
            affordable_points = max(
                maximum_authority_trace_values // (circuit.dynamic_size + 1),
                5,
            )
            affordable_factor = math.floor(
                (affordable_points - 1) * baseline_step / duration
            )
            refinement_factor = max(
                4,
                min(requested_refinement_factor, affordable_factor),
            )
    else:
        authority_definition = spec.family["authority"] if spec.family else {"refinement_factor": 8}
        refinement_factor = int(authority_definition.get("refinement_factor", 8))
    authority_grid, metadata = refined_authority(
        spec.path,
        grid,
        refinement_factor=refinement_factor,
        linear_backend=linear_backend,
    )
    if accuracy_mode == "fixed_accuracy":
        coarse_factor = refinement_factor // 2
        coarse_grid, coarse_metadata = refined_authority(
            spec.path,
            grid,
            refinement_factor=coarse_factor,
            linear_backend=linear_backend,
        )
        tolerances = runtime_manifest["accuracy"]
        convergence = trajectory_error(
            coarse_grid,
            authority_grid,
            circuit.dynamic_names,
            absolute_tolerance=float(tolerances["absolute_tolerance"]),
            relative_tolerance=float(tolerances["relative_tolerance"]),
        )
        convergence_cap = float(
            runtime_manifest["fixed_accuracy"][
                "authority_convergence_scaled_error_cap"
            ]
        )
        metadata = {
            **metadata,
            "minimum_refinement_beyond_finest_candidate": (
                refinement_factor
                / max(_fixed_accuracy_step_divisors(spec, runtime_manifest))
            ),
            "qualified": bool(
                not authority_budget_exceeded
                and refinement_factor >= 4 * maximum_divisor
                and convergence["maximum_scaled_trajectory_error"] <= convergence_cap
            ),
            "failure_reason": (
                "authority trace-value budget exceeded"
                if authority_budget_exceeded
                else (
                    "authority is not four times finer than the finest candidate"
                    if refinement_factor < 4 * maximum_divisor
                    else (
                        "authority refinement did not satisfy convergence cap"
                        if convergence["maximum_scaled_trajectory_error"] > convergence_cap
                        else None
                    )
                )
            ),
            "budget": {
                "maximum_estimated_trace_values": maximum_authority_trace_values,
                "requested_refinement_factor": requested_refinement_factor,
                "used_refinement_factor": refinement_factor,
                "requested_points": requested_points,
                "requested_trace_values": requested_trace_values,
                "exceeded": authority_budget_exceeded,
            },
            "convergence": {
                "coarse_refinement_factor": coarse_factor,
                "coarse_trace_sha256": coarse_metadata["trace_sha256"],
                "maximum_pointwise_absolute_error": convergence[
                    "maximum_pointwise_absolute_error"
                ],
                "maximum_scaled_error": convergence[
                    "maximum_scaled_trajectory_error"
                ],
                "scaled_error_cap": convergence_cap,
            },
        }
    else:
        metadata = {**metadata, "qualified": None, "convergence": None}
    return authority_grid, metadata


def _fixed_accuracy_step_divisors(
    spec: CaseSpec,
    runtime_manifest: dict[str, Any],
) -> tuple[int, ...]:
    fixed_accuracy = runtime_manifest["fixed_accuracy"]
    family_divisors = fixed_accuracy.get("family_step_divisors", {})
    raw_divisors = (
        family_divisors.get(spec.family_id)
        if spec.family_id is not None and spec.family_id in family_divisors
        else fixed_accuracy["step_divisors"]
    )
    divisors = tuple(int(value) for value in raw_divisors)
    if not divisors or any(value <= 0 for value in divisors) or tuple(sorted(set(divisors))) != divisors:
        raise RuntimeBenchmarkError(
            "fixed-accuracy step divisors must be unique positive ascending integers"
        )
    return divisors


def _calibrate_fixed_accuracy(
    spec: CaseSpec,
    *,
    case_data: dict[str, Any],
    circuit: Circuit,
    simulation: dict[str, float],
    state_names: tuple[str, ...],
    grid: tuple[float, ...],
    authority_grid: tuple[tuple[float, ...], ...],
    runtime_manifest: dict[str, Any],
    wheel_python: Path,
    babcs_backend: str,
    ngspice_executable: str,
    cpu: int | None,
    timeout: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    tolerances = runtime_manifest["accuracy"]
    target = float(tolerances["target_scaled_error"])
    divisors = _fixed_accuracy_step_divisors(spec, runtime_manifest)
    baseline_step = float(simulation["nominal_step"])
    maximum_estimated_points = int(
        runtime_manifest["fixed_accuracy"]["maximum_estimated_calibration_points"]
    )
    maximum_estimated_trace_values = int(
        runtime_manifest["fixed_accuracy"][
            "maximum_estimated_calibration_trace_values"
        ]
    )
    calibration_samples: list[dict[str, Any]] = []
    tool_evidence: dict[str, Any] = {}
    for tool in ("babcs", "ngspice"):
        attempts: list[dict[str, Any]] = []
        for divisor in divisors:
            nominal_step = baseline_step / divisor
            estimated_points = (
                math.ceil(
                    (float(simulation["stop_time"]) - float(simulation["start_time"]))
                    / nominal_step
                )
                + 1
            )
            estimated_trace_values = estimated_points * (circuit.dynamic_size + 1)
            if (
                estimated_points > maximum_estimated_points
                or estimated_trace_values > maximum_estimated_trace_values
            ):
                attempts.append(
                    {
                        "step_divisor": divisor,
                        "nominal_step": nominal_step,
                        "status": "budget_exceeded",
                        "failure_reason": (
                            f"estimated {estimated_points} points and {estimated_trace_values} "
                            "trace values exceed calibration budgets "
                            f"{maximum_estimated_points} points and "
                            f"{maximum_estimated_trace_values} trace values"
                        ),
                        "estimated_points": estimated_points,
                        "estimated_trace_values": estimated_trace_values,
                        "accepted_points": None,
                        "rejected_points": None,
                        "output_points": None,
                        "analysis_seconds": None,
                        "maximum_scaled_trajectory_error": None,
                        "maximum_pointwise_absolute_error": None,
                        "native_work": None,
                        "qualifies": False,
                    }
                )
                break
            if tool == "babcs":
                sample, payload = _run_babcs_sample(
                    spec,
                    python_path=wheel_python,
                    linear_backend=babcs_backend,
                    nominal_step=nominal_step,
                    cpu=cpu,
                    timeout=timeout,
                )
            else:
                netlist, calibration_state_names = generate_ngspice_netlist(
                    case_data,
                    output_filename="external.dat",
                    include_rusage=True,
                    nominal_step_override=nominal_step,
                )
                if calibration_state_names != state_names:
                    raise RuntimeBenchmarkError(
                        "ngspice calibration state order changed across timestep sweep"
                    )
                sample, payload = _run_ngspice_sample(
                    spec,
                    executable=ngspice_executable,
                    netlist=netlist,
                    expected_states=len(state_names),
                    cpu=cpu,
                    timeout=timeout,
                )
            sample.update(
                {
                    "phase": "calibration",
                    "step_divisor": divisor,
                    "nominal_step": nominal_step,
                }
            )
            calibration_samples.append(sample)
            attempt: dict[str, Any] = {
                "step_divisor": divisor,
                "nominal_step": nominal_step,
                "estimated_points": estimated_points,
                "estimated_trace_values": estimated_trace_values,
                "status": sample["status"],
                "failure_reason": sample["failure_reason"],
                "accepted_points": sample["accepted_points"],
                "rejected_points": sample["rejected_points"],
                "output_points": sample["output_points"],
                "analysis_seconds": sample["analysis_seconds"],
                "maximum_scaled_trajectory_error": None,
                "maximum_pointwise_absolute_error": None,
                "native_work": None,
                "qualifies": False,
            }
            if payload is not None:
                sampled, initial_point_injected = _payload_accuracy_grid(
                    tool,
                    payload,
                    circuit=circuit,
                    simulation=simulation,
                    grid=grid,
                )
                error = trajectory_error(
                    sampled,
                    authority_grid,
                    state_names,
                    absolute_tolerance=float(tolerances["absolute_tolerance"]),
                    relative_tolerance=float(tolerances["relative_tolerance"]),
                )
                native_work = (
                    _babcs_native_work(payload["summary"])
                    if tool == "babcs"
                    else int(payload["rusage"]["counters"]["total_iterations"])
                )
                attempt.update(
                    {
                        "maximum_scaled_trajectory_error": error[
                            "maximum_scaled_trajectory_error"
                        ],
                        "maximum_pointwise_absolute_error": error[
                            "maximum_pointwise_absolute_error"
                        ],
                        "native_work": native_work,
                        "qualifies": bool(
                            error["maximum_scaled_trajectory_error"] <= target
                        ),
                        "ngspice_evaluation_initial_point_injected": (
                            initial_point_injected if tool == "ngspice" else None
                        ),
                    }
                )
            attempts.append(attempt)
            if attempt["qualifies"] and runtime_manifest["fixed_accuracy"].get(
                "stop_at_first_qualifying",
                False,
            ):
                break
        selected = select_fixed_accuracy_attempt(attempts)
        budget_exceeded = bool(
            attempts and attempts[-1]["status"] == "budget_exceeded"
        )
        tool_status = (
            "selected"
            if selected is not None
            else (
                "calibration_budget_exceeded"
                if budget_exceeded
                else "no_qualifying_configuration"
            )
        )
        tool_evidence[tool] = {
            "status": tool_status,
            "selected_step_divisor": (
                None if selected is None else selected["step_divisor"]
            ),
            "selected_nominal_step": (
                baseline_step if selected is None else selected["nominal_step"]
            ),
            "selected_native_work": None if selected is None else selected["native_work"],
            "selected_maximum_scaled_trajectory_error": (
                None
                if selected is None
                else selected["maximum_scaled_trajectory_error"]
            ),
            "attempts": attempts,
        }
    qualified = all(
        evidence["status"] == "selected" for evidence in tool_evidence.values()
    )
    return (
        {
            "mode": "fixed_accuracy",
            "target_scaled_error": target,
            "selection": runtime_manifest["fixed_accuracy"]["selection"],
            "tools": tool_evidence,
            "qualified": qualified,
            "failure_reason": (
                None
                if qualified
                else "; ".join(
                    f"{tool}: {evidence['status']}"
                    for tool, evidence in tool_evidence.items()
                    if evidence["status"] != "selected"
                )
            ),
        },
        calibration_samples,
    )


def _execute_case(
    spec: CaseSpec,
    *,
    runtime_manifest: dict[str, Any],
    wheel_python: Path,
    babcs_backend: str,
    accuracy_mode: str,
    ngspice_executable: str,
    warmups: int,
    repeats: int,
    rounds: int,
    cpu: int | None,
    timeout: float,
    logs_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    case_data = json.loads(spec.path.read_text(encoding="utf-8"))
    circuit, simulation, babcs_config = load_case(spec.path)
    if spec.family_id is None:
        babcs_profile = {
            "id": f"case_declared:{spec.case_id}",
            "source": "case_file",
            "description": (
                "BAB-CS configuration declared directly by the semantic-breadth case."
            ),
            "declared_overrides": case_data.get("babcs", {}),
            "effective_configuration": asdict(babcs_config),
        }
    else:
        profile_id = str(case_data["runtime_benchmark"]["babcs_profile_id"])
        babcs_profile = {
            "id": profile_id,
            "source": "runtime_manifest",
            "description": case_data["runtime_benchmark"][
                "babcs_profile_description"
            ],
            "declared_overrides": case_data["babcs"],
            "effective_configuration": asdict(babcs_config),
        }
    _, state_names = generate_ngspice_netlist(case_data)
    grid = common_grid(
        float(simulation["start_time"]),
        float(simulation["stop_time"]),
        int(runtime_manifest["common_grid_samples"]),
    )
    authority_grid, authority_metadata = _case_authority(
        spec,
        case_data=case_data,
        circuit=circuit,
        grid=grid,
        runtime_manifest=runtime_manifest,
        accuracy_mode=accuracy_mode,
        linear_backend=babcs_backend,
    )
    samples: list[dict[str, Any]] = []
    baseline_nominal_step = float(simulation["nominal_step"])
    babcs_nominal_step = baseline_nominal_step
    ngspice_nominal_step = baseline_nominal_step
    accuracy_sweep: dict[str, Any] | None = None
    if accuracy_mode == "fixed_accuracy":
        if authority_metadata.get("qualified"):
            accuracy_sweep, calibration_samples = _calibrate_fixed_accuracy(
                spec,
                case_data=case_data,
                circuit=circuit,
                simulation=simulation,
                state_names=state_names,
                grid=grid,
                authority_grid=authority_grid,
                runtime_manifest=runtime_manifest,
                wheel_python=wheel_python,
                babcs_backend=babcs_backend,
                ngspice_executable=ngspice_executable,
                cpu=cpu,
                timeout=timeout,
            )
        else:
            calibration_samples = []
            accuracy_sweep = {
                "mode": "fixed_accuracy",
                "target_scaled_error": float(
                    runtime_manifest["accuracy"]["target_scaled_error"]
                ),
                "selection": runtime_manifest["fixed_accuracy"]["selection"],
                "status": "authority_unqualified",
                "qualified": False,
                "failure_reason": (
                    authority_metadata.get("failure_reason")
                    or "independent authority refinement did not satisfy its convergence cap"
                ),
                "tools": {
                    tool: {
                        "status": "authority_unqualified",
                        "selected_step_divisor": None,
                        "selected_nominal_step": baseline_nominal_step,
                        "selected_native_work": None,
                        "selected_maximum_scaled_trajectory_error": None,
                        "attempts": [],
                    }
                    for tool in ("babcs", "ngspice")
                },
            }
        for calibration_index, sample in enumerate(calibration_samples):
            sample.update(
                {
                    "sample_id": f"{spec.row_id}-calibration-{calibration_index}-{sample['tool']}",
                    "row_id": spec.row_id,
                    "round": None,
                    "repeat": calibration_index,
                    "execution_index": len(samples),
                }
            )
            samples.append(sample)
        babcs_nominal_step = float(
            accuracy_sweep["tools"]["babcs"]["selected_nominal_step"]
        )
        ngspice_nominal_step = float(
            accuracy_sweep["tools"]["ngspice"]["selected_nominal_step"]
        )
    netlist, state_names = generate_ngspice_netlist(
        case_data,
        output_filename="external.dat",
        include_rusage=True,
        nominal_step_override=ngspice_nominal_step,
    )
    (logs_root / f"{spec.row_id}.cir").write_text(netlist, encoding="utf-8")
    first_payload: dict[str, Any] = {}

    def execute(tool: str, phase: str, round_index: int | None, repeat_index: int) -> None:
        if tool == "babcs":
            sample, payload = _run_babcs_sample(
                spec,
                python_path=wheel_python,
                linear_backend=babcs_backend,
                nominal_step=babcs_nominal_step,
                cpu=cpu,
                timeout=timeout,
            )
        else:
            sample, payload = _run_ngspice_sample(
                spec,
                executable=ngspice_executable,
                netlist=netlist,
                expected_states=len(state_names),
                cpu=cpu,
                timeout=timeout,
            )
        sample.update(
            {
                "sample_id": f"{spec.row_id}-{phase}-{round_index if round_index is not None else 0}-{repeat_index}-{tool}",
                "row_id": spec.row_id,
                "phase": phase,
                "round": round_index,
                "repeat": repeat_index,
                "execution_index": len(samples),
            }
        )
        samples.append(sample)
        if phase == "timed" and payload is not None and tool not in first_payload:
            first_payload[tool] = payload

    for warmup_index in range(warmups):
        order = ("babcs", "ngspice") if warmup_index % 2 == 0 else ("ngspice", "babcs")
        for tool in order:
            execute(tool, "warmup", None, warmup_index)
    for round_index in range(rounds):
        for repeat_index in range(repeats):
            order = (
                ("babcs", "ngspice")
                if (round_index + repeat_index) % 2 == 0
                else ("ngspice", "babcs")
            )
            for tool in order:
                execute(tool, "timed", round_index, repeat_index)

    timed = [sample for sample in samples if sample["phase"] == "timed"]
    expected = repeats * rounds
    successful = {
        tool: [sample for sample in timed if sample["tool"] == tool and sample["status"] == "success"]
        for tool in ("babcs", "ngspice")
    }
    failure_reasons = [
        sample["failure_reason"] for sample in timed if sample["status"] != "success"
    ]
    if any(len(successful[tool]) != expected for tool in successful):
        status = "failed"
        failure_reasons.append(
            f"incomplete timed samples: expected {expected} per tool, got "
            f"BAB-CS={len(successful['babcs'])}, ngspice={len(successful['ngspice'])}"
        )
    else:
        status = "success"
    for tool in ("babcs", "ngspice"):
        point_signatures = {
            (
                sample["accepted_points"],
                sample["rejected_points"],
                sample["output_points"],
            )
            for sample in successful[tool]
        }
        if len(point_signatures) > 1:
            status = "failed"
            failure_reasons.append(f"{tool} point counts changed across timed samples")

    circuit_size = {
        "element_count": len(circuit.elements),
        "non_ground_node_count": len(circuit.nodes),
        "dynamic_state_count": circuit.dynamic_size,
        "algebraic_unknown_count": circuit.algebraic_size,
        "declared_mna_unknowns": circuit.dynamic_size + circuit.algebraic_size,
        "ngspice_circuit_equations": None,
    }
    runtime: dict[str, Any] = {"speedup_bootstrap_95": None}
    memory: dict[str, Any] = {}
    speedup = None
    for tool in ("babcs", "ngspice"):
        analysis_values = [float(sample["analysis_seconds"]) for sample in successful[tool]]
        process_values = [float(sample["process_seconds"]) for sample in successful[tool]]
        rss_values = [float(sample["maximum_rss_kib"]) for sample in successful[tool] if sample["maximum_rss_kib"] is not None]
        runtime[tool] = {
            "analysis_seconds": summarize_samples(analysis_values) if analysis_values else None,
            "process_seconds": summarize_samples(process_values) if process_values else None,
        }
        memory[tool] = {
            "maximum_rss_kib": summarize_samples(rss_values) if rss_values else None
        }
    if runtime["babcs"]["analysis_seconds"] and runtime["ngspice"]["analysis_seconds"]:
        bab_median = float(runtime["babcs"]["analysis_seconds"]["median"])
        ng_median = float(runtime["ngspice"]["analysis_seconds"]["median"])
        if bab_median > 0.0 and ng_median > 0.0:
            speedup = ng_median / bab_median
            runtime["speedup_bootstrap_95"] = _speedup_bootstrap(
                [float(sample["analysis_seconds"]) for sample in successful["babcs"]],
                [float(sample["analysis_seconds"]) for sample in successful["ngspice"]],
            )

    accuracy: dict[str, Any] = {"authority": None, "babcs": None, "ngspice": None, "direct_difference": None}
    points = {
        "babcs": {"accepted": None, "rejected": None, "output": None},
        "ngspice": {"accepted": None, "rejected": None, "output": None},
        "common_grid": int(runtime_manifest["common_grid_samples"]),
    }
    solver_work: dict[str, Any] = {"babcs": None, "ngspice": None}
    source_wheel_equivalent = False
    source_wheel_evidence: dict[str, Any] | None = None
    if "babcs" in first_payload and "ngspice" in first_payload:
        babcs_payload = first_payload["babcs"]
        ngspice_payload = first_payload["ngspice"]
        write_json(logs_root / f"{spec.row_id}-babcs.json", babcs_payload)
        (logs_root / f"{spec.row_id}-ngspice.log").write_text(ngspice_payload["log"], encoding="utf-8")
        (logs_root / f"{spec.row_id}-ngspice.dat").write_text(ngspice_payload["raw"], encoding="utf-8")
        rusage = ngspice_payload["rusage"]["counters"]
        circuit_size["ngspice_circuit_equations"] = rusage["circuit_equations"]
        points["babcs"] = {
            "accepted": int(babcs_payload["summary"]["accepted_steps"]) + 1,
            "rejected": int(babcs_payload["summary"]["rejected_steps"]),
            "output": int(babcs_payload["output_points"]),
        }
        points["ngspice"] = {
            "accepted": int(rusage["accepted_timepoints"]),
            "rejected": int(rusage["rejected_timepoints"]),
            "output": len(ngspice_payload["trace_rows"]),
        }
        summary = babcs_payload["summary"]
        solver_work["babcs"] = {
            **summary,
            "projection_iterations": int(summary["predictor_projection_iterations"]) + int(summary["corrected_projection_iterations"]),
        }
        solver_work["ngspice"] = {
            **rusage,
            "linear_solver": ngspice_payload["rusage"]["linear_solver"],
            "unknown_fields": ngspice_payload["rusage"]["unknown_fields"],
        }
        babcs_accepted = max(int(points["babcs"]["accepted"]), 1)
        ngspice_accepted = max(int(points["ngspice"]["accepted"]), 1)
        solver_work["babcs"]["normalized_per_accepted_timepoint"] = {
            key: float(solver_work["babcs"][key]) / babcs_accepted
            for key in (
                "candidate_solves",
                "reference_solves",
                "candidate_circuit_evaluations",
                "reference_circuit_evaluations",
                "projection_iterations",
                "differential_jacobian_evaluations",
            )
        }
        solver_work["ngspice"]["normalized_per_accepted_timepoint"] = {
            "total_iterations": float(rusage["total_iterations"]) / ngspice_accepted,
            "transient_iterations": float(rusage["transient_iterations"]) / ngspice_accepted,
        }
        source_rows, source_names = _source_trace(
            spec,
            linear_backend=babcs_backend,
            nominal_step=babcs_nominal_step,
        )
        wheel_rows = babcs_payload["trace_rows"]
        matching_shape = len(source_rows) == len(wheel_rows) and all(
            len(source_row) == len(wheel_row)
            for source_row, wheel_row in zip(source_rows, wheel_rows, strict=True)
        )
        matching_times = matching_shape and all(
            source_row[0] == wheel_row[0]
            for source_row, wheel_row in zip(source_rows, wheel_rows, strict=True)
        )
        source_wheel_evidence = {
            "absolute_tolerance": 1.0e-10,
            "relative_tolerance": 1.0e-6,
            "matching_state_names": source_names == babcs_payload["state_names"],
            "matching_times": matching_times,
            "maximum_absolute_error": None,
            "maximum_scaled_error": None,
        }
        if matching_shape and matching_times:
            equivalence_error = trajectory_error(
                [row[1:] for row in source_rows],
                [row[1:] for row in wheel_rows],
                source_names,
                absolute_tolerance=1.0e-10,
                relative_tolerance=1.0e-6,
            )
            source_wheel_evidence["maximum_absolute_error"] = equivalence_error[
                "maximum_pointwise_absolute_error"
            ]
            source_wheel_evidence["maximum_scaled_error"] = equivalence_error[
                "maximum_scaled_trajectory_error"
            ]
        source_wheel_equivalent = bool(
            source_wheel_evidence["matching_state_names"]
            and source_wheel_evidence["matching_times"]
            and source_wheel_evidence["maximum_scaled_error"] is not None
            and float(source_wheel_evidence["maximum_scaled_error"]) <= 1.0
        )
        if not source_wheel_equivalent:
            status = "failed"
            failure_reasons.append("source and installed-wheel BAB-CS traces differ")
        if tuple(babcs_payload["state_names"]) != state_names:
            status = "failed"
            failure_reasons.append("BAB-CS and ngspice state order differs")
        babcs_grid, _ = _payload_accuracy_grid(
            "babcs",
            babcs_payload,
            circuit=circuit,
            simulation=simulation,
            grid=grid,
        )
        ngspice_grid, evaluation_initial_point_injected = _payload_accuracy_grid(
            "ngspice",
            ngspice_payload,
            circuit=circuit,
            simulation=simulation,
            grid=grid,
        )
        tolerances = runtime_manifest["accuracy"]
        accuracy["authority"] = authority_metadata
        accuracy["babcs"] = trajectory_error(
            babcs_grid,
            authority_grid,
            state_names,
            absolute_tolerance=float(tolerances["absolute_tolerance"]),
            relative_tolerance=float(tolerances["relative_tolerance"]),
        )
        accuracy["ngspice"] = trajectory_error(
            ngspice_grid,
            authority_grid,
            state_names,
            absolute_tolerance=float(tolerances["absolute_tolerance"]),
            relative_tolerance=float(tolerances["relative_tolerance"]),
        )
        accuracy["direct_difference"] = trajectory_error(
            babcs_grid,
            ngspice_grid,
            state_names,
            absolute_tolerance=float(tolerances["absolute_tolerance"]),
            relative_tolerance=float(tolerances["relative_tolerance"]),
        )
        babcs_oscillator = oscillator_metrics(
            babcs_grid,
            authority_grid,
            grid,
            case_data,
        )
        ngspice_oscillator = oscillator_metrics(
            ngspice_grid,
            authority_grid,
            grid,
            case_data,
        )
        if babcs_oscillator is not None:
            accuracy["babcs"]["oscillator"] = babcs_oscillator
        if ngspice_oscillator is not None:
            accuracy["ngspice"]["oscillator"] = ngspice_oscillator
        accuracy["ngspice_evaluation_initial_point_injected"] = (
            evaluation_initial_point_injected
        )
        if accuracy_mode == "fixed_accuracy":
            target = float(tolerances["target_scaled_error"])
            qualified = bool(
                accuracy_sweep is not None
                and accuracy_sweep["qualified"]
                and accuracy["babcs"]["maximum_scaled_trajectory_error"] <= target
                and accuracy["ngspice"]["maximum_scaled_trajectory_error"] <= target
            )
            if not qualified and status == "success":
                status = "accuracy_unavailable"
                failure_reasons.append(
                    accuracy_sweep.get("failure_reason")
                    or "fixed-accuracy sweep did not produce a target-qualified configuration for both tools"
                )

    babcs_stop_time = first_payload.get("babcs", {}).get("summary", {}).get("stop_time")
    ngspice_stop_time = (
        first_payload.get("ngspice", {}).get("trace_rows", [[None]])[-1][0]
        if first_payload.get("ngspice")
        else None
    )
    semantic_equality = {
        "case_hash_matches_worker": (
            first_payload.get("babcs", {}).get("case_sha256") == sha256_file(spec.path)
        ),
        "state_order_matches": (
            tuple(first_payload.get("babcs", {}).get("state_names", ())) == state_names
        ),
        "start_time": float(simulation["start_time"]),
        "stop_time": float(simulation["stop_time"]),
        "accuracy_mode": accuracy_mode,
        "baseline_nominal_maximum_timestep": baseline_nominal_step,
        "babcs_nominal_maximum_timestep": babcs_nominal_step,
        "ngspice_nominal_maximum_timestep": ngspice_nominal_step,
        "same_nominal_maximum_timestep": math.isclose(
            babcs_nominal_step,
            ngspice_nominal_step,
            rel_tol=0.0,
            abs_tol=0.0,
        ),
        "babcs_stop_matches": (
            babcs_stop_time is not None
            and math.isclose(float(babcs_stop_time), float(simulation["stop_time"]), rel_tol=0.0, abs_tol=1.0e-12)
        ),
        "ngspice_stop_matches": (
            ngspice_stop_time is not None
            and math.isclose(
                float(ngspice_stop_time),
                float(simulation["stop_time"]),
                rel_tol=0.0,
                abs_tol=trace_time_tolerance(float(simulation["stop_time"])),
            )
        ),
        "source_tree_excluded": bool(
            first_payload.get("babcs", {}).get("source_tree_excluded", False)
        ),
        "babcs_backend_matches": (
            first_payload.get("babcs", {}).get("linear_backend") == babcs_backend
        ),
        "babcs_configuration_matches": (
            first_payload.get("babcs", {}).get("babcs_configuration")
            == asdict(babcs_config)
        ),
    }
    if first_payload and not all(
        semantic_equality[key]
        for key in (
            "case_hash_matches_worker",
            "state_order_matches",
            "babcs_stop_matches",
            "ngspice_stop_matches",
            "source_tree_excluded",
            "babcs_backend_matches",
            "babcs_configuration_matches",
        )
    ):
        status = "failed"
        failure_reasons.append("same-circuit or same-stop-time semantic equality failed")

    row = {
        "row_id": spec.row_id,
        "inventory": spec.inventory,
        "case_id": spec.case_id,
        "title": spec.title,
        "family_id": spec.family_id,
        "size": spec.size,
        "status": status,
        "failure_reason": "; ".join(str(value) for value in failure_reasons if value) or None,
        "case_sha256": sha256_file(spec.path),
        "netlist_sha256": sha256_bytes(netlist.encode()),
        "state_names": list(state_names),
        "circuit_size": circuit_size,
        "simulation": {
            **simulation,
            "baseline_nominal_step": baseline_nominal_step,
            "babcs_nominal_step": babcs_nominal_step,
            "ngspice_nominal_step": ngspice_nominal_step,
            "babcs_stop_time": babcs_stop_time,
            "ngspice_stop_time": ngspice_stop_time,
        },
        "semantic_equality": semantic_equality,
        "babcs_linear_backend": babcs_backend,
        "babcs_profile": babcs_profile,
        "profiles": {
            "babcs": (
                "installed-wheel "
                f"{babcs_profile['id']} "
                f"({babcs_backend})"
            ),
            "ngspice": "generated semantic netlist with rusage all",
        },
        "samples": {
            tool: [
                {key: value for key, value in sample.items() if key not in {"stdout", "stderr"}}
                for sample in timed if sample["tool"] == tool
            ]
            for tool in ("babcs", "ngspice")
        },
        "runtime": runtime,
        "memory": memory,
        "points": points,
        "solver_work": solver_work,
        "accuracy": accuracy,
        "accuracy_mode": accuracy_mode,
        "accuracy_sweep": accuracy_sweep,
        "source_wheel_equivalent": source_wheel_equivalent,
        "source_wheel_equivalence": source_wheel_evidence,
        "speedup_x": speedup,
    }
    return row, samples


def _failed_row_from_exception(
    spec: CaseSpec,
    error: Exception,
    *,
    babcs_backend: str,
    accuracy_mode: str,
) -> dict[str, Any]:
    circuit, simulation, _ = load_case(spec.path)
    return {
        "row_id": spec.row_id,
        "inventory": spec.inventory,
        "case_id": spec.case_id,
        "title": spec.title,
        "family_id": spec.family_id,
        "size": spec.size,
        "status": "failed",
        "failure_reason": f"unhandled row error: {type(error).__name__}: {error}",
        "case_sha256": sha256_file(spec.path),
        "netlist_sha256": None,
        "state_names": list(circuit.dynamic_names),
        "circuit_size": {
            "element_count": len(circuit.elements),
            "non_ground_node_count": len(circuit.nodes),
            "dynamic_state_count": circuit.dynamic_size,
            "algebraic_unknown_count": circuit.algebraic_size,
            "declared_mna_unknowns": circuit.dynamic_size + circuit.algebraic_size,
            "ngspice_circuit_equations": None,
        },
        "simulation": {
            **simulation,
            "babcs_stop_time": None,
            "ngspice_stop_time": None,
        },
        "semantic_equality": {},
        "babcs_linear_backend": babcs_backend,
        "accuracy_mode": accuracy_mode,
        "accuracy_sweep": None,
        "profiles": {
            "babcs": f"installed-wheel active bounded ({babcs_backend})",
            "ngspice": "generated semantic netlist with rusage all",
        },
        "samples": {"babcs": [], "ngspice": []},
        "runtime": {"babcs": None, "ngspice": None, "speedup_bootstrap_95": None},
        "memory": {"babcs": None, "ngspice": None},
        "points": {
            "babcs": {"accepted": None, "rejected": None, "output": None},
            "ngspice": {"accepted": None, "rejected": None, "output": None},
            "common_grid": None,
        },
        "solver_work": {"babcs": None, "ngspice": None},
        "accuracy": {
            "authority": None,
            "babcs": None,
            "ngspice": None,
            "direct_difference": None,
        },
        "source_wheel_equivalent": False,
        "source_wheel_equivalence": None,
        "speedup_x": None,
    }


def execute_runtime_benchmark(
    *,
    manifest_path: Path,
    external_manifest_path: Path,
    output_root: Path,
    profile_name: str,
    warmups: int | None,
    repeats: int | None,
    rounds: int | None,
    selected_case: str | None,
    ngspice_executable: str,
    cpu: int | None,
    timeout: float,
    overwrite: bool,
    publish_docs: bool,
    inventory: str = "all",
    babcs_backend: str | None = None,
    accuracy_mode: str | None = None,
) -> dict[str, Any]:
    if output_root.exists() and any(output_root.iterdir()):
        if not overwrite:
            raise FileExistsError(f"refusing to overwrite runtime benchmark evidence: {output_root}")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    logs_root = output_root / "logs"
    logs_root.mkdir(parents=True, exist_ok=True)
    checkpoints_root = output_root / "checkpoints"
    checkpoints_root.mkdir(parents=True, exist_ok=True)
    generate_runtime_cases(manifest_path, DEFAULT_OUTPUT_ROOT, check=True)
    manifest_data = load_runtime_manifest(manifest_path)
    resolved_babcs_backend = str(
        babcs_backend or manifest_data.get("babcs_linear_backend", "dense")
    )
    if resolved_babcs_backend not in {"dense", "scipy", "hybrid"}:
        raise RuntimeBenchmarkError(
            f"unsupported runtime BAB-CS backend: {resolved_babcs_backend}"
        )
    resolved_accuracy_mode = str(
        accuracy_mode or manifest_data.get("accuracy_mode", "fixed_config")
    )
    if resolved_accuracy_mode not in {"fixed_config", "fixed_accuracy"}:
        raise RuntimeBenchmarkError(
            f"unsupported runtime accuracy mode: {resolved_accuracy_mode}"
        )
    runtime_manifest, specs = _case_specs(
        manifest_path,
        external_manifest_path,
        profile_name,
        resolved_babcs_backend,
        resolved_accuracy_mode,
        selected_case,
        inventory,
    )
    profile = runtime_manifest["profiles"][profile_name]
    backend_profile = runtime_manifest.get("babcs_backend_profiles", {}).get(
        resolved_babcs_backend,
        {},
    )
    sparse_minimum_declared_mna_unknowns = int(
        backend_profile.get(
            "sparse_minimum_declared_mna_unknowns",
            HYBRID_SPARSE_MINIMUM_DECLARED_MNA_UNKNOWNS,
        )
    )
    resolved_warmups = int(profile["warmups"] if warmups is None else warmups)
    resolved_repeats = int(profile["repeats"] if repeats is None else repeats)
    resolved_rounds = int(profile["rounds"] if rounds is None else rounds)
    if min(resolved_warmups, resolved_repeats, resolved_rounds) < 0 or resolved_repeats == 0 or resolved_rounds == 0:
        raise RuntimeBenchmarkError("warmups may be zero; repeats and rounds must be positive")
    with tempfile.TemporaryDirectory(prefix="babcs-runtime-wheel-") as directory:
        wheel_python, wheel = build_isolated_wheel_environment(
            Path(directory),
            linear_backend=resolved_babcs_backend,
        )
        ngspice_path = shutil.which(ngspice_executable)
        if ngspice_path is None:
            raise RuntimeBenchmarkError(f"ngspice executable not found: {ngspice_executable}")
        environment = environment_metadata(
            REPOSITORY_ROOT,
            wheel=wheel,
            ngspice_executable=ngspice_path,
            cpu=cpu,
        )
        rows: list[dict[str, Any]] = []
        all_samples: list[dict[str, Any]] = []
        for spec in specs:
            case_babcs_backend = resolve_case_babcs_backend(
                spec,
                resolved_babcs_backend,
                sparse_minimum_declared_mna_unknowns=sparse_minimum_declared_mna_unknowns,
            )
            try:
                row, samples = _execute_case(
                    spec,
                    runtime_manifest=runtime_manifest,
                    wheel_python=wheel_python,
                    babcs_backend=case_babcs_backend,
                    accuracy_mode=resolved_accuracy_mode,
                    ngspice_executable=ngspice_path,
                    warmups=resolved_warmups,
                    repeats=resolved_repeats,
                    rounds=resolved_rounds,
                    cpu=cpu,
                    timeout=timeout,
                    logs_root=logs_root,
                )
            except Exception as error:
                row = _failed_row_from_exception(
                    spec,
                    error,
                    babcs_backend=case_babcs_backend,
                    accuracy_mode=resolved_accuracy_mode,
                )
                samples = []
            rows.append(row)
            all_samples.extend(samples)
            write_json(
                checkpoints_root / f"{spec.row_id}.json",
                {"row": row, "samples": samples},
            )
            print(
                json.dumps(
                    {"case": spec.case_id, "status": row["status"], "speedup_x": row["speedup_x"]},
                    sort_keys=True,
                ),
                flush=True,
            )
    configuration = {
        "profile": profile_name,
        "manifest": str(manifest_path),
        "external_manifest": str(external_manifest_path),
        "warmups": resolved_warmups,
        "repeats": resolved_repeats,
        "rounds": resolved_rounds,
        "cpu": cpu,
        "common_grid_samples": int(runtime_manifest["common_grid_samples"]),
        "accuracy": runtime_manifest["accuracy"],
        "accuracy_mode": resolved_accuracy_mode,
        "fixed_accuracy": (
            runtime_manifest["fixed_accuracy"]
            if resolved_accuracy_mode == "fixed_accuracy"
            else None
        ),
        "paired_order": "alternating BAB-CS/ngspice then ngspice/BAB-CS",
        "inventory": inventory,
        "babcs_linear_backend": resolved_babcs_backend,
        "babcs_backend_policy": {
            "requested": resolved_babcs_backend,
            "sparse_minimum_declared_mna_unknowns": (
                sparse_minimum_declared_mna_unknowns
                if resolved_babcs_backend == "hybrid"
                else None
            ),
        },
        "babcs_profiles": runtime_manifest["babcs_profiles"],
    }
    report = {
        "schema_version": 1,
        "environment": environment,
        "configuration": configuration,
        "rows": rows,
        "claim_boundary": runtime_manifest["claim_boundary"],
    }
    raw_samples = {
        "schema_version": 1,
        "environment": environment,
        "configuration": configuration,
        "samples": all_samples,
    }
    validate_runtime_report(report)
    write_json(output_root / "raw-samples.json", raw_samples)
    write_json(output_root / "matched-results.json", report)
    write_matched_csv(output_root / "matched-results.csv", report)
    write_solver_work_csv(output_root / "solver-work.csv", report)
    write_memory_csv(output_root / "memory.csv", report)
    write_speed_accuracy_svg(output_root / "speedup-accuracy-by-size.svg", report)
    write_memory_svg(output_root / "memory-by-size.svg", report)
    write_points_work_svg(output_root / "points-and-work-by-size.svg", report)
    write_markdown_report(output_root / "report.md", report)
    if publish_docs:
        write_markdown_report(
            REPOSITORY_ROOT / "docs" / "NGSPICE_RUNTIME_BENCHMARK.md",
            report,
            image_href="../artifacts/runtime/speedup-accuracy-by-size.svg",
        )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark BAB-CS and ngspice on matched same-machine circuit cases")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--external-manifest", default=str(DEFAULT_EXTERNAL_MANIFEST))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--profile", choices=("quick", "development", "publication"), default="development")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--warmups", type=int)
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--rounds", type=int)
    parser.add_argument("--case")
    parser.add_argument(
        "--inventory",
        choices=("all", "semantic_breadth", "size_scaling"),
        default="all",
    )
    parser.add_argument("--ngspice", default="ngspice")
    parser.add_argument(
        "--babcs-backend",
        choices=("dense", "scipy", "hybrid"),
        help="override the manifest BAB-CS linear backend for a named comparison profile",
    )
    parser.add_argument(
        "--accuracy-mode",
        choices=("fixed_config", "fixed_accuracy"),
        help="use one shared configuration or independently calibrate both tools to the common accuracy target",
    )
    parser.add_argument("--cpu", type=int)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--publish-docs", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    profile = "quick" if arguments.quick else arguments.profile
    report = execute_runtime_benchmark(
        manifest_path=Path(arguments.manifest).resolve(),
        external_manifest_path=Path(arguments.external_manifest).resolve(),
        output_root=Path(arguments.output_root).resolve(),
        profile_name=profile,
        warmups=arguments.warmups,
        repeats=arguments.repeats,
        rounds=arguments.rounds,
        selected_case=arguments.case,
        ngspice_executable=arguments.ngspice,
        cpu=arguments.cpu,
        timeout=arguments.timeout,
        overwrite=arguments.overwrite,
        publish_docs=arguments.publish_docs,
        inventory=arguments.inventory,
        babcs_backend=arguments.babcs_backend,
        accuracy_mode=arguments.accuracy_mode,
    )
    failures = sum(row["status"] != "success" for row in report["rows"])
    print(json.dumps({"rows": len(report["rows"]), "failures": failures, "output": str(Path(arguments.output_root).resolve())}, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
