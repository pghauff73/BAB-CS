from __future__ import annotations

import unittest

from babcs import BABCSConfig, BoundedAdamsBashforthIntegrator, Simulator
from babcs.bounded import StepRejected
from babcs.integrators import ImplicitSettings
from tests.support.circuits import diode_clip_circuit, diode_recovery_circuit, switched_rc_circuit
from tests.support.metrics import interpolate_trace


class NonlinearQualificationTests(unittest.TestCase):
    def test_diode_clip_matches_refined_implicit_replay(self) -> None:
        refined = self._run(diode_clip_circuit(), 1.0e-3, 1.25e-7, mode="disabled")
        refined_trace = refined.dynamic_trace(0)
        maximum_errors = []
        for step in (2.0e-6, 1.0e-6):
            active = self._run(diode_clip_circuit(), 1.0e-3, step, mode="active")
            maximum_errors.append(
                max(
                    abs(
                        point.state.evaluation.dynamic_state[0]
                        - interpolate_trace(refined_trace, point.time)
                    )
                    for point in active.points
                )
            )
        self.assertGreater(maximum_errors[0], maximum_errors[1])
        self.assertLess(maximum_errors[1], 3.0e-4)
        self.assertTrue(
            all(
                point.metrics is None or point.metrics.algebraic_residual <= 1.0e-8
                for point in active.points
            )
        )
        self.assertGreater(
            sum(
                point.metrics.reference_iterations
                for point in active.points
                if point.metrics is not None
            ),
            0,
        )

    def test_diode_recovery_remains_finite_through_all_events(self) -> None:
        refined = self._run(diode_recovery_circuit(), 6.0e-4, 1.25e-7, mode="disabled")
        refined_trace = refined.dynamic_trace(0)
        result = self._run(diode_recovery_circuit(), 6.0e-4, 2.0e-6, mode="active")
        self.assertGreaterEqual(sum(point.event_boundary for point in result.points), 4)
        self.assertTrue(
            all(
                abs(value) < 10.0
                for point in result.points
                for value in point.state.evaluation.dynamic_state
            )
        )
        maximum_error = max(
            abs(
                point.state.evaluation.dynamic_state[0]
                - interpolate_trace(refined_trace, point.time)
            )
            for point in result.points
        )
        self.assertLess(maximum_error, 6.0e-3)
        self.assertLess(
            max(point.metrics.algebraic_residual for point in result.points if point.metrics),
            1.0e-8,
        )
        self.assertGreater(
            sum(point.metrics.reference_iterations for point in result.points if point.metrics),
            0,
        )

    def test_diode_nonconvergence_fails_closed_with_constrained_iterations(self) -> None:
        circuit = diode_clip_circuit()
        integrator = BoundedAdamsBashforthIntegrator(
            BABCSConfig(
                rollout_mode="active",
                implicit_settings=ImplicitSettings(max_iterations=0),
            )
        )
        state, history = integrator.initialize(circuit)
        with self.assertRaisesRegex(StepRejected, "implicit startup failed"):
            integrator.step(circuit, state, history, 2.0e-6)

    def test_switched_rc_matches_refined_implicit_replay(self) -> None:
        refined = self._run(switched_rc_circuit(), 9.0e-4, 6.25e-7, mode="disabled")
        refined_trace = refined.dynamic_trace(0)
        final_errors = []
        maximum_errors = []
        for step in (1.0e-5, 5.0e-6):
            active = self._run(switched_rc_circuit(), 9.0e-4, step, mode="active")
            errors = [
                abs(point.state.evaluation.dynamic_state[0] - interpolate_trace(refined_trace, point.time))
                for point in active.points
            ]
            final_errors.append(errors[-1])
            maximum_errors.append(max(errors))
            self.assertGreater(sum(point.event_boundary for point in active.points), 0)
        self.assertGreater(final_errors[0], final_errors[1])
        self.assertLess(maximum_errors[1], 1.5e-2)

    @staticmethod
    def _run(circuit, stop_time: float, step: float, *, mode: str):
        config = BABCSConfig(
            rollout_mode=mode,
            predictor_reference_cap=1.0e9,
            anchor_reference_cap=1.0e9,
            energy_injection_cap=1.0e9,
            stiffness_limit=1.0e9,
            anchor_interval_steps=50,
        )
        return Simulator(BoundedAdamsBashforthIntegrator(config)).run(circuit, stop_time, step)


if __name__ == "__main__":
    unittest.main()
