from __future__ import annotations

import bisect
import csv
import hashlib
import html
import json
import math
import os
import platform
import random
import re
import shutil
import statistics
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Sequence

from babcs import BoundedIntegrator, Circuit, Simulator
from babcs.io import load_case, summary_data

try:
    from tools.compare_methods import source_metadata
    from tools.generate_runtime_cases import load_runtime_manifest, runtime_case_filename
except ModuleNotFoundError:
    from compare_methods import source_metadata
    from generate_runtime_cases import load_runtime_manifest, runtime_case_filename


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_MANIFEST = REPOSITORY_ROOT / "benchmarks" / "runtime" / "manifest.json"
DEFAULT_EXTERNAL_MANIFEST = REPOSITORY_ROOT / "benchmarks" / "external" / "manifest.json"
BOOTSTRAP_SEED = 20260827
BOOTSTRAP_ITERATIONS = 2000
DIAGNOSTIC_AUTHORITY_ANCHOR_INTERVAL = 2**63 - 1


class RuntimeBenchmarkError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def canonical_row_id(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return f"runtime-{sha256_bytes(encoded)[:24]}"


def parse_ngspice_rusage(text: str) -> dict[str, Any]:
    labels = {
        "Total elapsed time (seconds)": "total_elapsed_seconds",
        "Maximum ngspice program size": "maximum_program_size_mb",
        "Total iterations": "total_iterations",
        "Transient iterations": "transient_iterations",
        "Circuit Equations": "circuit_equations",
        "Transient timepoints": "transient_timepoints",
        "Accepted timepoints": "accepted_timepoints",
        "Rejected timepoints": "rejected_timepoints",
        "Total analysis time (seconds)": "total_analysis_seconds",
        "Matrix load time": "matrix_load_seconds",
        "Matrix reorder time": "matrix_reorder_seconds",
        "Matrix factor time": "matrix_factor_seconds",
        "Matrix solve time": "matrix_solve_seconds",
        "Transient analysis time": "transient_analysis_seconds",
        "Transient load time": "transient_load_seconds",
        "Transient factor time": "transient_factor_seconds",
        "Transient solve time": "transient_solve_seconds",
        "Transient trunc time": "transient_truncation_seconds",
    }
    integer_keys = {
        "total_iterations",
        "transient_iterations",
        "circuit_equations",
        "transient_timepoints",
        "accepted_timepoints",
        "rejected_timepoints",
    }
    required = {
        "total_iterations",
        "transient_iterations",
        "circuit_equations",
        "transient_timepoints",
        "accepted_timepoints",
        "rejected_timepoints",
        "total_analysis_seconds",
        "matrix_load_seconds",
        "matrix_reorder_seconds",
        "matrix_factor_seconds",
        "matrix_solve_seconds",
        "transient_analysis_seconds",
        "transient_load_seconds",
        "transient_factor_seconds",
        "transient_solve_seconds",
    }
    values: dict[str, int | float] = {}
    unknown: dict[str, str] = {}
    for raw_line in text.splitlines():
        match = re.match(r"^\s*([^=]+?)\s*=\s*(.*?)\s*$", raw_line)
        if not match:
            continue
        label, raw_value = match.groups()
        key = labels.get(label)
        if key is None:
            unknown[label] = raw_value
            continue
        if key in values:
            raise RuntimeBenchmarkError(f"duplicate ngspice rusage counter: {label}")
        number_match = re.match(r"^(\S+)", raw_value)
        if number_match is None:
            raise RuntimeBenchmarkError(f"malformed ngspice rusage counter: {label}")
        try:
            number = float(number_match.group(1))
        except ValueError as error:
            raise RuntimeBenchmarkError(f"malformed ngspice rusage counter: {label}") from error
        if not math.isfinite(number) or number < 0.0:
            raise RuntimeBenchmarkError(f"nonfinite or negative ngspice rusage counter: {label}")
        if key in integer_keys:
            if not number.is_integer():
                raise RuntimeBenchmarkError(f"ngspice integer counter is fractional: {label}")
            values[key] = int(number)
        else:
            values[key] = number
    missing = sorted(required - values.keys())
    if missing:
        raise RuntimeBenchmarkError(f"ngspice rusage is missing required counters: {', '.join(missing)}")
    solver_match = re.search(r"Using\s+(.+?)\s+as Direct Linear Solver", text)
    return {
        "counters": values,
        "unknown_fields": dict(sorted(unknown.items())),
        "linear_solver": solver_match.group(1).strip() if solver_match else "unknown",
    }


def percentile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise RuntimeBenchmarkError("cannot summarize an empty sample set")
    if not 0.0 <= probability <= 1.0:
        raise ValueError("percentile probability must be between zero and one")
    ordered = sorted(float(value) for value in values)
    if any(not math.isfinite(value) for value in ordered):
        raise RuntimeBenchmarkError("runtime samples must be finite")
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def summarize_samples(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        raise RuntimeBenchmarkError("cannot summarize an empty sample set")
    normalized = [float(value) for value in values]
    summary: dict[str, Any] = {
        "count": len(normalized),
        "minimum": min(normalized),
        "p25": percentile(normalized, 0.25),
        "median": statistics.median(normalized),
        "p75": percentile(normalized, 0.75),
        "maximum": max(normalized),
        "mean": statistics.fmean(normalized),
        "bootstrap_median_95": None,
    }
    if len(normalized) >= 11:
        generator = random.Random(BOOTSTRAP_SEED)
        medians = [
            statistics.median(generator.choices(normalized, k=len(normalized)))
            for _ in range(BOOTSTRAP_ITERATIONS)
        ]
        summary["bootstrap_median_95"] = {
            "lower": percentile(medians, 0.025),
            "upper": percentile(medians, 0.975),
            "seed": BOOTSTRAP_SEED,
            "iterations": BOOTSTRAP_ITERATIONS,
        }
    return summary


def common_grid(start_time: float, stop_time: float, samples: int) -> tuple[float, ...]:
    if samples < 2:
        raise RuntimeBenchmarkError("common accuracy grid requires at least two samples")
    if not math.isfinite(start_time) or not math.isfinite(stop_time) or stop_time <= start_time:
        raise RuntimeBenchmarkError("common accuracy grid requires finite increasing times")
    step = (stop_time - start_time) / (samples - 1)
    return tuple(start_time + index * step for index in range(samples - 1)) + (stop_time,)


def trace_time_tolerance(value: float) -> float:
    return max(128.0 * math.ulp(max(abs(value), 1.0)), 5.0e-8 * max(abs(value), 1.0e-300))


def interpolate_rows(
    rows: Sequence[Sequence[float]],
    state_count: int,
    times: Sequence[float],
) -> tuple[tuple[float, ...], ...]:
    if len(rows) < 2:
        raise RuntimeBenchmarkError("trajectory requires at least two rows")
    normalized = [tuple(float(value) for value in row) for row in rows]
    if any(len(row) != state_count + 1 for row in normalized):
        raise RuntimeBenchmarkError("trajectory row width does not match state count")
    native_times = [row[0] for row in normalized]
    if any(right <= left for left, right in zip(native_times, native_times[1:])):
        raise RuntimeBenchmarkError("trajectory times must be strictly increasing")
    tolerance = trace_time_tolerance(native_times[-1])
    sampled: list[tuple[float, ...]] = []
    for time_value in times:
        if time_value < native_times[0] - tolerance or time_value > native_times[-1] + tolerance:
            raise RuntimeBenchmarkError("common-grid sample lies outside trajectory")
        if time_value <= native_times[0] + tolerance:
            sampled.append(tuple(normalized[0][1:]))
            continue
        if time_value >= native_times[-1] - tolerance:
            sampled.append(tuple(normalized[-1][1:]))
            continue
        right_index = bisect.bisect_left(native_times, time_value)
        if native_times[right_index] == time_value:
            sampled.append(tuple(normalized[right_index][1:]))
            continue
        left = normalized[right_index - 1]
        right = normalized[right_index]
        fraction = (time_value - left[0]) / (right[0] - left[0])
        sampled.append(
            tuple(
                left[index] + fraction * (right[index] - left[index])
                for index in range(1, state_count + 1)
            )
        )
    return tuple(sampled)


def native_rows_at_times(
    rows: Sequence[Sequence[float]],
    state_count: int,
    times: Sequence[float],
) -> tuple[tuple[float, ...], ...]:
    if len(rows) < 2:
        raise RuntimeBenchmarkError("trajectory requires at least two rows")
    normalized = [tuple(float(value) for value in row) for row in rows]
    if any(len(row) != state_count + 1 for row in normalized):
        raise RuntimeBenchmarkError("trajectory row width does not match state count")
    native_times = [row[0] for row in normalized]
    if any(right <= left for left, right in zip(native_times, native_times[1:])):
        raise RuntimeBenchmarkError("trajectory times must be strictly increasing")
    tolerance = trace_time_tolerance(native_times[-1])
    sampled: list[tuple[float, ...]] = []
    for time_value in times:
        index = bisect.bisect_left(native_times, time_value)
        candidates = [
            candidate
            for candidate in (index - 1, index)
            if 0 <= candidate < len(normalized)
        ]
        native_index = min(
            candidates,
            key=lambda candidate: abs(native_times[candidate] - time_value),
            default=-1,
        )
        if (
            native_index < 0
            or abs(native_times[native_index] - time_value) > tolerance
        ):
            raise RuntimeBenchmarkError(
                "integrated output time is missing from the native trajectory"
            )
        sampled.append(tuple(normalized[native_index][1:]))
    return tuple(sampled)


def trajectory_error(
    actual: Sequence[Sequence[float]],
    authority: Sequence[Sequence[float]],
    state_names: Sequence[str],
    *,
    absolute_tolerance: float,
    relative_tolerance: float,
) -> dict[str, Any]:
    if len(actual) != len(authority) or not actual:
        raise RuntimeBenchmarkError("actual and authority grids must have equal nonzero lengths")
    if absolute_tolerance <= 0.0 or relative_tolerance < 0.0:
        raise RuntimeBenchmarkError("accuracy tolerances must be nonnegative and absolute tolerance positive")
    state_results: dict[str, dict[str, float]] = {}
    maximum_absolute = 0.0
    maximum_scaled = 0.0
    final_maximum = 0.0
    rms_maximum = 0.0
    for state_index, state_name in enumerate(state_names):
        absolute_errors: list[float] = []
        scaled_errors: list[float] = []
        for actual_row, authority_row in zip(actual, authority, strict=True):
            actual_value = float(actual_row[state_index])
            authority_value = float(authority_row[state_index])
            error = abs(actual_value - authority_value)
            scale = absolute_tolerance + relative_tolerance * max(abs(actual_value), abs(authority_value))
            absolute_errors.append(error)
            scaled_errors.append(error / scale)
        rms = math.sqrt(statistics.fmean(error * error for error in absolute_errors))
        state_maximum = max(absolute_errors)
        state_scaled = max(scaled_errors)
        state_final = absolute_errors[-1]
        state_results[str(state_name)] = {
            "final_absolute_error": state_final,
            "maximum_absolute_error": state_maximum,
            "rms_absolute_error": rms,
            "maximum_scaled_trajectory_error": state_scaled,
        }
        maximum_absolute = max(maximum_absolute, state_maximum)
        maximum_scaled = max(maximum_scaled, state_scaled)
        final_maximum = max(final_maximum, state_final)
        rms_maximum = max(rms_maximum, rms)
    return {
        "final_state_maximum_absolute_error": final_maximum,
        "maximum_pointwise_absolute_error": maximum_absolute,
        "maximum_rms_absolute_error": rms_maximum,
        "maximum_scaled_trajectory_error": maximum_scaled,
        "states": state_results,
    }


def oscillator_metrics(
    values: Sequence[Sequence[float]],
    authority: Sequence[Sequence[float]],
    times: Sequence[float],
    case_data: dict[str, Any],
) -> dict[str, float] | None:
    capacitors = [
        element for element in case_data.get("elements", [])
        if str(element.get("type", "")).lower() in {"c", "capacitor"}
    ]
    inductors = [
        element for element in case_data.get("elements", [])
        if str(element.get("type", "")).lower() in {"l", "inductor"}
    ]
    if len(capacitors) != 1 or len(inductors) != 1 or len(values[0]) < 2:
        return None
    capacitance = float(capacitors[0]["capacitance"])
    inductance = float(inductors[0]["inductance"])

    def energy(row: Sequence[float]) -> float:
        return 0.5 * capacitance * float(row[0]) ** 2 + 0.5 * inductance * float(row[1]) ** 2

    actual_energy = [energy(row) for row in values]
    authority_energy = [energy(row) for row in authority]
    energy_scale = max(max(authority_energy), 1.0e-300)
    amplitude = max(abs(float(row[0])) for row in values)
    authority_amplitude = max(abs(float(row[0])) for row in authority)

    def crossings(rows: Sequence[Sequence[float]]) -> list[float]:
        result: list[float] = []
        for left_time, right_time, left_row, right_row in zip(
            times,
            times[1:],
            rows,
            rows[1:],
        ):
            left_value = float(left_row[0])
            right_value = float(right_row[0])
            if left_value <= 0.0 < right_value:
                fraction = -left_value / (right_value - left_value)
                result.append(left_time + fraction * (right_time - left_time))
        return result

    actual_crossings = crossings(values)
    authority_crossings = crossings(authority)
    actual_period = None
    authority_period = None
    relative_period_error = None
    final_phase_error = None
    if len(actual_crossings) >= 2 and len(authority_crossings) >= 2:
        actual_period = statistics.fmean(
            right - left for left, right in zip(actual_crossings, actual_crossings[1:])
        )
        authority_period = statistics.fmean(
            right - left for left, right in zip(authority_crossings, authority_crossings[1:])
        )
        relative_period_error = abs(actual_period - authority_period) / authority_period
        final_phase_error = (
            2.0
            * math.pi
            * (actual_crossings[-1] - authority_crossings[-1])
            / authority_period
        )
    return {
        "amplitude": amplitude,
        "authority_amplitude": authority_amplitude,
        "relative_amplitude_error": (
            abs(amplitude - authority_amplitude) / max(authority_amplitude, 1.0e-300)
        ),
        "estimated_period": actual_period,
        "authority_estimated_period": authority_period,
        "relative_period_error": relative_period_error,
        "final_phase_error_radians": final_phase_error,
        "relative_energy_span": (max(actual_energy) - min(actual_energy)) / energy_scale,
        "authority_relative_energy_span": (
            max(authority_energy) - min(authority_energy)
        )
        / energy_scale,
        "final_relative_energy_error": abs(actual_energy[-1] - authority_energy[-1]) / energy_scale,
    }


def validate_runtime_report(report: dict[str, Any]) -> None:
    required_top_level = {"schema_version", "environment", "configuration", "rows", "claim_boundary"}
    if report.get("schema_version") != 1 or not required_top_level.issubset(report):
        raise RuntimeBenchmarkError("runtime report does not satisfy schema-version 1 top-level fields")
    rows = report.get("rows")
    if not isinstance(rows, list) or not rows:
        raise RuntimeBenchmarkError("runtime report requires at least one row")
    identifiers: set[str] = set()
    configuration = report.get("configuration")
    if not isinstance(configuration, dict) or configuration.get(
        "babcs_linear_backend"
    ) not in {"dense", "scipy", "hybrid"}:
        raise RuntimeBenchmarkError(
            "runtime report requires a declared dense, scipy, or hybrid BAB-CS backend"
        )
    wheel = report.get("environment", {}).get("babcs_wheel", {})
    if wheel.get("linear_backend") != configuration["babcs_linear_backend"]:
        raise RuntimeBenchmarkError(
            "runtime report BAB-CS backend does not match installed-wheel evidence"
        )
    backend_policy = configuration.get("babcs_backend_policy")
    if not isinstance(backend_policy, dict) or backend_policy.get(
        "requested"
    ) != configuration["babcs_linear_backend"]:
        raise RuntimeBenchmarkError(
            "runtime report requires a matching BAB-CS backend policy"
        )
    babcs_profiles = configuration.get("babcs_profiles")
    if not isinstance(babcs_profiles, dict) or not babcs_profiles:
        raise RuntimeBenchmarkError(
            "runtime report requires named BAB-CS operating profiles"
        )
    if any(
        not isinstance(profile_id, str)
        or not profile_id
        or not isinstance(profile, dict)
        or not isinstance(profile.get("description"), str)
        or not isinstance(profile.get("config"), dict)
        for profile_id, profile in babcs_profiles.items()
    ):
        raise RuntimeBenchmarkError(
            "runtime report has an invalid BAB-CS operating profile"
        )
    if configuration["babcs_linear_backend"] == "hybrid":
        threshold = backend_policy.get("sparse_minimum_declared_mna_unknowns")
        if not isinstance(threshold, int) or threshold <= 0:
            raise RuntimeBenchmarkError(
                "hybrid runtime report requires a positive sparse crossover"
            )
    accuracy_mode = configuration.get("accuracy_mode")
    if accuracy_mode not in {"fixed_config", "fixed_accuracy"}:
        raise RuntimeBenchmarkError(
            "runtime report requires fixed_config or fixed_accuracy mode"
        )
    fixed_accuracy = configuration.get("fixed_accuracy")
    if accuracy_mode == "fixed_accuracy":
        if not isinstance(fixed_accuracy, dict):
            raise RuntimeBenchmarkError(
                "fixed-accuracy runtime report requires its sweep contract"
            )
        divisors = fixed_accuracy.get("step_divisors")
        family_divisors = fixed_accuracy.get("family_step_divisors", {})
        authority_factor = fixed_accuracy.get("authority_refinement_factor")
        convergence_cap = fixed_accuracy.get(
            "authority_convergence_scaled_error_cap"
        )
        maximum_calibration_points = fixed_accuracy.get(
            "maximum_estimated_calibration_points"
        )
        maximum_calibration_trace_values = fixed_accuracy.get(
            "maximum_estimated_calibration_trace_values"
        )
        maximum_authority_trace_values = fixed_accuracy.get(
            "maximum_estimated_authority_trace_values"
        )
        if (
            not isinstance(divisors, list)
            or not divisors
            or any(not isinstance(value, int) or value <= 0 for value in divisors)
            or divisors != sorted(set(divisors))
            or not isinstance(family_divisors, dict)
            or any(
                not isinstance(values, list)
                or not values
                or any(
                    not isinstance(value, int) or value <= 0
                    for value in values
                )
                or values != sorted(set(values))
                for values in family_divisors.values()
            )
            or not isinstance(fixed_accuracy.get("stop_at_first_qualifying"), bool)
            or not isinstance(authority_factor, int)
            or authority_factor < 4 * max(divisors)
            or not isinstance(convergence_cap, (int, float))
            or not math.isfinite(float(convergence_cap))
            or float(convergence_cap) <= 0.0
            or not isinstance(maximum_calibration_points, int)
            or maximum_calibration_points < 2
            or not isinstance(maximum_calibration_trace_values, int)
            or maximum_calibration_trace_values < 2
            or not isinstance(maximum_authority_trace_values, int)
            or maximum_authority_trace_values < 2
        ):
            raise RuntimeBenchmarkError(
                "fixed-accuracy runtime report has an invalid timestep or authority sweep"
            )
    elif fixed_accuracy is not None:
        raise RuntimeBenchmarkError(
            "fixed-config runtime report must not declare a fixed-accuracy sweep"
        )
    for row in rows:
        row_id = str(row.get("row_id", ""))
        if not re.fullmatch(r"runtime-[a-f0-9]{24}", row_id):
            raise RuntimeBenchmarkError(f"invalid runtime row id: {row_id}")
        if row_id in identifiers:
            raise RuntimeBenchmarkError(f"duplicate runtime row id: {row_id}")
        identifiers.add(row_id)
        status = row.get("status")
        if status not in {"success", "failed", "incomplete", "accuracy_unavailable"}:
            raise RuntimeBenchmarkError(f"invalid runtime row status: {status}")
        if row.get("accuracy_mode") != accuracy_mode:
            raise RuntimeBenchmarkError(
                f"{row_id}: row accuracy mode does not match report configuration"
            )
        accuracy_sweep = row.get("accuracy_sweep")
        if accuracy_mode == "fixed_accuracy":
            if status != "failed" and not isinstance(accuracy_sweep, dict):
                raise RuntimeBenchmarkError(
                    f"{row_id}: fixed-accuracy row requires calibration evidence"
                )
        elif accuracy_sweep is not None:
            raise RuntimeBenchmarkError(
                f"{row_id}: fixed-config row must not include calibration evidence"
            )
        babcs_profile = row.get("babcs_profile")
        if status != "failed":
            if not isinstance(babcs_profile, dict):
                raise RuntimeBenchmarkError(
                    f"{row_id}: row requires its effective BAB-CS profile"
                )
            profile_id = babcs_profile.get("id")
            profile_source = babcs_profile.get("source")
            declared_overrides = babcs_profile.get("declared_overrides")
            effective_configuration = babcs_profile.get(
                "effective_configuration"
            )
            if (
                not isinstance(profile_id, str)
                or profile_source not in {"runtime_manifest", "case_file"}
                or not isinstance(babcs_profile.get("description"), str)
                or not isinstance(declared_overrides, dict)
                or not isinstance(effective_configuration, dict)
                or effective_configuration.get("rollout_mode") != "active"
            ):
                raise RuntimeBenchmarkError(
                    f"{row_id}: row has an invalid BAB-CS profile"
                )
            if profile_source == "runtime_manifest":
                declared_profile = babcs_profiles.get(profile_id)
                if (
                    not isinstance(declared_profile, dict)
                    or declared_profile.get("description")
                    != babcs_profile.get("description")
                    or declared_profile.get("config") != declared_overrides
                ):
                    raise RuntimeBenchmarkError(
                        f"{row_id}: row BAB-CS profile does not match the manifest"
                    )
            elif not profile_id.startswith("case_declared:"):
                raise RuntimeBenchmarkError(
                    f"{row_id}: case-file BAB-CS profile id is invalid"
                )
            semantic_equality = row.get("semantic_equality", {})
            if semantic_equality.get("babcs_configuration_matches") is not True:
                raise RuntimeBenchmarkError(
                    f"{row_id}: installed-wheel BAB-CS configuration is not proven"
                )
        actual_backend = row.get("babcs_linear_backend")
        if actual_backend not in {"dense", "scipy"}:
            raise RuntimeBenchmarkError(
                f"{row_id}: row requires an actual dense or scipy BAB-CS backend"
            )
        requested_backend = configuration["babcs_linear_backend"]
        if requested_backend != "hybrid" and actual_backend != requested_backend:
            raise RuntimeBenchmarkError(
                f"{row_id}: actual BAB-CS backend does not match requested profile"
            )
        if requested_backend == "hybrid":
            declared_mna_unknowns = row.get("circuit_size", {}).get(
                "declared_mna_unknowns"
            )
            threshold = backend_policy["sparse_minimum_declared_mna_unknowns"]
            expected_backend = (
                "scipy"
                if isinstance(declared_mna_unknowns, int)
                and declared_mna_unknowns >= threshold
                else "dense"
            )
            if actual_backend != expected_backend:
                raise RuntimeBenchmarkError(
                    f"{row_id}: actual BAB-CS backend violates hybrid crossover policy"
                )
        if status == "success":
            speedup = row.get("speedup_x")
            if not isinstance(speedup, (int, float)) or not math.isfinite(speedup) or speedup <= 0.0:
                raise RuntimeBenchmarkError(f"{row_id}: successful row requires finite positive speedup")
            for tool in ("babcs", "ngspice"):
                analysis = _nested(row, "runtime", tool, "analysis_seconds", "median")
                rss = _nested(row, "memory", tool, "maximum_rss_kib", "median")
                error = _nested(row, "accuracy", tool, "maximum_scaled_trajectory_error")
                if any(
                    not isinstance(value, (int, float)) or not math.isfinite(value)
                    for value in (analysis, rss, error)
                ):
                    raise RuntimeBenchmarkError(
                        f"{row_id}: successful row has missing or nonfinite {tool} evidence"
                    )
            if not row.get("source_wheel_equivalent"):
                raise RuntimeBenchmarkError(f"{row_id}: installed-wheel equivalence is not proven")
            if accuracy_mode == "fixed_accuracy":
                target = float(configuration["accuracy"]["target_scaled_error"])
                authority = _nested(row, "accuracy", "authority")
                if (
                    not isinstance(authority, dict)
                    or authority.get("qualified") is not True
                    or not accuracy_sweep.get("qualified")
                    or any(
                    float(_nested(row, "accuracy", tool, "maximum_scaled_trajectory_error"))
                    > target
                    for tool in ("babcs", "ngspice")
                    )
                ):
                    raise RuntimeBenchmarkError(
                        f"{row_id}: successful fixed-accuracy row does not meet the target"
                    )
        elif not row.get("failure_reason"):
            raise RuntimeBenchmarkError(f"{row_id}: nonsuccess row requires a failure reason")


def analytic_authority(
    family: dict[str, Any],
    state_count: int,
    times: Sequence[float],
) -> tuple[tuple[float, ...], ...]:
    parameters = family["parameters"]
    authority_type = str(family["authority"]["type"])
    if authority_type == "analytic_rc":
        resistance = float(parameters["resistance"])
        capacitance = float(parameters["capacitance"])
        source = float(parameters["source_voltage"])
        initial = float(parameters["initial_voltage"])
        tau = resistance * capacitance
        values = [source + (initial - source) * math.exp(-time_value / tau) for time_value in times]
    elif authority_type == "analytic_rl":
        resistance = float(parameters["resistance"])
        inductance = float(parameters["inductance"])
        source = float(parameters["source_voltage"])
        initial = float(parameters["initial_current"])
        steady = source / resistance
        tau = inductance / resistance
        values = [steady + (initial - steady) * math.exp(-time_value / tau) for time_value in times]
    elif authority_type == "analytic_switched_rc":
        resistance = float(parameters["resistance"])
        capacitance = float(parameters["capacitance"])
        source = float(parameters["source_voltage"])
        initial = float(parameters["initial_voltage"])
        on_resistance = float(parameters["on_resistance"])
        off_resistance = float(parameters["off_resistance"])
        delay = float(parameters["delay"])
        width = float(parameters["width"])
        period = float(parameters["period"])
        if width <= 0.0 or period <= 0.0 or width >= period:
            raise RuntimeBenchmarkError(
                "analytic switched RC authority requires 0 < width < period"
            )
        maximum_time = max(float(value) for value in times)
        events: list[tuple[float, bool]] = []
        cycle = 0
        while True:
            turn_on = delay + cycle * period
            if turn_on > maximum_time:
                break
            events.append((turn_on, True))
            turn_off = turn_on + width
            if turn_off <= maximum_time:
                events.append((turn_off, False))
            cycle += 1
        events.sort()
        event_index = 0
        current_time = 0.0
        current_value = initial
        switch_on = False
        values = []

        def advance(target_time: float) -> None:
            nonlocal current_time, current_value
            resistance_total = resistance + (
                on_resistance if switch_on else off_resistance
            )
            tau = resistance_total * capacitance
            current_value = source + (current_value - source) * math.exp(
                -(target_time - current_time) / tau
            )
            current_time = target_time

        for time_value in times:
            while event_index < len(events) and events[event_index][0] <= time_value:
                event_time, next_switch_on = events[event_index]
                if event_time > current_time:
                    advance(event_time)
                switch_on = next_switch_on
                event_index += 1
            if time_value > current_time:
                advance(time_value)
            values.append(current_value)
    else:
        raise RuntimeBenchmarkError(f"unsupported analytic authority: {authority_type}")
    return tuple(tuple(value for _ in range(state_count)) for value in values)


def external_analytic_authority(
    case_id: str,
    case_data: dict[str, Any],
    times: Sequence[float],
) -> tuple[tuple[tuple[float, ...], ...], dict[str, Any]] | None:
    elements = case_data.get("elements", [])
    resistors = [element for element in elements if str(element.get("type", "")).lower() in {"r", "resistor"}]
    capacitors = [element for element in elements if str(element.get("type", "")).lower() in {"c", "capacitor"}]
    inductors = [element for element in elements if str(element.get("type", "")).lower() in {"l", "inductor"}]
    voltage_sources = [element for element in elements if str(element.get("type", "")).lower() in {"v", "voltage_source"}]
    rows: tuple[tuple[float, ...], ...]
    authority_type: str
    if case_id in {"rc_step", "rc_discharge"} and len(resistors) == 1 and len(capacitors) == 1:
        resistance = float(resistors[0]["resistance"])
        capacitance = float(capacitors[0]["capacitance"])
        initial = float(capacitors[0].get("initial_voltage", 0.0))
        source = float(voltage_sources[0]["waveform"]) if voltage_sources else 0.0
        tau = resistance * capacitance
        rows = tuple(
            (source + (initial - source) * math.exp(-time_value / tau),)
            for time_value in times
        )
        authority_type = "analytic_rc"
    elif case_id == "driven_rc" and len(resistors) == 1 and len(capacitors) == 1 and len(voltage_sources) == 1:
        waveform = voltage_sources[0]["waveform"]
        if not isinstance(waveform, dict) or str(waveform.get("type", "")).lower() != "sine":
            return None
        resistance = float(resistors[0]["resistance"])
        capacitance = float(capacitors[0]["capacitance"])
        initial = float(capacitors[0].get("initial_voltage", 0.0))
        offset = float(waveform.get("offset", 0.0))
        amplitude = float(waveform["amplitude"])
        frequency = float(waveform["frequency"])
        tau = resistance * capacitance
        angular_frequency = 2.0 * math.pi * frequency
        phase = math.atan(angular_frequency * tau)
        steady_amplitude = amplitude / math.sqrt(1.0 + (angular_frequency * tau) ** 2)
        steady_at_zero = offset + steady_amplitude * math.sin(-phase)
        transient = initial - steady_at_zero
        rows = tuple(
            (
                offset
                + steady_amplitude * math.sin(angular_frequency * time_value - phase)
                + transient * math.exp(-time_value / tau),
            )
            for time_value in times
        )
        authority_type = "analytic_driven_rc"
    elif case_id in {"rl_step", "rl_decay"} and len(resistors) == 1 and len(inductors) == 1:
        resistance = float(resistors[0]["resistance"])
        inductance = float(inductors[0]["inductance"])
        initial = float(inductors[0].get("initial_current", 0.0))
        source = float(voltage_sources[0]["waveform"]) if voltage_sources else 0.0
        steady = source / resistance
        tau = inductance / resistance
        rows = tuple(
            (steady + (initial - steady) * math.exp(-time_value / tau),)
            for time_value in times
        )
        authority_type = "analytic_rl"
    elif case_id in {"lc_long", "lc_offset", "rlc_damped", "rlc_overdamped"} and len(capacitors) == 1 and len(inductors) == 1:
        capacitance = float(capacitors[0]["capacitance"])
        inductance = float(inductors[0]["inductance"])
        resistance = float(resistors[0]["resistance"]) if resistors else math.inf
        initial_voltage = float(capacitors[0].get("initial_voltage", 0.0))
        initial_current = float(inductors[0].get("initial_current", 0.0))
        rows = tuple(
            _parallel_rlc_state(
                time_value,
                resistance=resistance,
                capacitance=capacitance,
                inductance=inductance,
                initial_voltage=initial_voltage,
                initial_current=initial_current,
            )
            for time_value in times
        )
        authority_type = "analytic_parallel_rlc"
    else:
        return None
    payload = json.dumps(rows, separators=(",", ":"), allow_nan=False).encode()
    return rows, {"type": authority_type, "trace_sha256": sha256_bytes(payload)}


def _parallel_rlc_state(
    time_value: float,
    *,
    resistance: float,
    capacitance: float,
    inductance: float,
    initial_voltage: float,
    initial_current: float,
) -> tuple[float, float]:
    conductance = 0.0 if math.isinf(resistance) else 1.0 / resistance
    alpha = conductance / (2.0 * capacitance)
    omega_zero = math.sqrt(1.0 / (inductance * capacitance))
    initial_derivative = -(initial_current + conductance * initial_voltage) / capacitance
    discriminant = alpha * alpha - omega_zero * omega_zero
    if abs(discriminant) <= 1.0e-14 * omega_zero * omega_zero:
        coefficient = initial_derivative + alpha * initial_voltage
        exponential = math.exp(-alpha * time_value)
        voltage = (initial_voltage + coefficient * time_value) * exponential
        derivative = (
            coefficient - alpha * (initial_voltage + coefficient * time_value)
        ) * exponential
    elif discriminant < 0.0:
        omega_damped = math.sqrt(-discriminant)
        coefficient = (initial_derivative + alpha * initial_voltage) / omega_damped
        cosine = math.cos(omega_damped * time_value)
        sine = math.sin(omega_damped * time_value)
        exponential = math.exp(-alpha * time_value)
        voltage = exponential * (initial_voltage * cosine + coefficient * sine)
        derivative = exponential * (
            (-alpha * initial_voltage + coefficient * omega_damped) * cosine
            + (-alpha * coefficient - initial_voltage * omega_damped) * sine
        )
    else:
        root = math.sqrt(discriminant)
        first_root = -alpha + root
        second_root = -alpha - root
        first_coefficient = (initial_derivative - second_root * initial_voltage) / (
            first_root - second_root
        )
        second_coefficient = initial_voltage - first_coefficient
        first_term = first_coefficient * math.exp(first_root * time_value)
        second_term = second_coefficient * math.exp(second_root * time_value)
        voltage = first_term + second_term
        derivative = first_root * first_term + second_root * second_term
    current = -capacitance * derivative - conductance * voltage
    return voltage, current


def refined_authority(
    case_path: str | Path,
    times: Sequence[float],
    *,
    refinement_factor: int = 8,
    linear_backend: str | None = None,
    sampling_mode: str = "interpolate",
) -> tuple[tuple[tuple[float, ...], ...], dict[str, Any]]:
    if refinement_factor < 2:
        raise RuntimeBenchmarkError("refined authority requires a refinement factor of at least two")
    if sampling_mode not in {"interpolate", "integrated_output_times"}:
        raise RuntimeBenchmarkError(
            "refined authority sampling_mode must be interpolate or integrated_output_times"
        )
    circuit, simulation, config = load_case(case_path)
    if linear_backend is not None:
        circuit = Circuit(circuit.elements, linear_backend=linear_backend)
    configured_minimum_step = config.minimum_step
    authority_minimum_step = (
        diagnostic_minimum_step(
            times,
            start_time=float(simulation["start_time"]),
            stop_time=float(simulation["stop_time"]),
            configured_minimum_step=configured_minimum_step,
        )
        if sampling_mode == "integrated_output_times"
        else configured_minimum_step
    )
    authority_anchor_interval_steps = (
        DIAGNOSTIC_AUTHORITY_ANCHOR_INTERVAL
        if sampling_mode == "integrated_output_times"
        else config.anchor_interval_steps
    )
    authority_config = replace(
        config,
        rollout_mode="disabled",
        reference_method="trapezoidal",
        reference_interval_steps=1,
        minimum_step=authority_minimum_step,
        anchor_interval_steps=authority_anchor_interval_steps,
    )
    result = Simulator(BoundedIntegrator(authority_config)).run(
        circuit,
        simulation["stop_time"],
        simulation["nominal_step"] / refinement_factor,
        start_time=simulation["start_time"],
        output_times=(times if sampling_mode == "integrated_output_times" else None),
        output_interval_substeps=(
            refinement_factor
            if sampling_mode == "integrated_output_times"
            else None
        ),
    )
    diagnostics = summary_data(result)
    work_names = (
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
    work = {
        name: int(diagnostics.get(name, 0))
        for name in (
            "accepted_steps",
            "reference_solves",
            "reference_iterations",
            "reference_circuit_evaluations",
            "reference_algebraic_iterations",
            "replay_steps",
            "replay_reference_iterations",
            "replay_circuit_evaluations",
            "replay_algebraic_iterations",
        )
    }
    work["deterministic_work_units"] = sum(
        int(diagnostics.get(name, 0)) for name in work_names
    )
    rows = [[point.time, *point.state.evaluation.dynamic_state] for point in result.points]
    sampled = (
        native_rows_at_times(rows, circuit.dynamic_size, times)
        if sampling_mode == "integrated_output_times"
        else interpolate_rows(rows, circuit.dynamic_size, times)
    )
    trace_payload = json.dumps(
        {"times": list(times), "state_names": list(circuit.dynamic_names), "values": sampled},
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return sampled, {
        "type": "refined_trapezoidal",
        "refinement_factor": refinement_factor,
        "linear_backend": circuit.linear_backend,
        "sampling_mode": sampling_mode,
        "requested_output_times": len(times),
        "configured_minimum_step": configured_minimum_step,
        "effective_minimum_step": authority_minimum_step,
        "configured_anchor_interval_steps": config.anchor_interval_steps,
        "effective_anchor_interval_steps": authority_anchor_interval_steps,
        "output_interval_substeps": (
            refinement_factor
            if sampling_mode == "integrated_output_times"
            else None
        ),
        "native_points": len(rows),
        "work": work,
        "trace_sha256": sha256_bytes(trace_payload),
    }


def diagnostic_minimum_step(
    times: Sequence[float],
    *,
    start_time: float,
    stop_time: float,
    configured_minimum_step: float,
) -> float:
    normalized = tuple(float(value) for value in times)
    if any(not math.isfinite(value) for value in normalized):
        raise RuntimeBenchmarkError("diagnostic output times must be finite")
    if any(right <= left for left, right in zip(normalized, normalized[1:])):
        raise RuntimeBenchmarkError("diagnostic output times must be strictly increasing")
    if any(value < start_time or value > stop_time for value in normalized):
        raise RuntimeBenchmarkError("diagnostic output times must lie within the simulation interval")

    boundaries = [start_time]
    boundaries.extend(
        value for value in normalized if start_time < value < stop_time
    )
    boundaries.append(stop_time)
    positive_gaps = [
        right - left
        for left, right in zip(boundaries, boundaries[1:])
        if right > left
    ]
    if not positive_gaps:
        return configured_minimum_step

    minimum_gap = min(positive_gaps)
    boundary_resolution_step = min(
        4.0 * math.ulp(value)
        for value in boundaries
        if value != 0.0
    )
    return min(configured_minimum_step, minimum_gap, boundary_resolution_step)


def environment_metadata(
    repository_root: Path,
    *,
    wheel: dict[str, Any],
    ngspice_executable: str,
    cpu: int | None,
) -> dict[str, Any]:
    cpu_model = "unknown"
    physical_core_keys: set[tuple[str, str]] = set()
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        cpuinfo_text = cpuinfo.read_text(encoding="utf-8", errors="replace")
        for line in cpuinfo_text.splitlines():
            if line.lower().startswith("model name") and ":" in line:
                cpu_model = line.split(":", 1)[1].strip()
                break
        for block in cpuinfo_text.split("\n\n"):
            fields = {
                line.split(":", 1)[0].strip(): line.split(":", 1)[1].strip()
                for line in block.splitlines()
                if ":" in line
            }
            if "physical id" in fields and "core id" in fields:
                physical_core_keys.add((fields["physical id"], fields["core id"]))
    mem_total_kib = None
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        match = re.search(r"^MemTotal:\s+(\d+)\s+kB", meminfo.read_text(), re.MULTILINE)
        mem_total_kib = int(match.group(1)) if match else None
    governor = "unknown"
    governor_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    if governor_path.is_file():
        governor = governor_path.read_text().strip()
    ngspice_path = shutil.which(ngspice_executable)
    if ngspice_path is None:
        raise RuntimeBenchmarkError(f"ngspice executable not found: {ngspice_executable}")
    ngspice_version = subprocess.run(
        [ngspice_path, "--version"], capture_output=True, text=True, check=False
    )
    ngspice_version_text = (ngspice_version.stdout or ngspice_version.stderr).strip()
    ngspice_version_line = next(
        (
            line.strip("* ")
            for line in ngspice_version_text.splitlines()
            if "ngspice-" in line.lower()
        ),
        "unknown",
    )
    ngspice_creation_date = next(
        (
            line.split(":", 1)[1].strip()
            for line in ngspice_version_text.splitlines()
            if line.strip().lower().startswith("creation date:")
        ),
        "unknown",
    )
    ngspice_compiled_solver = next(
        (
            line.strip("* ").removeprefix("Compiled with ").removesuffix(" Direct Linear Solver")
            for line in ngspice_version_text.splitlines()
            if "Compiled with" in line and "Direct Linear Solver" in line
        ),
        "unknown",
    )
    time_path = shutil.which("time")
    if Path("/usr/bin/time").is_file():
        time_path = "/usr/bin/time"
    if time_path is None:
        raise RuntimeBenchmarkError("GNU Time executable not found")
    time_version = subprocess.run(
        [time_path, "--version"], capture_output=True, text=True, check=False
    )
    affinity = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None
    thread_variables = {
        name: os.environ.get(name, "1")
        for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")
    }
    return {
        "source": source_metadata(repository_root),
        "machine": {
            "hostname": platform.node(),
            "processor_model": cpu_model,
            "physical_cores": len(physical_core_keys) or None,
            "logical_cores": os.cpu_count(),
            "allowed_cpu_affinity": affinity,
            "selected_cpu": cpu,
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "total_memory_kib": mem_total_kib,
            "frequency_governor": governor,
        },
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "executable": os.path.realpath(os.sys.executable),
        },
        "babcs_wheel": wheel,
        "ngspice": {
            "path": ngspice_path,
            "version": ngspice_version_line,
            "version_output": ngspice_version_text,
            "creation_date": ngspice_creation_date,
            "compiled_linear_solver": ngspice_compiled_solver,
        },
        "gnu_time": {
            "path": time_path,
            "version": (time_version.stdout or time_version.stderr).splitlines()[0].strip(),
        },
        "thread_environment": thread_variables,
    }


def write_json(path: str | Path, value: Any) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_matched_csv(path: str | Path, report: dict[str, Any]) -> None:
    columns = [
        "row_id", "inventory", "case_id", "family_id", "size", "declared_mna_unknowns",
        "status", "accuracy_mode", "babcs_profile_id", "babcs_candidate_method",
        "babcs_reference_interval_steps", "babcs_nominal_step", "ngspice_nominal_step",
        "babcs_selected_step_divisor", "ngspice_selected_step_divisor",
        "babcs_selected_native_work", "ngspice_selected_native_work",
        "babcs_analysis_median_seconds", "ngspice_analysis_median_seconds",
        "speedup_x", "babcs_peak_rss_median_kib", "ngspice_peak_rss_median_kib",
        "babcs_accepted_points", "ngspice_accepted_points", "babcs_output_points",
        "ngspice_output_points", "common_grid_points", "babcs_maximum_scaled_error",
        "ngspice_maximum_scaled_error", "failure_reason",
    ]
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow({
                "row_id": row["row_id"],
                "inventory": row["inventory"],
                "case_id": row["case_id"],
                "family_id": row.get("family_id"),
                "size": row.get("size"),
                "declared_mna_unknowns": row["circuit_size"].get("declared_mna_unknowns"),
                "status": row["status"],
                "accuracy_mode": row.get("accuracy_mode"),
                "babcs_profile_id": _nested(row, "babcs_profile", "id"),
                "babcs_candidate_method": _nested(
                    row,
                    "babcs_profile",
                    "effective_configuration",
                    "candidate_method",
                ),
                "babcs_reference_interval_steps": _nested(
                    row,
                    "babcs_profile",
                    "effective_configuration",
                    "reference_interval_steps",
                ),
                "babcs_nominal_step": _nested(row, "simulation", "babcs_nominal_step"),
                "ngspice_nominal_step": _nested(row, "simulation", "ngspice_nominal_step"),
                "babcs_selected_step_divisor": _nested(
                    row, "accuracy_sweep", "tools", "babcs", "selected_step_divisor"
                ),
                "ngspice_selected_step_divisor": _nested(
                    row, "accuracy_sweep", "tools", "ngspice", "selected_step_divisor"
                ),
                "babcs_selected_native_work": _nested(
                    row, "accuracy_sweep", "tools", "babcs", "selected_native_work"
                ),
                "ngspice_selected_native_work": _nested(
                    row, "accuracy_sweep", "tools", "ngspice", "selected_native_work"
                ),
                "babcs_analysis_median_seconds": _nested(row, "runtime", "babcs", "analysis_seconds", "median"),
                "ngspice_analysis_median_seconds": _nested(row, "runtime", "ngspice", "analysis_seconds", "median"),
                "speedup_x": row.get("speedup_x"),
                "babcs_peak_rss_median_kib": _nested(row, "memory", "babcs", "maximum_rss_kib", "median"),
                "ngspice_peak_rss_median_kib": _nested(row, "memory", "ngspice", "maximum_rss_kib", "median"),
                "babcs_accepted_points": _nested(row, "points", "babcs", "accepted"),
                "ngspice_accepted_points": _nested(row, "points", "ngspice", "accepted"),
                "babcs_output_points": _nested(row, "points", "babcs", "output"),
                "ngspice_output_points": _nested(row, "points", "ngspice", "output"),
                "common_grid_points": row["points"].get("common_grid"),
                "babcs_maximum_scaled_error": _nested(row, "accuracy", "babcs", "maximum_scaled_trajectory_error"),
                "ngspice_maximum_scaled_error": _nested(row, "accuracy", "ngspice", "maximum_scaled_trajectory_error"),
                "failure_reason": row.get("failure_reason"),
            })


def write_solver_work_csv(path: str | Path, report: dict[str, Any]) -> None:
    columns = [
        "row_id", "case_id", "family_id", "size", "tool", "accepted_points",
        "rejected_points", "total_iterations", "transient_iterations", "candidate_solves",
        "reference_solves", "candidate_circuit_evaluations", "reference_circuit_evaluations",
        "projection_iterations", "differential_jacobian_evaluations", "matrix_load_seconds",
        "matrix_reorder_seconds", "matrix_factor_seconds", "matrix_solve_seconds",
    ]
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in report["rows"]:
            for tool in ("babcs", "ngspice"):
                work = row["solver_work"].get(tool) or {}
                writer.writerow({
                    "row_id": row["row_id"], "case_id": row["case_id"],
                    "family_id": row.get("family_id"), "size": row.get("size"), "tool": tool,
                    "accepted_points": _nested(row, "points", tool, "accepted"),
                    "rejected_points": _nested(row, "points", tool, "rejected"),
                    "total_iterations": work.get("total_iterations"),
                    "transient_iterations": work.get("transient_iterations"),
                    "candidate_solves": work.get("candidate_solves"),
                    "reference_solves": work.get("reference_solves"),
                    "candidate_circuit_evaluations": work.get("candidate_circuit_evaluations"),
                    "reference_circuit_evaluations": work.get("reference_circuit_evaluations"),
                    "projection_iterations": work.get("projection_iterations"),
                    "differential_jacobian_evaluations": work.get("differential_jacobian_evaluations"),
                    "matrix_load_seconds": work.get("matrix_load_seconds"),
                    "matrix_reorder_seconds": work.get("matrix_reorder_seconds"),
                    "matrix_factor_seconds": work.get("matrix_factor_seconds"),
                    "matrix_solve_seconds": work.get("matrix_solve_seconds"),
                })


def write_memory_csv(path: str | Path, report: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["row_id", "case_id", "family_id", "size", "tool", "median_maximum_rss_kib", "maximum_rss_kib"])
        for row in report["rows"]:
            for tool in ("babcs", "ngspice"):
                tool_memory = row["memory"].get(tool) or {}
                memory = tool_memory.get("maximum_rss_kib")
                writer.writerow([
                    row["row_id"], row["case_id"], row.get("family_id"), row.get("size"), tool,
                    memory.get("median") if memory else None,
                    memory.get("maximum") if memory else None,
                ])


def write_speed_accuracy_svg(path: str | Path, report: dict[str, Any]) -> None:
    rows = [row for row in report["rows"] if row["inventory"] == "size_scaling"]
    colors = {
        "rc_bank": "#0b6a82",
        "coupled_rc_ring": "#c2415d",
        "rl_bank": "#d98237",
        "diode_rc_bank": "#7c4d9e",
        "switched_rc_bank": "#2f855a",
    }
    width, height = 1200, 720
    left_x0, left_x1 = 120, 560
    right_x0, right_x1 = 700, 1140
    top, bottom = 190, 545
    successful = [row for row in rows if row["status"] == "success" and row.get("speedup_x")]
    x_values = [float(row["circuit_size"]["declared_mna_unknowns"]) for row in successful] or [1.0, 10.0]
    x_min, x_max = min(x_values), max(x_values)
    if x_min == x_max:
        x_max = x_min + 1.0
    speed_values = [float(row["speedup_x"]) for row in successful] or [0.5, 2.0]
    speed_min = min(min(speed_values), 0.5)
    speed_max = max(max(speed_values), 2.0)
    log_speed_min, log_speed_max = math.log2(speed_min), math.log2(speed_max)
    errors = [
        float(row["accuracy"][tool]["maximum_scaled_trajectory_error"])
        for row in successful for tool in ("babcs", "ngspice")
        if row["accuracy"].get(tool)
    ] or [1.0e-3, 1.0]
    target = float(report["configuration"]["accuracy"]["target_scaled_error"])
    error_min = max(min(errors + [target]) / 2.0, 1.0e-16)
    error_max = max(errors + [target]) * 2.0
    log_error_min, log_error_max = math.log10(error_min), math.log10(error_max)

    def x_coord(value: float, x0: float, x1: float) -> float:
        return x0 + (math.log2(value) - math.log2(x_min)) / (math.log2(x_max) - math.log2(x_min)) * (x1 - x0) if x_min > 0 else x0

    def speed_y(value: float) -> float:
        return bottom - (math.log2(value) - log_speed_min) / (log_speed_max - log_speed_min) * (bottom - top)

    def error_y(value: float) -> float:
        return bottom - (math.log10(max(value, 1.0e-300)) - log_error_min) / (log_error_max - log_error_min) * (bottom - top)

    machine = report["environment"]["machine"]
    babcs_backend = report["configuration"].get("babcs_linear_backend", "dense")
    accuracy_mode = report["configuration"].get("accuracy_mode", "fixed_config")
    subtitle = (
        f"{machine['processor_model']} · installed-wheel active bounded ({babcs_backend}) · "
        f"{report['environment']['ngspice']['version']} · {report['configuration']['profile']} profile · "
        f"{accuracy_mode.replace('_', '-')} · "
        f"{report['configuration']['warmups']} warmups · {report['configuration']['repeats']} repeats × "
        f"{report['configuration']['rounds']} rounds · analysis-only medians"
    )
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title description" viewBox="0 0 {width} {height}">',
        '<title id="title">BAB-CS speedup versus ngspice with accuracy beside it</title>',
        '<desc id="description">The left panel plots BAB-CS analysis speedup relative to ngspice against model-declared circuit unknowns. The right panel plots BAB-CS and ngspice maximum scaled trajectory error against the same case-size coordinate. The coordinate is not either solver\'s internal equation count. Above one times favors BAB-CS and lower error is better.</desc>',
        '<rect width="1200" height="720" rx="28" fill="#f5f8fb"/>',
        '<text x="60" y="58" font-family="sans-serif" font-size="28" font-weight="800" fill="#10243a">BAB-CS versus ngspice: speed and accuracy stay visible together</text>',
        f'<text x="60" y="88" font-family="sans-serif" font-size="12" fill="#607386">{html.escape(subtitle)}</text>',
        '<rect x="60" y="120" width="540" height="480" rx="18" fill="white" stroke="#d5e0e9"/>',
        '<rect x="640" y="120" width="540" height="480" rx="18" fill="white" stroke="#d5e0e9"/>',
        '<text x="88" y="154" font-family="sans-serif" font-size="12" font-weight="700" fill="#607386">HOW FAST?</text>',
        '<text x="88" y="180" font-family="sans-serif" font-size="18" font-weight="800" fill="#10243a">Speedup × versus ngspice</text>',
        '<text x="668" y="154" font-family="sans-serif" font-size="12" font-weight="700" fill="#607386">HOW ACCURATE?</text>',
        '<text x="668" y="180" font-family="sans-serif" font-size="18" font-weight="800" fill="#10243a">Maximum scaled trajectory error · lower is better</text>',
    ]
    family_labels = {
        "rc_bank": "RC bank",
        "coupled_rc_ring": "Coupled RC",
        "rl_bank": "RL bank",
        "diode_rc_bank": "Diode RC bank",
        "switched_rc_bank": "Switched RC bank",
    }
    legend_x = 86
    for family_id, color in colors.items():
        lines.append(
            f'<circle cx="{legend_x}" cy="108" r="4.5" fill="{color}"/>'
            f'<text x="{legend_x + 10}" y="112" font-family="sans-serif" font-size="10.5" fill="#607386">{family_labels[family_id]}</text>'
        )
        legend_x += 118 if family_id != "diode_rc_bank" else 142
    lines.extend(
        [
            '<circle cx="866" cy="108" r="5" fill="white" stroke="#477083" stroke-width="2"/>',
            '<text x="877" y="112" font-family="sans-serif" font-size="10.5" fill="#607386">BAB-CS error</text>',
            '<path d="M974 102 L980 108 L974 114 L968 108 Z" fill="white" stroke="#477083" stroke-width="2"/>',
            '<text x="986" y="112" font-family="sans-serif" font-size="10.5" fill="#607386">ngspice error</text>',
        ]
    )
    parity = speed_y(1.0)
    lines.extend([
        f'<rect x="{left_x0}" y="{top}" width="{left_x1-left_x0}" height="{max(parity-top, 0)}" fill="#eaf5f2"/>',
        f'<rect x="{left_x0}" y="{parity}" width="{left_x1-left_x0}" height="{max(bottom-parity, 0)}" fill="#fff1e7"/>',
        f'<line x1="{left_x0}" y1="{parity}" x2="{left_x1}" y2="{parity}" stroke="#10243a" stroke-width="3"/>',
        f'<text x="{left_x0+8}" y="{top+18}" font-family="sans-serif" font-size="11" font-weight="700" fill="#0b6a82">BAB-CS FASTER</text>',
        f'<text x="{left_x0+8}" y="{bottom-10}" font-family="sans-serif" font-size="11" font-weight="700" fill="#a35a22">NGSPICE FASTER</text>',
        f'<text x="{left_x0-12}" y="{parity+4}" text-anchor="end" font-family="sans-serif" font-size="12" fill="#10243a">1×</text>',
        f'<line x1="{right_x0}" y1="{error_y(target)}" x2="{right_x1}" y2="{error_y(target)}" stroke="#a6642e" stroke-width="2" stroke-dasharray="7 6"/>',
        f'<text x="{right_x1}" y="{error_y(target)-8}" text-anchor="end" font-family="sans-serif" font-size="10" fill="#a6642e">ACCURACY TARGET {target:g}</text>',
    ])
    for tick in (0.001, 0.01, 0.1, 1.0, 10.0):
        if speed_min <= tick <= speed_max:
            y = speed_y(tick)
            lines.append(
                f'<line x1="{left_x0}" y1="{y:.2f}" x2="{left_x1}" y2="{y:.2f}" stroke="#d5e0e9" stroke-width="1"/>'
            )
            lines.append(
                f'<text x="{left_x0-12}" y="{y+4:.2f}" text-anchor="end" font-family="sans-serif" font-size="11" fill="#607386">{tick:g}×</text>'
            )
    minimum_error_exponent = math.ceil(log_error_min)
    maximum_error_exponent = math.floor(log_error_max)
    error_exponents = list(range(minimum_error_exponent, maximum_error_exponent + 1))
    if len(error_exponents) > 6:
        stride = math.ceil(len(error_exponents) / 6)
        error_exponents = error_exponents[::stride]
    for exponent in error_exponents:
        tick = 10.0**exponent
        y = error_y(tick)
        lines.append(
            f'<line x1="{right_x0}" y1="{y:.2f}" x2="{right_x1}" y2="{y:.2f}" stroke="#d5e0e9" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{right_x0-12}" y="{y+4:.2f}" text-anchor="end" font-family="sans-serif" font-size="11" fill="#607386">10<tspan baseline-shift="super" font-size="8">{exponent}</tspan></text>'
        )
    x_ticks = sorted(
        {
            float(x_min),
            float(x_max),
            *(
                float(value)
                for value in (4, 8, 16, 32, 64, 128, 256, 512)
                if x_min <= value <= x_max
            ),
        }
    )
    for tick in x_ticks:
        left_tick = x_coord(tick, left_x0, left_x1)
        right_tick = x_coord(tick, right_x0, right_x1)
        lines.extend(
            [
                f'<line x1="{left_tick:.2f}" y1="{top}" x2="{left_tick:.2f}" y2="{bottom}" stroke="#e6edf3" stroke-width="1"/>',
                f'<text x="{left_tick:.2f}" y="{bottom+18}" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#607386">{tick:g}</text>',
                f'<line x1="{right_tick:.2f}" y1="{top}" x2="{right_tick:.2f}" y2="{bottom}" stroke="#e6edf3" stroke-width="1"/>',
                f'<text x="{right_tick:.2f}" y="{bottom+18}" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#607386">{tick:g}</text>',
            ]
        )
    label_offsets = {
        "rc_bank": 4,
        "coupled_rc_ring": -22,
        "rl_bank": -16,
        "diode_rc_bank": -10,
        "switched_rc_bank": 18,
    }
    for family_id in colors:
        family_rows = sorted([row for row in rows if row.get("family_id") == family_id], key=lambda row: int(row.get("size") or 0))
        speed_points: list[str] = []
        for row in family_rows:
            x_value = float(row["circuit_size"].get("declared_mna_unknowns") or 1.0)
            left_x = x_coord(x_value, left_x0, left_x1)
            right_x = x_coord(x_value, right_x0, right_x1)
            color = colors[family_id]
            if row["status"] != "success" or not row.get("speedup_x"):
                lines.append(f'<path d="M{left_x-6:.2f} {parity-6:.2f} L{left_x+6:.2f} {parity+6:.2f} M{left_x+6:.2f} {parity-6:.2f} L{left_x-6:.2f} {parity+6:.2f}" stroke="#b42318" stroke-width="3"/>')
                lines.append(f'<path d="M{right_x-6:.2f} {bottom-6:.2f} L{right_x+6:.2f} {bottom+6:.2f} M{right_x+6:.2f} {bottom-6:.2f} L{right_x-6:.2f} {bottom+6:.2f}" stroke="#b42318" stroke-width="3"/>')
                continue
            left_y = speed_y(float(row["speedup_x"]))
            speed_points.append(f"{left_x:.2f},{left_y:.2f}")
            interval = row["runtime"]["speedup_bootstrap_95"]
            if interval:
                lines.append(f'<line x1="{left_x:.2f}" y1="{speed_y(float(interval["upper"])):.2f}" x2="{left_x:.2f}" y2="{speed_y(float(interval["lower"])):.2f}" stroke="{color}" stroke-width="2"/>')
            lines.append(f'<circle cx="{left_x:.2f}" cy="{left_y:.2f}" r="5.5" fill="white" stroke="{color}" stroke-width="3"/>')
            bab_error = float(row["accuracy"]["babcs"]["maximum_scaled_trajectory_error"])
            ng_error = float(row["accuracy"]["ngspice"]["maximum_scaled_trajectory_error"])
            lines.append(f'<circle cx="{right_x-4:.2f}" cy="{error_y(bab_error):.2f}" r="5.5" fill="white" stroke="{color}" stroke-width="3"/>')
            diamond_y = error_y(ng_error)
            lines.append(f'<path d="M{right_x+4:.2f} {diamond_y-6:.2f} L{right_x+10:.2f} {diamond_y:.2f} L{right_x+4:.2f} {diamond_y+6:.2f} L{right_x-2:.2f} {diamond_y:.2f} Z" fill="white" stroke="{color}" stroke-width="3"/>')
        if len(speed_points) > 1:
            lines.append(f'<polyline points="{" ".join(speed_points)}" fill="none" stroke="{colors[family_id]}" stroke-width="2" opacity="0.75"/>')
        successful_family_rows = [
            row for row in family_rows if row["status"] == "success" and row.get("speedup_x")
        ]
        if successful_family_rows:
            largest = successful_family_rows[-1]
            label_x = x_coord(
                float(largest["circuit_size"]["declared_mna_unknowns"]),
                left_x0,
                left_x1,
            )
            label_y = speed_y(float(largest["speedup_x"])) + label_offsets[family_id]
            lines.append(
                f'<text x="{label_x-8:.2f}" y="{label_y:.2f}" text-anchor="end" font-family="sans-serif" font-size="10" font-weight="700" fill="{colors[family_id]}">{family_labels[family_id]}</text>'
            )
    lines.extend([
        f'<line x1="{left_x0}" y1="{bottom}" x2="{left_x1}" y2="{bottom}" stroke="#607386"/><line x1="{left_x0}" y1="{top}" x2="{left_x0}" y2="{bottom}" stroke="#607386"/>',
        f'<line x1="{right_x0}" y1="{bottom}" x2="{right_x1}" y2="{bottom}" stroke="#607386"/><line x1="{right_x0}" y1="{top}" x2="{right_x0}" y2="{bottom}" stroke="#607386"/>',
        '<text x="340" y="578" text-anchor="middle" font-family="sans-serif" font-size="11" font-weight="700" fill="#607386">CIRCUIT SIZE · DECLARED MNA UNKNOWNS →</text>',
        '<text x="920" y="578" text-anchor="middle" font-family="sans-serif" font-size="11" font-weight="700" fill="#607386">SAME CIRCUIT SIZE ORDERING →</text>',
        '<rect x="60" y="626" width="1120" height="58" rx="14" fill="#102f43"/>',
        '<text x="84" y="650" font-family="sans-serif" font-size="13" font-weight="800" fill="white">Reading rule</text>',
        '<text x="84" y="671" font-family="sans-serif" font-size="12" fill="#d7e7ef">Above 1× means BAB-CS was faster on this machine. Lower trajectory error is better. Failed rows remain visible as red crosses.</text>',
        '</svg>',
    ])
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_memory_svg(path: str | Path, report: dict[str, Any]) -> None:
    _write_simple_dual_series_svg(
        path,
        report,
        title="Peak resident memory by circuit size",
        y_label="Median maximum RSS (KiB)",
        value=lambda row, tool: _nested(row, "memory", tool, "maximum_rss_kib", "median"),
    )


def write_points_work_svg(path: str | Path, report: dict[str, Any]) -> None:
    _write_simple_dual_series_svg(
        path,
        report,
        title="Accepted points by circuit size",
        y_label="Accepted timepoints",
        value=lambda row, tool: _nested(row, "points", tool, "accepted"),
    )


def _write_simple_dual_series_svg(
    path: str | Path,
    report: dict[str, Any],
    *,
    title: str,
    y_label: str,
    value,
) -> None:
    rows = [row for row in report["rows"] if row["inventory"] == "size_scaling" and row["status"] == "success"]
    width, height = 1000, 600
    left, right, top, bottom = 100, 950, 110, 500
    x_values = [float(row["circuit_size"]["declared_mna_unknowns"]) for row in rows] or [1.0, 2.0]
    y_values = [float(value(row, tool)) for row in rows for tool in ("babcs", "ngspice") if value(row, tool) is not None] or [0.0, 1.0]
    x_min, x_max = min(x_values), max(x_values)
    y_max = max(y_values) * 1.1 or 1.0
    def x_coord(number: float) -> float:
        if x_max == x_min:
            return (left + right) / 2.0
        return left + (math.log2(number) - math.log2(x_min)) / (math.log2(x_max) - math.log2(x_min)) * (right - left)
    def y_coord(number: float) -> float:
        return bottom - number / y_max * (bottom - top)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title description" viewBox="0 0 {width} {height}">',
        f'<title id="title">{html.escape(title)}</title>',
        f'<desc id="description">{html.escape(title)} for BAB-CS and ngspice against declared circuit unknowns.</desc>',
        '<rect width="1000" height="600" rx="24" fill="#f5f8fb"/>',
        f'<text x="50" y="55" font-family="sans-serif" font-size="26" font-weight="800" fill="#10243a">{html.escape(title)}</text>',
        f'<text x="50" y="82" font-family="sans-serif" font-size="13" fill="#607386">{html.escape(y_label)} · same-machine informational evidence</text>',
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#607386"/><line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#607386"/>',
    ]
    colors = {"babcs": "#0b6a82", "ngspice": "#d98237"}
    for row in rows:
        x = x_coord(float(row["circuit_size"]["declared_mna_unknowns"]))
        for offset, tool in ((-4, "babcs"), (4, "ngspice")):
            number = value(row, tool)
            if number is not None:
                lines.append(f'<circle cx="{x+offset:.2f}" cy="{y_coord(float(number)):.2f}" r="4.5" fill="{colors[tool]}"/>')
    lines.extend([
        '<text x="500" y="550" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#607386">Declared MNA unknowns</text>',
        '<circle cx="760" cy="55" r="5" fill="#0b6a82"/><text x="773" y="59" font-family="sans-serif" font-size="12">BAB-CS</text>',
        '<circle cx="850" cy="55" r="5" fill="#d98237"/><text x="863" y="59" font-family="sans-serif" font-size="12">ngspice</text>',
        '</svg>',
    ])
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown_report(
    path: str | Path,
    report: dict[str, Any],
    *,
    image_href: str = "speedup-accuracy-by-size.svg",
) -> None:
    environment = report["environment"]
    configuration = report["configuration"]
    babcs_backend = configuration.get("babcs_linear_backend", "dense")
    accuracy_mode = configuration.get("accuracy_mode", "fixed_config")
    rows = report["rows"]
    profile_ids = sorted(
        {
            str(_nested(row, "babcs_profile", "id"))
            for row in rows
            if _nested(row, "babcs_profile", "id") is not None
        }
    )
    lines = [
        "# BAB-CS versus ngspice Runtime Benchmark",
        "",
        "This report records a same-machine comparison between Bounded-Authority-Based Circuit Simulation (BAB-CS) and ngspice. Modified nodal analysis (MNA) unknowns are the declared circuit equations used as the common size axis. Resident set size (RSS) is the peak physical memory retained by a process.",
        "",
        f"![BAB-CS speedup versus ngspice with accuracy beside it]({image_href})",
        "",
        "Above `1×` means BAB-CS was faster for the measured row. Lower trajectory error is better. Timing never overrides failed accuracy, convergence, or semantic mapping.",
        "",
        "## Exact Results",
        "",
        "| Case | Family | Size | MNA unknowns | BAB-CS profile | Status | BAB-CS step (s) | ngspice step (s) | BAB-CS median (s) | ngspice median (s) | Speedup × | BAB-CS scaled error | ngspice scaled error |",
        "| --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {case} | {family} | {size} | {mna} | {profile} | {status} | {babstep} | {ngstep} | {bab} | {ng} | {speed} | {baberr} | {ngerr} |".format(
                case=row["case_id"], family=row.get("family_id") or "—", size=row.get("size") or "—",
                mna=row["circuit_size"].get("declared_mna_unknowns") or "—", status=row["status"],
                profile=_nested(row, "babcs_profile", "id") or "—",
                babstep=_format_number(_nested(row, "simulation", "babcs_nominal_step")),
                ngstep=_format_number(_nested(row, "simulation", "ngspice_nominal_step")),
                bab=_format_number(_nested(row, "runtime", "babcs", "analysis_seconds", "median")),
                ng=_format_number(_nested(row, "runtime", "ngspice", "analysis_seconds", "median")),
                speed=_format_number(row.get("speedup_x")),
                baberr=_format_number(_nested(row, "accuracy", "babcs", "maximum_scaled_trajectory_error")),
                ngerr=_format_number(_nested(row, "accuracy", "ngspice", "maximum_scaled_trajectory_error")),
            )
        )
    lines.extend([
        "",
        "## Measurement Contract",
        "",
        f"- Machine: `{environment['machine']['processor_model']}` on `{environment['machine']['kernel']}`.",
        f"- Profile: `{configuration['profile']}` with BAB-CS `{babcs_backend}` linear algebra, {configuration['warmups']} warmups, {configuration['repeats']} repeats, and {configuration['rounds']} rounds.",
        f"- BAB-CS operating profiles: {', '.join(f'`{profile_id}`' for profile_id in profile_ids) or 'none recorded'}.",
        f"- Accuracy mode: `{accuracy_mode}`. Fixed-accuracy rows independently select each tool's lowest-native-work qualifying maximum timestep; fixed-config rows retain the shared case timestep.",
        f"- Accuracy grid: {configuration['common_grid_samples']} shared samples with absolute tolerance `{configuration['accuracy']['absolute_tolerance']}` and relative tolerance `{configuration['accuracy']['relative_tolerance']}`.",
        f"- BAB-CS wheel SHA-256: `{environment['babcs_wheel']['sha256']}`.",
        f"- ngspice: `{environment['ngspice']['version'].splitlines()[0] if environment['ngspice']['version'] else 'unknown'}`.",
        "- Runtime: analysis-only medians use BAB-CS `perf_counter_ns` timing around `Simulator.run` and ngspice `Total analysis time (seconds)` from `rusage all`.",
        "- Memory: both fresh child processes use GNU Time maximum RSS in kibibytes.",
        "",
        "## Claim Boundary",
        "",
        report["claim_boundary"],
        "",
    ])
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _nested(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _format_number(value: Any) -> str:
    if value is None:
        return "—"
    return format(float(value), ".6g")
