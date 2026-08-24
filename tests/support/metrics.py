from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from babcs.linalg import solve_linear


Trace = Sequence[tuple[float, float]]


def validate_trace(trace: Trace) -> None:
    if not trace:
        raise ValueError("trace must not be empty")
    if any(right[0] <= left[0] for left, right in zip(trace, trace[1:])):
        raise ValueError("trace times must be strictly increasing")
    if any(not math.isfinite(value) for point in trace for value in point):
        raise ValueError("trace values must be finite")


def interpolate_trace(trace: Trace, time: float) -> float:
    validate_trace(trace)
    tolerance = 64.0 * math.ulp(max(abs(time), abs(trace[0][0]), abs(trace[-1][0]), 1.0))
    if time < trace[0][0] - tolerance or time > trace[-1][0] + tolerance:
        raise ValueError("sample time lies outside the trace")
    if time <= trace[0][0] + tolerance:
        return trace[0][1]
    if time >= trace[-1][0] - tolerance:
        return trace[-1][1]
    for left, right in zip(trace, trace[1:]):
        if time <= right[0]:
            if time == right[0]:
                return right[1]
            fraction = (time - left[0]) / (right[0] - left[0])
            return left[1] + fraction * (right[1] - left[1])
    return trace[-1][1]


def sample_trace(trace: Trace, times: Iterable[float]) -> tuple[float, ...]:
    return tuple(interpolate_trace(trace, time) for time in times)


def error_metrics(
    actual: Sequence[float],
    expected: Sequence[float],
    *,
    absolute_tolerance: float = 1.0e-12,
    relative_tolerance: float = 1.0e-9,
) -> dict[str, float]:
    if len(actual) != len(expected) or not actual:
        raise ValueError("actual and expected values must have equal nonzero length")
    differences = [left - right for left, right in zip(actual, expected, strict=True)]
    scaled = [
        abs(difference)
        / (absolute_tolerance + relative_tolerance * max(abs(left), abs(right)))
        for difference, left, right in zip(differences, actual, expected, strict=True)
    ]
    return {
        "final_absolute_error": abs(differences[-1]),
        "maximum_absolute_error": max(abs(value) for value in differences),
        "rms_absolute_error": math.sqrt(sum(value * value for value in differences) / len(differences)),
        "maximum_scaled_error": max(scaled),
    }


def observed_order(coarse_error: float, fine_error: float, refinement_ratio: float = 2.0) -> float:
    if coarse_error <= 0.0 or fine_error <= 0.0:
        raise ValueError("convergence errors must be positive")
    if refinement_ratio <= 1.0:
        raise ValueError("refinement ratio must exceed one")
    return math.log(coarse_error / fine_error) / math.log(refinement_ratio)


def positive_zero_crossings(trace: Trace) -> tuple[float, ...]:
    validate_trace(trace)
    crossings: list[float] = []
    for left, right in zip(trace, trace[1:]):
        left_time, left_value = left
        right_time, right_value = right
        if left_value <= 0.0 < right_value:
            fraction = -left_value / (right_value - left_value)
            crossings.append(left_time + fraction * (right_time - left_time))
    return tuple(crossings)


def estimated_period(trace: Trace) -> float:
    crossings = positive_zero_crossings(trace)
    if len(crossings) < 2:
        raise ValueError("trace does not contain two positive-going zero crossings")
    intervals = [right - left for left, right in zip(crossings, crossings[1:])]
    return sum(intervals) / len(intervals)


def sinusoidal_amplitude_phase(
    trace: Trace,
    frequency: float,
    *,
    start_time: float | None = None,
) -> dict[str, float]:
    validate_trace(trace)
    if not math.isfinite(frequency) or frequency <= 0.0:
        raise ValueError("frequency must be positive and finite")
    selected = tuple(point for point in trace if start_time is None or point[0] >= start_time)
    if len(selected) < 3:
        raise ValueError("sinusoidal fit requires at least three samples")
    angular_frequency = 2.0 * math.pi * frequency
    rows = [
        (1.0, math.sin(angular_frequency * time), math.cos(angular_frequency * time))
        for time, _ in selected
    ]
    matrix = [
        [sum(row[left] * row[right] for row in rows) for right in range(3)]
        for left in range(3)
    ]
    right_hand_side = [
        sum(row[index] * point[1] for row, point in zip(rows, selected, strict=True))
        for index in range(3)
    ]
    offset, sine_coefficient, cosine_coefficient = solve_linear(matrix, right_hand_side)
    return {
        "offset": offset,
        "amplitude": math.hypot(sine_coefficient, cosine_coefficient),
        "phase_radians": math.atan2(cosine_coefficient, sine_coefficient),
    }
