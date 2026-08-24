from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass


Derivative = Callable[[float, tuple[float, ...]], Sequence[float]]


@dataclass(frozen=True)
class RawAB2Point:
    time: float
    state: tuple[float, ...]


def integrate_raw_ab2(
    derivative: Derivative,
    initial_state: Sequence[float],
    stop_time: float,
    step: float,
    *,
    start_time: float = 0.0,
) -> tuple[RawAB2Point, ...]:
    if stop_time <= start_time:
        raise ValueError("stop_time must follow start_time")
    if step <= 0.0:
        raise ValueError("step must be positive")
    state = tuple(float(value) for value in initial_state)
    if not state:
        raise ValueError("raw AB2 requires a nonempty state")

    time = start_time
    current_derivative = tuple(float(value) for value in derivative(time, state))
    _validate_derivative(state, current_derivative)
    points = [RawAB2Point(time, state)]
    previous_derivative: tuple[float, ...] | None = None
    previous_step: float | None = None
    time_tolerance = 64.0 * math.ulp(max(abs(start_time), abs(stop_time), 1.0))

    while time < stop_time - time_tolerance:
        current_step = min(step, stop_time - time)
        if previous_derivative is None or previous_step is None:
            next_state = tuple(
                value + current_step * rate
                for value, rate in zip(state, current_derivative, strict=True)
            )
        else:
            ratio = current_step / previous_step
            next_state = tuple(
                value
                + current_step
                * ((1.0 + 0.5 * ratio) * rate - 0.5 * ratio * previous_rate)
                for value, rate, previous_rate in zip(
                    state,
                    current_derivative,
                    previous_derivative,
                    strict=True,
                )
            )
        next_time = time + current_step
        next_derivative = tuple(float(value) for value in derivative(next_time, next_state))
        _validate_derivative(next_state, next_derivative)
        previous_derivative = current_derivative
        previous_step = current_step
        time = next_time
        state = next_state
        current_derivative = next_derivative
        points.append(RawAB2Point(time, state))
    return tuple(points)


def _validate_derivative(state: tuple[float, ...], derivative: tuple[float, ...]) -> None:
    if len(state) != len(derivative):
        raise ValueError("derivative dimension does not match the state")
    if any(not math.isfinite(value) for value in (*state, *derivative)):
        raise ValueError("raw AB2 state and derivative values must be finite")
