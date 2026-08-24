from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .linalg import SingularMatrixError, finite_difference_jacobian, norm_inf, solve_linear
from .model import Circuit, CircuitEvaluation, CircuitSolveError


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


def implicit_step(
    circuit: Circuit,
    method: str,
    current: CircuitEvaluation,
    step: float,
    *,
    previous_state: Sequence[float] | None = None,
    previous_step: float | None = None,
    initial_guess: Sequence[float] | None = None,
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

    def evaluate(
        time: float,
        state: Sequence[float],
        algebraic_guess: Sequence[float] | None,
    ) -> CircuitEvaluation:
        nonlocal circuit_evaluations, algebraic_iterations
        evaluation = circuit.evaluate(time, state, algebraic_guess)
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
    if initial_guess is None:
        candidate = [
            state_value + step * derivative
            for state_value, derivative in zip(current.dynamic_state, current.derivative, strict=True)
        ]
    else:
        candidate = [float(value) for value in initial_guess]
    if len(candidate) != circuit.dynamic_size:
        raise ValueError("implicit initial guess has the wrong size")

    algebraic_guess = current.algebraic.unknowns

    def step_residual(state: list[float]) -> list[float]:
        nonlocal algebraic_guess
        evaluation = evaluate(target_time, state, algebraic_guess)
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

    residual = step_residual(candidate)
    for iteration in range(settings.max_iterations + 1):
        residual_norm = norm_inf(residual)
        tolerance = settings.absolute_tolerance + settings.relative_tolerance * max(
            norm_inf(candidate), norm_inf(current_state), 1.0
        )
        if residual_norm <= tolerance:
            evaluation = evaluate(target_time, candidate, algebraic_guess)
            return ImplicitStepResult(
                evaluation,
                method_name,
                iteration,
                residual_norm,
                circuit_evaluations,
                algebraic_iterations,
            )
        if iteration == settings.max_iterations:
            break

        try:
            jacobian = finite_difference_jacobian(step_residual, candidate, residual)
            update = solve_linear(jacobian, [-value for value in residual])
        except (SingularMatrixError, CircuitSolveError) as error:
            raise IntegrationError(
                f"{method_name} Newton system failed at t={target_time:.17g}: {error}"
            ) from error

        damping = 1.0
        accepted = False
        while damping >= settings.minimum_damping:
            trial = [value + damping * delta for value, delta in zip(candidate, update, strict=True)]
            try:
                trial_residual = step_residual(trial)
            except CircuitSolveError:
                damping *= 0.5
                continue
            if norm_inf(trial_residual) < residual_norm:
                candidate = trial
                residual = trial_residual
                accepted = True
                break
            damping *= 0.5
        if not accepted:
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
) -> ReferenceWindowResult:
    if maximum_step <= 0.0:
        raise ValueError("reference maximum step must be positive")
    if any(right <= left for left, right in zip(target_times, target_times[1:])):
        raise ValueError("reference target times must be strictly increasing")
    if target_times and target_times[0] <= initial.time:
        raise ValueError("reference target times must follow the initial state")

    current = initial
    outputs: list[CircuitEvaluation] = []
    steps = 0
    reference_iterations = 0
    circuit_evaluations = 0
    algebraic_iterations = 0
    for target_time in target_times:
        while current.time < target_time:
            remaining = target_time - current.time
            step = min(maximum_step, remaining)
            if step <= 16.0 * max(abs(current.time), abs(target_time), 1.0) * 2.220446049250313e-16:
                break
            result = implicit_step(circuit, method, current, step, settings=settings)
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
    )
