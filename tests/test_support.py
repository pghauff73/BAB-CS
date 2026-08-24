from __future__ import annotations

import math
import unittest

from tests.support.analytic import driven_rc_voltage, parallel_rlc_state, rc_voltage, rl_current
from tests.support.metrics import (
    error_metrics,
    estimated_period,
    interpolate_trace,
    observed_order,
    sinusoidal_amplitude_phase,
)
from tests.support.raw_ab2 import integrate_raw_ab2


class QualificationSupportTests(unittest.TestCase):
    def test_analytic_solutions_preserve_initial_conditions(self) -> None:
        self.assertEqual(
            rc_voltage(
                0.0,
                resistance=1_000.0,
                capacitance=1.0e-6,
                source_voltage=1.0,
                initial_voltage=0.25,
            ),
            0.25,
        )
        self.assertAlmostEqual(
            rl_current(
                0.0,
                resistance=10.0,
                inductance=1.0e-3,
                source_voltage=1.0,
                initial_current=0.025,
            ),
            0.025,
        )
        voltage, current = parallel_rlc_state(
            0.0,
            resistance=100.0,
            capacitance=1.0e-6,
            inductance=1.0e-3,
            initial_voltage=1.0,
            initial_current=0.1,
        )
        self.assertAlmostEqual(voltage, 1.0)
        self.assertAlmostEqual(current, 0.1)
        self.assertAlmostEqual(
            driven_rc_voltage(
                0.0,
                resistance=1_000.0,
                capacitance=1.0e-6,
                amplitude=1.0,
                frequency=100.0,
                initial_voltage=0.2,
            ),
            0.2,
        )
        self.assertAlmostEqual(
            rc_voltage(
                1.0e-3,
                resistance=1_000.0,
                capacitance=1.0e-6,
                source_voltage=1.0,
                initial_voltage=0.0,
            ),
            1.0 - math.exp(-1.0),
        )
        self.assertAlmostEqual(
            rl_current(
                1.0e-4,
                resistance=10.0,
                inductance=1.0e-3,
                source_voltage=1.0,
                initial_current=0.0,
            ),
            0.1 * (1.0 - math.exp(-1.0)),
        )

    def test_trace_interpolation_and_error_metrics(self) -> None:
        trace = ((0.0, 0.0), (1.0, 2.0), (2.0, 2.0))
        self.assertEqual(interpolate_trace(trace, 0.5), 1.0)
        metrics = error_metrics((1.0, 2.0), (0.5, 2.25))
        self.assertEqual(metrics["final_absolute_error"], 0.25)
        self.assertEqual(metrics["maximum_absolute_error"], 0.5)
        self.assertAlmostEqual(observed_order(0.04, 0.01), 2.0)
        with self.assertRaises(ValueError):
            error_metrics((1.0,), (1.0, 2.0))
        with self.assertRaises(ValueError):
            interpolate_trace(((0.0, 0.0), (0.0, 1.0)), 0.0)

    def test_period_estimator_uses_positive_zero_crossings(self) -> None:
        step = 0.01
        trace = tuple((index * step, math.sin(2.0 * math.pi * index * step)) for index in range(301))
        self.assertAlmostEqual(estimated_period(trace), 1.0, delta=1.0e-12)

    def test_sinusoidal_fit_recovers_offset_amplitude_and_phase(self) -> None:
        phase = 0.4
        trace = tuple(
            (
                index / 100.0,
                0.3 + 2.0 * math.sin(2.0 * math.pi * index / 100.0 + phase),
            )
            for index in range(401)
        )
        fitted = sinusoidal_amplitude_phase(trace, 1.0)
        self.assertAlmostEqual(fitted["offset"], 0.3, places=12)
        self.assertAlmostEqual(fitted["amplitude"], 2.0, places=12)
        self.assertAlmostEqual(fitted["phase_radians"], phase, places=12)

    def test_raw_ab2_converges_at_second_order(self) -> None:
        def error(step: float) -> float:
            points = integrate_raw_ab2(
                lambda time, state: (-state[0],),
                (1.0,),
                1.0,
                step,
            )
            return abs(points[-1].state[0] - math.exp(-1.0))

        order = observed_order(error(0.05), error(0.025))
        self.assertGreater(order, 1.8)
        self.assertLess(order, 2.2)


if __name__ == "__main__":
    unittest.main()
