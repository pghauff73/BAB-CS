from __future__ import annotations

import math
import unittest

from babcs import (
    BABCSConfig,
    BoundedAdamsBashforthIntegrator,
    Capacitor,
    Circuit,
    Diode,
    Inductor,
    Pulse,
    Resistor,
    Sine,
    Simulator,
    Switch,
    VoltageSource,
)
from babcs.io import summary_data
from tests.support.circuits import rc_charge_circuit
from tests.support.circuits import pulsed_rc_circuit


def switched_capacitive_circuit() -> Circuit:
    return Circuit(
        [
            VoltageSource(
                "V1",
                "vin",
                "0",
                Pulse(0.0, 1.0, 2.0e-5, 1.0e-6, 2.0e-5, 1.0e-6, 5.0e-5),
            ),
            Resistor("R1", "vin", "out", 1_000.0),
            Diode("D1", "out", "0"),
            Capacitor("C1", "out", "0", 1.0e-6),
            Switch(
                "S1",
                "out",
                "0",
                Pulse(0.0, 1.0, 2.5e-5, 0.0, 1.0e-5, 0.0, 5.0e-5),
                threshold=0.5,
                on_resistance=10.0,
                off_resistance=1.0e9,
            ),
        ],
        linear_backend="auto",
    )


class BoundModelTests(unittest.TestCase):
    def test_emitted_metrics_reproduce_recursive_bound(self) -> None:
        config = BABCSConfig(
            rollout_mode="active",
            predictor_reference_cap=100.0,
            anchor_reference_cap=100.0,
            anchor_interval_steps=10_000,
        )
        result = Simulator(BoundedAdamsBashforthIntegrator(config)).run(
            rc_charge_circuit(),
            2.0e-4,
            1.0e-5,
        )
        previous_bound = 0.0
        for point in result.points[1:]:
            metrics = point.metrics
            assert metrics is not None
            expected_defect = metrics.corrected_reference_error + metrics.residual_ratio
            self.assertAlmostEqual(metrics.local_defect, expected_defect, places=14)
            if metrics.ab_used:
                expected_bound = metrics.closed_loop_gain * previous_bound + metrics.local_defect
                self.assertAlmostEqual(metrics.estimated_bound, expected_bound, places=12)
            else:
                self.assertEqual(metrics.estimated_bound, 0.0)
            previous_bound = metrics.estimated_bound

    def test_certification_requires_finite_strict_contraction(self) -> None:
        result = Simulator(
            BoundedAdamsBashforthIntegrator(
                BABCSConfig(
                    rollout_mode="active",
                    predictor_reference_cap=100.0,
                    anchor_interval_steps=10_000,
                )
            )
        ).run(rc_charge_circuit(), 1.0e-4, 1.0e-5)
        for point in result.points[1:]:
            metrics = point.metrics
            assert metrics is not None
            if metrics.certified_contractive:
                self.assertTrue(math.isfinite(metrics.closed_loop_gain))
                self.assertLess(metrics.closed_loop_gain, 1.0)

    def test_anchor_records_pre_reset_bound_and_replay_work(self) -> None:
        result = Simulator(
            BoundedAdamsBashforthIntegrator(
                BABCSConfig(
                    rollout_mode="active",
                    predictor_reference_cap=100.0,
                    anchor_reference_cap=100.0,
                    anchor_interval_steps=4,
                    anchor_substeps=3,
                )
            )
        ).run(rc_charge_circuit(), 1.2e-4, 1.0e-5)
        anchors = [point for point in result.points if point.metrics and point.metrics.periodic_reanchor]
        self.assertTrue(anchors)
        for point in anchors:
            metrics = point.metrics
            assert metrics is not None
            self.assertEqual(metrics.estimated_bound, 0.0)
            self.assertGreaterEqual(metrics.pre_reset_estimated_bound, 0.0)
            self.assertGreater(metrics.replay_steps, 0)
            self.assertGreater(metrics.replay_circuit_evaluations, 0)
            self.assertIn(point.history_reset_reason, {"periodic_reanchor", "safety_reanchor"})
        summary = summary_data(result)
        self.assertIn("replay_refinement_retries", summary)
        self.assertIn("maximum_replay_embedded_error", summary)

    def test_summary_operation_counts_match_simple_static_case(self) -> None:
        from babcs import Circuit, Resistor, VoltageSource
        from babcs.waveforms import Constant

        circuit = Circuit(
            [
                VoltageSource("V1", "n", "0", Constant(1.0)),
                Resistor("R1", "n", "0", 1_000.0),
            ]
        )
        result = Simulator(
            BoundedAdamsBashforthIntegrator(
                BABCSConfig(rollout_mode="disabled", anchor_interval_steps=100)
            )
        ).run(circuit, 1.0e-5, 1.0e-5)
        summary = summary_data(result)
        self.assertEqual(summary["reference_solves"], 1)
        self.assertEqual(summary["reference_circuit_evaluations"], 1)
        self.assertEqual(summary["explicit_projections"], 0)
        self.assertEqual(summary["differential_jacobian_evaluations"], 0)
        self.assertEqual(summary["minimum_accepted_step"], 1.0e-5)
        self.assertEqual(summary["maximum_accepted_step"], 1.0e-5)

    def test_event_reset_is_visible_and_next_bound_restarts_at_zero(self) -> None:
        result = Simulator(
            BoundedAdamsBashforthIntegrator(
                BABCSConfig(
                    rollout_mode="active",
                    predictor_reference_cap=100.0,
                    anchor_interval_steps=10_000,
                )
            )
        ).run(pulsed_rc_circuit(period=0.0), 7.0e-4, 7.0e-5)
        event_index = next(index for index, point in enumerate(result.points) if point.event_boundary)
        self.assertEqual(result.points[event_index].history_reset_reason, "event")
        next_metrics = result.points[event_index + 1].metrics
        assert next_metrics is not None
        self.assertFalse(next_metrics.ab_used)
        self.assertEqual(next_metrics.estimated_bound, 0.0)

    def test_full_reference_authority_has_zero_local_gain(self) -> None:
        result = Simulator(
            BoundedAdamsBashforthIntegrator(
                BABCSConfig(rollout_mode="disabled", anchor_interval_steps=10_000)
            )
        ).run(rc_charge_circuit(), 5.0e-5, 1.0e-5)
        self.assertTrue(
            all(
                point.metrics is None or point.metrics.closed_loop_gain == 0.0
                for point in result.points
            )
        )

    def test_anchor_refinement_is_adapted_to_replay_error_evidence(self) -> None:
        def mixed_circuit() -> Circuit:
            return Circuit(
                [
                    VoltageSource("V1", "vin", "0", Sine(0.0, 1.0, 1_000.0)),
                    Resistor("R1", "vin", "out", 1_000.0),
                    Diode("D1", "out", "0"),
                    Capacitor("C1", "out", "0", 1.0e-6),
                    Inductor("L1", "out", "0", 1.0e-3),
                ],
                linear_backend="auto",
            )

        cases = (
            (5.0, 2, 0, True),
            (1.25, 3, 1, True),
            (1.0e-12, 4, 1, False),
        )
        for error_cap, expected_substeps, expected_retries, cap_satisfied in cases:
            with self.subTest(error_cap=error_cap):
                result = Simulator(
                    BoundedAdamsBashforthIntegrator(
                        BABCSConfig(
                            rollout_mode="active",
                            predictor_reference_cap=1.0e9,
                            embedded_error_cap=1.0e9,
                            anchor_reference_cap=100.0,
                            energy_injection_cap=1.0e9,
                            stiffness_limit=1.0e9,
                            anchor_embedded_error_cap=error_cap,
                            anchor_interval_steps=16,
                            anchor_substeps=4,
                            minimum_anchor_substeps=2,
                        )
                    )
                ).run(mixed_circuit(), 3.2e-5, 2.0e-6)
                anchor_metrics = [
                    point.metrics
                    for point in result.points
                    if point.metrics and point.metrics.periodic_reanchor
                ]
                self.assertEqual(len(anchor_metrics), 1)
                metrics = anchor_metrics[0]
                self.assertEqual(
                    metrics.replay_refinement_substeps,
                    expected_substeps,
                )
                self.assertEqual(
                    metrics.replay_refinement_retries,
                    expected_retries,
                )
                if cap_satisfied:
                    self.assertLessEqual(
                        metrics.replay_embedded_error,
                        error_cap,
                    )
                else:
                    self.assertEqual(
                        metrics.replay_refinement_substeps,
                        4,
                    )
                    self.assertGreater(
                        metrics.replay_embedded_error,
                        error_cap,
                    )

    def test_anchor_refinement_adaptation_can_be_disabled(self) -> None:
        result = Simulator(
            BoundedAdamsBashforthIntegrator(
                BABCSConfig(
                    rollout_mode="active",
                    predictor_reference_cap=100.0,
                    anchor_reference_cap=100.0,
                    anchor_interval_steps=2,
                    anchor_substeps=4,
                    minimum_anchor_substeps=2,
                    adaptive_anchor_refinement=False,
                )
            )
        ).run(rc_charge_circuit(), 4.0e-5, 1.0e-5)
        anchor_metrics = [
            point.metrics
            for point in result.points
            if point.metrics and point.metrics.periodic_reanchor
        ]
        self.assertTrue(anchor_metrics)
        self.assertTrue(
            all(metrics.replay_refinement_substeps == 4 for metrics in anchor_metrics)
        )
        self.assertTrue(
            all(metrics.replay_refinement_retries == 0 for metrics in anchor_metrics)
        )
        self.assertTrue(
            all(metrics.replay_embedded_error == 0.0 for metrics in anchor_metrics)
        )

    def test_bdf2_anchor_refinement_is_gated_to_piecewise_switched_capacitive_circuits(self) -> None:
        integrator = BoundedAdamsBashforthIntegrator(
            BABCSConfig(
                rollout_mode="active",
                reference_method="bdf2",
                anchor_substeps=4,
                minimum_anchor_substeps=2,
            )
        )
        pulse = pulsed_rc_circuit()
        switched = switched_capacitive_circuit()
        mixed = Circuit([*switched.elements, Inductor("L1", "out", "0", 1.0e-3)])

        self.assertEqual(integrator._anchor_refinement_substeps(pulse), 4)
        self.assertEqual(integrator._anchor_refinement_substeps(switched), 2)
        self.assertEqual(integrator._anchor_refinement_substeps(mixed), 4)

    def test_bdf2_switched_replay_reduces_work_with_fixed_eight_authority_bound(self) -> None:
        def run(adaptive: bool, anchor_substeps: int):
            return Simulator(
                BoundedAdamsBashforthIntegrator(
                    BABCSConfig(
                        rollout_mode="active",
                        reference_method="bdf2",
                        reference_interval_steps=8,
                        predictor_reference_cap=1.0e9,
                        embedded_error_cap=1.0e9,
                        energy_injection_cap=1.0e9,
                        stiffness_limit=1.0e9,
                        anchor_interval_steps=16,
                        anchor_substeps=anchor_substeps,
                        minimum_anchor_substeps=2,
                        adaptive_anchor_refinement=adaptive,
                    )
                )
            ).run(switched_capacitive_circuit(), 1.6e-4, 2.0e-6)

        adaptive = run(True, 4)
        fixed_four = run(False, 4)
        fixed_eight = run(False, 8)
        adaptive_metrics = [point.metrics for point in adaptive.points if point.metrics]
        fixed_four_metrics = [point.metrics for point in fixed_four.points if point.metrics]

        self.assertEqual(sum(metric.replay_steps for metric in adaptive_metrics), 263)
        self.assertEqual(sum(metric.replay_steps for metric in fixed_four_metrics), 390)
        self.assertEqual(
            sum(metric.replay_refinement_retries for metric in adaptive_metrics),
            1,
        )
        self.assertEqual(
            tuple(point.time for point in adaptive.points),
            tuple(point.time for point in fixed_eight.points),
        )
        maximum_state_delta = max(
            abs(adaptive_value - authority_value)
            for adaptive_point, authority_point in zip(
                adaptive.points,
                fixed_eight.points,
                strict=True,
            )
            for adaptive_value, authority_value in zip(
                adaptive_point.state.evaluation.dynamic_state,
                authority_point.state.evaluation.dynamic_state,
                strict=True,
            )
        )
        self.assertLess(maximum_state_delta, 5.0e-9)


if __name__ == "__main__":
    unittest.main()
