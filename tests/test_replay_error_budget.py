from decimal import Decimal, localcontext
from fractions import Fraction as F
import unittest

from tools.replay_error_budget import (
    CASES, Case, exp_bounds, growth_factors, hermite_defect,
    logarithmic_norm_upper, point_step, propagate, run_case,
)


class ReplayErrorBudgetTests(unittest.TestCase):
    def test_rational_exponential_encloses_high_precision_values(self):
        with localcontext() as context:
            context.prec = 100
            for value in (F(-1), F(-1, 20), F(0), F(1, 1000), F(1)):
                lower, upper = exp_bounds(value)
                exact = (Decimal(value.numerator) / Decimal(value.denominator)).exp()
                self.assertLessEqual(Decimal(lower.numerator) / Decimal(lower.denominator), exact)
                self.assertGreaterEqual(Decimal(upper.numerator) / Decimal(upper.denominator), exact)

    def test_contracting_growing_and_neutral_growth_factors(self):
        for mu in (F(-2), F(0), F(2)):
            growth, integral = growth_factors(mu, F(1, 10))
            with localcontext() as context:
                context.prec = 80
                expected = (Decimal(mu.numerator) / Decimal(mu.denominator) / 10).exp()
                self.assertGreaterEqual(Decimal(growth.numerator) / Decimal(growth.denominator), expected)
                expected_integral = Decimal('0.1') if mu == 0 else (expected - 1) / Decimal(mu.numerator)
                self.assertGreaterEqual(Decimal(integral.numerator) / Decimal(integral.denominator), expected_integral)

    def test_exact_affine_solution_has_zero_defect(self):
        self.assertEqual(hermite_defect(((F(0),),), (F(2),), (F(3),),
                                        (F(4),), F(1, 2), "infinity"), 0)

    def test_endpoint_rounding_is_accounted_for(self):
        defect = hermite_defect(((F(0),),), (F(0),), (F(0),),
                               (F(1, 10**24),), F(1), "infinity")
        self.assertGreater(defect, 0)
        self.assertGreaterEqual(propagate(F(0), defect, F(0), F(1)), F(1, 10**24))

    def test_trapezoidal_defect_covers_known_endpoint_error(self):
        a, b, x, h = ((F(-1),),), (F(0),), (F(1),), F(1, 10)
        y = point_step(a, b, x, h, "trapezoidal")
        radius = propagate(F(0), hermite_defect(a, b, x, y, h, "infinity"), F(-1), h)
        with localcontext() as context:
            context.prec = 80
            exact = Decimal('-0.1').exp()
            approx = Decimal(y[0].numerator) / Decimal(y[0].denominator)
            self.assertLessEqual(abs(exact - approx), Decimal(radius.numerator) / Decimal(radius.denominator))

    def test_energy_norm_avoids_spurious_lc_growth(self):
        self.assertEqual(logarithmic_norm_upper(CASES[3].matrix, "euclidean"), 0)
        self.assertEqual(logarithmic_norm_upper(CASES[3].matrix, "infinity"), 1)

    def test_nonnormal_stable_matrix_is_not_assumed_contractive(self):
        a = ((F(-1), F(10)), (F(0), F(-1)))
        self.assertEqual(logarithmic_norm_upper(a, "infinity"), 9)
        with self.assertRaisesRegex(ValueError, "negative semidefinite"):
            logarithmic_norm_upper(a, "euclidean")

    def test_replay_preserves_uncertainty_when_dynamics_are_constant(self):
        case = Case("constant", ((F(0),),), (F(0),), (F(0),), (F(0),), "infinity")
        row = run_case(case, F(1, 10), 2, initial_radius=F(1, 100), stop=F(1))
        for point in row["points"]:
            self.assertEqual(F(point["radius"]), F(1, 100))
            if point["replay"]:
                self.assertEqual(F(point["fresh_replay_defect_radius"]), 0)
                self.assertEqual(F(point["inherited_anchor_radius"]), F(1, 100))

    def test_refinement_reduces_replay_error_and_radius(self):
        coarse = run_case(CASES[0], F(1, 10), 4, refinement=1, stop=F(4, 5))
        fine = run_case(CASES[0], F(1, 10), 4, refinement=4, stop=F(4, 5))
        self.assertLess(F(fine["final_radius"]), F(coarse["final_radius"]))
        self.assertLess(fine["final_central_error_diagnostic"], coarse["final_central_error_diagnostic"])

    def test_longer_replay_windows_do_not_save_substeps(self):
        short = run_case(CASES[0], F(1, 10), 1, stop=F(4, 5))
        long = run_case(CASES[0], F(1, 10), 4, stop=F(4, 5))
        self.assertEqual(short["replay_steps"], long["replay_steps"])
        self.assertEqual(short["points"][-1]["state"], long["points"][-1]["state"])
        self.assertGreater(long["max_central_error_diagnostic"], short["max_central_error_diagnostic"])

    def test_reference_only_baseline_has_no_candidate_work(self):
        baseline = run_case(CASES[0], F(1, 10), 1, stop=F(2, 5), reference_only=True)
        replay = run_case(CASES[0], F(1, 10), 1, stop=F(2, 5))
        self.assertEqual(baseline["candidate_steps"], 0)
        self.assertEqual(baseline["final_radius"], replay["final_radius"])
        self.assertEqual(baseline["points"][-1]["state"], replay["points"][-1]["state"])

    def test_scheduled_event_retains_nonzero_total_radius(self):
        row = run_case(CASES[4], F(1, 10), 4, initial_radius=F(1, 1000))
        event = next(p for p in row["points"] if F(p["time"]) == 1)
        self.assertTrue(event["replay"])
        self.assertGreater(F(event["inherited_anchor_radius"]), 0)
        self.assertTrue(row["all_diagnostics_covered"])

    def test_all_circuit_families_cover_independent_diagnostics(self):
        for case in CASES:
            with self.subTest(case=case.name):
                self.assertTrue(run_case(case, F(1, 10), 4, stop=F(6, 5))["all_diagnostics_covered"])

    def test_invalid_or_unsupported_cases_fail_explicitly(self):
        with self.assertRaisesRegex(ValueError, "abs"):
            exp_bounds(F(2))
        with self.assertRaisesRegex(ValueError, "positive"):
            growth_factors(F(0), F(0))
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            propagate(F(-1), F(0), F(0), F(1))
        with self.assertRaisesRegex(ValueError, "event"):
            run_case(CASES[4], F(2, 5), 4)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            run_case(CASES[0], F(1, 10), 0)


if __name__ == "__main__":
    unittest.main()
