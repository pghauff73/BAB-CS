from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from babcs import BABCSConfig, BoundedAdamsBashforthIntegrator, Simulator
from babcs.integrators import ImplicitSettings
from babcs.io import load_case, summary_data
from babcs.linalg import weighted_rms
from tests.support.metrics import interpolate_trace
from tools.compare_methods import _analytic_state, _work_data, load_manifest, source_metadata
from tools.experiment_records import canonical_row_id, classify_reason


DEFAULT_ATLAS_MANIFEST = REPOSITORY_ROOT / "benchmarks/atlas/manifest.json"


@dataclass(frozen=True)
class AuthorityProvider:
    state_at: Callable[[float], tuple[float, ...]]
    authority_type: str
    identity: dict[str, Any]


def execute_bound_atlas(
    observatory_report: dict[str, Any],
    *,
    observatory_report_sha256: str = "in-memory",
    observatory_manifest_path: str | Path | None = None,
    atlas_manifest_path: str | Path = DEFAULT_ATLAS_MANIFEST,
) -> dict[str, Any]:
    atlas_manifest = json.loads(Path(atlas_manifest_path).read_text(encoding="utf-8"))
    if atlas_manifest.get("schema_version") != 1:
        raise ValueError("unsupported bound atlas manifest schema")
    manifest_path = (
        Path(observatory_manifest_path)
        if observatory_manifest_path is not None
        else Path(atlas_manifest_path).parent / str(atlas_manifest["observatory_manifest"])
    )
    manifest = load_manifest(manifest_path)
    case_map = {str(case["id"]): case for case in manifest["cases"]}
    requested_cases = set(map(str, atlas_manifest["cases"]))
    report_cases = {str(row["case_id"]) for row in observatory_report["results"]}
    if not report_cases <= requested_cases:
        raise ValueError("observatory report contains cases outside the atlas manifest")
    if report_cases - set(case_map):
        raise ValueError("observatory report contains cases missing from its manifest")
    current_source = source_metadata(REPOSITORY_ROOT)
    if observatory_report["source"]["source_tree_sha256"] != current_source["source_tree_sha256"]:
        raise ValueError("observatory report source tree does not match the current source")

    authority_cache: dict[str, AuthorityProvider] = {}
    samples: list[dict[str, Any]] = []
    anchors: list[dict[str, Any]] = []
    causes: list[dict[str, Any]] = []
    aggregates: list[dict[str, Any]] = []

    for record in sorted(observatory_report["results"], key=lambda item: item["row_id"]):
        case_id = str(record["case_id"])
        case = case_map[case_id]
        input_path = manifest_path.parent / str(case["input"])
        circuit, simulation, _ = load_case(input_path)
        config = _config_from_record(record["configuration"])
        expected_row_id = canonical_row_id(
            case_id=case_id,
            method=str(record["method"]),
            nominal_step=float(record["nominal_step"]),
            anchor_interval=record["anchor_interval"],
            configuration=record["configuration"],
        )
        if expected_row_id != record["row_id"]:
            raise ValueError(f"{record['row_id']}: row identity does not match configuration")
        result = Simulator(BoundedAdamsBashforthIntegrator(config)).run(
            circuit,
            simulation["stop_time"],
            float(record["nominal_step"]),
            start_time=simulation["start_time"],
        )
        diagnostics = summary_data(result)
        if diagnostics != record["diagnostics"]:
            raise ValueError(f"{record['row_id']}: atlas replay diagnostics do not reconcile")
        if _work_data(diagnostics) != record["work"]:
            raise ValueError(f"{record['row_id']}: atlas replay work does not reconcile")
        provider = authority_cache.get(case_id)
        if provider is None:
            provider = _authority_provider(case, input_path)
            authority_cache[case_id] = provider
        row_samples, row_anchors, row_causes = _row_samples(
            record,
            case,
            circuit,
            config,
            result,
            provider,
        )
        samples.extend(row_samples)
        anchors.extend(row_anchors)
        causes.extend(row_causes)
        aggregates.append(_aggregate_row(record, row_samples, row_anchors, row_causes))

    _reconcile_atlas(observatory_report, samples, anchors, causes, aggregates)
    return {
        "schema_version": 1,
        "facility": "BAB-CS Bound Coverage Atlas",
        "source": current_source,
        "observatory_report_sha256": observatory_report_sha256,
        "observatory_manifest": str(manifest_path),
        "atlas_manifest_sha256": _sha256_file(Path(atlas_manifest_path)),
        "authority_note": (
            "Actual authority error is analytic or refined-replay relative. Recursive bound "
            "coverage is empirical characterization, not a formal physical-error enclosure."
        ),
        "sample_count": len(samples),
        "anchor_count": len(anchors),
        "cause_count": len(causes),
        "aggregates": aggregates,
        "anchors": anchors,
        "causes": causes,
        "samples": samples,
    }


def write_atlas_json(path: str | Path, atlas: dict[str, Any], *, overwrite: bool = False) -> None:
    output = _prepare_output(path, overwrite)
    output.write_text(
        json.dumps(atlas, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_sample_csv(path: str | Path, atlas: dict[str, Any], *, overwrite: bool = False) -> None:
    output = _prepare_output(path, overwrite)
    fields = sorted({key for row in atlas["samples"] for key in row})
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(atlas["samples"])


def write_atlas_plots(
    directory: str | Path,
    atlas: dict[str, Any],
    *,
    overwrite: bool = False,
) -> None:
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    _write_scatter_svg(
        root / "error-versus-bound.svg",
        [
            (
                row["recursive_internal_bound"],
                row["authority_epoch_drift_error"],
                f'{row["row_id"]}:{row["sample_index"]}',
            )
            for row in atlas["samples"]
            if row["coverage_eligible"]
            and row["recursive_internal_bound"] > 0.0
            and row["authority_epoch_drift_error"] > 0.0
        ],
        x_label="log10 recursive internal bound",
        y_label="log10 authority epoch drift error",
        overwrite=overwrite,
    )
    age_counts: Counter[str] = Counter()
    age_covered: Counter[str] = Counter()
    for row in atlas["samples"]:
        if not row["coverage_eligible"]:
            continue
        bucket = str(row["anchor_age_bucket"])
        age_counts[bucket] += 1
        age_covered[bucket] += int(bool(row["covered"]))
    _write_bar_svg(
        root / "coverage-versus-anchor-age.svg",
        [
            (bucket, age_covered[bucket] / age_counts[bucket])
            for bucket in sorted(age_counts, key=_age_bucket_key)
        ],
        y_label="empirical coverage fraction",
        overwrite=overwrite,
    )
    _write_scatter_svg(
        root / "phase-versus-energy.svg",
        [
            (
                abs(row["relative_energy_error"]),
                row["phase_error_radians"],
                f'{row["row_id"]}:{row["sample_index"]}',
            )
            for row in atlas["samples"]
            if row["phase_error_radians"] is not None
            and row["phase_error_radians"] > 0.0
            and abs(row["relative_energy_error"]) > 0.0
        ],
        x_label="log10 absolute relative energy error",
        y_label="log10 phase error radians",
        overwrite=overwrite,
    )
    cause_counts = Counter(cause["reason_code"] for cause in atlas["causes"])
    _write_bar_svg(
        root / "rejection-and-fallback-causes.svg",
        sorted(cause_counts.items()),
        y_label="count",
        overwrite=overwrite,
    )


def _row_samples(
    record: dict[str, Any],
    case: dict[str, Any],
    circuit,
    config: BABCSConfig,
    result,
    provider: AuthorityProvider,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    authority_states = [provider.state_at(point.time) for point in result.points]
    authority_hash = _authority_sample_hash(result.points, authority_states)
    epoch_candidate = result.points[0].state.evaluation.dynamic_state
    epoch_authority = authority_states[0]
    epoch_time = result.points[0].time
    epoch_generation = 0
    age_steps = 0
    row_samples: list[dict[str, Any]] = []
    row_anchors: list[dict[str, Any]] = []
    row_causes: list[dict[str, Any]] = []
    oscillator = case.get("oscillator")

    for sample_index, (point, authority_state) in enumerate(
        zip(result.points[1:], authority_states[1:], strict=True),
        start=1,
    ):
        metrics = point.metrics
        assert metrics is not None
        candidate_state = point.state.evaluation.dynamic_state
        actual_error = _scaled_error(candidate_state, authority_state, config)
        candidate_delta = tuple(
            value - anchor for value, anchor in zip(candidate_state, epoch_candidate, strict=True)
        )
        authority_delta = tuple(
            value - anchor for value, anchor in zip(authority_state, epoch_authority, strict=True)
        )
        epoch_error = _scaled_error(candidate_delta, authority_delta, config)
        coverage_eligible = (
            math.isfinite(metrics.estimated_bound)
            and metrics.estimated_bound > 0.0
            and not metrics.periodic_reanchor
            and not point.event_boundary
        )
        error_to_bound = (
            epoch_error / metrics.estimated_bound if coverage_eligible else None
        )
        bound_to_error = (
            metrics.estimated_bound / epoch_error
            if coverage_eligible and epoch_error > 0.0
            else None
        )
        covered = epoch_error <= metrics.estimated_bound if coverage_eligible else None
        authority_evaluation = circuit.evaluate(point.time, authority_state)
        energy_scale = max(abs(authority_evaluation.stored_energy), config.energy_absolute_tolerance)
        relative_energy_error = (
            point.state.evaluation.stored_energy - authority_evaluation.stored_energy
        ) / energy_scale
        phase_error = _phase_error(case, candidate_state, authority_state)
        age_steps += 1
        reason_codes = [classify_reason(rejection.reason) for rejection in point.rejections]
        sample = {
            "row_id": record["row_id"],
            "case_id": record["case_id"],
            "method": record["method"],
            "sample_index": sample_index,
            "time": point.time,
            "accepted_step": point.state.accepted_step,
            "event_boundary": point.event_boundary,
            "history_reset_reason": point.history_reset_reason,
            "candidate_effective_method": metrics.candidate_effective_method,
            "accepted_method": metrics.method,
            "authority_type": provider.authority_type,
            "authority_sample_sha256": authority_hash,
            "actual_authority_error": actual_error,
            "authority_epoch_drift_error": epoch_error,
            "recursive_internal_bound": metrics.estimated_bound,
            "pre_reset_recursive_bound": metrics.pre_reset_estimated_bound,
            "coverage_eligible": coverage_eligible,
            "covered": covered,
            "error_to_bound_ratio": error_to_bound,
            "bound_to_error_coverage_ratio": bound_to_error,
            "zero_epoch_error": coverage_eligible and epoch_error == 0.0,
            "anchor_generation": epoch_generation,
            "anchor_age_steps": age_steps,
            "anchor_age_seconds": point.time - epoch_time,
            "anchor_age_bucket": _age_bucket(age_steps),
            "anchor_deviation": metrics.anchor_reference_error,
            "periodic_reanchor": metrics.periodic_reanchor,
            "safety_reanchor": metrics.safety_reanchor,
            "phase_error_radians": phase_error,
            "candidate_stored_energy": point.state.evaluation.stored_energy,
            "authority_stored_energy": authority_evaluation.stored_energy,
            "relative_energy_error": relative_energy_error,
            "energy_balance_error": metrics.energy_balance_error,
            "energy_injection_ratio": metrics.energy_injection_ratio,
            "candidate_source_power": point.state.evaluation.source_power,
            "candidate_dissipated_power": point.state.evaluation.dissipated_power,
            "authority_source_power": authority_evaluation.source_power,
            "authority_dissipated_power": authority_evaluation.dissipated_power,
            "algebraic_residual": metrics.algebraic_residual,
            "full_residual": metrics.full_residual,
            "dynamic_reference_checkpoint": metrics.dynamic_reference_checkpoint,
            "implicit_authority_transfer": (
                metrics.method.startswith("implicit_") or metrics.method.endswith("_startup")
            ),
            "implicit_fallback": "fallback" in metrics.method,
            "rejection_count": point.rejection_count,
            "primary_rejection_code": reason_codes[-1] if reason_codes else None,
            "contributing_rejection_codes": "|".join(sorted(set(reason_codes))),
        }
        row_samples.append(sample)

        for rejection_index, rejection in enumerate(point.rejections):
            row_causes.append(
                {
                    "row_id": record["row_id"],
                    "case_id": record["case_id"],
                    "method": record["method"],
                    "sample_index": sample_index,
                    "rejection_index": rejection_index,
                    "time": result.points[sample_index - 1].time,
                    "reason_code": classify_reason(rejection.reason),
                    "reason": rejection.reason,
                    "primary": rejection_index == len(point.rejections) - 1,
                    "requested_step": rejection.requested_step,
                    "suggested_step": rejection.suggested_step,
                }
            )
        if sample["implicit_fallback"]:
            row_causes.append(
                {
                    "row_id": record["row_id"],
                    "case_id": record["case_id"],
                    "method": record["method"],
                    "sample_index": sample_index,
                    "rejection_index": None,
                    "time": point.time,
                    "reason_code": "implicit_fallback",
                    "reason": metrics.method,
                    "primary": True,
                    "requested_step": point.state.accepted_step,
                    "suggested_step": point.state.accepted_step,
                }
            )

        if metrics.periodic_reanchor:
            pre_anchor_state = metrics.pre_anchor_dynamic_state
            if pre_anchor_state is None:
                raise ValueError(f"{record['row_id']}: anchor is missing provisional state")
            pre_anchor_error = _scaled_error(pre_anchor_state, authority_state, config)
            row_anchors.append(
                {
                    "row_id": record["row_id"],
                    "case_id": record["case_id"],
                    "method": record["method"],
                    "sample_index": sample_index,
                    "time": point.time,
                    "event_forced": point.event_boundary,
                    "safety_reanchor": metrics.safety_reanchor,
                    "generation_before": epoch_generation,
                    "generation_after": epoch_generation + 1,
                    "authority_age_steps": age_steps,
                    "authority_age_seconds": point.time - epoch_time,
                    "pre_reset_recursive_bound": metrics.pre_reset_estimated_bound,
                    "anchor_deviation": metrics.anchor_reference_error,
                    "actual_authority_error_before_replacement": pre_anchor_error,
                    "actual_authority_error_after_replacement": actual_error,
                    "replay_method": config.reference_method,
                    "replay_steps": metrics.replay_steps,
                    "replay_refinement_substeps": metrics.replay_refinement_substeps,
                    "replay_refinement_retries": metrics.replay_refinement_retries,
                    "replay_embedded_error": metrics.replay_embedded_error,
                    "energy_balance_error": metrics.energy_balance_error,
                    "energy_injection_ratio": metrics.energy_injection_ratio,
                    "algebraic_residual": metrics.algebraic_residual,
                    "full_residual": metrics.full_residual,
                }
            )
            epoch_generation += 1
            epoch_candidate = candidate_state
            epoch_authority = authority_state
            epoch_time = point.time
            age_steps = 0

    return row_samples, row_anchors, row_causes


def _aggregate_row(
    record: dict[str, Any],
    samples: list[dict[str, Any]],
    anchors: list[dict[str, Any]],
    causes: list[dict[str, Any]],
) -> dict[str, Any]:
    eligible = [sample for sample in samples if sample["coverage_eligible"]]
    ratios = [sample["error_to_bound_ratio"] for sample in eligible]
    uncovered_run = 0
    maximum_uncovered_run = 0
    for sample in eligible:
        if sample["covered"]:
            uncovered_run = 0
        else:
            uncovered_run += 1
            maximum_uncovered_run = max(maximum_uncovered_run, uncovered_run)
    age_counts: Counter[str] = Counter()
    age_covered: Counter[str] = Counter()
    for sample in eligible:
        bucket = str(sample["anchor_age_bucket"])
        age_counts[bucket] += 1
        age_covered[bucket] += int(bool(sample["covered"]))
    cause_counts = Counter(cause["reason_code"] for cause in causes)
    phase_values = [sample["phase_error_radians"] for sample in samples if sample["phase_error_radians"] is not None]
    return {
        "row_id": record["row_id"],
        "case_id": record["case_id"],
        "method": record["method"],
        "accepted_sample_count": len(samples),
        "coverage_eligible_count": len(eligible),
        "covered_count": sum(bool(sample["covered"]) for sample in eligible),
        "empirical_coverage_fraction": (
            sum(bool(sample["covered"]) for sample in eligible) / len(eligible)
            if eligible
            else None
        ),
        "median_error_to_bound_ratio": _percentile(ratios, 0.5),
        "p95_error_to_bound_ratio": _percentile(ratios, 0.95),
        "maximum_error_to_bound_ratio": max(ratios, default=None),
        "maximum_consecutive_uncovered_samples": maximum_uncovered_run,
        "maximum_actual_authority_error": max(
            (sample["actual_authority_error"] for sample in samples),
            default=0.0,
        ),
        "maximum_recursive_internal_bound": max(
            (sample["recursive_internal_bound"] for sample in samples),
            default=0.0,
        ),
        "maximum_anchor_deviation": max(
            (anchor["anchor_deviation"] for anchor in anchors),
            default=0.0,
        ),
        "maximum_phase_error_radians": max(phase_values, default=None),
        "maximum_absolute_relative_energy_error": max(
            (abs(sample["relative_energy_error"]) for sample in samples),
            default=0.0,
        ),
        "maximum_energy_injection_ratio": max(
            (sample["energy_injection_ratio"] for sample in samples),
            default=0.0,
        ),
        "anchor_count": len(anchors),
        "event_anchor_count": sum(anchor["event_forced"] for anchor in anchors),
        "safety_anchor_count": sum(anchor["safety_reanchor"] for anchor in anchors),
        "fallback_count": sum(sample["implicit_fallback"] for sample in samples),
        "rejection_count": sum(sample["rejection_count"] for sample in samples),
        "cause_counts": dict(sorted(cause_counts.items())),
        "coverage_by_anchor_age": {
            bucket: {
                "eligible": age_counts[bucket],
                "covered": age_covered[bucket],
                "fraction": age_covered[bucket] / age_counts[bucket],
            }
            for bucket in sorted(age_counts, key=_age_bucket_key)
        },
    }


def _authority_provider(case: dict[str, Any], input_path: Path) -> AuthorityProvider:
    circuit, simulation, config = load_case(input_path)
    authority = case["authority"]
    if authority["type"] == "analytic":
        return AuthorityProvider(
            state_at=lambda time: _analytic_state(authority, time),
            authority_type="analytic",
            identity=authority,
        )
    reference_method = str(authority.get("method", "trapezoidal"))
    reference_config = BABCSConfig(
        **{
            **config.__dict__,
            "rollout_mode": "disabled",
            "reference_method": reference_method,
            "anchor_interval_steps": 1_000_000_000,
        }
    )
    reference = Simulator(BoundedAdamsBashforthIntegrator(reference_config)).run(
        circuit,
        simulation["stop_time"],
        float(authority["maximum_step"]),
        start_time=simulation["start_time"],
    )
    traces = [reference.dynamic_trace(index) for index in range(circuit.dynamic_size)]
    return AuthorityProvider(
        state_at=lambda time: tuple(interpolate_trace(trace, time) for trace in traces),
        authority_type="refined_replay",
        identity=authority,
    )


def _config_from_record(configuration: dict[str, Any]) -> BABCSConfig:
    values = dict(configuration)
    implicit = values.get("implicit_settings")
    if isinstance(implicit, dict):
        values["implicit_settings"] = ImplicitSettings(**implicit)
    return BABCSConfig(**values)


def _scaled_error(left, right, config: BABCSConfig) -> float:
    difference = [left_value - right_value for left_value, right_value in zip(left, right, strict=True)]
    return weighted_rms(
        difference,
        left,
        right,
        config.absolute_tolerance,
        config.relative_tolerance,
    )


def _phase_error(case: dict[str, Any], candidate, authority) -> float | None:
    oscillator = case.get("oscillator")
    indices = [int(value) for value in case["state_indices"]]
    if not isinstance(oscillator, dict) or len(indices) < 2:
        return None
    voltage_index, current_index = indices[:2]
    phase_scale = math.sqrt(float(oscillator["inductance"]) / float(oscillator["capacitance"]))
    candidate_phase = math.atan2(candidate[current_index] * phase_scale, candidate[voltage_index])
    authority_phase = math.atan2(authority[current_index] * phase_scale, authority[voltage_index])
    return abs(
        math.atan2(
            math.sin(candidate_phase - authority_phase),
            math.cos(candidate_phase - authority_phase),
        )
    )


def _authority_sample_hash(points, states) -> str:
    digest = hashlib.sha256()
    for point, state in zip(points, states, strict=True):
        digest.update(point.time.hex().encode("ascii"))
        digest.update(b"\0")
        for value in state:
            digest.update(value.hex().encode("ascii"))
            digest.update(b"\0")
    return digest.hexdigest()


def _age_bucket(age: int) -> str:
    if age <= 3:
        return "0-3"
    if age <= 7:
        return "4-7"
    if age <= 15:
        return "8-15"
    return "16+"


def _age_bucket_key(value: str) -> int:
    return {"0-3": 0, "4-7": 1, "8-15": 2, "16+": 3}.get(value, 99)


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[index]


def _reconcile_atlas(observatory, samples, anchors, causes, aggregates) -> None:
    records = {record["row_id"]: record for record in observatory["results"]}
    aggregate_ids = {aggregate["row_id"] for aggregate in aggregates}
    if aggregate_ids != set(records):
        raise ValueError("atlas aggregates do not cover every observatory row")
    sample_counts = Counter(sample["row_id"] for sample in samples)
    anchor_counts = Counter(anchor["row_id"] for anchor in anchors)
    cause_counts = Counter(cause["row_id"] for cause in causes)
    for aggregate in aggregates:
        row_id = aggregate["row_id"]
        record = records[row_id]
        if sample_counts[row_id] != record["diagnostics"]["accepted_steps"]:
            raise ValueError(f"{row_id}: atlas accepted samples do not reconcile")
        if anchor_counts[row_id] != record["diagnostics"]["periodic_reanchors"]:
            raise ValueError(f"{row_id}: atlas anchor count does not reconcile")
        expected_causes = aggregate["rejection_count"] + aggregate["fallback_count"]
        if cause_counts[row_id] != expected_causes:
            raise ValueError(f"{row_id}: atlas cause count does not reconcile")


def _write_scatter_svg(path, points, *, x_label, y_label, overwrite) -> None:
    output = _prepare_output(path, overwrite)
    width, height, margin = 900, 520, 70
    positive = [(x, y, label) for x, y, label in points if x > 0.0 and y > 0.0]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width/2}" y="{height-18}" text-anchor="middle" font-family="sans-serif">{html.escape(x_label)}</text>',
        f'<text x="18" y="{height/2}" text-anchor="middle" transform="rotate(-90 18 {height/2})" font-family="sans-serif">{html.escape(y_label)}</text>',
    ]
    if positive:
        xs = [math.log10(point[0]) for point in positive]
        ys = [math.log10(point[1]) for point in positive]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        xspan, yspan = max(xmax - xmin, 1.0), max(ymax - ymin, 1.0)
        for (x_value, y_value, label), x_log, y_log in zip(positive, xs, ys, strict=True):
            x = margin + (x_log - xmin) / xspan * (width - 2 * margin)
            y = height - margin - (y_log - ymin) / yspan * (height - 2 * margin)
            lines.append(f'<circle cx="{x:.6f}" cy="{y:.6f}" r="3"><title>{html.escape(label)}</title></circle>')
    else:
        lines.append('<text x="450" y="260" text-anchor="middle" font-family="sans-serif">No applicable positive samples</text>')
    lines.append("</svg>\n")
    output.write_text("\n".join(lines), encoding="utf-8")


def _write_bar_svg(path, values, *, y_label, overwrite) -> None:
    output = _prepare_output(path, overwrite)
    width, height, margin = 900, 520, 70
    maximum = max((float(value) for _, value in values), default=1.0)
    maximum = max(maximum, 1.0e-300)
    bar_width = (width - 2 * margin) / max(len(values), 1)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="18" y="{height/2}" text-anchor="middle" transform="rotate(-90 18 {height/2})" font-family="sans-serif">{html.escape(y_label)}</text>',
    ]
    for index, (label, value) in enumerate(values):
        bar_height = float(value) / maximum * (height - 2 * margin)
        x = margin + index * bar_width + 0.1 * bar_width
        y = height - margin - bar_height
        lines.append(f'<rect x="{x:.6f}" y="{y:.6f}" width="{0.8*bar_width:.6f}" height="{bar_height:.6f}" fill="#315b7d"><title>{html.escape(str(label))}: {value}</title></rect>')
    if not values:
        lines.append('<text x="450" y="260" text-anchor="middle" font-family="sans-serif">No applicable records</text>')
    lines.append("</svg>\n")
    output.write_text("\n".join(lines), encoding="utf-8")


def _prepare_output(path: str | Path, overwrite: bool) -> Path:
    output = Path(path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite bound atlas evidence: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the BAB-CS Bound Coverage Atlas")
    parser.add_argument("--observatory-report", required=True)
    parser.add_argument("--observatory-manifest")
    parser.add_argument("--atlas-manifest", default=str(DEFAULT_ATLAS_MANIFEST))
    parser.add_argument("--output", required=True)
    parser.add_argument("--sample-csv")
    parser.add_argument("--plot-directory")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    observatory_path = Path(arguments.observatory_report)
    observatory = json.loads(observatory_path.read_text(encoding="utf-8"))
    atlas = execute_bound_atlas(
        observatory,
        observatory_report_sha256=_sha256_file(observatory_path),
        observatory_manifest_path=arguments.observatory_manifest,
        atlas_manifest_path=arguments.atlas_manifest,
    )
    write_atlas_json(arguments.output, atlas, overwrite=arguments.overwrite)
    if arguments.sample_csv:
        write_sample_csv(arguments.sample_csv, atlas, overwrite=arguments.overwrite)
    if arguments.plot_directory:
        write_atlas_plots(arguments.plot_directory, atlas, overwrite=arguments.overwrite)
    print(
        json.dumps(
            {
                "rows": len(atlas["aggregates"]),
                "samples": atlas["sample_count"],
                "anchors": atlas["anchor_count"],
                "causes": atlas["cause_count"],
                "output": arguments.output,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
