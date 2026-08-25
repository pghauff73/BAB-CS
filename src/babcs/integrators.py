from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .linalg import (
    SingularMatrixError,
    finite_difference_jacobian,
    norm_inf,
    solve_factored,
    solve_linear,
    weighted_rms,
)
from .model import Circuit, CircuitEvaluation, CircuitSolveError


SPARSE_CHORD_MAXIMUM_RESIDUAL_RATIO = 0.9


class IntegrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ImplicitSettings:
    absolute_tolerance: float = 1.0e-10
    relative_tolerance: float = 1.0e-8
    max_iterations: int = 20
    minimum_damping: float = 2.0**-14

    def __post_init__(self) -> None:
        if not all(math.isfinite(value) for value in (self.absolute_tolerance, self.relative_tolerance)):
            raise ValueError("implicit tolerances must be finite")
        if self.absolute_tolerance <= 0.0 or self.relative_tolerance <= 0.0:
            raise ValueError("implicit tolerances must be positive")
        if not math.isfinite(self.minimum_damping):
            raise ValueError("implicit minimum_damping must be finite")
        if self.max_iterations < 0:
            raise ValueError("implicit max_iterations must be non-negative")
        if not 0.0 < self.minimum_damping <= 1.0:
            raise ValueError("implicit minimum_damping must lie in (0, 1]")


@dataclass(frozen=True)
class ImplicitStepResult:
    evaluation: CircuitEvaluation
    method: str
    iterations: int
    residual_norm: float
    circuit_evaluations: int
    algebraic_iterations: int


@dataclass(frozen=True)
class ReferenceWindowResult:
    evaluations: tuple[CircuitEvaluation, ...]
    steps: int
    reference_iterations: int
    circuit_evaluations: int
    algebraic_iterations: int
    maximum_embedded_error: float


def implicit_step(
    circuit: Circuit,
    method: str,
    current: CircuitEvaluation,
    step: float,
    *,
    previous_state: Sequence[float] | None = None,
    previous_step: float | None = None,
    initial_guess: Sequence[float] | None = None,
    initial_algebraic_guess: Sequence[float] | None = None,
    initial_evaluation: CircuitEvaluation | None = None,
    settings: ImplicitSettings = ImplicitSettings(),
) -> ImplicitStepResult:
    if step <= 0.0:
        raise ValueError("integration step must be positive")
    method_name = method.lower().replace("-", "_")
    if method_name not in {"backward_euler", "trapezoidal", "bdf2"}:
        raise ValueError(f"unknown implicit method: {method}")
    if method_name == "bdf2" and (previous_state is None or previous_step is None):
        method_name = "backward_euler"

    target_time = current.time + step
    circuit_evaluations = 0
    algebraic_iterations = 0
    reusable_initial_evaluation = initial_evaluation

    def evaluate(
        time: float,
        state: Sequence[float],
        algebraic_guess: Sequence[float] | None,
    ) -> CircuitEvaluation:
        nonlocal algebraic_iterations, circuit_evaluations, reusable_initial_evaluation
        state_values = tuple(state)
        if (
            reusable_initial_evaluation is not None
            and reusable_initial_evaluation.time == time
            and reusable_initial_evaluation.dynamic_state == state_values
        ):
            evaluation = reusable_initial_evaluation
            reusable_initial_evaluation = None
            return evaluation
        evaluation = circuit.evaluate(time, state_values, algebraic_guess)
        circuit_evaluations += 1
        algebraic_iterations += evaluation.algebraic.iterations
        return evaluation

    if circuit.dynamic_size == 0:
        evaluation = evaluate(target_time, (), current.algebraic.unknowns)
        return ImplicitStepResult(
            evaluation,
            method_name,
            0,
            evaluation.algebraic.residual_norm,
            circuit_evaluations,
            algebraic_iterations,
        )

    current_state = list(current.dynamic_state)
    euler_candidate = [
        state_value + step * derivative
        for state_value, derivative in zip(current.dynamic_state, current.derivative, strict=True)
    ]
    if initial_guess is None:
        candidate = list(euler_candidate)
    else:
        candidate = list(map(float, initial_guess))
    if len(candidate) != circuit.dynamic_size:
        raise ValueError("implicit initial guess has the wrong size")
    if initial_evaluation is not None and (
        initial_evaluation.time != target_time
        or initial_evaluation.dynamic_state != tuple(candidate)
    ):
        raise ValueError("implicit initial evaluation does not match its initial guess")

    algebraic_guess = (
        current.algebraic.unknowns
        if initial_algebraic_guess is None
        else tuple(map(float, initial_algebraic_guess))
    )
    if len(algebraic_guess) != circuit.algebraic_size:
        raise ValueError("implicit algebraic initial guess has the wrong size")
    last_evaluation: CircuitEvaluation | None = None
    sparse_chord_available = True
    predictor_restart_available = initial_guess is not None
    algebraic_predictor_restart_available = initial_algebraic_guess is not None

    def restart_from_euler_predictor() -> None:
        nonlocal algebraic_guess, candidate, last_evaluation, predictor_restart_available
        candidate = list(euler_candidate)
        algebraic_guess = current.algebraic.unknowns
        last_evaluation = None
        predictor_restart_available = False

    def step_residual(state: list[float]) -> list[float]:
        nonlocal algebraic_guess, last_evaluation
        evaluation = evaluate(target_time, state, algebraic_guess)
        last_evaluation = evaluation
        algebraic_guess = evaluation.algebraic.unknowns
        if method_name == "backward_euler":
            return [
                new_value - old_value - step * derivative
                for new_value, old_value, derivative in zip(
                    state,
                    current.dynamic_state,
                    evaluation.derivative,
                    strict=True,
                )
            ]
        if method_name == "trapezoidal":
            return [
                new_value - old_value - 0.5 * step * (old_derivative + new_derivative)
                for new_value, old_value, old_derivative, new_derivative in zip(
                    state,
                    current.dynamic_state,
                    current.derivative,
                    evaluation.derivative,
                    strict=True,
                )
            ]

        assert previous_state is not None
        assert previous_step is not None
        ratio = step / previous_step
        coefficient_new = (1.0 + 2.0 * ratio) / (1.0 + ratio)
        coefficient_current = -(1.0 + ratio)
        coefficient_previous = ratio * ratio / (1.0 + ratio)
        return [
            coefficient_new * new_value
            + coefficient_current * old_value
            + coefficient_previous * previous_value
            - step * derivative
            for new_value, old_value, previous_value, derivative in zip(
                state,
                current.dynamic_state,
                previous_state,
                evaluation.derivative,
                strict=True,
            )
        ]

    try:
        residual = step_residual(candidate)
    except CircuitSolveError:
        if not algebraic_predictor_restart_available:
            raise
        algebraic_guess = current.algebraic.unknowns
        last_evaluation = None
        residual = step_residual(candidate)
    for iteration in range(settings.max_iterations + 1):
        assert last_evaluation is not None
        residual_norm = norm_inf(residual)
        tolerance = settings.absolute_tolerance + settings.relative_tolerance * max(
            last_evaluation.dynamic_state_norm,
            current.dynamic_state_norm,
            1.0,
        )
        if residual_norm <= tolerance:
            assert last_evaluation.dynamic_state == tuple(candidate)
            return ImplicitStepResult(
                last_evaluation,
                method_name,
                iteration,
                residual_norm,
                circuit_evaluations,
                algebraic_iterations,
            )
        if iteration == settings.max_iterations:
            break

        algebraic_update: tuple[float, ...] | None = None
        algebraic_update_base: tuple[float, ...] | None = None
        sparse_chord_update = False
        try:
            if type(circuit) is Circuit:
                assert last_evaluation is not None
                if method_name == "backward_euler":
                    state_coefficient = 1.0
                    derivative_coefficient = step
                elif method_name == "trapezoidal":
                    state_coefficient = 1.0
                    derivative_coefficient = 0.5 * step
                else:
                    assert previous_step is not None
                    ratio = step / previous_step
                    state_coefficient = (1.0 + 2.0 * ratio) / (1.0 + ratio)
                    derivative_coefficient = step
                factorization = circuit.linear_implicit_factorization(
                    last_evaluation,
                    state_coefficient,
                    derivative_coefficient,
                )
                if factorization is not None:
                    update = solve_factored(factorization, [-value for value in residual])
                else:
                    coupled_update = circuit.sparse_implicit_update(
                        last_evaluation,
                        state_coefficient,
                        derivative_coefficient,
                        residual,
                        allow_chord=(
                            sparse_chord_available
                            and iteration < settings.max_iterations - 1
                        ),
                    )
                    if coupled_update is not None:
                        update = list(coupled_update.dynamic_update)
                        algebraic_update = coupled_update.algebraic_update
                        algebraic_update_base = last_evaluation.algebraic.unknowns
                        sparse_chord_update = coupled_update.requires_contraction
                        if sparse_chord_update:
                            sparse_chord_available = False
                    else:
                        differential_jacobian = circuit.differential_jacobian_at_evaluation(
                            last_evaluation
                        )
                        jacobian = [
                            [
                                (state_coefficient if row == column else 0.0)
                                - derivative_coefficient * differential_jacobian[row][column]
                                for column in range(circuit.dynamic_size)
                            ]
                            for row in range(circuit.dynamic_size)
                        ]
                        update = solve_linear(
                            jacobian,
                            [-value for value in residual],
                            backend=circuit.linear_backend,
                        )
            else:
                jacobian = finite_difference_jacobian(step_residual, candidate, residual)
                update = solve_linear(jacobian, [-value for value in residual])
                sparse_chord_update = False
        except (SingularMatrixError, CircuitSolveError) as error:
            if predictor_restart_available:
                restart_from_euler_predictor()
                try:
                    residual = step_residual(candidate)
                except CircuitSolveError as restart_error:
                    raise IntegrationError(
                        f"{method_name} predictor restart failed at t={target_time:.17g}: "
                        f"{restart_error}"
                    ) from restart_error
                continue
            raise IntegrationError(
                f"{method_name} Newton system failed at t={target_time:.17g}: {error}"
            ) from error

        damping = 1.0
        accepted = False
        while damping >= settings.minimum_damping:
            trial = [value + damping * delta for value, delta in zip(candidate, update, strict=True)]
            if algebraic_update is not None:
                assert algebraic_update_base is not None
                trial_algebraic_guess = [
                    value + damping * delta
                    for value, delta in zip(
                        algebraic_update_base,
                        algebraic_update,
                        strict=True,
                    )
                ]
                saved_algebraic_guess = algebraic_guess
                algebraic_guess = trial_algebraic_guess
            else:
                saved_algebraic_guess = None
            try:
                trial_residual = step_residual(trial)
            except CircuitSolveError:
                if saved_algebraic_guess is not None:
                    algebraic_guess = saved_algebraic_guess
                damping *= 0.5
                continue
            maximum_trial_residual = residual_norm * (
                SPARSE_CHORD_MAXIMUM_RESIDUAL_RATIO
                if sparse_chord_update
                else 1.0
            )
            if norm_inf(trial_residual) < maximum_trial_residual:
                candidate = trial
                residual = trial_residual
                accepted = True
                break
            damping *= 0.5
        if not accepted:
            if sparse_chord_update:
                assert algebraic_update_base is not None
                algebraic_guess = algebraic_update_base
                last_evaluation = None
                try:
                    residual = step_residual(candidate)
                except CircuitSolveError as error:
                    raise IntegrationError(
                        f"{method_name} sparse chord fallback failed at "
                        f"t={target_time:.17g}: {error}"
                    ) from error
                continue
            if predictor_restart_available:
                restart_from_euler_predictor()
                try:
                    residual = step_residual(candidate)
                except CircuitSolveError as error:
                    raise IntegrationError(
                        f"{method_name} predictor restart failed at t={target_time:.17g}: {error}"
                    ) from error
                continue
            raise IntegrationError(
                f"{method_name} Newton line search failed at t={target_time:.17g}, "
                f"residual={residual_norm:.6g}"
            )

    raise IntegrationError(
        f"{method_name} did not converge at t={target_time:.17g}, residual={residual_norm:.6g}"
    )


def integrate_reference_window(
    circuit: Circuit,
    initial: CircuitEvaluation,
    target_times: Sequence[float],
    maximum_step: float,
    *,
    method: str = "trapezoidal",
    settings: ImplicitSettings = ImplicitSettings(),
) -> list[CircuitEvaluation]:
    return list(
        integrate_reference_window_with_stats(
            circuit,
            initial,
            target_times,
            maximum_step,
            method=method,
            settings=settings,
        ).evaluations
    )


def integrate_reference_window_with_stats(
    circuit: Circuit,
    initial: CircuitEvaluation,
    target_times: Sequence[float],
    maximum_step: float,
    *,
    method: str = "trapezoidal",
    settings: ImplicitSettings = ImplicitSettings(),
    error_absolute_tolerance: float | None = None,
    error_relative_tolerance: float | None = None,
) -> ReferenceWindowResult:
    if maximum_step <= 0.0:
        raise ValueError("reference maximum step must be positive")
    if any(right <= left for left, right in zip(target_times, target_times[1:])):
        raise ValueError("reference target times must be strictly increasing")
    if target_times and target_times[0] <= initial.time:
        raise ValueError("reference target times must follow the initial state")
    if (error_absolute_tolerance is None) != (error_relative_tolerance is None):
        raise ValueError("reference error tolerances must be configured together")
    if error_absolute_tolerance is not None and (
        error_absolute_tolerance <= 0.0
        or error_relative_tolerance is None
        or error_relative_tolerance <= 0.0
        or not math.isfinite(error_absolute_tolerance)
        or not math.isfinite(error_relative_tolerance)
    ):
        raise ValueError("reference error tolerances must be positive and finite")

    current = initial
    previous_evaluation: CircuitEvaluation | None = None
    older_evaluation: CircuitEvaluation | None = None
    third_previous_evaluation: CircuitEvaluation | None = None
    fourth_previous_evaluation: CircuitEvaluation | None = None
    previous_state: tuple[float, ...] | None = None
    previous_step: float | None = None
    older_step: float | None = None
    third_previous_step: float | None = None
    fourth_previous_step: float | None = None
    outputs: list[CircuitEvaluation] = []
    steps = 0
    reference_iterations = 0
    circuit_evaluations = 0
    algebraic_iterations = 0
    maximum_embedded_error = 0.0
    for target_time in target_times:
        while current.time < target_time:
            remaining = target_time - current.time
            step = min(maximum_step, remaining)
            if step <= 16.0 * max(abs(current.time), abs(target_time), 1.0) * 2.220446049250313e-16:
                break
            initial_guess = None
            initial_algebraic_guess = None
            if (
                older_evaluation is not None
                and previous_evaluation is not None
                and older_step is not None
                and previous_step is not None
                and _matching_replay_step(step, previous_step)
                and _matching_replay_step(previous_step, older_step)
            ):
                initial_guess = [
                    state_value
                    + step
                    * (
                        (23.0 / 12.0) * derivative
                        - (16.0 / 12.0) * previous_derivative
                        + (5.0 / 12.0) * older_derivative
                    )
                    for state_value, derivative, previous_derivative, older_derivative in zip(
                        current.dynamic_state,
                        current.derivative,
                        previous_evaluation.derivative,
                        older_evaluation.derivative,
                        strict=True,
                    )
                ]
            elif previous_evaluation is not None and previous_step is not None:
                ratio = step / previous_step
                initial_guess = [
                    state_value
                    + step
                    * (
                        (1.0 + 0.5 * ratio) * derivative
                        - 0.5 * ratio * previous_derivative
                    )
                    for state_value, derivative, previous_derivative in zip(
                        current.dynamic_state,
                        current.derivative,
                        previous_evaluation.derivative,
                        strict=True,
                    )
                ]
            if (
                circuit._uses_reusable_algebraic_inputs()
                and previous_evaluation is not None
                and older_evaluation is not None
                and third_previous_evaluation is not None
                and fourth_previous_evaluation is not None
                and previous_step is not None
                and older_step is not None
                and third_previous_step is not None
                and fourth_previous_step is not None
                and _matching_replay_step(step, previous_step)
                and _matching_replay_step(previous_step, older_step)
                and _matching_replay_step(older_step, third_previous_step)
                and _matching_replay_step(third_previous_step, fourth_previous_step)
            ):
                initial_algebraic_guess = [
                    5.0 * current_value
                    - 10.0 * previous_value
                    + 10.0 * older_value
                    - 5.0 * third_previous_value
                    + fourth_previous_value
                    for (
                        current_value,
                        previous_value,
                        older_value,
                        third_previous_value,
                        fourth_previous_value,
                    ) in zip(
                        current.algebraic.unknowns,
                        previous_evaluation.algebraic.unknowns,
                        older_evaluation.algebraic.unknowns,
                        third_previous_evaluation.algebraic.unknowns,
                        fourth_previous_evaluation.algebraic.unknowns,
                        strict=True,
                    )
                ]
            result = implicit_step(
                circuit,
                method,
                current,
                step,
                previous_state=previous_state,
                previous_step=previous_step,
                initial_guess=initial_guess,
                initial_algebraic_guess=initial_algebraic_guess,
                settings=settings,
            )
            if (
                error_absolute_tolerance is not None
                and previous_evaluation is not None
                and result.method == "trapezoidal"
            ):
                embedded_error = _trapezoidal_embedded_error(
                    previous_evaluation,
                    current,
                    result.evaluation,
                    error_absolute_tolerance,
                    error_relative_tolerance,
                )
                if math.isnan(embedded_error):
                    maximum_embedded_error = embedded_error
                elif embedded_error > maximum_embedded_error:
                    maximum_embedded_error = embedded_error
            fourth_previous_evaluation = third_previous_evaluation
            third_previous_evaluation = older_evaluation
            older_evaluation = previous_evaluation
            previous_evaluation = current
            fourth_previous_step = third_previous_step
            third_previous_step = older_step
            older_step = previous_step
            previous_state = current.dynamic_state
            previous_step = step
            current = result.evaluation
            steps += 1
            reference_iterations += result.iterations
            circuit_evaluations += result.circuit_evaluations
            algebraic_iterations += result.algebraic_iterations
        if abs(current.time - target_time) > 64.0 * max(abs(target_time), 1.0) * 2.220446049250313e-16:
            raise IntegrationError("reference replay failed to reach its target time")
        outputs.append(current)
    return ReferenceWindowResult(
        evaluations=tuple(outputs),
        steps=steps,
        reference_iterations=reference_iterations,
        circuit_evaluations=circuit_evaluations,
        algebraic_iterations=algebraic_iterations,
        maximum_embedded_error=maximum_embedded_error,
    )


def _matching_replay_step(left: float, right: float) -> bool:
    tolerance = 64.0 * max(abs(left), abs(right), 1.0) * 2.220446049250313e-16
    return abs(left - right) <= tolerance


def _trapezoidal_embedded_error(
    previous: CircuitEvaluation,
    current: CircuitEvaluation,
    following: CircuitEvaluation,
    absolute_tolerance: float,
    relative_tolerance: float,
) -> float:
    previous_step = current.time - previous.time
    step = following.time - current.time
    if previous_step <= 0.0 or step <= 0.0:
        return math.inf
    coefficient = step * step * step / (6.0 * (previous_step + step))
    defect = [
        coefficient
        * (
            (following_derivative - current_derivative) / step
            - (current_derivative - previous_derivative) / previous_step
        )
        for previous_derivative, current_derivative, following_derivative in zip(
            previous.derivative,
            current.derivative,
            following.derivative,
            strict=True,
        )
    ]
    return weighted_rms(
        defect,
        current.dynamic_state,
        following.dynamic_state,
        absolute_tolerance,
        relative_tolerance,
    )
