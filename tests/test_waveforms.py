from __future__ import annotations

import math
import unittest

from babcs import PiecewiseLinear, Pulse, Sine
from babcs.waveforms import Constant


class WaveformTests(unittest.TestCase):
    def test_piecewise_linear_interpolates_and_reports_breakpoints(self) -> None:
        waveform = PiecewiseLinear(((0.0, 0.0), (1.0, 2.0), (3.0, 0.0)))
        self.assertAlmostEqual(waveform.value(0.5), 1.0)
        self.assertAlmostEqual(waveform.value(2.0), 1.0)
        self.assertEqual(waveform.breakpoints(0.25, 2.5), [1.0])

    def test_periodic_pulse_reports_each_transition(self) -> None:
        waveform = Pulse(0.0, 1.0, delay=1.0, rise=0.1, width=0.2, fall=0.1, period=1.0)
        self.assertEqual(waveform.breakpoints(0.0, 2.0), [1.0, 1.1, 1.3, 1.4, 2.0])
        self.assertAlmostEqual(waveform.value(1.05), 0.5)
        self.assertAlmostEqual(waveform.value(1.2), 1.0)

    def test_non_finite_waveform_parameters_are_rejected(self) -> None:
        for constructor in (
            lambda: Constant(math.nan),
            lambda: Sine(0.0, 1.0, math.inf),
            lambda: PiecewiseLinear(((0.0, 0.0), (1.0, math.nan))),
            lambda: Pulse(0.0, 1.0, 0.0, 0.0, math.inf, 0.0),
        ):
            with self.subTest(constructor=constructor), self.assertRaises(ValueError):
                constructor()


if __name__ == "__main__":
    unittest.main()
