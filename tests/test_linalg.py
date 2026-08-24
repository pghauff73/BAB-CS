from __future__ import annotations

import math
import unittest
from unittest.mock import patch

import babcs.linalg as linalg_module
from babcs.linalg import (
    LinearBackendUnavailableError,
    SparseMatrix,
    SingularMatrixError,
    factor_linear,
    finite_difference_jacobian,
    matrix_inf_norm,
    norm_inf,
    solve_linear,
    solve_linear_multiple,
    solve_factored,
    solve_factored_multiple_array,
    scipy_sparse_available,
    weighted_rms,
)


def _sparse_matrix_from_entries(
    size: int,
    entries: list[tuple[int, int, float]],
) -> SparseMatrix:
    columns: list[list[tuple[int, float]]] = [[] for _ in range(size)]
    for row, column, value in entries:
        columns[column].append((row, value))
    data: list[float] = []
    row_indices: list[int] = []
    column_pointers = [0]
    for column in columns:
        for row, value in sorted(column):
            row_indices.append(row)
            data.append(value)
        column_pointers.append(len(data))
    return SparseMatrix(
        size,
        tuple(data),
        tuple(row_indices),
        tuple(column_pointers),
    )


class LinearAlgebraTests(unittest.TestCase):
    def test_sparse_matrix_round_trips_and_preserves_norm(self) -> None:
        sparse = SparseMatrix(
            3,
            (2.0, -1.0, 4.0, 3.0),
            (0, 2, 1, 2),
            (0, 2, 3, 4),
        )
        dense = [
            [2.0, 0.0, 0.0],
            [0.0, 4.0, 0.0],
            [-1.0, 0.0, 3.0],
        ]

        self.assertEqual(sparse.to_dense(), dense)
        self.assertEqual(matrix_inf_norm(sparse), matrix_inf_norm(dense))
        self.assertEqual(solve_linear(sparse, [2.0, 8.0, 5.0]), [1.0, 2.0, 2.0])
        self.assertEqual(
            sparse.with_data((4.0, -2.0, 8.0, 6.0)).to_dense(),
            [[4.0, 0.0, 0.0], [0.0, 8.0, 0.0], [-2.0, 0.0, 6.0]],
        )
        with self.assertRaisesRegex(ValueError, "wrong size"):
            sparse.with_data((1.0,))

    def test_sparse_matrix_validates_structure(self) -> None:
        with self.assertRaisesRegex(ValueError, "data and row"):
            SparseMatrix(1, (1.0,), (), (0, 1))
        with self.assertRaisesRegex(ValueError, "column pointers"):
            SparseMatrix(2, (), (), (0, 0))
        with self.assertRaisesRegex(ValueError, "row index"):
            SparseMatrix(1, (1.0,), (1,), (0, 1))

    def test_scalar_system_uses_same_pivot_contract(self) -> None:
        self.assertEqual(solve_linear([[2.0]], [6.0]), [3.0])
        with self.assertRaises(SingularMatrixError):
            solve_linear([[0.0]], [1.0])

    def test_partial_pivoting_solves_dense_system(self) -> None:
        solution = solve_linear([[0.0, 2.0], [1.0, 3.0]], [4.0, 5.0])
        self.assertAlmostEqual(solution[0], -1.0)
        self.assertAlmostEqual(solution[1], 2.0)

    def test_singular_system_is_rejected(self) -> None:
        with self.assertRaises(SingularMatrixError):
            solve_linear([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])

    def test_multiple_right_hand_sides_share_one_factorization(self) -> None:
        matrix = [[0.0, 2.0], [1.0, 3.0]]
        right_hand_sides = [[4.0, 5.0], [2.0, 4.0]]
        solutions = solve_linear_multiple(matrix, right_hand_sides)

        self.assertEqual(len(solutions), 2)
        for solution, right_hand_side in zip(solutions, right_hand_sides, strict=True):
            expected = solve_linear(matrix, right_hand_side)
            for value, expected_value in zip(solution, expected, strict=True):
                self.assertAlmostEqual(value, expected_value)

    def test_multiple_right_hand_sides_validate_shape_and_singularity(self) -> None:
        with self.assertRaisesRegex(ValueError, "square"):
            solve_linear_multiple([[1.0, 2.0]], [[1.0]])
        with self.assertRaisesRegex(ValueError, "wrong size"):
            solve_linear_multiple([[1.0]], [[1.0, 2.0]])
        with self.assertRaises(SingularMatrixError):
            solve_linear_multiple([[1.0, 2.0], [2.0, 4.0]], [[1.0, 2.0]])

    def test_reusable_factorization_matches_direct_solves(self) -> None:
        cases = (
            ([[2.0]], ([6.0], [4.0])),
            ([[0.0, 2.0], [1.0, 3.0]], ([4.0, 5.0], [2.0, 4.0])),
            (
                [[2.0, 1.0, 0.0], [1.0, 3.0, 1.0], [0.0, 1.0, 2.0]],
                ([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]),
            ),
        )
        for matrix, right_hand_sides in cases:
            factorization = factor_linear(matrix)
            for right_hand_side in right_hand_sides:
                expected = solve_linear(matrix, right_hand_side)
                actual = solve_factored(factorization, right_hand_side)
                for value, expected_value in zip(actual, expected, strict=True):
                    self.assertAlmostEqual(value, expected_value)

    def test_reusable_factorization_validates_inputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "square"):
            factor_linear([[1.0, 2.0]])
        with self.assertRaises(SingularMatrixError):
            factor_linear([[1.0, 2.0], [2.0, 4.0]])
        with self.assertRaisesRegex(ValueError, "wrong size"):
            solve_factored(factor_linear([[1.0]]), [1.0, 2.0])

    def test_auto_backend_preserves_dense_small_systems(self) -> None:
        factorization = factor_linear([[2.0, 1.0], [1.0, 3.0]], backend="auto")
        self.assertEqual(factorization.backend, "dense")

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_auto_single_solve_defers_sparse_crossover(self) -> None:
        size = 16
        matrix = [[0.0] * size for _ in range(size)]
        for index in range(size):
            matrix[index][index] = 2.0
        with patch("babcs.linalg._factor_linear_scipy") as sparse_factor:
            self.assertEqual(
                solve_linear(matrix, [1.0] * size, backend="auto"),
                [0.5] * size,
            )
        sparse_factor.assert_not_called()

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_auto_multiple_rhs_requires_enough_columns_at_small_crossover(self) -> None:
        size = 16
        matrix = [[0.0] * size for _ in range(size)]
        for index in range(size):
            matrix[index][index] = 2.0
        right_hand_sides = [[1.0] * size for _ in range(4)]
        with patch("babcs.linalg._factor_linear_scipy") as sparse_factor:
            self.assertEqual(
                solve_linear_multiple(matrix, right_hand_sides, backend="auto"),
                [[0.5] * size for _ in right_hand_sides],
            )
        sparse_factor.assert_not_called()

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_scipy_backend_matches_dense_for_sparse_multiple_rhs(self) -> None:
        size = 16
        matrix = [[0.0] * size for _ in range(size)]
        for index in range(size):
            matrix[index][index] = 4.0
            if index:
                matrix[index][index - 1] = -1.0
                matrix[index - 1][index] = -1.0
        right_hand_sides = [
            [float((index + offset) % 5 - 2) for index in range(size)]
            for offset in range(4)
        ]

        factorization = factor_linear(matrix, backend="auto")
        self.assertEqual(factorization.backend, "scipy")
        sparse_solutions = solve_linear_multiple(
            matrix,
            right_hand_sides,
            backend="scipy",
        )
        dense_solutions = solve_linear_multiple(matrix, right_hand_sides)
        for sparse_solution, dense_solution in zip(
            sparse_solutions,
            dense_solutions,
            strict=True,
        ):
            for sparse_value, dense_value in zip(
                sparse_solution,
                dense_solution,
                strict=True,
            ):
                self.assertAlmostEqual(sparse_value, dense_value, places=12)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_native_sparse_multiple_rhs_array_matches_list_orientation(self) -> None:
        matrix = SparseMatrix(
            3,
            (4.0, -1.0, -1.0, 4.0, -1.0, -1.0, 4.0),
            (0, 1, 0, 1, 2, 1, 2),
            (0, 2, 5, 7),
        )
        right_hand_sides = ([1.0, 2.0, 3.0], [3.0, 2.0, 1.0])
        factorization = factor_linear(matrix, backend="scipy")

        native = solve_factored_multiple_array(factorization, right_hand_sides)

        self.assertIsNotNone(native)
        assert native is not None
        self.assertEqual(native.shape, (2, 3))
        self.assertEqual(
            native.tolist(),
            solve_linear_multiple(matrix, right_hand_sides, backend="scipy"),
        )

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_scipy_backend_accepts_precompiled_csc_structure(self) -> None:
        sparse = SparseMatrix(
            3,
            (4.0, -1.0, -1.0, 4.0, -1.0, -1.0, 4.0),
            (0, 1, 0, 1, 2, 1, 2),
            (0, 2, 5, 7),
        )
        right_hand_side = [2.0, 4.0, 10.0]

        dense_solution = solve_linear(sparse.to_dense(), right_hand_side)
        sparse_solution = solve_linear(sparse, right_hand_side, backend="scipy")
        for sparse_value, dense_value in zip(
            sparse_solution,
            dense_solution,
            strict=True,
        ):
            self.assertAlmostEqual(sparse_value, dense_value, places=12)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_reused_sparse_workspace_keeps_factorizations_independent(self) -> None:
        first_matrix = SparseMatrix(
            3,
            (4.0, -1.0, -1.0, 4.0, -1.0, -1.0, 4.0),
            (0, 1, 0, 1, 2, 1, 2),
            (0, 2, 5, 7),
        )
        second_matrix = first_matrix.with_data((6.0, -1.0, -1.0, 5.0, -1.0, -1.0, 3.0))
        first_factorization = factor_linear(first_matrix, backend="scipy")
        second_factorization = factor_linear(second_matrix, backend="scipy")

        for matrix, factorization, right_hand_side in (
            (first_matrix, first_factorization, [2.0, 4.0, 10.0]),
            (second_matrix, second_factorization, [3.0, 2.0, 1.0]),
        ):
            expected = solve_linear(matrix.to_dense(), right_hand_side)
            actual = solve_factored(factorization, right_hand_side)
            for actual_value, expected_value in zip(actual, expected, strict=True):
                self.assertAlmostEqual(actual_value, expected_value, places=12)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_repeated_block_pattern_selects_natural_ordering_when_fill_matches(self) -> None:
        linalg_module._SCIPY_SPARSE_WORKSPACES.values = {}
        entries = []
        for block in range(16):
            first = 2 * block
            second = first + 1
            entries.extend(
                (
                    (first, first, 4.0),
                    (second, first, -1.0),
                    (first, second, -1.0),
                    (second, second, 3.0),
                )
            )
        matrix = _sparse_matrix_from_entries(32, entries)

        for _ in range(linalg_module.SCIPY_ORDERING_PROBE_FACTOR_COUNT - 1):
            factor_linear(matrix, backend="scipy")
        workspace = linalg_module._scipy_sparse_workspace(
            matrix.size,
            matrix.row_indices,
            matrix.column_pointers,
        )
        self.assertIsNone(workspace.column_ordering)
        factorization = factor_linear(matrix, backend="scipy")

        self.assertEqual(workspace.column_ordering, "NATURAL")
        actual = solve_factored(factorization, [1.0] * matrix.size)
        expected = solve_linear(matrix.to_dense(), [1.0] * matrix.size)
        for actual_value, expected_value in zip(actual, expected, strict=True):
            self.assertAlmostEqual(actual_value, expected_value, places=12)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_repeated_grid_pattern_rejects_natural_ordering_with_more_fill(self) -> None:
        linalg_module._SCIPY_SPARSE_WORKSPACES.values = {}
        side = 8
        entries = []
        for row in range(side):
            for column in range(side):
                index = row * side + column
                entries.append((index, index, 4.0))
                if row:
                    entries.append((index, index - side, -1.0))
                if row + 1 < side:
                    entries.append((index, index + side, -1.0))
                if column:
                    entries.append((index, index - 1, -1.0))
                if column + 1 < side:
                    entries.append((index, index + 1, -1.0))
        matrix = _sparse_matrix_from_entries(side * side, entries)

        for _ in range(linalg_module.SCIPY_ORDERING_PROBE_FACTOR_COUNT):
            factor_linear(matrix, backend="scipy")

        workspace = linalg_module._scipy_sparse_workspace(
            matrix.size,
            matrix.row_indices,
            matrix.column_pointers,
        )
        self.assertEqual(workspace.column_ordering, "COLAMD")

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_cached_natural_ordering_falls_back_to_colamd_on_failure(self) -> None:
        linalg_module._SCIPY_SPARSE_WORKSPACES.values = {}
        matrix = _sparse_matrix_from_entries(
            4,
            [
                (0, 0, 4.0),
                (1, 0, -1.0),
                (0, 1, -1.0),
                (1, 1, 3.0),
                (2, 2, 4.0),
                (3, 2, -1.0),
                (2, 3, -1.0),
                (3, 3, 3.0),
            ],
        )
        for _ in range(linalg_module.SCIPY_ORDERING_PROBE_FACTOR_COUNT):
            factor_linear(matrix, backend="scipy")
        components = linalg_module._scipy_sparse_components()
        assert components is not None
        numpy, csc_matrix, real_splu = components
        orderings = []

        def fail_natural(values, *, permc_spec=None, **options):
            orderings.append(permc_spec)
            if permc_spec == "NATURAL":
                raise RuntimeError("forced natural-ordering failure")
            return real_splu(values, permc_spec=permc_spec, **options)

        with patch(
            "babcs.linalg._scipy_sparse_components",
            return_value=(numpy, csc_matrix, fail_natural),
        ):
            factorization = factor_linear(matrix, backend="scipy")

        workspace = linalg_module._scipy_sparse_workspace(
            matrix.size,
            matrix.row_indices,
            matrix.column_pointers,
        )
        self.assertEqual(orderings, ["NATURAL", "COLAMD"])
        self.assertEqual(workspace.column_ordering, "COLAMD")
        actual = solve_factored(factorization, [1.0] * matrix.size)
        expected = solve_linear(matrix.to_dense(), [1.0] * matrix.size)
        for actual_value, expected_value in zip(actual, expected, strict=True):
            self.assertAlmostEqual(actual_value, expected_value, places=12)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_sparse_workspace_cache_has_bounded_per_thread_capacity(self) -> None:
        linalg_module._SCIPY_SPARSE_WORKSPACES.values = {}
        for size in range(1, 132):
            linalg_module._scipy_sparse_workspace(
                size,
                tuple(range(size)),
                tuple(range(size + 1)),
            )

        self.assertLessEqual(
            len(linalg_module._SCIPY_SPARSE_WORKSPACES.values),
            linalg_module.MAXIMUM_SCIPY_WORKSPACES_PER_THREAD,
        )

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_scipy_backend_preserves_singularity_gate(self) -> None:
        with self.assertRaises(SingularMatrixError):
            factor_linear([[1.0, 2.0], [2.0, 4.0]], backend="scipy")

    def test_explicit_scipy_backend_fails_when_dependency_is_missing(self) -> None:
        with patch("babcs.linalg._scipy_sparse_components", return_value=None):
            with self.assertRaises(LinearBackendUnavailableError):
                factor_linear([[1.0]], backend="scipy")

    def test_unknown_linear_backend_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "linear backend"):
            factor_linear([[1.0]], backend="unknown")

    def test_weighted_rms_uses_absolute_and_relative_scale(self) -> None:
        error = weighted_rms([1.0e-6], [1.0], [1.0], 1.0e-9, 1.0e-6)
        self.assertGreater(error, 0.99)
        self.assertLess(error, 1.0)

    def test_infinity_norms_propagate_nan(self) -> None:
        self.assertTrue(math.isnan(norm_inf([1.0, math.nan])))
        self.assertTrue(math.isnan(norm_inf([1.0] * 63 + [math.nan])))
        self.assertTrue(math.isnan(norm_inf([math.nan] + [1.0] * 63)))
        self.assertTrue(math.isnan(matrix_inf_norm([[1.0], [math.nan]])))

    def test_scalar_finite_difference_jacobian(self) -> None:
        jacobian = finite_difference_jacobian(lambda values: [values[0] ** 2], [3.0], [9.0])
        self.assertAlmostEqual(jacobian[0][0], 6.0, places=6)


if __name__ == "__main__":
    unittest.main()
