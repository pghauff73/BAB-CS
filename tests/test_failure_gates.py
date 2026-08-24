from __future__ import annotations

import unittest
from dataclasses import replace

from babcs import BABCSConfig, BoundedAdamsBashforthIntegrator, Circuit, Simulator
from babcs.bounded import StepRejected
from babcs.integrators import ImplicitSettings
from babcs.model import CircuitSolveError
from tests.support.circuits import rc_charge_circuit


class FailureGateTests(unittest.TestCase):
    def test_requested_step_below_minimum_is_rejected_without_history_change(self) -> None:
        circuit = rc_charge_circuit()
        integrator = BoundedAdamsBashforthIntegrator(BABCSConfig(minimum_step=1.0e-6))
        state, history = integrator.initialize(circuit)
        with self.assertRaisesRegex(StepRejected, "below the configured minimum"):
            integrator.step(circuit, state, history, 5.0e-7)
        self.assertEqual(history.accepted_steps, 0)
        self.assertIsNone(history.previous_evaluation)

    def test_reference_nonconvergence_is_rejected(self) -> None:
        circuit = rc_charge_circuit()
        integrator = BoundedAdamsBashforthIntegrator(
            BABCSConfig(
                rollout_mode="active",
                implicit_settings=ImplicitSettings(max_iterations=0),
            )
        )
        state, history = integrator.initialize(circuit)
        with self.assertRaisesRegex(StepRejected, "implicit startup failed"):
            integrator.step(circuit, state, history, 1.0e-4)

    def test_algebraic_residual_cap_has_distinct_rejection(self) -> None:
        circuit = _HighAlgebraicResidualCircuit(rc_charge_circuit().elements, after=1.5e-5)
        integrator = _permissive_integrator(algebraic_residual_cap=1.0e-8)
        state, history = integrator.initialize(circuit)
        first = integrator.step(circuit, state, history, 1.0e-5)
        with self.assertRaisesRegex(StepRejected, "algebraic residual cap exceeded"):
            integrator.step(circuit, first.state, first.history, 1.0e-5)

    def test_full_residual_cap_has_distinct_rejection(self) -> None:
        circuit = _HighFullResidualCircuit(rc_charge_circuit().elements, after=1.5e-5)
        integrator = _permissive_integrator(full_residual_cap=1.0e-8)
        state, history = integrator.initialize(circuit)
        first = integrator.step(circuit, state, history, 1.0e-5)
        with self.assertRaisesRegex(StepRejected, "full residual cap exceeded"):
            integrator.step(circuit, first.state, first.history, 1.0e-5)

    def test_failed_corrected_projection_transfers_reference_authority(self) -> None:
        circuit = _CorrectedProjectionFailureCircuit(rc_charge_circuit().elements)
        integrator = _permissive_integrator()
        state, history = integrator.initialize(circuit)
        first = integrator.step(circuit, state, history, 1.0e-5)
        second = integrator.step(circuit, first.state, first.history, 1.0e-5)
        self.assertEqual(second.metrics.method, "implicit_projection_fallback")
        self.assertEqual(second.metrics.correction_gain, 1.0)
        self.assertEqual(second.metrics.explicit_projection_count, 1)

    def test_energy_cap_rejects_even_implicit_authority(self) -> None:
        circuit = rc_charge_circuit()
        integrator = _InjectedEnergyIntegrator(
            BABCSConfig(rollout_mode="disabled", energy_injection_cap=1.0)
        )
        state, history = integrator.initialize(circuit)
        with self.assertRaisesRegex(StepRejected, "implicit authority energy cap exceeded"):
            integrator.step(circuit, state, history, 1.0e-5)

    def test_failed_independent_replay_is_rejected(self) -> None:
        circuit = _ToggleFailureCircuit(rc_charge_circuit().elements)
        integrator = _permissive_integrator(anchor_interval_steps=1)
        state, history = integrator.initialize(circuit)
        result = integrator.step(circuit, state, history, 1.0e-5)
        circuit.fail = True
        with self.assertRaisesRegex(StepRejected, "independent re-anchor failed"):
            integrator.reanchor_if_due(circuit, result)

    def test_simulator_stops_at_rejection_budget(self) -> None:
        integrator = BoundedAdamsBashforthIntegrator(
            BABCSConfig(
                rollout_mode="active",
                predictor_reference_cap=1.0e-12,
                energy_injection_cap=1.0e9,
                maximum_rejections=2,
                minimum_step=1.0e-20,
                anchor_interval_steps=100,
            )
        )
        with self.assertRaisesRegex(RuntimeError, "exhausted step retries"):
            Simulator(integrator).run(rc_charge_circuit(), 5.0e-4, 1.0e-4)


class _HighAlgebraicResidualCircuit(Circuit):
    def __init__(self, elements, *, after: float) -> None:
        super().__init__(elements)
        self.after = after

    def evaluate(self, time, dynamic_state, algebraic_guess=None, **settings):
        evaluation = super().evaluate(time, dynamic_state, algebraic_guess, **settings)
        if time > self.after:
            algebraic = replace(evaluation.algebraic, residual_norm=1.0)
            return replace(evaluation, algebraic=algebraic)
        return evaluation


class _HighFullResidualCircuit(Circuit):
    def __init__(self, elements, *, after: float) -> None:
        super().__init__(elements)
        self.after = after

    def full_residual_norm(self, evaluation, derivative=None):
        if evaluation.time > self.after:
            return 1.0
        return super().full_residual_norm(evaluation, derivative)


class _CorrectedProjectionFailureCircuit(Circuit):
    def __init__(self, elements) -> None:
        super().__init__(elements)
        self.jacobian_calls = 0

    def differential_jacobian(self, time, dynamic_state, algebraic_guess=None):
        del time, dynamic_state, algebraic_guess
        self.jacobian_calls += 1
        return [[-1_000.0]]

    def evaluate(self, time, dynamic_state, algebraic_guess=None, **settings):
        if self.jacobian_calls >= 2 and time > 1.5e-5:
            raise CircuitSolveError("synthetic corrected projection failure")
        return super().evaluate(time, dynamic_state, algebraic_guess, **settings)


class _ToggleFailureCircuit(Circuit):
    def __init__(self, elements) -> None:
        super().__init__(elements)
        self.fail = False

    def evaluate(self, time, dynamic_state, algebraic_guess=None, **settings):
        if self.fail:
            raise CircuitSolveError("synthetic replay failure")
        return super().evaluate(time, dynamic_state, algebraic_guess, **settings)


class _InjectedEnergyIntegrator(BoundedAdamsBashforthIntegrator):
    def _energy_metrics(self, current, candidate, step):
        del current, candidate, step
        return 1.0, self.config.energy_injection_cap + 1.0


def _permissive_integrator(**overrides) -> BoundedAdamsBashforthIntegrator:
    values = {
        "rollout_mode": "active",
        "predictor_reference_cap": 1.0e9,
        "anchor_reference_cap": 1.0e9,
        "energy_injection_cap": 1.0e9,
        "stiffness_limit": 1.0e9,
        "anchor_interval_steps": 10_000,
    }
    values.update(overrides)
    return BoundedAdamsBashforthIntegrator(BABCSConfig(**values))


if __name__ == "__main__":
    unittest.main()
