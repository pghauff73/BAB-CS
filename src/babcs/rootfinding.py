from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass


ScalarFunction = Callable[[float], float]
DerivativeIntervalFunction = Callable[[float, float], tuple[float, float]]


class RootFindingError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RootSettings:
    absolute_tolerance: float = 1.0e-12
    relative_tolerance: float = 1.0e-12
    residual_tolerance: float = 1.0e-12
    max_iterations: int = 100

    def __post_init__(self) -> None:
        tolerances = (
            self.absolute_tolerance,
            self.relative_tolerance,
            self.residual_tolerance,
        )
        if not all(math.isfinite(value) for value in tolerances):
            raise ValueError("root tolerances must be finite")
        if self.absolute_tolerance < 0.0 or self.relative_tolerance < 0.0:
            raise ValueError("root position tolerances must be non-negative")
        if self.absolute_tolerance == 0.0 and self.relative_tolerance == 0.0:
            raise ValueError("at least one root position tolerance must be positive")
        if self.residual_tolerance <= 0.0:
            raise ValueError("root residual_tolerance must be positive")
        if self.max_iterations < 0:
            raise ValueError("root max_iterations must be non-negative")


@dataclass(frozen=True, slots=True)
class RootIteration:
    iteration: int
    best_estimate: float
    best_residual: float
    lower_bound: float | None
    upper_bound: float | None
    enclosure_radius: float | None
    step_kind: str
    function_evaluations: int
    derivative_evaluations: int


@dataclass(frozen=True, slots=True)
class RootResult:
    method: str
    root: float
    residual: float
    converged: bool
    iterations: int
    function_evaluations: int
    derivative_evaluations: int
    bracket: tuple[float, float] | None
    absolute_error_bound: float | None
    reason: str
    trace: tuple[RootIteration, ...]


def newton_raphson(
    function: ScalarFunction,
    derivative: ScalarFunction,
    initial: float,
    *,
    settings: RootSettings = RootSettings(),
) -> RootResult:
    method = "newton_raphson"
    current = _finite_input(initial, "initial Newton iterate")
    current_value = _evaluate(function, current, "function")
    function_evaluations = 1
    derivative_evaluations = 0
    trace: list[RootIteration] = []
    if abs(current_value) <= settings.residual_tolerance:
        return _point_result(
            method,
            current,
            current_value,
            True,
            0,
            function_evaluations,
            derivative_evaluations,
            "residual tolerance satisfied",
            trace,
        )

    for iteration in range(1, settings.max_iterations + 1):
        derivative_value = _evaluate(derivative, current, "derivative")
        derivative_evaluations += 1
        if derivative_value == 0.0:
            return _point_result(
                method,
                current,
                current_value,
                False,
                iteration - 1,
                function_evaluations,
                derivative_evaluations,
                "zero derivative",
                trace,
            )
        candidate = current - current_value / derivative_value
        if not math.isfinite(candidate):
            return _point_result(
                method,
                current,
                current_value,
                False,
                iteration - 1,
                function_evaluations,
                derivative_evaluations,
                "non-finite Newton iterate",
                trace,
            )
        candidate_value = _evaluate(function, candidate, "function")
        function_evaluations += 1
        trace.append(
            RootIteration(
                iteration,
                candidate,
                abs(candidate_value),
                None,
                None,
                None,
                "newton",
                function_evaluations,
                derivative_evaluations,
            )
        )
        current = candidate
        current_value = candidate_value
        if abs(current_value) <= settings.residual_tolerance:
            return _point_result(
                method,
                current,
                current_value,
                True,
                iteration,
                function_evaluations,
                derivative_evaluations,
                "residual tolerance satisfied",
                trace,
            )

    return _point_result(
        method,
        current,
        current_value,
        False,
        settings.max_iterations,
        function_evaluations,
        derivative_evaluations,
        "iteration budget exhausted",
        trace,
    )


def secant(
    function: ScalarFunction,
    first: float,
    second: float,
    *,
    settings: RootSettings = RootSettings(),
) -> RootResult:
    method = "secant"
    previous = _finite_input(first, "first secant iterate")
    current = _finite_input(second, "second secant iterate")
    if previous == current:
        raise ValueError("secant starting iterates must be distinct")
    previous_value = _evaluate(function, previous, "function")
    current_value = _evaluate(function, current, "function")
    function_evaluations = 2
    trace: list[RootIteration] = []
    if abs(previous_value) <= settings.residual_tolerance:
        return _point_result(
            method,
            previous,
            previous_value,
            True,
            0,
            function_evaluations,
            0,
            "residual tolerance satisfied",
            trace,
        )
    if abs(current_value) <= settings.residual_tolerance:
        return _point_result(
            method,
            current,
            current_value,
            True,
            0,
            function_evaluations,
            0,
            "residual tolerance satisfied",
            trace,
        )

    for iteration in range(1, settings.max_iterations + 1):
        denominator = current_value - previous_value
        if denominator == 0.0:
            return _point_result(
                method,
                current,
                current_value,
                False,
                iteration - 1,
                function_evaluations,
                0,
                "zero secant denominator",
                trace,
            )
        candidate = current - current_value * (current - previous) / denominator
        if not math.isfinite(candidate):
            return _point_result(
                method,
                current,
                current_value,
                False,
                iteration - 1,
                function_evaluations,
                0,
                "non-finite secant iterate",
                trace,
            )
        candidate_value = _evaluate(function, candidate, "function")
        function_evaluations += 1
        trace.append(
            RootIteration(
                iteration,
                candidate,
                abs(candidate_value),
                None,
                None,
                None,
                "secant",
                function_evaluations,
                0,
            )
        )
        previous, previous_value = current, current_value
        current, current_value = candidate, candidate_value
        if abs(current_value) <= settings.residual_tolerance:
            return _point_result(
                method,
                current,
                current_value,
                True,
                iteration,
                function_evaluations,
                0,
                "residual tolerance satisfied",
                trace,
            )

    return _point_result(
        method,
        current,
        current_value,
        False,
        settings.max_iterations,
        function_evaluations,
        0,
        "iteration budget exhausted",
        trace,
    )


def bisection(
    function: ScalarFunction,
    lower: float,
    upper: float,
    *,
    settings: RootSettings = RootSettings(),
) -> RootResult:
    method = "bisection"
    lower, lower_value, upper, upper_value = _initial_bracket(function, lower, upper)
    function_evaluations = 2
    trace: list[RootIteration] = []
    exact = _endpoint_result(
        method,
        lower,
        lower_value,
        upper,
        upper_value,
        function_evaluations,
        0,
        trace,
    )
    if exact is not None:
        return exact

    for iteration in range(1, settings.max_iterations + 1):
        if _bracket_converged(lower, upper, settings):
            return _bracket_result(
                method,
                function,
                lower,
                upper,
                True,
                iteration - 1,
                function_evaluations,
                0,
                "enclosure tolerance satisfied",
                trace,
            )
        midpoint = lower + 0.5 * (upper - lower)
        if midpoint == lower or midpoint == upper:
            return _bracket_result(
                method,
                function,
                lower,
                upper,
                False,
                iteration - 1,
                function_evaluations,
                0,
                "floating-point bracket stagnation",
                trace,
            )
        midpoint_value = _evaluate(function, midpoint, "function")
        function_evaluations += 1
        if midpoint_value == 0.0:
            return _exact_result(
                method,
                midpoint,
                function_evaluations,
                0,
                iteration,
                "exact sampled root",
                trace,
            )
        lower, lower_value, upper, upper_value = _update_bracket(
            lower,
            lower_value,
            upper,
            upper_value,
            midpoint,
            midpoint_value,
        )
        trace.append(
            _bracket_iteration(
                iteration,
                lower,
                lower_value,
                upper,
                upper_value,
                "bisection",
                function_evaluations,
                0,
            )
        )

    return _bracket_result(
        method,
        function,
        lower,
        upper,
        _bracket_converged(lower, upper, settings),
        settings.max_iterations,
        function_evaluations,
        0,
        (
            "enclosure tolerance satisfied"
            if _bracket_converged(lower, upper, settings)
            else "iteration budget exhausted"
        ),
        trace,
    )


def bounded_newton_raphson(
    function: ScalarFunction,
    derivative: ScalarFunction,
    lower: float,
    upper: float,
    *,
    settings: RootSettings = RootSettings(),
) -> RootResult:
    method = "bounded_newton_raphson"
    lower, lower_value, upper, upper_value = _initial_bracket(function, lower, upper)
    function_evaluations = 2
    derivative_evaluations = 0
    trace: list[RootIteration] = []
    exact = _endpoint_result(
        method,
        lower,
        lower_value,
        upper,
        upper_value,
        function_evaluations,
        derivative_evaluations,
        trace,
    )
    if exact is not None:
        return exact

    for iteration in range(1, settings.max_iterations + 1):
        if _bracket_converged(lower, upper, settings):
            return _bracket_result(
                method,
                function,
                lower,
                upper,
                True,
                iteration - 1,
                function_evaluations,
                derivative_evaluations,
                "enclosure tolerance satisfied",
                trace,
            )

        endpoints = [(lower, lower_value), (upper, upper_value)]
        endpoints.sort(key=lambda item: abs(item[1]))
        failure_kinds: list[str] = []
        step_kind = "bisection:newton_unavailable"
        for base, base_value in endpoints:
            derivative_evaluations += 1
            try:
                derivative_value = float(derivative(base))
            except (ArithmeticError, TypeError, ValueError):
                derivative_value = math.nan
            if not math.isfinite(derivative_value):
                failure_kinds.append("invalid_derivative")
                continue
            if derivative_value == 0.0:
                failure_kinds.append("zero_derivative")
                continue
            candidate = base - base_value / derivative_value
            if not math.isfinite(candidate) or not lower < candidate < upper:
                failure_kinds.append("newton_outside_bracket")
                continue
            candidate_value = _evaluate(function, candidate, "function")
            function_evaluations += 1
            if candidate_value == 0.0:
                return _exact_result(
                    method,
                    candidate,
                    function_evaluations,
                    derivative_evaluations,
                    iteration,
                    "exact Newton root",
                    trace,
                )
            lower, lower_value, upper, upper_value = _update_bracket(
                lower,
                lower_value,
                upper,
                upper_value,
                candidate,
                candidate_value,
            )
            step_kind = "newton+bisection"
            break
        else:
            if failure_kinds and all(kind == failure_kinds[0] for kind in failure_kinds):
                step_kind = f"bisection:{failure_kinds[0]}"
            elif failure_kinds:
                step_kind = "bisection:newton_unavailable"

        if _bracket_converged(lower, upper, settings):
            trace.append(
                _bracket_iteration(
                    iteration,
                    lower,
                    lower_value,
                    upper,
                    upper_value,
                    "newton",
                    function_evaluations,
                    derivative_evaluations,
                )
            )
            return _bracket_result(
                method,
                function,
                lower,
                upper,
                True,
                iteration,
                function_evaluations,
                derivative_evaluations,
                "enclosure tolerance satisfied",
                trace,
            )

        midpoint = lower + 0.5 * (upper - lower)
        if midpoint == lower or midpoint == upper:
            return _bracket_result(
                method,
                function,
                lower,
                upper,
                False,
                iteration - 1,
                function_evaluations,
                derivative_evaluations,
                "floating-point bracket stagnation",
                trace,
            )
        midpoint_value = _evaluate(function, midpoint, "function")
        function_evaluations += 1
        if midpoint_value == 0.0:
            return _exact_result(
                method,
                midpoint,
                function_evaluations,
                derivative_evaluations,
                iteration,
                "exact bisection root",
                trace,
            )
        lower, lower_value, upper, upper_value = _update_bracket(
            lower,
            lower_value,
            upper,
            upper_value,
            midpoint,
            midpoint_value,
        )
        trace.append(
            _bracket_iteration(
                iteration,
                lower,
                lower_value,
                upper,
                upper_value,
                step_kind,
                function_evaluations,
                derivative_evaluations,
            )
        )

    converged = _bracket_converged(lower, upper, settings)
    return _bracket_result(
        method,
        function,
        lower,
        upper,
        converged,
        settings.max_iterations,
        function_evaluations,
        derivative_evaluations,
        "enclosure tolerance satisfied" if converged else "iteration budget exhausted",
        trace,
    )


def interval_newton(
    function: ScalarFunction,
    derivative_interval: DerivativeIntervalFunction,
    lower: float,
    upper: float,
    *,
    settings: RootSettings = RootSettings(),
) -> RootResult:
    method = "interval_newton"
    lower, lower_value, upper, upper_value = _initial_bracket(function, lower, upper)
    function_evaluations = 2
    derivative_evaluations = 0
    trace: list[RootIteration] = []
    exact = _endpoint_result(
        method,
        lower,
        lower_value,
        upper,
        upper_value,
        function_evaluations,
        derivative_evaluations,
        trace,
    )
    if exact is not None:
        return exact

    for iteration in range(1, settings.max_iterations + 1):
        if _bracket_converged(lower, upper, settings):
            return _bracket_result(
                method,
                function,
                lower,
                upper,
                True,
                iteration - 1,
                function_evaluations,
                derivative_evaluations,
                "enclosure tolerance satisfied",
                trace,
            )

        previous_width = upper - lower
        midpoint = lower + 0.5 * previous_width
        if midpoint == lower or midpoint == upper:
            return _bracket_result(
                method,
                function,
                lower,
                upper,
                False,
                iteration - 1,
                function_evaluations,
                derivative_evaluations,
                "floating-point bracket stagnation",
                trace,
            )
        midpoint_value = _evaluate(function, midpoint, "function")
        function_evaluations += 1
        if midpoint_value == 0.0:
            return _exact_result(
                method,
                midpoint,
                function_evaluations,
                derivative_evaluations,
                iteration,
                "exact interval-Newton center root",
                trace,
            )

        derivative_evaluations += 1
        derivative_bounds, fallback_kind = _derivative_interval_bounds(
            derivative_interval,
            lower,
            upper,
        )
        contraction = None
        if derivative_bounds is not None:
            contraction = _interval_newton_contraction(
                lower,
                upper,
                midpoint,
                midpoint_value,
                *derivative_bounds,
            )
            if contraction is None:
                fallback_kind = "interval_newton_no_contraction"
            elif contraction[1] - contraction[0] > 0.5 * previous_width:
                contraction = None
                fallback_kind = "interval_newton_insufficient_contraction"

        if contraction is not None:
            contracted_lower, contracted_upper = contraction
            if contracted_lower != lower:
                lower_value = None
            if contracted_upper != upper:
                upper_value = None
            lower, upper = contracted_lower, contracted_upper
            trace.append(
                RootIteration(
                    iteration,
                    midpoint,
                    abs(midpoint_value),
                    lower,
                    upper,
                    _enclosure_radius(lower, upper),
                    "interval_newton",
                    function_evaluations,
                    derivative_evaluations,
                )
            )
            continue

        if lower_value is None:
            lower_value = _evaluate(function, lower, "function")
            function_evaluations += 1
            if lower_value == 0.0:
                return _exact_result(
                    method,
                    lower,
                    function_evaluations,
                    derivative_evaluations,
                    iteration,
                    "exact recovered lower endpoint root",
                    trace,
                )
        if upper_value is None:
            upper_value = _evaluate(function, upper, "function")
            function_evaluations += 1
            if upper_value == 0.0:
                return _exact_result(
                    method,
                    upper,
                    function_evaluations,
                    derivative_evaluations,
                    iteration,
                    "exact recovered upper endpoint root",
                    trace,
                )
        if not _opposite_signs(lower_value, upper_value):
            raise RootFindingError(
                "interval derivative enclosure did not preserve a recoverable sign bracket"
            )

        lower, lower_value, upper, upper_value = _update_bracket(
            lower,
            lower_value,
            upper,
            upper_value,
            midpoint,
            midpoint_value,
        )
        trace.append(
            _bracket_iteration(
                iteration,
                lower,
                lower_value,
                upper,
                upper_value,
                f"bisection:{fallback_kind}",
                function_evaluations,
                derivative_evaluations,
            )
        )

    converged = _bracket_converged(lower, upper, settings)
    return _bracket_result(
        method,
        function,
        lower,
        upper,
        converged,
        settings.max_iterations,
        function_evaluations,
        derivative_evaluations,
        "enclosure tolerance satisfied" if converged else "iteration budget exhausted",
        trace,
    )


def ridders(
    function: ScalarFunction,
    lower: float,
    upper: float,
    *,
    settings: RootSettings = RootSettings(),
) -> RootResult:
    method = "ridders"
    lower, lower_value, upper, upper_value = _initial_bracket(function, lower, upper)
    function_evaluations = 2
    trace: list[RootIteration] = []
    exact = _endpoint_result(
        method,
        lower,
        lower_value,
        upper,
        upper_value,
        function_evaluations,
        0,
        trace,
    )
    if exact is not None:
        return exact

    for iteration in range(1, settings.max_iterations + 1):
        if _bracket_converged(lower, upper, settings):
            return _bracket_result(
                method,
                function,
                lower,
                upper,
                True,
                iteration - 1,
                function_evaluations,
                0,
                "enclosure tolerance satisfied",
                trace,
            )
        midpoint = lower + 0.5 * (upper - lower)
        if midpoint == lower or midpoint == upper:
            return _bracket_result(
                method,
                function,
                lower,
                upper,
                False,
                iteration - 1,
                function_evaluations,
                0,
                "floating-point bracket stagnation",
                trace,
            )
        midpoint_value = _evaluate(function, midpoint, "function")
        function_evaluations += 1
        if midpoint_value == 0.0:
            return _exact_result(
                method,
                midpoint,
                function_evaluations,
                0,
                iteration,
                "exact midpoint root",
                trace,
            )

        radicand = midpoint_value * midpoint_value - lower_value * upper_value
        candidate = math.nan
        if math.isfinite(radicand) and radicand > 0.0:
            scale = math.sqrt(radicand)
            direction = math.copysign(1.0, lower_value - upper_value)
            candidate = midpoint + (midpoint - lower) * direction * midpoint_value / scale

        if not math.isfinite(candidate) or not lower < candidate < upper:
            lower, lower_value, upper, upper_value = _update_bracket(
                lower,
                lower_value,
                upper,
                upper_value,
                midpoint,
                midpoint_value,
            )
            step_kind = "bisection_fallback"
        else:
            candidate_value = _evaluate(function, candidate, "function")
            function_evaluations += 1
            if candidate_value == 0.0:
                return _exact_result(
                    method,
                    candidate,
                    function_evaluations,
                    0,
                    iteration,
                    "exact Ridders root",
                    trace,
                )
            lower, lower_value, upper, upper_value = _ridders_bracket(
                lower,
                lower_value,
                midpoint,
                midpoint_value,
                upper,
                upper_value,
                candidate,
                candidate_value,
            )
            step_kind = "ridders"
        trace.append(
            _bracket_iteration(
                iteration,
                lower,
                lower_value,
                upper,
                upper_value,
                step_kind,
                function_evaluations,
                0,
            )
        )

    converged = _bracket_converged(lower, upper, settings)
    return _bracket_result(
        method,
        function,
        lower,
        upper,
        converged,
        settings.max_iterations,
        function_evaluations,
        0,
        "enclosure tolerance satisfied" if converged else "iteration budget exhausted",
        trace,
    )


def _finite_input(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _evaluate(function: ScalarFunction, point: float, name: str) -> float:
    try:
        value = float(function(point))
    except (ArithmeticError, TypeError, ValueError) as error:
        raise RootFindingError(f"{name} evaluation failed at x={point:.17g}: {error}") from error
    if not math.isfinite(value):
        raise RootFindingError(f"{name} evaluation is non-finite at x={point:.17g}")
    return value


def _derivative_interval_bounds(
    derivative_interval: DerivativeIntervalFunction,
    lower: float,
    upper: float,
) -> tuple[tuple[float, float] | None, str]:
    try:
        derivative_lower, derivative_upper = derivative_interval(lower, upper)
        derivative_lower = float(derivative_lower)
        derivative_upper = float(derivative_upper)
    except (ArithmeticError, TypeError, ValueError):
        return None, "invalid_derivative_interval"
    if not math.isfinite(derivative_lower) or not math.isfinite(derivative_upper):
        return None, "invalid_derivative_interval"
    if derivative_lower > derivative_upper:
        return None, "invalid_derivative_interval"
    if derivative_lower <= 0.0 <= derivative_upper:
        return None, "derivative_interval_contains_zero"
    return (derivative_lower, derivative_upper), "interval_newton"


def _interval_newton_contraction(
    lower: float,
    upper: float,
    midpoint: float,
    midpoint_value: float,
    derivative_lower: float,
    derivative_upper: float,
) -> tuple[float, float] | None:
    try:
        quotient_first = midpoint_value / derivative_lower
        quotient_second = midpoint_value / derivative_upper
    except ArithmeticError:
        return None
    if not math.isfinite(quotient_first) or not math.isfinite(quotient_second):
        return None

    quotient_lower = math.nextafter(
        min(quotient_first, quotient_second),
        -math.inf,
    )
    quotient_upper = math.nextafter(
        max(quotient_first, quotient_second),
        math.inf,
    )
    newton_lower = math.nextafter(midpoint - quotient_upper, -math.inf)
    newton_upper = math.nextafter(midpoint - quotient_lower, math.inf)
    contracted_lower = max(lower, newton_lower)
    contracted_upper = min(upper, newton_upper)
    if not contracted_lower < contracted_upper:
        return None
    if contracted_lower == lower and contracted_upper == upper:
        return None
    return contracted_lower, contracted_upper


def _initial_bracket(
    function: ScalarFunction,
    lower: float,
    upper: float,
) -> tuple[float, float, float, float]:
    lower_value = _finite_input(lower, "lower bracket endpoint")
    upper_value = _finite_input(upper, "upper bracket endpoint")
    if lower_value >= upper_value:
        raise ValueError("root bracket must satisfy lower < upper")
    function_lower = _evaluate(function, lower_value, "function")
    function_upper = _evaluate(function, upper_value, "function")
    if function_lower != 0.0 and function_upper != 0.0 and not _opposite_signs(
        function_lower,
        function_upper,
    ):
        raise ValueError("root bracket endpoints must have opposite function signs")
    return lower_value, function_lower, upper_value, function_upper


def _update_bracket(
    lower: float,
    lower_value: float,
    upper: float,
    upper_value: float,
    point: float,
    point_value: float,
) -> tuple[float, float, float, float]:
    if not lower < point < upper:
        raise RootFindingError("bracket update point must lie strictly inside the bracket")
    if _opposite_signs(lower_value, point_value):
        return lower, lower_value, point, point_value
    if _opposite_signs(point_value, upper_value):
        return point, point_value, upper, upper_value
    raise RootFindingError("function signs no longer preserve a root bracket")


def _ridders_bracket(
    lower: float,
    lower_value: float,
    midpoint: float,
    midpoint_value: float,
    upper: float,
    upper_value: float,
    candidate: float,
    candidate_value: float,
) -> tuple[float, float, float, float]:
    if _opposite_signs(midpoint_value, candidate_value):
        return _ordered_bracket(midpoint, midpoint_value, candidate, candidate_value)
    if _opposite_signs(lower_value, candidate_value):
        return _ordered_bracket(lower, lower_value, candidate, candidate_value)
    if _opposite_signs(candidate_value, upper_value):
        return _ordered_bracket(candidate, candidate_value, upper, upper_value)
    raise RootFindingError("Ridders update did not preserve a root bracket")


def _ordered_bracket(
    first: float,
    first_value: float,
    second: float,
    second_value: float,
) -> tuple[float, float, float, float]:
    if first < second:
        return first, first_value, second, second_value
    return second, second_value, first, first_value


def _opposite_signs(first: float, second: float) -> bool:
    return (first < 0.0 < second) or (second < 0.0 < first)


def _position_tolerance(lower: float, upper: float, settings: RootSettings) -> float:
    scale = max(abs(lower), abs(upper))
    return settings.absolute_tolerance + settings.relative_tolerance * scale


def _bracket_converged(lower: float, upper: float, settings: RootSettings) -> bool:
    return _enclosure_radius(lower, upper) <= _position_tolerance(lower, upper, settings)


def _enclosure_radius(lower: float, upper: float) -> float:
    midpoint = lower + 0.5 * (upper - lower)
    return max(midpoint - lower, upper - midpoint)


def _best_endpoint(
    lower: float,
    lower_value: float,
    upper: float,
    upper_value: float,
) -> tuple[float, float]:
    if abs(lower_value) <= abs(upper_value):
        return lower, lower_value
    return upper, upper_value


def _bracket_iteration(
    iteration: int,
    lower: float,
    lower_value: float,
    upper: float,
    upper_value: float,
    step_kind: str,
    function_evaluations: int,
    derivative_evaluations: int,
) -> RootIteration:
    estimate, value = _best_endpoint(lower, lower_value, upper, upper_value)
    return RootIteration(
        iteration,
        estimate,
        abs(value),
        lower,
        upper,
        _enclosure_radius(lower, upper),
        step_kind,
        function_evaluations,
        derivative_evaluations,
    )


def _point_result(
    method: str,
    root: float,
    value: float,
    converged: bool,
    iterations: int,
    function_evaluations: int,
    derivative_evaluations: int,
    reason: str,
    trace: list[RootIteration],
) -> RootResult:
    return RootResult(
        method,
        root,
        abs(value),
        converged,
        iterations,
        function_evaluations,
        derivative_evaluations,
        None,
        None,
        reason,
        tuple(trace),
    )


def _bracket_result(
    method: str,
    function: ScalarFunction,
    lower: float,
    upper: float,
    converged: bool,
    iterations: int,
    function_evaluations: int,
    derivative_evaluations: int,
    reason: str,
    trace: list[RootIteration],
) -> RootResult:
    root = lower + 0.5 * (upper - lower)
    value = _evaluate(function, root, "function")
    return RootResult(
        method,
        root,
        abs(value),
        converged,
        iterations,
        function_evaluations + 1,
        derivative_evaluations,
        (lower, upper),
        _enclosure_radius(lower, upper),
        reason,
        tuple(trace),
    )


def _endpoint_result(
    method: str,
    lower: float,
    lower_value: float,
    upper: float,
    upper_value: float,
    function_evaluations: int,
    derivative_evaluations: int,
    trace: list[RootIteration],
) -> RootResult | None:
    if lower_value == 0.0:
        return _exact_result(
            method,
            lower,
            function_evaluations,
            derivative_evaluations,
            0,
            "exact lower endpoint root",
            trace,
        )
    if upper_value == 0.0:
        return _exact_result(
            method,
            upper,
            function_evaluations,
            derivative_evaluations,
            0,
            "exact upper endpoint root",
            trace,
        )
    return None


def _exact_result(
    method: str,
    root: float,
    function_evaluations: int,
    derivative_evaluations: int,
    iterations: int,
    reason: str,
    trace: list[RootIteration],
) -> RootResult:
    return RootResult(
        method,
        root,
        0.0,
        True,
        iterations,
        function_evaluations,
        derivative_evaluations,
        (root, root),
        0.0,
        reason,
        tuple(trace),
    )
