from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from babcs import (
    RootSettings,
    bisection,
    bounded_newton_raphson,
    interval_newton,
    newton_raphson,
    ridders,
    secant,
)
from tools.compare_rootfinders import execute_comparison, write_csv, write_report


class RootFindingTests(unittest.TestCase):
    def test_settings_reject_invalid_budgets_and_tolerances(self) -> None:
        with self.assertRaises(ValueError):
            RootSettings(absolute_tolerance=0.0, relative_tolerance=0.0)
        with self.assertRaises(ValueError):
            RootSettings(residual_tolerance=0.0)
        with self.assertRaises(ValueError):
            RootSettings(max_iterations=-1)

    def test_newton_and_secant_converge_locally(self) -> None:
        function = lambda value: value * value - 2.0
        newton = newton_raphson(function, lambda value: 2.0 * value, 2.0)
        secant_result = secant(function, 0.0, 2.0)
        for result in (newton, secant_result):
            self.assertTrue(result.converged)
            self.assertAlmostEqual(result.root, math.sqrt(2.0), places=12)
            self.assertIsNone(result.bracket)
            self.assertIsNone(result.absolute_error_bound)

    def test_bisection_returns_a_certified_enclosure(self) -> None:
        result = bisection(lambda value: value * value - 2.0, 0.0, 2.0)
        self.assertTrue(result.converged)
        self.assertIsNotNone(result.bracket)
        self.assertIsNotNone(result.absolute_error_bound)
        assert result.bracket is not None and result.absolute_error_bound is not None
        self.assertLessEqual(result.bracket[0], math.sqrt(2.0))
        self.assertGreaterEqual(result.bracket[1], math.sqrt(2.0))
        self.assertLessEqual(abs(result.root - math.sqrt(2.0)), result.absolute_error_bound)
        for previous, current in zip(result.trace, result.trace[1:], strict=False):
            assert previous.enclosure_radius is not None and current.enclosure_radius is not None
            self.assertLessEqual(current.enclosure_radius, 0.5 * previous.enclosure_radius)

    def test_bounded_newton_preserves_bracket_and_uses_newton(self) -> None:
        result = bounded_newton_raphson(
            lambda value: value * value - 2.0,
            lambda value: 2.0 * value,
            0.0,
            2.0,
        )
        self.assertTrue(result.converged)
        self.assertTrue(any("newton" in point.step_kind for point in result.trace))
        assert result.bracket is not None and result.absolute_error_bound is not None
        self.assertLessEqual(result.bracket[0], math.sqrt(2.0))
        self.assertGreaterEqual(result.bracket[1], math.sqrt(2.0))
        self.assertLessEqual(abs(result.root - math.sqrt(2.0)), result.absolute_error_bound)
        previous_width = 2.0
        for point in result.trace:
            assert point.lower_bound is not None and point.upper_bound is not None
            width = point.upper_bound - point.lower_bound
            if "bisection" in point.step_kind:
                self.assertLessEqual(width, 0.5 * previous_width)
            else:
                self.assertLessEqual(width, previous_width)
            previous_width = width

    def test_bounded_newton_recovers_from_classical_newton_cycle(self) -> None:
        function = lambda value: value**3 - 2.0 * value + 2.0
        derivative = lambda value: 3.0 * value * value - 2.0
        settings = RootSettings(max_iterations=20)
        unbounded = newton_raphson(function, derivative, 0.0, settings=settings)
        bounded = bounded_newton_raphson(
            function,
            derivative,
            -2.0,
            0.0,
            settings=settings,
        )
        self.assertFalse(unbounded.converged)
        self.assertEqual(unbounded.reason, "iteration budget exhausted")
        self.assertTrue(bounded.converged)
        self.assertAlmostEqual(bounded.root, -1.7692923542386314, places=14)

    def test_bounded_newton_falls_back_when_derivative_is_unusable(self) -> None:
        function = lambda value: value**3 - 0.2
        result = bounded_newton_raphson(function, lambda value: math.nan, 0.0, 1.0)
        self.assertTrue(result.converged)
        self.assertTrue(
            all(point.step_kind == "bisection:invalid_derivative" for point in result.trace)
        )
        self.assertAlmostEqual(result.root, 0.2 ** (1.0 / 3.0), places=11)

    def test_interval_newton_contracts_both_sides_with_outward_rounding(self) -> None:
        function = lambda value: value * value - 2.0
        result = interval_newton(
            function,
            lambda lower, upper: (2.0 * lower, 2.0 * upper),
            0.0,
            2.0,
        )
        bounded = bounded_newton_raphson(function, lambda value: 2.0 * value, 0.0, 2.0)
        self.assertTrue(result.converged)
        self.assertLess(result.function_evaluations, bounded.function_evaluations)
        self.assertTrue(any(point.step_kind == "interval_newton" for point in result.trace))
        assert result.bracket is not None and result.absolute_error_bound is not None
        self.assertLess(result.bracket[0], result.bracket[1])
        self.assertLessEqual(result.bracket[0], math.sqrt(2.0))
        self.assertGreaterEqual(result.bracket[1], math.sqrt(2.0))
        self.assertLessEqual(abs(result.root - math.sqrt(2.0)), result.absolute_error_bound)
        previous_width = 2.0
        for point in result.trace:
            assert point.lower_bound is not None and point.upper_bound is not None
            width = point.upper_bound - point.lower_bound
            self.assertLessEqual(width, 0.5 * previous_width)
            previous_width = width

    def test_interval_newton_falls_back_when_derivative_interval_contains_zero(self) -> None:
        result = interval_newton(
            lambda value: (value - 1.0) ** 3,
            lambda lower, upper: (
                0.0 if lower <= 1.0 <= upper else min(
                    3.0 * (lower - 1.0) ** 2,
                    3.0 * (upper - 1.0) ** 2,
                ),
                max(
                    3.0 * (lower - 1.0) ** 2,
                    3.0 * (upper - 1.0) ** 2,
                ),
            ),
            0.0,
            1.5,
        )
        self.assertTrue(result.converged)
        self.assertTrue(
            all(
                point.step_kind == "bisection:derivative_interval_contains_zero"
                for point in result.trace
            )
        )
        assert result.bracket is not None
        self.assertLessEqual(result.bracket[0], 1.0)
        self.assertGreaterEqual(result.bracket[1], 1.0)

    def test_interval_newton_falls_back_on_invalid_derivative_interval(self) -> None:
        result = interval_newton(
            lambda value: value**3 - 0.2,
            lambda lower, upper: (math.nan, math.nan),
            0.0,
            1.0,
        )
        self.assertTrue(result.converged)
        self.assertTrue(
            all(
                point.step_kind == "bisection:invalid_derivative_interval"
                for point in result.trace
            )
        )
        self.assertAlmostEqual(result.root, 0.2 ** (1.0 / 3.0), places=11)

    def test_interval_newton_recovers_unsampled_signs_before_fallback(self) -> None:
        interval_calls = 0

        def derivative_interval(lower: float, upper: float) -> tuple[float, float]:
            nonlocal interval_calls
            interval_calls += 1
            if interval_calls == 2:
                return math.nan, math.nan
            return math.exp(lower), math.exp(upper)

        result = interval_newton(
            lambda value: math.exp(value) - 3.0,
            derivative_interval,
            0.0,
            2.0,
        )
        self.assertTrue(result.converged)
        self.assertTrue(
            any(
                point.step_kind == "bisection:invalid_derivative_interval"
                for point in result.trace
            )
        )
        assert result.bracket is not None
        self.assertLessEqual(result.bracket[0], math.log(3.0))
        self.assertGreaterEqual(result.bracket[1], math.log(3.0))

    def test_bracketed_methods_reject_missing_sign_change(self) -> None:
        for method in (bisection, ridders):
            with self.assertRaisesRegex(ValueError, "opposite function signs"):
                method(lambda value: value * value + 1.0, -1.0, 1.0)
        with self.assertRaisesRegex(ValueError, "opposite function signs"):
            bounded_newton_raphson(
                lambda value: value * value + 1.0,
                lambda value: 2.0 * value,
                -1.0,
                1.0,
            )

    def test_bracketed_methods_compute_extreme_midpoints_without_overflow(self) -> None:
        function = lambda value: value
        results = (
            bisection(function, -1.0e308, 1.0e308),
            bounded_newton_raphson(
                function,
                lambda value: math.nan,
                -1.0e308,
                1.0e308,
            ),
            interval_newton(
                function,
                lambda lower, upper: (1.0, 1.0),
                -1.0e308,
                1.0e308,
            ),
            ridders(function, -1.0e308, 1.0e308),
        )
        for result in results:
            self.assertTrue(result.converged, result)
            self.assertEqual(result.root, 0.0)
            self.assertEqual(result.residual, 0.0)
        with self.assertRaisesRegex(ValueError, "opposite function signs"):
            interval_newton(
                lambda value: value * value + 1.0,
                lambda lower, upper: (2.0 * lower, 2.0 * upper),
                -1.0,
                1.0,
            )

    def test_ridders_is_bracketed_and_accurate(self) -> None:
        result = ridders(lambda value: math.exp(value) - 3.0, 0.0, 2.0)
        self.assertTrue(result.converged)
        self.assertLess(result.iterations, 20)
        assert result.bracket is not None and result.absolute_error_bound is not None
        expected = math.log(3.0)
        self.assertLessEqual(result.bracket[0], expected)
        self.assertGreaterEqual(result.bracket[1], expected)
        self.assertLessEqual(abs(result.root - expected), result.absolute_error_bound)

    def test_comparison_report_is_deterministic_and_exposes_failure(self) -> None:
        first = execute_comparison()
        second = execute_comparison()
        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], 2)
        cycle = [
            result
            for result in first["results"]
            if result["case_id"] == "newton_cycle"
        ]
        by_method = {result["method"]: result for result in cycle}
        self.assertFalse(by_method["newton_raphson"]["converged"])
        self.assertTrue(by_method["bounded_newton_raphson"]["converged"])
        self.assertTrue(by_method["interval_newton"]["converged"])
        self.assertTrue(by_method["ridders"]["converged"])

    def test_comparison_writers_refuse_unapproved_overwrite(self) -> None:
        report = execute_comparison()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            json_path = root / "comparison.json"
            csv_path = root / "comparison.csv"
            write_report(json_path, report)
            write_csv(csv_path, report)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), report)
            self.assertIn("bounded_newton_raphson", csv_path.read_text(encoding="utf-8"))
            with self.assertRaises(FileExistsError):
                write_report(json_path, report)
            with self.assertRaises(FileExistsError):
                write_csv(csv_path, report)


if __name__ == "__main__":
    unittest.main()
