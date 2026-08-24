from __future__ import annotations

import math
import unittest

from babcs import (
    BABCSConfig,
    BoundedIntegrator,
    Capacitor,
    Circuit,
    Diode,
    Resistor,
    Simulator,
    Sine,
    VoltageSource,
)
from babcs.linalg import scipy_sparse_available
from babcs.candidates import candidate_step
from babcs.candidates import CANDIDATE_METHODS, candidate_amplification, normalize_candidate_method
from babcs.io import summary_data
from babcs.waveforms import Constant


def rc_circuit() -> Circuit:
    return Circuit(
        [
            VoltageSource("V1", "vin", "0", Constant(1.0)),
            Resistor("R1", "vin", "out", 1_000.0),
            Capacitor("C1", "out", "0", 1.0e-6),
        ]
    )


REFERENCE_BY_CANDIDATE = {
    "explicit_euler": "trapezoidal",
    "heun": "trapezoidal",
    "rk23": "trapezoidal",
    "ab2": "trapezoidal",
    "backward_euler": "trapezoidal",
    "trapezoidal": "bdf2",
    "bdf2": "trapezoidal",
}


class CandidateIntegratorTests(unittest.TestCase):
    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_explicit_candidates_reuse_native_base_sensitivity(self) -> None:
        elements = []
        for index in range(16):
            source = f"vin{index}"
            output = f"out{index}"
            elements.extend(
                [
                    VoltageSource(
                        f"V{index}",
                        source,
                        "0",
                        Sine(0.0, 1.0 + index * 0.01, 1_000.0),
                    ),
                    Resistor(f"R{index}", source, output, 1_000.0),
                    Diode(f"D{index}", output, "0"),
                    Capacitor(f"C{index}", output, "0", 1.0e-6),
                ]
            )
        circuit = Circuit(elements, linear_backend="auto")
        previous = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        current = circuit.evaluate(
            2.0e-6,
            tuple(
                value + 2.0e-6 * derivative
                for value, derivative in zip(
                    previous.dynamic_state,
                    previous.derivative,
                    strict=True,
                )
            ),
            previous.algebraic.unknowns,
        )

        expected_maximum_iterations = {
            "explicit_euler": 0,
            "heun": 1,
            "rk23": 2,
            "ab2": 0,
        }
        for method, maximum_iterations in expected_maximum_iterations.items():
            with self.subTest(method=method):
                result = candidate_step(
                    circuit,
                    method,
                    current,
                    2.0e-6,
                    previous_evaluation=previous,
                    previous_step=2.0e-6,
                )
                self.assertIsNotNone(result.base_jacobian_norm)
                self.assertLessEqual(result.algebraic_iterations, maximum_iterations)

    def test_all_supported_candidates_share_the_bounded_controller(self) -> None:
        self.assertEqual(set(REFERENCE_BY_CANDIDATE), CANDIDATE_METHODS)
        expected = 1.0 - math.exp(-0.5)
        for method, reference_method in REFERENCE_BY_CANDIDATE.items():
            with self.subTest(method=method):
                result = Simulator(
                    BoundedIntegrator(
                        BABCSConfig(
                            rollout_mode="active",
                            candidate_method=method,
                            reference_method=reference_method,
                            predictor_reference_cap=1.0e6,
                            embedded_error_cap=1.0e6,
                            energy_injection_cap=1.0e6,
                            stiffness_limit=10.0,
                            anchor_interval_steps=1_000,
                        )
                    )
                ).run(rc_circuit(), 5.0e-4, 1.0e-5)

                metrics = [point.metrics for point in result.points if point.metrics]
                candidate_metrics = [metric for metric in metrics if metric.candidate_used]
                self.assertTrue(candidate_metrics)
                self.assertTrue(all(metric.candidate_method == method for metric in candidate_metrics))
                self.assertTrue(all(metric.closed_loop_gain < 1.0 for metric in candidate_metrics))
                self.assertTrue(all(metric.certified_contractive for metric in candidate_metrics))
                final_value = result.points[-1].state.evaluation.dynamic_state[0]
                self.assertAlmostEqual(final_value, expected, delta=1.5e-3)

                if method in {"backward_euler", "trapezoidal", "bdf2"}:
                    self.assertGreater(
                        sum(metric.candidate_circuit_evaluations for metric in candidate_metrics),
                        0,
                    )
                    self.assertGreater(
                        sum(metric.candidate_solve_count for metric in candidate_metrics),
                        0,
                    )
                else:
                    self.assertGreater(
                        sum(metric.explicit_projection_count for metric in candidate_metrics),
                        0,
                    )

    def test_embedded_candidates_report_scaled_local_error(self) -> None:
        for method in ("heun", "rk23"):
            with self.subTest(method=method):
                result = Simulator(
                    BoundedIntegrator(
                        BABCSConfig(
                            rollout_mode="active",
                            candidate_method=method,
                            predictor_reference_cap=1.0e9,
                            embedded_error_cap=1.0e9,
                            energy_injection_cap=1.0e9,
                            anchor_interval_steps=1_000,
                        )
                    )
                ).run(rc_circuit(), 5.0e-5, 1.0e-5)
                metrics = [
                    point.metrics
                    for point in result.points
                    if point.metrics is not None and point.metrics.candidate_used
                ]
                self.assertTrue(any(metric.embedded_error > 0.0 for metric in metrics))
                self.assertTrue(
                    all(
                        metric.local_defect
                        == metric.corrected_reference_error + metric.residual_ratio
                        for metric in metrics
                    )
                )

    def test_shadow_rk23_transfers_full_reference_authority(self) -> None:
        integrator = BoundedIntegrator(
            BABCSConfig(
                rollout_mode="shadow",
                candidate_method="rk23",
                predictor_reference_cap=1.0e9,
                embedded_error_cap=1.0e9,
                energy_injection_cap=1.0e9,
                anchor_interval_steps=1_000,
            )
        )
        state, history = integrator.initialize(rc_circuit())
        result = integrator.step(rc_circuit(), state, history, 1.0e-5)
        self.assertEqual(result.metrics.method, "shadow_reference_authority")
        self.assertEqual(result.metrics.correction_gain, 1.0)
        self.assertEqual(result.metrics.corrected_reference_error, 0.0)
        self.assertEqual(result.metrics.embedded_defect, 0.0)

    def test_rate_based_contraction_reduces_high_order_blending(self) -> None:
        circuit = rc_circuit()
        fixed = BoundedIntegrator(
            BABCSConfig(
                rollout_mode="active",
                candidate_method="rk23",
                predictor_reference_cap=1.0e9,
                embedded_error_cap=1.0e9,
                energy_injection_cap=1.0e9,
                anchor_interval_steps=1_000,
            )
        )
        rate_based = BoundedIntegrator(
            BABCSConfig(
                rollout_mode="active",
                candidate_method="rk23",
                contraction_rate=10.0,
                minimum_correction_gain=0.0,
                predictor_reference_cap=1.0e9,
                embedded_error_cap=1.0e9,
                energy_injection_cap=1.0e9,
                anchor_interval_steps=1_000,
            )
        )
        fixed_state, fixed_history = fixed.initialize(circuit)
        rate_state, rate_history = rate_based.initialize(circuit)
        fixed_result = fixed.step(circuit, fixed_state, fixed_history, 1.0e-5)
        rate_result = rate_based.step(circuit, rate_state, rate_history, 1.0e-5)
        self.assertLess(rate_result.metrics.correction_gain, fixed_result.metrics.correction_gain)
        self.assertLess(rate_result.metrics.closed_loop_gain, 1.0)

    def test_embedded_fast_path_defers_reference_work_until_checkpoints(self) -> None:
        common = {
            "rollout_mode": "active",
            "candidate_method": "rk23",
            "predictor_reference_cap": 1.0e9,
            "embedded_error_cap": 1.0e9,
            "energy_injection_cap": 1.0e9,
            "anchor_interval_steps": 8,
            "anchor_substeps": 2,
        }
        every_step = Simulator(BoundedIntegrator(BABCSConfig(**common))).run(
            rc_circuit(),
            2.0e-4,
            1.0e-5,
        )
        deferred = Simulator(
            BoundedIntegrator(BABCSConfig(reference_interval_steps=4, **common))
        ).run(rc_circuit(), 2.0e-4, 1.0e-5)
        every_step_summary = summary_data(every_step)
        deferred_summary = summary_data(deferred)
        deferred_metrics = [point.metrics for point in deferred.points if point.metrics]

        self.assertTrue(
            any(metric.method == "babcs_rk23_embedded_fast" for metric in deferred_metrics)
        )
        self.assertTrue(
            any(
                metric.reference_solve_count == 0
                and metric.local_defect == metric.embedded_error + metric.residual_ratio
                for metric in deferred_metrics
            )
        )
        self.assertLess(
            deferred_summary["reference_circuit_evaluations"],
            every_step_summary["reference_circuit_evaluations"],
        )
        self.assertLessEqual(
            deferred_summary["maximum_estimated_bound"],
            100.0,
        )
        self.assertGreater(deferred.final_history.periodic_reanchors, 0)
        self.assertAlmostEqual(
            deferred.points[-1].state.evaluation.dynamic_state[0],
            1.0 - math.exp(-0.2),
            delta=5.0e-4,
        )

    def test_dynamic_bound_checkpoint_promotes_reference_authority(self) -> None:
        result = Simulator(
            BoundedIntegrator(
                BABCSConfig(
                    rollout_mode="active",
                    candidate_method="rk23",
                    reference_interval_steps=100,
                    deferred_reference_bound_cap=1.0,
                    predictor_reference_cap=1.0e9,
                    embedded_error_cap=1.0e9,
                    energy_injection_cap=1.0e9,
                    anchor_interval_steps=1_000,
                )
            )
        ).run(rc_circuit(), 3.0e-4, 1.0e-4)
        checkpoints = [
            point.metrics
            for point in result.points
            if point.metrics is not None and point.metrics.dynamic_reference_checkpoint
        ]
        self.assertTrue(checkpoints)
        self.assertTrue(all(metric.method == "implicit_bound_fallback" for metric in checkpoints))
        self.assertTrue(all(metric.correction_gain == 1.0 for metric in checkpoints))

    def test_candidate_aliases_and_amplification_models(self) -> None:
        self.assertEqual(normalize_candidate_method("Bogacki-Shampine"), "rk23")
        self.assertEqual(normalize_candidate_method("forward-euler"), "explicit_euler")
        self.assertAlmostEqual(candidate_amplification("heun", 0.1, 2.0), 1.22)
        self.assertIsNone(candidate_amplification("backward_euler", 1.0, 1.0))
        self.assertGreater(
            candidate_amplification("bdf2", 0.1, 1.0, previous_step=0.1),
            1.0,
        )

    def test_implicit_candidate_requires_an_independent_reference(self) -> None:
        with self.assertRaisesRegex(ValueError, "must differ from reference_method"):
            BABCSConfig(
                rollout_mode="active",
                candidate_method="trapezoidal",
                reference_method="trapezoidal",
            )
        BABCSConfig(
            rollout_mode="disabled",
            candidate_method="trapezoidal",
            reference_method="trapezoidal",
        )
        with self.assertRaisesRegex(ValueError, "requires an embedded"):
            BABCSConfig(
                rollout_mode="active",
                candidate_method="backward_euler",
                reference_interval_steps=2,
            )


if __name__ == "__main__":
    unittest.main()
