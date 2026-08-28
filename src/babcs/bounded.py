from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, replace

from .candidates import (
    CANDIDATE_METHODS,
    IMPLICIT_CANDIDATE_METHODS,
    CandidateUnavailable,
    candidate_amplification,
    candidate_step,
    finite_candidate_metrics,
    normalize_candidate_method,
)
from .integrators import (
    ImplicitSettings,
    ImplicitStepResult,
    IntegrationError,
    energy_balance_metrics,
    implicit_step,
    integrate_reference_window_with_stats,
)
from .linalg import matrix_inf_norm, weighted_rms
from .model import Circuit, CircuitEvaluation, CircuitSolveError


DEFERRED_NATIVE_JACOBIAN_MINIMUM_SIZE = 64
MINIMUM_EVENT_ANCHOR_SUBSTEPS = 8


@dataclass(frozen=True)
class BABCSConfig:
    rollout_mode: str = "shadow"
    candidate_method: str = "ab2"
    absolute_tolerance: float = 1.0e-9
    relative_tolerance: float = 1.0e-6
    algebraic_residual_cap: float = 1.0e-8
    full_residual_cap: float = 1.0e-8
    predictor_reference_cap: float = 25.0
    embedded_error_cap: float = 25.0
    deferred_reference_bound_cap: float = 1.0e2
    anchor_reference_cap: float = 20.0
    anchor_embedded_error_cap: float = 1.25
    energy_absolute_tolerance: float = 1.0e-12
    energy_relative_tolerance: float = 1.0e-5
    energy_injection_cap: float = 2.0
    target_contraction: float = 0.8
    contraction_rate: float | None = None
    minimum_correction_gain: float = 0.25
    maximum_correction_gain: float = 1.0
    stiffness_limit: float = 0.8
    jacobian_safety_factor: float = 1.0
    maximum_step_ratio: float = 2.0
    reference_interval_steps: int = 1
    anchor_interval_steps: int = 16
    anchor_substeps: int = 4
    minimum_anchor_substeps: int = 2
    adaptive_anchor_refinement: bool = True
    minimum_step: float = 1.0e-15
    maximum_rejections: int = 12
    reference_method: str = "trapezoidal"
    startup_method: str = "backward_euler"
    reference_uncertainty_mode: str = "disabled"
    implicit_settings: ImplicitSettings = ImplicitSettings()

    def __post_init__(self) -> None:
        positive_values = (
            self.absolute_tolerance,
            self.relative_tolerance,
            self.algebraic_residual_cap,
            self.full_residual_cap,
            self.predictor_reference_cap,
            self.embedded_error_cap,
            self.deferred_reference_bound_cap,
            self.anchor_reference_cap,
            self.anchor_embedded_error_cap,
            self.energy_absolute_tolerance,
            self.energy_relative_tolerance,
            self.energy_injection_cap,
            self.stiffness_limit,
            self.jacobian_safety_factor,
            self.maximum_step_ratio,
            self.minimum_step,
        )
        if any(value <= 0.0 for value in positive_values):
            raise ValueError("BAB-CS tolerances and limits must be positive")
        if any(not math.isfinite(value) for value in positive_values):
            raise ValueError("BAB-CS tolerances and limits must be finite")
        if not 0.0 < self.target_contraction < 1.0:
            raise ValueError("target_contraction must lie strictly between zero and one")
        if self.contraction_rate is not None and (
            not math.isfinite(self.contraction_rate) or self.contraction_rate <= 0.0
        ):
            raise ValueError("contraction_rate must be positive and finite when configured")
        if not 0.0 <= self.minimum_correction_gain <= self.maximum_correction_gain <= 1.0:
            raise ValueError("correction gains must satisfy 0 <= min <= max <= 1")
        if (
            self.reference_interval_steps < 1
            or self.anchor_interval_steps < 1
            or self.anchor_substeps < 1
            or self.minimum_anchor_substeps < 1
        ):
            raise ValueError("reference intervals, anchor intervals, and substeps must be positive")
        if self.minimum_anchor_substeps > self.anchor_substeps:
            raise ValueError("minimum_anchor_substeps must not exceed anchor_substeps")
        if self.maximum_rejections < 1:
            raise ValueError("maximum_rejections must be positive")
        if self.rollout_mode not in {"disabled", "shadow", "active"}:
            raise ValueError("rollout_mode must be disabled, shadow, or active")
        if self.maximum_step_ratio < 1.0:
            raise ValueError("maximum_step_ratio must be at least one")
        valid_implicit_methods = {"backward_euler", "trapezoidal", "bdf2"}
        candidate_method = normalize_candidate_method(self.candidate_method)
        reference_method = self.reference_method.lower().replace("-", "_")
        if candidate_method not in CANDIDATE_METHODS:
            raise ValueError(
                "candidate_method must be explicit_euler, heun, rk23, ab2, "
                "backward_euler, trapezoidal, or bdf2"
            )
        if reference_method not in valid_implicit_methods:
            raise ValueError("reference_method must be backward_euler, trapezoidal, or bdf2")
        if self.startup_method.lower().replace("-", "_") not in valid_implicit_methods:
            raise ValueError("startup_method must be backward_euler, trapezoidal, or bdf2")
        if self.reference_uncertainty_mode not in {"disabled", "dual_resolution"}:
            raise ValueError(
                "reference_uncertainty_mode must be disabled or dual_resolution"
            )
        if self.reference_uncertainty_mode == "dual_resolution" and (
            self.rollout_mode != "active"
            or candidate_method != "heun"
            or reference_method != "trapezoidal"
            or self.startup_method.lower().replace("-", "_") != "trapezoidal"
        ):
            raise ValueError(
                "dual-resolution reference uncertainty currently requires active Heun "
                "with trapezoidal reference and startup methods"
            )
        if (
            self.rollout_mode != "disabled"
            and candidate_method in IMPLICIT_CANDIDATE_METHODS
            and candidate_method == reference_method
        ):
            raise ValueError(
                "an implicit candidate_method must differ from reference_method so the "
                "per-step defect estimate remains independent"
            )
        if self.reference_interval_steps > 1 and candidate_method not in {"ab2", "heun", "rk23"}:
            raise ValueError(
                "reference_interval_steps greater than one requires an embedded "
                "ab2, heun, or rk23 candidate"
            )


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
    previous_jacobian_norm: float | None = None
    reference_uncertainty: float = 0.0
    periodic_reanchors: int = 0
    safety_reanchors: int = 0
    implicit_fallbacks: int = 0
    rejected_steps: int = 0
    event_restart: bool = False


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
    residual_ratio: float = 0.0
    local_defect: float = 0.0
    reference_solve_count: int = 0
    reference_circuit_evaluations: int = 0
    reference_algebraic_iterations: int = 0
    predictor_projection_iterations: int = 0
    explicit_projection_count: int = 0
    differential_jacobian_evaluations: int = 0
    replay_steps: int = 0
    replay_reference_iterations: int = 0
    replay_circuit_evaluations: int = 0
    replay_algebraic_iterations: int = 0
    pre_reset_estimated_bound: float = 0.0
    periodic_reanchor: bool = False
    safety_reanchor: bool = False
    anchor_reference_error: float = 0.0
    candidate_method: str = "ab2"
    candidate_effective_method: str = ""
    candidate_order: int = 0
    candidate_used: bool = False
    embedded_error: float = 0.0
    embedded_defect: float = 0.0
    candidate_iterations: int = 0
    candidate_solve_count: int = 0
    candidate_circuit_evaluations: int = 0
    candidate_algebraic_iterations: int = 0
    dynamic_reference_checkpoint: bool = False
    replay_refinement_substeps: int = 0
    replay_refinement_retries: int = 0
    replay_embedded_error: float = 0.0
    pre_anchor_dynamic_state: tuple[float, ...] | None = None
    reference_discretization_defect: float = 0.0
    reference_uncertainty: float = 0.0
    pre_reset_reference_uncertainty: float = 0.0
    total_estimated_uncertainty: float = 0.0
    reference_refinement_solve_count: int = 0


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
        requested_method = normalize_candidate_method(self.config.candidate_method)
        if requested_method == "ab2" and not self._can_use_ab(history, step):
            return self._implicit_startup_step(circuit, state, history, step)

        scheduled_reference = (
            self.config.rollout_mode == "shadow"
            or self.config.reference_interval_steps == 1
            or history.accepted_steps % self.config.reference_interval_steps == 0
        )
        prepare_sparse_chord = (
            scheduled_reference
            or circuit.dynamic_size < DEFERRED_NATIVE_JACOBIAN_MINIMUM_SIZE
        )

        try:
            candidate_result = candidate_step(
                circuit,
                requested_method,
                current,
                step,
                previous_evaluation=history.previous_evaluation,
                previous_step=history.previous_step,
                implicit_settings=self.config.implicit_settings,
                prepare_sparse_chord=prepare_sparse_chord,
            )
        except CandidateUnavailable:
            return self._implicit_startup_step(circuit, state, history, step)
        except (CircuitSolveError, IntegrationError) as error:
            raise StepRejected(
                f"candidate solve failed: {error}",
                max(step * 0.5, self.config.minimum_step),
            ) from error

        if not finite_candidate_metrics(candidate_result):
            raise StepRejected(
                "non-finite candidate state",
                max(step * 0.5, self.config.minimum_step),
            )

        candidate = candidate_result.evaluation
        embedded_error = 0.0
        use_embedded_estimator = not (
            requested_method == "ab2" and self.config.reference_interval_steps == 1
        )
        if candidate_result.embedded_state is not None and use_embedded_estimator:
            embedded_error = self._scaled_state_error(
                candidate.dynamic_state,
                candidate_result.embedded_state,
            )
            if not math.isfinite(embedded_error) or embedded_error > self.config.embedded_error_cap:
                raise StepRejected(
                    f"embedded candidate cap exceeded: {embedded_error:.6g}",
                    max(step * 0.5, self.config.minimum_step),
                )

        reference_result = None
        reference = None
        predictor_error = 0.0
        reference_discretization_defect = 0.0
        reference_solve_count = 0
        reference_refinement_solve_count = 0
        if scheduled_reference:
            try:
                (
                    reference_result,
                    reference_discretization_defect,
                    reference_solve_count,
                    reference_refinement_solve_count,
                ) = self._reference_step_with_uncertainty(
                    circuit,
                    current,
                    step,
                    history,
                    candidate,
                )
            except (CircuitSolveError, IntegrationError) as error:
                raise StepRejected(
                    f"reference solve failed: {error}",
                    max(step * 0.5, self.config.minimum_step),
                ) from error
            reference = reference_result.evaluation

        current_jacobian_norm = candidate_result.base_jacobian_norm
        if current_jacobian_norm is None:
            current_jacobian_norm = circuit.differential_jacobian_norm_at_evaluation(current)
        differential_jacobian_evaluations = 1
        previous_jacobian_norm: float | None = None
        if requested_method == "ab2" and history.previous_jacobian_norm is None:
            assert history.previous_evaluation is not None
            previous_jacobian_norm = circuit.differential_jacobian_norm_at_evaluation(
                history.previous_evaluation
            )
            differential_jacobian_evaluations += 1
        elif requested_method == "ab2":
            previous_jacobian_norm = history.previous_jacobian_norm
        bounded_current_jacobian = self.config.jacobian_safety_factor * current_jacobian_norm
        bounded_previous_jacobian = (
            None
            if previous_jacobian_norm is None
            else self.config.jacobian_safety_factor * previous_jacobian_norm
        )
        stiffness_indicator = step * max(
            bounded_current_jacobian,
            bounded_previous_jacobian or 0.0,
        )
        predictor_amplification = candidate_amplification(
            candidate_result.effective_method,
            step,
            bounded_current_jacobian,
            previous_jacobian_norm=bounded_previous_jacobian,
            previous_step=history.previous_step,
        )
        if not math.isfinite(stiffness_indicator):
            raise StepRejected(
                "non-finite stiffness metric",
                max(step * 0.5, self.config.minimum_step),
            )
        amplification_domain_fallback = predictor_amplification is None
        if predictor_amplification is None:
            if stiffness_indicator <= self.config.stiffness_limit:
                raise StepRejected(
                    "candidate amplification domain exceeded",
                    max(step * 0.5, self.config.minimum_step),
                )
            predictor_amplification = max(1.0, 1.0 + stiffness_indicator)
        if not math.isfinite(predictor_amplification):
            raise StepRejected(
                "non-finite candidate amplification metric",
                max(step * 0.5, self.config.minimum_step),
            )
        projected_embedded_bound = (
            predictor_amplification * history.estimated_bound + embedded_error
        )
        dynamic_reference_checkpoint = (
            self.config.reference_interval_steps > 1
            and projected_embedded_bound > self.config.deferred_reference_bound_cap
        )
        force_reference = (
            scheduled_reference
            or stiffness_indicator > self.config.stiffness_limit
            or amplification_domain_fallback
            or dynamic_reference_checkpoint
        )
        if force_reference and reference_result is None:
            try:
                (
                    reference_result,
                    reference_discretization_defect,
                    reference_solve_count,
                    reference_refinement_solve_count,
                ) = self._reference_step_with_uncertainty(
                    circuit,
                    current,
                    step,
                    history,
                    candidate,
                )
            except (CircuitSolveError, IntegrationError) as error:
                raise StepRejected(
                    f"reference solve failed: {error}",
                    max(step * 0.5, self.config.minimum_step),
                ) from error
            reference = reference_result.evaluation
        if reference is not None:
            predictor_error = self._scaled_state_error(
                candidate.dynamic_state,
                reference.dynamic_state,
            )
            if (
                not math.isfinite(predictor_error)
                or predictor_error > self.config.predictor_reference_cap
            ):
                raise StepRejected(
                    f"predictor-reference cap exceeded: {predictor_error:.6g}",
                    max(step * 0.5, self.config.minimum_step),
                )

        reference_uncertainty = 0.0
        if self.config.reference_uncertainty_mode == "dual_resolution":
            reference_uncertainty = (
                predictor_amplification * history.reference_uncertainty
                + reference_discretization_defect
            )
            if not math.isfinite(reference_uncertainty):
                raise StepRejected(
                    "non-finite reference uncertainty metric",
                    max(step * 0.5, self.config.minimum_step),
                )

        fallback = False
        if reference is None:
            correction_gain = 0.0
            closed_loop_gain = predictor_amplification
            method = f"babcs_{requested_method}_embedded_fast"
        else:
            required_gain = 1.0 - self._target_contraction(step) / predictor_amplification
            correction_gain = min(
                self.config.maximum_correction_gain,
                max(self.config.minimum_correction_gain, required_gain),
            )
            method = f"babcs_{requested_method}"
            if self.config.rollout_mode == "shadow":
                correction_gain = 1.0
                method = "shadow_reference_authority"
            if stiffness_indicator > self.config.stiffness_limit or amplification_domain_fallback:
                correction_gain = 1.0
                method = "implicit_stiffness_fallback"
                fallback = True
            elif dynamic_reference_checkpoint:
                correction_gain = 1.0
                method = "implicit_bound_fallback"
                fallback = True

            closed_loop_gain = (1.0 - correction_gain) * predictor_amplification
            if closed_loop_gain >= 1.0:
                correction_gain = 1.0
                closed_loop_gain = 0.0
                method = "implicit_contraction_fallback"
                fallback = True

        explicit_projection_count = candidate_result.projection_count
        if reference is None:
            corrected = candidate
        elif correction_gain == 1.0:
            corrected = reference
        else:
            corrected_state = tuple(
                (1.0 - correction_gain) * candidate_value
                + correction_gain * reference_value
                for candidate_value, reference_value in zip(
                    candidate.dynamic_state,
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
                explicit_projection_count += 1
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
            if reference is None:
                raise StepRejected(
                    f"embedded fast-path energy cap exceeded: {energy_injection_ratio:.6g}",
                    max(step * 0.5, self.config.minimum_step),
                )
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

        corrected_reference_error = (
            0.0
            if reference is None
            else self._scaled_state_error(
                corrected.dynamic_state,
                reference.dynamic_state,
            )
        )
        residual_ratio = max(
            algebraic_residual / self.config.algebraic_residual_cap,
            full_residual / self.config.full_residual_cap,
        )
        embedded_defect = embedded_error if reference is None else 0.0
        local_defect = (
            embedded_defect if reference is None else corrected_reference_error
        ) + residual_ratio
        estimated_bound = closed_loop_gain * history.estimated_bound + local_defect
        if (
            self.config.reference_interval_steps > 1
            and estimated_bound > self.config.deferred_reference_bound_cap
            and reference is not None
            and correction_gain < 1.0
        ):
            corrected = reference
            dynamic_reference_checkpoint = True
            correction_gain = 1.0
            closed_loop_gain = 0.0
            method = "implicit_bound_fallback"
            fallback = True
            energy_balance_error, energy_injection_ratio = self._energy_metrics(
                current,
                corrected,
                step,
            )
            algebraic_residual = corrected.algebraic.residual_norm
            full_residual = circuit.full_residual_norm(corrected)
            if not all(
                math.isfinite(value)
                for value in (
                    energy_balance_error,
                    energy_injection_ratio,
                    algebraic_residual,
                    full_residual,
                )
            ):
                raise StepRejected(
                    "non-finite bound fallback metric",
                    max(step * 0.5, self.config.minimum_step),
                )
            if energy_injection_ratio > self.config.energy_injection_cap:
                raise StepRejected(
                    f"bound fallback energy cap exceeded: {energy_injection_ratio:.6g}",
                    max(step * 0.5, self.config.minimum_step),
                )
            if algebraic_residual > self.config.algebraic_residual_cap:
                raise StepRejected(
                    f"bound fallback algebraic residual cap exceeded: {algebraic_residual:.6g}",
                    max(step * 0.5, self.config.minimum_step),
                )
            if full_residual > self.config.full_residual_cap:
                raise StepRejected(
                    f"bound fallback full residual cap exceeded: {full_residual:.6g}",
                    max(step * 0.5, self.config.minimum_step),
                )
            corrected_reference_error = 0.0
            embedded_defect = 0.0
            residual_ratio = max(
                algebraic_residual / self.config.algebraic_residual_cap,
                full_residual / self.config.full_residual_cap,
            )
            local_defect = residual_ratio
            estimated_bound = local_defect
        if (
            reference is None
            and estimated_bound > self.config.deferred_reference_bound_cap
        ):
            raise StepRejected(
                f"deferred-reference bound cap exceeded: {estimated_bound:.6g}",
                max(step * 0.5, self.config.minimum_step),
            )
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
            previous_jacobian_norm=current_jacobian_norm,
            estimated_bound=estimated_bound,
            reference_uncertainty=reference_uncertainty,
            accepted_steps=history.accepted_steps + 1,
            steps_since_anchor=history.steps_since_anchor + 1,
            implicit_fallbacks=history.implicit_fallbacks + int(fallback),
            event_restart=False,
        )
        metrics = StepMetrics(
            method=method,
            ab_used=requested_method == "ab2",
            reference_method=(
                "deferred_to_periodic_anchor"
                if reference_result is None
                else reference_result.method
            ),
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
            reference_iterations=(0 if reference_result is None else reference_result.iterations),
            projection_iterations=corrected.algebraic.iterations,
            residual_ratio=residual_ratio,
            local_defect=local_defect,
            reference_solve_count=reference_solve_count,
            reference_circuit_evaluations=(
                0 if reference_result is None else reference_result.circuit_evaluations
            ),
            reference_algebraic_iterations=(
                0 if reference_result is None else reference_result.algebraic_iterations
            ),
            predictor_projection_iterations=candidate_result.algebraic_iterations,
            explicit_projection_count=explicit_projection_count,
            differential_jacobian_evaluations=differential_jacobian_evaluations,
            pre_reset_estimated_bound=estimated_bound,
            candidate_method=requested_method,
            candidate_effective_method=candidate_result.effective_method,
            candidate_order=candidate_result.order,
            candidate_used=True,
            embedded_error=embedded_error,
            embedded_defect=embedded_defect,
            candidate_iterations=candidate_result.iterations,
            candidate_solve_count=candidate_result.solve_count,
            candidate_circuit_evaluations=candidate_result.circuit_evaluations,
            candidate_algebraic_iterations=candidate_result.algebraic_iterations,
            dynamic_reference_checkpoint=dynamic_reference_checkpoint,
            reference_discretization_defect=reference_discretization_defect,
            reference_uncertainty=reference_uncertainty,
            pre_reset_reference_uncertainty=reference_uncertainty,
            total_estimated_uncertainty=estimated_bound + reference_uncertainty,
            reference_refinement_solve_count=reference_refinement_solve_count,
        )
        return StepResult(new_state, new_history, metrics)

    def step_to_event(
        self,
        circuit: Circuit,
        state: SimulationState,
        history: BABCSHistory,
        step: float,
    ) -> StepResult:
        return self._implicit_authority_step(circuit, state, history, step)

    def _reference_step_with_uncertainty(
        self,
        circuit: Circuit,
        current: CircuitEvaluation,
        step: float,
        history: BABCSHistory,
        candidate: CircuitEvaluation | None,
    ) -> tuple[ImplicitStepResult, float, int, int]:
        coarse = implicit_step(
            circuit,
            self.config.reference_method,
            current,
            step,
            previous_state=(
                history.previous_evaluation.dynamic_state
                if history.previous_evaluation is not None
                else None
            ),
            previous_step=history.previous_step,
            initial_guess=(None if candidate is None else candidate.dynamic_state),
            initial_evaluation=candidate,
            settings=self.config.implicit_settings,
        )
        if self.config.reference_uncertainty_mode != "dual_resolution":
            return coarse, 0.0, 1, 0

        half_step = 0.5 * step
        if half_step < self.config.minimum_step:
            raise IntegrationError(
                "dual-resolution reference refinement is below the configured minimum step"
            )
        endpoint_guess = candidate if candidate is not None else coarse.evaluation
        midpoint_guess = tuple(
            0.5 * (current_value + endpoint_value)
            for current_value, endpoint_value in zip(
                current.dynamic_state,
                endpoint_guess.dynamic_state,
                strict=True,
            )
        )
        first_half = implicit_step(
            circuit,
            self.config.reference_method,
            current,
            half_step,
            initial_guess=midpoint_guess,
            initial_algebraic_guess=current.algebraic.unknowns,
            settings=self.config.implicit_settings,
        )
        second_half = implicit_step(
            circuit,
            self.config.reference_method,
            first_half.evaluation,
            half_step,
            initial_guess=endpoint_guess.dynamic_state,
            initial_algebraic_guess=endpoint_guess.algebraic.unknowns,
            settings=self.config.implicit_settings,
        )
        defect = self._scaled_state_error(
            coarse.evaluation.dynamic_state,
            second_half.evaluation.dynamic_state,
        )
        if not math.isfinite(defect):
            raise IntegrationError(
                "dual-resolution reference produced a non-finite discrepancy"
            )
        refined = ImplicitStepResult(
            evaluation=second_half.evaluation,
            method=second_half.method,
            iterations=(
                coarse.iterations + first_half.iterations + second_half.iterations
            ),
            residual_norm=second_half.residual_norm,
            circuit_evaluations=(
                coarse.circuit_evaluations
                + first_half.circuit_evaluations
                + second_half.circuit_evaluations
            ),
            algebraic_iterations=(
                coarse.algebraic_iterations
                + first_half.algebraic_iterations
                + second_half.algebraic_iterations
            ),
        )
        return refined, defect, 3, 2

    def _implicit_authority_step(
        self,
        circuit: Circuit,
        state: SimulationState,
        history: BABCSHistory,
        step: float,
    ) -> StepResult:
        try:
            if self.config.reference_uncertainty_mode == "dual_resolution":
                (
                    result,
                    reference_discretization_defect,
                    reference_solve_count,
                    reference_refinement_solve_count,
                ) = self._reference_step_with_uncertainty(
                    circuit,
                    state.evaluation,
                    step,
                    history,
                    None,
                )
            else:
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
                reference_discretization_defect = 0.0
                reference_solve_count = 1
                reference_refinement_solve_count = 0
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
        reference_uncertainty = (
            history.reference_uncertainty + reference_discretization_defect
        )
        new_state = SimulationState(evaluation, step, "implicit_authority")
        new_history = replace(
            history,
            previous_evaluation=state.evaluation,
            previous_step=step,
            previous_jacobian_norm=None,
            estimated_bound=0.0,
            reference_uncertainty=reference_uncertainty,
            accepted_steps=history.accepted_steps + 1,
            steps_since_anchor=history.steps_since_anchor + 1,
            implicit_fallbacks=history.implicit_fallbacks + 1,
            event_restart=False,
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
            reference_solve_count=reference_solve_count,
            reference_circuit_evaluations=result.circuit_evaluations,
            reference_algebraic_iterations=result.algebraic_iterations,
            reference_discretization_defect=reference_discretization_defect,
            reference_uncertainty=reference_uncertainty,
            pre_reset_reference_uncertainty=reference_uncertainty,
            total_estimated_uncertainty=reference_uncertainty,
            reference_refinement_solve_count=reference_refinement_solve_count,
        )
        return StepResult(new_state, new_history, metrics)

    def _implicit_startup_step(
        self,
        circuit: Circuit,
        state: SimulationState,
        history: BABCSHistory,
        step: float,
    ) -> StepResult:
        startup_method = (
            self.config.reference_method
            if history.event_restart
            else self.config.startup_method
        )
        try:
            if self.config.reference_uncertainty_mode == "dual_resolution":
                (
                    result,
                    reference_discretization_defect,
                    reference_solve_count,
                    reference_refinement_solve_count,
                ) = self._reference_step_with_uncertainty(
                    circuit,
                    state.evaluation,
                    step,
                    history,
                    None,
                )
            else:
                result = implicit_step(
                    circuit,
                    startup_method,
                    state.evaluation,
                    step,
                    settings=self.config.implicit_settings,
                )
                reference_discretization_defect = 0.0
                reference_solve_count = 1
                reference_refinement_solve_count = 0
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

        reference_uncertainty = (
            history.reference_uncertainty + reference_discretization_defect
        )

        new_state = SimulationState(evaluation, step, f"{result.method}_startup")
        new_history = replace(
            history,
            previous_evaluation=state.evaluation,
            previous_step=step,
            previous_jacobian_norm=None,
            estimated_bound=0.0,
            reference_uncertainty=reference_uncertainty,
            accepted_steps=history.accepted_steps + 1,
            steps_since_anchor=history.steps_since_anchor + 1,
            implicit_fallbacks=history.implicit_fallbacks + 1,
            event_restart=False,
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
            reference_solve_count=reference_solve_count,
            reference_circuit_evaluations=result.circuit_evaluations,
            reference_algebraic_iterations=result.algebraic_iterations,
            reference_discretization_defect=reference_discretization_defect,
            reference_uncertainty=reference_uncertainty,
            pre_reset_reference_uncertainty=reference_uncertainty,
            total_estimated_uncertainty=reference_uncertainty,
            reference_refinement_solve_count=reference_refinement_solve_count,
        )
        return StepResult(new_state, new_history, metrics)

    def reanchor_if_due(
        self,
        circuit: Circuit,
        result: StepResult,
        *,
        force: bool = False,
    ) -> StepResult:
        history = result.history
        if not force and history.steps_since_anchor < self.config.anchor_interval_steps:
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
        reference_method = self.config.reference_method.lower().replace("-", "_")
        replay_refinement_substeps = (
            max(self.config.anchor_substeps, MINIMUM_EVENT_ANCHOR_SUBSTEPS)
            if force
            else self._anchor_refinement_substeps(circuit)
        )
        adaptive_replay = (
            not force
            and self.config.adaptive_anchor_refinement
            and self.config.minimum_anchor_substeps < self.config.anchor_substeps
            and (
                (
                    reference_method == "bdf2"
                    and bool(circuit.capacitors)
                    and not circuit.inductors
                    and circuit._has_piecewise_switch_schedule()
                )
                or (
                    reference_method == "trapezoidal"
                    and bool(circuit.capacitors)
                    and bool(circuit.inductors)
                )
            )
        )
        replay_local_error_order = 2.0 if reference_method == "bdf2" else 3.0
        replay_refinement_retries = 0
        replay_steps = 0
        replay_reference_iterations = 0
        replay_circuit_evaluations = 0
        replay_algebraic_iterations = 0
        while True:
            maximum_step = window / max(
                history.steps_since_anchor * replay_refinement_substeps,
                1,
            )
            maximum_step = max(maximum_step, self.config.minimum_step)
            try:
                replay = integrate_reference_window_with_stats(
                    circuit,
                    anchor,
                    target_times,
                    maximum_step,
                    method=self.config.reference_method,
                    settings=self.config.implicit_settings,
                    error_absolute_tolerance=(
                        self.config.absolute_tolerance if adaptive_replay else None
                    ),
                    error_relative_tolerance=(
                        self.config.relative_tolerance if adaptive_replay else None
                    ),
                    energy_absolute_tolerance=self.config.energy_absolute_tolerance,
                    energy_relative_tolerance=self.config.energy_relative_tolerance,
                    exact_target_projection=force,
                )
            except (CircuitSolveError, IntegrationError) as error:
                raise StepRejected(
                    f"independent re-anchor failed: {error}",
                    max(result.state.accepted_step * 0.5, self.config.minimum_step),
                ) from error
            replay_steps += replay.steps
            replay_reference_iterations += replay.reference_iterations
            replay_circuit_evaluations += replay.circuit_evaluations
            replay_algebraic_iterations += replay.algebraic_iterations
            if not adaptive_replay:
                break
            embedded_error = replay.maximum_embedded_error
            if not math.isfinite(embedded_error):
                raise StepRejected(
                    "non-finite independent replay accuracy metric",
                    max(result.state.accepted_step * 0.5, self.config.minimum_step),
                )
            if embedded_error <= self.config.anchor_embedded_error_cap:
                break
            if replay_refinement_substeps >= self.config.anchor_substeps:
                break
            scale = (
                embedded_error / self.config.anchor_embedded_error_cap
            ) ** (1.0 / replay_local_error_order)
            replay_refinement_substeps = min(
                self.config.anchor_substeps,
                max(
                    replay_refinement_substeps + 1,
                    math.ceil(replay_refinement_substeps * scale),
                ),
            )
            replay_refinement_retries += 1

        reference_states = replay.evaluations
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
        energy_balance_error = replay.cumulative_energy_balance_error
        energy_injection_ratio = replay.maximum_energy_injection_ratio
        algebraic_residual = anchored_current.algebraic.residual_norm
        full_residual = circuit.full_residual_norm(anchored_current)
        if not all(
            math.isfinite(value)
            for value in (
                energy_balance_error,
                energy_injection_ratio,
                algebraic_residual,
                full_residual,
            )
        ):
            raise StepRejected(
                "non-finite independent re-anchor metric",
                max(result.state.accepted_step * 0.5, self.config.minimum_step),
            )
        if energy_injection_ratio > self.config.energy_injection_cap:
            raise StepRejected(
                f"independent re-anchor energy cap exceeded: {energy_injection_ratio:.6g}",
                max(result.state.accepted_step * 0.5, self.config.minimum_step),
            )
        if algebraic_residual > self.config.algebraic_residual_cap:
            raise StepRejected(
                f"independent re-anchor algebraic residual cap exceeded: {algebraic_residual:.6g}",
                max(result.state.accepted_step * 0.5, self.config.minimum_step),
            )
        if full_residual > self.config.full_residual_cap:
            raise StepRejected(
                f"independent re-anchor full residual cap exceeded: {full_residual:.6g}",
                max(result.state.accepted_step * 0.5, self.config.minimum_step),
            )
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
            previous_jacobian_norm=None,
            estimated_bound=0.0,
            reference_uncertainty=history.reference_uncertainty,
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
            algebraic_residual=algebraic_residual,
            full_residual=full_residual,
            energy_balance_error=energy_balance_error,
            energy_injection_ratio=energy_injection_ratio,
            estimated_bound=0.0,
            residual_ratio=0.0,
            local_defect=0.0,
            reference_uncertainty=history.reference_uncertainty,
            pre_reset_reference_uncertainty=history.reference_uncertainty,
            total_estimated_uncertainty=history.reference_uncertainty,
            certified_contractive=True,
            periodic_reanchor=True,
            safety_reanchor=safety_reanchor,
            anchor_reference_error=anchor_error,
            replay_steps=replay_steps,
            replay_reference_iterations=replay_reference_iterations,
            replay_circuit_evaluations=replay_circuit_evaluations,
            replay_algebraic_iterations=replay_algebraic_iterations,
            replay_refinement_substeps=replay_refinement_substeps,
            replay_refinement_retries=replay_refinement_retries,
            replay_embedded_error=replay.maximum_embedded_error,
            pre_anchor_dynamic_state=current.dynamic_state,
        )
        return StepResult(new_state, new_history, metrics)

    def reset_history(
        self,
        state: SimulationState,
        history: BABCSHistory,
    ) -> BABCSHistory:
        del state
        return replace(
            history,
            previous_evaluation=None,
            previous_step=None,
            previous_jacobian_norm=None,
            estimated_bound=0.0,
            event_restart=True,
        )

    def record_rejection(self, history: BABCSHistory) -> BABCSHistory:
        return replace(history, rejected_steps=history.rejected_steps + 1)

    def _can_use_ab(self, history: BABCSHistory, step: float) -> bool:
        if history.previous_evaluation is None or history.previous_step is None:
            return False
        ratio = step / history.previous_step
        return 1.0 / self.config.maximum_step_ratio <= ratio <= self.config.maximum_step_ratio

    def _target_contraction(self, step: float) -> float:
        if self.config.contraction_rate is None:
            return self.config.target_contraction
        return math.exp(-self.config.contraction_rate * step)

    def _anchor_refinement_substeps(self, circuit: Circuit) -> int:
        if not self.config.adaptive_anchor_refinement:
            return self.config.anchor_substeps
        reference_method = self.config.reference_method.lower().replace("-", "_")
        if reference_method == "bdf2":
            if (
                not circuit.capacitors
                or circuit.inductors
                or not circuit._has_piecewise_switch_schedule()
            ):
                return self.config.anchor_substeps
        elif reference_method != "trapezoidal":
            return self.config.anchor_substeps
        return self.config.minimum_anchor_substeps

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
        return energy_balance_metrics(
            current,
            candidate,
            step,
            self.config.energy_absolute_tolerance,
            self.config.energy_relative_tolerance,
        )


BoundedIntegrator = BoundedAdamsBashforthIntegrator
