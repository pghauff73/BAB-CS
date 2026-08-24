from __future__ import annotations

import math
import os
import unittest

from babcs import BABCSConfig, BoundedAdamsBashforthIntegrator, Capacitor, Circuit, Inductor, Resistor, Simulator
from tests.support.circuits import parallel_rlc_circuit
from tests.support.metrics import estimated_period
from tests.support.raw_ab2 import integrate_raw_ab2


class LongHorizonQualificationTests(unittest.TestCase):
    def test_ten_period_lc_tracks_energy_and_phase_separately(self) -> None:
        result, period = self._active_lc(periods=10, steps_per_period=120, anchor_interval=20)
        energies = [point.state.evaluation.stored_energy for point in result.points]
        relative_energy_span = (max(energies) - min(energies)) / energies[0]
        relative_period_error = abs(estimated_period(result.dynamic_trace(0)) - period) / period
        self.assertLess(relative_energy_span, 3.0e-3)
        self.assertLess(relative_period_error, 2.0e-5)
        self.assertGreater(result.final_history.periodic_reanchors, 0)

    def test_anchor_interval_sweep_remains_finite_and_contracting(self) -> None:
        for interval in (5, 20, 100):
            with self.subTest(anchor_interval=interval):
                result, _ = self._active_lc(periods=3, steps_per_period=120, anchor_interval=interval)
                metrics = [point.metrics for point in result.points if point.metrics]
                self.assertTrue(all(math.isfinite(metric.estimated_bound) for metric in metrics))
                self.assertTrue(all(metric.closed_loop_gain < 1.0 for metric in metrics))
                self.assertGreater(result.final_history.periodic_reanchors, 0)

    def test_damped_rlc_energy_decays(self) -> None:
        circuit = parallel_rlc_circuit(resistance=100.0)
        result = self._run(circuit, 2.0e-3, 1.0e-6, mode="active", anchor_interval=50)
        energies = [point.state.evaluation.stored_energy for point in result.points]
        self.assertLess(energies[-1], 1.0e-4 * energies[0])
        self.assertLess(max(energies), 1.001 * energies[0])

    def test_source_free_rc_and_rl_energy_are_monotone(self) -> None:
        cases = (
            (
                Circuit(
                    [Capacitor("C1", "n", "0", 1.0e-6, 1.0), Resistor("R1", "n", "0", 1_000.0)]
                ),
                5.0e-3,
            ),
            (
                Circuit(
                    [Inductor("L1", "n", "0", 1.0e-3, 0.1), Resistor("R1", "n", "0", 10.0)]
                ),
                5.0e-4,
            ),
        )
        for circuit, stop_time in cases:
            with self.subTest(dynamic_names=circuit.dynamic_names):
                result = self._run(circuit, stop_time, 2.0e-6, mode="disabled", anchor_interval=10_000)
                energies = [point.state.evaluation.stored_energy for point in result.points]
                self.assertTrue(
                    all(
                        right <= left * (1.0 + 1.0e-12) + 1.0e-18
                        for left, right in zip(energies, energies[1:])
                    )
                )

    def test_active_lc_improves_phase_over_raw_ab2_at_equal_step(self) -> None:
        active, period = self._active_lc(periods=10, steps_per_period=120, anchor_interval=20)
        raw = integrate_raw_ab2(
            lambda time, state: (-state[1] / 1.0e-6, state[0] / 1.0e-3),
            (1.0, 0.0),
            10.0 * period,
            period / 120.0,
        )
        active_phase_error = abs(estimated_period(active.dynamic_trace(0)) - period)
        raw_phase_error = abs(estimated_period(tuple((point.time, point.state[0]) for point in raw)) - period)
        self.assertLess(active_phase_error, raw_phase_error)

    @unittest.skipUnless(os.environ.get("BABCS_LONG_TESTS") == "1", "scheduled qualification")
    def test_hundred_period_lc(self) -> None:
        result, period = self._active_lc(periods=100, steps_per_period=120, anchor_interval=20)
        energies = [point.state.evaluation.stored_energy for point in result.points]
        self.assertLess((max(energies) - min(energies)) / energies[0], 3.0e-3)
        self.assertLess(abs(estimated_period(result.dynamic_trace(0)) - period) / period, 2.0e-5)

    @unittest.skipUnless(os.environ.get("BABCS_VERY_LONG_TESTS") == "1", "release qualification")
    def test_thousand_period_lc(self) -> None:
        result, period = self._active_lc(periods=1_000, steps_per_period=120, anchor_interval=20)
        energies = [point.state.evaluation.stored_energy for point in result.points]
        self.assertLess((max(energies) - min(energies)) / energies[0], 3.0e-3)
        self.assertLess(abs(estimated_period(result.dynamic_trace(0)) - period) / period, 2.0e-5)

    def _active_lc(self, *, periods: int, steps_per_period: int, anchor_interval: int):
        capacitance = 1.0e-6
        inductance = 1.0e-3
        period = 2.0 * math.pi * math.sqrt(capacitance * inductance)
        result = self._run(
            parallel_rlc_circuit(capacitance=capacitance, inductance=inductance),
            periods * period,
            period / steps_per_period,
            mode="active",
            anchor_interval=anchor_interval,
        )
        return result, period

    @staticmethod
    def _run(circuit, stop_time: float, step: float, *, mode: str, anchor_interval: int):
        config = BABCSConfig(
            rollout_mode=mode,
            predictor_reference_cap=1.0e9,
            anchor_reference_cap=1.0e9,
            energy_injection_cap=1.0e9,
            stiffness_limit=1.0e9,
            anchor_interval_steps=anchor_interval,
        )
        return Simulator(BoundedAdamsBashforthIntegrator(config)).run(circuit, stop_time, step)


if __name__ == "__main__":
    unittest.main()
