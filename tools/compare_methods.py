from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import platform
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from babcs import BABCSConfig, BoundedAdamsBashforthIntegrator, Simulator
from babcs.io import load_case, summary_data
from tests.support.analytic import driven_rc_voltage, parallel_rlc_state, rc_voltage, rl_current
from tests.support.metrics import error_metrics, estimated_period, interpolate_trace, observed_order
from tests.support.raw_ab2 import RawAB2Point, integrate_raw_ab2


SCHEMA_VERSION = 1
SUPPORTED_METHODS = {
    "backward_euler",
    "trapezoidal",
    "bdf2",
    "shadow",
    "active",
    "raw_ab2",
    "bounded_explicit_euler",
    "bounded_heun",
    "bounded_rk23",
    "bounded_backward_euler",
    "bounded_trapezoidal",
    "bounded_bdf2",
    "bounded_ab2_fast",
    "bounded_heun_fast",
    "bounded_rk23_fast",
}
IMPLICIT_METHODS = {"backward_euler", "trapezoidal", "bdf2"}
BOUNDED_CANDIDATES = {
    "bounded_explicit_euler": ("explicit_euler", "trapezoidal", 1),
    "bounded_heun": ("heun", "trapezoidal", 1),
    "bounded_rk23": ("rk23", "trapezoidal", 1),
    "bounded_backward_euler": ("backward_euler", "trapezoidal", 1),
    "bounded_trapezoidal": ("trapezoidal", "bdf2", 1),
    "bounded_bdf2": ("bdf2", "trapezoidal", 1),
    "bounded_ab2_fast": ("ab2", "trapezoidal", 4),
    "bounded_heun_fast": ("heun", "trapezoidal", 4),
    "bounded_rk23_fast": ("rk23", "trapezoidal", 4),
}
SOURCE_HASH_EXCLUDED_PATHS = {
    "docs/PERFORMANCE_OPTIMIZATION_AUDIT.md",
    "docs/TESTS_AND_COMPARISONS_AUDIT.md",
}
SOURCE_HASH_EXCLUDED_PREFIXES = ("artifacts/", "build/", "dist/")


class ComparisonConfigurationError(ValueError):
    pass


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ComparisonConfigurationError("comparison manifest must be a JSON object")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ComparisonConfigurationError(
            f"unsupported comparison manifest schema: {data.get('schema_version')!r}"
        )
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ComparisonConfigurationError("comparison manifest requires a nonempty cases list")
    seen_ids: set[str] = set()
    for case in cases:
        _validate_case(case, manifest_path.parent, seen_ids)
    return data


def execute_manifest(
    manifest_path: str | Path,
    *,
    selected_cases: set[str] | None = None,
    quick: bool = False,
    timing_repeats: int = 0,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    path = Path(manifest_path)
    manifest = load_manifest(path)
    if timing_repeats < 0:
        raise ComparisonConfigurationError("timing_repeats must be non-negative")

    available_ids = {str(case["id"]) for case in manifest["cases"]}
    if selected_cases:
        missing = sorted(selected_cases - available_ids)
        if missing:
            raise ComparisonConfigurationError(f"unknown comparison cases: {', '.join(missing)}")

    source = source_metadata(REPOSITORY_ROOT)
    numerical_results: list[dict[str, Any]] = []
    timing_results: list[dict[str, Any]] = []
    selected = [
        case
        for case in manifest["cases"]
        if selected_cases is None or str(case["id"]) in selected_cases
    ]
    if quick and selected_cases is None:
        selected = selected[:1]
    case_evidence = [_case_evidence(case, path.parent) for case in selected]

    for case in selected:
        case_results, case_timing = _execute_case(
            case,
            path.parent,
            sample_count=int(manifest.get("sample_count", 100)),
            quick=quick,
            timing_repeats=timing_repeats,
        )
        numerical_results.extend(case_results)
        timing_results.extend(case_timing)

    numerical = {
        "schema_version": SCHEMA_VERSION,
        "manifest_sha256": _sha256_file(path),
        "source": source,
        "environment": environment_metadata(),
        "runner": {
            "path": "tools/compare_methods.py",
            "manifest": path.name,
            "quick": quick,
        },
        "cases": case_evidence,
        "authority_note": (
            "Errors are relative to the authority declared per case. Internal BAB-CS bounds remain "
            "reference-relative diagnostics, not unconditional exact-trajectory proofs."
        ),
        "results": numerical_results,
        "analyses": _analysis_data(
            numerical_results,
            accuracy_targets=[float(value) for value in manifest.get("accuracy_targets", [])],
            work_budgets=[int(value) for value in manifest.get("work_budgets", [])],
        ),
    }
    timing = None
    if timing_repeats:
        timing = {
            "schema_version": SCHEMA_VERSION,
            "source": source,
            "environment": environment_metadata(),
            "timing_repeats": timing_repeats,
            "results": timing_results,
            "acceptance_note": "Wall-clock measurements are informational and are not CI correctness gates.",
        }
    return numerical, timing


def write_report(path: str | Path, data: dict[str, Any], *, overwrite: bool = False) -> None:
    output = Path(path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing comparison evidence: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_csv_report(path: str | Path, report: dict[str, Any], *, overwrite: bool = False) -> None:
    output = _prepare_output(path, overwrite)
    columns = (
        "case_id",
        "method",
        "nominal_step",
        "anchor_interval",
        "authority_type",
        "final_state_maximum_absolute_error",
        "maximum_absolute_error",
        "rms_absolute_error",
        "deterministic_work_units",
        "accepted_steps",
        "rejected_steps",
        "implicit_fallbacks",
        "periodic_reanchors",
        "safety_reanchors",
        "maximum_estimated_bound",
        "maximum_anchor_reference_error",
        "maximum_empirical_anchor_error_to_pre_reset_bound",
        "relative_amplitude_error",
        "final_phase_error_radians",
        "relative_period_error",
        "relative_energy_span",
    )
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for result in report["results"]:
            oscillator = result["oscillator"] or {}
            writer.writerow(
                {
                    "case_id": result["case_id"],
                    "method": result["method"],
                    "nominal_step": result["nominal_step"],
                    "anchor_interval": result["anchor_interval"],
                    "authority_type": result["authority"]["type"],
                    "final_state_maximum_absolute_error": result["accuracy"][
                        "final_state_maximum_absolute_error"
                    ],
                    "maximum_absolute_error": result["accuracy"]["maximum_absolute_error"],
                    "rms_absolute_error": result["accuracy"]["rms_absolute_error"],
                    "deterministic_work_units": result["work"]["deterministic_work_units"],
                    "accepted_steps": result["diagnostics"]["accepted_steps"],
                    "rejected_steps": result["diagnostics"]["rejected_steps"],
                    "implicit_fallbacks": result["diagnostics"]["implicit_fallbacks"],
                    "periodic_reanchors": result["diagnostics"]["periodic_reanchors"],
                    "safety_reanchors": result["diagnostics"]["safety_reanchors"],
                    "maximum_estimated_bound": result["bound"]["maximum_estimated_bound"],
                    "maximum_anchor_reference_error": result["bound"][
                        "maximum_anchor_reference_error"
                    ],
                    "maximum_empirical_anchor_error_to_pre_reset_bound": result["bound"][
                        "maximum_empirical_anchor_error_to_pre_reset_bound"
                    ],
                    "relative_amplitude_error": oscillator.get("relative_amplitude_error"),
                    "final_phase_error_radians": oscillator.get("final_phase_error_radians"),
                    "relative_period_error": oscillator.get("relative_period_error"),
                    "relative_energy_span": oscillator.get("relative_energy_span"),
                }
            )


def write_svg_plot(path: str | Path, report: dict[str, Any], *, overwrite: bool = False) -> None:
    output = _prepare_output(path, overwrite)
    results_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in report["results"]:
        results_by_case[result["case_id"]].append(result)
    cases = sorted(results_by_case)
    panel_height = 250
    width = 1200
    height = 60 + panel_height * len(cases)
    colors = {
        "backward_euler": "#8c564b",
        "trapezoidal": "#1f77b4",
        "bdf2": "#9467bd",
        "shadow": "#7f7f7f",
        "active": "#2ca02c",
        "raw_ab2": "#d62728",
        "bounded_explicit_euler": "#ff9896",
        "bounded_heun": "#17becf",
        "bounded_rk23": "#00a6a6",
        "bounded_backward_euler": "#c49c94",
        "bounded_trapezoidal": "#6baed6",
        "bounded_bdf2": "#bcbddc",
        "bounded_ab2_fast": "#98df8a",
        "bounded_heun_fast": "#9edae5",
        "bounded_rk23_fast": "#008b8b",
    }
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="30" y="30" font-family="sans-serif" font-size="20">BAB-CS maximum absolute error by timestep</text>',
    ]
    for panel_index, case_id in enumerate(cases):
        panel_results = results_by_case[case_id]
        left = 90
        right = width - 40
        top = 60 + panel_index * panel_height
        bottom = top + panel_height - 55
        x_values = [math.log10(result["nominal_step"]) for result in panel_results]
        y_values = [
            math.log10(max(result["accuracy"]["maximum_absolute_error"], 1.0e-300))
            for result in panel_results
        ]
        x_min, x_max = _expanded_range(min(x_values), max(x_values))
        y_min, y_max = _expanded_range(min(y_values), max(y_values))

        def x_coordinate(value: float) -> float:
            return left + (value - x_min) / (x_max - x_min) * (right - left)

        def y_coordinate(value: float) -> float:
            return bottom - (value - y_min) / (y_max - y_min) * (bottom - top)

        lines.extend(
            [
                f'<text x="30" y="{top + 15}" font-family="sans-serif" font-size="16">{html.escape(case_id)}</text>',
                f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#333"/>',
                f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#333"/>',
                f'<text x="{left}" y="{bottom + 35}" font-family="sans-serif" font-size="11">log10 timestep: {x_min:.3g} to {x_max:.3g}</text>',
                f'<text x="{right - 250}" y="{bottom + 35}" font-family="sans-serif" font-size="11">log10 max error: {y_min:.3g} to {y_max:.3g}</text>',
            ]
        )
        grouped: dict[tuple[str, int | None], list[dict[str, Any]]] = defaultdict(list)
        for result in panel_results:
            grouped[(result["method"], result["anchor_interval"])].append(result)
        for (method, anchor_interval), group in sorted(grouped.items()):
            ordered = sorted(group, key=lambda result: result["nominal_step"])
            points = " ".join(
                f"{x_coordinate(math.log10(result['nominal_step'])):.3f},{y_coordinate(math.log10(max(result['accuracy']['maximum_absolute_error'], 1.0e-300))):.3f}"
                for result in ordered
            )
            color = colors.get(method, "#000000")
            label = method if anchor_interval is None else f"{method}/a{anchor_interval}"
            lines.append(
                f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2"><title>{html.escape(label)}</title></polyline>'
            )
            for result in ordered:
                x_value = x_coordinate(math.log10(result["nominal_step"]))
                y_value = y_coordinate(
                    math.log10(max(result["accuracy"]["maximum_absolute_error"], 1.0e-300))
                )
                lines.append(
                    f'<circle cx="{x_value:.3f}" cy="{y_value:.3f}" r="3" fill="{color}"><title>{html.escape(label)}</title></circle>'
                )
    lines.append("</svg>\n")
    output.write_text("\n".join(lines), encoding="utf-8")


def _validate_case(case: object, manifest_root: Path, seen_ids: set[str]) -> None:
    if not isinstance(case, dict):
        raise ComparisonConfigurationError("each comparison case must be an object")
    case_id = str(case.get("id", ""))
    if not case_id:
        raise ComparisonConfigurationError("comparison case id must not be empty")
    if case_id in seen_ids:
        raise ComparisonConfigurationError(f"duplicate comparison case id: {case_id}")
    seen_ids.add(case_id)
    input_value = case.get("input")
    if not isinstance(input_value, str) or not (manifest_root / input_value).is_file():
        raise ComparisonConfigurationError(f"{case_id}: comparison input does not exist")
    methods = case.get("methods")
    if not isinstance(methods, list) or not methods:
        raise ComparisonConfigurationError(f"{case_id}: methods must be a nonempty list")
    unknown_methods = sorted(set(map(str, methods)) - SUPPORTED_METHODS)
    if unknown_methods:
        raise ComparisonConfigurationError(
            f"{case_id}: unsupported methods: {', '.join(unknown_methods)}"
        )
    if "raw_ab2" in methods and not isinstance(case.get("raw_model"), dict):
        raise ComparisonConfigurationError(f"{case_id}: raw_ab2 requires raw_model")
    steps = case.get("nominal_steps")
    if not isinstance(steps, list) or not steps or any(float(value) <= 0.0 for value in steps):
        raise ComparisonConfigurationError(f"{case_id}: nominal_steps must be positive")
    indices = case.get("state_indices")
    if not isinstance(indices, list) or not indices or any(int(value) < 0 for value in indices):
        raise ComparisonConfigurationError(f"{case_id}: state_indices must be non-negative")
    authority = case.get("authority")
    if not isinstance(authority, dict) or authority.get("type") not in {
        "analytic",
        "refined_replay",
    }:
        raise ComparisonConfigurationError(f"{case_id}: unsupported authority")
    intervals = case.get("anchor_intervals", [16])
    if not isinstance(intervals, list) or not intervals or any(int(value) < 1 for value in intervals):
        raise ComparisonConfigurationError(f"{case_id}: anchor_intervals must be positive")


def _execute_case(
    case: dict[str, Any],
    manifest_root: Path,
    *,
    sample_count: int,
    quick: bool,
    timing_repeats: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    case_id = str(case["id"])
    input_path = manifest_root / str(case["input"])
    circuit, simulation, config = load_case(input_path)
    state_indices = [int(value) for value in case["state_indices"]]
    if any(index >= circuit.dynamic_size for index in state_indices):
        raise ComparisonConfigurationError(f"{case_id}: state index exceeds circuit dimension")
    sample_times = _sample_times(
        simulation["start_time"],
        simulation["stop_time"],
        max(2, sample_count),
    )
    authority_values = _authority_values(
        case,
        circuit,
        simulation,
        config,
        state_indices,
        sample_times,
    )
    steps = [float(value) for value in case["nominal_steps"]]
    if quick:
        steps = steps[:2]
    methods = [str(value) for value in case["methods"]]
    intervals = [int(value) for value in case.get("anchor_intervals", [config.anchor_interval_steps])]
    numerical_results: list[dict[str, Any]] = []
    timing_results: list[dict[str, Any]] = []

    for method in methods:
        method_intervals: list[int | None] = intervals if method in {"active", "shadow"} else [None]
        for anchor_interval in method_intervals:
            for nominal_step in steps:
                durations: list[float] = []
                start = time.perf_counter()
                execution = _execute_method(
                    case,
                    circuit,
                    simulation,
                    config,
                    method,
                    nominal_step,
                    anchor_interval,
                )
                durations.append(time.perf_counter() - start)
                for _ in range(max(0, timing_repeats - 1)):
                    start = time.perf_counter()
                    _execute_method(
                        case,
                        circuit,
                        simulation,
                        config,
                        method,
                        nominal_step,
                        anchor_interval,
                    )
                    durations.append(time.perf_counter() - start)

                result = _comparison_result(
                    case,
                    execution,
                    method,
                    nominal_step,
                    anchor_interval,
                    state_indices,
                    sample_times,
                    authority_values,
                )
                numerical_results.append(result)
                if timing_repeats:
                    timing_results.append(
                        {
                            "case_id": case_id,
                            "method": method,
                            "nominal_step": nominal_step,
                            "anchor_interval": anchor_interval,
                            "median_seconds": statistics.median(durations),
                            "minimum_seconds": min(durations),
                            "maximum_seconds": max(durations),
                        }
                    )
    return numerical_results, timing_results


def _authority_values(
    case: dict[str, Any],
    circuit,
    simulation: dict[str, float],
    config: BABCSConfig,
    state_indices: list[int],
    sample_times: tuple[float, ...],
) -> dict[int, tuple[float, ...]]:
    authority = case["authority"]
    authority_type = authority["type"]
    if authority_type == "analytic":
        return {
            index: tuple(_analytic_state(authority, time)[index] for time in sample_times)
            for index in state_indices
        }
    if authority_type == "refined_replay":
        reference_method = str(authority.get("method", "trapezoidal"))
        reference_step = float(authority["maximum_step"])
        reference_config = replace(
            config,
            rollout_mode="disabled",
            reference_method=reference_method,
            anchor_interval_steps=1_000_000_000,
        )
        reference = Simulator(BoundedAdamsBashforthIntegrator(reference_config)).run(
            circuit,
            simulation["stop_time"],
            reference_step,
            start_time=simulation["start_time"],
        )
        return {
            index: tuple(interpolate_trace(reference.dynamic_trace(index), time) for time in sample_times)
            for index in state_indices
        }
    raise AssertionError("validated authority is unreachable")


def _execute_method(
    case: dict[str, Any],
    circuit,
    simulation: dict[str, float],
    config: BABCSConfig,
    method: str,
    nominal_step: float,
    anchor_interval: int | None,
) -> dict[str, Any]:
    if method == "raw_ab2":
        derivative = _raw_derivative(case["raw_model"])
        points = integrate_raw_ab2(
            derivative,
            circuit.initial_dynamic_state(),
            simulation["stop_time"],
            nominal_step,
            start_time=simulation["start_time"],
        )
        return {
            "kind": "raw",
            "points": points,
            "configuration": {
                "rollout_mode": "test_only_raw_ab2",
                "nominal_step": nominal_step,
            },
        }

    if method in IMPLICIT_METHODS:
        run_config = replace(
            config,
            rollout_mode="disabled",
            reference_method=method,
            anchor_interval_steps=1_000_000_000,
        )
    elif method in BOUNDED_CANDIDATES:
        candidate_method, reference_method, reference_interval_steps = BOUNDED_CANDIDATES[method]
        run_config = replace(
            config,
            rollout_mode="active",
            candidate_method=candidate_method,
            reference_method=reference_method,
            reference_interval_steps=reference_interval_steps,
            embedded_error_cap=max(
                config.embedded_error_cap,
                config.predictor_reference_cap,
            ),
            anchor_interval_steps=(
                config.anchor_interval_steps if anchor_interval is None else anchor_interval
            ),
        )
    else:
        run_config = replace(
            config,
            rollout_mode=method,
            anchor_interval_steps=(
                config.anchor_interval_steps if anchor_interval is None else anchor_interval
            ),
        )
    result = Simulator(BoundedAdamsBashforthIntegrator(run_config)).run(
        circuit,
        simulation["stop_time"],
        nominal_step,
        start_time=simulation["start_time"],
    )
    return {"kind": "babcs", "result": result, "configuration": asdict(run_config)}


def _comparison_result(
    case: dict[str, Any],
    execution: dict[str, Any],
    method: str,
    nominal_step: float,
    anchor_interval: int | None,
    state_indices: list[int],
    sample_times: tuple[float, ...],
    authority_values: dict[int, tuple[float, ...]],
) -> dict[str, Any]:
    actual_values: dict[int, tuple[float, ...]] = {}
    if execution["kind"] == "raw":
        points: tuple[RawAB2Point, ...] = execution["points"]
        for index in state_indices:
            trace = tuple((point.time, point.state[index]) for point in points)
            actual_values[index] = tuple(interpolate_trace(trace, time) for time in sample_times)
        diagnostics = _raw_summary(points)
        native_voltage_trace = tuple((point.time, point.state[state_indices[0]]) for point in points)
        raw_points = points
    else:
        result = execution["result"]
        for index in state_indices:
            actual_values[index] = tuple(
                interpolate_trace(result.dynamic_trace(index), time) for time in sample_times
            )
        diagnostics = summary_data(result)
        native_voltage_trace = result.dynamic_trace(state_indices[0])
        raw_points = None

    per_state: dict[str, dict[str, float]] = {}
    all_differences: list[float] = []
    final_differences: list[float] = []
    for index in state_indices:
        metrics = error_metrics(actual_values[index], authority_values[index])
        per_state[str(index)] = metrics
        differences = [
            actual - expected
            for actual, expected in zip(actual_values[index], authority_values[index], strict=True)
        ]
        all_differences.extend(differences)
        final_differences.append(differences[-1])
    accuracy = {
        "per_state": per_state,
        "final_state_maximum_absolute_error": max(abs(value) for value in final_differences),
        "maximum_absolute_error": max(abs(value) for value in all_differences),
        "rms_absolute_error": math.sqrt(
            sum(value * value for value in all_differences) / len(all_differences)
        ),
    }
    work = _work_data(diagnostics)
    bound = _bound_data(execution)
    primary_index = state_indices[0]
    oscillator = _oscillator_data(
        case,
        execution,
        native_voltage_trace,
        actual_values,
        authority_values,
        state_indices,
        raw_points,
    )
    return {
        "case_id": str(case["id"]),
        "method": method,
        "nominal_step": nominal_step,
        "anchor_interval": anchor_interval,
        "authority": case["authority"],
        "configuration": execution["configuration"],
        "accuracy": accuracy,
        "bound": bound,
        "diagnostics": diagnostics,
        "work": work,
        "oscillator": oscillator,
    }


def _analytic_state(authority: dict[str, Any], time: float) -> tuple[float, ...]:
    model = authority["model"]
    parameters = _numeric_parameters(authority.get("parameters", {}))
    if model == "rc":
        return (rc_voltage(time, **parameters),)
    if model == "rl":
        return (rl_current(time, **parameters),)
    if model == "parallel_rlc":
        return parallel_rlc_state(time, **parameters)
    if model == "driven_rc":
        return (driven_rc_voltage(time, **parameters),)
    raise ComparisonConfigurationError(f"unsupported analytic model: {model}")


def _raw_derivative(raw_model: dict[str, Any]):
    model = raw_model["model"]
    parameters = _numeric_parameters(raw_model.get("parameters", {}))
    if model == "rc":
        resistance = parameters["resistance"]
        capacitance = parameters["capacitance"]
        source_voltage = parameters["source_voltage"]
        return lambda time, state: ((source_voltage - state[0]) / (resistance * capacitance),)
    if model == "rl":
        resistance = parameters["resistance"]
        inductance = parameters["inductance"]
        source_voltage = parameters["source_voltage"]
        return lambda time, state: ((source_voltage - resistance * state[0]) / inductance,)
    if model == "parallel_rlc":
        resistance = parameters["resistance"]
        capacitance = parameters["capacitance"]
        inductance = parameters["inductance"]
        conductance = 0.0 if math.isinf(resistance) else 1.0 / resistance
        return lambda time, state: (
            -(state[1] + conductance * state[0]) / capacitance,
            state[0] / inductance,
        )
    raise ComparisonConfigurationError(f"unsupported raw AB2 model: {model}")


def _numeric_parameters(parameters: dict[str, Any]) -> dict[str, float]:
    return {
        key: math.inf if value == "inf" else float(value)
        for key, value in parameters.items()
    }


def _raw_summary(points: tuple[RawAB2Point, ...]) -> dict[str, Any]:
    steps = [right.time - left.time for left, right in zip(points, points[1:])]
    return {
        "points": len(points),
        "start_time": points[0].time,
        "stop_time": points[-1].time,
        "accepted_steps": len(points) - 1,
        "rejected_steps": 0,
        "periodic_reanchors": 0,
        "safety_reanchors": 0,
        "implicit_fallbacks": 0,
        "history_generation": 0,
        "minimum_accepted_step": min(steps, default=0.0),
        "maximum_accepted_step": max(steps, default=0.0),
        "mean_accepted_step": sum(steps) / len(steps) if steps else 0.0,
        "contractive_steps": 0,
        "candidate_steps": 0,
        "dynamic_reference_checkpoints": 0,
        "ab_steps": max(0, len(points) - 2),
        "candidate_solves": 0,
        "candidate_iterations": 0,
        "candidate_circuit_evaluations": 0,
        "candidate_algebraic_iterations": 0,
        "reference_solves": 0,
        "reference_iterations": 0,
        "reference_circuit_evaluations": 0,
        "reference_algebraic_iterations": 0,
        "explicit_projections": 0,
        "predictor_projection_iterations": 0,
        "corrected_projection_iterations": 0,
        "differential_jacobian_evaluations": 0,
        "replay_steps": 0,
        "replay_reference_iterations": 0,
        "replay_circuit_evaluations": 0,
        "replay_algebraic_iterations": 0,
        "rejection_reasons": {},
        "history_resets": {},
    }


def _work_data(diagnostics: dict[str, Any]) -> dict[str, int]:
    names = (
        "accepted_steps",
        "candidate_solves",
        "candidate_iterations",
        "candidate_circuit_evaluations",
        "candidate_algebraic_iterations",
        "reference_solves",
        "reference_iterations",
        "reference_circuit_evaluations",
        "reference_algebraic_iterations",
        "explicit_projections",
        "predictor_projection_iterations",
        "corrected_projection_iterations",
        "differential_jacobian_evaluations",
        "replay_steps",
        "replay_reference_iterations",
        "replay_circuit_evaluations",
        "replay_algebraic_iterations",
    )
    work = {name: int(diagnostics.get(name, 0)) for name in names}
    aggregate_names = (
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
    return {
        "deterministic_work_units": sum(work[name] for name in aggregate_names),
        **work,
    }


def _bound_data(execution: dict[str, Any]) -> dict[str, Any]:
    if execution["kind"] == "raw":
        return {
            "authority": "none",
            "maximum_estimated_bound": None,
            "maximum_anchor_reference_error": None,
            "maximum_empirical_anchor_error_to_pre_reset_bound": None,
            "anchor_ratio_samples": 0,
        }
    result = execution["result"]
    ratios = []
    for point in result.points:
        metrics = point.metrics
        if metrics is None or not metrics.periodic_reanchor:
            continue
        if metrics.pre_reset_estimated_bound > 0.0:
            ratios.append(metrics.anchor_reference_error / metrics.pre_reset_estimated_bound)
    diagnostics = summary_data(result)
    return {
        "authority": "internal_reference_and_independent_replay",
        "maximum_estimated_bound": diagnostics["maximum_estimated_bound"],
        "maximum_anchor_reference_error": diagnostics["maximum_anchor_reference_error"],
        "maximum_empirical_anchor_error_to_pre_reset_bound": max(ratios, default=None),
        "anchor_ratio_samples": len(ratios),
    }


def _oscillator_data(
    case: dict[str, Any],
    execution: dict[str, Any],
    voltage_trace,
    sampled_values: dict[int, tuple[float, ...]],
    authority_values: dict[int, tuple[float, ...]],
    state_indices: list[int],
    raw_points: tuple[RawAB2Point, ...] | None,
) -> dict[str, float] | None:
    oscillator = case.get("oscillator")
    if not isinstance(oscillator, dict):
        return None
    expected_period = float(oscillator["period"])
    measured_period = estimated_period(voltage_trace)
    capacitance = float(oscillator["capacitance"])
    inductance = float(oscillator["inductance"])
    if execution["kind"] == "raw":
        assert raw_points is not None
        energies = [
            0.5 * capacitance * point.state[0] ** 2
            + 0.5 * inductance * point.state[1] ** 2
            for point in raw_points
        ]
    else:
        energies = [point.state.evaluation.stored_energy for point in execution["result"].points]
    primary_index = state_indices[0]
    sampled_voltage = sampled_values[primary_index]
    authority_voltage = authority_values[primary_index]
    measured_amplitude = 0.5 * (max(sampled_voltage) - min(sampled_voltage))
    authority_amplitude = 0.5 * (max(authority_voltage) - min(authority_voltage))
    phase_error = 0.0
    if len(state_indices) >= 2:
        current_index = state_indices[1]
        phase_scale = math.sqrt(inductance / capacitance)
        measured_phase = math.atan2(
            sampled_values[current_index][-1] * phase_scale,
            sampled_voltage[-1],
        )
        authority_phase = math.atan2(
            authority_values[current_index][-1] * phase_scale,
            authority_voltage[-1],
        )
        phase_error = abs(
            math.atan2(
                math.sin(measured_phase - authority_phase),
                math.cos(measured_phase - authority_phase),
            )
        )
    return {
        "measured_amplitude": measured_amplitude,
        "authority_amplitude": authority_amplitude,
        "relative_amplitude_error": abs(measured_amplitude - authority_amplitude)
        / max(authority_amplitude, 1.0e-300),
        "final_phase_error_radians": phase_error,
        "measured_period": measured_period,
        "relative_period_error": abs(measured_period - expected_period) / expected_period,
        "relative_energy_span": (max(energies) - min(energies)) / energies[0],
    }


def _analysis_data(
    results: list[dict[str, Any]],
    *,
    accuracy_targets: list[float],
    work_budgets: list[int],
) -> dict[str, Any]:
    grouped: dict[tuple[str, str, int | None], list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[(result["case_id"], result["method"], result["anchor_interval"])].append(result)

    convergence = []
    fixed_accuracy = []
    fixed_work = []
    for (case_id, method, anchor_interval), group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda item: item["nominal_step"], reverse=True)
        orders = []
        for coarse, fine in zip(ordered, ordered[1:]):
            coarse_error = coarse["accuracy"]["maximum_absolute_error"]
            fine_error = fine["accuracy"]["maximum_absolute_error"]
            ratio = coarse["nominal_step"] / fine["nominal_step"]
            if coarse_error > 0.0 and fine_error > 0.0 and ratio > 1.0:
                orders.append(
                    {
                        "coarse_step": coarse["nominal_step"],
                        "fine_step": fine["nominal_step"],
                        "observed_order": observed_order(coarse_error, fine_error, ratio),
                    }
                )
        convergence.append(
            {
                "case_id": case_id,
                "method": method,
                "anchor_interval": anchor_interval,
                "orders": orders,
            }
        )
        for target in accuracy_targets:
            eligible = [
                result
                for result in group
                if result["accuracy"]["maximum_absolute_error"] <= target
            ]
            selected = min(
                eligible,
                key=lambda item: item["work"]["deterministic_work_units"],
                default=None,
            )
            fixed_accuracy.append(
                {
                    "case_id": case_id,
                    "method": method,
                    "anchor_interval": anchor_interval,
                    "accuracy_target": target,
                    "selected_nominal_step": None if selected is None else selected["nominal_step"],
                    "deterministic_work_units": (
                        None if selected is None else selected["work"]["deterministic_work_units"]
                    ),
                }
            )
        for budget in work_budgets:
            eligible = [
                result
                for result in group
                if result["work"]["deterministic_work_units"] <= budget
            ]
            selected = min(
                eligible,
                key=lambda item: item["accuracy"]["maximum_absolute_error"],
                default=None,
            )
            fixed_work.append(
                {
                    "case_id": case_id,
                    "method": method,
                    "anchor_interval": anchor_interval,
                    "work_budget": budget,
                    "selected_nominal_step": None if selected is None else selected["nominal_step"],
                    "maximum_absolute_error": (
                        None if selected is None else selected["accuracy"]["maximum_absolute_error"]
                    ),
                }
            )
    return {
        "convergence": convergence,
        "fixed_accuracy": fixed_accuracy,
        "fixed_work": fixed_work,
    }


def _sample_times(start_time: float, stop_time: float, count: int) -> tuple[float, ...]:
    return tuple(
        stop_time if index == count else start_time + (stop_time - start_time) * index / count
        for index in range(count + 1)
    )


def _case_evidence(case: dict[str, Any], manifest_root: Path) -> dict[str, Any]:
    input_path = manifest_root / str(case["input"])
    input_data = json.loads(input_path.read_text(encoding="utf-8"))
    return {
        "id": str(case["id"]),
        "input": str(case["input"]),
        "input_sha256": _sha256_file(input_path),
        "elements": input_data["elements"],
        "simulation": input_data["simulation"],
        "base_babcs_configuration": input_data.get("babcs", {}),
        "authority": case["authority"],
        "state_indices": case["state_indices"],
    }


def _expanded_range(minimum: float, maximum: float) -> tuple[float, float]:
    if minimum == maximum:
        return minimum - 0.5, maximum + 0.5
    padding = 0.05 * (maximum - minimum)
    return minimum - padding, maximum + padding


def _prepare_output(path: str | Path, overwrite: bool) -> Path:
    output = Path(path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing comparison evidence: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def environment_metadata() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
    }


def source_metadata(repository_root: Path) -> dict[str, Any]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = _source_scope_dirty(repository_root)
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
        dirty = True
    source_files = _source_files(repository_root)
    digest = hashlib.sha256()
    for relative_path in source_files:
        path = repository_root / relative_path
        encoded_path = relative_path.as_posix().encode("utf-8")
        payload = path.read_bytes()
        mode = path.stat().st_mode & 0o777
        digest.update(len(encoded_path).to_bytes(8, "big"))
        digest.update(encoded_path)
        digest.update(mode.to_bytes(4, "big"))
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return {
        "commit": commit,
        "dirty": dirty,
        "source_tree_sha256": digest.hexdigest(),
        "source_file_count": len(source_files),
        "source_tree_scope": (
            "Git tracked and untracked non-ignored files, excluding generated build/evidence "
            "directories and evidence-only audit documents."
        ),
    }


def _source_scope_dirty(repository_root: Path) -> bool:
    tracked = subprocess.run(
        ["git", "diff", "--name-only", "-z", "HEAD", "--"],
        cwd=repository_root,
        check=True,
        capture_output=True,
    ).stdout
    untracked = subprocess.run(
        ["git", "ls-files", "-z", "--others", "--exclude-standard"],
        cwd=repository_root,
        check=True,
        capture_output=True,
    ).stdout
    return any(
        _include_source_path(Path(value.decode("utf-8")))
        for value in (*tracked.split(b"\0"), *untracked.split(b"\0"))
        if value
    )


def _source_files(repository_root: Path) -> tuple[Path, ...]:
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=repository_root,
            check=True,
            capture_output=True,
        )
        candidates = (
            Path(value.decode("utf-8"))
            for value in completed.stdout.split(b"\0")
            if value
        )
    except (OSError, subprocess.CalledProcessError):
        candidates = (
            path.relative_to(repository_root)
            for path in repository_root.rglob("*")
            if path.is_file()
        )
    return tuple(
        sorted(
            relative_path
            for relative_path in candidates
            if _include_source_path(relative_path)
            and (repository_root / relative_path).is_file()
        )
    )


def _include_source_path(relative_path: Path) -> bool:
    value = relative_path.as_posix()
    if value in SOURCE_HASH_EXCLUDED_PATHS:
        return False
    if value.startswith(SOURCE_HASH_EXCLUDED_PREFIXES):
        return False
    if relative_path.suffix in {".pyc", ".pyo"}:
        return False
    return not any(
        part in {".git", ".mypy_cache", ".pytest_cache", ".venv", "__pycache__", "venv"}
        or part.endswith(".egg-info")
        for part in relative_path.parts
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run deterministic BAB-CS method comparisons")
    parser.add_argument("--manifest", default="benchmarks/manifest.json")
    parser.add_argument("--case", action="append", dest="cases")
    parser.add_argument("--output", required=True)
    parser.add_argument("--csv-output")
    parser.add_argument("--plot-output")
    parser.add_argument("--timing-output")
    parser.add_argument("--timing-repeats", type=int, default=0)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.timing_repeats and not arguments.timing_output:
        raise ComparisonConfigurationError("--timing-repeats requires --timing-output")
    numerical, timing = execute_manifest(
        arguments.manifest,
        selected_cases=set(arguments.cases) if arguments.cases else None,
        quick=arguments.quick,
        timing_repeats=arguments.timing_repeats,
    )
    write_report(arguments.output, numerical, overwrite=arguments.overwrite)
    if arguments.csv_output:
        write_csv_report(arguments.csv_output, numerical, overwrite=arguments.overwrite)
    if arguments.plot_output:
        write_svg_plot(arguments.plot_output, numerical, overwrite=arguments.overwrite)
    if timing is not None:
        assert arguments.timing_output is not None
        write_report(arguments.timing_output, timing, overwrite=arguments.overwrite)
    print(
        json.dumps(
            {
                "cases": len({result["case_id"] for result in numerical["results"]}),
                "results": len(numerical["results"]),
                "output": str(arguments.output),
                "timing_output": arguments.timing_output,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
