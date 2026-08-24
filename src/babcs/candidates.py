from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .integrators import ImplicitSettings, implicit_step
from .model import Circuit, CircuitEvaluation


EXPLICIT_CANDIDATE_METHODS = {"explicit_euler", "heun", "rk23", "ab2"}
IMPLICIT_CANDIDATE_METHODS = {"backward_euler", "trapezoidal", "bdf2"}
CANDIDATE_METHODS = EXPLICIT_CANDIDATE_METHODS | IMPLICIT_CANDIDATE_METHODS


class CandidateUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class CandidateStepResult:
    evaluation: CircuitEvaluation
    requested_method: str
    effective_method: str
    order: int
    embedded_state: tuple[float, ...] | None
    used_multistep: bool
    iterations: int
    solve_count: int
    circuit_evaluations: int
    algebraic_iterations: int
    projection_count: int
    base_jacobian_norm: float | None = None


def normalize_candidate_method(method: str) -> str:
    normalized = method.lower().replace("-", "_")
    aliases = {
        "euler": "explicit_euler",
        "forward_euler": "explicit_euler",
        "improved_euler": "heun",
        "explicit_trapezoidal": "heun",
        "bogacki_shampine": "rk23",
        "bogacki_shampine_23": "rk23",
        "adams_bashforth": "ab2",
        "adams_bashforth_2": "ab2",
        "backwardeuler": "backward_euler",
    }
    return aliases.get(normalized, normalized)


def candidate_order(method: str) -> int:
    normalized = normalize_candidate_method(method)
    return {
        "explicit_euler": 1,
        "heun": 2,
        "rk23": 3,
        "ab2": 2,
        "backward_euler": 1,
        "trapezoidal": 2,
        "bdf2": 2,
    }[normalized]


def candidate_step(
    circuit: Circuit,
    method: str,
    current: CircuitEvaluation,
    step: float,
    *,
    previous_evaluation: CircuitEvaluation | None = None,
    previous_step: float | None = None,
    implicit_settings: ImplicitSettings = ImplicitSettings(),
) -> CandidateStepResult:
    normalized = normalize_candidate_method(method)
    if normalized not in CANDIDATE_METHODS:
        raise ValueError(f"unsupported bounded candidate method: {method}")
    if normalized == "explicit_euler":
        return _explicit_euler_step(circuit, current, step)
    if normalized == "heun":
        return _heun_step(circuit, current, step)
    if normalized == "rk23":
        return _rk23_step(circuit, current, step)
    if normalized == "ab2":
        return _ab2_step(circuit, current, step, previous_evaluation, previous_step)

    result = implicit_step(
        circuit,
        normalized,
        current,
        step,
        previous_state=(
            previous_evaluation.dynamic_state if previous_evaluation is not None else None
        ),
        previous_step=previous_step,
        settings=implicit_settings,
    )
    return CandidateStepResult(
        evaluation=result.evaluation,
        requested_method=normalized,
        effective_method=result.method,
        order=candidate_order(result.method),
        embedded_state=None,
        used_multistep=result.method == "bdf2",
        iterations=result.iterations,
        solve_count=1,
        circuit_evaluations=result.circuit_evaluations,
        algebraic_iterations=result.algebraic_iterations,
        projection_count=0,
    )


def candidate_amplification(
    method: str,
    step: float,
    jacobian_norm: float,
    *,
    previous_jacobian_norm: float | None = None,
    previous_step: float | None = None,
) -> float | None:
    normalized = normalize_candidate_method(method)
    scaled = step * jacobian_norm
    if normalized == "explicit_euler":
        return max(1.0, 1.0 + scaled)
    if normalized == "heun":
        return max(1.0, 1.0 + scaled + 0.5 * scaled * scaled)
    if normalized == "rk23":
        return max(1.0, 1.0 + scaled + 0.5 * scaled**2 + scaled**3 / 6.0)
    if normalized == "ab2":
        if previous_jacobian_norm is None or previous_step is None:
            return None
        ratio = step / previous_step
        coefficient_current = 1.0 + 0.5 * ratio
        coefficient_previous = 0.5 * ratio
        return max(
            1.0,
            1.0
            + step
            * (
                coefficient_current * jacobian_norm
                + coefficient_previous * previous_jacobian_norm
            ),
        )
    if normalized == "backward_euler":
        denominator = 1.0 - scaled
        return None if denominator <= 0.0 else max(1.0, 1.0 / denominator)
    if normalized == "trapezoidal":
        denominator = 1.0 - 0.5 * scaled
        return None if denominator <= 0.0 else max(1.0, (1.0 + 0.5 * scaled) / denominator)
    if normalized == "bdf2":
        if previous_step is None:
            return candidate_amplification("backward_euler", step, jacobian_norm)
        ratio = step / previous_step
        coefficient_new = (1.0 + 2.0 * ratio) / (1.0 + ratio)
        coefficient_current = 1.0 + ratio
        coefficient_previous = ratio * ratio / (1.0 + ratio)
        denominator = coefficient_new - scaled
        if denominator <= 0.0:
            return None
        return max(1.0, (coefficient_current + coefficient_previous) / denominator)
    raise ValueError(f"unsupported bounded candidate method: {method}")


def _explicit_euler_step(
    circuit: Circuit,
    current: CircuitEvaluation,
    step: float,
) -> CandidateStepResult:
    candidate_state = tuple(
        value + step * derivative
        for value, derivative in zip(current.dynamic_state, current.derivative, strict=True)
    )
    evaluation, base_jacobian_norm = _explicit_projection(
        circuit,
        current,
        current.time + step,
        candidate_state,
    )
    return CandidateStepResult(
        evaluation=evaluation,
        requested_method="explicit_euler",
        effective_method="explicit_euler",
        order=1,
        embedded_state=None,
        used_multistep=False,
        iterations=0,
        solve_count=0,
        circuit_evaluations=1,
        algebraic_iterations=evaluation.algebraic.iterations,
        projection_count=1,
        base_jacobian_norm=base_jacobian_norm,
    )


def _heun_step(
    circuit: Circuit,
    current: CircuitEvaluation,
    step: float,
) -> CandidateStepResult:
    euler_state = tuple(
        value + step * derivative
        for value, derivative in zip(current.dynamic_state, current.derivative, strict=True)
    )
    euler_evaluation, base_jacobian_norm = _explicit_projection(
        circuit,
        current,
        current.time + step,
        euler_state,
    )
    candidate_state = tuple(
        value + 0.5 * step * (first_rate + second_rate)
        for value, first_rate, second_rate in zip(
            current.dynamic_state,
            current.derivative,
            euler_evaluation.derivative,
            strict=True,
        )
    )
    evaluation = circuit.evaluate(
        current.time + step,
        candidate_state,
        euler_evaluation.algebraic.unknowns,
    )
    return CandidateStepResult(
        evaluation=evaluation,
        requested_method="heun",
        effective_method="heun",
        order=2,
        embedded_state=euler_state,
        used_multistep=False,
        iterations=0,
        solve_count=0,
        circuit_evaluations=2,
        algebraic_iterations=(
            euler_evaluation.algebraic.iterations + evaluation.algebraic.iterations
        ),
        projection_count=2,
        base_jacobian_norm=base_jacobian_norm,
    )


def _rk23_step(
    circuit: Circuit,
    current: CircuitEvaluation,
    step: float,
) -> CandidateStepResult:
    second_state = tuple(
        value + 0.5 * step * first_rate
        for value, first_rate in zip(current.dynamic_state, current.derivative, strict=True)
    )
    second, base_jacobian_norm = _explicit_projection(
        circuit,
        current,
        current.time + 0.5 * step,
        second_state,
    )
    third_state = tuple(
        value + 0.75 * step * second_rate
        for value, second_rate in zip(current.dynamic_state, second.derivative, strict=True)
    )
    third = circuit.evaluate(
        current.time + 0.75 * step,
        third_state,
        second.algebraic.unknowns,
    )
    high_state = tuple(
        value
        + step
        * (
            (2.0 / 9.0) * first_rate
            + (1.0 / 3.0) * second_rate
            + (4.0 / 9.0) * third_rate
        )
        for value, first_rate, second_rate, third_rate in zip(
            current.dynamic_state,
            current.derivative,
            second.derivative,
            third.derivative,
            strict=True,
        )
    )
    high = circuit.evaluate(
        current.time + step,
        high_state,
        third.algebraic.unknowns,
    )
    low_state = tuple(
        value
        + step
        * (
            (7.0 / 24.0) * first_rate
            + 0.25 * second_rate
            + (1.0 / 3.0) * third_rate
            + 0.125 * fourth_rate
        )
        for value, first_rate, second_rate, third_rate, fourth_rate in zip(
            current.dynamic_state,
            current.derivative,
            second.derivative,
            third.derivative,
            high.derivative,
            strict=True,
        )
    )
    return CandidateStepResult(
        evaluation=high,
        requested_method="rk23",
        effective_method="rk23",
        order=3,
        embedded_state=low_state,
        used_multistep=False,
        iterations=0,
        solve_count=0,
        circuit_evaluations=3,
        algebraic_iterations=(
            second.algebraic.iterations
            + third.algebraic.iterations
            + high.algebraic.iterations
        ),
        projection_count=3,
        base_jacobian_norm=base_jacobian_norm,
    )


def _ab2_step(
    circuit: Circuit,
    current: CircuitEvaluation,
    step: float,
    previous_evaluation: CircuitEvaluation | None,
    previous_step: float | None,
) -> CandidateStepResult:
    if previous_evaluation is None or previous_step is None:
        raise CandidateUnavailable("AB2 requires one accepted history state")
    ratio = step / previous_step
    coefficient_current = 1.0 + 0.5 * ratio
    coefficient_previous = 0.5 * ratio
    candidate_state = tuple(
        value
        + step
        * (
            coefficient_current * current_rate
            - coefficient_previous * previous_rate
        )
        for value, current_rate, previous_rate in zip(
            current.dynamic_state,
            current.derivative,
            previous_evaluation.derivative,
            strict=True,
        )
    )
    euler_state = tuple(
        value + step * current_rate
        for value, current_rate in zip(
            current.dynamic_state,
            current.derivative,
            strict=True,
        )
    )
    evaluation, base_jacobian_norm = _explicit_projection(
        circuit,
        current,
        current.time + step,
        candidate_state,
    )
    return CandidateStepResult(
        evaluation=evaluation,
        requested_method="ab2",
        effective_method="ab2",
        order=2,
        embedded_state=euler_state,
        used_multistep=True,
        iterations=0,
        solve_count=0,
        circuit_evaluations=1,
        algebraic_iterations=evaluation.algebraic.iterations,
        projection_count=1,
        base_jacobian_norm=base_jacobian_norm,
    )


def _explicit_projection(
    circuit: Circuit,
    current: CircuitEvaluation,
    target_time: float,
    target_state: Sequence[float],
) -> tuple[CircuitEvaluation, float | None]:
    projection = circuit._predict_sparse_algebraic_projection(
        current,
        target_time,
        target_state,
    )
    if projection is None:
        return (
            circuit.evaluate(
                target_time,
                target_state,
                current.algebraic.unknowns,
            ),
            None,
        )
    return (
        circuit.evaluate(
            target_time,
            target_state,
            projection.unknowns,
            _algebraic_inputs=projection.inputs,
        ),
        projection.differential_jacobian_norm,
    )


def finite_candidate_metrics(result: CandidateStepResult) -> bool:
    return all(
        math.isfinite(value)
        for value in result.evaluation.dynamic_state + result.evaluation.derivative
    )
