from __future__ import annotations

import math
import sys
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal


LinearBackend = Literal["auto", "dense", "scipy"]
ScipyColumnOrdering = Literal["COLAMD", "NATURAL"]
LINEAR_BACKENDS: tuple[LinearBackend, ...] = ("auto", "dense", "scipy")
SCIPY_SPARSE_REUSABLE_MINIMUM_SIZE = 16
SCIPY_SPARSE_SINGLE_SOLVE_MINIMUM_SIZE = 32
SCIPY_SPARSE_MULTI_RHS_MINIMUM_COUNT = 8
SCIPY_SPARSE_MAXIMUM_DENSITY = 0.35
SCIPY_ORDERING_PROBE_FACTOR_COUNT = 4
MAXIMUM_SCIPY_WORKSPACES_PER_THREAD = 128
_SCIPY_SPARSE_WORKSPACES = threading.local()


class SingularMatrixError(RuntimeError):
    pass


class LinearBackendUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class LinearFactorization:
    factors: tuple[tuple[float, ...], ...]
    permutation: tuple[int, ...]
    minimum_pivot: float

    @property
    def backend(self) -> str:
        return "dense"


@dataclass(frozen=True)
class ScipyLinearFactorization:
    solver: Any
    size: int
    minimum_pivot: float

    @property
    def backend(self) -> str:
        return "scipy"


ReusableLinearFactorization = LinearFactorization | ScipyLinearFactorization


@dataclass
class _ScipySparseWorkspace:
    values: Any
    factorization_count: int = 0
    column_ordering: ScipyColumnOrdering | None = None


@dataclass(frozen=True)
class SparseMatrix:
    size: int
    data: tuple[float, ...]
    row_indices: tuple[int, ...]
    column_pointers: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.size < 0:
            raise ValueError("sparse matrix size must be nonnegative")
        if len(self.data) != len(self.row_indices):
            raise ValueError("sparse matrix data and row indices must have equal length")
        if len(self.column_pointers) != self.size + 1:
            raise ValueError("sparse matrix column pointers have the wrong size")
        if not self.column_pointers or self.column_pointers[0] != 0:
            raise ValueError("sparse matrix column pointers must start at zero")
        if self.column_pointers[-1] != len(self.data):
            raise ValueError("sparse matrix column pointers must end at the data length")
        if any(
            left > right
            for left, right in zip(
                self.column_pointers,
                self.column_pointers[1:],
            )
        ):
            raise ValueError("sparse matrix column pointers must be nondecreasing")
        if any(row < 0 or row >= self.size for row in self.row_indices):
            raise ValueError("sparse matrix row index is out of range")

    @property
    def nonzero_count(self) -> int:
        return len(self.data)

    def with_data(self, data: Sequence[float]) -> SparseMatrix:
        if len(data) != len(self.row_indices):
            raise ValueError("sparse matrix data has the wrong size")
        matrix = object.__new__(SparseMatrix)
        object.__setattr__(matrix, "size", self.size)
        object.__setattr__(matrix, "data", tuple(data))
        object.__setattr__(matrix, "row_indices", self.row_indices)
        object.__setattr__(matrix, "column_pointers", self.column_pointers)
        return matrix

    def to_dense(self) -> list[list[float]]:
        matrix = [[0.0] * self.size for _ in range(self.size)]
        for column in range(self.size):
            start = self.column_pointers[column]
            stop = self.column_pointers[column + 1]
            for index in range(start, stop):
                matrix[self.row_indices[index]][column] = self.data[index]
        return matrix


LinearMatrix = Sequence[Sequence[float]] | SparseMatrix


def validate_linear_backend(backend: str) -> LinearBackend:
    if backend not in LINEAR_BACKENDS:
        choices = ", ".join(LINEAR_BACKENDS)
        raise ValueError(f"linear backend must be one of: {choices}")
    return backend


@lru_cache(maxsize=1)
def _scipy_sparse_components() -> tuple[Any, Any, Any] | None:
    try:
        import numpy
        from scipy.sparse import csc_matrix
        from scipy.sparse.linalg import splu
    except ImportError:
        return None
    return numpy, csc_matrix, splu


def scipy_sparse_available() -> bool:
    return _scipy_sparse_components() is not None


@lru_cache(maxsize=128)
def _scipy_sparse_structure(
    size: int,
    row_indices: tuple[int, ...],
    column_pointers: tuple[int, ...],
) -> Any:
    components = _scipy_sparse_components()
    if components is None:
        raise LinearBackendUnavailableError(
            "the scipy linear backend requires the optional scipy dependency"
        )
    numpy, csc_matrix, _ = components
    return csc_matrix(
        (
            numpy.zeros(len(row_indices), dtype=float),
            numpy.asarray(row_indices, dtype=int),
            numpy.asarray(column_pointers, dtype=int),
        ),
        shape=(size, size),
    )


def _scipy_sparse_workspace(
    size: int,
    row_indices: tuple[int, ...],
    column_pointers: tuple[int, ...],
) -> _ScipySparseWorkspace:
    key = (size, row_indices, column_pointers)
    workspaces = getattr(_SCIPY_SPARSE_WORKSPACES, "values", None)
    if workspaces is None:
        workspaces = {}
        _SCIPY_SPARSE_WORKSPACES.values = workspaces
    workspace = workspaces.get(key)
    if workspace is not None:
        return workspace
    if len(workspaces) >= MAXIMUM_SCIPY_WORKSPACES_PER_THREAD:
        workspaces.pop(next(iter(workspaces)))
    workspace = _ScipySparseWorkspace(
        _scipy_sparse_structure(size, row_indices, column_pointers).copy()
    )
    workspaces[key] = workspace
    return workspace


def _selected_linear_backend(
    matrix: LinearMatrix,
    backend: str,
    *,
    minimum_size: int = SCIPY_SPARSE_REUSABLE_MINIMUM_SIZE,
) -> LinearBackend:
    selected = validate_linear_backend(backend)
    if selected == "dense":
        return selected
    components = _scipy_sparse_components()
    if selected == "scipy":
        if components is None:
            raise LinearBackendUnavailableError(
                "the scipy linear backend requires the optional scipy dependency"
            )
        return selected

    size = matrix.size if isinstance(matrix, SparseMatrix) else len(matrix)
    if size < minimum_size or components is None:
        return "dense"
    nonzero_entries = (
        matrix.nonzero_count
        if isinstance(matrix, SparseMatrix)
        else sum(value != 0.0 for row in matrix for value in row)
    )
    if nonzero_entries > SCIPY_SPARSE_MAXIMUM_DENSITY * size * size:
        return "dense"
    return "scipy"


def _square_matrix_size(matrix: LinearMatrix) -> int:
    if isinstance(matrix, SparseMatrix):
        return matrix.size
    size = len(matrix)
    if any(len(row) != size for row in matrix):
        raise ValueError("linear system must be square")
    return size


def _dense_matrix(matrix: LinearMatrix) -> Sequence[Sequence[float]]:
    return matrix.to_dense() if isinstance(matrix, SparseMatrix) else matrix


def norm_inf(values: Sequence[float]) -> float:
    if len(values) == 0:
        return 0.0
    if len(values) == 1:
        return abs(values[0])
    if len(values) == 2:
        left = abs(values[0])
        right = abs(values[1])
        if math.isnan(left):
            return left
        if math.isnan(right):
            return right
        return left if left >= right else right
    if len(values) >= 64:
        if any(map(math.isnan, values)):
            return math.nan
        return max(map(abs, values))
    maximum = 0.0
    for value in values:
        magnitude = abs(value)
        if math.isnan(magnitude):
            return magnitude
        if magnitude > maximum:
            maximum = magnitude
    return maximum


def matrix_inf_norm(matrix: LinearMatrix) -> float:
    if isinstance(matrix, SparseMatrix):
        if matrix.size == 0:
            return 0.0
        row_sums = [0.0] * matrix.size
        for row, value in zip(matrix.row_indices, matrix.data, strict=True):
            row_sums[row] += abs(value)
        return norm_inf(row_sums)
    if len(matrix) == 0:
        return 0.0
    if len(matrix) == 1 and len(matrix[0]) == 1:
        return abs(matrix[0][0])
    maximum = 0.0
    for row in matrix:
        row_sum = 0.0
        for value in row:
            row_sum += abs(value)
        if math.isnan(row_sum):
            return row_sum
        if row_sum > maximum:
            maximum = row_sum
    return maximum


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
    matrix: LinearMatrix,
    right_hand_side: Sequence[float],
    pivot_tolerance: float = 1.0e-14,
    *,
    backend: str = "dense",
) -> list[float]:
    size = len(right_hand_side)
    if _square_matrix_size(matrix) != size:
        raise ValueError("linear system must be square")
    if size == 0:
        return []
    if (
        _selected_linear_backend(
            matrix,
            backend,
            minimum_size=SCIPY_SPARSE_SINGLE_SOLVE_MINIMUM_SIZE,
        )
        == "scipy"
    ):
        return solve_factored(
            factor_linear(matrix, pivot_tolerance, backend="scipy"),
            right_hand_side,
        )
    matrix = _dense_matrix(matrix)

    if size == 1:
        pivot = matrix[0][0]
        minimum_pivot = pivot_tolerance * max(abs(pivot), 1.0)
        if abs(pivot) <= minimum_pivot:
            raise SingularMatrixError("singular matrix at column 0")
        return [float(right_hand_side[0]) / pivot]

    augmented: list[list[float]] = []
    scale = 1.0
    for row, value in zip(matrix, right_hand_side, strict=True):
        row_values = list(row)
        row_sum = 0.0
        for entry in row_values:
            row_sum += abs(entry)
        if math.isnan(row_sum):
            scale = row_sum
        elif row_sum > scale:
            scale = row_sum
        augmented.append(row_values + [float(value)])
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


def factor_linear(
    matrix: LinearMatrix,
    pivot_tolerance: float = 1.0e-14,
    *,
    backend: str = "dense",
) -> ReusableLinearFactorization:
    size = _square_matrix_size(matrix)
    if size == 0:
        return LinearFactorization((), (), pivot_tolerance)
    if _selected_linear_backend(matrix, backend) == "scipy":
        return _factor_linear_scipy(matrix, pivot_tolerance)
    matrix = _dense_matrix(matrix)

    factors: list[list[float]] = []
    scale = 1.0
    for row in matrix:
        row_values = list(row)
        row_sum = 0.0
        for entry in row_values:
            row_sum += abs(entry)
        if math.isnan(row_sum):
            scale = row_sum
        elif row_sum > scale:
            scale = row_sum
        factors.append(row_values)
    minimum_pivot = pivot_tolerance * scale
    permutation = list(range(size))

    for column in range(size):
        pivot_row = max(range(column, size), key=lambda row: abs(factors[row][column]))
        pivot = factors[pivot_row][column]
        if abs(pivot) <= minimum_pivot:
            raise SingularMatrixError(f"singular matrix at column {column}")
        if pivot_row != column:
            factors[column], factors[pivot_row] = factors[pivot_row], factors[column]
            permutation[column], permutation[pivot_row] = (
                permutation[pivot_row],
                permutation[column],
            )

        pivot = factors[column][column]
        for row in range(column + 1, size):
            multiplier = factors[row][column] / pivot
            factors[row][column] = multiplier
            if multiplier == 0.0:
                continue
            for index in range(column + 1, size):
                factors[row][index] -= multiplier * factors[column][index]

    return LinearFactorization(
        tuple(tuple(row) for row in factors),
        tuple(permutation),
        minimum_pivot,
    )


def _factor_linear_scipy(
    matrix: LinearMatrix,
    pivot_tolerance: float,
) -> ScipyLinearFactorization:
    components = _scipy_sparse_components()
    if components is None:
        raise LinearBackendUnavailableError(
            "the scipy linear backend requires the optional scipy dependency"
        )
    numpy, csc_matrix, splu = components
    workspace = None
    if isinstance(matrix, SparseMatrix):
        workspace = _scipy_sparse_workspace(
            matrix.size,
            matrix.row_indices,
            matrix.column_pointers,
        )
        values = workspace.values
        data = numpy.asarray(matrix.data, dtype=float)
        row_sums = numpy.bincount(
            values.indices,
            weights=numpy.abs(data),
            minlength=matrix.size,
        )
        minimum_pivot = pivot_tolerance * max(float(row_sums.max(initial=0.0)), 1.0)
        values.data = data
        size = matrix.size
    else:
        minimum_pivot = pivot_tolerance * max(matrix_inf_norm(matrix), 1.0)
        values = csc_matrix(numpy.asarray(matrix, dtype=float))
        size = len(matrix)
    if workspace is None:
        solver = _factor_scipy_values(
            values,
            minimum_pivot,
            numpy,
            splu,
            "COLAMD",
        )
    else:
        solver = _factor_repeated_scipy_values(
            workspace,
            minimum_pivot,
            numpy,
            splu,
        )
    return ScipyLinearFactorization(solver, size, minimum_pivot)


def _factor_scipy_values(
    values: Any,
    minimum_pivot: float,
    numpy: Any,
    splu: Callable[..., Any],
    column_ordering: ScipyColumnOrdering,
) -> Any:
    try:
        solver = splu(values, permc_spec=column_ordering)
    except (RuntimeError, ValueError) as error:
        raise SingularMatrixError("sparse matrix factorization failed") from error
    pivots = numpy.abs(solver.U.diagonal())
    if bool(numpy.any(pivots <= minimum_pivot)):
        pivot_index = int(numpy.argmin(pivots))
        raise SingularMatrixError(f"singular matrix at sparse pivot {pivot_index}")
    return solver


def _try_factor_scipy_values(
    values: Any,
    minimum_pivot: float,
    numpy: Any,
    splu: Callable[..., Any],
    column_ordering: ScipyColumnOrdering,
) -> Any | None:
    try:
        return _factor_scipy_values(
            values,
            minimum_pivot,
            numpy,
            splu,
            column_ordering,
        )
    except SingularMatrixError:
        return None


def _factor_repeated_scipy_values(
    workspace: _ScipySparseWorkspace,
    minimum_pivot: float,
    numpy: Any,
    splu: Callable[..., Any],
) -> Any:
    if workspace.column_ordering == "COLAMD":
        return _factor_scipy_values(
            workspace.values,
            minimum_pivot,
            numpy,
            splu,
            "COLAMD",
        )
    if workspace.column_ordering == "NATURAL":
        solver = _try_factor_scipy_values(
            workspace.values,
            minimum_pivot,
            numpy,
            splu,
            "NATURAL",
        )
        if solver is not None:
            return solver
        workspace.column_ordering = "COLAMD"
        return _factor_scipy_values(
            workspace.values,
            minimum_pivot,
            numpy,
            splu,
            "COLAMD",
        )

    colamd_solver = _factor_scipy_values(
        workspace.values,
        minimum_pivot,
        numpy,
        splu,
        "COLAMD",
    )
    workspace.factorization_count += 1
    if workspace.factorization_count < SCIPY_ORDERING_PROBE_FACTOR_COUNT:
        return colamd_solver

    natural_solver = _try_factor_scipy_values(
        workspace.values,
        minimum_pivot,
        numpy,
        splu,
        "NATURAL",
    )
    if natural_solver is not None and _scipy_factor_fill(natural_solver) <= _scipy_factor_fill(
        colamd_solver
    ):
        workspace.column_ordering = "NATURAL"
        return natural_solver
    workspace.column_ordering = "COLAMD"
    return colamd_solver


def _scipy_factor_fill(solver: Any) -> int:
    return int(solver.L.nnz + solver.U.nnz)


def solve_factored(
    factorization: ReusableLinearFactorization,
    right_hand_side: Sequence[float],
) -> list[float]:
    if isinstance(factorization, ScipyLinearFactorization):
        if len(right_hand_side) != factorization.size:
            raise ValueError("linear right-hand side has the wrong size")
        components = _scipy_sparse_components()
        if components is None:
            raise LinearBackendUnavailableError(
                "the scipy linear backend requires the optional scipy dependency"
            )
        numpy, _, _ = components
        return factorization.solver.solve(
            numpy.asarray(right_hand_side, dtype=float)
        ).tolist()

    size = len(factorization.permutation)
    if len(right_hand_side) != size:
        raise ValueError("linear right-hand side has the wrong size")
    if size == 0:
        return []

    factors = factorization.factors
    if size == 1:
        pivot = factors[0][0]
        if abs(pivot) <= factorization.minimum_pivot:
            raise SingularMatrixError("singular matrix at row 0")
        return [float(right_hand_side[factorization.permutation[0]]) / pivot]
    if size == 2:
        first_pivot = factors[0][0]
        second_pivot = factors[1][1]
        if abs(first_pivot) <= factorization.minimum_pivot:
            raise SingularMatrixError("singular matrix at row 0")
        if abs(second_pivot) <= factorization.minimum_pivot:
            raise SingularMatrixError("singular matrix at row 1")
        first = float(right_hand_side[factorization.permutation[0]])
        second = (
            float(right_hand_side[factorization.permutation[1]])
            - factors[1][0] * first
        ) / second_pivot
        return [(first - factors[0][1] * second) / first_pivot, second]

    solution = [0.0] * size
    for row in range(size):
        remainder = float(right_hand_side[factorization.permutation[row]])
        for column in range(row):
            remainder -= factors[row][column] * solution[column]
        solution[row] = remainder

    for row in range(size - 1, -1, -1):
        remainder = solution[row]
        for column in range(row + 1, size):
            remainder -= factors[row][column] * solution[column]
        pivot = factors[row][row]
        if abs(pivot) <= factorization.minimum_pivot:
            raise SingularMatrixError(f"singular matrix at row {row}")
        solution[row] = remainder / pivot
    return solution


def solve_factored_multiple(
    factorization: ReusableLinearFactorization,
    right_hand_sides: Sequence[Sequence[float]],
) -> list[list[float]]:
    native_solutions = solve_factored_multiple_array(factorization, right_hand_sides)
    if native_solutions is not None:
        return native_solutions.tolist()
    return [solve_factored(factorization, right_hand_side) for right_hand_side in right_hand_sides]


def solve_factored_multiple_array(
    factorization: ReusableLinearFactorization,
    right_hand_sides: Sequence[Sequence[float]],
) -> Any | None:
    if not isinstance(factorization, ScipyLinearFactorization):
        return None
    if any(len(right_hand_side) != factorization.size for right_hand_side in right_hand_sides):
        raise ValueError("linear right-hand side has the wrong size")
    if len(right_hand_sides) == 0:
        components = _scipy_sparse_components()
        if components is None:
            raise LinearBackendUnavailableError(
                "the scipy linear backend requires the optional scipy dependency"
            )
        numpy, _, _ = components
        return numpy.empty((0, factorization.size), dtype=float)
    components = _scipy_sparse_components()
    if components is None:
        raise LinearBackendUnavailableError(
            "the scipy linear backend requires the optional scipy dependency"
        )
    numpy, _, _ = components
    return factorization.solver.solve(
        numpy.asarray(right_hand_sides, dtype=float).transpose()
    ).transpose()


def solve_linear_multiple(
    matrix: LinearMatrix,
    right_hand_sides: Sequence[Sequence[float]],
    pivot_tolerance: float = 1.0e-14,
    *,
    backend: str = "dense",
) -> list[list[float]]:
    size = _square_matrix_size(matrix)
    if any(len(right_hand_side) != size for right_hand_side in right_hand_sides):
        raise ValueError("linear right-hand side has the wrong size")
    right_hand_side_count = len(right_hand_sides)
    if right_hand_side_count == 0:
        return []
    if size == 0:
        return [[] for _ in right_hand_sides]
    minimum_size = (
        SCIPY_SPARSE_REUSABLE_MINIMUM_SIZE
        if right_hand_side_count >= SCIPY_SPARSE_MULTI_RHS_MINIMUM_COUNT
        else SCIPY_SPARSE_SINGLE_SOLVE_MINIMUM_SIZE
    )
    if _selected_linear_backend(matrix, backend, minimum_size=minimum_size) == "scipy":
        return solve_factored_multiple(
            factor_linear(matrix, pivot_tolerance, backend="scipy"),
            right_hand_sides,
        )
    matrix = _dense_matrix(matrix)
    if size == 1:
        pivot = matrix[0][0]
        minimum_pivot = pivot_tolerance * max(abs(pivot), 1.0)
        if abs(pivot) <= minimum_pivot:
            raise SingularMatrixError("singular matrix at column 0")
        return [[float(right_hand_side[0]) / pivot] for right_hand_side in right_hand_sides]

    augmented: list[list[float]] = []
    scale = 1.0
    for row_index, row in enumerate(matrix):
        row_values = list(row)
        row_sum = 0.0
        for entry in row_values:
            row_sum += abs(entry)
        if math.isnan(row_sum):
            scale = row_sum
        elif row_sum > scale:
            scale = row_sum
        row_values.extend(
            float(right_hand_side[row_index]) for right_hand_side in right_hand_sides
        )
        augmented.append(row_values)
    minimum_pivot = pivot_tolerance * scale
    augmented_width = size + right_hand_side_count

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
            for index in range(column + 1, augmented_width):
                augmented[row][index] -= factor * augmented[column][index]

    solutions = [[0.0] * size for _ in right_hand_sides]
    for row in range(size - 1, -1, -1):
        pivot = augmented[row][row]
        if abs(pivot) <= minimum_pivot:
            raise SingularMatrixError(f"singular matrix at row {row}")
        for right_hand_side_index, solution in enumerate(solutions):
            remainder = augmented[row][size + right_hand_side_index]
            for column in range(row + 1, size):
                remainder -= augmented[row][column] * solution[column]
            solution[row] = remainder / pivot
    return solutions


def finite_difference_jacobian(
    function: Callable[[list[float]], list[float]],
    point: Sequence[float],
    value: Sequence[float] | None = None,
) -> list[list[float]]:
    base_point = list(point)
    base_value = list(value) if value is not None else function(base_point)
    rows = len(base_value)
    columns = len(base_point)
    relative_step = math.sqrt(sys.float_info.epsilon)

    if columns == 1:
        step = relative_step * max(abs(base_point[0]), 1.0)
        trial_value = function([base_point[0] + step])
        return [[(trial_value[row] - base_value[row]) / step] for row in range(rows)]

    jacobian = [[0.0] * columns for _ in range(rows)]

    for column in range(columns):
        step = relative_step * max(abs(base_point[column]), 1.0)
        trial = list(base_point)
        trial[column] += step
        trial_value = function(trial)
        for row in range(rows):
            jacobian[row][column] = (trial_value[row] - base_value[row]) / step
    return jacobian
