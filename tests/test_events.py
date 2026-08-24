from __future__ import annotations

import unittest

from babcs import BABCSConfig, BoundedAdamsBashforthIntegrator, Simulator
from tests.support.circuits import (
    piecewise_linear_rc_circuit,
    pulsed_rc_circuit,
    switched_rc_circuit,
)


class EventQualificationTests(unittest.TestCase):
    def test_piecewise_linear_breakpoints_are_each_reached_once(self) -> None:
        result = self._run(piecewise_linear_rc_circuit(), 5.0e-4, 8.0e-5)
        event_times = [point.time for point in result.points if point.event_boundary]
        expected = [2.0e-4, 2.2e-4, 2.4e-4, 4.0e-4]
        self.assertEqual(len(event_times), len(expected))
        for actual, target in zip(event_times, expected, strict=True):
            self.assertAlmostEqual(actual, target, places=15)

    def test_finite_rise_and_fall_breakpoints_reset_history(self) -> None:
        result = self._run(
            pulsed_rc_circuit(rise=2.0e-5, fall=3.0e-5),
            1.2e-3,
            7.0e-5,
        )
        event_indices = [index for index, point in enumerate(result.points) if point.event_boundary]
        self.assertGreaterEqual(len(event_indices), 4)
        for index in event_indices:
            self.assertEqual(result.points[index].history_reset_reason, "event")
            if index + 1 < len(result.points):
                metrics = result.points[index + 1].metrics
                assert metrics is not None
                self.assertFalse(metrics.ab_used)

    def test_repeated_switch_transitions_preserve_exact_event_times(self) -> None:
        result = self._run(switched_rc_circuit(), 9.0e-4, 7.0e-5)
        event_times = [point.time for point in result.points if point.event_boundary]
        expected = [1.0e-4, 2.0e-4, 5.0e-4, 6.0e-4, 9.0e-4]
        self.assertEqual(len(event_times), len(expected))
        for actual, target in zip(event_times, expected, strict=True):
            self.assertAlmostEqual(actual, target, places=15)
        self.assertGreaterEqual(result.final_history.rejected_steps, 1)

    @staticmethod
    def _run(circuit, stop_time: float, step: float):
        config = BABCSConfig(
            rollout_mode="active",
            predictor_reference_cap=1.0e6,
            anchor_reference_cap=1.0e6,
            energy_injection_cap=1.0e6,
            stiffness_limit=1.0e6,
            anchor_interval_steps=20,
        )
        return Simulator(BoundedAdamsBashforthIntegrator(config)).run(circuit, stop_time, step)


if __name__ == "__main__":
    unittest.main()
