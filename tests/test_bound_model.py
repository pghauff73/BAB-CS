from __future__ import annotations

import math
import unittest

from babcs import BABCSConfig, BoundedAdamsBashforthIntegrator, Simulator
from babcs.io import summary_data
from tests.support.circuits import rc_charge_circuit
from tests.support.circuits import pulsed_rc_circuit


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


if __name__ == "__main__":
    unittest.main()
