from __future__ import annotations

import math
from collections.abc import Sequence
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
class RejectionRecord:
    reason: str
    requested_step: float
    suggested_step: float


@dataclass(frozen=True)
class SimulationPoint:
    state: SimulationState
    metrics: StepMetrics | None
    event_boundary: bool = False
    rejection_count: int = 0
    rejection_reasons: tuple[str, ...] = ()
    rejections: tuple[RejectionRecord, ...] = ()
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
        output_times: Sequence[float] | None = None,
        output_interval_substeps: int | None = None,
    ) -> SimulationResult:
        if not all(math.isfinite(value) for value in (start_time, stop_time, nominal_step)):
            raise ValueError("simulation times and nominal_step must be finite")
        if stop_time <= start_time:
            raise ValueError("stop_time must follow start_time")
        if nominal_step <= 0.0:
            raise ValueError("nominal_step must be positive")
        output_schedule = _validated_output_times(
            output_times,
            start_time=start_time,
            stop_time=stop_time,
        )
        if output_interval_substeps is not None and (
            not isinstance(output_interval_substeps, int)
            or isinstance(output_interval_substeps, bool)
            or output_interval_substeps < 1
        ):
            raise ValueError("output_interval_substeps must be a positive integer")
        if output_interval_substeps is not None and not output_schedule:
            raise ValueError("output_interval_substeps requires output_times")

        state, history = self.integrator.initialize(circuit, start_time, initial_dynamic_state)
        breakpoint_waveforms = (
            circuit._simulation_breakpoint_waveforms()
            if type(circuit) is Circuit
            else None
        )
        points = [SimulationPoint(state, None)]
        current_step = nominal_step
        output_index = 0
        previous_output_time = start_time

        while state.time < stop_time:
            while output_index < len(output_schedule) and _matching_time(
                state.time,
                output_schedule[output_index],
            ):
                previous_output_time = output_schedule[output_index]
                output_index += 1
            next_output_time = (
                output_schedule[output_index]
                if output_index < len(output_schedule)
                else None
            )
            remaining = stop_time - state.time
            proposed_step = min(current_step, remaining)
            if output_interval_substeps is not None and next_output_time is not None:
                proposed_step = min(
                    proposed_step,
                    (next_output_time - previous_output_time)
                    / output_interval_substeps,
                )
            output_boundary_time = None
            if next_output_time is not None and (
                next_output_time < state.time + proposed_step
                or _matching_time(next_output_time, state.time + proposed_step)
            ):
                proposed_step = next_output_time - state.time
                output_boundary_time = next_output_time
            terminal_breakpoints = (
                Circuit._breakpoints_from_waveforms(
                    breakpoint_waveforms,
                    state.time,
                    stop_time,
                )
                if remaining < self.integrator.config.minimum_step
                and breakpoint_waveforms is not None
                else (
                    circuit.breakpoints(state.time, stop_time)
                    if remaining < self.integrator.config.minimum_step
                    else []
                )
            )
            terminal_breakpoints = [
                breakpoint
                for breakpoint in terminal_breakpoints
                if not _matching_time(state.time, breakpoint)
            ]
            if remaining < self.integrator.config.minimum_step:
                terminal_boundaries = list(terminal_breakpoints)
                if output_boundary_time is not None:
                    terminal_boundaries.append(output_boundary_time)
                if not terminal_boundaries:
                    break
                proposed_step = min(terminal_boundaries) - state.time
            if state.time + proposed_step <= state.time:
                raise RuntimeError(
                    f"nominal step cannot advance simulation time at t={state.time:.17g}"
                )
            breakpoints = (
                Circuit._breakpoints_from_waveforms(
                    breakpoint_waveforms,
                    state.time,
                    state.time + proposed_step,
                )
                if breakpoint_waveforms is not None
                else circuit.breakpoints(state.time, state.time + proposed_step)
            )
            breakpoints = [
                breakpoint
                for breakpoint in breakpoints
                if not _matching_time(state.time, breakpoint)
            ]
            event_time = breakpoints[0] if breakpoints else None
            if breakpoints:
                proposed_step = event_time - state.time

            attempt_step = proposed_step
            rejection_count = 0
            rejection_reasons: list[str] = []
            rejections: list[RejectionRecord] = []
            while True:
                try:
                    result = (
                        self.integrator.step_to_event(circuit, state, history, attempt_step)
                        if event_time is not None
                        else self.integrator.step(circuit, state, history, attempt_step)
                    )
                    if result.state.time <= state.time:
                        raise RuntimeError(
                            f"accepted step did not advance simulation time at t={state.time:.17g}"
                        )
                    reached_event = event_time is not None and _matching_time(
                        result.state.time,
                        event_time,
                    )
                    reached_output_boundary = (
                        output_boundary_time is not None
                        and _matching_time(
                            result.state.time,
                            output_boundary_time,
                        )
                    )
                    if reached_event:
                        result = self.integrator.reanchor_if_due(
                            circuit,
                            result,
                            force=True,
                        )
                    else:
                        result = self.integrator.reanchor_if_due(circuit, result)
                    break
                except StepRejected as error:
                    rejection_count += 1
                    rejection_reasons.append(error.reason)
                    rejections.append(
                        RejectionRecord(
                            reason=error.reason,
                            requested_step=attempt_step,
                            suggested_step=error.suggested_step,
                        )
                    )
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
                    rejections=tuple(rejections),
                    history_reset_reason=history_reset_reason,
                )
            )
            if reached_event:
                history = self.integrator.reset_history(state, history)
                current_step = min(
                    nominal_step,
                    max(attempt_step, self.integrator.config.minimum_step),
                )
            elif rejection_count:
                current_step = attempt_step
            elif reached_output_boundary and attempt_step < current_step:
                current_step = min(nominal_step, current_step)
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


def _matching_time(left: float, right: float) -> bool:
    if left == right:
        return True
    tolerance = 4.0 * max(math.ulp(left), math.ulp(right))
    return abs(left - right) <= tolerance


def _validated_output_times(
    output_times: Sequence[float] | None,
    *,
    start_time: float,
    stop_time: float,
) -> tuple[float, ...]:
    if output_times is None:
        return ()
    schedule = tuple(float(value) for value in output_times)
    if any(not math.isfinite(value) for value in schedule):
        raise ValueError("output_times must be finite")
    if any(right <= left for left, right in zip(schedule, schedule[1:])):
        raise ValueError("output_times must be strictly increasing")
    if any(value < start_time or value > stop_time for value in schedule):
        raise ValueError("output_times must lie within the simulation interval")
    return schedule
