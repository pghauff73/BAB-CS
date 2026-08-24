from __future__ import annotations

import math
import sys
from collections.abc import Callable, Sequence


class SingularMatrixError(RuntimeError):
    pass


def norm_inf(values: Sequence[float]) -> float:
    return max((abs(value) for value in values), default=0.0)


def matrix_inf_norm(matrix: Sequence[Sequence[float]]) -> float:
    return max((sum(abs(value) for value in row) for row in matrix), default=0.0)


def weighted_rms(
    difference: Sequence[float],
    left: Sequence[float],
    right: Sequence[float],
    absolute_tolerance: float,
    relative_tolerance: float,
) -> float:
    if not difference:
        return 0.0
    total = 0.0
    for delta, left_value, right_value in zip(difference, left, right, strict=True):
        scale = absolute_tolerance + relative_tolerance * max(abs(left_value), abs(right_value))
        total += (delta / scale) ** 2
    return math.sqrt(total / len(difference))


def solve_linear(
    matrix: Sequence[Sequence[float]],
    right_hand_side: Sequence[float],
    pivot_tolerance: float = 1.0e-14,
) -> list[float]:
    size = len(right_hand_side)
    if len(matrix) != size or any(len(row) != size for row in matrix):
        raise ValueError("linear system must be square")
    if size == 0:
        return []

    augmented = [list(row) + [float(value)] for row, value in zip(matrix, right_hand_side, strict=True)]
    scale = max(matrix_inf_norm(matrix), 1.0)
    minimum_pivot = pivot_tolerance * scale

    for column in range(size):
        pivot_row = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        pivot = augmented[pivot_row][column]
        if abs(pivot) <= minimum_pivot:
            raise SingularMatrixError(f"singular matrix at column {column}")
        if pivot_row != column:
            augmented[column], augmented[pivot_row] = augmented[pivot_row], augmented[column]

        pivot = augmented[column][column]
        for row in range(column + 1, size):
            factor = augmented[row][column] / pivot
            if factor == 0.0:
                continue
            augmented[row][column] = 0.0
            for index in range(column + 1, size + 1):
                augmented[row][index] -= factor * augmented[column][index]

    solution = [0.0] * size
    for row in range(size - 1, -1, -1):
        remainder = augmented[row][size]
        for column in range(row + 1, size):
            remainder -= augmented[row][column] * solution[column]
        pivot = augmented[row][row]
        if abs(pivot) <= minimum_pivot:
            raise SingularMatrixError(f"singular matrix at row {row}")
        solution[row] = remainder / pivot
    return solution


def finite_difference_jacobian(
    function: Callable[[list[float]], list[float]],
    point: Sequence[float],
    value: Sequence[float] | None = None,
) -> list[list[float]]:
    base_point = list(point)
    base_value = list(value) if value is not None else function(base_point)
    rows = len(base_value)
    columns = len(base_point)
    jacobian = [[0.0] * columns for _ in range(rows)]
    relative_step = math.sqrt(sys.float_info.epsilon)

    for column in range(columns):
        step = relative_step * max(abs(base_point[column]), 1.0)
        trial = list(base_point)
        trial[column] += step
        trial_value = function(trial)
        for row in range(rows):
            jacobian[row][column] = (trial_value[row] - base_value[row]) / step
    return jacobian

