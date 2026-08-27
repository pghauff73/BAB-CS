from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from copy import deepcopy
from typing import Any, Iterable

from tests.support.metrics import observed_order


EXPERIMENT_RECORD_SCHEMA_VERSION = 1

REASON_CODES = (
    "minimum_step",
    "non_finite_metric",
    "projection_failure",
    "reference_nonconvergence",
    "candidate_nonconvergence",
    "predictor_reference_cap",
    "anchor_reference_cap",
    "recursive_bound_cap",
    "algebraic_residual_cap",
    "full_residual_cap",
    "energy_injection_cap",
    "stiffness_transfer",
    "non_contractive",
    "event_restart",
    "replay_failure",
    "linear_solve_failure",
    "configuration_error",
    "unknown",
)


def canonical_row_id(
    *,
    case_id: str,
    method: str,
    nominal_step: float,
    anchor_interval: int | None,
    configuration: dict[str, Any],
) -> str:
    identity = {
        "case_id": case_id,
        "method": method,
        "nominal_step": nominal_step,
        "anchor_interval": anchor_interval,
        "configuration": configuration,
    }
    payload = json.dumps(
        _canonical_value(identity),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return f"exp-{hashlib.sha256(payload).hexdigest()[:24]}"


def decorate_comparison_record(result: dict[str, Any]) -> dict[str, Any]:
    record = deepcopy(result)
    record["schema_version"] = EXPERIMENT_RECORD_SCHEMA_VERSION
    record["row_id"] = canonical_row_id(
        case_id=str(record["case_id"]),
        method=str(record["method"]),
        nominal_step=float(record["nominal_step"]),
        anchor_interval=record.get("anchor_interval"),
        configuration=record["configuration"],
    )
    record["status"] = "success"
    rejection_reasons = record.get("diagnostics", {}).get("rejection_reasons", {})
    record["reason_codes"] = sorted(
        {
            classify_reason(str(reason))
            for reason, count in rejection_reasons.items()
            if int(count) > 0
        }
    )
    oscillator = record.get("oscillator")
    bounded = record.get("bound", {}).get("authority") != "none"
    record["applicability"] = {
        "internal_bound": bounded,
        "anchor": bounded,
        "passivity": record["method"] != "raw_ab2",
        "oscillator": oscillator is not None,
        "phase": oscillator is not None,
        "energy_span": oscillator is not None,
    }
    validate_experiment_record(record)
    return record


def validate_experiment_record(record: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "row_id",
        "case_id",
        "method",
        "nominal_step",
        "anchor_interval",
        "authority",
        "configuration",
        "accuracy",
        "bound",
        "diagnostics",
        "work",
        "oscillator",
        "status",
        "reason_codes",
        "applicability",
    }
    missing = sorted(required - set(record))
    if missing:
        raise ValueError(f"experiment record missing fields: {', '.join(missing)}")
    if record["schema_version"] != EXPERIMENT_RECORD_SCHEMA_VERSION:
        raise ValueError("unsupported experiment record schema")
    if not isinstance(record["row_id"], str) or not record["row_id"].startswith("exp-"):
        raise ValueError("experiment row_id must use the exp- prefix")
    if not isinstance(record["case_id"], str) or not record["case_id"]:
        raise ValueError("experiment case_id must not be empty")
    if not isinstance(record["method"], str) or not record["method"]:
        raise ValueError("experiment method must not be empty")
    if not math.isfinite(float(record["nominal_step"])) or float(record["nominal_step"]) <= 0:
        raise ValueError("experiment nominal_step must be positive and finite")
    if record["status"] not in {"success", "controlled_rejection", "execution_failure"}:
        raise ValueError("unsupported experiment status")
    unknown_codes = sorted(set(record["reason_codes"]) - set(REASON_CODES))
    if unknown_codes:
        raise ValueError(f"unsupported experiment reason codes: {', '.join(unknown_codes)}")
    if not isinstance(record["applicability"], dict):
        raise ValueError("experiment applicability must be an object")


def classify_reason(reason: str) -> str:
    normalized = reason.lower().replace("_", "-")
    rules = (
        ("minimum step", "minimum_step"),
        ("non-finite", "non_finite_metric"),
        ("predictor/reference", "predictor_reference_cap"),
        ("anchor/reference", "anchor_reference_cap"),
        ("estimated-bound", "recursive_bound_cap"),
        ("bound cap", "recursive_bound_cap"),
        ("algebraic residual", "algebraic_residual_cap"),
        ("full residual", "full_residual_cap"),
        ("energy", "energy_injection_cap"),
        ("stiff", "stiffness_transfer"),
        ("contract", "non_contractive"),
        ("event", "event_restart"),
        ("re-anchor", "replay_failure"),
        ("replay", "replay_failure"),
        ("projection", "projection_failure"),
        ("reference", "reference_nonconvergence"),
        ("candidate", "candidate_nonconvergence"),
        ("linear", "linear_solve_failure"),
        ("config", "configuration_error"),
    )
    for fragment, code in rules:
        if fragment in normalized:
            return code
    return "unknown"


def analyze_experiment_records(
    records: Iterable[dict[str, Any]],
    *,
    accuracy_targets: list[float],
    work_budgets: list[int],
) -> dict[str, Any]:
    grouped: dict[tuple[str, str, int | None], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        validate_experiment_record(record)
        grouped[(record["case_id"], record["method"], record["anchor_interval"])].append(
            record
        )

    convergence = []
    fixed_accuracy = []
    fixed_work = []
    for (case_id, method, anchor_interval), group in sorted(grouped.items()):
        successful = [record for record in group if record["status"] == "success"]
        ordered = sorted(successful, key=lambda item: item["nominal_step"], reverse=True)
        orders = []
        for coarse, fine in zip(ordered, ordered[1:]):
            coarse_error = coarse["accuracy"]["maximum_absolute_error"]
            fine_error = fine["accuracy"]["maximum_absolute_error"]
            ratio = coarse["nominal_step"] / fine["nominal_step"]
            if coarse_error > 0.0 and fine_error > 0.0 and ratio > 1.0:
                orders.append(
                    {
                        "coarse_row_id": coarse["row_id"],
                        "fine_row_id": fine["row_id"],
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
                record
                for record in successful
                if record["accuracy"]["maximum_absolute_error"] <= target
            ]
            selected = min(
                eligible,
                key=lambda item: (
                    item["work"]["deterministic_work_units"],
                    item["accuracy"]["maximum_absolute_error"],
                    item["nominal_step"],
                    item["row_id"],
                ),
                default=None,
            )
            fixed_accuracy.append(
                {
                    "case_id": case_id,
                    "method": method,
                    "anchor_interval": anchor_interval,
                    "accuracy_target": target,
                    "status": "no_qualifying_row" if selected is None else "selected",
                    "selected_row_id": None if selected is None else selected["row_id"],
                    "selected_nominal_step": (
                        None if selected is None else selected["nominal_step"]
                    ),
                    "maximum_absolute_error": (
                        None
                        if selected is None
                        else selected["accuracy"]["maximum_absolute_error"]
                    ),
                    "deterministic_work_units": (
                        None
                        if selected is None
                        else selected["work"]["deterministic_work_units"]
                    ),
                }
            )

        for budget in work_budgets:
            eligible = [
                record
                for record in successful
                if record["work"]["deterministic_work_units"] <= budget
            ]
            selected = min(
                eligible,
                key=lambda item: (
                    item["accuracy"]["maximum_absolute_error"],
                    item["accuracy"]["rms_absolute_error"],
                    item["work"]["deterministic_work_units"],
                    item["row_id"],
                ),
                default=None,
            )
            fixed_work.append(
                {
                    "case_id": case_id,
                    "method": method,
                    "anchor_interval": anchor_interval,
                    "work_budget": budget,
                    "status": "no_qualifying_row" if selected is None else "selected",
                    "selected_row_id": None if selected is None else selected["row_id"],
                    "selected_nominal_step": (
                        None if selected is None else selected["nominal_step"]
                    ),
                    "maximum_absolute_error": (
                        None
                        if selected is None
                        else selected["accuracy"]["maximum_absolute_error"]
                    ),
                    "rms_absolute_error": (
                        None if selected is None else selected["accuracy"]["rms_absolute_error"]
                    ),
                    "deterministic_work_units": (
                        None
                        if selected is None
                        else selected["work"]["deterministic_work_units"]
                    ),
                    "unused_work_budget": (
                        None
                        if selected is None
                        else budget - selected["work"]["deterministic_work_units"]
                    ),
                }
            )

    return {
        "convergence": convergence,
        "fixed_accuracy": fixed_accuracy,
        "fixed_work": fixed_work,
    }


def _canonical_value(value: Any) -> Any:
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("experiment row identity cannot contain non-finite floats")
        return {"$float": value.hex()}
    if isinstance(value, dict):
        return {str(key): _canonical_value(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if value is None or isinstance(value, (bool, int, str)):
        return value
    raise TypeError(f"unsupported experiment identity value: {type(value).__name__}")
