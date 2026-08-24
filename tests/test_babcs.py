from __future__ import annotations

import math
import unittest

from babcs import (
    BABCSConfig,
    BoundedAdamsBashforthIntegrator,
    Capacitor,
    Circuit,
    Inductor,
    Pulse,
    Resistor,
    Simulator,
    VoltageSource,
)
from babcs.bounded import StepRejected, variable_step_ab2_predict
from babcs.waveforms import Constant


def rc_circuit(time_constant: float = 1.0e-3) -> Circuit:
    capacitance = 1.0e-6
    return Circuit(
        [
            VoltageSource("V1", "vin", "0", Constant(1.0)),
            Resistor("R1", "vin", "out", time_constant / capacitance),
            Capacitor("C1", "out", "0", capacitance),
        ]
    )


class BoundedAdamsBashforthTests(unittest.TestCase):
    def test_variable_step_ab2_coefficients(self) -> None:
        prediction = variable_step_ab2_predict(
            current_state=(1.0,),
            current_derivative=(2.0,),
            previous_derivative=(0.5,),
            step=0.2,
            previous_step=0.1,
        )
        self.assertAlmostEqual(prediction[0], 1.7)

    def test_active_mode_is_contractive_and_accurate(self) -> None:
        circuit = rc_circuit()
        config = BABCSConfig(
            rollout_mode="active",
            predictor_reference_cap=100.0,
            anchor_reference_cap=100.0,
            anchor_interval_steps=10,
        )
        result = Simulator(BoundedAdamsBashforthIntegrator(config)).run(circuit, 1.0e-3, 1.0e-5)
        final_voltage = result.points[-1].state.evaluation.dynamic_state[0]
        self.assertAlmostEqual(final_voltage, 1.0 - math.exp(-1.0), delta=2.0e-6)
        ab_metrics = [point.metrics for point in result.points if point.metrics and point.metrics.ab_used]
        self.assertTrue(ab_metrics)
        self.assertTrue(all(metric.closed_loop_gain < 1.0 for metric in ab_metrics))
        self.assertTrue(
            all(metric.corrected_reference_error <= metric.predictor_reference_error for metric in ab_metrics)
        )
        self.assertGreater(result.final_history.periodic_reanchors, 0)

    def test_active_mode_reuses_previous_jacobian_norm(self) -> None:
        class CountingCircuit(Circuit):
            def __init__(self) -> None:
                super().__init__(
                    [
                        VoltageSource("V1", "vin", "0", Constant(1.0)),
                        Resistor("R1", "vin", "out", 1_000.0),
                        Capacitor("C1", "out", "0", 1.0e-6),
                    ]
                )
                self.jacobian_evaluations = 0

            def differential_jacobian(self, *args, **kwargs):
                self.jacobian_evaluations += 1
                return super().differential_jacobian(*args, **kwargs)

        circuit = CountingCircuit()
        integrator = BoundedAdamsBashforthIntegrator(
            BABCSConfig(
                rollout_mode="active",
                predictor_reference_cap=100.0,
                anchor_interval_steps=100,
            )
        )
        state, history = integrator.initialize(circuit)
        startup = integrator.step(circuit, state, history, 1.0e-5)
        first_ab = integrator.step(circuit, startup.state, startup.history, 1.0e-5)
        second_ab = integrator.step(circuit, first_ab.state, first_ab.history, 1.0e-5)

        self.assertEqual(first_ab.metrics.differential_jacobian_evaluations, 2)
        self.assertEqual(second_ab.metrics.differential_jacobian_evaluations, 1)
        self.assertEqual(circuit.jacobian_evaluations, 3)
        self.assertIsNotNone(second_ab.history.previous_jacobian_norm)

    def test_hard_predictor_cap_rejects_large_step(self) -> None:
        circuit = rc_circuit()
        integrator = BoundedAdamsBashforthIntegrator(
            BABCSConfig(
                rollout_mode="active",
                predictor_reference_cap=1.0e-3,
                energy_injection_cap=1.0e6,
                anchor_interval_steps=100,
            )
        )
        state, history = integrator.initialize(circuit)
        first = integrator.step(circuit, state, history, 1.0e-4)
        with self.assertRaises(StepRejected):
            integrator.step(circuit, first.state, first.history, 1.0e-4)

    def test_stiffness_gate_uses_implicit_authority(self) -> None:
        circuit = rc_circuit(1.0e-6)
        integrator = BoundedAdamsBashforthIntegrator(
            BABCSConfig(
                rollout_mode="active",
                predictor_reference_cap=1.0e9,
                energy_injection_cap=1.0e9,
                stiffness_limit=0.05,
                anchor_interval_steps=100,
            )
        )
        state, history = integrator.initialize(circuit)
        first = integrator.step(circuit, state, history, 1.0e-7)
        second = integrator.step(circuit, first.state, first.history, 1.0e-7)
        self.assertEqual(second.metrics.method, "implicit_stiffness_fallback")
        self.assertEqual(second.metrics.correction_gain, 1.0)

    def test_non_finite_amplification_fails_closed(self) -> None:
        class NonFiniteJacobianCircuit(Circuit):
            def differential_jacobian(self, time, dynamic_state, algebraic_guess=None):
                del time, dynamic_state, algebraic_guess
                return [[math.nan]]

        base = rc_circuit()
        circuit = NonFiniteJacobianCircuit(base.elements)
        integrator = BoundedAdamsBashforthIntegrator(
            BABCSConfig(
                rollout_mode="active",
                predictor_reference_cap=1.0e9,
                energy_injection_cap=1.0e9,
            )
        )
        state, history = integrator.initialize(circuit)
        first = integrator.step(circuit, state, history, 1.0e-5)
        with self.assertRaises(StepRejected):
            integrator.step(circuit, first.state, first.history, 1.0e-5)

    def test_shadow_mode_never_accepts_ab_state(self) -> None:
        circuit = rc_circuit()
        result = Simulator(
            BoundedAdamsBashforthIntegrator(
                BABCSConfig(rollout_mode="shadow", predictor_reference_cap=100.0)
            )
        ).run(circuit, 5.0e-5, 1.0e-5)
        shadow_metrics = [point.metrics for point in result.points if point.metrics and point.metrics.ab_used]
        self.assertTrue(shadow_metrics)
        self.assertTrue(all(metric.correction_gain == 1.0 for metric in shadow_metrics))
        self.assertTrue(all(metric.method == "shadow_reference_authority" for metric in shadow_metrics))
        self.assertTrue(all(metric.explicit_projection_count == 1 for metric in shadow_metrics))

    def test_disabled_mode_never_executes_ab(self) -> None:
        circuit = rc_circuit()
        result = Simulator(
            BoundedAdamsBashforthIntegrator(BABCSConfig(rollout_mode="disabled"))
        ).run(circuit, 5.0e-5, 1.0e-5)
        metrics = [point.metrics for point in result.points if point.metrics]
        self.assertTrue(metrics)
        self.assertTrue(all(not metric.ab_used for metric in metrics))
        self.assertTrue(all(metric.method == "implicit_authority" for metric in metrics))

    def test_tiny_anchor_cap_forces_safety_reanchor(self) -> None:
        circuit = rc_circuit()
        config = BABCSConfig(
            rollout_mode="active",
            predictor_reference_cap=100.0,
            anchor_reference_cap=1.0e-12,
            anchor_interval_steps=2,
        )
        result = Simulator(BoundedAdamsBashforthIntegrator(config)).run(circuit, 5.0e-5, 1.0e-5)
        safety_points = [point for point in result.points if point.metrics and point.metrics.safety_reanchor]
        self.assertTrue(safety_points)
        self.assertGreater(result.final_history.safety_reanchors, 0)
        self.assertTrue(all(point.state.method == "safety_reanchor" for point in safety_points))

    def test_pulse_breakpoint_resets_multistep_history(self) -> None:
        circuit = Circuit(
            [
                VoltageSource(
                    "V1",
                    "vin",
                    "0",
                    Pulse(low=0.0, high=1.0, delay=5.0e-4, rise=0.0, width=5.0e-4, fall=0.0),
                ),
                Resistor("R1", "vin", "out", 1_000.0),
                Capacitor("C1", "out", "0", 1.0e-6),
            ]
        )
        config = BABCSConfig(rollout_mode="active", predictor_reference_cap=100.0)
        result = Simulator(BoundedAdamsBashforthIntegrator(config)).run(circuit, 8.0e-4, 3.0e-4)
        event_index = next(
            index
            for index, point in enumerate(result.points)
            if point.event_boundary and abs(point.time - 5.0e-4) < 1.0e-15
        )
        self.assertFalse(result.points[event_index + 1].metrics.ab_used)
        self.assertGreaterEqual(result.final_history.generation, 1)

    def test_rejected_short_step_is_not_mislabeled_as_event(self) -> None:
        circuit = Circuit(
            [
                VoltageSource(
                    "V1",
                    "vin",
                    "0",
                    Pulse(low=0.0, high=1.0, delay=5.0e-4, rise=0.0, width=5.0e-4, fall=0.0),
                ),
                Resistor("R1", "vin", "out", 1_000.0),
                Capacitor("C1", "out", "0", 1.0e-6),
            ]
        )
        config = BABCSConfig(
            rollout_mode="active",
            predictor_reference_cap=1.0,
            maximum_rejections=20,
            energy_injection_cap=1.0e6,
        )
        result = Simulator(BoundedAdamsBashforthIntegrator(config)).run(circuit, 6.0e-4, 3.0e-4)
        event_points = [point for point in result.points if point.event_boundary]
        self.assertEqual(len(event_points), 1)
        self.assertAlmostEqual(event_points[0].time, 5.0e-4, places=15)
        self.assertTrue(all(not point.event_boundary for point in result.points if point.time < 5.0e-4))

    def test_lossless_lc_energy_is_bounded_by_periodic_reanchor(self) -> None:
        capacitance = 1.0e-6
        inductance = 1.0e-3
        period = 2.0 * math.pi * math.sqrt(capacitance * inductance)
        circuit = Circuit(
            [
                Capacitor("C1", "n", "0", capacitance, 1.0),
                Inductor("L1", "n", "0", inductance, 0.0),
            ]
        )
        config = BABCSConfig(
            rollout_mode="active",
            predictor_reference_cap=250.0,
            anchor_reference_cap=50.0,
            energy_injection_cap=20.0,
            anchor_interval_steps=20,
        )
        result = Simulator(BoundedAdamsBashforthIntegrator(config)).run(
            circuit,
            3.0 * period,
            period / 300.0,
        )
        energies = [point.state.evaluation.stored_energy for point in result.points]
        relative_span = (max(energies) - min(energies)) / energies[0]
        self.assertLess(relative_span, 2.0e-3)
        self.assertGreater(result.final_history.periodic_reanchors, 0)


if __name__ == "__main__":
    unittest.main()
