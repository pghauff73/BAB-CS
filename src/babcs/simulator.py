from __future__ import annotations

import math
from dataclasses import dataclass

from .bounded import (
    BABCSHistory,
    BoundedIntegrator,
    SimulationState,
    StepMetrics,
    StepRejected,
)
from .model import Circuit


@dataclass(frozen=True)
class SimulationPoint:
    state: SimulationState
    metrics: StepMetrics | None
    event_boundary: bool = False
    rejection_count: int = 0
    rejection_reasons: tuple[str, ...] = ()
    history_reset_reason: str = ""

    @property
    def time(self) -> float:
        return self.state.time


@dataclass(frozen=True)
class SimulationResult:
    points: tuple[SimulationPoint, ...]
    final_history: BABCSHistory
    linear_backend: str

    def node_trace(self, node: str) -> list[tuple[float, float]]:
        return [
            (point.time, point.state.evaluation.algebraic.node_voltages[node])
            for point in self.points
        ]

    def dynamic_trace(self, index: int) -> list[tuple[float, float]]:
        return [
            (point.time, point.state.evaluation.dynamic_state[index])
            for point in self.points
        ]


class Simulator:
    def __init__(self, integrator: BoundedIntegrator | None = None) -> None:
        self.integrator = integrator or BoundedIntegrator()

    def run(
        self,
        circuit: Circuit,
        stop_time: float,
        nominal_step: float,
        *,
        start_time: float = 0.0,
        initial_dynamic_state: tuple[float, ...] | None = None,
    ) -> SimulationResult:
        if stop_time <= start_time:
            raise ValueError("stop_time must follow start_time")
        if nominal_step <= 0.0:
            raise ValueError("nominal_step must be positive")

        state, history = self.integrator.initialize(circuit, start_time, initial_dynamic_state)
        points = [SimulationPoint(state, None)]
        time_tolerance = 64.0 * math.ulp(max(abs(start_time), abs(stop_time), 1.0))
        current_step = nominal_step

        while state.time < stop_time - time_tolerance:
            proposed_step = min(current_step, stop_time - state.time)
            breakpoints = circuit.breakpoints(state.time, state.time + proposed_step)
            event_time = breakpoints[0] if breakpoints else None
            if breakpoints:
                proposed_step = event_time - state.time

            attempt_step = proposed_step
            rejection_count = 0
            rejection_reasons: list[str] = []
            while True:
                try:
                    result = self.integrator.step(circuit, state, history, attempt_step)
                    reached_event = event_time is not None and abs(result.state.time - event_time) <= time_tolerance
                    if not reached_event:
                        result = self.integrator.reanchor_if_due(circuit, result)
                    break
                except StepRejected as error:
                    rejection_count += 1
                    rejection_reasons.append(error.reason)
                    history = self.integrator.record_rejection(history)
                    if rejection_count >= self.integrator.config.maximum_rejections:
                        raise RuntimeError(
                            f"BAB-CS exhausted step retries at t={state.time:.17g}: {error.reason}"
                        ) from error
                    attempt_step = min(error.suggested_step, attempt_step * 0.5)
                    if attempt_step < self.integrator.config.minimum_step:
                        raise RuntimeError(
                            f"BAB-CS reached minimum step at t={state.time:.17g}: {error.reason}"
                        ) from error

            state = result.state
            history = result.history
            if reached_event:
                history_reset_reason = "event"
            elif result.metrics.safety_reanchor:
                history_reset_reason = "safety_reanchor"
            elif result.metrics.periodic_reanchor:
                history_reset_reason = "periodic_reanchor"
            else:
                history_reset_reason = ""
            points.append(
                SimulationPoint(
                    state=state,
                    metrics=result.metrics,
                    event_boundary=reached_event,
                    rejection_count=rejection_count,
                    rejection_reasons=tuple(rejection_reasons),
                    history_reset_reason=history_reset_reason,
                )
            )
            if reached_event:
                history = self.integrator.reset_history(state, history)
                current_step = min(nominal_step, attempt_step)
            elif rejection_count:
                current_step = attempt_step
            elif max(
                result.metrics.predictor_reference_error,
                result.metrics.embedded_error,
            ) < 0.25 * min(
                self.integrator.config.predictor_reference_cap,
                self.integrator.config.embedded_error_cap,
            ):
                current_step = min(nominal_step, attempt_step * 1.25)
            else:
                current_step = attempt_step

        return SimulationResult(tuple(points), history, circuit.linear_backend)
