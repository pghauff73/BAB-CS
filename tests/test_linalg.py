from __future__ import annotations

import unittest

from babcs.linalg import SingularMatrixError, solve_linear, weighted_rms


class LinearAlgebraTests(unittest.TestCase):
    def test_partial_pivoting_solves_dense_system(self) -> None:
        solution = solve_linear([[0.0, 2.0], [1.0, 3.0]], [4.0, 5.0])
        self.assertAlmostEqual(solution[0], -1.0)
        self.assertAlmostEqual(solution[1], 2.0)

    def test_singular_system_is_rejected(self) -> None:
        with self.assertRaises(SingularMatrixError):
            solve_linear([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])

    def test_weighted_rms_uses_absolute_and_relative_scale(self) -> None:
        error = weighted_rms([1.0e-6], [1.0], [1.0], 1.0e-9, 1.0e-6)
        self.assertGreater(error, 0.99)
        self.assertLess(error, 1.0)


if __name__ == "__main__":
    unittest.main()

