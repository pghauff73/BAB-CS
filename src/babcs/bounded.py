from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, replace

from .integrators import (
    ImplicitSettings,
    IntegrationError,
    implicit_step,
    integrate_reference_window,
)
from .linalg import matrix_inf_norm, weighted_rms
from .model import Circuit, CircuitEvaluation, CircuitSolveError


@dataclass(frozen=True)
class BABCSConfig:
    rollout_mode: str = "shadow"
    absolute_tolerance: float = 1.0e-9
    relative_tolerance: float = 1.0e-6
    algebraic_residual_cap: float = 1.0e-8
    full_residual_cap: float = 1.0e-8
    predictor_reference_cap: float = 25.0
    anchor_reference_cap: float = 20.0
    energy_absolute_tolerance: float = 1.0e-12
    energy_relative_tolerance: float = 1.0e-5
    energy_injection_cap: float = 2.0
    target_contraction: float = 0.8
    minimum_correction_gain: float = 0.25
    maximum_correction_gain: float = 1.0
    stiffness_limit: float = 0.8
    maximum_step_ratio: float = 2.0
    anchor_interval_steps: int = 16
    anchor_substeps: int = 4
    minimum_step: float = 1.0e-15
    maximum_rejections: int = 12
    reference_method: str = "trapezoidal"
    startup_method: str = "backward_euler"
    implicit_settings: ImplicitSettings = ImplicitSettings()

    def __post_init__(self) -> None:
        positive_values = (
            self.absolute_tolerance,
            self.relative_tolerance,
            self.algebraic_residual_cap,
            self.full_residual_cap,
            self.predictor_reference_cap,
            self.anchor_reference_cap,
            self.energy_absolute_tolerance,
            self.energy_relative_tolerance,
            self.energy_injection_cap,
            self.stiffness_limit,
            self.maximum_step_ratio,
            self.minimum_step,
        )
        if any(value <= 0.0 for value in positive_values):
            raise ValueError("BAB-CS tolerances and limits must be positive")
        if not 0.0 < self.target_contraction < 1.0:
            raise ValueError("target_contraction must lie strictly between zero and one")
        if not 0.0 <= self.minimum_correction_gain <= self.maximum_correction_gain <= 1.0:
            raise ValueError("correction gains must satisfy 0 <= min <= max <= 1")
        if self.anchor_interval_steps < 1 or self.anchor_substeps < 1:
            raise ValueError("anchor intervals and substeps must be positive")
        if self.maximum_rejections < 1:
            raise ValueError("maximum_rejections must be positive")
        if self.rollout_mode not in {"disabled", "shadow", "active"}:
            raise ValueError("rollout_mode must be disabled, shadow, or active")


@dataclass(frozen=True)
class SimulationState:
    evaluation: CircuitEvaluation
    accepted_step: float
    method: str

    @property
    def time(self) -> float:
        return self.evaluation.time


@dataclass(frozen=True)
class BABCSHistory:
    previous_evaluation: CircuitEvaluation | None
    previous_step: float | None
    estimated_bound: float
    generation: int
    accepted_steps: int
    steps_since_anchor: int
    anchor_evaluation: CircuitEvaluation
    periodic_reanchors: int = 0
    safety_reanchors: int = 0
    implicit_fallbacks: int = 0
    rejected_steps: int = 0


@dataclass(frozen=True)
class StepMetrics:
    method: str
    ab_used: bool
    reference_method: str
    correction_gain: float
    predictor_reference_error: float
    corrected_reference_error: float
    algebraic_residual: float
    full_residual: float
    energy_balance_error: float
    energy_injection_ratio: float
    stiffness_indicator: float
    predictor_amplification: float
    closed_loop_gain: float
    estimated_bound: float
    certified_contractive: bool
    reference_iterations: int
    projection_iterations: int
    periodic_reanchor: bool = False
    safety_reanchor: bool = False
    anchor_reference_error: float = 0.0


@dataclass(frozen=True)
class StepResult:
    state: SimulationState
    history: BABCSHistory
    metrics: StepMetrics


class StepRejected(RuntimeError):
    def __init__(self, reason: str, suggested_step: float) -> None:
        super().__init__(reason)
        self.reason = reason
        self.suggested_step = suggested_step


def variable_step_ab2_predict(
    current_state: Sequence[float],
    current_derivative: Sequence[float],
    previous_derivative: Sequence[float],
    step: float,
    previous_step: float,
) -> tuple[float, ...]:
    if step <= 0.0 or previous_step <= 0.0:
        raise ValueError("AB2 steps must be positive")
    if not (
        len(current_state) == len(current_derivative) == len(previous_derivative)
    ):
        raise ValueError("AB2 state and derivative vectors must have equal lengths")
    ratio = step / previous_step
    coefficient_current = 1.0 + 0.5 * ratio
    coefficient_previous = 0.5 * ratio
    return tuple(
        value
        + step
        * (
            coefficient_current * current_rate
            - coefficient_previous * previous_rate
        )
        for value, current_rate, previous_rate in zip(
            current_state,
            current_derivative,
            previous_derivative,
            strict=True,
        )
    )


class BoundedAdamsBashforthIntegrator:
    def __init__(self, config: BABCSConfig = BABCSConfig()) -> None:
        self.config = config

    def initialize(
        self,
        circuit: Circuit,
        time: float = 0.0,
        dynamic_state: Sequence[float] | None = None,
    ) -> tuple[SimulationState, BABCSHistory]:
        state_values = circuit.initial_dynamic_state() if dynamic_state is None else tuple(dynamic_state)
        evaluation = circuit.evaluate(time, state_values)
        state = SimulationState(evaluation, 0.0, "initial")
        history = BABCSHistory(
            previous_evaluation=None,
            previous_step=None,
            estimated_bound=0.0,
            generation=0,
            accepted_steps=0,
            steps_since_anchor=0,
            anchor_evaluation=evaluation,
        )
        return state, history

    def step(
        self,
        circuit: Circuit,
        state: SimulationState,
        history: BABCSHistory,
        step: float,
    ) -> StepResult:
        if step < self.config.minimum_step:
            raise StepRejected("requested step is below the configured minimum", step)
        current = state.evaluation
        if self.config.rollout_mode == "disabled":
            return self._implicit_authority_step(circuit, state, history, step)
        can_use_ab = self._can_use_ab(history, step)
        if not can_use_ab:
            return self._implicit_startup_step(circuit, state, history, step)

        assert history.previous_evaluation is not None
        assert history.previous_step is not None
        ratio = step / history.previous_step
        coefficient_current = 1.0 + 0.5 * ratio
        coefficient_previous = 0.5 * ratio
        predicted_state = variable_step_ab2_predict(
            current.dynamic_state,
            current.derivative,
            history.previous_evaluation.derivative,
            step,
            history.previous_step,
        )

        try:
            predicted = circuit.evaluate(
                current.time + step,
                predicted_state,
                current.algebraic.unknowns,
            )
            reference_result = implicit_step(
                circuit,
                self.config.reference_method,
                current,
                step,
                previous_state=history.previous_evaluation.dynamic_state,
                previous_step=history.previous_step,
                initial_guess=predicted_state,
                settings=self.config.implicit_settings,
            )
        except (CircuitSolveError, IntegrationError) as error:
            raise StepRejected(
                f"predictor or reference solve failed: {error}",
                max(step * 0.5, self.config.minimum_step),
            ) from error

        reference = reference_result.evaluation
        predictor_error = self._scaled_state_error(predicted.dynamic_state, reference.dynamic_state)
        if not math.isfinite(predictor_error) or predictor_error > self.config.predictor_reference_cap:
            raise StepRejected(
                f"predictor-reference cap exceeded: {predictor_error:.6g}",
                max(step * 0.5, self.config.minimum_step),
            )

        current_jacobian_norm = matrix_inf_norm(
            circuit.differential_jacobian(current.time, current.dynamic_state, current.algebraic.unknowns)
        )
        previous_jacobian_norm = matrix_inf_norm(
            circuit.differential_jacobian(
                history.previous_evaluation.time,
                history.previous_evaluation.dynamic_state,
                history.previous_evaluation.algebraic.unknowns,
            )
        )
        stiffness_indicator = step * max(current_jacobian_norm, previous_jacobian_norm)
        predictor_amplification = max(
            1.0,
            1.0
            + step
            * (
                coefficient_current * current_jacobian_norm
                + coefficient_previous * previous_jacobian_norm
            ),
        )
        if not all(
            math.isfinite(value)
            for value in (stiffness_indicator, predictor_amplification)
        ):
            raise StepRejected(
                "non-finite stiffness or amplification metric",
                max(step * 0.5, self.config.minimum_step),
            )
        required_gain = 1.0 - self.config.target_contraction / predictor_amplification
        correction_gain = min(
            self.config.maximum_correction_gain,
            max(self.config.minimum_correction_gain, required_gain),
        )
        method = "babcs_ab2"
        fallback = False
        if self.config.rollout_mode == "shadow":
            correction_gain = 1.0
            method = "shadow_reference_authority"
        if stiffness_indicator > self.config.stiffness_limit:
            correction_gain = 1.0
            method = "implicit_stiffness_fallback"
            fallback = True

        closed_loop_gain = (1.0 - correction_gain) * predictor_amplification
        if closed_loop_gain >= 1.0:
            correction_gain = 1.0
            closed_loop_gain = 0.0
            method = "implicit_contraction_fallback"
            fallback = True

        corrected_state = tuple(
            (1.0 - correction_gain) * predicted_value + correction_gain * reference_value
            for predicted_value, reference_value in zip(
                predicted.dynamic_state,
                reference.dynamic_state,
                strict=True,
            )
        )
        try:
            corrected = circuit.evaluate(
                current.time + step,
                corrected_state,
                reference.algebraic.unknowns,
            )
        except CircuitSolveError:
            corrected = reference
            correction_gain = 1.0
            closed_loop_gain = 0.0
            method = "implicit_projection_fallback"
            fallback = True

        energy_balance_error, energy_injection_ratio = self._energy_metrics(current, corrected, step)
        if not all(math.isfinite(value) for value in (energy_balance_error, energy_injection_ratio)):
            raise StepRejected(
                "non-finite energy metric",
                max(step * 0.5, self.config.minimum_step),
            )
        if energy_injection_ratio > self.config.energy_injection_cap and correction_gain < 1.0:
            corrected = reference
            correction_gain = 1.0
            closed_loop_gain = 0.0
            method = "implicit_passivity_fallback"
            fallback = True
            energy_balance_error, energy_injection_ratio = self._energy_metrics(current, corrected, step)

        if energy_injection_ratio > self.config.energy_injection_cap:
            raise StepRejected(
                f"energy-injection cap exceeded: {energy_injection_ratio:.6g}",
                max(step * 0.5, self.config.minimum_step),
            )

        algebraic_residual = corrected.algebraic.residual_norm
        full_residual = circuit.full_residual_norm(corrected)
        if not all(math.isfinite(value) for value in (algebraic_residual, full_residual)):
            raise StepRejected(
                "non-finite circuit residual",
                max(step * 0.5, self.config.minimum_step),
            )
        if algebraic_residual > self.config.algebraic_residual_cap:
            raise StepRejected(
                f"algebraic residual cap exceeded: {algebraic_residual:.6g}",
                max(step * 0.5, self.config.minimum_step),
            )
        if full_residual > self.config.full_residual_cap:
            raise StepRejected(
                f"full residual cap exceeded: {full_residual:.6g}",
                max(step * 0.5, self.config.minimum_step),
            )

        corrected_reference_error = self._scaled_state_error(
            corrected.dynamic_state,
            reference.dynamic_state,
        )
        residual_ratio = max(
            algebraic_residual / self.config.algebraic_residual_cap,
            full_residual / self.config.full_residual_cap,
        )
        local_defect = corrected_reference_error + residual_ratio
        estimated_bound = closed_loop_gain * history.estimated_bound + local_defect
        if not all(
            math.isfinite(value)
            for value in (
                corrected_reference_error,
                closed_loop_gain,
                local_defect,
                estimated_bound,
            )
        ):
            raise StepRejected(
                "non-finite correction or bound metric",
                max(step * 0.5, self.config.minimum_step),
            )
        certified = closed_loop_gain < 1.0

        new_state = SimulationState(corrected, step, method)
        new_history = replace(
            history,
            previous_evaluation=current,
            previous_step=step,
            estimated_bound=estimated_bound,
            accepted_steps=history.accepted_steps + 1,
            steps_since_anchor=history.steps_since_anchor + 1,
            implicit_fallbacks=history.implicit_fallbacks + int(fallback),
        )
        metrics = StepMetrics(
            method=method,
            ab_used=True,
            reference_method=reference_result.method,
            correction_gain=correction_gain,
            predictor_reference_error=predictor_error,
            corrected_reference_error=corrected_reference_error,
            algebraic_residual=algebraic_residual,
            full_residual=full_residual,
            energy_balance_error=energy_balance_error,
            energy_injection_ratio=energy_injection_ratio,
            stiffness_indicator=stiffness_indicator,
            predictor_amplification=predictor_amplification,
            closed_loop_gain=closed_loop_gain,
            estimated_bound=estimated_bound,
            certified_contractive=certified,
            reference_iterations=reference_result.iterations,
            projection_iterations=corrected.algebraic.iterations,
        )
        return StepResult(new_state, new_history, metrics)

    def _implicit_authority_step(
        self,
        circuit: Circuit,
        state: SimulationState,
        history: BABCSHistory,
        step: float,
    ) -> StepResult:
        try:
            result = implicit_step(
                circuit,
                self.config.reference_method,
                state.evaluation,
                step,
                previous_state=(
                    history.previous_evaluation.dynamic_state
                    if history.previous_evaluation is not None
                    else None
                ),
                previous_step=history.previous_step,
                settings=self.config.implicit_settings,
            )
        except (CircuitSolveError, IntegrationError) as error:
            raise StepRejected(
                f"implicit authority failed: {error}",
                max(step * 0.5, self.config.minimum_step),
            ) from error
        evaluation = result.evaluation
        algebraic_residual = evaluation.algebraic.residual_norm
        full_residual = circuit.full_residual_norm(evaluation)
        if not all(math.isfinite(value) for value in (algebraic_residual, full_residual)):
            raise StepRejected(
                "non-finite implicit authority residual",
                max(step * 0.5, self.config.minimum_step),
            )
        if algebraic_residual > self.config.algebraic_residual_cap or full_residual > self.config.full_residual_cap:
            raise StepRejected(
                "implicit authority residual cap exceeded",
                max(step * 0.5, self.config.minimum_step),
            )
        energy_balance_error, energy_injection_ratio = self._energy_metrics(state.evaluation, evaluation, step)
        if not all(math.isfinite(value) for value in (energy_balance_error, energy_injection_ratio)):
            raise StepRejected(
                "non-finite implicit authority energy metric",
                max(step * 0.5, self.config.minimum_step),
            )
        if energy_injection_ratio > self.config.energy_injection_cap:
            raise StepRejected(
                f"implicit authority energy cap exceeded: {energy_injection_ratio:.6g}",
                max(step * 0.5, self.config.minimum_step),
            )
        new_state = SimulationState(evaluation, step, "implicit_authority")
        new_history = replace(
            history,
            previous_evaluation=state.evaluation,
            previous_step=step,
            estimated_bound=0.0,
            accepted_steps=history.accepted_steps + 1,
            steps_since_anchor=history.steps_since_anchor + 1,
            implicit_fallbacks=history.implicit_fallbacks + 1,
        )
        metrics = StepMetrics(
            method=new_state.method,
            ab_used=False,
            reference_method=result.method,
            correction_gain=1.0,
            predictor_reference_error=0.0,
            corrected_reference_error=0.0,
            algebraic_residual=algebraic_residual,
            full_residual=full_residual,
            energy_balance_error=energy_balance_error,
            energy_injection_ratio=energy_injection_ratio,
            stiffness_indicator=0.0,
            predictor_amplification=0.0,
            closed_loop_gain=0.0,
            estimated_bound=0.0,
            certified_contractive=True,
            reference_iterations=result.iterations,
            projection_iterations=evaluation.algebraic.iterations,
        )
        return StepResult(new_state, new_history, metrics)

    def _implicit_startup_step(
        self,
        circuit: Circuit,
        state: SimulationState,
        history: BABCSHistory,
        step: float,
    ) -> StepResult:
        try:
            result = implicit_step(
                circuit,
                self.config.startup_method,
                state.evaluation,
                step,
                settings=self.config.implicit_settings,
            )
        except (CircuitSolveError, IntegrationError) as error:
            raise StepRejected(
                f"implicit startup failed: {error}",
                max(step * 0.5, self.config.minimum_step),
            ) from error

        evaluation = result.evaluation
        algebraic_residual = evaluation.algebraic.residual_norm
        full_residual = circuit.full_residual_norm(evaluation)
        if not all(math.isfinite(value) for value in (algebraic_residual, full_residual)):
            raise StepRejected(
                "non-finite implicit startup residual",
                max(step * 0.5, self.config.minimum_step),
            )
        if algebraic_residual > self.config.algebraic_residual_cap or full_residual > self.config.full_residual_cap:
            raise StepRejected(
                "implicit startup residual cap exceeded",
                max(step * 0.5, self.config.minimum_step),
            )
        energy_balance_error, energy_injection_ratio = self._energy_metrics(state.evaluation, evaluation, step)
        if not all(math.isfinite(value) for value in (energy_balance_error, energy_injection_ratio)):
            raise StepRejected(
                "non-finite implicit startup energy metric",
                max(step * 0.5, self.config.minimum_step),
            )
        if energy_injection_ratio > self.config.energy_injection_cap:
            raise StepRejected(
                f"implicit startup energy cap exceeded: {energy_injection_ratio:.6g}",
                max(step * 0.5, self.config.minimum_step),
            )

        new_state = SimulationState(evaluation, step, f"{result.method}_startup")
        new_history = replace(
            history,
            previous_evaluation=state.evaluation,
            previous_step=step,
            estimated_bound=0.0,
            accepted_steps=history.accepted_steps + 1,
            steps_since_anchor=history.steps_since_anchor + 1,
            implicit_fallbacks=history.implicit_fallbacks + 1,
        )
        metrics = StepMetrics(
            method=new_state.method,
            ab_used=False,
            reference_method=result.method,
            correction_gain=1.0,
            predictor_reference_error=0.0,
            corrected_reference_error=0.0,
            algebraic_residual=algebraic_residual,
            full_residual=full_residual,
            energy_balance_error=energy_balance_error,
            energy_injection_ratio=energy_injection_ratio,
            stiffness_indicator=0.0,
            predictor_amplification=0.0,
            closed_loop_gain=0.0,
            estimated_bound=0.0,
            certified_contractive=True,
            reference_iterations=result.iterations,
            projection_iterations=evaluation.algebraic.iterations,
        )
        return StepResult(new_state, new_history, metrics)

    def reanchor_if_due(
        self,
        circuit: Circuit,
        result: StepResult,
    ) -> StepResult:
        history = result.history
        if history.steps_since_anchor < self.config.anchor_interval_steps:
            return result
        anchor = history.anchor_evaluation
        current = result.state.evaluation
        if current.time <= anchor.time:
            return result

        target_times: list[float] = []
        if history.previous_evaluation is not None and history.previous_evaluation.time > anchor.time:
            target_times.append(history.previous_evaluation.time)
        target_times.append(current.time)
        target_times = sorted(set(target_times))
        window = current.time - anchor.time
        maximum_step = window / max(history.steps_since_anchor * self.config.anchor_substeps, 1)
        maximum_step = max(maximum_step, self.config.minimum_step)

        try:
            reference_states = integrate_reference_window(
                circuit,
                anchor,
                target_times,
                maximum_step,
                method=self.config.reference_method,
                settings=self.config.implicit_settings,
            )
        except IntegrationError as error:
            raise StepRejected(
                f"independent re-anchor failed: {error}",
                max(result.state.accepted_step * 0.5, self.config.minimum_step),
            ) from error

        anchored_current = reference_states[-1]
        anchor_error = self._scaled_state_error(
            current.dynamic_state,
            anchored_current.dynamic_state,
        )
        if not math.isfinite(anchor_error):
            raise StepRejected(
                "non-finite independent anchor metric",
                max(result.state.accepted_step * 0.5, self.config.minimum_step),
            )
        safety_reanchor = anchor_error > self.config.anchor_reference_cap
        previous_evaluation = None
        previous_step = None
        if len(reference_states) == 2:
            previous_evaluation = reference_states[0]
            previous_step = anchored_current.time - previous_evaluation.time

        new_state = SimulationState(
            anchored_current,
            result.state.accepted_step,
            "safety_reanchor" if safety_reanchor else "periodic_reanchor",
        )
        new_history = replace(
            history,
            previous_evaluation=previous_evaluation,
            previous_step=previous_step,
            estimated_bound=0.0,
            generation=history.generation + 1,
            steps_since_anchor=0,
            anchor_evaluation=anchored_current,
            periodic_reanchors=history.periodic_reanchors + 1,
            safety_reanchors=history.safety_reanchors + int(safety_reanchor),
        )
        metrics = replace(
            result.metrics,
            method=new_state.method,
            corrected_reference_error=0.0,
            estimated_bound=0.0,
            certified_contractive=True,
            periodic_reanchor=True,
            safety_reanchor=safety_reanchor,
            anchor_reference_error=anchor_error,
        )
        return StepResult(new_state, new_history, metrics)

    def reset_history(
        self,
        state: SimulationState,
        history: BABCSHistory,
    ) -> BABCSHistory:
        return replace(
            history,
            previous_evaluation=None,
            previous_step=None,
            estimated_bound=0.0,
            generation=history.generation + 1,
            steps_since_anchor=0,
            anchor_evaluation=state.evaluation,
        )

    def record_rejection(self, history: BABCSHistory) -> BABCSHistory:
        return replace(history, rejected_steps=history.rejected_steps + 1)

    def _can_use_ab(self, history: BABCSHistory, step: float) -> bool:
        if history.previous_evaluation is None or history.previous_step is None:
            return False
        ratio = step / history.previous_step
        return 1.0 / self.config.maximum_step_ratio <= ratio <= self.config.maximum_step_ratio

    def _scaled_state_error(self, left: Sequence[float], right: Sequence[float]) -> float:
        difference = [left_value - right_value for left_value, right_value in zip(left, right, strict=True)]
        return weighted_rms(
            difference,
            left,
            right,
            self.config.absolute_tolerance,
            self.config.relative_tolerance,
        )

    def _energy_metrics(
        self,
        current: CircuitEvaluation,
        candidate: CircuitEvaluation,
        step: float,
    ) -> tuple[float, float]:
        source_work = 0.5 * step * (current.source_power + candidate.source_power)
        dissipated_work = 0.5 * step * (current.dissipated_power + candidate.dissipated_power)
        energy_change = candidate.stored_energy - current.stored_energy
        balance_error = energy_change - (source_work - dissipated_work)
        scale = self.config.energy_absolute_tolerance + self.config.energy_relative_tolerance * max(
            abs(current.stored_energy),
            abs(candidate.stored_energy),
            abs(source_work),
            abs(dissipated_work),
            self.config.energy_absolute_tolerance,
        )
        injection_ratio = max(0.0, balance_error) / scale
        return balance_error, injection_ratio
