from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from typing import Any, Callable

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from babcs import BABCSConfig, BoundedAdamsBashforthIntegrator, Simulator
from babcs.integrators import ImplicitSettings
from babcs.io import load_case, summary_data
from babcs.linalg import SingularMatrixError, solve_linear, weighted_rms
from babcs.model import Circuit
from tests.support.metrics import interpolate_trace
from tools.compare_methods import _analytic_state, _work_data, load_manifest, source_metadata
from tools.experiment_records import canonical_row_id, classify_reason
from tools.generate_runtime_cases import load_runtime_manifest
from tools.runtime_benchmark import (
    analytic_authority,
    common_grid,
    refined_authority,
    trace_time_tolerance,
    trajectory_error,
)


DEFAULT_ATLAS_MANIFEST = REPOSITORY_ROOT / "benchmarks/atlas/manifest.json"
DEFAULT_RUNTIME_ATLAS_MANIFEST = (
    REPOSITORY_ROOT / "benchmarks/atlas/runtime-scaling.json"
)


@dataclass(frozen=True)
class AuthorityProvider:
    state_at: Callable[[float], tuple[float, ...]]
    authority_type: str
    identity: dict[str, Any]


@dataclass(frozen=True)
class GlobalDualTrajectory:
    pair_id: str
    coarse_refinement_factor: int
    fine_refinement_factor: int
    coarse_states: tuple[tuple[float, ...], ...]
    fine_states: tuple[tuple[float, ...], ...]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class GlobalDualTrajectorySweep:
    trajectories: tuple[GlobalDualTrajectory, ...]
    factor_states: dict[int, tuple[tuple[float, ...], ...]]
    safety_factors: tuple[float, ...]
    metadata: dict[str, Any]

    @property
    def primary(self) -> GlobalDualTrajectory:
        return self.trajectories[0]


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


def execute_runtime_bound_atlas(
    runtime_atlas_manifest_path: str | Path = DEFAULT_RUNTIME_ATLAS_MANIFEST,
    *,
    selected_cases: set[str] | None = None,
) -> dict[str, Any]:
    atlas_path = Path(runtime_atlas_manifest_path)
    atlas_manifest = json.loads(atlas_path.read_text(encoding="utf-8"))
    if atlas_manifest.get("schema_version") != 1:
        raise ValueError("unsupported runtime bound atlas manifest schema")
    runtime_manifest_value = atlas_manifest.get("runtime_manifest")
    if not isinstance(runtime_manifest_value, str) or not runtime_manifest_value:
        raise ValueError("runtime bound atlas requires a runtime_manifest path")
    runtime_manifest_path = atlas_path.parent / runtime_manifest_value
    runtime_manifest = load_runtime_manifest(runtime_manifest_path)
    requested = _runtime_atlas_cases(atlas_manifest, selected_cases=selected_cases)
    global_dual_settings = _global_dual_trajectory_settings(atlas_manifest)
    families = {str(family["id"]): family for family in runtime_manifest["families"]}
    source = source_metadata(REPOSITORY_ROOT)
    records: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    anchors: list[dict[str, Any]] = []
    causes: list[dict[str, Any]] = []
    aggregates: list[dict[str, Any]] = []
    qualifications: list[dict[str, Any]] = []

    for selection in requested:
        case_id = str(selection["id"])
        case_path = runtime_manifest_path.parent / "cases" / f"{case_id}.json"
        if not case_path.is_file():
            raise ValueError(f"{case_id}: generated runtime case does not exist")
        case_data = json.loads(case_path.read_text(encoding="utf-8"))
        runtime_metadata = case_data.get("runtime_benchmark")
        if not isinstance(runtime_metadata, dict):
            raise ValueError(f"{case_id}: generated case lacks runtime metadata")
        family_id = str(runtime_metadata.get("family_id", ""))
        family = families.get(family_id)
        if family is None:
            raise ValueError(f"{case_id}: runtime family is not declared")
        size = int(runtime_metadata.get("size", 0))
        if case_id != f"{family_id}-n{size:03d}":
            raise ValueError(f"{case_id}: runtime case identity is inconsistent")
        profile_id = str(runtime_metadata.get("babcs_profile_id", ""))
        if profile_id != str(family["babcs_profile"]):
            raise ValueError(f"{case_id}: runtime profile does not match its family")
        profile = runtime_manifest["babcs_profiles"][profile_id]
        if case_data.get("babcs", {}) != profile["config"]:
            raise ValueError(f"{case_id}: generated BAB-CS configuration is stale")

        circuit, simulation, config = load_case(case_path)
        config = replace(config, **selection["config_overrides"])
        backend = _runtime_atlas_backend(
            runtime_manifest,
            circuit,
            str(atlas_manifest.get("babcs_linear_backend", "hybrid")),
        )
        if backend != circuit.linear_backend:
            circuit = Circuit(circuit.elements, linear_backend=backend)
        step_divisor = int(selection["step_divisor"])
        nominal_step = float(simulation["nominal_step"]) / step_divisor
        result = Simulator(BoundedAdamsBashforthIntegrator(config)).run(
            circuit,
            simulation["stop_time"],
            nominal_step,
            start_time=simulation["start_time"],
        )
        provider, qualification = _runtime_authority_provider(
            case_id,
            case_path,
            family,
            circuit,
            result,
            runtime_manifest,
            backend,
        )
        qualification.update(
            {
                "case_id": case_id,
                "family_id": family_id,
                "size": size,
                "step_divisor": step_divisor,
                "nominal_step": nominal_step,
                "babcs_profile_id": profile_id,
                "linear_backend": backend,
            }
        )
        qualifications.append(qualification)
        if provider is None:
            continue

        global_dual_trajectory = _global_dual_trajectory(
            case_path,
            result,
            circuit=circuit,
            linear_backend=backend,
            settings=global_dual_settings,
        )

        configuration = asdict(config)
        variant_id = str(selection["variant_id"])
        method_id = profile_id if variant_id == "baseline" else f"{profile_id}:{variant_id}"
        row_id = canonical_row_id(
            case_id=case_id,
            method=method_id,
            nominal_step=nominal_step,
            anchor_interval=config.anchor_interval_steps,
            configuration=configuration,
        )
        diagnostics = summary_data(result)
        record = {
            "row_id": row_id,
            "case_id": case_id,
            "method": method_id,
            "nominal_step": nominal_step,
            "anchor_interval": config.anchor_interval_steps,
            "configuration": configuration,
            "diagnostics": diagnostics,
            "work": _work_data(diagnostics),
            "circuit_size": {
                "element_count": len(circuit.elements),
                "non_ground_node_count": len(circuit.nodes),
                "dynamic_state_count": circuit.dynamic_size,
                "algebraic_unknown_count": circuit.algebraic_size,
                "declared_mna_unknowns": (
                    circuit.dynamic_size + circuit.algebraic_size
                ),
            },
            "global_dual_trajectory": (
                None
                if global_dual_trajectory is None
                else global_dual_trajectory.metadata
            ),
        }
        row_samples, row_anchors, row_causes = _row_samples(
            record,
            family,
            circuit,
            config,
            result,
            provider,
            global_dual_trajectory,
        )
        records.append(record)
        samples.extend(row_samples)
        anchors.extend(row_anchors)
        causes.extend(row_causes)
        aggregate = _aggregate_row(record, row_samples, row_anchors, row_causes)
        aggregate.update(
            {
                "family_id": family_id,
                "size": size,
                "step_divisor": step_divisor,
                "babcs_profile_id": profile_id,
                "variant_id": variant_id,
                "linear_backend": backend,
                "circuit_size": record["circuit_size"],
            }
        )
        aggregates.append(aggregate)

    _reconcile_atlas({"results": records}, samples, anchors, causes, aggregates)
    common_policy_frontier = _global_common_policy_frontier(aggregates)
    order_aware_common_policy_frontier = (
        _global_order_aware_common_policy_frontier(aggregates)
    )
    order_aware_epoch_common_policy_frontier = (
        _global_order_aware_epoch_common_policy_frontier(aggregates)
    )
    order_aware_epoch_envelope_common_policy_frontier = (
        _global_order_aware_epoch_envelope_common_policy_frontier(aggregates)
    )
    statewise_four_level_common_policy_frontier = (
        _global_statewise_four_level_common_policy_frontier(aggregates)
    )
    statewise_epoch_common_policy_frontier = (
        _global_statewise_epoch_common_policy_frontier(aggregates)
    )
    two_term_modal_common_policy_frontier = (
        _global_two_term_modal_common_policy_frontier(aggregates)
    )
    modal_epoch_common_policy_frontier = (
        _global_modal_epoch_common_policy_frontier(aggregates)
    )
    temporally_aligned_modal_epoch_common_policy_frontier = (
        _global_temporally_aligned_modal_epoch_common_policy_frontier(
            aggregates
        )
    )
    return {
        "schema_version": 1,
        "facility": "BAB-CS Runtime Bound Coverage Atlas",
        "source": source,
        "runtime_atlas_manifest_sha256": _sha256_file(atlas_path),
        "runtime_manifest_sha256": _sha256_file(runtime_manifest_path),
        "runtime_manifest": str(runtime_manifest_path),
        "authority_note": (
            "The recursive bound is internal and reference-relative. Coverage against analytic "
            "or independently refined trajectory authority is empirical characterization and "
            "can expose reference-discretization error that the internal recurrence does not model."
        ),
        "claim_boundary": str(atlas_manifest["claim_boundary"]),
        "global_dual_trajectory": global_dual_settings,
        "global_refinement_work_accounting": {
            "unit": "unweighted solver events and iterations",
            "claim_boundary": (
                "Deterministic work units count solver operations but do not weight "
                "those operations by circuit dimension, matrix sparsity, factorization "
                "complexity, or runtime. They are diagnostic work counts, not a scaling "
                "cost or floating-point-operation estimate."
            ),
        },
        "global_refinement_common_policy_frontier": common_policy_frontier,
        "global_order_aware_common_policy_frontier": (
            order_aware_common_policy_frontier
        ),
        "global_order_aware_epoch_common_policy_frontier": (
            order_aware_epoch_common_policy_frontier
        ),
        "global_order_aware_epoch_envelope_common_policy_frontier": (
            order_aware_epoch_envelope_common_policy_frontier
        ),
        "global_statewise_four_level_common_policy_frontier": (
            statewise_four_level_common_policy_frontier
        ),
        "global_statewise_epoch_common_policy_frontier": (
            statewise_epoch_common_policy_frontier
        ),
        "global_two_term_modal_common_policy_frontier": (
            two_term_modal_common_policy_frontier
        ),
        "global_modal_epoch_common_policy_frontier": (
            modal_epoch_common_policy_frontier
        ),
        "global_temporally_aligned_modal_epoch_common_policy_frontier": (
            temporally_aligned_modal_epoch_common_policy_frontier
        ),
        "requested_case_count": len(requested),
        "qualified_case_count": len(records),
        "unqualified_case_count": len(requested) - len(records),
        "sample_count": len(samples),
        "anchor_count": len(anchors),
        "cause_count": len(causes),
        "authority_qualifications": qualifications,
        "aggregates": aggregates,
        "anchors": anchors,
        "causes": causes,
        "samples": samples,
    }


def _runtime_atlas_cases(
    manifest: dict[str, Any],
    *,
    selected_cases: set[str] | None,
) -> list[dict[str, Any]]:
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("runtime bound atlas requires a nonempty cases list")
    requested: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for value in cases:
        if not isinstance(value, dict):
            raise ValueError("runtime bound atlas cases must be objects")
        case_id = value.get("id")
        step_divisor = value.get("step_divisor")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("runtime bound atlas case ids must be nonempty strings")
        if case_id in identifiers:
            raise ValueError(f"duplicate runtime bound atlas case: {case_id}")
        identifiers.add(case_id)
        if not isinstance(step_divisor, int) or isinstance(step_divisor, bool) or step_divisor < 1:
            raise ValueError(f"{case_id}: step_divisor must be a positive integer")
        variant_id = value.get("variant_id", "baseline")
        if not isinstance(variant_id, str) or not variant_id:
            raise ValueError(f"{case_id}: variant_id must be a nonempty string")
        config_overrides = value.get("config_overrides", {})
        if not isinstance(config_overrides, dict):
            raise ValueError(f"{case_id}: config_overrides must be an object")
        valid_config_fields = {field.name for field in fields(BABCSConfig)}
        unknown_overrides = sorted(set(config_overrides) - valid_config_fields)
        if unknown_overrides:
            raise ValueError(
                f"{case_id}: unknown config overrides: " + ", ".join(unknown_overrides)
            )
        if selected_cases is None or case_id in selected_cases:
            requested.append(
                {
                    "id": case_id,
                    "step_divisor": step_divisor,
                    "variant_id": variant_id,
                    "config_overrides": config_overrides,
                }
            )
    if selected_cases is not None:
        missing = sorted(selected_cases - identifiers)
        if missing:
            raise ValueError(
                "unknown runtime bound atlas cases: " + ", ".join(missing)
            )
    if not requested:
        raise ValueError("runtime bound atlas selection is empty")
    return requested


def _global_dual_trajectory_settings(
    manifest: dict[str, Any],
) -> dict[str, Any] | None:
    value = manifest.get("global_dual_trajectory")
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("global_dual_trajectory must be an object")
    sampling_mode = str(value.get("sampling_mode", "interpolate"))
    if sampling_mode not in {"interpolate", "integrated_output_times"}:
        raise ValueError(
            "global dual-trajectory sampling_mode must be interpolate or integrated_output_times"
        )
    pair_values = value.get("refinement_pairs")
    if pair_values is None:
        pair_values = [
            {
                "coarse_refinement_factor": value.get("coarse_refinement_factor"),
                "fine_refinement_factor": value.get("fine_refinement_factor"),
            }
        ]
    if not isinstance(pair_values, list) or not pair_values:
        raise ValueError("global dual-trajectory refinement_pairs must be a nonempty list")
    refinement_pairs: list[dict[str, Any]] = []
    pair_ids: set[str] = set()
    for pair in pair_values:
        if not isinstance(pair, dict):
            raise ValueError("global dual-trajectory refinement pairs must be objects")
        coarse_factor = pair.get("coarse_refinement_factor")
        fine_factor = pair.get("fine_refinement_factor")
        if (
            not isinstance(coarse_factor, int)
            or isinstance(coarse_factor, bool)
            or coarse_factor < 2
        ):
            raise ValueError(
                "global coarse_refinement_factor must be an integer of at least two"
            )
        if (
            not isinstance(fine_factor, int)
            or isinstance(fine_factor, bool)
            or fine_factor <= coarse_factor
            or fine_factor % coarse_factor
        ):
            raise ValueError(
                "global fine_refinement_factor must be an integer multiple greater than coarse"
            )
        pair_id = f"{coarse_factor}x{fine_factor}"
        if pair_id in pair_ids:
            raise ValueError(f"duplicate global dual-trajectory refinement pair: {pair_id}")
        pair_ids.add(pair_id)
        refinement_pairs.append(
            {
                "pair_id": pair_id,
                "coarse_refinement_factor": coarse_factor,
                "fine_refinement_factor": fine_factor,
            }
        )
    safety_values = value.get("safety_factors", [1.0])
    if not isinstance(safety_values, list) or not safety_values:
        raise ValueError("global dual-trajectory safety_factors must be a nonempty list")
    safety_factors = tuple(sorted({float(factor) for factor in safety_values}))
    if any(not math.isfinite(factor) or factor <= 0.0 for factor in safety_factors):
        raise ValueError("global dual-trajectory safety factors must be positive and finite")
    order_aware_value = value.get("order_aware")
    order_aware = None
    if order_aware_value is not None:
        if not isinstance(order_aware_value, dict):
            raise ValueError("global dual-trajectory order_aware must be an object")
        expected_order = float(order_aware_value.get("expected_order", 2.0))
        minimum_order = float(order_aware_value.get("minimum_observed_order", 1.0))
        maximum_order = float(order_aware_value.get("maximum_observed_order", 3.0))
        discrepancy_floor = float(order_aware_value.get("discrepancy_floor", 1.0e-12))
        if (
            not math.isfinite(expected_order)
            or not math.isfinite(minimum_order)
            or not math.isfinite(maximum_order)
            or expected_order <= 0.0
            or minimum_order <= 0.0
            or maximum_order < minimum_order
        ):
            raise ValueError(
                "global order-aware observed-order bounds must be finite and positive"
            )
        if not math.isfinite(discrepancy_floor) or discrepancy_floor <= 0.0:
            raise ValueError(
                "global order-aware discrepancy_floor must be positive and finite"
            )
        triplets: list[dict[str, Any]] = []
        for coarse_pair in refinement_pairs:
            coarse_factor = int(coarse_pair["coarse_refinement_factor"])
            middle_factor = int(coarse_pair["fine_refinement_factor"])
            first_ratio = middle_factor / coarse_factor
            for fine_pair in refinement_pairs:
                if int(fine_pair["coarse_refinement_factor"]) != middle_factor:
                    continue
                fine_factor = int(fine_pair["fine_refinement_factor"])
                second_ratio = fine_factor / middle_factor
                if not math.isclose(first_ratio, second_ratio, rel_tol=0.0, abs_tol=0.0):
                    continue
                triplets.append(
                    {
                        "triplet_id": f"{coarse_factor}x{middle_factor}x{fine_factor}",
                        "coarse_refinement_factor": coarse_factor,
                        "middle_refinement_factor": middle_factor,
                        "fine_refinement_factor": fine_factor,
                        "coarse_pair_id": coarse_pair["pair_id"],
                        "fine_pair_id": fine_pair["pair_id"],
                        "refinement_ratio": first_ratio,
                    }
                )
        if not triplets:
            raise ValueError(
                "global order-aware qualification requires adjacent equal-ratio refinement pairs"
            )
        order_aware = {
            "expected_order": expected_order,
            "minimum_observed_order": minimum_order,
            "maximum_observed_order": maximum_order,
            "discrepancy_floor": discrepancy_floor,
            "triplets": triplets,
        }
    statewise_value = value.get("statewise_four_level")
    statewise_four_level = None
    if statewise_value is not None:
        if not isinstance(statewise_value, dict):
            raise ValueError(
                "global dual-trajectory statewise_four_level must be an object"
            )
        minimum_order = float(statewise_value.get("minimum_observed_order", 1.0))
        maximum_order = float(statewise_value.get("maximum_observed_order", 3.0))
        difference_floor = float(
            statewise_value.get("scaled_difference_floor", 1.0e-12)
        )
        maximum_order_difference = float(
            statewise_value.get("maximum_adjacent_order_difference", 0.5)
        )
        maximum_coefficient_difference = float(
            statewise_value.get("maximum_coefficient_relative_difference", 0.5)
        )
        maximum_residual_ratio = float(
            statewise_value.get("maximum_extrapolant_residual_ratio", 1.0)
        )
        numeric_values = (
            minimum_order,
            maximum_order,
            difference_floor,
            maximum_order_difference,
            maximum_coefficient_difference,
            maximum_residual_ratio,
        )
        if any(not math.isfinite(number) for number in numeric_values):
            raise ValueError("global statewise four-level gates must be finite")
        if (
            minimum_order <= 0.0
            or maximum_order < minimum_order
            or difference_floor <= 0.0
            or maximum_order_difference < 0.0
            or maximum_coefficient_difference < 0.0
            or maximum_residual_ratio <= 0.0
        ):
            raise ValueError(
                "global statewise four-level gates must have valid positive ranges"
            )
        factors = sorted(
            {
                int(pair[field])
                for pair in refinement_pairs
                for field in (
                    "coarse_refinement_factor",
                    "fine_refinement_factor",
                )
            }
        )
        quadruplets: list[dict[str, Any]] = []
        for index in range(len(factors) - 3):
            selected = factors[index : index + 4]
            ratios = [
                selected[position + 1] / selected[position]
                for position in range(3)
            ]
            if not all(
                math.isclose(ratio, ratios[0], rel_tol=0.0, abs_tol=0.0)
                for ratio in ratios[1:]
            ):
                continue
            quadruplets.append(
                {
                    "quadruplet_id": "x".join(str(factor) for factor in selected),
                    "refinement_factors": selected,
                    "refinement_ratio": ratios[0],
                }
            )
        if not quadruplets:
            raise ValueError(
                "global statewise four-level qualification requires four successive equal-ratio factors"
            )
        epoch_fit_value = statewise_value.get("epoch_fit")
        epoch_fit = None
        if epoch_fit_value is not None:
            if not isinstance(epoch_fit_value, dict):
                raise ValueError("global statewise epoch_fit must be an object")
            minimum_epoch_samples = int(
                epoch_fit_value.get("minimum_epoch_samples", 4)
            )
            minimum_direction_cosine = float(
                epoch_fit_value.get("minimum_pairwise_direction_cosine", 0.9)
            )
            maximum_unmatched_sign_changes = int(
                epoch_fit_value.get(
                    "maximum_unmatched_sign_change_intervals",
                    0,
                )
            )
            modal_fit_value = epoch_fit_value.get("modal_fit")
            modal_fit = None
            if modal_fit_value is not None:
                if not isinstance(modal_fit_value, dict):
                    raise ValueError("global statewise modal_fit must be an object")
                temporal_alignment_value = modal_fit_value.get(
                    "temporal_alignment"
                )
                temporal_alignment = None
                if temporal_alignment_value is not None:
                    if not isinstance(temporal_alignment_value, dict):
                        raise ValueError(
                            "global statewise modal temporal_alignment must be an object"
                        )
                    temporal_alignment = {
                        "maximum_sample_lag": int(
                            temporal_alignment_value.get(
                                "maximum_sample_lag",
                                1,
                            )
                        ),
                    }
                    if temporal_alignment["maximum_sample_lag"] < 1:
                        raise ValueError(
                            "global statewise modal temporal_alignment maximum_sample_lag must be positive"
                        )
                five_level_value = modal_fit_value.get("five_level_two_term")
                five_level_two_term = None
                if five_level_value is not None:
                    if not isinstance(five_level_value, dict):
                        raise ValueError(
                            "global statewise modal five_level_two_term must be an object"
                        )
                    training_factors = tuple(
                        int(value)
                        for value in five_level_value.get(
                            "training_refinement_factors",
                            (2, 4, 8, 16),
                        )
                    )
                    holdout_factor = int(
                        five_level_value.get("holdout_refinement_factor", 32)
                    )
                    fallback_candidates = [
                        quadruplet
                        for quadruplet in quadruplets
                        if int(quadruplet["refinement_factors"][-1])
                        == holdout_factor
                    ]
                    fallback_quadruplet_id = str(
                        five_level_value.get(
                            "fallback_quadruplet_id",
                            (
                                fallback_candidates[-1]["quadruplet_id"]
                                if fallback_candidates
                                else ""
                            ),
                        )
                    )
                    primary_order = float(
                        five_level_value.get("primary_order", 2.0)
                    )
                    secondary_orders = tuple(
                        float(value)
                        for value in five_level_value.get(
                            "secondary_orders",
                            (3.0, 4.0),
                        )
                    )
                    maximum_condition = float(
                        five_level_value.get(
                            "maximum_design_condition_number",
                            1.0e3,
                        )
                    )
                    maximum_training_ratio = float(
                        five_level_value.get(
                            "maximum_training_residual_ratio",
                            0.25,
                        )
                    )
                    maximum_holdout_ratio = float(
                        five_level_value.get(
                            "maximum_holdout_residual_ratio",
                            1.0,
                        )
                    )
                    if len(training_factors) < 4:
                        raise ValueError(
                            "global statewise modal five_level_two_term requires at least four training factors"
                        )
                    if (
                        len(set(training_factors)) != len(training_factors)
                        or any(value < 1 for value in training_factors)
                        or tuple(sorted(training_factors)) != training_factors
                    ):
                        raise ValueError(
                            "global statewise modal five_level_two_term training factors must be unique positive ascending integers"
                        )
                    if holdout_factor in training_factors or holdout_factor < 1:
                        raise ValueError(
                            "global statewise modal five_level_two_term holdout factor must be positive and distinct"
                        )
                    fallback_quadruplets = {
                        str(quadruplet["quadruplet_id"]): quadruplet
                        for quadruplet in fallback_candidates
                    }
                    if fallback_quadruplet_id not in fallback_quadruplets:
                        raise ValueError(
                            "global statewise modal five_level_two_term fallback quadruplet must end at the holdout factor"
                        )
                    available_factors = set(factors)
                    if not set(training_factors) | {holdout_factor} <= available_factors:
                        raise ValueError(
                            "global statewise modal five_level_two_term factors must be available in the refinement sweep"
                        )
                    if (
                        not math.isfinite(primary_order)
                        or primary_order <= 0.0
                        or not secondary_orders
                        or len(set(secondary_orders)) != len(secondary_orders)
                        or any(
                            not math.isfinite(order) or order <= primary_order
                            for order in secondary_orders
                        )
                    ):
                        raise ValueError(
                            "global statewise modal five_level_two_term orders must be finite, unique, and greater than the primary order"
                        )
                    if any(
                        not math.isfinite(value) or value <= 0.0
                        for value in (
                            maximum_condition,
                            maximum_training_ratio,
                            maximum_holdout_ratio,
                        )
                    ):
                        raise ValueError(
                            "global statewise modal five_level_two_term gates must be finite and positive"
                        )
                    five_level_two_term = {
                        "training_refinement_factors": list(training_factors),
                        "holdout_refinement_factor": holdout_factor,
                        "fallback_quadruplet_id": fallback_quadruplet_id,
                        "primary_order": primary_order,
                        "secondary_orders": list(secondary_orders),
                        "maximum_design_condition_number": maximum_condition,
                        "maximum_training_residual_ratio": maximum_training_ratio,
                        "maximum_holdout_residual_ratio": maximum_holdout_ratio,
                        "scaled_difference_floor": difference_floor,
                        "policies": [
                            {
                                "policy_id": (
                                    f"p{primary_order:g}q{secondary_order:g}"
                                ),
                                "primary_order": primary_order,
                                "secondary_order": secondary_order,
                                "training_refinement_factors": list(
                                    training_factors
                                ),
                                "holdout_refinement_factor": holdout_factor,
                            }
                            for secondary_order in secondary_orders
                        ],
                    }
                modal_fit = {
                    "maximum_symmetry_relative_error": float(
                        modal_fit_value.get(
                            "maximum_symmetry_relative_error",
                            1.0e-10,
                        )
                    ),
                    "maximum_eigen_residual_relative_error": float(
                        modal_fit_value.get(
                            "maximum_eigen_residual_relative_error",
                            1.0e-9,
                        )
                    ),
                    "maximum_orthogonality_error": float(
                        modal_fit_value.get(
                            "maximum_orthogonality_error",
                            1.0e-9,
                        )
                    ),
                    "repeated_eigenvalue_relative_tolerance": float(
                        modal_fit_value.get(
                            "repeated_eigenvalue_relative_tolerance",
                            1.0e-9,
                        )
                    ),
                    "repeated_eigenvalue_absolute_tolerance": float(
                        modal_fit_value.get(
                            "repeated_eigenvalue_absolute_tolerance",
                            1.0e-12,
                        )
                    ),
                    "maximum_jacobi_sweeps": int(
                        modal_fit_value.get("maximum_jacobi_sweeps", 128)
                    ),
                    "temporal_alignment": temporal_alignment,
                    "five_level_two_term": five_level_two_term,
                }
                modal_numeric = tuple(
                    float(modal_fit[name])
                    for name in (
                        "maximum_symmetry_relative_error",
                        "maximum_eigen_residual_relative_error",
                        "maximum_orthogonality_error",
                        "repeated_eigenvalue_relative_tolerance",
                        "repeated_eigenvalue_absolute_tolerance",
                    )
                )
                if any(not math.isfinite(number) or number < 0.0 for number in modal_numeric):
                    raise ValueError(
                        "global statewise modal_fit tolerances must be finite and nonnegative"
                    )
                if modal_fit["maximum_jacobi_sweeps"] < 1:
                    raise ValueError(
                        "global statewise modal_fit maximum_jacobi_sweeps must be positive"
                    )
            if minimum_epoch_samples < 2:
                raise ValueError(
                    "global statewise epoch_fit minimum_epoch_samples must be at least two"
                )
            if (
                not math.isfinite(minimum_direction_cosine)
                or not 0.0 <= minimum_direction_cosine <= 1.0
            ):
                raise ValueError(
                    "global statewise epoch_fit direction cosine must lie between zero and one"
                )
            if maximum_unmatched_sign_changes < 0:
                raise ValueError(
                    "global statewise epoch_fit unmatched sign-change limit must be nonnegative"
                )
            epoch_fit = {
                "minimum_epoch_samples": minimum_epoch_samples,
                "minimum_pairwise_direction_cosine": minimum_direction_cosine,
                "maximum_unmatched_sign_change_intervals": (
                    maximum_unmatched_sign_changes
                ),
                "modal_fit": modal_fit,
            }
        statewise_four_level = {
            "minimum_observed_order": minimum_order,
            "maximum_observed_order": maximum_order,
            "scaled_difference_floor": difference_floor,
            "maximum_adjacent_order_difference": maximum_order_difference,
            "maximum_coefficient_relative_difference": (
                maximum_coefficient_difference
            ),
            "maximum_extrapolant_residual_ratio": maximum_residual_ratio,
            "quadruplets": quadruplets,
            "epoch_fit": epoch_fit,
        }
    return {
        "method": "trapezoidal",
        "sampling_mode": sampling_mode,
        "refinement_pairs": refinement_pairs,
        "safety_factors": list(safety_factors),
        "order_aware": order_aware,
        "statewise_four_level": statewise_four_level,
    }


def _global_dual_trajectory(
    case_path: Path,
    result,
    *,
    circuit: Circuit,
    linear_backend: str,
    settings: dict[str, Any] | None,
) -> GlobalDualTrajectorySweep | None:
    if settings is None:
        return None
    _, simulation, _ = load_case(case_path)
    times = tuple(point.time for point in result.points)
    factor_results: dict[int, tuple[tuple[tuple[float, ...], ...], dict[str, Any]]] = {}
    for pair in settings["refinement_pairs"]:
        for factor in (
            int(pair["coarse_refinement_factor"]),
            int(pair["fine_refinement_factor"]),
        ):
            if factor in factor_results:
                continue
            factor_results[factor] = refined_authority(
                case_path,
                times,
                refinement_factor=factor,
                linear_backend=linear_backend,
                sampling_mode=str(settings["sampling_mode"]),
            )
    trajectories: list[GlobalDualTrajectory] = []
    pair_metadata: list[dict[str, Any]] = []
    for pair in settings["refinement_pairs"]:
        pair_id = str(pair["pair_id"])
        coarse_factor = int(pair["coarse_refinement_factor"])
        fine_factor = int(pair["fine_refinement_factor"])
        coarse_states, coarse_metadata = factor_results[coarse_factor]
        fine_states, fine_metadata = factor_results[fine_factor]
        if len(coarse_states) != len(result.points) or len(fine_states) != len(result.points):
            raise ValueError("global dual trajectories do not align with BAB-CS output points")
        metadata = {
            **pair,
            "coarse_trace_sha256": coarse_metadata["trace_sha256"],
            "fine_trace_sha256": fine_metadata["trace_sha256"],
            "coarse_native_points": coarse_metadata["native_points"],
            "fine_native_points": fine_metadata["native_points"],
            "coarse_work": coarse_metadata["work"],
            "fine_work": fine_metadata["work"],
            "independent_pair_work_units": (
                coarse_metadata["work"]["deterministic_work_units"]
                + fine_metadata["work"]["deterministic_work_units"]
            ),
        }
        pair_metadata.append(metadata)
        trajectories.append(
            GlobalDualTrajectory(
                pair_id=pair_id,
                coarse_refinement_factor=coarse_factor,
                fine_refinement_factor=fine_factor,
                coarse_states=coarse_states,
                fine_states=fine_states,
                metadata=metadata,
            )
        )
    factor_metadata = {
        str(factor): {
            "refinement_factor": factor,
            "nominal_step": float(simulation["nominal_step"]) / factor,
            "sampling_mode": metadata["sampling_mode"],
            "configured_minimum_step": metadata["configured_minimum_step"],
            "effective_minimum_step": metadata["effective_minimum_step"],
            "configured_anchor_interval_steps": metadata[
                "configured_anchor_interval_steps"
            ],
            "effective_anchor_interval_steps": metadata[
                "effective_anchor_interval_steps"
            ],
            "output_interval_substeps": metadata["output_interval_substeps"],
            "trace_sha256": metadata["trace_sha256"],
            "native_points": metadata["native_points"],
            "work": metadata["work"],
        }
        for factor, (_, metadata) in sorted(factor_results.items())
    }
    primary = trajectories[0]
    statewise_settings = settings.get("statewise_four_level")
    epoch_fit = (
        statewise_settings.get("epoch_fit")
        if isinstance(statewise_settings, dict)
        else None
    )
    modal_fit = epoch_fit.get("modal_fit") if isinstance(epoch_fit, dict) else None
    modal_basis = (
        _modal_basis_metadata(
            circuit,
            result.points[0].state.evaluation,
            modal_fit,
        )
        if isinstance(modal_fit, dict)
        else None
    )
    return GlobalDualTrajectorySweep(
        trajectories=tuple(trajectories),
        factor_states={
            factor: states for factor, (states, _) in factor_results.items()
        },
        safety_factors=tuple(float(value) for value in settings["safety_factors"]),
        metadata={
            **settings,
            "pairs": pair_metadata,
            "factor_trajectories": factor_metadata,
            "modal_basis": modal_basis,
            "start_time": float(simulation["start_time"]),
            "stop_time": float(simulation["stop_time"]),
            "sweep_deterministic_work_units": sum(
                metadata["work"]["deterministic_work_units"]
                for _, metadata in factor_results.values()
            ),
            "coarse_refinement_factor": primary.coarse_refinement_factor,
            "fine_refinement_factor": primary.fine_refinement_factor,
            "coarse_trace_sha256": primary.metadata["coarse_trace_sha256"],
            "fine_trace_sha256": primary.metadata["fine_trace_sha256"],
            "coarse_native_points": primary.metadata["coarse_native_points"],
            "fine_native_points": primary.metadata["fine_native_points"],
        },
    )


def _runtime_atlas_backend(
    runtime_manifest: dict[str, Any],
    circuit: Circuit,
    requested_backend: str,
) -> str:
    if requested_backend not in {"dense", "scipy", "hybrid"}:
        raise ValueError("runtime bound atlas backend must be dense, scipy, or hybrid")
    if requested_backend != "hybrid":
        return requested_backend
    profile = runtime_manifest["babcs_backend_profiles"]["hybrid"]
    threshold = int(profile["sparse_minimum_declared_mna_unknowns"])
    declared_mna_unknowns = circuit.dynamic_size + circuit.algebraic_size
    return "scipy" if declared_mna_unknowns >= threshold else "dense"


def _runtime_authority_provider(
    case_id: str,
    case_path: Path,
    family: dict[str, Any],
    circuit: Circuit,
    result,
    runtime_manifest: dict[str, Any],
    linear_backend: str,
) -> tuple[AuthorityProvider | None, dict[str, Any]]:
    times = tuple(point.time for point in result.points)
    authority_type = str(family["authority"]["type"])
    if authority_type.startswith("analytic_"):
        states = analytic_authority(family, circuit.dynamic_size, times)
        identity = {
            "type": authority_type,
            "qualified": True,
            "convergence": {
                "type": "analytic_exact",
                "maximum_scaled_error": 0.0,
            },
            "trace_sha256": _authority_sample_hash(result.points, states),
        }
        return _sampled_authority_provider(times, states, identity), {
            "status": "qualified",
            "qualified": True,
            "failure_reason": None,
            "authority": identity,
        }
    if authority_type != "refined_trapezoidal":
        raise ValueError(f"{case_id}: unsupported runtime authority: {authority_type}")

    fixed_accuracy = runtime_manifest["fixed_accuracy"]
    refinement_factor = int(fixed_accuracy["authority_refinement_factor"])
    coarse_factor = refinement_factor // 2
    duration = times[-1] - times[0]
    _, simulation, _ = load_case(case_path)
    baseline_step = float(simulation["nominal_step"])
    estimated_points = math.ceil(duration / (baseline_step / refinement_factor)) + 1
    estimated_trace_values = estimated_points * (circuit.dynamic_size + 1)
    trace_budget = int(fixed_accuracy["maximum_estimated_authority_trace_values"])
    if estimated_trace_values > trace_budget:
        return None, {
            "status": "authority_unqualified",
            "qualified": False,
            "failure_reason": "authority trace-value budget exceeded",
            "authority": {
                "type": authority_type,
                "requested_refinement_factor": refinement_factor,
                "estimated_trace_values": estimated_trace_values,
                "maximum_estimated_trace_values": trace_budget,
            },
        }

    qualification_times = common_grid(
        float(simulation["start_time"]),
        float(simulation["stop_time"]),
        int(runtime_manifest["common_grid_samples"]),
    )
    fine_qualification_states, fine_qualification_metadata = refined_authority(
        case_path,
        qualification_times,
        refinement_factor=refinement_factor,
        linear_backend=linear_backend,
    )
    coarse_states, coarse_metadata = refined_authority(
        case_path,
        qualification_times,
        refinement_factor=coarse_factor,
        linear_backend=linear_backend,
    )
    tolerances = runtime_manifest["accuracy"]
    convergence = trajectory_error(
        coarse_states,
        fine_qualification_states,
        circuit.dynamic_names,
        absolute_tolerance=float(tolerances["absolute_tolerance"]),
        relative_tolerance=float(tolerances["relative_tolerance"]),
    )
    family_divisors = fixed_accuracy.get("family_step_divisors", {})
    candidate_divisors = family_divisors.get(
        str(family["id"]),
        fixed_accuracy["step_divisors"],
    )
    maximum_candidate_divisor = max(int(value) for value in candidate_divisors)
    convergence_cap = float(
        fixed_accuracy["authority_convergence_scaled_error_cap"]
    )
    qualified = bool(
        refinement_factor >= 4 * maximum_candidate_divisor
        and convergence["maximum_scaled_trajectory_error"] <= convergence_cap
    )
    failure_reason = None
    if refinement_factor < 4 * maximum_candidate_divisor:
        failure_reason = "authority is not four times finer than the finest candidate"
    elif convergence["maximum_scaled_trajectory_error"] > convergence_cap:
        failure_reason = "authority refinement did not satisfy convergence cap"
    sampled_states: tuple[tuple[float, ...], ...] | None = None
    sampled_metadata: dict[str, Any] | None = None
    if qualified:
        sampled_states, sampled_metadata = refined_authority(
            case_path,
            times,
            refinement_factor=refinement_factor,
            linear_backend=linear_backend,
        )
    identity = {
        **fine_qualification_metadata,
        "qualified": qualified,
        "qualification_grid_samples": len(qualification_times),
        "qualification_trace_sha256": fine_qualification_metadata["trace_sha256"],
        "sample_trace_sha256": (
            None if sampled_metadata is None else sampled_metadata["trace_sha256"]
        ),
        "coarse_refinement_factor": coarse_factor,
        "coarse_trace_sha256": coarse_metadata["trace_sha256"],
        "convergence": convergence,
        "convergence_cap": convergence_cap,
        "maximum_candidate_divisor": maximum_candidate_divisor,
        "minimum_refinement_beyond_finest_candidate": (
            refinement_factor / maximum_candidate_divisor
        ),
        "estimated_trace_values": estimated_trace_values,
        "maximum_estimated_trace_values": trace_budget,
    }
    provider = (
        _sampled_authority_provider(times, sampled_states, identity)
        if sampled_states is not None
        else None
    )
    return provider, {
        "status": "qualified" if qualified else "authority_unqualified",
        "qualified": qualified,
        "failure_reason": failure_reason,
        "authority": identity,
    }


def _sampled_authority_provider(
    times: tuple[float, ...],
    states: tuple[tuple[float, ...], ...],
    identity: dict[str, Any],
) -> AuthorityProvider:
    state_by_time = {
        float(time_value): tuple(float(value) for value in state)
        for time_value, state in zip(times, states, strict=True)
    }

    def state_at(time_value: float) -> tuple[float, ...]:
        try:
            return state_by_time[float(time_value)]
        except KeyError as error:
            raise ValueError("runtime authority was not sampled at the requested time") from error

    return AuthorityProvider(
        state_at=state_at,
        authority_type=str(identity["type"]),
        identity=identity,
    )


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
        writer.writerows(
            {
                key: _csv_value(row.get(key))
                for key in fields
            }
            for row in atlas["samples"]
        )


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return value


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
    transfer_counts: Counter[str] = Counter()
    transfer_covered: Counter[str] = Counter()
    for row in atlas["samples"]:
        if not row["coverage_eligible"]:
            continue
        transfer = str(row["authority_transfer_kind"])
        transfer_counts[transfer] += 1
        transfer_covered[transfer] += int(bool(row["covered"]))
    _write_bar_svg(
        root / "coverage-versus-authority-transfer.svg",
        [
            (transfer, transfer_covered[transfer] / transfer_counts[transfer])
            for transfer in sorted(transfer_counts)
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
    global_coverage_rows = [
        (
            f'{aggregate["case_id"]} @ {entry["safety_factor"]:g}x',
            entry["babcs_total_coverage_fraction"],
        )
        for aggregate in atlas["aggregates"]
        for entry in aggregate["global_trajectory_coverage_by_safety_factor"].values()
        if entry["babcs_total_coverage_fraction"] is not None
    ]
    if global_coverage_rows:
        _write_bar_svg(
            root / "global-trajectory-total-coverage.svg",
            global_coverage_rows,
            y_label="BAB-CS total empirical coverage fraction",
            overwrite=overwrite,
        )
    pair_coverage_rows = [
        (
            f'{aggregate["case_id"]} @ {pair_id}',
            pair["coverage_by_safety_factor"]["1"][
                "babcs_total_coverage_fraction"
            ],
        )
        for aggregate in atlas["aggregates"]
        for pair_id, pair in aggregate["global_refinement_pair_sweep"].items()
        if len(aggregate["global_refinement_pair_sweep"]) > 1
        and pair["coverage_by_safety_factor"]["1"][
            "babcs_total_coverage_fraction"
        ]
        is not None
    ]
    pair_inflation_rows = [
        (
            f'{aggregate["case_id"]} @ {pair_id}',
            pair["coverage_by_safety_factor"]["1"][
                "median_uncertainty_to_authority_error_ratio"
            ],
        )
        for aggregate in atlas["aggregates"]
        for pair_id, pair in aggregate["global_refinement_pair_sweep"].items()
        if len(aggregate["global_refinement_pair_sweep"]) > 1
        and pair["coverage_by_safety_factor"]["1"][
            "median_uncertainty_to_authority_error_ratio"
        ]
        is not None
    ]
    if pair_coverage_rows:
        _write_bar_svg(
            root / "global-refinement-pair-total-coverage.svg",
            pair_coverage_rows,
            y_label="raw BAB-CS total empirical coverage fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-refinement-pair-median-inflation.svg",
            pair_inflation_rows,
            y_label="median uncertainty to authority error ratio",
            overwrite=overwrite,
        )
    order_qualification_rows = [
        (
            f'{aggregate["case_id"]} @ {triplet_id}',
            triplet["qualification_fraction"],
        )
        for aggregate in atlas["aggregates"]
        for triplet_id, triplet in aggregate[
            "global_order_aware_triplet_sweep"
        ].items()
        if triplet["qualification_fraction"] is not None
    ]
    order_coverage_rows = [
        (
            f'{aggregate["case_id"]} @ {triplet_id}',
            triplet["effective_babcs_total_coverage_fraction"],
        )
        for aggregate in atlas["aggregates"]
        for triplet_id, triplet in aggregate[
            "global_order_aware_triplet_sweep"
        ].items()
        if triplet["effective_babcs_total_coverage_fraction"] is not None
    ]
    order_inflation_rows = [
        (
            f'{aggregate["case_id"]} @ {triplet_id}',
            triplet["median_uncertainty_to_finest_authority_error_ratio"],
        )
        for aggregate in atlas["aggregates"]
        for triplet_id, triplet in aggregate[
            "global_order_aware_triplet_sweep"
        ].items()
        if triplet["median_uncertainty_to_finest_authority_error_ratio"]
        is not None
    ]
    if order_qualification_rows:
        _write_bar_svg(
            root / "global-order-aware-qualification.svg",
            order_qualification_rows,
            y_label="asymptotic qualification fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-order-aware-effective-coverage.svg",
            order_coverage_rows,
            y_label="fail-closed effective BAB-CS coverage fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-order-aware-median-inflation.svg",
            order_inflation_rows,
            y_label="median estimated error to finest authority error ratio",
            overwrite=overwrite,
        )
        epoch_qualification_rows = [
            (
                f'{aggregate["case_id"]} @ {triplet_id}',
                triplet["epoch_qualified"]["sample_qualification_fraction"],
            )
            for aggregate in atlas["aggregates"]
            for triplet_id, triplet in aggregate[
                "global_order_aware_triplet_sweep"
            ].items()
            if triplet["epoch_qualified"]["sample_qualification_fraction"]
            is not None
        ]
        epoch_coverage_rows = [
            (
                f'{aggregate["case_id"]} @ {triplet_id}',
                triplet["epoch_qualified"][
                    "effective_babcs_total_coverage_fraction"
                ],
            )
            for aggregate in atlas["aggregates"]
            for triplet_id, triplet in aggregate[
                "global_order_aware_triplet_sweep"
            ].items()
            if triplet["epoch_qualified"][
                "effective_babcs_total_coverage_fraction"
            ]
            is not None
        ]
        epoch_inflation_rows = [
            (
                f'{aggregate["case_id"]} @ {triplet_id}',
                triplet["epoch_qualified"][
                    "median_uncertainty_to_finest_authority_error_ratio"
                ],
            )
            for aggregate in atlas["aggregates"]
            for triplet_id, triplet in aggregate[
                "global_order_aware_triplet_sweep"
            ].items()
            if triplet["epoch_qualified"][
                "median_uncertainty_to_finest_authority_error_ratio"
            ]
            is not None
        ]
        _write_bar_svg(
            root / "global-order-aware-epoch-qualification.svg",
            epoch_qualification_rows,
            y_label="epoch-qualified sample fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-order-aware-epoch-effective-coverage.svg",
            epoch_coverage_rows,
            y_label="epoch-qualified effective BAB-CS coverage fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-order-aware-epoch-median-inflation.svg",
            epoch_inflation_rows,
            y_label="epoch-qualified median estimated error ratio",
            overwrite=overwrite,
        )
        envelope_reference_rows = [
            (
                f'{aggregate["case_id"]} @ {triplet_id}',
                triplet["epoch_qualified"]["envelope"][
                    "effective_reference_estimator_coverage_fraction"
                ],
            )
            for aggregate in atlas["aggregates"]
            for triplet_id, triplet in aggregate[
                "global_order_aware_triplet_sweep"
            ].items()
        ]
        envelope_total_rows = [
            (
                f'{aggregate["case_id"]} @ {triplet_id}',
                triplet["epoch_qualified"]["envelope"][
                    "effective_babcs_total_coverage_fraction"
                ],
            )
            for aggregate in atlas["aggregates"]
            for triplet_id, triplet in aggregate[
                "global_order_aware_triplet_sweep"
            ].items()
        ]
        envelope_inflation_rows = [
            (
                f'{aggregate["case_id"]} @ {triplet_id}',
                triplet["epoch_qualified"]["envelope"][
                    "median_uncertainty_to_finest_authority_error_ratio"
                ],
            )
            for aggregate in atlas["aggregates"]
            for triplet_id, triplet in aggregate[
                "global_order_aware_triplet_sweep"
            ].items()
        ]
        _write_bar_svg(
            root / "global-order-aware-epoch-envelope-reference-coverage.svg",
            envelope_reference_rows,
            y_label="epoch-envelope effective reference coverage fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-order-aware-epoch-envelope-total-coverage.svg",
            envelope_total_rows,
            y_label="epoch-envelope effective BAB-CS coverage fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-order-aware-epoch-envelope-median-inflation.svg",
            envelope_inflation_rows,
            y_label="epoch-envelope median estimated error ratio",
            overwrite=overwrite,
        )
    statewise_available = any(
        aggregate["global_statewise_four_level_sweep"]
        for aggregate in atlas["aggregates"]
    )
    if statewise_available:
        statewise_qualification_rows = [
            (
                f'{aggregate["case_id"]} @ {quadruplet_id}',
                quadruplet["sample_qualification_fraction"],
            )
            for aggregate in atlas["aggregates"]
            for quadruplet_id, quadruplet in aggregate[
                "global_statewise_four_level_sweep"
            ].items()
            if quadruplet["sample_qualification_fraction"] is not None
        ]
        statewise_reference_coverage_rows = [
            (
                f'{aggregate["case_id"]} @ {quadruplet_id}',
                quadruplet["effective_reference_estimator_coverage_fraction"],
            )
            for aggregate in atlas["aggregates"]
            for quadruplet_id, quadruplet in aggregate[
                "global_statewise_four_level_sweep"
            ].items()
            if quadruplet["effective_reference_estimator_coverage_fraction"]
            is not None
        ]
        statewise_inflation_rows = [
            (
                f'{aggregate["case_id"]} @ {quadruplet_id}',
                quadruplet[
                    "median_uncertainty_to_finest_authority_error_ratio"
                ],
            )
            for aggregate in atlas["aggregates"]
            for quadruplet_id, quadruplet in aggregate[
                "global_statewise_four_level_sweep"
            ].items()
            if quadruplet[
                "median_uncertainty_to_finest_authority_error_ratio"
            ]
            is not None
        ]
        _write_bar_svg(
            root / "global-statewise-four-level-qualification.svg",
            statewise_qualification_rows,
            y_label="four-level qualified sample fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-statewise-four-level-effective-reference-coverage.svg",
            statewise_reference_coverage_rows,
            y_label="four-level effective reference coverage fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-statewise-four-level-median-inflation.svg",
            statewise_inflation_rows,
            y_label="four-level median estimated error ratio",
            overwrite=overwrite,
        )
    epoch_statewise_available = any(
        aggregate["global_statewise_epoch_sweep"]
        for aggregate in atlas["aggregates"]
    )
    if epoch_statewise_available:
        epoch_qualification_rows = [
            (
                f'{aggregate["case_id"]} @ {quadruplet_id}',
                quadruplet["sample_qualification_fraction"],
            )
            for aggregate in atlas["aggregates"]
            for quadruplet_id, quadruplet in aggregate[
                "global_statewise_epoch_sweep"
            ].items()
            if quadruplet["sample_qualification_fraction"] is not None
        ]
        epoch_reference_rows = [
            (
                f'{aggregate["case_id"]} @ {quadruplet_id}',
                quadruplet["effective_reference_estimator_coverage_fraction"],
            )
            for aggregate in atlas["aggregates"]
            for quadruplet_id, quadruplet in aggregate[
                "global_statewise_epoch_sweep"
            ].items()
            if quadruplet["effective_reference_estimator_coverage_fraction"]
            is not None
        ]
        epoch_inflation_rows = [
            (
                f'{aggregate["case_id"]} @ {quadruplet_id}',
                quadruplet[
                    "median_uncertainty_to_finest_authority_error_ratio"
                ],
            )
            for aggregate in atlas["aggregates"]
            for quadruplet_id, quadruplet in aggregate[
                "global_statewise_epoch_sweep"
            ].items()
            if quadruplet[
                "median_uncertainty_to_finest_authority_error_ratio"
            ]
            is not None
        ]
        epoch_zero_crossing_rows = [
            (
                f'{aggregate["case_id"]} @ {quadruplet_id}',
                quadruplet["coherent_zero_crossing_intervals"],
            )
            for aggregate in atlas["aggregates"]
            for quadruplet_id, quadruplet in aggregate[
                "global_statewise_epoch_sweep"
            ].items()
        ]
        _write_bar_svg(
            root / "global-statewise-epoch-qualification.svg",
            epoch_qualification_rows,
            y_label="epoch-fit qualified sample fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-statewise-epoch-effective-reference-coverage.svg",
            epoch_reference_rows,
            y_label="epoch-fit effective reference coverage fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-statewise-epoch-median-inflation.svg",
            epoch_inflation_rows,
            y_label="epoch-fit median estimated error ratio",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-statewise-epoch-zero-crossings.svg",
            epoch_zero_crossing_rows,
            y_label="coherent zero-crossing intervals",
            overwrite=overwrite,
        )
    two_term_modal_available = any(
        aggregate["global_two_term_modal_sweep"]
        for aggregate in atlas["aggregates"]
    )
    if two_term_modal_available:
        two_term_rows = [
            (
                f'{aggregate["case_id"]} @ {policy_id}',
                policy,
            )
            for aggregate in atlas["aggregates"]
            for policy_id, policy in aggregate[
                "global_two_term_modal_sweep"
            ].items()
        ]
        _write_bar_svg(
            root / "global-two-term-modal-epoch-qualification.svg",
            [
                (label, row["sample_qualification_fraction"])
                for label, row in two_term_rows
                if row["sample_qualification_fraction"] is not None
            ],
            y_label="two-term modal qualified sample fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-two-term-modal-group-qualification.svg",
            [
                (label, row["mode_group_epoch_qualification_fraction"])
                for label, row in two_term_rows
                if row["mode_group_epoch_qualification_fraction"] is not None
            ],
            y_label="two-term qualified modal group fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-two-term-modal-effective-reference-coverage.svg",
            [
                (
                    label,
                    row["effective_reference_estimator_coverage_fraction"],
                )
                for label, row in two_term_rows
                if row["effective_reference_estimator_coverage_fraction"]
                is not None
            ],
            y_label="two-term modal effective reference coverage",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-two-term-modal-median-inflation.svg",
            [
                (
                    label,
                    row["median_uncertainty_to_finest_authority_error_ratio"],
                )
                for label, row in two_term_rows
                if row["median_uncertainty_to_finest_authority_error_ratio"]
                is not None
            ],
            y_label="two-term modal median estimated error ratio",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-two-term-modal-holdout-residual.svg",
            [
                (label, row["maximum_holdout_residual_ratio"])
                for label, row in two_term_rows
                if row["maximum_holdout_residual_ratio"] is not None
            ],
            y_label="maximum holdout residual ratio",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-two-term-modal-secondary-contribution.svg",
            [
                (
                    label,
                    row[
                        "median_secondary_to_primary_contribution_ratio"
                    ],
                )
                for label, row in two_term_rows
                if row["median_secondary_to_primary_contribution_ratio"]
                is not None
            ],
            y_label="median secondary to primary contribution ratio",
            overwrite=overwrite,
        )
    modal_epoch_available = any(
        aggregate["global_modal_epoch_sweep"]
        for aggregate in atlas["aggregates"]
    )
    if modal_epoch_available:
        modal_qualification_rows = [
            (
                f'{aggregate["case_id"]} @ {quadruplet_id}',
                quadruplet["sample_qualification_fraction"],
            )
            for aggregate in atlas["aggregates"]
            for quadruplet_id, quadruplet in aggregate[
                "global_modal_epoch_sweep"
            ].items()
            if quadruplet["sample_qualification_fraction"] is not None
        ]
        modal_group_rows = [
            (
                f'{aggregate["case_id"]} @ {quadruplet_id}',
                quadruplet["mode_group_epoch_qualification_fraction"],
            )
            for aggregate in atlas["aggregates"]
            for quadruplet_id, quadruplet in aggregate[
                "global_modal_epoch_sweep"
            ].items()
            if quadruplet["mode_group_epoch_qualification_fraction"] is not None
        ]
        modal_reference_rows = [
            (
                f'{aggregate["case_id"]} @ {quadruplet_id}',
                quadruplet["effective_reference_estimator_coverage_fraction"],
            )
            for aggregate in atlas["aggregates"]
            for quadruplet_id, quadruplet in aggregate[
                "global_modal_epoch_sweep"
            ].items()
            if quadruplet["effective_reference_estimator_coverage_fraction"]
            is not None
        ]
        modal_inflation_rows = [
            (
                f'{aggregate["case_id"]} @ {quadruplet_id}',
                quadruplet[
                    "median_uncertainty_to_finest_authority_error_ratio"
                ],
            )
            for aggregate in atlas["aggregates"]
            for quadruplet_id, quadruplet in aggregate[
                "global_modal_epoch_sweep"
            ].items()
            if quadruplet[
                "median_uncertainty_to_finest_authority_error_ratio"
            ]
            is not None
        ]
        _write_bar_svg(
            root / "global-modal-epoch-qualification.svg",
            modal_qualification_rows,
            y_label="modal epoch qualified sample fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-modal-group-qualification.svg",
            modal_group_rows,
            y_label="qualified modal group epoch fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-modal-epoch-effective-reference-coverage.svg",
            modal_reference_rows,
            y_label="modal effective reference coverage fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-modal-epoch-median-inflation.svg",
            modal_inflation_rows,
            y_label="modal median estimated error ratio",
            overwrite=overwrite,
        )
    temporally_aligned_modal_available = any(
        aggregate["global_temporally_aligned_modal_epoch_sweep"]
        for aggregate in atlas["aggregates"]
    )
    if temporally_aligned_modal_available:
        temporal_rows = [
            (
                f'{aggregate["case_id"]} @ {quadruplet_id}',
                quadruplet,
            )
            for aggregate in atlas["aggregates"]
            for quadruplet_id, quadruplet in aggregate[
                "global_temporally_aligned_modal_epoch_sweep"
            ].items()
        ]
        _write_bar_svg(
            root / "global-temporal-modal-epoch-qualification.svg",
            [
                (label, row["sample_qualification_fraction"])
                for label, row in temporal_rows
                if row["sample_qualification_fraction"] is not None
            ],
            y_label="temporal modal qualified sample fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-temporal-modal-group-qualification.svg",
            [
                (label, row["mode_group_epoch_qualification_fraction"])
                for label, row in temporal_rows
                if row["mode_group_epoch_qualification_fraction"] is not None
            ],
            y_label="temporal qualified modal group fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-temporal-modal-effective-reference-coverage.svg",
            [
                (
                    label,
                    row["effective_reference_estimator_coverage_fraction"],
                )
                for label, row in temporal_rows
                if row["effective_reference_estimator_coverage_fraction"]
                is not None
            ],
            y_label="temporal modal effective reference coverage",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-temporal-modal-median-inflation.svg",
            [
                (
                    label,
                    row["median_uncertainty_to_finest_authority_error_ratio"],
                )
                for label, row in temporal_rows
                if row["median_uncertainty_to_finest_authority_error_ratio"]
                is not None
            ],
            y_label="temporal modal median estimated error ratio",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-temporal-modal-alignment-use.svg",
            [
                (
                    label,
                    row["temporally_aligned_mode_group_epochs"]
                    / row["mode_group_epoch_count"],
                )
                for label, row in temporal_rows
                if row["mode_group_epoch_count"]
            ],
            y_label="temporally aligned modal group fraction",
            overwrite=overwrite,
        )
        _write_bar_svg(
            root / "global-temporal-modal-discarded-endpoints.svg",
            [
                (label, row["discarded_endpoint_count"])
                for label, row in temporal_rows
            ],
            y_label="discarded direction-comparison endpoints",
            overwrite=overwrite,
        )


def _row_samples(
    record: dict[str, Any],
    case: dict[str, Any],
    circuit,
    config: BABCSConfig,
    result,
    provider: AuthorityProvider,
    global_dual_trajectory: GlobalDualTrajectorySweep | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    authority_states = [provider.state_at(point.time) for point in result.points]
    authority_hash = _authority_sample_hash(result.points, authority_states)
    epoch_candidate = result.points[0].state.evaluation.dynamic_state
    epoch_authority = authority_states[0]
    epoch_time = result.points[0].time
    epoch_generation = 0
    age_steps = 0
    previous_recursive_bound = 0.0
    epoch_global_states = (
        {}
        if global_dual_trajectory is None
        else {
            trajectory.pair_id: (
                trajectory.coarse_states[0],
                trajectory.fine_states[0],
            )
            for trajectory in global_dual_trajectory.trajectories
        }
    )
    epoch_global_factor_states = (
        {}
        if global_dual_trajectory is None
        else {
            factor: states[0]
            for factor, states in global_dual_trajectory.factor_states.items()
        }
    )
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
        total_uncertainty_covered = (
            epoch_error <= metrics.total_estimated_uncertainty
            if coverage_eligible
            else None
        )
        total_uncertainty_error_ratio = (
            epoch_error / metrics.total_estimated_uncertainty
            if coverage_eligible and metrics.total_estimated_uncertainty > 0.0
            else None
        )
        global_reference_absolute_discrepancy = None
        global_reference_epoch_discrepancy = None
        global_refined_absolute_authority_error = None
        global_refined_epoch_authority_error = None
        global_reference_estimator_covered = None
        global_total_uncertainty = None
        global_total_uncertainty_covered = None
        global_refinement_pair_diagnostics: dict[str, dict[str, Any]] = {}
        global_order_aware_diagnostics: dict[str, dict[str, Any]] = {}
        global_statewise_four_level_diagnostics: dict[str, dict[str, Any]] = {}
        if global_dual_trajectory is not None:
            for trajectory in global_dual_trajectory.trajectories:
                epoch_global_coarse, epoch_global_fine = epoch_global_states[
                    trajectory.pair_id
                ]
                global_coarse_state = trajectory.coarse_states[sample_index]
                global_fine_state = trajectory.fine_states[sample_index]
                global_coarse_delta = tuple(
                    value - anchor
                    for value, anchor in zip(
                        global_coarse_state,
                        epoch_global_coarse,
                        strict=True,
                    )
                )
                global_fine_delta = tuple(
                    value - anchor
                    for value, anchor in zip(
                        global_fine_state,
                        epoch_global_fine,
                        strict=True,
                    )
                )
                absolute_discrepancy = _scaled_error(
                    global_coarse_state,
                    global_fine_state,
                    config,
                )
                epoch_discrepancy = _scaled_error(
                    global_coarse_delta,
                    global_fine_delta,
                    config,
                )
                refined_absolute_authority_error = _scaled_error(
                    global_fine_state,
                    authority_state,
                    config,
                )
                refined_epoch_authority_error = _scaled_error(
                    global_fine_delta,
                    authority_delta,
                    config,
                )
                pair_diagnostic = {
                    "pair_id": trajectory.pair_id,
                    "coarse_refinement_factor": trajectory.coarse_refinement_factor,
                    "fine_refinement_factor": trajectory.fine_refinement_factor,
                    "absolute_discrepancy": absolute_discrepancy,
                    "epoch_discrepancy": epoch_discrepancy,
                    "refined_absolute_authority_error": (
                        refined_absolute_authority_error
                    ),
                    "refined_epoch_authority_error": refined_epoch_authority_error,
                    "reference_estimator_covered": (
                        refined_epoch_authority_error <= epoch_discrepancy
                        if coverage_eligible
                        else None
                    ),
                    "total_uncertainty": (
                        metrics.estimated_bound + epoch_discrepancy
                        if coverage_eligible
                        else None
                    ),
                    "total_uncertainty_covered": (
                        epoch_error <= metrics.estimated_bound + epoch_discrepancy
                        if coverage_eligible
                        else None
                    ),
                }
                global_refinement_pair_diagnostics[trajectory.pair_id] = pair_diagnostic
            order_settings = global_dual_trajectory.metadata.get("order_aware")
            if isinstance(order_settings, dict):
                for triplet in order_settings["triplets"]:
                    coarse_diagnostic = global_refinement_pair_diagnostics[
                        triplet["coarse_pair_id"]
                    ]
                    fine_diagnostic = global_refinement_pair_diagnostics[
                        triplet["fine_pair_id"]
                    ]
                    global_order_aware_diagnostics[triplet["triplet_id"]] = (
                        _order_aware_sample_diagnostic(
                            triplet,
                            order_settings,
                            coarse_diagnostic,
                            fine_diagnostic,
                            recursive_internal_bound=metrics.estimated_bound,
                            authority_epoch_drift_error=epoch_error,
                            coverage_eligible=coverage_eligible,
                        )
                    )
            statewise_settings = global_dual_trajectory.metadata.get(
                "statewise_four_level"
            )
            if isinstance(statewise_settings, dict):
                for quadruplet in statewise_settings["quadruplets"]:
                    factors = tuple(
                        int(factor) for factor in quadruplet["refinement_factors"]
                    )
                    factor_deltas = tuple(
                        tuple(
                            value - anchor
                            for value, anchor in zip(
                                global_dual_trajectory.factor_states[factor][
                                    sample_index
                                ],
                                epoch_global_factor_states[factor],
                                strict=True,
                            )
                        )
                        for factor in factors
                    )
                    global_statewise_four_level_diagnostics[
                        quadruplet["quadruplet_id"]
                    ] = _statewise_four_level_sample_diagnostic(
                        quadruplet,
                        statewise_settings,
                        factor_deltas,
                        state_names=tuple(circuit.dynamic_names),
                        candidate_delta=candidate_delta,
                        authority_delta=authority_delta,
                        recursive_internal_bound=metrics.estimated_bound,
                        authority_epoch_drift_error=epoch_error,
                        config=config,
                        coverage_eligible=coverage_eligible,
                        sampling_context=_statewise_sampling_context(
                            point.time,
                            quadruplet,
                            global_dual_trajectory.metadata,
                            anchor_age_steps=age_steps + 1,
                            algebraic_residual=metrics.algebraic_residual,
                            full_residual=metrics.full_residual,
                            scaled_difference_floor=float(
                                statewise_settings["scaled_difference_floor"]
                            ),
                        ),
                    )
            primary_diagnostic = global_refinement_pair_diagnostics[
                global_dual_trajectory.primary.pair_id
            ]
            global_reference_absolute_discrepancy = primary_diagnostic[
                "absolute_discrepancy"
            ]
            global_reference_epoch_discrepancy = primary_diagnostic[
                "epoch_discrepancy"
            ]
            global_refined_absolute_authority_error = primary_diagnostic[
                "refined_absolute_authority_error"
            ]
            global_refined_epoch_authority_error = primary_diagnostic[
                "refined_epoch_authority_error"
            ]
            global_reference_estimator_covered = primary_diagnostic[
                "reference_estimator_covered"
            ]
            global_total_uncertainty = primary_diagnostic["total_uncertainty"]
            global_total_uncertainty_covered = primary_diagnostic[
                "total_uncertainty_covered"
            ]
        propagated_prior_bound = metrics.closed_loop_gain * previous_recursive_bound
        pre_reset_local_defect = max(
            0.0,
            metrics.pre_reset_estimated_bound - propagated_prior_bound,
        )
        uncovered_authority_gap = (
            max(0.0, epoch_error - metrics.estimated_bound)
            if coverage_eligible
            else None
        )
        if metrics.periodic_reanchor:
            authority_transfer_kind = "periodic_reanchor"
        elif metrics.correction_gain >= 1.0:
            authority_transfer_kind = "full_reference"
        elif metrics.reference_solve_count:
            authority_transfer_kind = "partial_reference"
        else:
            authority_transfer_kind = "embedded_fast"
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
            "total_uncertainty_covered": total_uncertainty_covered,
            "total_uncertainty_error_ratio": total_uncertainty_error_ratio,
            "error_to_bound_ratio": error_to_bound,
            "bound_to_error_coverage_ratio": bound_to_error,
            "uncovered_authority_gap": uncovered_authority_gap,
            "zero_epoch_error": coverage_eligible and epoch_error == 0.0,
            "propagated_prior_bound": propagated_prior_bound,
            "pre_reset_local_defect": pre_reset_local_defect,
            "reported_local_defect": metrics.local_defect,
            "embedded_defect": metrics.embedded_defect,
            "corrected_reference_defect": metrics.corrected_reference_error,
            "residual_defect": metrics.residual_ratio,
            "predictor_amplification": metrics.predictor_amplification,
            "closed_loop_gain": metrics.closed_loop_gain,
            "correction_gain": metrics.correction_gain,
            "reference_solve_count": metrics.reference_solve_count,
            "reference_refinement_solve_count": (
                metrics.reference_refinement_solve_count
            ),
            "reference_discretization_defect": (
                metrics.reference_discretization_defect
            ),
            "reference_uncertainty": metrics.reference_uncertainty,
            "pre_reset_reference_uncertainty": (
                metrics.pre_reset_reference_uncertainty
            ),
            "total_estimated_uncertainty": metrics.total_estimated_uncertainty,
            "global_dual_trajectory_available": global_dual_trajectory is not None,
            "global_reference_absolute_discrepancy": (
                global_reference_absolute_discrepancy
            ),
            "global_reference_epoch_discrepancy": global_reference_epoch_discrepancy,
            "global_refined_absolute_authority_error": (
                global_refined_absolute_authority_error
            ),
            "global_refined_epoch_authority_error": (
                global_refined_epoch_authority_error
            ),
            "global_reference_estimator_covered": global_reference_estimator_covered,
            "global_total_uncertainty": global_total_uncertainty,
            "global_total_uncertainty_covered": global_total_uncertainty_covered,
            "global_refinement_pair_diagnostics": global_refinement_pair_diagnostics,
            "global_order_aware_diagnostics": global_order_aware_diagnostics,
            "global_statewise_four_level_diagnostics": (
                global_statewise_four_level_diagnostics
            ),
            "authority_transfer_kind": authority_transfer_kind,
            "full_reference_authority_transfer": authority_transfer_kind
            in {"full_reference", "periodic_reanchor"},
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
            if global_dual_trajectory is not None:
                epoch_global_states = {
                    trajectory.pair_id: (
                        trajectory.coarse_states[sample_index],
                        trajectory.fine_states[sample_index],
                    )
                    for trajectory in global_dual_trajectory.trajectories
                }
                epoch_global_factor_states = {
                    factor: states[sample_index]
                    for factor, states in global_dual_trajectory.factor_states.items()
                }
            epoch_time = point.time
            age_steps = 0
        previous_recursive_bound = metrics.estimated_bound

    return row_samples, row_anchors, row_causes


def _global_refinement_pair_sweep(
    record: dict[str, Any],
    eligible_samples: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    metadata = record.get("global_dual_trajectory")
    if not isinstance(metadata, dict):
        return {}, []
    pair_metadata = metadata.get("pairs")
    if not isinstance(pair_metadata, list):
        return {}, []
    safety_factors = tuple(float(value) for value in metadata["safety_factors"])
    pair_results: dict[str, dict[str, Any]] = {}
    candidates: list[dict[str, Any]] = []
    for pair in pair_metadata:
        pair_id = str(pair["pair_id"])
        paired_samples = [
            (sample, sample["global_refinement_pair_diagnostics"].get(pair_id))
            for sample in eligible_samples
        ]
        paired_samples = [
            (sample, diagnostic)
            for sample, diagnostic in paired_samples
            if isinstance(diagnostic, dict)
        ]
        discrepancies = [
            float(diagnostic["epoch_discrepancy"])
            for _, diagnostic in paired_samples
        ]
        inflation_ratios = [
            diagnostic["epoch_discrepancy"] / sample["authority_epoch_drift_error"]
            for sample, diagnostic in paired_samples
            if sample["authority_epoch_drift_error"] > 0.0
        ]
        curve: dict[str, dict[str, Any]] = {}
        for safety_factor in safety_factors:
            reference_covered = sum(
                diagnostic["refined_epoch_authority_error"]
                <= safety_factor * diagnostic["epoch_discrepancy"]
                for _, diagnostic in paired_samples
            )
            total_covered = sum(
                sample["authority_epoch_drift_error"]
                <= sample["recursive_internal_bound"]
                + safety_factor * diagnostic["epoch_discrepancy"]
                for sample, diagnostic in paired_samples
            )
            curve_row = {
                "safety_factor": safety_factor,
                "eligible": len(paired_samples),
                "reference_estimator_covered": reference_covered,
                "reference_estimator_coverage_fraction": (
                    reference_covered / len(paired_samples) if paired_samples else None
                ),
                "babcs_total_covered": total_covered,
                "babcs_total_coverage_fraction": (
                    total_covered / len(paired_samples) if paired_samples else None
                ),
                "maximum_added_uncertainty": max(
                    (
                        safety_factor * diagnostic["epoch_discrepancy"]
                        for _, diagnostic in paired_samples
                    ),
                    default=0.0,
                ),
                "median_added_uncertainty": (
                    safety_factor * _percentile(discrepancies, 0.5)
                    if discrepancies
                    else None
                ),
                "p95_added_uncertainty": (
                    safety_factor * _percentile(discrepancies, 0.95)
                    if discrepancies
                    else None
                ),
                "median_uncertainty_to_authority_error_ratio": (
                    safety_factor * _percentile(inflation_ratios, 0.5)
                    if inflation_ratios
                    else None
                ),
                "p95_uncertainty_to_authority_error_ratio": (
                    safety_factor * _percentile(inflation_ratios, 0.95)
                    if inflation_ratios
                    else None
                ),
                "independent_pair_work_units": pair["independent_pair_work_units"],
            }
            curve[format(safety_factor, ".17g")] = curve_row
            if (
                curve_row["babcs_total_coverage_fraction"] is not None
                and curve_row["median_uncertainty_to_authority_error_ratio"] is not None
            ):
                candidates.append(
                    {
                        "pair_id": pair_id,
                        "coarse_refinement_factor": pair["coarse_refinement_factor"],
                        "fine_refinement_factor": pair["fine_refinement_factor"],
                        **curve_row,
                    }
                )
        pair_results[pair_id] = {
            **pair,
            "eligible": len(paired_samples),
            "maximum_epoch_discrepancy": max(discrepancies, default=0.0),
            "median_epoch_discrepancy": _percentile(discrepancies, 0.5),
            "p95_epoch_discrepancy": _percentile(discrepancies, 0.95),
            "coverage_by_safety_factor": curve,
        }

    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_global_pair(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["independent_pair_work_units"],
            row["median_uncertainty_to_authority_error_ratio"],
            -row["babcs_total_coverage_fraction"],
            row["pair_id"],
            row["safety_factor"],
        )
    )
    return pair_results, frontier


def _order_aware_sample_diagnostic(
    triplet: dict[str, Any],
    settings: dict[str, Any],
    coarse_diagnostic: dict[str, Any],
    fine_diagnostic: dict[str, Any],
    *,
    recursive_internal_bound: float,
    authority_epoch_drift_error: float,
    coverage_eligible: bool,
) -> dict[str, Any]:
    coarse_discrepancy = float(coarse_diagnostic["epoch_discrepancy"])
    fine_discrepancy = float(fine_diagnostic["epoch_discrepancy"])
    ratio = float(triplet["refinement_ratio"])
    observed_order, estimated_fine_error, rejection_cause = (
        _order_aware_estimate(
            coarse_discrepancy,
            fine_discrepancy,
            ratio=ratio,
            settings=settings,
        )
    )
    qualified = rejection_cause is None
    finest_authority_error = float(
        fine_diagnostic["refined_epoch_authority_error"]
    )
    total_uncertainty = (
        recursive_internal_bound + estimated_fine_error
        if coverage_eligible and estimated_fine_error is not None
        else None
    )
    return {
        **triplet,
        "coarse_epoch_discrepancy": coarse_discrepancy,
        "fine_epoch_discrepancy": fine_discrepancy,
        "observed_order": observed_order,
        "order_error": (
            abs(observed_order - float(settings["expected_order"]))
            if observed_order is not None
            else None
        ),
        "qualified": qualified,
        "rejection_cause": rejection_cause,
        "estimated_fine_error": estimated_fine_error,
        "finest_refined_epoch_authority_error": finest_authority_error,
        "reference_estimator_covered": (
            finest_authority_error <= estimated_fine_error
            if coverage_eligible and estimated_fine_error is not None
            else None
        ),
        "total_uncertainty": total_uncertainty,
        "total_uncertainty_covered": (
            authority_epoch_drift_error <= total_uncertainty
            if total_uncertainty is not None
            else None
        ),
    }


def _order_aware_estimate(
    coarse_discrepancy: float,
    fine_discrepancy: float,
    *,
    ratio: float,
    settings: dict[str, Any],
) -> tuple[float | None, float | None, str | None]:
    discrepancy_floor = float(settings["discrepancy_floor"])
    if coarse_discrepancy <= discrepancy_floor:
        return None, None, "coarse_discrepancy_at_or_below_floor"
    if fine_discrepancy <= discrepancy_floor:
        return None, None, "fine_discrepancy_at_or_below_floor"
    if fine_discrepancy >= coarse_discrepancy:
        return None, None, "nondecreasing_refinement_discrepancy"
    observed_order = math.log(coarse_discrepancy / fine_discrepancy, ratio)
    if observed_order < float(settings["minimum_observed_order"]):
        return observed_order, None, "observed_order_below_minimum"
    if observed_order > float(settings["maximum_observed_order"]):
        return observed_order, None, "observed_order_above_maximum"
    denominator = ratio**observed_order - 1.0
    if denominator <= sys.float_info.epsilon:
        return observed_order, None, "richardson_denominator_at_or_below_floor"
    return observed_order, fine_discrepancy / denominator, None


def _statewise_four_level_sample_diagnostic(
    quadruplet: dict[str, Any],
    settings: dict[str, Any],
    factor_deltas: tuple[tuple[float, ...], ...],
    *,
    state_names: tuple[str, ...],
    candidate_delta: tuple[float, ...],
    authority_delta: tuple[float, ...],
    recursive_internal_bound: float,
    authority_epoch_drift_error: float,
    config: BABCSConfig,
    coverage_eligible: bool,
    sampling_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if len(factor_deltas) != 4:
        raise ValueError("statewise four-level diagnostics require four trajectories")
    state_count = len(state_names)
    if any(len(values) != state_count for values in factor_deltas):
        raise ValueError("statewise four-level trajectories have inconsistent state counts")
    if len(candidate_delta) != state_count or len(authority_delta) != state_count:
        raise ValueError("statewise four-level comparison states do not align")

    state_diagnostics = [
        _statewise_four_level_state_diagnostic(
            quadruplet,
            settings,
            tuple(values[state_index] for values in factor_deltas),
            state_index=state_index,
            state_name=state_name,
            authority_delta=authority_delta[state_index],
            config=config,
        )
        for state_index, state_name in enumerate(state_names)
    ]
    for state_index, diagnostic in enumerate(state_diagnostics):
        coverage_scale = config.absolute_tolerance + config.relative_tolerance * max(
            abs(candidate_delta[state_index]),
            abs(authority_delta[state_index]),
        )
        diagnostic["coverage_scale"] = coverage_scale
        diagnostic["actual_finest_scaled_authority_error"] = (
            diagnostic["actual_finest_absolute_authority_error"] / coverage_scale
        )
    qualified_states = [
        diagnostic for diagnostic in state_diagnostics if diagnostic["qualified"]
    ]
    state_rejection_causes = Counter(
        str(diagnostic["rejection_cause"])
        for diagnostic in state_diagnostics
        if diagnostic["rejection_cause"] is not None
    )
    floor_states = [
        diagnostic
        for diagnostic in state_diagnostics
        if str(diagnostic["rejection_cause"] or "").endswith(
            "_at_or_below_floor"
        )
    ]
    floor_contexts: list[str] = []
    if floor_states:
        context = sampling_context or {}
        if context.get("interpolated_refinement_factors"):
            floor_contexts.append("interpolation")
        if context.get("anchor_reset_context"):
            floor_contexts.append("anchor_reset")
        if context.get("algebraic_solve_floor_context"):
            floor_contexts.append("algebraic_solve")
        if not floor_contexts:
            floor_contexts.append("unclassified_numerical_floor")
        for diagnostic in floor_states:
            diagnostic["floor_contexts"] = list(floor_contexts)
    statewise_qualified = len(qualified_states) == state_count
    qualified = coverage_eligible and statewise_qualified
    estimated_components = (
        tuple(
            float(diagnostic["estimated_finest_absolute_error"])
            for diagnostic in state_diagnostics
        )
        if statewise_qualified
        else None
    )
    estimated_scaled_finest_error = (
        weighted_rms(
            estimated_components,
            candidate_delta,
            authority_delta,
            config.absolute_tolerance,
            config.relative_tolerance,
        )
        if estimated_components is not None
        else None
    )
    finest_delta = factor_deltas[-1]
    finest_refined_epoch_authority_error = _scaled_error(
        finest_delta,
        authority_delta,
        config,
    )
    total_uncertainty = (
        recursive_internal_bound + estimated_scaled_finest_error
        if coverage_eligible and estimated_scaled_finest_error is not None
        else None
    )
    if not coverage_eligible:
        rejection_cause = "coverage_ineligible"
    elif not statewise_qualified:
        rejection_cause = "state_qualification_failed"
    else:
        rejection_cause = None
    return {
        **quadruplet,
        "coverage_eligible": coverage_eligible,
        "qualified": qualified,
        "rejection_cause": rejection_cause,
        "state_count": state_count,
        "qualified_state_count": len(qualified_states),
        "rejected_state_count": state_count - len(qualified_states),
        "state_qualification_fraction": (
            len(qualified_states) / state_count if state_count else None
        ),
        "state_rejection_causes": dict(sorted(state_rejection_causes.items())),
        "floor_rejected_state_count": len(floor_states),
        "floor_contexts": floor_contexts,
        "sampling_context": sampling_context,
        "states": state_diagnostics,
        "estimated_scaled_finest_error": estimated_scaled_finest_error,
        "finest_refined_epoch_authority_error": (
            finest_refined_epoch_authority_error
        ),
        "reference_estimator_covered": (
            finest_refined_epoch_authority_error <= estimated_scaled_finest_error
            if qualified and estimated_scaled_finest_error is not None
            else None
        ),
        "total_uncertainty": total_uncertainty,
        "total_uncertainty_covered": (
            authority_epoch_drift_error <= total_uncertainty
            if qualified and total_uncertainty is not None
            else None
        ),
        "uncertainty_to_finest_authority_error_ratio": (
            estimated_scaled_finest_error
            / finest_refined_epoch_authority_error
            if qualified
            and estimated_scaled_finest_error is not None
            and finest_refined_epoch_authority_error > 0.0
            else None
        ),
    }


def _statewise_four_level_state_diagnostic(
    quadruplet: dict[str, Any],
    settings: dict[str, Any],
    values: tuple[float, float, float, float],
    *,
    state_index: int,
    state_name: str,
    authority_delta: float,
    config: BABCSConfig,
) -> dict[str, Any]:
    factors = tuple(int(value) for value in quadruplet["refinement_factors"])
    ratio = float(quadruplet["refinement_ratio"])
    state_scale = config.absolute_tolerance + config.relative_tolerance * max(
        (abs(value) for value in values),
        default=0.0,
    )
    physical_difference_floor = (
        float(settings["scaled_difference_floor"]) * state_scale
    )
    differences = (
        values[0] - values[1],
        values[1] - values[2],
        values[2] - values[3],
    )
    normalized_differences = tuple(
        difference / state_scale for difference in differences
    )
    diagnostic: dict[str, Any] = {
        "state_index": state_index,
        "state_name": state_name,
        "refinement_factors": list(factors),
        "refinement_values": list(values),
        "state_scale": state_scale,
        "physical_difference_floor": physical_difference_floor,
        "signed_differences": list(differences),
        "normalized_signed_differences": list(normalized_differences),
        "left_observed_order": None,
        "right_observed_order": None,
        "common_observed_order": None,
        "adjacent_order_difference": None,
        "leading_coefficient_estimates": None,
        "coefficient_relative_difference": None,
        "level_two_error_estimate": None,
        "level_three_error_estimate": None,
        "level_two_extrapolant": None,
        "level_three_extrapolant": None,
        "extrapolant_residual": None,
        "extrapolant_residual_ratio": None,
        "estimated_finest_absolute_error": None,
        "actual_finest_absolute_authority_error": abs(values[3] - authority_delta),
        "component_reference_covered": None,
        "floor_contexts": [],
        "qualified": False,
        "rejection_cause": None,
    }

    def reject(cause: str) -> dict[str, Any]:
        diagnostic["rejection_cause"] = cause
        return diagnostic

    if any(not math.isfinite(value) for value in values + differences):
        return reject("nonfinite_state_or_difference")
    for difference_index, cause in enumerate(
        (
            "first_difference_at_or_below_floor",
            "second_difference_at_or_below_floor",
            "third_difference_at_or_below_floor",
        )
    ):
        if abs(differences[difference_index]) <= physical_difference_floor:
            return reject(cause)
    signs = tuple(math.copysign(1.0, difference) for difference in differences)
    if signs[0] != signs[1] or signs[1] != signs[2]:
        return reject("signed_difference_inconsistent")

    left_order = math.log(abs(differences[0] / differences[1]), ratio)
    right_order = math.log(abs(differences[1] / differences[2]), ratio)
    diagnostic["left_observed_order"] = left_order
    diagnostic["right_observed_order"] = right_order
    if not math.isfinite(left_order) or not math.isfinite(right_order):
        return reject("nonfinite_observed_order")
    minimum_order = float(settings["minimum_observed_order"])
    maximum_order = float(settings["maximum_observed_order"])
    if left_order < minimum_order:
        return reject("left_observed_order_below_minimum")
    if left_order > maximum_order:
        return reject("left_observed_order_above_maximum")
    if right_order < minimum_order:
        return reject("right_observed_order_below_minimum")
    if right_order > maximum_order:
        return reject("right_observed_order_above_maximum")
    order_difference = abs(left_order - right_order)
    common_order = 0.5 * (left_order + right_order)
    diagnostic["common_observed_order"] = common_order
    diagnostic["adjacent_order_difference"] = order_difference
    if order_difference > float(settings["maximum_adjacent_order_difference"]):
        return reject("adjacent_order_difference_exceeded")

    coefficient_denominator = 1.0 - ratio ** (-common_order)
    richardson_denominator = ratio**common_order - 1.0
    if (
        coefficient_denominator <= sys.float_info.epsilon
        or richardson_denominator <= sys.float_info.epsilon
    ):
        return reject("richardson_denominator_at_or_below_floor")
    coefficients = tuple(
        difference * factor**common_order / coefficient_denominator
        for difference, factor in zip(differences, factors[:3], strict=True)
    )
    coefficient_scale = max(
        max(abs(coefficient) for coefficient in coefficients),
        physical_difference_floor,
    )
    coefficient_difference = (
        max(coefficients) - min(coefficients)
    ) / coefficient_scale
    diagnostic["leading_coefficient_estimates"] = list(coefficients)
    diagnostic["coefficient_relative_difference"] = coefficient_difference
    if coefficient_difference > float(
        settings["maximum_coefficient_relative_difference"]
    ):
        return reject("coefficient_relative_difference_exceeded")

    level_two_error = differences[1] / richardson_denominator
    level_three_error = differences[2] / richardson_denominator
    level_two_extrapolant = values[2] - level_two_error
    level_three_extrapolant = values[3] - level_three_error
    residual = abs(level_two_extrapolant - level_three_extrapolant)
    residual_ratio = residual / max(
        abs(level_three_error),
        physical_difference_floor,
    )
    diagnostic.update(
        {
            "level_two_error_estimate": level_two_error,
            "level_three_error_estimate": level_three_error,
            "level_two_extrapolant": level_two_extrapolant,
            "level_three_extrapolant": level_three_extrapolant,
            "extrapolant_residual": residual,
            "extrapolant_residual_ratio": residual_ratio,
        }
    )
    if residual_ratio > float(settings["maximum_extrapolant_residual_ratio"]):
        return reject("extrapolant_residual_ratio_exceeded")

    estimated_error = abs(level_three_error) + residual
    actual_error = float(diagnostic["actual_finest_absolute_authority_error"])
    diagnostic.update(
        {
            "estimated_finest_absolute_error": estimated_error,
            "component_reference_covered": actual_error <= estimated_error,
            "qualified": True,
        }
    )
    return diagnostic


def _statewise_sampling_context(
    sample_time: float,
    quadruplet: dict[str, Any],
    metadata: dict[str, Any],
    *,
    anchor_age_steps: int,
    algebraic_residual: float,
    full_residual: float,
    scaled_difference_floor: float,
) -> dict[str, Any]:
    start_time = float(metadata["start_time"])
    stop_time = float(metadata["stop_time"])
    tolerance = trace_time_tolerance(stop_time)
    factor_metadata = metadata["factor_trajectories"]
    if metadata["sampling_mode"] == "integrated_output_times":
        interpolated_factors: list[int] = []
    else:
        interpolated_factors = [
            int(factor)
            for factor in quadruplet["refinement_factors"]
            if not _is_native_refinement_time(
                sample_time,
                start_time=start_time,
                stop_time=stop_time,
                nominal_step=float(factor_metadata[str(factor)]["nominal_step"]),
                tolerance=tolerance,
            )
        ]
    maximum_solve_residual = max(abs(algebraic_residual), abs(full_residual))
    return {
        "sample_time": sample_time,
        "native_time_tolerance": tolerance,
        "sampling_mode": metadata["sampling_mode"],
        "interpolated_refinement_factors": interpolated_factors,
        "all_refinement_factors_native": not interpolated_factors,
        "anchor_age_steps": anchor_age_steps,
        "anchor_reset_context": anchor_age_steps <= 1,
        "maximum_solve_residual": maximum_solve_residual,
        "algebraic_solve_floor_context": (
            maximum_solve_residual >= scaled_difference_floor
        ),
    }


def _is_native_refinement_time(
    sample_time: float,
    *,
    start_time: float,
    stop_time: float,
    nominal_step: float,
    tolerance: float,
) -> bool:
    if abs(sample_time - start_time) <= tolerance:
        return True
    if abs(sample_time - stop_time) <= tolerance:
        return True
    index = round((sample_time - start_time) / nominal_step)
    native_time = start_time + index * nominal_step
    return abs(sample_time - native_time) <= tolerance


def _global_order_aware_epoch_summary(
    eligible_samples: list[dict[str, Any]],
    triplet: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    triplet_id = str(triplet["triplet_id"])
    grouped: dict[int, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for sample in eligible_samples:
        diagnostic = sample["global_order_aware_diagnostics"].get(triplet_id)
        if isinstance(diagnostic, dict):
            grouped[int(sample["anchor_generation"])].append((sample, diagnostic))
    epoch_records: list[dict[str, Any]] = []
    qualified_samples = 0
    reference_covered = 0
    total_covered = 0
    envelope_reference_covered = 0
    envelope_total_covered = 0
    observed_orders: list[float] = []
    inflation_ratios: list[float] = []
    envelope_inflation_ratios: list[float] = []
    rejection_causes: Counter[str] = Counter()
    for generation, rows in sorted(grouped.items()):
        coarse_rms = math.sqrt(
            sum(
                diagnostic["coarse_epoch_discrepancy"] ** 2
                for _, diagnostic in rows
            )
            / len(rows)
        )
        fine_rms = math.sqrt(
            sum(
                diagnostic["fine_epoch_discrepancy"] ** 2
                for _, diagnostic in rows
            )
            / len(rows)
        )
        observed_order, _, rejection_cause = _order_aware_estimate(
            coarse_rms,
            fine_rms,
            ratio=float(triplet["refinement_ratio"]),
            settings=settings,
        )
        epoch_record = {
            "anchor_generation": generation,
            "sample_count": len(rows),
            "coarse_rms_epoch_discrepancy": coarse_rms,
            "fine_rms_epoch_discrepancy": fine_rms,
            "observed_order": observed_order,
            "qualified": rejection_cause is None,
            "rejection_cause": rejection_cause,
        }
        epoch_records.append(epoch_record)
        if rejection_cause is not None:
            rejection_causes[rejection_cause] += 1
            continue
        assert observed_order is not None
        denominator = float(triplet["refinement_ratio"]) ** observed_order - 1.0
        envelope_estimate = max(
            diagnostic["fine_epoch_discrepancy"] for _, diagnostic in rows
        ) / denominator
        epoch_record["envelope_estimated_fine_error"] = envelope_estimate
        observed_orders.append(observed_order)
        qualified_samples += len(rows)
        for sample, diagnostic in rows:
            estimated_fine_error = (
                diagnostic["fine_epoch_discrepancy"] / denominator
            )
            finest_authority_error = diagnostic[
                "finest_refined_epoch_authority_error"
            ]
            reference_covered += finest_authority_error <= estimated_fine_error
            total_covered += sample["authority_epoch_drift_error"] <= (
                sample["recursive_internal_bound"] + estimated_fine_error
            )
            envelope_reference_covered += (
                finest_authority_error <= envelope_estimate
            )
            envelope_total_covered += sample["authority_epoch_drift_error"] <= (
                sample["recursive_internal_bound"] + envelope_estimate
            )
            if finest_authority_error > 0.0:
                inflation_ratios.append(
                    estimated_fine_error / finest_authority_error
                )
                envelope_inflation_ratios.append(
                    envelope_estimate / finest_authority_error
                )
    eligible_count = sum(len(rows) for rows in grouped.values())
    qualified_epochs = sum(record["qualified"] for record in epoch_records)
    return {
        "epoch_count": len(epoch_records),
        "qualified_epochs": qualified_epochs,
        "rejected_epochs": len(epoch_records) - qualified_epochs,
        "epoch_qualification_fraction": (
            qualified_epochs / len(epoch_records) if epoch_records else None
        ),
        "eligible_samples": eligible_count,
        "qualified_samples": qualified_samples,
        "rejected_samples": eligible_count - qualified_samples,
        "sample_qualification_fraction": (
            qualified_samples / eligible_count if eligible_count else None
        ),
        "reference_estimator_covered": reference_covered,
        "effective_reference_estimator_coverage_fraction": (
            reference_covered / eligible_count if eligible_count else None
        ),
        "qualified_reference_estimator_coverage_fraction": (
            reference_covered / qualified_samples if qualified_samples else None
        ),
        "babcs_total_covered": total_covered,
        "effective_babcs_total_coverage_fraction": (
            total_covered / eligible_count if eligible_count else None
        ),
        "qualified_babcs_total_coverage_fraction": (
            total_covered / qualified_samples if qualified_samples else None
        ),
        "minimum_observed_order": min(observed_orders, default=None),
        "median_observed_order": _percentile(observed_orders, 0.5),
        "maximum_observed_order": max(observed_orders, default=None),
        "median_uncertainty_to_finest_authority_error_ratio": _percentile(
            inflation_ratios,
            0.5,
        ),
        "p95_uncertainty_to_finest_authority_error_ratio": _percentile(
            inflation_ratios,
            0.95,
        ),
        "rejection_causes": dict(sorted(rejection_causes.items())),
        "envelope": {
            "reference_estimator_covered": envelope_reference_covered,
            "effective_reference_estimator_coverage_fraction": (
                envelope_reference_covered / eligible_count
                if eligible_count
                else None
            ),
            "qualified_reference_estimator_coverage_fraction": (
                envelope_reference_covered / qualified_samples
                if qualified_samples
                else None
            ),
            "babcs_total_covered": envelope_total_covered,
            "effective_babcs_total_coverage_fraction": (
                envelope_total_covered / eligible_count if eligible_count else None
            ),
            "qualified_babcs_total_coverage_fraction": (
                envelope_total_covered / qualified_samples
                if qualified_samples
                else None
            ),
            "median_uncertainty_to_finest_authority_error_ratio": _percentile(
                envelope_inflation_ratios,
                0.5,
            ),
            "p95_uncertainty_to_finest_authority_error_ratio": _percentile(
                envelope_inflation_ratios,
                0.95,
            ),
        },
        "epochs": epoch_records,
    }


def _global_order_aware_triplet_sweep(
    record: dict[str, Any],
    eligible_samples: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    metadata = record.get("global_dual_trajectory")
    if not isinstance(metadata, dict):
        return {}, []
    settings = metadata.get("order_aware")
    if not isinstance(settings, dict):
        return {}, []
    factor_metadata = metadata["factor_trajectories"]
    triplet_results: dict[str, dict[str, Any]] = {}
    candidates: list[dict[str, Any]] = []
    for triplet in settings["triplets"]:
        triplet_id = str(triplet["triplet_id"])
        diagnostics = [
            sample["global_order_aware_diagnostics"].get(triplet_id)
            for sample in eligible_samples
        ]
        diagnostics = [
            diagnostic for diagnostic in diagnostics if isinstance(diagnostic, dict)
        ]
        qualified = [diagnostic for diagnostic in diagnostics if diagnostic["qualified"]]
        observed_orders = [
            float(diagnostic["observed_order"])
            for diagnostic in qualified
            if diagnostic["observed_order"] is not None
        ]
        estimates = [
            float(diagnostic["estimated_fine_error"])
            for diagnostic in qualified
            if diagnostic["estimated_fine_error"] is not None
        ]
        inflation_ratios = [
            diagnostic["estimated_fine_error"]
            / diagnostic["finest_refined_epoch_authority_error"]
            for diagnostic in qualified
            if diagnostic["estimated_fine_error"] is not None
            and diagnostic["finest_refined_epoch_authority_error"] > 0.0
        ]
        reference_covered = sum(
            bool(diagnostic["reference_estimator_covered"])
            for diagnostic in qualified
        )
        total_covered = sum(
            bool(diagnostic["total_uncertainty_covered"])
            for diagnostic in qualified
        )
        rejection_causes = Counter(
            str(diagnostic["rejection_cause"])
            for diagnostic in diagnostics
            if diagnostic["rejection_cause"] is not None
        )
        factors = (
            int(triplet["coarse_refinement_factor"]),
            int(triplet["middle_refinement_factor"]),
            int(triplet["fine_refinement_factor"]),
        )
        work_units = sum(
            int(factor_metadata[str(factor)]["work"]["deterministic_work_units"])
            for factor in factors
        )
        result = {
            **triplet,
            "eligible": len(diagnostics),
            "qualified": len(qualified),
            "rejected": len(diagnostics) - len(qualified),
            "qualification_fraction": (
                len(qualified) / len(diagnostics) if diagnostics else None
            ),
            "rejection_causes": dict(sorted(rejection_causes.items())),
            "reference_estimator_covered": reference_covered,
            "qualified_reference_estimator_coverage_fraction": (
                reference_covered / len(qualified) if qualified else None
            ),
            "effective_reference_estimator_coverage_fraction": (
                reference_covered / len(diagnostics) if diagnostics else None
            ),
            "babcs_total_covered": total_covered,
            "qualified_babcs_total_coverage_fraction": (
                total_covered / len(qualified) if qualified else None
            ),
            "effective_babcs_total_coverage_fraction": (
                total_covered / len(diagnostics) if diagnostics else None
            ),
            "minimum_observed_order": min(observed_orders, default=None),
            "median_observed_order": _percentile(observed_orders, 0.5),
            "p95_observed_order": _percentile(observed_orders, 0.95),
            "maximum_observed_order": max(observed_orders, default=None),
            "maximum_estimated_fine_error": max(estimates, default=None),
            "median_estimated_fine_error": _percentile(estimates, 0.5),
            "p95_estimated_fine_error": _percentile(estimates, 0.95),
            "median_uncertainty_to_finest_authority_error_ratio": _percentile(
                inflation_ratios,
                0.5,
            ),
            "p95_uncertainty_to_finest_authority_error_ratio": _percentile(
                inflation_ratios,
                0.95,
            ),
            "independent_triplet_work_units": work_units,
            "epoch_qualified": _global_order_aware_epoch_summary(
                eligible_samples,
                triplet,
                settings,
            ),
        }
        triplet_results[triplet_id] = result
        if (
            result["qualification_fraction"] is not None
            and result["median_uncertainty_to_finest_authority_error_ratio"] is not None
        ):
            candidates.append(result)
    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_order_aware_triplet(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["independent_triplet_work_units"],
            row["median_uncertainty_to_finest_authority_error_ratio"],
            -row["effective_babcs_total_coverage_fraction"],
            row["triplet_id"],
        )
    )
    return triplet_results, frontier


def _global_statewise_four_level_sweep(
    record: dict[str, Any],
    eligible_samples: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    metadata = record.get("global_dual_trajectory")
    if not isinstance(metadata, dict):
        return {}, []
    settings = metadata.get("statewise_four_level")
    factor_metadata = metadata.get("factor_trajectories")
    if not isinstance(settings, dict) or not isinstance(factor_metadata, dict):
        return {}, []

    quadruplet_results: dict[str, dict[str, Any]] = {}
    candidates: list[dict[str, Any]] = []
    for quadruplet in settings["quadruplets"]:
        quadruplet_id = str(quadruplet["quadruplet_id"])
        diagnostics = [
            sample["global_statewise_four_level_diagnostics"].get(quadruplet_id)
            for sample in eligible_samples
        ]
        diagnostics = [
            diagnostic for diagnostic in diagnostics if isinstance(diagnostic, dict)
        ]
        qualified = [diagnostic for diagnostic in diagnostics if diagnostic["qualified"]]
        state_diagnostics = [
            state
            for diagnostic in diagnostics
            for state in diagnostic["states"]
        ]
        qualified_states = [state for state in state_diagnostics if state["qualified"]]
        sample_rejection_causes = Counter(
            str(diagnostic["rejection_cause"])
            for diagnostic in diagnostics
            if diagnostic["rejection_cause"] is not None
        )
        state_rejection_causes = Counter(
            str(state["rejection_cause"])
            for state in state_diagnostics
            if state["rejection_cause"] is not None
        )
        floor_context_state_mentions: Counter[str] = Counter()
        for diagnostic in diagnostics:
            for context in diagnostic["floor_contexts"]:
                floor_context_state_mentions[str(context)] += int(
                    diagnostic["floor_rejected_state_count"]
                )
        reference_covered = sum(
            bool(diagnostic["reference_estimator_covered"])
            for diagnostic in qualified
        )
        total_covered = sum(
            bool(diagnostic["total_uncertainty_covered"])
            for diagnostic in qualified
        )
        component_reference_covered = sum(
            bool(state["component_reference_covered"])
            for state in qualified_states
        )
        order_differences = [
            float(state["adjacent_order_difference"])
            for state in state_diagnostics
            if state["adjacent_order_difference"] is not None
        ]
        coefficient_differences = [
            float(state["coefficient_relative_difference"])
            for state in state_diagnostics
            if state["coefficient_relative_difference"] is not None
        ]
        residual_ratios = [
            float(state["extrapolant_residual_ratio"])
            for state in state_diagnostics
            if state["extrapolant_residual_ratio"] is not None
        ]
        estimates = [
            float(diagnostic["estimated_scaled_finest_error"])
            for diagnostic in qualified
            if diagnostic["estimated_scaled_finest_error"] is not None
        ]
        inflation_ratios = [
            float(diagnostic["uncertainty_to_finest_authority_error_ratio"])
            for diagnostic in qualified
            if diagnostic["uncertainty_to_finest_authority_error_ratio"] is not None
        ]
        factors = tuple(int(value) for value in quadruplet["refinement_factors"])
        work_units = sum(
            int(factor_metadata[str(factor)]["work"]["deterministic_work_units"])
            for factor in factors
        )
        result = {
            **quadruplet,
            "eligible_samples": len(diagnostics),
            "qualified_samples": len(qualified),
            "rejected_samples": len(diagnostics) - len(qualified),
            "sample_qualification_fraction": (
                len(qualified) / len(diagnostics) if diagnostics else None
            ),
            "sample_rejection_causes": dict(
                sorted(sample_rejection_causes.items())
            ),
            "total_states": len(state_diagnostics),
            "qualified_states": len(qualified_states),
            "rejected_states": len(state_diagnostics) - len(qualified_states),
            "state_qualification_fraction": (
                len(qualified_states) / len(state_diagnostics)
                if state_diagnostics
                else None
            ),
            "state_rejection_causes": dict(sorted(state_rejection_causes.items())),
            "floor_rejected_state_count": sum(
                int(diagnostic["floor_rejected_state_count"])
                for diagnostic in diagnostics
            ),
            "floor_context_state_mentions": dict(
                sorted(floor_context_state_mentions.items())
            ),
            "interpolated_sample_count": sum(
                bool(
                    diagnostic["sampling_context"]
                    and diagnostic["sampling_context"][
                        "interpolated_refinement_factors"
                    ]
                )
                for diagnostic in diagnostics
            ),
            "all_native_sample_count": sum(
                bool(
                    diagnostic["sampling_context"]
                    and diagnostic["sampling_context"][
                        "all_refinement_factors_native"
                    ]
                )
                for diagnostic in diagnostics
            ),
            "anchor_reset_context_sample_count": sum(
                bool(
                    diagnostic["sampling_context"]
                    and diagnostic["sampling_context"]["anchor_reset_context"]
                )
                for diagnostic in diagnostics
            ),
            "algebraic_solve_floor_context_sample_count": sum(
                bool(
                    diagnostic["sampling_context"]
                    and diagnostic["sampling_context"][
                        "algebraic_solve_floor_context"
                    ]
                )
                for diagnostic in diagnostics
            ),
            "component_reference_covered": component_reference_covered,
            "qualified_component_reference_coverage_fraction": (
                component_reference_covered / len(qualified_states)
                if qualified_states
                else None
            ),
            "effective_component_reference_coverage_fraction": (
                component_reference_covered / len(state_diagnostics)
                if state_diagnostics
                else None
            ),
            "reference_estimator_covered": reference_covered,
            "qualified_reference_estimator_coverage_fraction": (
                reference_covered / len(qualified) if qualified else None
            ),
            "effective_reference_estimator_coverage_fraction": (
                reference_covered / len(diagnostics) if diagnostics else None
            ),
            "babcs_total_covered": total_covered,
            "qualified_babcs_total_coverage_fraction": (
                total_covered / len(qualified) if qualified else None
            ),
            "effective_babcs_total_coverage_fraction": (
                total_covered / len(diagnostics) if diagnostics else None
            ),
            "median_adjacent_order_difference": _percentile(
                order_differences,
                0.5,
            ),
            "p95_adjacent_order_difference": _percentile(
                order_differences,
                0.95,
            ),
            "median_coefficient_relative_difference": _percentile(
                coefficient_differences,
                0.5,
            ),
            "p95_coefficient_relative_difference": _percentile(
                coefficient_differences,
                0.95,
            ),
            "median_extrapolant_residual_ratio": _percentile(
                residual_ratios,
                0.5,
            ),
            "p95_extrapolant_residual_ratio": _percentile(
                residual_ratios,
                0.95,
            ),
            "maximum_estimated_scaled_finest_error": max(estimates, default=None),
            "median_estimated_scaled_finest_error": _percentile(estimates, 0.5),
            "p95_estimated_scaled_finest_error": _percentile(estimates, 0.95),
            "median_uncertainty_to_finest_authority_error_ratio": _percentile(
                inflation_ratios,
                0.5,
            ),
            "p95_uncertainty_to_finest_authority_error_ratio": _percentile(
                inflation_ratios,
                0.95,
            ),
            "independent_quadruplet_work_units": work_units,
        }
        quadruplet_results[quadruplet_id] = result
        if (
            result["sample_qualification_fraction"] is not None
            and result["median_uncertainty_to_finest_authority_error_ratio"]
            is not None
        ):
            candidates.append(result)
    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_statewise_quadruplet(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["independent_quadruplet_work_units"],
            row["median_uncertainty_to_finest_authority_error_ratio"],
            -row["effective_babcs_total_coverage_fraction"],
            row["quadruplet_id"],
        )
    )
    return quadruplet_results, frontier


def _global_statewise_epoch_sweep(
    record: dict[str, Any],
    eligible_samples: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    metadata = record.get("global_dual_trajectory")
    if not isinstance(metadata, dict):
        return {}, []
    settings = metadata.get("statewise_four_level")
    factor_metadata = metadata.get("factor_trajectories")
    if not isinstance(settings, dict) or not isinstance(factor_metadata, dict):
        return {}, []
    epoch_fit = settings.get("epoch_fit")
    if not isinstance(epoch_fit, dict):
        return {}, []

    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for sample in eligible_samples:
        grouped[int(sample["anchor_generation"])].append(sample)

    sweep: dict[str, dict[str, Any]] = {}
    candidates: list[dict[str, Any]] = []
    for quadruplet in settings["quadruplets"]:
        quadruplet_id = str(quadruplet["quadruplet_id"])
        epochs = [
            _statewise_epoch_diagnostic(
                generation,
                rows,
                quadruplet,
                settings,
                epoch_fit,
            )
            for generation, rows in sorted(grouped.items())
        ]
        qualified_epochs = [epoch for epoch in epochs if epoch["qualified"]]
        eligible_sample_count = sum(epoch["sample_count"] for epoch in epochs)
        qualified_sample_count = sum(
            epoch["sample_count"] for epoch in qualified_epochs
        )
        state_epoch_count = sum(epoch["state_count"] for epoch in epochs)
        qualified_state_epoch_count = sum(
            epoch["qualified_state_count"] for epoch in epochs
        )
        reference_covered = sum(
            epoch["reference_estimator_covered"] for epoch in qualified_epochs
        )
        total_covered = sum(
            epoch["babcs_total_covered"] for epoch in qualified_epochs
        )
        inflation_ratios = [
            ratio
            for epoch in qualified_epochs
            for ratio in epoch["uncertainty_to_finest_authority_error_ratios"]
        ]
        epoch_rejection_causes = Counter(
            str(epoch["rejection_cause"])
            for epoch in epochs
            if epoch["rejection_cause"] is not None
        )
        state_rejection_causes = Counter(
            str(state["rejection_cause"])
            for epoch in epochs
            for state in epoch["states"]
            if state["rejection_cause"] is not None
        )
        per_state: dict[str, dict[str, Any]] = {}
        state_names = sorted(
            {
                str(state["state_name"])
                for epoch in epochs
                for state in epoch["states"]
            }
        )
        for state_name in state_names:
            rows = [
                state
                for epoch in epochs
                for state in epoch["states"]
                if state["state_name"] == state_name
            ]
            causes = Counter(
                str(state["rejection_cause"])
                for state in rows
                if state["rejection_cause"] is not None
            )
            per_state[state_name] = {
                "epoch_count": len(rows),
                "qualified_epochs": sum(bool(state["qualified"]) for state in rows),
                "rejected_epochs": sum(not state["qualified"] for state in rows),
                "coherent_zero_crossing_intervals": sum(
                    int(state["coherent_zero_crossing_interval_count"])
                    for state in rows
                ),
                "unmatched_sign_change_intervals": sum(
                    int(state["unmatched_sign_change_interval_count"])
                    for state in rows
                ),
                "rejection_causes": dict(sorted(causes.items())),
            }
        factors = tuple(int(value) for value in quadruplet["refinement_factors"])
        work_units = sum(
            int(factor_metadata[str(factor)]["work"]["deterministic_work_units"])
            for factor in factors
        )
        result = {
            **quadruplet,
            "sampling_mode": metadata["sampling_mode"],
            "epoch_count": len(epochs),
            "qualified_epochs": len(qualified_epochs),
            "rejected_epochs": len(epochs) - len(qualified_epochs),
            "epoch_qualification_fraction": (
                len(qualified_epochs) / len(epochs) if epochs else None
            ),
            "eligible_samples": eligible_sample_count,
            "qualified_samples": qualified_sample_count,
            "rejected_samples": eligible_sample_count - qualified_sample_count,
            "sample_qualification_fraction": (
                qualified_sample_count / eligible_sample_count
                if eligible_sample_count
                else None
            ),
            "state_epoch_count": state_epoch_count,
            "qualified_state_epochs": qualified_state_epoch_count,
            "rejected_state_epochs": state_epoch_count - qualified_state_epoch_count,
            "state_epoch_qualification_fraction": (
                qualified_state_epoch_count / state_epoch_count
                if state_epoch_count
                else None
            ),
            "epoch_rejection_causes": dict(sorted(epoch_rejection_causes.items())),
            "state_rejection_causes": dict(sorted(state_rejection_causes.items())),
            "coherent_zero_crossing_intervals": sum(
                int(epoch["coherent_zero_crossing_interval_count"])
                for epoch in epochs
            ),
            "unmatched_sign_change_intervals": sum(
                int(epoch["unmatched_sign_change_interval_count"])
                for epoch in epochs
            ),
            "reference_estimator_covered": reference_covered,
            "qualified_reference_estimator_coverage_fraction": (
                reference_covered / qualified_sample_count
                if qualified_sample_count
                else None
            ),
            "effective_reference_estimator_coverage_fraction": (
                reference_covered / eligible_sample_count
                if eligible_sample_count
                else None
            ),
            "babcs_total_covered": total_covered,
            "qualified_babcs_total_coverage_fraction": (
                total_covered / qualified_sample_count
                if qualified_sample_count
                else None
            ),
            "effective_babcs_total_coverage_fraction": (
                total_covered / eligible_sample_count
                if eligible_sample_count
                else None
            ),
            "median_uncertainty_to_finest_authority_error_ratio": _percentile(
                inflation_ratios,
                0.5,
            ),
            "p95_uncertainty_to_finest_authority_error_ratio": _percentile(
                inflation_ratios,
                0.95,
            ),
            "independent_quadruplet_work_units": work_units,
            "per_state": per_state,
            "epochs": epochs,
        }
        sweep[quadruplet_id] = result
        if (
            result["sample_qualification_fraction"] is not None
            and result["median_uncertainty_to_finest_authority_error_ratio"]
            is not None
        ):
            candidates.append(result)
    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_statewise_epoch(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["independent_quadruplet_work_units"],
            row["median_uncertainty_to_finest_authority_error_ratio"],
            -row["effective_babcs_total_coverage_fraction"],
            row["quadruplet_id"],
        )
    )
    return sweep, frontier


def _two_term_design_metadata(policy: dict[str, Any]) -> dict[str, Any]:
    training_factors = tuple(
        int(value) for value in policy["training_refinement_factors"]
    )
    holdout_factor = int(policy["holdout_refinement_factor"])
    primary_order = float(policy["primary_order"])
    secondary_order = float(policy["secondary_order"])
    design_matrix = [
        [1.0, factor ** (-primary_order), factor ** (-secondary_order)]
        for factor in training_factors
    ]
    normal_matrix = [
        [
            sum(row[left] * row[right] for row in design_matrix)
            for right in range(3)
        ]
        for left in range(3)
    ]
    try:
        inverse_columns = [
            solve_linear(
                normal_matrix,
                [1.0 if row == column else 0.0 for row in range(3)],
            )
            for column in range(3)
        ]
    except SingularMatrixError:
        return {
            **policy,
            "qualified": False,
            "rejection_cause": "singular_two_term_design",
            "design_condition_number": None,
            "intercept_residual_leverage": None,
            "residual_amplification_factor": None,
        }
    normal_inverse = [
        [inverse_columns[column][row] for column in range(3)]
        for row in range(3)
    ]
    condition_number = math.sqrt(
        _matrix_infinity_norm(normal_matrix)
        * _matrix_infinity_norm(normal_inverse)
    )
    intercept_weights = [
        sum(
            normal_inverse[0][column] * design_matrix[row][column]
            for column in range(3)
        )
        for row in range(len(training_factors))
    ]
    intercept_leverage = sum(abs(value) for value in intercept_weights)
    return {
        **policy,
        "qualified": all(
            math.isfinite(value)
            for value in (
                condition_number,
                intercept_leverage,
            )
        ),
        "rejection_cause": (
            None
            if math.isfinite(condition_number)
            and math.isfinite(intercept_leverage)
            else "non_finite_two_term_design"
        ),
        "design_condition_number": condition_number,
        "intercept_residual_leverage": intercept_leverage,
        "residual_amplification_factor": 1.0 + intercept_leverage,
        "design_matrix": design_matrix,
        "normal_inverse": normal_inverse,
        "holdout_design_row": [
            1.0,
            holdout_factor ** (-primary_order),
            holdout_factor ** (-secondary_order),
        ],
    }


def _fit_two_term_component(
    values_by_factor: dict[int, float],
    design: dict[str, Any],
) -> dict[str, Any] | None:
    training_factors = tuple(
        int(value) for value in design["training_refinement_factors"]
    )
    holdout_factor = int(design["holdout_refinement_factor"])
    training_values = [values_by_factor[factor] for factor in training_factors]
    right_hand_side = [
        sum(
            design["design_matrix"][row][column] * training_values[row]
            for row in range(len(training_factors))
        )
        for column in range(3)
    ]
    coefficients = [
        sum(
            design["normal_inverse"][row][column]
            * right_hand_side[column]
            for column in range(3)
        )
        for row in range(3)
    ]
    training_predictions = [
        sum(
            design["design_matrix"][row][column] * coefficients[column]
            for column in range(3)
        )
        for row in range(len(training_factors))
    ]
    training_residuals = [
        actual - predicted
        for actual, predicted in zip(
            training_values,
            training_predictions,
            strict=True,
        )
    ]
    holdout_prediction = sum(
        value * coefficient
        for value, coefficient in zip(
            design["holdout_design_row"],
            coefficients,
            strict=True,
        )
    )
    holdout_residual = values_by_factor[holdout_factor] - holdout_prediction
    primary_contribution = (
        coefficients[1]
        * holdout_factor ** (-float(design["primary_order"]))
    )
    secondary_contribution = (
        coefficients[2]
        * holdout_factor ** (-float(design["secondary_order"]))
    )
    values = (
        *coefficients,
        *training_predictions,
        *training_residuals,
        holdout_prediction,
        holdout_residual,
        primary_contribution,
        secondary_contribution,
    )
    if any(not math.isfinite(value) for value in values):
        return None
    residual_envelope = max(
        *(abs(value) for value in training_residuals),
        abs(holdout_residual),
    )
    estimated_holdout_error = (
        abs(primary_contribution)
        + abs(secondary_contribution)
        + float(design["residual_amplification_factor"])
        * residual_envelope
    )
    return {
        "limit_value": coefficients[0],
        "primary_coefficient": coefficients[1],
        "secondary_coefficient": coefficients[2],
        "training_predictions": training_predictions,
        "training_residuals": training_residuals,
        "holdout_prediction": holdout_prediction,
        "holdout_residual": holdout_residual,
        "primary_holdout_contribution": primary_contribution,
        "secondary_holdout_contribution": secondary_contribution,
        "residual_envelope": residual_envelope,
        "estimated_holdout_absolute_error": estimated_holdout_error,
    }


def _matrix_infinity_norm(matrix: list[list[float]]) -> float:
    return max(
        (sum(abs(value) for value in row) for row in matrix),
        default=0.0,
    )


def _five_level_modal_row(
    sample: dict[str, Any],
    *,
    required_factors: tuple[int, ...],
    fallback_quadruplet_id: str,
    basis_vectors: list[list[float]],
    config: BABCSConfig,
) -> tuple[dict[str, Any] | None, str | None]:
    diagnostics = sample.get("global_statewise_four_level_diagnostics")
    if not isinstance(diagnostics, dict):
        return None, "missing_statewise_diagnostics"
    factor_states: dict[int, list[float]] = {}
    state_names: list[str] | None = None
    for diagnostic in diagnostics.values():
        if not isinstance(diagnostic, dict):
            continue
        factors = [int(value) for value in diagnostic["refinement_factors"]]
        states = diagnostic["states"]
        names = [str(state["state_name"]) for state in states]
        if state_names is None:
            state_names = names
        elif names != state_names:
            return None, "inconsistent_five_level_state_order"
        for level, factor in enumerate(factors):
            if factor not in required_factors:
                continue
            values = [
                float(state["refinement_values"][level]) for state in states
            ]
            existing = factor_states.get(factor)
            if existing is not None and existing != values:
                return None, "inconsistent_overlapping_factor_values"
            factor_states[factor] = values
    if any(factor not in factor_states for factor in required_factors):
        return None, "missing_five_level_factor_values"
    fallback = diagnostics.get(fallback_quadruplet_id)
    if not isinstance(fallback, dict):
        return None, "missing_loop_5g_fallback_diagnostic"
    refinement_modes = {
        factor: _modal_coordinates(factor_states[factor], basis_vectors)
        for factor in required_factors
    }
    mode_count = len(basis_vectors)
    mode_scales = [
        config.absolute_tolerance
        + config.relative_tolerance
        * max(
            abs(refinement_modes[factor][mode])
            for factor in required_factors
        )
        for mode in range(mode_count)
    ]
    return (
        {
            "sample": sample,
            "fallback_diagnostic": fallback,
            "refinement_modes_by_factor": refinement_modes,
            "mode_scales": mode_scales,
        },
        None,
    )


def _two_term_modal_group_diagnostic(
    policy: dict[str, Any],
    settings: dict[str, Any],
    epoch_fit: dict[str, Any],
    group: dict[str, Any],
    rows: list[dict[str, Any]],
    design: dict[str, Any],
    fallback_group: dict[str, Any] | None,
) -> dict[str, Any]:
    mode_indices = [int(value) for value in group["mode_indices"]]
    dimension = len(mode_indices)
    diagnostic: dict[str, Any] = {
        "group_id": str(group["group_id"]),
        "mode_indices": mode_indices,
        "dimension": dimension,
        "eigenvalues": list(map(float, group["eigenvalues"])),
        "sample_count": len(rows),
        "policy_id": str(policy["policy_id"]),
        "primary_order": float(policy["primary_order"]),
        "secondary_order": float(policy["secondary_order"]),
        "training_refinement_factors": list(
            map(int, policy["training_refinement_factors"])
        ),
        "holdout_refinement_factor": int(
            policy["holdout_refinement_factor"]
        ),
        "design_condition_number": design.get("design_condition_number"),
        "intercept_residual_leverage": design.get(
            "intercept_residual_leverage"
        ),
        "residual_amplification_factor": design.get(
            "residual_amplification_factor"
        ),
        "loop_5g_fallback_qualified": bool(
            fallback_group is not None and fallback_group.get("qualified")
        ),
        "loop_5g_fallback_rejection_cause": (
            fallback_group.get("rejection_cause")
            if fallback_group is not None
            else "missing_loop_5g_group"
        ),
        "fit_attempted": False,
        "qualification_source": None,
        "training_residual_ratio": None,
        "holdout_residual_ratio": None,
        "primary_holdout_contribution_norm": None,
        "secondary_holdout_contribution_norm": None,
        "secondary_to_primary_contribution_ratio": None,
        "residual_envelope_norm": None,
        "estimated_holdout_absolute_errors": None,
        "qualified": False,
        "rejection_cause": None,
    }

    def reject(cause: str) -> dict[str, Any]:
        diagnostic["rejection_cause"] = cause
        return diagnostic

    if fallback_group is not None and fallback_group.get("qualified"):
        diagnostic.update(
            {
                "estimated_holdout_absolute_errors": fallback_group[
                    "estimated_finest_absolute_errors"
                ],
                "qualification_source": "loop_5g_fallback",
                "qualified": True,
            }
        )
        return diagnostic
    diagnostic["fit_attempted"] = True
    if len(rows) < int(epoch_fit["minimum_epoch_samples"]):
        return reject("insufficient_two_term_epoch_samples")
    if not design.get("qualified"):
        return reject(str(design.get("rejection_cause")))
    condition_number = float(design["design_condition_number"])
    if condition_number > float(
        settings["maximum_design_condition_number"]
    ):
        return reject("two_term_design_condition_exceeded")

    training_factors = tuple(
        int(value) for value in policy["training_refinement_factors"]
    )
    holdout_factor = int(policy["holdout_refinement_factor"])
    component_scales: list[float] = []
    component_values: list[dict[int, float]] = []
    for row in rows:
        for mode in mode_indices:
            component_scales.append(float(row["mode_scales"][mode]))
            component_values.append(
                {
                    factor: float(
                        row["refinement_modes_by_factor"][factor][mode]
                    )
                    for factor in (*training_factors, holdout_factor)
                }
            )
    fits = [
        _fit_two_term_component(values, design) for values in component_values
    ]
    if any(fit is None for fit in fits):
        return reject("non_finite_two_term_fit")
    completed_fits = [fit for fit in fits if fit is not None]
    normalized_training_residuals: list[float] = []
    normalized_training_signal: list[float] = []
    normalized_holdout_residuals: list[float] = []
    normalized_holdout_signal: list[float] = []
    normalized_primary_contributions: list[float] = []
    normalized_secondary_contributions: list[float] = []
    normalized_residual_envelopes: list[float] = []
    estimates: list[float] = []
    for scale, fit in zip(component_scales, completed_fits, strict=True):
        normalized_training_residuals.extend(
            residual / scale for residual in fit["training_residuals"]
        )
        normalized_training_signal.extend(
            (prediction - fit["limit_value"]) / scale
            for prediction in fit["training_predictions"]
        )
        normalized_holdout_residuals.append(
            fit["holdout_residual"] / scale
        )
        normalized_holdout_signal.append(
            (
                fit["primary_holdout_contribution"]
                + fit["secondary_holdout_contribution"]
            )
            / scale
        )
        normalized_primary_contributions.append(
            fit["primary_holdout_contribution"] / scale
        )
        normalized_secondary_contributions.append(
            fit["secondary_holdout_contribution"] / scale
        )
        normalized_residual_envelopes.append(
            fit["residual_envelope"] / scale
        )
        estimates.append(float(fit["estimated_holdout_absolute_error"]))
    floor = float(settings["scaled_difference_floor"])
    training_floor = floor * math.sqrt(
        len(training_factors) * len(component_values)
    )
    holdout_floor = floor * math.sqrt(len(component_values))
    training_signal_norm = _vector_norm(normalized_training_signal)
    holdout_signal_norm = _vector_norm(normalized_holdout_signal)
    if holdout_signal_norm <= holdout_floor:
        return reject("two_term_holdout_signal_at_or_below_floor")
    training_ratio = _vector_norm(normalized_training_residuals) / max(
        training_signal_norm,
        training_floor,
    )
    holdout_ratio = _vector_norm(normalized_holdout_residuals) / max(
        holdout_signal_norm,
        holdout_floor,
    )
    primary_norm = _vector_norm(normalized_primary_contributions)
    secondary_norm = _vector_norm(normalized_secondary_contributions)
    diagnostic.update(
        {
            "training_residual_ratio": training_ratio,
            "holdout_residual_ratio": holdout_ratio,
            "primary_holdout_contribution_norm": primary_norm,
            "secondary_holdout_contribution_norm": secondary_norm,
            "secondary_to_primary_contribution_ratio": (
                secondary_norm / max(primary_norm, holdout_floor)
            ),
            "residual_envelope_norm": _vector_norm(
                normalized_residual_envelopes
            ),
        }
    )
    if training_ratio > float(settings["maximum_training_residual_ratio"]):
        return reject("two_term_training_residual_ratio_exceeded")
    if holdout_ratio > float(settings["maximum_holdout_residual_ratio"]):
        return reject("two_term_holdout_residual_ratio_exceeded")
    diagnostic.update(
        {
            "estimated_holdout_absolute_errors": [
                estimates[index : index + dimension]
                for index in range(0, len(estimates), dimension)
            ],
            "qualification_source": "five_level_two_term",
            "qualified": True,
        }
    )
    return diagnostic


def _two_term_modal_epoch_diagnostic(
    anchor_generation: int,
    samples: list[dict[str, Any]],
    policy: dict[str, Any],
    settings: dict[str, Any],
    statewise_settings: dict[str, Any],
    epoch_fit: dict[str, Any],
    basis: dict[str, Any],
    config: BABCSConfig,
    design: dict[str, Any],
) -> dict[str, Any]:
    fallback_quadruplet_id = str(settings["fallback_quadruplet_id"])
    fallback_quadruplet = next(
        quadruplet
        for quadruplet in statewise_settings["quadruplets"]
        if quadruplet["quadruplet_id"] == fallback_quadruplet_id
    )
    fallback_epoch = _modal_epoch_diagnostic(
        anchor_generation,
        samples,
        fallback_quadruplet,
        statewise_settings,
        epoch_fit,
        basis,
        config,
    )
    fallback_groups = {
        str(group["group_id"]): group
        for group in fallback_epoch["mode_groups"]
    }
    basis_vectors = [list(map(float, row)) for row in basis["basis_vectors"]]
    required_factors = tuple(
        int(value) for value in policy["training_refinement_factors"]
    ) + (int(policy["holdout_refinement_factor"]),)
    rows: list[dict[str, Any]] = []
    for sample in samples:
        row, cause = _five_level_modal_row(
            sample,
            required_factors=required_factors,
            fallback_quadruplet_id=fallback_quadruplet_id,
            basis_vectors=basis_vectors,
            config=config,
        )
        if row is None:
            return {
                "anchor_generation": anchor_generation,
                "sample_count": 0,
                "mode_group_count": len(basis["mode_groups"]),
                "qualified_mode_group_count": 0,
                "qualified": False,
                "rejection_cause": cause,
                "loop_5g_fallback_mode_group_count": 0,
                "two_term_mode_group_count": 0,
                "reference_estimator_covered": 0,
                "babcs_total_covered": 0,
                "uncertainty_to_finest_authority_error_ratios": [],
                "mode_groups": [],
                "sample_estimates": [],
            }
        rows.append(row)
    mode_group_diagnostics = [
        _two_term_modal_group_diagnostic(
            policy,
            settings,
            epoch_fit,
            group,
            rows,
            design,
            fallback_groups.get(str(group["group_id"])),
        )
        for group in basis["mode_groups"]
    ]
    qualified_groups = [
        group for group in mode_group_diagnostics if group["qualified"]
    ]
    qualified = len(qualified_groups) == len(mode_group_diagnostics)
    mode_count = len(basis_vectors)
    sample_estimates: list[dict[str, Any]] = []
    reference_covered = 0
    total_covered = 0
    inflation_ratios: list[float] = []
    if qualified:
        for sample_offset, row in enumerate(rows):
            modal_estimates = [0.0] * mode_count
            for group in mode_group_diagnostics:
                for group_offset, mode in enumerate(group["mode_indices"]):
                    modal_estimates[mode] = group[
                        "estimated_holdout_absolute_errors"
                    ][sample_offset][group_offset]
            state_estimates = [
                sum(
                    abs(basis_vectors[state][mode]) * modal_estimates[mode]
                    for mode in range(mode_count)
                )
                for state in range(mode_count)
            ]
            scales = [
                float(state["coverage_scale"])
                for state in row["fallback_diagnostic"]["states"]
            ]
            estimated_scaled_error = math.sqrt(
                sum(
                    (estimate / scale) ** 2
                    for estimate, scale in zip(
                        state_estimates,
                        scales,
                        strict=True,
                    )
                )
                / mode_count
            )
            finest_error = float(
                row["fallback_diagnostic"][
                    "finest_refined_epoch_authority_error"
                ]
            )
            total_uncertainty = (
                float(row["sample"]["recursive_internal_bound"])
                + estimated_scaled_error
            )
            reference_sample_covered = finest_error <= estimated_scaled_error
            total_sample_covered = (
                float(row["sample"]["authority_epoch_drift_error"])
                <= total_uncertainty
            )
            reference_covered += reference_sample_covered
            total_covered += total_sample_covered
            ratio = (
                estimated_scaled_error / finest_error
                if finest_error > 0.0
                else None
            )
            if ratio is not None:
                inflation_ratios.append(ratio)
            sample_estimates.append(
                {
                    "sample_index": row["sample"]["sample_index"],
                    "time": row["sample"]["time"],
                    "estimated_scaled_holdout_error": estimated_scaled_error,
                    "holdout_refined_epoch_authority_error": finest_error,
                    "reference_estimator_covered": reference_sample_covered,
                    "total_uncertainty": total_uncertainty,
                    "total_uncertainty_covered": total_sample_covered,
                    "uncertainty_to_holdout_authority_error_ratio": ratio,
                }
            )
    return {
        "anchor_generation": anchor_generation,
        "sample_count": len(rows),
        "sample_indices": [row["sample"]["sample_index"] for row in rows],
        "mode_group_count": len(mode_group_diagnostics),
        "qualified_mode_group_count": len(qualified_groups),
        "rejected_mode_group_count": (
            len(mode_group_diagnostics) - len(qualified_groups)
        ),
        "qualified": qualified,
        "rejection_cause": (
            None if qualified else "two_term_mode_group_qualification_failed"
        ),
        "loop_5g_fallback_mode_group_count": sum(
            group["qualification_source"] == "loop_5g_fallback"
            for group in mode_group_diagnostics
        ),
        "two_term_mode_group_count": sum(
            group["qualification_source"] == "five_level_two_term"
            for group in mode_group_diagnostics
        ),
        "reference_estimator_covered": reference_covered,
        "babcs_total_covered": total_covered,
        "uncertainty_to_finest_authority_error_ratios": inflation_ratios,
        "mode_groups": mode_group_diagnostics,
        "sample_estimates": sample_estimates,
    }


def _global_two_term_modal_sweep(
    record: dict[str, Any],
    eligible_samples: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    metadata = record.get("global_dual_trajectory")
    if not isinstance(metadata, dict):
        return {}, []
    statewise_settings = metadata.get("statewise_four_level")
    basis = metadata.get("modal_basis")
    factor_metadata = metadata.get("factor_trajectories")
    if (
        not isinstance(statewise_settings, dict)
        or not isinstance(basis, dict)
        or not isinstance(factor_metadata, dict)
        or not basis.get("qualified")
    ):
        return {}, []
    epoch_fit = statewise_settings.get("epoch_fit")
    modal_fit = epoch_fit.get("modal_fit") if isinstance(epoch_fit, dict) else None
    settings = (
        modal_fit.get("five_level_two_term")
        if isinstance(modal_fit, dict)
        else None
    )
    if not isinstance(epoch_fit, dict) or not isinstance(settings, dict):
        return {}, []

    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for sample in eligible_samples:
        grouped[int(sample["anchor_generation"])].append(sample)
    config = _config_from_record(record["configuration"])
    sweep: dict[str, dict[str, Any]] = {}
    candidates: list[dict[str, Any]] = []
    for policy in settings["policies"]:
        policy_id = str(policy["policy_id"])
        design = _two_term_design_metadata(policy)
        epochs = [
            _two_term_modal_epoch_diagnostic(
                generation,
                rows,
                policy,
                settings,
                statewise_settings,
                epoch_fit,
                basis,
                config,
                design,
            )
            for generation, rows in sorted(grouped.items())
        ]
        qualified_epochs = [epoch for epoch in epochs if epoch["qualified"]]
        eligible_sample_count = sum(epoch["sample_count"] for epoch in epochs)
        qualified_sample_count = sum(
            epoch["sample_count"] for epoch in qualified_epochs
        )
        group_epoch_count = sum(epoch["mode_group_count"] for epoch in epochs)
        qualified_group_epoch_count = sum(
            epoch["qualified_mode_group_count"] for epoch in epochs
        )
        reference_covered = sum(
            epoch["reference_estimator_covered"] for epoch in qualified_epochs
        )
        total_covered = sum(
            epoch["babcs_total_covered"] for epoch in qualified_epochs
        )
        inflation_ratios = [
            ratio
            for epoch in qualified_epochs
            for ratio in epoch["uncertainty_to_finest_authority_error_ratios"]
        ]
        group_rows = [
            group for epoch in epochs for group in epoch["mode_groups"]
        ]
        rejection_causes = Counter(
            str(group["rejection_cause"])
            for group in group_rows
            if group["rejection_cause"] is not None
        )
        training_ratios = [
            float(group["training_residual_ratio"])
            for group in group_rows
            if group["training_residual_ratio"] is not None
        ]
        holdout_ratios = [
            float(group["holdout_residual_ratio"])
            for group in group_rows
            if group["holdout_residual_ratio"] is not None
        ]
        secondary_ratios = [
            float(group["secondary_to_primary_contribution_ratio"])
            for group in group_rows
            if group["secondary_to_primary_contribution_ratio"] is not None
        ]
        per_group: dict[str, dict[str, Any]] = {}
        for group_id in (
            str(group["group_id"]) for group in basis["mode_groups"]
        ):
            rows = [
                group for group in group_rows if group["group_id"] == group_id
            ]
            causes = Counter(
                str(group["rejection_cause"])
                for group in rows
                if group["rejection_cause"] is not None
            )
            per_group[group_id] = {
                "epoch_count": len(rows),
                "qualified_epochs": sum(bool(group["qualified"]) for group in rows),
                "rejected_epochs": sum(not group["qualified"] for group in rows),
                "dimension": rows[0]["dimension"] if rows else 0,
                "eigenvalues": rows[0]["eigenvalues"] if rows else [],
                "loop_5g_fallback_epochs": sum(
                    group["qualification_source"] == "loop_5g_fallback"
                    for group in rows
                ),
                "five_level_two_term_epochs": sum(
                    group["qualification_source"] == "five_level_two_term"
                    for group in rows
                ),
                "fit_attempted_epochs": sum(
                    bool(group["fit_attempted"]) for group in rows
                ),
                "maximum_training_residual_ratio": max(
                    (
                        float(group["training_residual_ratio"])
                        for group in rows
                        if group["training_residual_ratio"] is not None
                    ),
                    default=None,
                ),
                "maximum_holdout_residual_ratio": max(
                    (
                        float(group["holdout_residual_ratio"])
                        for group in rows
                        if group["holdout_residual_ratio"] is not None
                    ),
                    default=None,
                ),
                "rejection_causes": dict(sorted(causes.items())),
            }
        required_factors = tuple(
            int(value) for value in policy["training_refinement_factors"]
        ) + (int(policy["holdout_refinement_factor"]),)
        work_units = sum(
            int(factor_metadata[str(factor)]["work"]["deterministic_work_units"])
            for factor in required_factors
        )
        result = {
            **policy,
            "sampling_mode": metadata["sampling_mode"],
            "fallback_quadruplet_id": settings["fallback_quadruplet_id"],
            "basis_sha256": basis["basis_sha256"],
            "basis_state_unit": basis["state_unit"],
            "mode_group_count": len(basis["mode_groups"]),
            "design_condition_number": design.get("design_condition_number"),
            "intercept_residual_leverage": design.get(
                "intercept_residual_leverage"
            ),
            "residual_amplification_factor": design.get(
                "residual_amplification_factor"
            ),
            "epoch_count": len(epochs),
            "qualified_epochs": len(qualified_epochs),
            "rejected_epochs": len(epochs) - len(qualified_epochs),
            "epoch_qualification_fraction": (
                len(qualified_epochs) / len(epochs) if epochs else None
            ),
            "eligible_samples": eligible_sample_count,
            "qualified_samples": qualified_sample_count,
            "rejected_samples": eligible_sample_count - qualified_sample_count,
            "sample_qualification_fraction": (
                qualified_sample_count / eligible_sample_count
                if eligible_sample_count
                else None
            ),
            "mode_group_epoch_count": group_epoch_count,
            "qualified_mode_group_epochs": qualified_group_epoch_count,
            "rejected_mode_group_epochs": (
                group_epoch_count - qualified_group_epoch_count
            ),
            "mode_group_epoch_qualification_fraction": (
                qualified_group_epoch_count / group_epoch_count
                if group_epoch_count
                else None
            ),
            "loop_5g_fallback_mode_group_epochs": sum(
                int(epoch["loop_5g_fallback_mode_group_count"])
                for epoch in epochs
            ),
            "five_level_two_term_mode_group_epochs": sum(
                int(epoch["two_term_mode_group_count"]) for epoch in epochs
            ),
            "fit_attempted_mode_group_epochs": sum(
                bool(group["fit_attempted"]) for group in group_rows
            ),
            "mode_group_rejection_causes": dict(
                sorted(rejection_causes.items())
            ),
            "maximum_training_residual_ratio": max(
                training_ratios,
                default=None,
            ),
            "maximum_holdout_residual_ratio": max(
                holdout_ratios,
                default=None,
            ),
            "median_secondary_to_primary_contribution_ratio": _percentile(
                secondary_ratios,
                0.5,
            ),
            "p95_secondary_to_primary_contribution_ratio": _percentile(
                secondary_ratios,
                0.95,
            ),
            "reference_estimator_covered": reference_covered,
            "qualified_reference_estimator_coverage_fraction": (
                reference_covered / qualified_sample_count
                if qualified_sample_count
                else None
            ),
            "effective_reference_estimator_coverage_fraction": (
                reference_covered / eligible_sample_count
                if eligible_sample_count
                else None
            ),
            "babcs_total_covered": total_covered,
            "qualified_babcs_total_coverage_fraction": (
                total_covered / qualified_sample_count
                if qualified_sample_count
                else None
            ),
            "effective_babcs_total_coverage_fraction": (
                total_covered / eligible_sample_count
                if eligible_sample_count
                else None
            ),
            "median_uncertainty_to_finest_authority_error_ratio": _percentile(
                inflation_ratios,
                0.5,
            ),
            "p95_uncertainty_to_finest_authority_error_ratio": _percentile(
                inflation_ratios,
                0.95,
            ),
            "independent_policy_work_units": work_units,
            "per_mode_group": per_group,
            "epochs": epochs,
        }
        sweep[policy_id] = result
        if (
            result["sample_qualification_fraction"] is not None
            and result["median_uncertainty_to_finest_authority_error_ratio"]
            is not None
        ):
            candidates.append(result)
    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_two_term_modal(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["independent_policy_work_units"],
            row["median_uncertainty_to_finest_authority_error_ratio"],
            -row["effective_babcs_total_coverage_fraction"],
            row["policy_id"],
        )
    )
    return sweep, frontier


def _global_modal_epoch_sweep(
    record: dict[str, Any],
    eligible_samples: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    return _global_modal_epoch_sweep_impl(
        record,
        eligible_samples,
        temporal_alignment_enabled=False,
    )


def _global_temporally_aligned_modal_epoch_sweep(
    record: dict[str, Any],
    eligible_samples: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    return _global_modal_epoch_sweep_impl(
        record,
        eligible_samples,
        temporal_alignment_enabled=True,
    )


def _global_modal_epoch_sweep_impl(
    record: dict[str, Any],
    eligible_samples: list[dict[str, Any]],
    *,
    temporal_alignment_enabled: bool,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    metadata = record.get("global_dual_trajectory")
    if not isinstance(metadata, dict):
        return {}, []
    settings = metadata.get("statewise_four_level")
    basis = metadata.get("modal_basis")
    if not isinstance(settings, dict) or not isinstance(basis, dict):
        return {}, []
    epoch_fit = settings.get("epoch_fit")
    if (
        not isinstance(epoch_fit, dict)
        or not isinstance(epoch_fit.get("modal_fit"), dict)
        or not basis.get("qualified")
    ):
        return {}, []
    modal_fit = epoch_fit["modal_fit"]
    temporal_alignment = (
        modal_fit.get("temporal_alignment")
        if temporal_alignment_enabled
        else None
    )
    if temporal_alignment_enabled and not isinstance(temporal_alignment, dict):
        return {}, []

    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for sample in eligible_samples:
        grouped[int(sample["anchor_generation"])].append(sample)
    config = _config_from_record(record["configuration"])
    factor_metadata = metadata["factor_trajectories"]
    sweep: dict[str, dict[str, Any]] = {}
    candidates: list[dict[str, Any]] = []
    for quadruplet in settings["quadruplets"]:
        quadruplet_id = str(quadruplet["quadruplet_id"])
        epochs = [
            _modal_epoch_diagnostic(
                generation,
                rows,
                quadruplet,
                settings,
                epoch_fit,
                basis,
                config,
                temporal_alignment=temporal_alignment,
            )
            for generation, rows in sorted(grouped.items())
        ]
        qualified_epochs = [epoch for epoch in epochs if epoch["qualified"]]
        eligible_sample_count = sum(epoch["sample_count"] for epoch in epochs)
        qualified_sample_count = sum(
            epoch["sample_count"] for epoch in qualified_epochs
        )
        group_epoch_count = sum(epoch["mode_group_count"] for epoch in epochs)
        qualified_group_epoch_count = sum(
            epoch["qualified_mode_group_count"] for epoch in epochs
        )
        reference_covered = sum(
            epoch["reference_estimator_covered"] for epoch in qualified_epochs
        )
        total_covered = sum(
            epoch["babcs_total_covered"] for epoch in qualified_epochs
        )
        inflation_ratios = [
            ratio
            for epoch in qualified_epochs
            for ratio in epoch["uncertainty_to_finest_authority_error_ratios"]
        ]
        rejection_causes = Counter(
            str(group["rejection_cause"])
            for epoch in epochs
            for group in epoch["mode_groups"]
            if group["rejection_cause"] is not None
        )
        temporal_rejection_causes = Counter(
            str(group["temporal_alignment_rejection_cause"])
            for epoch in epochs
            for group in epoch["mode_groups"]
            if group["temporal_alignment_rejection_cause"] is not None
        )
        selected_lag_counts = Counter(
            ",".join(
                str(value)
                for value in group["selected_sequence_sample_lags"]
            )
            for epoch in epochs
            for group in epoch["mode_groups"]
            if group["temporal_alignment_applied"]
        )
        per_group: dict[str, dict[str, Any]] = {}
        for group_id in (
            str(group["group_id"])
            for group in basis["mode_groups"]
        ):
            rows = [
                group
                for epoch in epochs
                for group in epoch["mode_groups"]
                if group["group_id"] == group_id
            ]
            causes = Counter(
                str(group["rejection_cause"])
                for group in rows
                if group["rejection_cause"] is not None
            )
            temporal_causes = Counter(
                str(group["temporal_alignment_rejection_cause"])
                for group in rows
                if group["temporal_alignment_rejection_cause"] is not None
            )
            per_group[group_id] = {
                "epoch_count": len(rows),
                "qualified_epochs": sum(bool(group["qualified"]) for group in rows),
                "rejected_epochs": sum(not group["qualified"] for group in rows),
                "dimension": rows[0]["dimension"] if rows else 0,
                "eigenvalues": rows[0]["eigenvalues"] if rows else [],
                "coherent_zero_crossing_intervals": sum(
                    int(group["coherent_zero_crossing_interval_count"])
                    for group in rows
                ),
                "unmatched_sign_change_intervals": sum(
                    int(group["unmatched_sign_change_interval_count"])
                    for group in rows
                ),
                "temporal_alignment_attempted_epochs": sum(
                    bool(group["temporal_alignment_attempted"])
                    for group in rows
                ),
                "temporally_aligned_epochs": sum(
                    bool(group["temporal_alignment_applied"])
                    for group in rows
                ),
                "matched_zero_crossing_intervals": sum(
                    int(group["matched_zero_crossing_interval_count"])
                    for group in rows
                ),
                "discarded_endpoint_count": sum(
                    int(group["discarded_endpoint_count"])
                    for group in rows
                ),
                "rejection_causes": dict(sorted(causes.items())),
                "temporal_alignment_rejection_causes": dict(
                    sorted(temporal_causes.items())
                ),
            }
        factors = tuple(int(value) for value in quadruplet["refinement_factors"])
        work_units = sum(
            int(factor_metadata[str(factor)]["work"]["deterministic_work_units"])
            for factor in factors
        )
        result = {
            **quadruplet,
            "sampling_mode": metadata["sampling_mode"],
            "basis_sha256": basis["basis_sha256"],
            "basis_state_unit": basis["state_unit"],
            "mode_group_count": len(basis["mode_groups"]),
            "epoch_count": len(epochs),
            "qualified_epochs": len(qualified_epochs),
            "rejected_epochs": len(epochs) - len(qualified_epochs),
            "epoch_qualification_fraction": (
                len(qualified_epochs) / len(epochs) if epochs else None
            ),
            "eligible_samples": eligible_sample_count,
            "qualified_samples": qualified_sample_count,
            "rejected_samples": eligible_sample_count - qualified_sample_count,
            "sample_qualification_fraction": (
                qualified_sample_count / eligible_sample_count
                if eligible_sample_count
                else None
            ),
            "mode_group_epoch_count": group_epoch_count,
            "qualified_mode_group_epochs": qualified_group_epoch_count,
            "rejected_mode_group_epochs": (
                group_epoch_count - qualified_group_epoch_count
            ),
            "mode_group_epoch_qualification_fraction": (
                qualified_group_epoch_count / group_epoch_count
                if group_epoch_count
                else None
            ),
            "mode_group_rejection_causes": dict(sorted(rejection_causes.items())),
            "temporal_alignment_enabled": temporal_alignment_enabled,
            "temporal_alignment_maximum_sample_lag": (
                int(temporal_alignment["maximum_sample_lag"])
                if temporal_alignment is not None
                else None
            ),
            "temporal_alignment_attempted_mode_group_epochs": sum(
                int(epoch["temporal_alignment_attempted_mode_group_count"])
                for epoch in epochs
            ),
            "temporally_aligned_mode_group_epochs": sum(
                int(epoch["temporally_aligned_mode_group_count"])
                for epoch in epochs
            ),
            "temporal_alignment_failed_mode_group_epochs": sum(
                int(epoch["temporal_alignment_failed_mode_group_count"])
                for epoch in epochs
            ),
            "matched_zero_crossing_intervals": sum(
                int(epoch["matched_zero_crossing_interval_count"])
                for epoch in epochs
            ),
            "discarded_endpoint_count": sum(
                int(epoch["discarded_endpoint_count"])
                for epoch in epochs
            ),
            "selected_sequence_sample_lag_counts": dict(
                sorted(selected_lag_counts.items())
            ),
            "temporal_alignment_rejection_causes": dict(
                sorted(temporal_rejection_causes.items())
            ),
            "coherent_zero_crossing_intervals": sum(
                int(epoch["coherent_zero_crossing_interval_count"])
                for epoch in epochs
            ),
            "unmatched_sign_change_intervals": sum(
                int(epoch["unmatched_sign_change_interval_count"])
                for epoch in epochs
            ),
            "reference_estimator_covered": reference_covered,
            "qualified_reference_estimator_coverage_fraction": (
                reference_covered / qualified_sample_count
                if qualified_sample_count
                else None
            ),
            "effective_reference_estimator_coverage_fraction": (
                reference_covered / eligible_sample_count
                if eligible_sample_count
                else None
            ),
            "babcs_total_covered": total_covered,
            "qualified_babcs_total_coverage_fraction": (
                total_covered / qualified_sample_count
                if qualified_sample_count
                else None
            ),
            "effective_babcs_total_coverage_fraction": (
                total_covered / eligible_sample_count
                if eligible_sample_count
                else None
            ),
            "median_uncertainty_to_finest_authority_error_ratio": _percentile(
                inflation_ratios,
                0.5,
            ),
            "p95_uncertainty_to_finest_authority_error_ratio": _percentile(
                inflation_ratios,
                0.95,
            ),
            "independent_quadruplet_work_units": work_units,
            "per_mode_group": per_group,
            "epochs": epochs,
        }
        sweep[quadruplet_id] = result
        if (
            result["sample_qualification_fraction"] is not None
            and result["median_uncertainty_to_finest_authority_error_ratio"]
            is not None
        ):
            candidates.append(result)
    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_modal_epoch(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["independent_quadruplet_work_units"],
            row["median_uncertainty_to_finest_authority_error_ratio"],
            -row["effective_babcs_total_coverage_fraction"],
            row["quadruplet_id"],
        )
    )
    return sweep, frontier


def _modal_epoch_diagnostic(
    anchor_generation: int,
    samples: list[dict[str, Any]],
    quadruplet: dict[str, Any],
    settings: dict[str, Any],
    epoch_fit: dict[str, Any],
    basis: dict[str, Any],
    config: BABCSConfig,
    *,
    temporal_alignment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    quadruplet_id = str(quadruplet["quadruplet_id"])
    rows = [
        (sample, sample["global_statewise_four_level_diagnostics"].get(quadruplet_id))
        for sample in samples
    ]
    rows = [
        (sample, diagnostic)
        for sample, diagnostic in rows
        if isinstance(diagnostic, dict)
    ]
    if not rows:
        return {
            "anchor_generation": anchor_generation,
            "sample_count": 0,
            "mode_group_count": len(basis["mode_groups"]),
            "qualified_mode_group_count": 0,
            "qualified": False,
            "rejection_cause": "missing_statewise_samples",
            "coherent_zero_crossing_interval_count": 0,
            "unmatched_sign_change_interval_count": 0,
            "temporal_alignment_attempted_mode_group_count": 0,
            "temporally_aligned_mode_group_count": 0,
            "temporal_alignment_failed_mode_group_count": 0,
            "matched_zero_crossing_interval_count": 0,
            "discarded_endpoint_count": 0,
            "reference_estimator_covered": 0,
            "babcs_total_covered": 0,
            "uncertainty_to_finest_authority_error_ratios": [],
            "mode_groups": [],
            "sample_estimates": [],
        }

    basis_vectors = [list(map(float, row)) for row in basis["basis_vectors"]]
    mode_count = len(basis_vectors)
    modal_rows: list[dict[str, Any]] = []
    for sample, diagnostic in rows:
        states = diagnostic["states"]
        refinement_states = [
            [float(state["refinement_values"][level]) for state in states]
            for level in range(4)
        ]
        refinement_modes = [
            _modal_coordinates(values, basis_vectors)
            for values in refinement_states
        ]
        mode_scales = [
            config.absolute_tolerance
            + config.relative_tolerance
            * max(abs(refinement_modes[level][mode]) for level in range(4))
            for mode in range(mode_count)
        ]
        modal_rows.append(
            {
                "sample": sample,
                "diagnostic": diagnostic,
                "refinement_modes": refinement_modes,
                "mode_scales": mode_scales,
            }
        )

    mode_group_diagnostics = [
        _modal_epoch_group_diagnostic(
            quadruplet,
            settings,
            epoch_fit,
            group,
            modal_rows,
            temporal_alignment=temporal_alignment,
        )
        for group in basis["mode_groups"]
    ]
    qualified_groups = [
        group for group in mode_group_diagnostics if group["qualified"]
    ]
    qualified = len(qualified_groups) == len(mode_group_diagnostics)
    sample_estimates: list[dict[str, Any]] = []
    reference_covered = 0
    total_covered = 0
    inflation_ratios: list[float] = []
    if qualified:
        for sample_offset, row in enumerate(modal_rows):
            modal_estimates = [0.0] * mode_count
            for group in mode_group_diagnostics:
                for group_offset, mode in enumerate(group["mode_indices"]):
                    modal_estimates[mode] = group[
                        "estimated_finest_absolute_errors"
                    ][sample_offset][group_offset]
            state_estimates = [
                sum(
                    abs(basis_vectors[state][mode]) * modal_estimates[mode]
                    for mode in range(mode_count)
                )
                for state in range(mode_count)
            ]
            scales = [
                float(state["coverage_scale"])
                for state in row["diagnostic"]["states"]
            ]
            estimated_scaled_error = math.sqrt(
                sum(
                    (estimate / scale) ** 2
                    for estimate, scale in zip(state_estimates, scales, strict=True)
                )
                / mode_count
            )
            finest_error = float(
                row["diagnostic"]["finest_refined_epoch_authority_error"]
            )
            total_uncertainty = (
                float(row["sample"]["recursive_internal_bound"])
                + estimated_scaled_error
            )
            reference_sample_covered = finest_error <= estimated_scaled_error
            total_sample_covered = (
                float(row["sample"]["authority_epoch_drift_error"])
                <= total_uncertainty
            )
            reference_covered += reference_sample_covered
            total_covered += total_sample_covered
            ratio = (
                estimated_scaled_error / finest_error
                if finest_error > 0.0
                else None
            )
            if ratio is not None:
                inflation_ratios.append(ratio)
            sample_estimates.append(
                {
                    "sample_index": row["sample"]["sample_index"],
                    "time": row["sample"]["time"],
                    "estimated_scaled_finest_error": estimated_scaled_error,
                    "finest_refined_epoch_authority_error": finest_error,
                    "reference_estimator_covered": reference_sample_covered,
                    "total_uncertainty": total_uncertainty,
                    "total_uncertainty_covered": total_sample_covered,
                    "uncertainty_to_finest_authority_error_ratio": ratio,
                }
            )
    return {
        "anchor_generation": anchor_generation,
        "sample_count": len(modal_rows),
        "sample_indices": [row["sample"]["sample_index"] for row in modal_rows],
        "mode_group_count": len(mode_group_diagnostics),
        "qualified_mode_group_count": len(qualified_groups),
        "rejected_mode_group_count": (
            len(mode_group_diagnostics) - len(qualified_groups)
        ),
        "qualified": qualified,
        "rejection_cause": None if qualified else "mode_group_qualification_failed",
        "coherent_zero_crossing_interval_count": sum(
            int(group["coherent_zero_crossing_interval_count"])
            for group in mode_group_diagnostics
        ),
        "unmatched_sign_change_interval_count": sum(
            int(group["unmatched_sign_change_interval_count"])
            for group in mode_group_diagnostics
        ),
        "temporal_alignment_attempted_mode_group_count": sum(
            bool(group["temporal_alignment_attempted"])
            for group in mode_group_diagnostics
        ),
        "temporally_aligned_mode_group_count": sum(
            bool(group["temporal_alignment_applied"])
            for group in mode_group_diagnostics
        ),
        "temporal_alignment_failed_mode_group_count": sum(
            bool(group["temporal_alignment_attempted"])
            and not bool(group["temporal_alignment_applied"])
            for group in mode_group_diagnostics
        ),
        "matched_zero_crossing_interval_count": sum(
            int(group["matched_zero_crossing_interval_count"])
            for group in mode_group_diagnostics
        ),
        "discarded_endpoint_count": sum(
            int(group["discarded_endpoint_count"])
            for group in mode_group_diagnostics
        ),
        "reference_estimator_covered": reference_covered,
        "babcs_total_covered": total_covered,
        "uncertainty_to_finest_authority_error_ratios": inflation_ratios,
        "mode_groups": mode_group_diagnostics,
        "sample_estimates": sample_estimates,
    }


def _modal_epoch_group_diagnostic(
    quadruplet: dict[str, Any],
    settings: dict[str, Any],
    epoch_fit: dict[str, Any],
    group: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    temporal_alignment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mode_indices = [int(value) for value in group["mode_indices"]]
    dimension = len(mode_indices)
    diagnostic: dict[str, Any] = {
        "group_id": str(group["group_id"]),
        "mode_indices": mode_indices,
        "dimension": dimension,
        "eigenvalues": list(map(float, group["eigenvalues"])),
        "sample_count": len(rows),
        "qualified": False,
        "rejection_cause": None,
        "left_direction_cosine": None,
        "right_direction_cosine": None,
        "unshifted_left_direction_cosine": None,
        "unshifted_right_direction_cosine": None,
        "left_observed_order": None,
        "right_observed_order": None,
        "common_observed_order": None,
        "adjacent_order_difference": None,
        "coefficient_relative_difference": None,
        "extrapolant_residual_ratio": None,
        "sign_change_classification": (
            "scalar_mode" if dimension == 1 else "repeated_modal_subspace"
        ),
        "coherent_zero_crossing_interval_count": 0,
        "unmatched_sign_change_interval_count": 0,
        "qualification_source": None,
        "temporal_alignment_enabled": temporal_alignment is not None,
        "temporal_alignment_attempted": False,
        "temporal_alignment_applied": False,
        "temporal_alignment_maximum_sample_lag": (
            int(temporal_alignment["maximum_sample_lag"])
            if temporal_alignment is not None
            else None
        ),
        "selected_sequence_sample_lags": [0, 0, 0],
        "retained_direction_sample_count": len(rows) * dimension,
        "retained_direction_sample_ranges": [
            {"start": 0, "stop_exclusive": len(rows) * dimension}
            for _ in range(3)
        ],
        "discarded_endpoint_count": 0,
        "matched_zero_crossing_interval_count": 0,
        "discarded_zero_crossing_interval_count": 0,
        "temporal_alignment_candidate_count": 0,
        "temporal_alignment_rejection_cause": None,
        "estimated_finest_absolute_errors": None,
    }

    def reject(cause: str) -> dict[str, Any]:
        diagnostic["rejection_cause"] = cause
        return diagnostic

    if len(rows) < int(epoch_fit["minimum_epoch_samples"]):
        return reject("insufficient_epoch_samples")
    raw_sequences: list[list[float]] = [[], [], []]
    normalized_sequences: list[list[float]] = [[], [], []]
    physical_floors: list[float] = []
    refinement_values: list[list[list[float]]] = []
    for row in rows:
        sample_levels = [
            [row["refinement_modes"][level][mode] for mode in mode_indices]
            for level in range(4)
        ]
        refinement_values.append(sample_levels)
        for group_offset, mode in enumerate(mode_indices):
            scale = float(row["mode_scales"][mode])
            physical_floors.append(
                float(settings["scaled_difference_floor"]) * scale
            )
            differences = [
                sample_levels[pair][group_offset]
                - sample_levels[pair + 1][group_offset]
                for pair in range(3)
            ]
            for pair, difference in enumerate(differences):
                raw_sequences[pair].append(difference)
                normalized_sequences[pair].append(difference / scale)
    norms = [_vector_norm(sequence) for sequence in normalized_sequences]
    floor = float(settings["scaled_difference_floor"])
    epoch_floor = floor * math.sqrt(len(rows) * dimension)
    for pair_index, cause in enumerate(
        (
            "first_epoch_difference_at_or_below_floor",
            "second_epoch_difference_at_or_below_floor",
            "third_epoch_difference_at_or_below_floor",
        )
    ):
        if norms[pair_index] <= epoch_floor:
            return reject(cause)
    sign_change_rejected = False
    scalar_sequences: list[list[float]] | None = None
    if dimension == 1:
        scalar_sequences = [
            [sequence[sample] for sample in range(len(rows))]
            for sequence in normalized_sequences
        ]
        coherent, unmatched = _epoch_sign_change_counts(
            scalar_sequences,
            floor=floor,
        )
        diagnostic["coherent_zero_crossing_interval_count"] = coherent
        diagnostic["unmatched_sign_change_interval_count"] = unmatched
        sign_change_rejected = unmatched > int(
            epoch_fit["maximum_unmatched_sign_change_intervals"]
        )
    left_cosine = _vector_cosine(normalized_sequences[0], normalized_sequences[1])
    right_cosine = _vector_cosine(normalized_sequences[1], normalized_sequences[2])
    diagnostic["left_direction_cosine"] = left_cosine
    diagnostic["right_direction_cosine"] = right_cosine
    diagnostic["unshifted_left_direction_cosine"] = left_cosine
    diagnostic["unshifted_right_direction_cosine"] = right_cosine
    minimum_cosine = float(epoch_fit["minimum_pairwise_direction_cosine"])
    direction_rejection_cause = None
    if left_cosine < minimum_cosine:
        direction_rejection_cause = "left_direction_cosine_below_minimum"
    elif right_cosine < minimum_cosine:
        direction_rejection_cause = "right_direction_cosine_below_minimum"
    if sign_change_rejected or direction_rejection_cause is not None:
        baseline_cause = (
            "unmatched_sign_change_intervals_exceeded"
            if sign_change_rejected
            else direction_rejection_cause
        )
        if temporal_alignment is None:
            return reject(str(baseline_cause))
        diagnostic["temporal_alignment_attempted"] = True
        if scalar_sequences is None:
            diagnostic["temporal_alignment_rejection_cause"] = (
                "non_scalar_modal_group"
            )
            return reject(str(baseline_cause))
        alignment = _temporally_align_scalar_sequences(
            scalar_sequences,
            floor=floor,
            maximum_sample_lag=int(temporal_alignment["maximum_sample_lag"]),
            minimum_retained_samples=int(epoch_fit["minimum_epoch_samples"]),
        )
        diagnostic.update(
            {
                "selected_sequence_sample_lags": alignment[
                    "selected_sequence_sample_lags"
                ],
                "retained_direction_sample_count": alignment[
                    "retained_sample_count"
                ],
                "retained_direction_sample_ranges": alignment[
                    "retained_sample_ranges"
                ],
                "discarded_endpoint_count": alignment[
                    "discarded_endpoint_count"
                ],
                "matched_zero_crossing_interval_count": alignment[
                    "matched_zero_crossing_interval_count"
                ],
                "discarded_zero_crossing_interval_count": alignment[
                    "discarded_zero_crossing_interval_count"
                ],
                "temporal_alignment_candidate_count": alignment[
                    "candidate_count"
                ],
                "temporal_alignment_rejection_cause": alignment[
                    "rejection_cause"
                ],
            }
        )
        if not alignment["qualified"]:
            return reject(str(alignment["rejection_cause"]))
        left_cosine = float(alignment["left_direction_cosine"])
        right_cosine = float(alignment["right_direction_cosine"])
        diagnostic["left_direction_cosine"] = left_cosine
        diagnostic["right_direction_cosine"] = right_cosine
        if left_cosine < minimum_cosine:
            diagnostic["temporal_alignment_rejection_cause"] = (
                "aligned_left_direction_cosine_below_minimum"
            )
            return reject("aligned_left_direction_cosine_below_minimum")
        if right_cosine < minimum_cosine:
            diagnostic["temporal_alignment_rejection_cause"] = (
                "aligned_right_direction_cosine_below_minimum"
            )
            return reject("aligned_right_direction_cosine_below_minimum")
        diagnostic["temporal_alignment_applied"] = True
        diagnostic["temporal_alignment_rejection_cause"] = None

    ratio = float(quadruplet["refinement_ratio"])
    left_order = math.log(norms[0] / norms[1], ratio)
    right_order = math.log(norms[1] / norms[2], ratio)
    diagnostic["left_observed_order"] = left_order
    diagnostic["right_observed_order"] = right_order
    minimum_order = float(settings["minimum_observed_order"])
    maximum_order = float(settings["maximum_observed_order"])
    if left_order < minimum_order:
        return reject("left_observed_order_below_minimum")
    if left_order > maximum_order:
        return reject("left_observed_order_above_maximum")
    if right_order < minimum_order:
        return reject("right_observed_order_below_minimum")
    if right_order > maximum_order:
        return reject("right_observed_order_above_maximum")
    common_order = 0.5 * (left_order + right_order)
    order_difference = abs(left_order - right_order)
    diagnostic["common_observed_order"] = common_order
    diagnostic["adjacent_order_difference"] = order_difference
    if order_difference > float(settings["maximum_adjacent_order_difference"]):
        return reject("adjacent_order_difference_exceeded")

    factors = tuple(int(value) for value in quadruplet["refinement_factors"])
    coefficient_denominator = 1.0 - ratio ** (-common_order)
    richardson_denominator = ratio**common_order - 1.0
    if (
        coefficient_denominator <= sys.float_info.epsilon
        or richardson_denominator <= sys.float_info.epsilon
    ):
        return reject("richardson_denominator_at_or_below_floor")
    coefficient_vectors = [
        [
            difference * factors[pair] ** common_order
            / coefficient_denominator
            for difference in raw_sequences[pair]
        ]
        for pair in range(3)
    ]
    mean_coefficients = [
        sum(values) / 3.0
        for values in zip(*coefficient_vectors, strict=True)
    ]
    coefficient_residual = math.sqrt(
        sum(
            (value - mean_coefficients[index]) ** 2
            for vector in coefficient_vectors
            for index, value in enumerate(vector)
        )
        / (3 * len(mean_coefficients))
    )
    coefficient_scale = max(
        math.sqrt(
            sum(value * value for value in mean_coefficients)
            / len(mean_coefficients)
        ),
        max(physical_floors),
    )
    coefficient_difference = coefficient_residual / coefficient_scale
    diagnostic["coefficient_relative_difference"] = coefficient_difference
    if coefficient_difference > float(
        settings["maximum_coefficient_relative_difference"]
    ):
        return reject("coefficient_relative_difference_exceeded")

    level_two_errors = [
        difference / richardson_denominator for difference in raw_sequences[1]
    ]
    level_three_errors = [
        difference / richardson_denominator for difference in raw_sequences[2]
    ]
    level_two_values = [
        value
        for sample in refinement_values
        for value in sample[2]
    ]
    level_three_values = [
        value
        for sample in refinement_values
        for value in sample[3]
    ]
    residuals = [
        abs((left - left_error) - (right - right_error))
        for left, left_error, right, right_error in zip(
            level_two_values,
            level_two_errors,
            level_three_values,
            level_three_errors,
            strict=True,
        )
    ]
    residual_ratio = _vector_norm(residuals) / max(
        _vector_norm(level_three_errors),
        max(physical_floors),
    )
    diagnostic["extrapolant_residual_ratio"] = residual_ratio
    if residual_ratio > float(settings["maximum_extrapolant_residual_ratio"]):
        return reject("extrapolant_residual_ratio_exceeded")
    estimates = [
        abs(error) + residual
        for error, residual in zip(level_three_errors, residuals, strict=True)
    ]
    diagnostic.update(
        {
            "estimated_finest_absolute_errors": [
                estimates[index : index + dimension]
                for index in range(0, len(estimates), dimension)
            ],
            "qualification_source": (
                "temporally_aligned"
                if diagnostic["temporal_alignment_applied"]
                else "unshifted"
            ),
            "qualified": True,
        }
    )
    return diagnostic


def _temporally_align_scalar_sequences(
    sequences: list[list[float]],
    *,
    floor: float,
    maximum_sample_lag: int,
    minimum_retained_samples: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "qualified": False,
        "rejection_cause": None,
        "candidate_count": 0,
        "selected_sequence_sample_lags": [0, 0, 0],
        "retained_sample_count": 0,
        "retained_sample_ranges": [
            {"start": 0, "stop_exclusive": 0}
            for _ in range(3)
        ],
        "discarded_endpoint_count": 0,
        "matched_zero_crossing_interval_count": 0,
        "discarded_zero_crossing_interval_count": 0,
        "left_direction_cosine": None,
        "right_direction_cosine": None,
    }

    def reject(cause: str) -> dict[str, Any]:
        result["rejection_cause"] = cause
        return result

    if len(sequences) != 3:
        return reject("temporal_alignment_requires_three_sequences")
    sample_count = len(sequences[0])
    if sample_count < minimum_retained_samples:
        return reject("insufficient_temporal_alignment_samples")
    if any(len(sequence) != sample_count for sequence in sequences):
        return reject("temporal_alignment_sequence_length_mismatch")
    crossing_intervals = [
        _sign_change_intervals(sequence, floor=floor)
        for sequence in sequences
    ]
    if any(
        right - left <= maximum_sample_lag
        for intervals in crossing_intervals
        for left, right in zip(intervals, intervals[1:])
    ):
        return reject("temporal_alignment_sign_chatter_detected")
    if not all(crossing_intervals):
        return reject("temporal_alignment_missing_crossing_evidence")

    candidates: list[dict[str, Any]] = []
    for left_lag in range(-maximum_sample_lag, maximum_sample_lag + 1):
        for right_lag in range(-maximum_sample_lag, maximum_sample_lag + 1):
            lags = (left_lag, 0, right_lag)
            retained_start = max(0, *(-lag for lag in lags))
            retained_stop = min(
                sample_count,
                *(sample_count - lag for lag in lags),
            )
            retained_count = retained_stop - retained_start
            if retained_count < minimum_retained_samples:
                continue
            retained_crossings = [
                [
                    interval - lag
                    for interval in intervals
                    if retained_start <= interval - lag < retained_stop - 1
                ]
                for intervals, lag in zip(
                    crossing_intervals,
                    lags,
                    strict=True,
                )
            ]
            if (
                not retained_crossings[0]
                or retained_crossings[0] != retained_crossings[1]
                or retained_crossings[1] != retained_crossings[2]
            ):
                continue
            ranges = [
                {
                    "start": retained_start + lag,
                    "stop_exclusive": retained_stop + lag,
                }
                for lag in lags
            ]
            aligned_sequences = [
                sequence[span["start"] : span["stop_exclusive"]]
                for sequence, span in zip(sequences, ranges, strict=True)
            ]
            matched_crossings = len(retained_crossings[0])
            discarded_crossings = sum(
                len(intervals) - matched_crossings
                for intervals in crossing_intervals
            )
            candidates.append(
                {
                    "selected_sequence_sample_lags": list(lags),
                    "retained_sample_count": retained_count,
                    "retained_sample_ranges": ranges,
                    "discarded_endpoint_count": 3
                    * (sample_count - retained_count),
                    "matched_zero_crossing_interval_count": matched_crossings,
                    "discarded_zero_crossing_interval_count": discarded_crossings,
                    "left_direction_cosine": _vector_cosine(
                        aligned_sequences[0],
                        aligned_sequences[1],
                    ),
                    "right_direction_cosine": _vector_cosine(
                        aligned_sequences[1],
                        aligned_sequences[2],
                    ),
                }
            )
    result["candidate_count"] = len(candidates)
    if not candidates:
        return reject("temporal_alignment_crossing_match_failed")
    maximum_matches = max(
        int(candidate["matched_zero_crossing_interval_count"])
        for candidate in candidates
    )
    candidates = [
        candidate
        for candidate in candidates
        if candidate["matched_zero_crossing_interval_count"] == maximum_matches
    ]
    minimum_discarded = min(
        int(candidate["discarded_endpoint_count"])
        for candidate in candidates
    )
    candidates = [
        candidate
        for candidate in candidates
        if candidate["discarded_endpoint_count"] == minimum_discarded
    ]
    if len(candidates) != 1:
        return reject("temporal_alignment_ambiguous_crossing_match")
    result.update(candidates[0])
    result.update({"qualified": True, "rejection_cause": None})
    return result


def _sign_change_intervals(
    sequence: list[float],
    *,
    floor: float,
) -> list[int]:
    return [
        sample_index
        for sample_index in range(len(sequence) - 1)
        if _signed_interval_change(
            sequence[sample_index],
            sequence[sample_index + 1],
            floor=floor,
        )
    ]


def _modal_coordinates(
    state_values: list[float],
    basis_vectors: list[list[float]],
) -> list[float]:
    return [
        sum(
            basis_vectors[state][mode] * state_values[state]
            for state in range(len(state_values))
        )
        for mode in range(len(state_values))
    ]


def _statewise_epoch_diagnostic(
    anchor_generation: int,
    samples: list[dict[str, Any]],
    quadruplet: dict[str, Any],
    settings: dict[str, Any],
    epoch_fit: dict[str, Any],
) -> dict[str, Any]:
    quadruplet_id = str(quadruplet["quadruplet_id"])
    rows = [
        (sample, sample["global_statewise_four_level_diagnostics"].get(quadruplet_id))
        for sample in samples
    ]
    rows = [
        (sample, diagnostic)
        for sample, diagnostic in rows
        if isinstance(diagnostic, dict)
    ]
    if not rows:
        return {
            "anchor_generation": anchor_generation,
            "sample_count": 0,
            "state_count": 0,
            "qualified_state_count": 0,
            "qualified": False,
            "rejection_cause": "missing_statewise_samples",
            "coherent_zero_crossing_interval_count": 0,
            "unmatched_sign_change_interval_count": 0,
            "reference_estimator_covered": 0,
            "babcs_total_covered": 0,
            "uncertainty_to_finest_authority_error_ratios": [],
            "states": [],
            "sample_estimates": [],
        }
    state_count = int(rows[0][1]["state_count"])
    state_diagnostics = [
        _statewise_epoch_state_diagnostic(
            quadruplet,
            settings,
            epoch_fit,
            [diagnostic["states"][state_index] for _, diagnostic in rows],
        )
        for state_index in range(state_count)
    ]
    qualified_states = [state for state in state_diagnostics if state["qualified"]]
    qualified = len(qualified_states) == state_count
    rejection_cause = None if qualified else "state_epoch_qualification_failed"
    sample_estimates: list[dict[str, Any]] = []
    reference_covered = 0
    total_covered = 0
    inflation_ratios: list[float] = []
    if qualified:
        for sample_offset, (sample, diagnostic) in enumerate(rows):
            component_estimates = [
                state["estimated_finest_absolute_errors"][sample_offset]
                for state in state_diagnostics
            ]
            scales = [
                diagnostic["states"][state_index]["coverage_scale"]
                for state_index in range(state_count)
            ]
            estimated_scaled_error = math.sqrt(
                sum(
                    (estimate / scale) ** 2
                    for estimate, scale in zip(
                        component_estimates,
                        scales,
                        strict=True,
                    )
                )
                / state_count
            )
            finest_error = float(
                diagnostic["finest_refined_epoch_authority_error"]
            )
            total_uncertainty = (
                float(sample["recursive_internal_bound"]) + estimated_scaled_error
            )
            reference_sample_covered = finest_error <= estimated_scaled_error
            total_sample_covered = (
                float(sample["authority_epoch_drift_error"]) <= total_uncertainty
            )
            reference_covered += reference_sample_covered
            total_covered += total_sample_covered
            ratio = (
                estimated_scaled_error / finest_error
                if finest_error > 0.0
                else None
            )
            if ratio is not None:
                inflation_ratios.append(ratio)
            sample_estimates.append(
                {
                    "sample_index": sample["sample_index"],
                    "time": sample["time"],
                    "estimated_scaled_finest_error": estimated_scaled_error,
                    "finest_refined_epoch_authority_error": finest_error,
                    "reference_estimator_covered": reference_sample_covered,
                    "total_uncertainty": total_uncertainty,
                    "total_uncertainty_covered": total_sample_covered,
                    "uncertainty_to_finest_authority_error_ratio": ratio,
                }
            )
    return {
        "anchor_generation": anchor_generation,
        "sample_count": len(rows),
        "sample_indices": [sample["sample_index"] for sample, _ in rows],
        "state_count": state_count,
        "qualified_state_count": len(qualified_states),
        "rejected_state_count": state_count - len(qualified_states),
        "qualified": qualified,
        "rejection_cause": rejection_cause,
        "coherent_zero_crossing_interval_count": sum(
            int(state["coherent_zero_crossing_interval_count"])
            for state in state_diagnostics
        ),
        "unmatched_sign_change_interval_count": sum(
            int(state["unmatched_sign_change_interval_count"])
            for state in state_diagnostics
        ),
        "reference_estimator_covered": reference_covered,
        "babcs_total_covered": total_covered,
        "uncertainty_to_finest_authority_error_ratios": inflation_ratios,
        "states": state_diagnostics,
        "sample_estimates": sample_estimates,
    }


def _statewise_epoch_state_diagnostic(
    quadruplet: dict[str, Any],
    settings: dict[str, Any],
    epoch_fit: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    state_index = int(rows[0]["state_index"]) if rows else -1
    state_name = str(rows[0]["state_name"]) if rows else "unknown"
    diagnostic: dict[str, Any] = {
        "state_index": state_index,
        "state_name": state_name,
        "sample_count": len(rows),
        "qualified": False,
        "rejection_cause": None,
        "left_direction_cosine": None,
        "right_direction_cosine": None,
        "left_observed_order": None,
        "right_observed_order": None,
        "common_observed_order": None,
        "adjacent_order_difference": None,
        "coefficient_relative_difference": None,
        "extrapolant_residual_ratio": None,
        "coherent_zero_crossing_interval_count": 0,
        "unmatched_sign_change_interval_count": 0,
        "estimated_finest_absolute_errors": None,
        "component_reference_covered_count": 0,
    }

    def reject(cause: str) -> dict[str, Any]:
        diagnostic["rejection_cause"] = cause
        return diagnostic

    if len(rows) < int(epoch_fit["minimum_epoch_samples"]):
        return reject("insufficient_epoch_samples")
    normalized_sequences = [
        [float(row["normalized_signed_differences"][pair_index]) for row in rows]
        for pair_index in range(3)
    ]
    raw_sequences = [
        [float(row["signed_differences"][pair_index]) for row in rows]
        for pair_index in range(3)
    ]
    norms = [_vector_norm(sequence) for sequence in normalized_sequences]
    floor = float(settings["scaled_difference_floor"])
    epoch_floor = floor * math.sqrt(len(rows))
    for pair_index, cause in enumerate(
        (
            "first_epoch_difference_at_or_below_floor",
            "second_epoch_difference_at_or_below_floor",
            "third_epoch_difference_at_or_below_floor",
        )
    ):
        if norms[pair_index] <= epoch_floor:
            return reject(cause)
    coherent_crossings, unmatched_crossings = _epoch_sign_change_counts(
        normalized_sequences,
        floor=floor,
    )
    diagnostic["coherent_zero_crossing_interval_count"] = coherent_crossings
    diagnostic["unmatched_sign_change_interval_count"] = unmatched_crossings
    if unmatched_crossings > int(
        epoch_fit["maximum_unmatched_sign_change_intervals"]
    ):
        return reject("unmatched_sign_change_intervals_exceeded")
    left_cosine = _vector_cosine(
        normalized_sequences[0],
        normalized_sequences[1],
    )
    right_cosine = _vector_cosine(
        normalized_sequences[1],
        normalized_sequences[2],
    )
    diagnostic["left_direction_cosine"] = left_cosine
    diagnostic["right_direction_cosine"] = right_cosine
    minimum_cosine = float(epoch_fit["minimum_pairwise_direction_cosine"])
    if left_cosine < minimum_cosine:
        return reject("left_direction_cosine_below_minimum")
    if right_cosine < minimum_cosine:
        return reject("right_direction_cosine_below_minimum")

    ratio = float(quadruplet["refinement_ratio"])
    left_order = math.log(norms[0] / norms[1], ratio)
    right_order = math.log(norms[1] / norms[2], ratio)
    diagnostic["left_observed_order"] = left_order
    diagnostic["right_observed_order"] = right_order
    minimum_order = float(settings["minimum_observed_order"])
    maximum_order = float(settings["maximum_observed_order"])
    if left_order < minimum_order:
        return reject("left_observed_order_below_minimum")
    if left_order > maximum_order:
        return reject("left_observed_order_above_maximum")
    if right_order < minimum_order:
        return reject("right_observed_order_below_minimum")
    if right_order > maximum_order:
        return reject("right_observed_order_above_maximum")
    common_order = 0.5 * (left_order + right_order)
    order_difference = abs(left_order - right_order)
    diagnostic["common_observed_order"] = common_order
    diagnostic["adjacent_order_difference"] = order_difference
    if order_difference > float(settings["maximum_adjacent_order_difference"]):
        return reject("adjacent_order_difference_exceeded")

    factors = tuple(int(value) for value in quadruplet["refinement_factors"])
    coefficient_denominator = 1.0 - ratio ** (-common_order)
    richardson_denominator = ratio**common_order - 1.0
    if (
        coefficient_denominator <= sys.float_info.epsilon
        or richardson_denominator <= sys.float_info.epsilon
    ):
        return reject("richardson_denominator_at_or_below_floor")
    coefficient_vectors = [
        [
            difference * factors[pair_index] ** common_order
            / coefficient_denominator
            for difference in raw_sequences[pair_index]
        ]
        for pair_index in range(3)
    ]
    mean_coefficients = [
        sum(values) / 3.0
        for values in zip(*coefficient_vectors, strict=True)
    ]
    coefficient_residual = math.sqrt(
        sum(
            (value - mean_coefficients[sample_index]) ** 2
            for vector in coefficient_vectors
            for sample_index, value in enumerate(vector)
        )
        / (3 * len(rows))
    )
    coefficient_scale = max(
        math.sqrt(
            sum(value * value for value in mean_coefficients) / len(rows)
        ),
        max(float(row["physical_difference_floor"]) for row in rows),
    )
    coefficient_difference = coefficient_residual / coefficient_scale
    diagnostic["coefficient_relative_difference"] = coefficient_difference
    if coefficient_difference > float(
        settings["maximum_coefficient_relative_difference"]
    ):
        return reject("coefficient_relative_difference_exceeded")

    level_two_errors = [
        difference / richardson_denominator for difference in raw_sequences[1]
    ]
    level_three_errors = [
        difference / richardson_denominator for difference in raw_sequences[2]
    ]
    level_two_extrapolants = [
        float(row["refinement_values"][2]) - error
        for row, error in zip(rows, level_two_errors, strict=True)
    ]
    level_three_extrapolants = [
        float(row["refinement_values"][3]) - error
        for row, error in zip(rows, level_three_errors, strict=True)
    ]
    residuals = [
        abs(left - right)
        for left, right in zip(
            level_two_extrapolants,
            level_three_extrapolants,
            strict=True,
        )
    ]
    residual_ratio = _vector_norm(residuals) / max(
        _vector_norm(level_three_errors),
        max(float(row["physical_difference_floor"]) for row in rows),
    )
    diagnostic["extrapolant_residual_ratio"] = residual_ratio
    if residual_ratio > float(settings["maximum_extrapolant_residual_ratio"]):
        return reject("extrapolant_residual_ratio_exceeded")

    estimates = [
        abs(error) + residual
        for error, residual in zip(level_three_errors, residuals, strict=True)
    ]
    diagnostic.update(
        {
            "estimated_finest_absolute_errors": estimates,
            "component_reference_covered_count": sum(
                float(row["actual_finest_absolute_authority_error"]) <= estimate
                for row, estimate in zip(rows, estimates, strict=True)
            ),
            "qualified": True,
        }
    )
    return diagnostic


def _epoch_sign_change_counts(
    sequences: list[list[float]],
    *,
    floor: float,
) -> tuple[int, int]:
    coherent = 0
    unmatched = 0
    for sample_index in range(len(sequences[0]) - 1):
        changed = [
            _signed_interval_change(
                sequence[sample_index],
                sequence[sample_index + 1],
                floor=floor,
            )
            for sequence in sequences
        ]
        if all(changed):
            coherent += 1
        elif any(changed):
            unmatched += 1
    return coherent, unmatched


def _signed_interval_change(left: float, right: float, *, floor: float) -> bool:
    if abs(left) <= floor or abs(right) <= floor:
        return False
    return math.copysign(1.0, left) != math.copysign(1.0, right)


def _modal_basis_metadata(
    circuit: Circuit,
    evaluation,
    settings: dict[str, Any],
) -> dict[str, Any]:
    state_names = tuple(circuit.dynamic_names)
    metadata: dict[str, Any] = {
        "qualified": False,
        "rejection_cause": None,
        "state_count": len(state_names),
        "state_names": list(state_names),
        "state_unit": None,
        "matrix_infinity_norm": None,
        "symmetry_relative_error": None,
        "eigen_residual_relative_error": None,
        "orthogonality_error": None,
        "jacobi_sweeps": None,
        "eigenvalues": None,
        "basis_vectors": None,
        "mode_groups": [],
        "basis_sha256": None,
    }

    def reject(cause: str) -> dict[str, Any]:
        metadata["rejection_cause"] = cause
        return metadata

    if circuit.diodes:
        return reject("nonlinear_circuit")
    if circuit.switches:
        return reject("topology_changing_circuit")
    if not state_names:
        return reject("missing_dynamic_states")
    if circuit.capacitors and circuit.inductors:
        return reject("mixed_dynamic_units")
    if circuit.capacitors:
        metadata["state_unit"] = "voltage"
    elif circuit.inductors:
        metadata["state_unit"] = "current"
    else:
        return reject("unsupported_dynamic_state_kind")

    matrix = [
        [float(value) for value in row]
        for row in circuit.differential_jacobian_at_evaluation(evaluation)
    ]
    size = len(state_names)
    if len(matrix) != size or any(len(row) != size for row in matrix):
        return reject("differential_jacobian_shape_mismatch")
    if any(not math.isfinite(value) for row in matrix for value in row):
        return reject("nonfinite_differential_jacobian")
    matrix_norm = max(
        (sum(abs(value) for value in row) for row in matrix),
        default=0.0,
    )
    matrix_scale = max(matrix_norm, sys.float_info.min)
    symmetry_error = max(
        (
            abs(matrix[row][column] - matrix[column][row])
            for row in range(size)
            for column in range(row + 1, size)
        ),
        default=0.0,
    ) / matrix_scale
    metadata["matrix_infinity_norm"] = matrix_norm
    metadata["symmetry_relative_error"] = symmetry_error
    if symmetry_error > float(settings["maximum_symmetry_relative_error"]):
        return reject("differential_jacobian_not_symmetric")

    convergence_tolerance = max(
        64.0 * sys.float_info.epsilon,
        min(
            float(settings["maximum_eigen_residual_relative_error"]),
            float(settings["maximum_orthogonality_error"]),
        )
        * 0.01,
    )
    eigenvalues, basis_vectors, sweeps, converged = _symmetric_eigenbasis(
        matrix,
        maximum_sweeps=int(settings["maximum_jacobi_sweeps"]),
        relative_tolerance=convergence_tolerance,
    )
    metadata["jacobi_sweeps"] = sweeps
    if not converged:
        return reject("jacobi_eigendecomposition_not_converged")

    residual_error = max(
        (
            max(
                abs(
                    sum(matrix[row][column] * basis_vectors[column][mode]
                        for column in range(size))
                    - eigenvalues[mode] * basis_vectors[row][mode]
                )
                for row in range(size)
            )
            / max(matrix_scale, abs(eigenvalues[mode]))
            for mode in range(size)
        ),
        default=0.0,
    )
    orthogonality_error = max(
        (
            abs(
                sum(
                    basis_vectors[row][left] * basis_vectors[row][right]
                    for row in range(size)
                )
                - (1.0 if left == right else 0.0)
            )
            for left in range(size)
            for right in range(size)
        ),
        default=0.0,
    )
    metadata["eigen_residual_relative_error"] = residual_error
    metadata["orthogonality_error"] = orthogonality_error
    if residual_error > float(settings["maximum_eigen_residual_relative_error"]):
        return reject("eigen_residual_exceeds_limit")
    if orthogonality_error > float(settings["maximum_orthogonality_error"]):
        return reject("modal_basis_not_orthogonal")

    groups: list[list[int]] = []
    relative_tolerance = float(
        settings["repeated_eigenvalue_relative_tolerance"]
    )
    absolute_tolerance = float(
        settings["repeated_eigenvalue_absolute_tolerance"]
    )
    for mode, eigenvalue in enumerate(eigenvalues):
        if groups:
            previous = eigenvalues[groups[-1][-1]]
            repeated_limit = absolute_tolerance + relative_tolerance * max(
                abs(previous),
                abs(eigenvalue),
            )
        else:
            repeated_limit = -1.0
        if groups and abs(eigenvalue - previous) <= repeated_limit:
            groups[-1].append(mode)
        else:
            groups.append([mode])
    mode_groups = [
        {
            "group_id": f"mode-group-{index:03d}",
            "mode_indices": group,
            "dimension": len(group),
            "eigenvalues": [eigenvalues[mode] for mode in group],
        }
        for index, group in enumerate(groups)
    ]
    basis_payload = {
        "state_names": list(state_names),
        "eigenvalues": eigenvalues,
        "basis_vectors": basis_vectors,
        "mode_groups": mode_groups,
    }
    metadata.update(
        {
            "qualified": True,
            "eigenvalues": eigenvalues,
            "basis_vectors": basis_vectors,
            "mode_groups": mode_groups,
            "basis_sha256": hashlib.sha256(
                json.dumps(
                    basis_payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode()
            ).hexdigest(),
        }
    )
    return metadata


def _symmetric_eigenbasis(
    matrix: list[list[float]],
    *,
    maximum_sweeps: int,
    relative_tolerance: float,
) -> tuple[list[float], list[list[float]], int, bool]:
    size = len(matrix)
    values = [list(row) for row in matrix]
    vectors = [
        [1.0 if row == column else 0.0 for column in range(size)]
        for row in range(size)
    ]
    matrix_scale = max(
        (sum(abs(value) for value in row) for row in values),
        default=0.0,
    )
    tolerance = relative_tolerance * max(matrix_scale, sys.float_info.min)
    converged = size < 2
    completed_sweeps = 0
    for sweep in range(maximum_sweeps):
        completed_sweeps = sweep + 1
        for left in range(size - 1):
            for right in range(left + 1, size):
                off_diagonal = values[left][right]
                if abs(off_diagonal) <= tolerance:
                    continue
                angle = 0.5 * math.atan2(
                    2.0 * off_diagonal,
                    values[right][right] - values[left][left],
                )
                cosine = math.cos(angle)
                sine = math.sin(angle)
                left_diagonal = values[left][left]
                right_diagonal = values[right][right]
                for index in range(size):
                    if index in (left, right):
                        continue
                    index_left = values[index][left]
                    index_right = values[index][right]
                    values[index][left] = cosine * index_left - sine * index_right
                    values[left][index] = values[index][left]
                    values[index][right] = sine * index_left + cosine * index_right
                    values[right][index] = values[index][right]
                values[left][left] = (
                    cosine * cosine * left_diagonal
                    - 2.0 * sine * cosine * off_diagonal
                    + sine * sine * right_diagonal
                )
                values[right][right] = (
                    sine * sine * left_diagonal
                    + 2.0 * sine * cosine * off_diagonal
                    + cosine * cosine * right_diagonal
                )
                values[left][right] = 0.0
                values[right][left] = 0.0
                for index in range(size):
                    vector_left = vectors[index][left]
                    vector_right = vectors[index][right]
                    vectors[index][left] = cosine * vector_left - sine * vector_right
                    vectors[index][right] = sine * vector_left + cosine * vector_right
        maximum_off_diagonal = max(
            (
                abs(values[left][right])
                for left in range(size - 1)
                for right in range(left + 1, size)
            ),
            default=0.0,
        )
        if maximum_off_diagonal <= tolerance:
            converged = True
            break

    eigenpairs = [
        (values[mode][mode], [vectors[row][mode] for row in range(size)])
        for mode in range(size)
    ]
    eigenpairs.sort(key=lambda pair: pair[0])
    eigenvalues: list[float] = []
    sorted_vectors = [[0.0] * size for _ in range(size)]
    for mode, (eigenvalue, vector) in enumerate(eigenpairs):
        pivot = max(range(size), key=lambda index: abs(vector[index]), default=0)
        if vector and vector[pivot] < 0.0:
            vector = [-value for value in vector]
        eigenvalues.append(eigenvalue)
        for row, value in enumerate(vector):
            sorted_vectors[row][mode] = value
    return eigenvalues, sorted_vectors, completed_sweeps, converged


def _vector_norm(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values))


def _vector_cosine(left: list[float], right: list[float]) -> float:
    denominator = _vector_norm(left) * _vector_norm(right)
    if denominator <= sys.float_info.min:
        return -1.0
    return sum(
        left_value * right_value
        for left_value, right_value in zip(left, right, strict=True)
    ) / denominator


def _dominates_statewise_epoch(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    maximize = (
        "sample_qualification_fraction",
        "state_epoch_qualification_fraction",
        "effective_reference_estimator_coverage_fraction",
        "effective_babcs_total_coverage_fraction",
    )
    minimize = (
        "median_uncertainty_to_finest_authority_error_ratio",
        "independent_quadruplet_work_units",
    )
    no_worse = all(left[name] >= right[name] for name in maximize) and all(
        left[name] <= right[name] for name in minimize
    )
    strictly_better = any(left[name] > right[name] for name in maximize) or any(
        left[name] < right[name] for name in minimize
    )
    return no_worse and strictly_better


def _dominates_modal_epoch(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    maximize = (
        "sample_qualification_fraction",
        "mode_group_epoch_qualification_fraction",
        "effective_reference_estimator_coverage_fraction",
        "effective_babcs_total_coverage_fraction",
    )
    minimize = (
        "median_uncertainty_to_finest_authority_error_ratio",
        "independent_quadruplet_work_units",
    )
    no_worse = all(left[name] >= right[name] for name in maximize) and all(
        left[name] <= right[name] for name in minimize
    )
    strictly_better = any(left[name] > right[name] for name in maximize) or any(
        left[name] < right[name] for name in minimize
    )
    return no_worse and strictly_better


def _dominates_two_term_modal(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    maximize = (
        "sample_qualification_fraction",
        "mode_group_epoch_qualification_fraction",
        "effective_reference_estimator_coverage_fraction",
        "effective_babcs_total_coverage_fraction",
    )
    minimize = (
        "median_uncertainty_to_finest_authority_error_ratio",
        "independent_policy_work_units",
    )
    no_worse = all(left[name] >= right[name] for name in maximize) and all(
        left[name] <= right[name] for name in minimize
    )
    strictly_better = any(left[name] > right[name] for name in maximize) or any(
        left[name] < right[name] for name in minimize
    )
    return no_worse and strictly_better


def _dominates_statewise_quadruplet(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    maximize = (
        "sample_qualification_fraction",
        "state_qualification_fraction",
        "effective_reference_estimator_coverage_fraction",
        "effective_babcs_total_coverage_fraction",
    )
    minimize = (
        "median_uncertainty_to_finest_authority_error_ratio",
        "independent_quadruplet_work_units",
    )
    no_worse = all(left[name] >= right[name] for name in maximize) and all(
        left[name] <= right[name] for name in minimize
    )
    strictly_better = any(left[name] > right[name] for name in maximize) or any(
        left[name] < right[name] for name in minimize
    )
    return no_worse and strictly_better


def _dominates_order_aware_triplet(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    maximize = (
        "qualification_fraction",
        "effective_reference_estimator_coverage_fraction",
        "effective_babcs_total_coverage_fraction",
    )
    minimize = (
        "median_uncertainty_to_finest_authority_error_ratio",
        "independent_triplet_work_units",
    )
    no_worse = all(left[name] >= right[name] for name in maximize) and all(
        left[name] <= right[name] for name in minimize
    )
    strictly_better = any(left[name] > right[name] for name in maximize) or any(
        left[name] < right[name] for name in minimize
    )
    return no_worse and strictly_better


def _dominates_global_pair(left: dict[str, Any], right: dict[str, Any]) -> bool:
    no_worse = (
        left["babcs_total_coverage_fraction"]
        >= right["babcs_total_coverage_fraction"]
        and left["median_uncertainty_to_authority_error_ratio"]
        <= right["median_uncertainty_to_authority_error_ratio"]
        and left["independent_pair_work_units"]
        <= right["independent_pair_work_units"]
    )
    strictly_better = (
        left["babcs_total_coverage_fraction"]
        > right["babcs_total_coverage_fraction"]
        or left["median_uncertainty_to_authority_error_ratio"]
        < right["median_uncertainty_to_authority_error_ratio"]
        or left["independent_pair_work_units"]
        < right["independent_pair_work_units"]
    )
    return no_worse and strictly_better


def _global_common_policy_frontier(
    aggregates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    applicable = [
        aggregate
        for aggregate in aggregates
        if aggregate.get("global_refinement_pair_sweep")
    ]
    if not applicable:
        return []
    policy_keys: set[tuple[str, str]] | None = None
    for aggregate in applicable:
        available = {
            (pair_id, safety_factor)
            for pair_id, pair in aggregate["global_refinement_pair_sweep"].items()
            for safety_factor in pair["coverage_by_safety_factor"]
        }
        policy_keys = available if policy_keys is None else policy_keys & available
    candidates: list[dict[str, Any]] = []
    for pair_id, safety_factor_key in sorted(policy_keys or ()):
        rows = [
            aggregate["global_refinement_pair_sweep"][pair_id][
                "coverage_by_safety_factor"
            ][safety_factor_key]
            for aggregate in applicable
        ]
        pair = applicable[0]["global_refinement_pair_sweep"][pair_id]
        candidate = {
            "pair_id": pair_id,
            "coarse_refinement_factor": pair["coarse_refinement_factor"],
            "fine_refinement_factor": pair["fine_refinement_factor"],
            "safety_factor": rows[0]["safety_factor"],
            "case_count": len(rows),
            "minimum_babcs_total_coverage_fraction": min(
                row["babcs_total_coverage_fraction"] for row in rows
            ),
            "minimum_reference_estimator_coverage_fraction": min(
                row["reference_estimator_coverage_fraction"] for row in rows
            ),
            "maximum_median_uncertainty_to_authority_error_ratio": max(
                row["median_uncertainty_to_authority_error_ratio"] for row in rows
            ),
            "maximum_p95_uncertainty_to_authority_error_ratio": max(
                row["p95_uncertainty_to_authority_error_ratio"] for row in rows
            ),
            "maximum_independent_pair_work_units": max(
                row["independent_pair_work_units"] for row in rows
            ),
            "total_independent_pair_work_units": sum(
                row["independent_pair_work_units"] for row in rows
            ),
        }
        candidates.append(candidate)
    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_global_common_policy(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["maximum_independent_pair_work_units"],
            row["maximum_median_uncertainty_to_authority_error_ratio"],
            -row["minimum_babcs_total_coverage_fraction"],
            row["pair_id"],
            row["safety_factor"],
        )
    )
    return frontier


def _global_order_aware_common_policy_frontier(
    aggregates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    applicable = [
        aggregate
        for aggregate in aggregates
        if aggregate.get("global_order_aware_triplet_sweep")
    ]
    if not applicable:
        return []
    triplet_ids = set(applicable[0]["global_order_aware_triplet_sweep"])
    for aggregate in applicable[1:]:
        triplet_ids &= set(aggregate["global_order_aware_triplet_sweep"])
    candidates: list[dict[str, Any]] = []
    for triplet_id in sorted(triplet_ids):
        rows = [
            aggregate["global_order_aware_triplet_sweep"][triplet_id]
            for aggregate in applicable
        ]
        required = (
            "qualification_fraction",
            "effective_reference_estimator_coverage_fraction",
            "effective_babcs_total_coverage_fraction",
            "median_uncertainty_to_finest_authority_error_ratio",
            "p95_uncertainty_to_finest_authority_error_ratio",
        )
        if any(any(row[name] is None for name in required) for row in rows):
            continue
        triplet = rows[0]
        candidates.append(
            {
                "triplet_id": triplet_id,
                "coarse_refinement_factor": triplet["coarse_refinement_factor"],
                "middle_refinement_factor": triplet["middle_refinement_factor"],
                "fine_refinement_factor": triplet["fine_refinement_factor"],
                "case_count": len(rows),
                "minimum_qualification_fraction": min(
                    row["qualification_fraction"] for row in rows
                ),
                "minimum_effective_reference_estimator_coverage_fraction": min(
                    row["effective_reference_estimator_coverage_fraction"]
                    for row in rows
                ),
                "minimum_effective_babcs_total_coverage_fraction": min(
                    row["effective_babcs_total_coverage_fraction"] for row in rows
                ),
                "maximum_median_uncertainty_to_finest_authority_error_ratio": max(
                    row["median_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_p95_uncertainty_to_finest_authority_error_ratio": max(
                    row["p95_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_independent_triplet_work_units": max(
                    row["independent_triplet_work_units"] for row in rows
                ),
                "total_independent_triplet_work_units": sum(
                    row["independent_triplet_work_units"] for row in rows
                ),
            }
        )
    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_order_aware_common_policy(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["maximum_independent_triplet_work_units"],
            row["maximum_median_uncertainty_to_finest_authority_error_ratio"],
            -row["minimum_effective_babcs_total_coverage_fraction"],
            row["triplet_id"],
        )
    )
    return frontier


def _global_order_aware_epoch_common_policy_frontier(
    aggregates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    applicable = [
        aggregate
        for aggregate in aggregates
        if aggregate.get("global_order_aware_triplet_sweep")
    ]
    if not applicable:
        return []
    triplet_ids = set(applicable[0]["global_order_aware_triplet_sweep"])
    for aggregate in applicable[1:]:
        triplet_ids &= set(aggregate["global_order_aware_triplet_sweep"])
    candidates: list[dict[str, Any]] = []
    for triplet_id in sorted(triplet_ids):
        triplets = [
            aggregate["global_order_aware_triplet_sweep"][triplet_id]
            for aggregate in applicable
        ]
        rows = [triplet["epoch_qualified"] for triplet in triplets]
        required = (
            "sample_qualification_fraction",
            "effective_reference_estimator_coverage_fraction",
            "effective_babcs_total_coverage_fraction",
            "median_uncertainty_to_finest_authority_error_ratio",
            "p95_uncertainty_to_finest_authority_error_ratio",
        )
        if any(any(row[name] is None for name in required) for row in rows):
            continue
        triplet = triplets[0]
        candidates.append(
            {
                "triplet_id": triplet_id,
                "coarse_refinement_factor": triplet["coarse_refinement_factor"],
                "middle_refinement_factor": triplet["middle_refinement_factor"],
                "fine_refinement_factor": triplet["fine_refinement_factor"],
                "case_count": len(rows),
                "minimum_sample_qualification_fraction": min(
                    row["sample_qualification_fraction"] for row in rows
                ),
                "minimum_effective_reference_estimator_coverage_fraction": min(
                    row["effective_reference_estimator_coverage_fraction"]
                    for row in rows
                ),
                "minimum_effective_babcs_total_coverage_fraction": min(
                    row["effective_babcs_total_coverage_fraction"] for row in rows
                ),
                "maximum_median_uncertainty_to_finest_authority_error_ratio": max(
                    row["median_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_p95_uncertainty_to_finest_authority_error_ratio": max(
                    row["p95_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_independent_triplet_work_units": max(
                    triplet["independent_triplet_work_units"]
                    for triplet in triplets
                ),
                "total_independent_triplet_work_units": sum(
                    triplet["independent_triplet_work_units"]
                    for triplet in triplets
                ),
            }
        )
    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_order_aware_epoch_common_policy(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["maximum_independent_triplet_work_units"],
            row["maximum_median_uncertainty_to_finest_authority_error_ratio"],
            -row["minimum_effective_babcs_total_coverage_fraction"],
            row["triplet_id"],
        )
    )
    return frontier


def _global_order_aware_epoch_envelope_common_policy_frontier(
    aggregates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    applicable = [
        aggregate
        for aggregate in aggregates
        if aggregate.get("global_order_aware_triplet_sweep")
    ]
    if not applicable:
        return []
    triplet_ids = set(applicable[0]["global_order_aware_triplet_sweep"])
    for aggregate in applicable[1:]:
        triplet_ids &= set(aggregate["global_order_aware_triplet_sweep"])
    candidates: list[dict[str, Any]] = []
    for triplet_id in sorted(triplet_ids):
        triplets = [
            aggregate["global_order_aware_triplet_sweep"][triplet_id]
            for aggregate in applicable
        ]
        epoch_rows = [triplet["epoch_qualified"] for triplet in triplets]
        rows = [epoch["envelope"] for epoch in epoch_rows]
        required = (
            "effective_reference_estimator_coverage_fraction",
            "effective_babcs_total_coverage_fraction",
            "median_uncertainty_to_finest_authority_error_ratio",
            "p95_uncertainty_to_finest_authority_error_ratio",
        )
        if any(any(row[name] is None for name in required) for row in rows):
            continue
        triplet = triplets[0]
        candidates.append(
            {
                "triplet_id": triplet_id,
                "coarse_refinement_factor": triplet["coarse_refinement_factor"],
                "middle_refinement_factor": triplet["middle_refinement_factor"],
                "fine_refinement_factor": triplet["fine_refinement_factor"],
                "case_count": len(rows),
                "minimum_sample_qualification_fraction": min(
                    epoch["sample_qualification_fraction"] for epoch in epoch_rows
                ),
                "minimum_effective_reference_estimator_coverage_fraction": min(
                    row["effective_reference_estimator_coverage_fraction"]
                    for row in rows
                ),
                "minimum_effective_babcs_total_coverage_fraction": min(
                    row["effective_babcs_total_coverage_fraction"] for row in rows
                ),
                "maximum_median_uncertainty_to_finest_authority_error_ratio": max(
                    row["median_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_p95_uncertainty_to_finest_authority_error_ratio": max(
                    row["p95_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_independent_triplet_work_units": max(
                    triplet["independent_triplet_work_units"]
                    for triplet in triplets
                ),
                "total_independent_triplet_work_units": sum(
                    triplet["independent_triplet_work_units"]
                    for triplet in triplets
                ),
            }
        )
    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_order_aware_epoch_common_policy(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["maximum_independent_triplet_work_units"],
            row["maximum_median_uncertainty_to_finest_authority_error_ratio"],
            -row["minimum_effective_babcs_total_coverage_fraction"],
            row["triplet_id"],
        )
    )
    return frontier


def _dominates_order_aware_epoch_common_policy(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    maximize = (
        "minimum_sample_qualification_fraction",
        "minimum_effective_reference_estimator_coverage_fraction",
        "minimum_effective_babcs_total_coverage_fraction",
    )
    minimize = (
        "maximum_median_uncertainty_to_finest_authority_error_ratio",
        "maximum_p95_uncertainty_to_finest_authority_error_ratio",
        "maximum_independent_triplet_work_units",
        "total_independent_triplet_work_units",
    )
    no_worse = all(left[name] >= right[name] for name in maximize) and all(
        left[name] <= right[name] for name in minimize
    )
    strictly_better = any(left[name] > right[name] for name in maximize) or any(
        left[name] < right[name] for name in minimize
    )
    return no_worse and strictly_better


def _dominates_order_aware_common_policy(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    maximize = (
        "minimum_qualification_fraction",
        "minimum_effective_reference_estimator_coverage_fraction",
        "minimum_effective_babcs_total_coverage_fraction",
    )
    minimize = (
        "maximum_median_uncertainty_to_finest_authority_error_ratio",
        "maximum_p95_uncertainty_to_finest_authority_error_ratio",
        "maximum_independent_triplet_work_units",
        "total_independent_triplet_work_units",
    )
    no_worse = all(left[name] >= right[name] for name in maximize) and all(
        left[name] <= right[name] for name in minimize
    )
    strictly_better = any(left[name] > right[name] for name in maximize) or any(
        left[name] < right[name] for name in minimize
    )
    return no_worse and strictly_better


def _global_statewise_four_level_common_policy_frontier(
    aggregates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    applicable = [
        aggregate
        for aggregate in aggregates
        if aggregate.get("global_statewise_four_level_sweep")
    ]
    if not applicable:
        return []
    quadruplet_ids = set(applicable[0]["global_statewise_four_level_sweep"])
    for aggregate in applicable[1:]:
        quadruplet_ids &= set(aggregate["global_statewise_four_level_sweep"])
    candidates: list[dict[str, Any]] = []
    for quadruplet_id in sorted(quadruplet_ids):
        rows = [
            aggregate["global_statewise_four_level_sweep"][quadruplet_id]
            for aggregate in applicable
        ]
        required = (
            "sample_qualification_fraction",
            "state_qualification_fraction",
            "effective_reference_estimator_coverage_fraction",
            "effective_babcs_total_coverage_fraction",
            "median_uncertainty_to_finest_authority_error_ratio",
            "p95_uncertainty_to_finest_authority_error_ratio",
        )
        if any(any(row[name] is None for name in required) for row in rows):
            continue
        quadruplet = rows[0]
        candidates.append(
            {
                "quadruplet_id": quadruplet_id,
                "refinement_factors": quadruplet["refinement_factors"],
                "refinement_ratio": quadruplet["refinement_ratio"],
                "case_count": len(rows),
                "minimum_sample_qualification_fraction": min(
                    row["sample_qualification_fraction"] for row in rows
                ),
                "minimum_state_qualification_fraction": min(
                    row["state_qualification_fraction"] for row in rows
                ),
                "minimum_effective_reference_estimator_coverage_fraction": min(
                    row["effective_reference_estimator_coverage_fraction"]
                    for row in rows
                ),
                "minimum_effective_babcs_total_coverage_fraction": min(
                    row["effective_babcs_total_coverage_fraction"] for row in rows
                ),
                "maximum_median_uncertainty_to_finest_authority_error_ratio": max(
                    row["median_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_p95_uncertainty_to_finest_authority_error_ratio": max(
                    row["p95_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_independent_quadruplet_work_units": max(
                    row["independent_quadruplet_work_units"] for row in rows
                ),
                "total_independent_quadruplet_work_units": sum(
                    row["independent_quadruplet_work_units"] for row in rows
                ),
            }
        )
    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_statewise_common_policy(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["maximum_independent_quadruplet_work_units"],
            row["maximum_median_uncertainty_to_finest_authority_error_ratio"],
            -row["minimum_effective_babcs_total_coverage_fraction"],
            row["quadruplet_id"],
        )
    )
    return frontier


def _global_statewise_epoch_common_policy_frontier(
    aggregates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    applicable = [
        aggregate
        for aggregate in aggregates
        if aggregate.get("global_statewise_epoch_sweep")
    ]
    if not applicable:
        return []
    quadruplet_ids = set(applicable[0]["global_statewise_epoch_sweep"])
    for aggregate in applicable[1:]:
        quadruplet_ids &= set(aggregate["global_statewise_epoch_sweep"])
    candidates: list[dict[str, Any]] = []
    for quadruplet_id in sorted(quadruplet_ids):
        rows = [
            aggregate["global_statewise_epoch_sweep"][quadruplet_id]
            for aggregate in applicable
        ]
        required = (
            "sample_qualification_fraction",
            "state_epoch_qualification_fraction",
            "effective_reference_estimator_coverage_fraction",
            "effective_babcs_total_coverage_fraction",
            "median_uncertainty_to_finest_authority_error_ratio",
            "p95_uncertainty_to_finest_authority_error_ratio",
        )
        if any(any(row[name] is None for name in required) for row in rows):
            continue
        quadruplet = rows[0]
        candidates.append(
            {
                "quadruplet_id": quadruplet_id,
                "refinement_factors": quadruplet["refinement_factors"],
                "refinement_ratio": quadruplet["refinement_ratio"],
                "sampling_mode": quadruplet["sampling_mode"],
                "case_count": len(rows),
                "minimum_sample_qualification_fraction": min(
                    row["sample_qualification_fraction"] for row in rows
                ),
                "minimum_state_epoch_qualification_fraction": min(
                    row["state_epoch_qualification_fraction"] for row in rows
                ),
                "minimum_effective_reference_estimator_coverage_fraction": min(
                    row["effective_reference_estimator_coverage_fraction"]
                    for row in rows
                ),
                "minimum_effective_babcs_total_coverage_fraction": min(
                    row["effective_babcs_total_coverage_fraction"] for row in rows
                ),
                "maximum_median_uncertainty_to_finest_authority_error_ratio": max(
                    row["median_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_p95_uncertainty_to_finest_authority_error_ratio": max(
                    row["p95_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_independent_quadruplet_work_units": max(
                    row["independent_quadruplet_work_units"] for row in rows
                ),
                "total_independent_quadruplet_work_units": sum(
                    row["independent_quadruplet_work_units"] for row in rows
                ),
            }
        )
    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_statewise_epoch_common_policy(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["maximum_independent_quadruplet_work_units"],
            row["maximum_median_uncertainty_to_finest_authority_error_ratio"],
            -row["minimum_effective_babcs_total_coverage_fraction"],
            row["quadruplet_id"],
        )
    )
    return frontier


def _dominates_statewise_epoch_common_policy(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    maximize = (
        "minimum_sample_qualification_fraction",
        "minimum_state_epoch_qualification_fraction",
        "minimum_effective_reference_estimator_coverage_fraction",
        "minimum_effective_babcs_total_coverage_fraction",
    )
    minimize = (
        "maximum_median_uncertainty_to_finest_authority_error_ratio",
        "maximum_p95_uncertainty_to_finest_authority_error_ratio",
        "maximum_independent_quadruplet_work_units",
        "total_independent_quadruplet_work_units",
    )
    no_worse = all(left[name] >= right[name] for name in maximize) and all(
        left[name] <= right[name] for name in minimize
    )
    strictly_better = any(left[name] > right[name] for name in maximize) or any(
        left[name] < right[name] for name in minimize
    )
    return no_worse and strictly_better


def _global_two_term_modal_common_policy_frontier(
    aggregates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    applicable = [
        aggregate
        for aggregate in aggregates
        if aggregate.get("global_two_term_modal_sweep")
    ]
    if not applicable:
        return []
    policy_ids = set(applicable[0]["global_two_term_modal_sweep"])
    for aggregate in applicable[1:]:
        policy_ids &= set(aggregate["global_two_term_modal_sweep"])
    candidates: list[dict[str, Any]] = []
    for policy_id in sorted(policy_ids):
        rows = [
            aggregate["global_two_term_modal_sweep"][policy_id]
            for aggregate in applicable
        ]
        required = (
            "sample_qualification_fraction",
            "mode_group_epoch_qualification_fraction",
            "effective_reference_estimator_coverage_fraction",
            "effective_babcs_total_coverage_fraction",
            "median_uncertainty_to_finest_authority_error_ratio",
            "p95_uncertainty_to_finest_authority_error_ratio",
        )
        if any(any(row[name] is None for name in required) for row in rows):
            continue
        policy = rows[0]
        training_ratios = [
            float(row["maximum_training_residual_ratio"])
            for row in rows
            if row["maximum_training_residual_ratio"] is not None
        ]
        holdout_ratios = [
            float(row["maximum_holdout_residual_ratio"])
            for row in rows
            if row["maximum_holdout_residual_ratio"] is not None
        ]
        candidates.append(
            {
                "policy_id": policy_id,
                "primary_order": policy["primary_order"],
                "secondary_order": policy["secondary_order"],
                "training_refinement_factors": policy[
                    "training_refinement_factors"
                ],
                "holdout_refinement_factor": policy[
                    "holdout_refinement_factor"
                ],
                "case_count": len(rows),
                "minimum_sample_qualification_fraction": min(
                    row["sample_qualification_fraction"] for row in rows
                ),
                "minimum_mode_group_epoch_qualification_fraction": min(
                    row["mode_group_epoch_qualification_fraction"]
                    for row in rows
                ),
                "minimum_effective_reference_estimator_coverage_fraction": min(
                    row["effective_reference_estimator_coverage_fraction"]
                    for row in rows
                ),
                "minimum_effective_babcs_total_coverage_fraction": min(
                    row["effective_babcs_total_coverage_fraction"]
                    for row in rows
                ),
                "maximum_median_uncertainty_to_finest_authority_error_ratio": max(
                    row["median_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_p95_uncertainty_to_finest_authority_error_ratio": max(
                    row["p95_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_training_residual_ratio": max(
                    training_ratios,
                    default=None,
                ),
                "maximum_holdout_residual_ratio": max(
                    holdout_ratios,
                    default=None,
                ),
                "maximum_design_condition_number": max(
                    row["design_condition_number"] for row in rows
                ),
                "maximum_independent_policy_work_units": max(
                    row["independent_policy_work_units"] for row in rows
                ),
                "total_independent_policy_work_units": sum(
                    row["independent_policy_work_units"] for row in rows
                ),
            }
        )
    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_two_term_modal_common_policy(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["maximum_independent_policy_work_units"],
            row["maximum_median_uncertainty_to_finest_authority_error_ratio"],
            -row["minimum_effective_babcs_total_coverage_fraction"],
            row["policy_id"],
        )
    )
    return frontier


def _dominates_two_term_modal_common_policy(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    maximize = (
        "minimum_sample_qualification_fraction",
        "minimum_mode_group_epoch_qualification_fraction",
        "minimum_effective_reference_estimator_coverage_fraction",
        "minimum_effective_babcs_total_coverage_fraction",
    )
    minimize = (
        "maximum_median_uncertainty_to_finest_authority_error_ratio",
        "maximum_p95_uncertainty_to_finest_authority_error_ratio",
        "maximum_independent_policy_work_units",
        "total_independent_policy_work_units",
    )
    no_worse = all(left[name] >= right[name] for name in maximize) and all(
        left[name] <= right[name] for name in minimize
    )
    strictly_better = any(left[name] > right[name] for name in maximize) or any(
        left[name] < right[name] for name in minimize
    )
    return no_worse and strictly_better


def _global_modal_epoch_common_policy_frontier(
    aggregates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return _global_modal_epoch_common_policy_frontier_for(
        aggregates,
        sweep_key="global_modal_epoch_sweep",
    )


def _global_temporally_aligned_modal_epoch_common_policy_frontier(
    aggregates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return _global_modal_epoch_common_policy_frontier_for(
        aggregates,
        sweep_key="global_temporally_aligned_modal_epoch_sweep",
    )


def _global_modal_epoch_common_policy_frontier_for(
    aggregates: list[dict[str, Any]],
    *,
    sweep_key: str,
) -> list[dict[str, Any]]:
    applicable = [
        aggregate
        for aggregate in aggregates
        if aggregate.get(sweep_key)
    ]
    if not applicable:
        return []
    quadruplet_ids = set(applicable[0][sweep_key])
    for aggregate in applicable[1:]:
        quadruplet_ids &= set(aggregate[sweep_key])
    candidates: list[dict[str, Any]] = []
    for quadruplet_id in sorted(quadruplet_ids):
        rows = [
            aggregate[sweep_key][quadruplet_id]
            for aggregate in applicable
        ]
        required = (
            "sample_qualification_fraction",
            "mode_group_epoch_qualification_fraction",
            "effective_reference_estimator_coverage_fraction",
            "effective_babcs_total_coverage_fraction",
            "median_uncertainty_to_finest_authority_error_ratio",
            "p95_uncertainty_to_finest_authority_error_ratio",
        )
        if any(any(row[name] is None for name in required) for row in rows):
            continue
        quadruplet = rows[0]
        candidates.append(
            {
                "quadruplet_id": quadruplet_id,
                "refinement_factors": quadruplet["refinement_factors"],
                "refinement_ratio": quadruplet["refinement_ratio"],
                "sampling_mode": quadruplet["sampling_mode"],
                "case_count": len(rows),
                "minimum_sample_qualification_fraction": min(
                    row["sample_qualification_fraction"] for row in rows
                ),
                "minimum_mode_group_epoch_qualification_fraction": min(
                    row["mode_group_epoch_qualification_fraction"] for row in rows
                ),
                "minimum_effective_reference_estimator_coverage_fraction": min(
                    row["effective_reference_estimator_coverage_fraction"]
                    for row in rows
                ),
                "minimum_effective_babcs_total_coverage_fraction": min(
                    row["effective_babcs_total_coverage_fraction"] for row in rows
                ),
                "maximum_median_uncertainty_to_finest_authority_error_ratio": max(
                    row["median_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_p95_uncertainty_to_finest_authority_error_ratio": max(
                    row["p95_uncertainty_to_finest_authority_error_ratio"]
                    for row in rows
                ),
                "maximum_independent_quadruplet_work_units": max(
                    row["independent_quadruplet_work_units"] for row in rows
                ),
                "total_independent_quadruplet_work_units": sum(
                    row["independent_quadruplet_work_units"] for row in rows
                ),
            }
        )
    frontier = [
        candidate
        for candidate in candidates
        if not any(
            _dominates_modal_epoch_common_policy(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    frontier.sort(
        key=lambda row: (
            row["maximum_independent_quadruplet_work_units"],
            row["maximum_median_uncertainty_to_finest_authority_error_ratio"],
            -row["minimum_effective_babcs_total_coverage_fraction"],
            row["quadruplet_id"],
        )
    )
    return frontier


def _dominates_modal_epoch_common_policy(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    maximize = (
        "minimum_sample_qualification_fraction",
        "minimum_mode_group_epoch_qualification_fraction",
        "minimum_effective_reference_estimator_coverage_fraction",
        "minimum_effective_babcs_total_coverage_fraction",
    )
    minimize = (
        "maximum_median_uncertainty_to_finest_authority_error_ratio",
        "maximum_p95_uncertainty_to_finest_authority_error_ratio",
        "maximum_independent_quadruplet_work_units",
        "total_independent_quadruplet_work_units",
    )
    no_worse = all(left[name] >= right[name] for name in maximize) and all(
        left[name] <= right[name] for name in minimize
    )
    strictly_better = any(left[name] > right[name] for name in maximize) or any(
        left[name] < right[name] for name in minimize
    )
    return no_worse and strictly_better


def _dominates_statewise_common_policy(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    maximize = (
        "minimum_sample_qualification_fraction",
        "minimum_state_qualification_fraction",
        "minimum_effective_reference_estimator_coverage_fraction",
        "minimum_effective_babcs_total_coverage_fraction",
    )
    minimize = (
        "maximum_median_uncertainty_to_finest_authority_error_ratio",
        "maximum_p95_uncertainty_to_finest_authority_error_ratio",
        "maximum_independent_quadruplet_work_units",
        "total_independent_quadruplet_work_units",
    )
    no_worse = all(left[name] >= right[name] for name in maximize) and all(
        left[name] <= right[name] for name in minimize
    )
    strictly_better = any(left[name] > right[name] for name in maximize) or any(
        left[name] < right[name] for name in minimize
    )
    return no_worse and strictly_better


def _dominates_global_common_policy(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    maximize = (
        "minimum_babcs_total_coverage_fraction",
        "minimum_reference_estimator_coverage_fraction",
    )
    minimize = (
        "maximum_median_uncertainty_to_authority_error_ratio",
        "maximum_p95_uncertainty_to_authority_error_ratio",
        "maximum_independent_pair_work_units",
        "total_independent_pair_work_units",
    )
    no_worse = all(left[name] >= right[name] for name in maximize) and all(
        left[name] <= right[name] for name in minimize
    )
    strictly_better = any(left[name] > right[name] for name in maximize) or any(
        left[name] < right[name] for name in minimize
    )
    return no_worse and strictly_better


def _aggregate_row(
    record: dict[str, Any],
    samples: list[dict[str, Any]],
    anchors: list[dict[str, Any]],
    causes: list[dict[str, Any]],
) -> dict[str, Any]:
    eligible = [sample for sample in samples if sample["coverage_eligible"]]
    global_pair_sweep, global_pair_frontier = _global_refinement_pair_sweep(
        record,
        eligible,
    )
    global_order_sweep, global_order_frontier = _global_order_aware_triplet_sweep(
        record,
        eligible,
    )
    global_statewise_sweep, global_statewise_frontier = (
        _global_statewise_four_level_sweep(
            record,
            eligible,
        )
    )
    global_statewise_epoch_sweep, global_statewise_epoch_frontier = (
        _global_statewise_epoch_sweep(
            record,
            eligible,
        )
    )
    global_two_term_modal_sweep, global_two_term_modal_frontier = (
        _global_two_term_modal_sweep(
            record,
            eligible,
        )
    )
    global_modal_epoch_sweep, global_modal_epoch_frontier = (
        _global_modal_epoch_sweep(
            record,
            eligible,
        )
    )
    (
        global_temporally_aligned_modal_epoch_sweep,
        global_temporally_aligned_modal_epoch_frontier,
    ) = _global_temporally_aligned_modal_epoch_sweep(
        record,
        eligible,
    )
    global_eligible = [
        sample
        for sample in eligible
        if sample["global_reference_epoch_discrepancy"] is not None
        and sample["global_refined_epoch_authority_error"] is not None
    ]
    global_metadata = record.get("global_dual_trajectory")
    global_safety_factors = (
        ()
        if not isinstance(global_metadata, dict)
        else tuple(float(value) for value in global_metadata["safety_factors"])
    )
    global_discrepancies = [
        float(sample["global_reference_epoch_discrepancy"])
        for sample in global_eligible
    ]
    global_inflation_ratios = [
        sample["global_reference_epoch_discrepancy"]
        / sample["authority_epoch_drift_error"]
        for sample in global_eligible
        if sample["authority_epoch_drift_error"] > 0.0
    ]
    global_coverage_by_safety_factor: dict[str, dict[str, Any]] = {}
    for safety_factor in global_safety_factors:
        estimator_covered = sum(
            sample["global_refined_epoch_authority_error"]
            <= safety_factor * sample["global_reference_epoch_discrepancy"]
            for sample in global_eligible
        )
        total_covered = sum(
            sample["authority_epoch_drift_error"]
            <= sample["recursive_internal_bound"]
            + safety_factor * sample["global_reference_epoch_discrepancy"]
            for sample in global_eligible
        )
        global_coverage_by_safety_factor[format(safety_factor, ".17g")] = {
            "safety_factor": safety_factor,
            "eligible": len(global_eligible),
            "reference_estimator_covered": estimator_covered,
            "reference_estimator_coverage_fraction": (
                estimator_covered / len(global_eligible) if global_eligible else None
            ),
            "babcs_total_covered": total_covered,
            "babcs_total_coverage_fraction": (
                total_covered / len(global_eligible) if global_eligible else None
            ),
            "maximum_added_uncertainty": max(
                (
                    safety_factor * sample["global_reference_epoch_discrepancy"]
                    for sample in global_eligible
                ),
                default=0.0,
            ),
            "median_added_uncertainty": (
                safety_factor * _percentile(global_discrepancies, 0.5)
                if global_discrepancies
                else None
            ),
            "p95_added_uncertainty": (
                safety_factor * _percentile(global_discrepancies, 0.95)
                if global_discrepancies
                else None
            ),
            "median_uncertainty_to_authority_error_ratio": (
                safety_factor * _percentile(global_inflation_ratios, 0.5)
                if global_inflation_ratios
                else None
            ),
            "p95_uncertainty_to_authority_error_ratio": (
                safety_factor * _percentile(global_inflation_ratios, 0.95)
                if global_inflation_ratios
                else None
            ),
            "maximum_total_uncertainty": max(
                (
                    sample["recursive_internal_bound"]
                    + safety_factor * sample["global_reference_epoch_discrepancy"]
                    for sample in global_eligible
                ),
                default=0.0,
            ),
        }
    ratios = [sample["error_to_bound_ratio"] for sample in eligible]
    total_covered_count = sum(
        bool(sample["total_uncertainty_covered"]) for sample in eligible
    )
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
    transfer_counts: Counter[str] = Counter()
    transfer_covered: Counter[str] = Counter()
    for sample in eligible:
        transfer = str(sample["authority_transfer_kind"])
        transfer_counts[transfer] += 1
        transfer_covered[transfer] += int(bool(sample["covered"]))
    phase_values = [sample["phase_error_radians"] for sample in samples if sample["phase_error_radians"] is not None]
    return {
        "row_id": record["row_id"],
        "case_id": record["case_id"],
        "method": record["method"],
        "work": record["work"],
        "global_dual_trajectory": global_metadata,
        "accepted_sample_count": len(samples),
        "coverage_eligible_count": len(eligible),
        "covered_count": sum(bool(sample["covered"]) for sample in eligible),
        "empirical_coverage_fraction": (
            sum(bool(sample["covered"]) for sample in eligible) / len(eligible)
            if eligible
            else None
        ),
        "total_uncertainty_covered_count": total_covered_count,
        "empirical_total_uncertainty_coverage_fraction": (
            total_covered_count / len(eligible) if eligible else None
        ),
        "median_error_to_bound_ratio": _percentile(ratios, 0.5),
        "p95_error_to_bound_ratio": _percentile(ratios, 0.95),
        "maximum_error_to_bound_ratio": max(ratios, default=None),
        "maximum_consecutive_uncovered_samples": maximum_uncovered_run,
        "maximum_uncovered_authority_gap": max(
            (
                sample["uncovered_authority_gap"]
                for sample in eligible
                if sample["uncovered_authority_gap"] is not None
            ),
            default=0.0,
        ),
        "maximum_actual_authority_error": max(
            (sample["actual_authority_error"] for sample in samples),
            default=0.0,
        ),
        "maximum_recursive_internal_bound": max(
            (sample["recursive_internal_bound"] for sample in samples),
            default=0.0,
        ),
        "maximum_propagated_prior_bound": max(
            (sample["propagated_prior_bound"] for sample in samples),
            default=0.0,
        ),
        "maximum_pre_reset_local_defect": max(
            (sample["pre_reset_local_defect"] for sample in samples),
            default=0.0,
        ),
        "maximum_embedded_defect": max(
            (sample["embedded_defect"] for sample in samples),
            default=0.0,
        ),
        "maximum_corrected_reference_defect": max(
            (sample["corrected_reference_defect"] for sample in samples),
            default=0.0,
        ),
        "maximum_residual_defect": max(
            (sample["residual_defect"] for sample in samples),
            default=0.0,
        ),
        "maximum_reference_discretization_defect": max(
            (sample["reference_discretization_defect"] for sample in samples),
            default=0.0,
        ),
        "maximum_reference_uncertainty": max(
            (sample["reference_uncertainty"] for sample in samples),
            default=0.0,
        ),
        "maximum_total_estimated_uncertainty": max(
            (sample["total_estimated_uncertainty"] for sample in samples),
            default=0.0,
        ),
        "reference_refinement_solve_count": sum(
            sample["reference_refinement_solve_count"] for sample in samples
        ),
        "maximum_global_reference_epoch_discrepancy": max(
            (
                sample["global_reference_epoch_discrepancy"]
                for sample in samples
                if sample["global_reference_epoch_discrepancy"] is not None
            ),
            default=None,
        ),
        "maximum_global_refined_epoch_authority_error": max(
            (
                sample["global_refined_epoch_authority_error"]
                for sample in samples
                if sample["global_refined_epoch_authority_error"] is not None
            ),
            default=None,
        ),
        "median_global_reference_epoch_discrepancy": _percentile(
            global_discrepancies,
            0.5,
        ),
        "p95_global_reference_epoch_discrepancy": _percentile(
            global_discrepancies,
            0.95,
        ),
        "median_global_uncertainty_to_authority_error_ratio": _percentile(
            global_inflation_ratios,
            0.5,
        ),
        "p95_global_uncertainty_to_authority_error_ratio": _percentile(
            global_inflation_ratios,
            0.95,
        ),
        "global_reference_estimator_coverage_fraction": (
            sum(bool(sample["global_reference_estimator_covered"]) for sample in global_eligible)
            / len(global_eligible)
            if global_eligible
            else None
        ),
        "global_total_uncertainty_coverage_fraction": (
            sum(bool(sample["global_total_uncertainty_covered"]) for sample in global_eligible)
            / len(global_eligible)
            if global_eligible
            else None
        ),
        "global_trajectory_coverage_by_safety_factor": (
            global_coverage_by_safety_factor
        ),
        "global_refinement_pair_sweep": global_pair_sweep,
        "global_refinement_pair_pareto_frontier": global_pair_frontier,
        "global_order_aware_triplet_sweep": global_order_sweep,
        "global_order_aware_triplet_pareto_frontier": global_order_frontier,
        "global_statewise_four_level_sweep": global_statewise_sweep,
        "global_statewise_four_level_pareto_frontier": (
            global_statewise_frontier
        ),
        "global_statewise_epoch_sweep": global_statewise_epoch_sweep,
        "global_statewise_epoch_pareto_frontier": (
            global_statewise_epoch_frontier
        ),
        "global_two_term_modal_sweep": global_two_term_modal_sweep,
        "global_two_term_modal_pareto_frontier": (
            global_two_term_modal_frontier
        ),
        "global_modal_epoch_sweep": global_modal_epoch_sweep,
        "global_modal_epoch_pareto_frontier": global_modal_epoch_frontier,
        "global_temporally_aligned_modal_epoch_sweep": (
            global_temporally_aligned_modal_epoch_sweep
        ),
        "global_temporally_aligned_modal_epoch_pareto_frontier": (
            global_temporally_aligned_modal_epoch_frontier
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
        "coverage_by_authority_transfer": {
            transfer: {
                "eligible": transfer_counts[transfer],
                "covered": transfer_covered[transfer],
                "fraction": transfer_covered[transfer] / transfer_counts[transfer],
            }
            for transfer in sorted(transfer_counts)
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
    indices = [
        int(value)
        for value in case.get("state_indices", range(len(candidate)))
    ]
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
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--observatory-report")
    source.add_argument("--runtime-atlas-manifest")
    parser.add_argument("--observatory-manifest")
    parser.add_argument("--atlas-manifest", default=str(DEFAULT_ATLAS_MANIFEST))
    parser.add_argument("--case", action="append", dest="cases")
    parser.add_argument("--output", required=True)
    parser.add_argument("--sample-csv")
    parser.add_argument("--plot-directory")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.observatory_report:
        if arguments.cases:
            raise ValueError("--case is supported only with --runtime-atlas-manifest")
        observatory_path = Path(arguments.observatory_report)
        observatory = json.loads(observatory_path.read_text(encoding="utf-8"))
        atlas = execute_bound_atlas(
            observatory,
            observatory_report_sha256=_sha256_file(observatory_path),
            observatory_manifest_path=arguments.observatory_manifest,
            atlas_manifest_path=arguments.atlas_manifest,
        )
    else:
        if arguments.observatory_manifest:
            raise ValueError(
                "--observatory-manifest cannot be combined with --runtime-atlas-manifest"
            )
        atlas = execute_runtime_bound_atlas(
            arguments.runtime_atlas_manifest,
            selected_cases=set(arguments.cases) if arguments.cases else None,
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
                "qualified_cases": atlas.get("qualified_case_count"),
                "unqualified_cases": atlas.get("unqualified_case_count"),
                "output": arguments.output,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
