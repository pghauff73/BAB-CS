from __future__ import annotations

import csv
import json
import math
from collections import Counter
from dataclasses import fields
from pathlib import Path
from typing import Any

from .bounded import BABCSConfig
from .integrators import ImplicitSettings
from .model import (
    Capacitor,
    Circuit,
    CurrentSource,
    Diode,
    Inductor,
    Resistor,
    Switch,
    VoltageSource,
)
from .simulator import SimulationResult
from .waveforms import waveform_from_data


def load_case(path: str | Path) -> tuple[Circuit, dict[str, float], BABCSConfig]:
    data = json.loads(
        Path(path).read_text(encoding="utf-8"),
        parse_constant=_reject_non_finite_json_constant,
    )
    if not isinstance(data, dict):
        raise ValueError("BAB-CS input must be a JSON object")
    raw_elements = data.get("elements")
    if not isinstance(raw_elements, list):
        raise ValueError("BAB-CS input requires an elements list")
    linear_backend = data.get("linear_backend", "dense")
    if not isinstance(linear_backend, str):
        raise ValueError("linear_backend must be a string")
    circuit = Circuit(
        (_element_from_data(element) for element in raw_elements),
        linear_backend=linear_backend,
    )

    simulation = data.get("simulation", {})
    if not isinstance(simulation, dict):
        raise ValueError("simulation must be an object")
    settings = {
        "start_time": float(simulation.get("start_time", 0.0)),
        "stop_time": float(simulation["stop_time"]),
        "nominal_step": float(simulation["nominal_step"]),
    }
    if not all(math.isfinite(value) for value in settings.values()):
        raise ValueError("simulation times and nominal_step must be finite")

    config_data = data.get("babcs", {})
    if not isinstance(config_data, dict):
        raise ValueError("babcs must be an object")
    config_values: dict[str, Any] = {}
    valid_fields = {field.name for field in fields(BABCSConfig)}
    unknown = set(config_data) - valid_fields
    if unknown:
        raise ValueError(f"unknown BAB-CS configuration fields: {', '.join(sorted(unknown))}")
    config_values.update(config_data)
    if "implicit_settings" in config_values:
        raw_implicit = config_values["implicit_settings"]
        if not isinstance(raw_implicit, dict):
            raise ValueError("implicit_settings must be an object")
        config_values["implicit_settings"] = ImplicitSettings(**raw_implicit)
    return circuit, settings, BABCSConfig(**config_values)


def _reject_non_finite_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is not supported: {value}")


def _element_from_data(data: object):
    if not isinstance(data, dict):
        raise ValueError("each element must be an object")
    kind = str(data["type"]).lower()
    common = (str(data["name"]), str(data["positive"]), str(data["negative"]))
    if kind in {"r", "resistor"}:
        return Resistor(*common, float(data["resistance"]))
    if kind in {"c", "capacitor"}:
        return Capacitor(
            *common,
            float(data["capacitance"]),
            float(data.get("initial_voltage", 0.0)),
        )
    if kind in {"l", "inductor"}:
        return Inductor(
            *common,
            float(data["inductance"]),
            float(data.get("initial_current", 0.0)),
        )
    if kind in {"i", "current_source"}:
        return CurrentSource(*common, waveform_from_data(data["waveform"]))
    if kind in {"v", "voltage_source"}:
        return VoltageSource(*common, waveform_from_data(data["waveform"]))
    if kind in {"d", "diode"}:
        return Diode(
            *common,
            float(data.get("saturation_current", 1.0e-12)),
            float(data.get("thermal_voltage", 0.02585)),
        )
    if kind in {"s", "switch"}:
        return Switch(
            *common,
            waveform_from_data(data["control"]),
            float(data.get("threshold", 0.5)),
            float(data.get("on_resistance", 1.0e-3)),
            float(data.get("off_resistance", 1.0e9)),
        )
    raise ValueError(f"unknown element type: {kind}")


def write_csv(path: str | Path, circuit: Circuit, result: SimulationResult) -> None:
    node_names = list(circuit.nodes)
    metric_names = [
        "correction_gain",
        "predictor_reference_error",
        "embedded_error",
        "embedded_defect",
        "corrected_reference_error",
        "algebraic_residual",
        "full_residual",
        "energy_balance_error",
        "energy_injection_ratio",
        "stiffness_indicator",
        "predictor_amplification",
        "closed_loop_gain",
        "estimated_bound",
        "residual_ratio",
        "local_defect",
        "anchor_reference_error",
        "reference_iterations",
        "projection_iterations",
        "reference_solve_count",
        "reference_circuit_evaluations",
        "reference_algebraic_iterations",
        "candidate_iterations",
        "candidate_solve_count",
        "candidate_circuit_evaluations",
        "candidate_algebraic_iterations",
        "dynamic_reference_checkpoint",
        "predictor_projection_iterations",
        "explicit_projection_count",
        "differential_jacobian_evaluations",
        "replay_steps",
        "replay_reference_iterations",
        "replay_circuit_evaluations",
        "replay_algebraic_iterations",
        "replay_refinement_substeps",
        "replay_refinement_retries",
        "replay_embedded_error",
        "pre_reset_estimated_bound",
    ]
    columns = (
        [
            "time",
            "accepted_step",
            "method",
            "event_boundary",
            "history_reset_reason",
            "rejection_count",
            "rejection_reasons",
            "rejection_requested_steps",
            "rejection_suggested_steps",
        ]
        + [f"state:{name}" for name in circuit.dynamic_names]
        + [f"voltage:{node}" for node in node_names]
        + metric_names
    )
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for point in result.points:
            row: dict[str, object] = {
                "time": point.time,
                "accepted_step": point.state.accepted_step,
                "method": point.state.method,
                "event_boundary": int(point.event_boundary),
                "history_reset_reason": point.history_reset_reason,
                "rejection_count": point.rejection_count,
                "rejection_reasons": " | ".join(point.rejection_reasons),
                "rejection_requested_steps": " | ".join(
                    format(rejection.requested_step, ".17g")
                    for rejection in point.rejections
                ),
                "rejection_suggested_steps": " | ".join(
                    format(rejection.suggested_step, ".17g")
                    for rejection in point.rejections
                ),
            }
            row.update(
                {
                    f"state:{name}": value
                    for name, value in zip(
                        circuit.dynamic_names,
                        point.state.evaluation.dynamic_state,
                        strict=True,
                    )
                }
            )
            row.update(
                {
                    f"voltage:{node}": point.state.evaluation.algebraic.node_voltages[node]
                    for node in node_names
                }
            )
            if point.metrics is not None:
                for name in metric_names:
                    row[name] = getattr(point.metrics, name)
            writer.writerow(row)


def summary_data(result: SimulationResult) -> dict[str, object]:
    metrics = [point.metrics for point in result.points if point.metrics is not None]
    accepted_steps = [point.state.accepted_step for point in result.points[1:]]
    rejection_categories = Counter(
        _rejection_category(reason)
        for point in result.points
        for reason in point.rejection_reasons
    )
    reset_reasons = Counter(
        point.history_reset_reason for point in result.points if point.history_reset_reason
    )
    return {
        "linear_backend": result.linear_backend,
        "points": len(result.points),
        "start_time": result.points[0].time,
        "stop_time": result.points[-1].time,
        "accepted_steps": result.final_history.accepted_steps,
        "rejected_steps": result.final_history.rejected_steps,
        "periodic_reanchors": result.final_history.periodic_reanchors,
        "safety_reanchors": result.final_history.safety_reanchors,
        "implicit_fallbacks": result.final_history.implicit_fallbacks,
        "history_generation": result.final_history.generation,
        "minimum_accepted_step": min(accepted_steps, default=0.0),
        "maximum_accepted_step": max(accepted_steps, default=0.0),
        "mean_accepted_step": (
            sum(accepted_steps) / len(accepted_steps) if accepted_steps else 0.0
        ),
        "maximum_predictor_reference_error": max(
            (metric.predictor_reference_error for metric in metrics), default=0.0
        ),
        "maximum_corrected_reference_error": max(
            (metric.corrected_reference_error for metric in metrics), default=0.0
        ),
        "maximum_embedded_error": max(
            (metric.embedded_error for metric in metrics), default=0.0
        ),
        "maximum_algebraic_residual": max((metric.algebraic_residual for metric in metrics), default=0.0),
        "maximum_full_residual": max((metric.full_residual for metric in metrics), default=0.0),
        "maximum_energy_injection_ratio": max(
            (metric.energy_injection_ratio for metric in metrics), default=0.0
        ),
        "maximum_estimated_bound": max((metric.estimated_bound for metric in metrics), default=0.0),
        "maximum_pre_reset_estimated_bound": max(
            (metric.pre_reset_estimated_bound for metric in metrics), default=0.0
        ),
        "maximum_anchor_reference_error": max(
            (metric.anchor_reference_error for metric in metrics), default=0.0
        ),
        "contractive_steps": sum(metric.certified_contractive for metric in metrics),
        "candidate_steps": sum(metric.candidate_used for metric in metrics),
        "dynamic_reference_checkpoints": sum(
            metric.dynamic_reference_checkpoint for metric in metrics
        ),
        "ab_steps": sum(metric.ab_used for metric in metrics),
        "candidate_solves": sum(metric.candidate_solve_count for metric in metrics),
        "candidate_iterations": sum(metric.candidate_iterations for metric in metrics),
        "candidate_circuit_evaluations": sum(
            metric.candidate_circuit_evaluations for metric in metrics
        ),
        "candidate_algebraic_iterations": sum(
            metric.candidate_algebraic_iterations for metric in metrics
        ),
        "reference_solves": sum(metric.reference_solve_count for metric in metrics),
        "reference_iterations": sum(metric.reference_iterations for metric in metrics),
        "reference_circuit_evaluations": sum(
            metric.reference_circuit_evaluations for metric in metrics
        ),
        "reference_algebraic_iterations": sum(
            metric.reference_algebraic_iterations for metric in metrics
        ),
        "explicit_projections": sum(metric.explicit_projection_count for metric in metrics),
        "predictor_projection_iterations": sum(
            metric.predictor_projection_iterations for metric in metrics
        ),
        "corrected_projection_iterations": sum(
            metric.projection_iterations for metric in metrics
        ),
        "differential_jacobian_evaluations": sum(
            metric.differential_jacobian_evaluations for metric in metrics
        ),
        "replay_steps": sum(metric.replay_steps for metric in metrics),
        "replay_reference_iterations": sum(
            metric.replay_reference_iterations for metric in metrics
        ),
        "replay_circuit_evaluations": sum(
            metric.replay_circuit_evaluations for metric in metrics
        ),
        "replay_algebraic_iterations": sum(
            metric.replay_algebraic_iterations for metric in metrics
        ),
        "maximum_replay_refinement_substeps": max(
            (metric.replay_refinement_substeps for metric in metrics),
            default=0,
        ),
        "replay_refinement_retries": sum(
            metric.replay_refinement_retries for metric in metrics
        ),
        "maximum_replay_embedded_error": max(
            (metric.replay_embedded_error for metric in metrics),
            default=0.0,
        ),
        "rejection_reasons": dict(sorted(rejection_categories.items())),
        "history_resets": dict(sorted(reset_reasons.items())),
    }


def _rejection_category(reason: str) -> str:
    prefix = reason.split(":", 1)[0].strip().lower()
    return "_".join(prefix.replace("-", " ").split())


def write_summary(path: str | Path, result: SimulationResult) -> None:
    Path(path).write_text(json.dumps(summary_data(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
