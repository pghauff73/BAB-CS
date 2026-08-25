from __future__ import annotations

import math
import unittest
from dataclasses import replace

from babcs import BABCSConfig, BoundedAdamsBashforthIntegrator
from babcs.bounded import variable_step_ab2_predict
from babcs.integrators import ImplicitSettings
from tests.support.circuits import rc_charge_circuit


class IntegratorBoundaryTests(unittest.TestCase):
    def test_config_rejects_invalid_boundaries(self) -> None:
        invalid_values = (
            {"absolute_tolerance": 0.0},
            {"relative_tolerance": math.inf},
            {"embedded_error_cap": 0.0},
            {"anchor_embedded_error_cap": 0.0},
            {"deferred_reference_bound_cap": math.inf},
            {"target_contraction": 0.0},
            {"target_contraction": 1.0},
            {"contraction_rate": 0.0},
            {"contraction_rate": math.inf},
            {"minimum_correction_gain": 0.8, "maximum_correction_gain": 0.7},
            {"maximum_step_ratio": 0.99},
            {"reference_interval_steps": 0},
            {"anchor_interval_steps": 0},
            {"anchor_substeps": 0},
            {"minimum_anchor_substeps": 0},
            {"anchor_substeps": 2, "minimum_anchor_substeps": 3},
            {"maximum_rejections": 0},
            {"rollout_mode": "raw"},
            {"candidate_method": "rk45"},
            {"reference_method": "explicit_euler"},
            {"startup_method": "explicit_euler"},
        )
        for values in invalid_values:
            with self.subTest(values=values), self.assertRaises(ValueError):
                BABCSConfig(**values)

    def test_implicit_settings_reject_invalid_boundaries(self) -> None:
        for values in (
            {"absolute_tolerance": 0.0},
            {"absolute_tolerance": math.inf},
            {"relative_tolerance": 0.0},
            {"relative_tolerance": math.nan},
            {"max_iterations": -1},
            {"minimum_damping": 0.0},
            {"minimum_damping": 1.1},
            {"minimum_damping": math.inf},
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                ImplicitSettings(**values)

    def test_ab2_is_exact_for_constant_and_linear_rates(self) -> None:
        constant = variable_step_ab2_predict((1.0,), (2.0,), (2.0,), 0.2, 0.1)
        self.assertAlmostEqual(constant[0], 1.4)
        linear = variable_step_ab2_predict((0.005,), (0.1,), (0.0,), 0.2, 0.1)
        self.assertAlmostEqual(linear[0], 0.045)

    def test_ab2_rejects_nonpositive_steps_and_dimension_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            variable_step_ab2_predict((1.0,), (1.0,), (1.0,), 0.0, 0.1)
        with self.assertRaises(ValueError):
            variable_step_ab2_predict((1.0,), (1.0, 2.0), (1.0,), 0.1, 0.1)

    def test_exact_step_ratio_boundaries_use_ab(self) -> None:
        for ratio in (0.5, 2.0):
            with self.subTest(ratio=ratio):
                integrator = self._integrator(maximum_step_ratio=2.0)
                circuit = rc_charge_circuit()
                state, history = integrator.initialize(circuit)
                first = integrator.step(circuit, state, history, 1.0e-5)
                second = integrator.step(circuit, first.state, first.history, ratio * 1.0e-5)
                self.assertTrue(second.metrics.ab_used)

    def test_outside_step_ratio_boundaries_restarts_implicitly(self) -> None:
        for ratio in (0.49, 2.01):
            with self.subTest(ratio=ratio):
                integrator = self._integrator(maximum_step_ratio=2.0)
                circuit = rc_charge_circuit()
                state, history = integrator.initialize(circuit)
                first = integrator.step(circuit, state, history, 1.0e-5)
                second = integrator.step(circuit, first.state, first.history, ratio * 1.0e-5)
                self.assertFalse(second.metrics.ab_used)
                self.assertTrue(second.metrics.method.endswith("_startup"))

    def test_stricter_contraction_target_increases_correction_gain(self) -> None:
        loose = self._second_step(target_contraction=0.9)
        strict = self._second_step(target_contraction=0.2)
        self.assertGreater(strict.metrics.correction_gain, loose.metrics.correction_gain)
        self.assertLessEqual(strict.metrics.closed_loop_gain, loose.metrics.closed_loop_gain)

    def test_impossible_configured_contraction_uses_reference_authority(self) -> None:
        circuit = rc_charge_circuit(resistance=1.0, capacitance=1.0e-6)
        integrator = self._integrator(
            minimum_correction_gain=0.1,
            maximum_correction_gain=0.1,
            stiffness_limit=100.0,
        )
        state, history = integrator.initialize(circuit)
        first = integrator.step(circuit, state, history, 1.0e-7)
        second = integrator.step(circuit, first.state, first.history, 1.0e-7)
        self.assertEqual(second.metrics.method, "implicit_contraction_fallback")
        self.assertEqual(second.metrics.correction_gain, 1.0)
        self.assertEqual(second.metrics.closed_loop_gain, 0.0)

    def _second_step(self, **overrides):
        circuit = rc_charge_circuit()
        integrator = self._integrator(**overrides)
        state, history = integrator.initialize(circuit)
        first = integrator.step(circuit, state, history, 1.0e-5)
        return integrator.step(circuit, first.state, first.history, 1.0e-5)

    @staticmethod
    def _integrator(**overrides) -> BoundedAdamsBashforthIntegrator:
        config = BABCSConfig(
            rollout_mode="active",
            predictor_reference_cap=1.0e9,
            anchor_reference_cap=1.0e9,
            energy_injection_cap=1.0e9,
            anchor_interval_steps=10_000,
            **overrides,
        )
        return BoundedAdamsBashforthIntegrator(config)


if __name__ == "__main__":
    unittest.main()
