from __future__ import annotations

import math
import unittest

from babcs import BABCSConfig, BoundedAdamsBashforthIntegrator, Simulator
from tests.support.analytic import driven_rc_voltage, parallel_rlc_state, rc_voltage, rl_current
from tests.support.circuits import (
    driven_rc_circuit,
    parallel_rlc_circuit,
    rc_charge_circuit,
    rl_step_circuit,
)
from tests.support.metrics import observed_order, sinusoidal_amplitude_phase
from tests.support.raw_ab2 import integrate_raw_ab2


class AccuracyAndConvergenceTests(unittest.TestCase):
    def test_backward_euler_is_first_order_on_rc(self) -> None:
        errors = [self._rc_error("backward_euler", step) for step in (1.0e-4, 5.0e-5, 2.5e-5)]
        for order in self._orders(errors):
            self.assertGreater(order, 0.8)
            self.assertLess(order, 1.2)

    def test_trapezoidal_is_second_order_on_rl(self) -> None:
        errors = [self._rl_error("trapezoidal", step) for step in (1.0e-5, 5.0e-6, 2.5e-6)]
        for order in self._orders(errors):
            self.assertGreater(order, 1.8)
            self.assertLess(order, 2.2)

    def test_bdf2_is_second_order_on_rc(self) -> None:
        errors = [self._rc_error("bdf2", step) for step in (1.0e-4, 5.0e-5, 2.5e-5)]
        for order in self._orders(errors):
            self.assertGreater(order, 1.8)
            self.assertLess(order, 2.3)

    def test_raw_ab2_is_second_order_on_rl_reduced_system(self) -> None:
        def error(step: float) -> float:
            resistance = 10.0
            inductance = 1.0e-3
            source_voltage = 1.0
            points = integrate_raw_ab2(
                lambda time, state: ((source_voltage - resistance * state[0]) / inductance,),
                (0.0,),
                1.0e-4,
                step,
            )
            exact = rl_current(
                1.0e-4,
                resistance=resistance,
                inductance=inductance,
                source_voltage=source_voltage,
                initial_current=0.0,
            )
            return abs(points[-1].state[0] - exact)

        errors = [error(step) for step in (1.0e-5, 5.0e-6, 2.5e-6)]
        for order in self._orders(errors):
            self.assertGreater(order, 1.7)
            self.assertLess(order, 2.3)

    def test_active_babcs_error_decreases_under_refinement(self) -> None:
        errors = [self._rc_error("trapezoidal", step, mode="active") for step in (1.0e-4, 5.0e-5, 2.5e-5)]
        self.assertGreater(errors[0], errors[1])
        self.assertGreater(errors[1], errors[2])
        for order in self._orders(errors):
            self.assertGreater(order, 1.5)

    def test_shadow_matches_backward_euler_authority(self) -> None:
        circuit = rc_charge_circuit()
        disabled = self._run(circuit, "backward_euler", 2.0e-4, 1.0e-5, mode="disabled")
        shadow = self._run(circuit, "backward_euler", 2.0e-4, 1.0e-5, mode="shadow")
        self.assertEqual(len(disabled.points), len(shadow.points))
        for disabled_point, shadow_point in zip(disabled.points, shadow.points, strict=True):
            self.assertAlmostEqual(disabled_point.time, shadow_point.time, places=16)
            for disabled_value, shadow_value in zip(
                disabled_point.state.evaluation.dynamic_state,
                shadow_point.state.evaluation.dynamic_state,
                strict=True,
            ):
                self.assertAlmostEqual(disabled_value, shadow_value, delta=1.0e-12)

    def test_trapezoidal_matches_underdamped_rlc_solution(self) -> None:
        resistance = 100.0
        capacitance = 1.0e-6
        inductance = 1.0e-3
        stop_time = 5.0e-4

        def error(step: float) -> float:
            result = self._run(
                parallel_rlc_circuit(
                    resistance=resistance,
                    capacitance=capacitance,
                    inductance=inductance,
                ),
                "trapezoidal",
                stop_time,
                step,
            )
            exact = parallel_rlc_state(
                stop_time,
                resistance=resistance,
                capacitance=capacitance,
                inductance=inductance,
                initial_voltage=1.0,
                initial_current=0.0,
            )
            actual = result.points[-1].state.evaluation.dynamic_state
            return math.sqrt(sum((left - right) ** 2 for left, right in zip(actual, exact, strict=True)))

        coarse = error(2.0e-6)
        fine = error(1.0e-6)
        self.assertGreater(observed_order(coarse, fine), 1.8)

    def test_trapezoidal_matches_overdamped_rlc_solution(self) -> None:
        resistance = 10.0
        capacitance = 1.0e-6
        inductance = 1.0e-3
        stop_time = 2.0e-4
        result = self._run(
            parallel_rlc_circuit(
                resistance=resistance,
                capacitance=capacitance,
                inductance=inductance,
            ),
            "trapezoidal",
            stop_time,
            5.0e-7,
        )
        exact = parallel_rlc_state(
            stop_time,
            resistance=resistance,
            capacitance=capacitance,
            inductance=inductance,
            initial_voltage=1.0,
            initial_current=0.0,
        )
        for actual, expected in zip(
            result.points[-1].state.evaluation.dynamic_state,
            exact,
            strict=True,
        ):
            self.assertAlmostEqual(actual, expected, delta=3.0e-6)

    def test_rc_discharge_matches_analytic_solution(self) -> None:
        circuit = rc_charge_circuit(source_voltage=0.0, initial_voltage=1.0)
        result = self._run(circuit, "trapezoidal", 1.0e-3, 1.0e-5)
        exact = rc_voltage(
            1.0e-3,
            resistance=1_000.0,
            capacitance=1.0e-6,
            source_voltage=0.0,
            initial_voltage=1.0,
        )
        self.assertAlmostEqual(result.points[-1].state.evaluation.dynamic_state[0], exact, delta=4.0e-6)

    def test_rl_decay_matches_analytic_solution(self) -> None:
        circuit = rl_step_circuit(source_voltage=0.0, initial_current=0.1)
        result = self._run(circuit, "trapezoidal", 1.0e-4, 1.0e-6)
        exact = rl_current(
            1.0e-4,
            resistance=10.0,
            inductance=1.0e-3,
            source_voltage=0.0,
            initial_current=0.1,
        )
        self.assertAlmostEqual(result.points[-1].state.evaluation.dynamic_state[0], exact, delta=4.0e-6)

    def test_driven_rc_amplitude_and_phase_solution(self) -> None:
        stop_time = 2.8e-2
        result = self._run(driven_rc_circuit(), "trapezoidal", stop_time, 1.0e-5)
        exact = driven_rc_voltage(
            stop_time,
            resistance=1_000.0,
            capacitance=1.0e-6,
            amplitude=1.0,
            frequency=250.0,
            initial_voltage=0.0,
        )
        self.assertAlmostEqual(
            result.points[-1].state.evaluation.dynamic_state[0],
            exact,
            delta=4.0e-6,
        )
        fitted = sinusoidal_amplitude_phase(
            result.dynamic_trace(0),
            250.0,
            start_time=1.2e-2,
        )
        angular_tau = 2.0 * math.pi * 250.0 * 1_000.0 * 1.0e-6
        expected_amplitude = 1.0 / math.sqrt(1.0 + angular_tau * angular_tau)
        expected_phase = -math.atan(angular_tau)
        phase_error = math.atan2(
            math.sin(fitted["phase_radians"] - expected_phase),
            math.cos(fitted["phase_radians"] - expected_phase),
        )
        self.assertAlmostEqual(fitted["amplitude"], expected_amplitude, delta=2.0e-5)
        self.assertAlmostEqual(phase_error, 0.0, delta=3.0e-5)

    def _rc_error(self, method: str, step: float, *, mode: str = "disabled") -> float:
        result = self._run(rc_charge_circuit(), method, 1.0e-3, step, mode=mode)
        exact = rc_voltage(
            1.0e-3,
            resistance=1_000.0,
            capacitance=1.0e-6,
            source_voltage=1.0,
            initial_voltage=0.0,
        )
        return abs(result.points[-1].state.evaluation.dynamic_state[0] - exact)

    def _rl_error(self, method: str, step: float) -> float:
        result = self._run(rl_step_circuit(), method, 1.0e-4, step)
        exact = rl_current(
            1.0e-4,
            resistance=10.0,
            inductance=1.0e-3,
            source_voltage=1.0,
            initial_current=0.0,
        )
        return abs(result.points[-1].state.evaluation.dynamic_state[0] - exact)

    @staticmethod
    def _run(circuit, method: str, stop_time: float, step: float, *, mode: str = "disabled"):
        config = BABCSConfig(
            rollout_mode=mode,
            reference_method=method,
            startup_method="backward_euler",
            predictor_reference_cap=1.0e12,
            anchor_reference_cap=1.0e12,
            energy_injection_cap=1.0e12,
            stiffness_limit=1.0e12,
            anchor_interval_steps=1_000_000,
        )
        return Simulator(BoundedAdamsBashforthIntegrator(config)).run(circuit, stop_time, step)

    @staticmethod
    def _orders(errors: list[float]) -> tuple[float, ...]:
        return tuple(observed_order(left, right) for left, right in zip(errors, errors[1:]))


if __name__ == "__main__":
    unittest.main()
