from __future__ import annotations

import math
import unittest
from unittest.mock import patch

from babcs import Capacitor, Circuit, Diode, Resistor, Sine, VoltageSource
from babcs.linalg import scipy_sparse_available
from babcs.integrators import implicit_step, integrate_reference_window_with_stats
from babcs.model import SparseImplicitUpdate
from babcs.waveforms import Constant


def rc_circuit() -> Circuit:
    return Circuit(
        [
            VoltageSource("V1", "vin", "0", Constant(1.0)),
            Resistor("R1", "vin", "out", 1_000.0),
            Capacitor("C1", "out", "0", 1.0e-6),
        ]
    )


class ImplicitIntegratorTests(unittest.TestCase):
    def test_reference_replay_advances_when_maximum_step_is_below_one_second_scaled_roundoff(self) -> None:
        circuit = Circuit()
        initial_time = 2.8e-4
        target_time = initial_time + 1.0e-12
        initial = circuit.evaluate(initial_time, ())

        replay = integrate_reference_window_with_stats(
            circuit,
            initial,
            [target_time],
            1.0e-15,
            exact_target_projection=True,
        )

        self.assertGreater(replay.steps, 900)
        self.assertEqual(replay.evaluations[-1].time, target_time)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_failed_sparse_chord_retries_exact_coupled_update(self) -> None:
        elements = []
        for index in range(16):
            source = f"vin{index}"
            output = f"out{index}"
            elements.extend(
                [
                    VoltageSource(f"V{index}", source, "0", Constant(1.0)),
                    Resistor(f"R{index}", source, output, 1_000.0),
                    Diode(f"D{index}", output, "0"),
                    Capacitor(f"C{index}", output, "0", 1.0e-6),
                ]
            )
        circuit = Circuit(elements, linear_backend="auto")
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        calls: list[bool] = []
        exact_update = circuit.sparse_implicit_update

        def injected_update(
            evaluation,
            state_coefficient,
            derivative_coefficient,
            residual,
            *,
            allow_chord=True,
        ):
            calls.append(allow_chord)
            if allow_chord:
                return SparseImplicitUpdate(
                    algebraic_update=(1.0e6,) * circuit.algebraic_size,
                    dynamic_update=(1.0e6,) * circuit.dynamic_size,
                    requires_contraction=True,
                )
            return exact_update(
                evaluation,
                state_coefficient,
                derivative_coefficient,
                residual,
                allow_chord=False,
            )

        circuit.sparse_implicit_update = injected_update

        result = implicit_step(circuit, "trapezoidal", initial, 1.0e-6)

        self.assertIn(True, calls)
        self.assertIn(False, calls)
        self.assertLess(result.residual_norm, 1.0e-8)

    def test_backward_euler_matches_closed_form_step(self) -> None:
        circuit = rc_circuit()
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        result = implicit_step(circuit, "backward_euler", initial, 1.0e-4)
        self.assertAlmostEqual(result.evaluation.dynamic_state[0], 1.0 / 11.0, places=10)
        self.assertEqual(result.circuit_evaluations, 2)

    def test_trapezoidal_is_second_order_on_rc_decay(self) -> None:
        circuit = rc_circuit()

        def run(step: float) -> float:
            current = circuit.evaluate(0.0, circuit.initial_dynamic_state())
            while current.time < 1.0e-3 - 1.0e-16:
                current = implicit_step(circuit, "trapezoidal", current, step).evaluation
            return abs(current.dynamic_state[0] - (1.0 - math.exp(-1.0)))

        coarse = run(5.0e-5)
        fine = run(2.5e-5)
        self.assertGreater(coarse / fine, 3.8)

    def test_variable_step_bdf2_runs_with_history(self) -> None:
        circuit = rc_circuit()
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        first = implicit_step(circuit, "backward_euler", initial, 1.0e-5).evaluation
        second = implicit_step(
            circuit,
            "bdf2",
            first,
            1.5e-5,
            previous_state=initial.dynamic_state,
            previous_step=1.0e-5,
        )
        self.assertEqual(second.method, "bdf2")
        self.assertGreater(second.evaluation.dynamic_state[0], first.dynamic_state[0])

    def test_bdf2_reference_replay_preserves_multistep_history(self) -> None:
        circuit = rc_circuit()
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        step = 1.0e-4
        replay = integrate_reference_window_with_stats(
            circuit,
            initial,
            (step, 2.0 * step, 3.0 * step),
            step,
            method="bdf2",
        )

        current = initial
        previous_state = None
        previous_step = None
        expected = []
        for _ in range(3):
            result = implicit_step(
                circuit,
                "bdf2",
                current,
                step,
                previous_state=previous_state,
                previous_step=previous_step,
            )
            previous_state = current.dynamic_state
            previous_step = step
            current = result.evaluation
            expected.append(current.dynamic_state[0])

        backward_euler = integrate_reference_window_with_stats(
            circuit,
            initial,
            (step, 2.0 * step, 3.0 * step),
            step,
            method="backward_euler",
        )
        for replay_evaluation, expected_value in zip(replay.evaluations, expected, strict=True):
            self.assertAlmostEqual(replay_evaluation.dynamic_state[0], expected_value, places=9)
        self.assertGreater(
            abs(replay.evaluations[-1].dynamic_state[0] - backward_euler.evaluations[-1].dynamic_state[0]),
            1.0e-4,
        )

    def test_reference_replay_higher_order_predictor_reduces_rc_newton_work(self) -> None:
        circuit = rc_circuit()
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        step = 1.0e-6
        replay = integrate_reference_window_with_stats(
            circuit,
            initial,
            tuple(index * step for index in range(1, 101)),
            step,
        )

        self.assertLess(replay.reference_iterations, replay.steps // 10)
        self.assertLess(replay.circuit_evaluations, replay.steps + replay.steps // 10)

    def test_reference_replay_reports_ordered_trapezoidal_error_evidence(self) -> None:
        circuit = rc_circuit()
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        coarse = integrate_reference_window_with_stats(
            circuit,
            initial,
            (1.0e-4,),
            1.0e-5,
            error_absolute_tolerance=1.0e-9,
            error_relative_tolerance=1.0e-6,
        )
        fine = integrate_reference_window_with_stats(
            circuit,
            initial,
            (1.0e-4,),
            5.0e-6,
            error_absolute_tolerance=1.0e-9,
            error_relative_tolerance=1.0e-6,
        )

        self.assertGreater(coarse.maximum_embedded_error, 0.0)
        self.assertLess(
            fine.maximum_embedded_error,
            coarse.maximum_embedded_error / 3.0,
        )

    def test_reference_replay_reports_ordered_bdf2_error_evidence(self) -> None:
        circuit = rc_circuit()
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        coarse = integrate_reference_window_with_stats(
            circuit,
            initial,
            (1.0e-5,),
            1.0e-6,
            method="bdf2",
            error_absolute_tolerance=1.0e-9,
            error_relative_tolerance=1.0e-6,
        )
        fine = integrate_reference_window_with_stats(
            circuit,
            initial,
            (1.0e-5,),
            5.0e-7,
            method="bdf2",
            error_absolute_tolerance=1.0e-9,
            error_relative_tolerance=1.0e-6,
        )

        self.assertGreater(coarse.maximum_embedded_error, 0.0)
        self.assertLess(
            fine.maximum_embedded_error,
            coarse.maximum_embedded_error / 2.5,
        )

    def test_reference_replay_uses_ab3_after_two_matching_steps(self) -> None:
        circuit = rc_circuit()
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        step = 1.0e-5
        captured_guesses = []

        def capture_step(*args, **kwargs):
            captured_guesses.append(kwargs.get("initial_guess"))
            return implicit_step(*args, **kwargs)

        with patch("babcs.integrators.implicit_step", side_effect=capture_step):
            replay = integrate_reference_window_with_stats(
                circuit,
                initial,
                (step, 2.0 * step, 3.0 * step),
                step,
            )

        current = replay.evaluations[1]
        previous = replay.evaluations[0]
        expected = [
            state_value
            + step
            * (
                (23.0 / 12.0) * derivative
                - (16.0 / 12.0) * previous_derivative
                + (5.0 / 12.0) * older_derivative
            )
            for state_value, derivative, previous_derivative, older_derivative in zip(
                current.dynamic_state,
                current.derivative,
                previous.derivative,
                initial.derivative,
                strict=True,
            )
        ]
        self.assertEqual(captured_guesses[2], expected)

    def test_reference_replay_falls_back_to_variable_step_ab2(self) -> None:
        circuit = rc_circuit()
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        step = 1.0e-5
        captured_guesses = []

        def capture_step(*args, **kwargs):
            captured_guesses.append(kwargs.get("initial_guess"))
            return implicit_step(*args, **kwargs)

        with patch("babcs.integrators.implicit_step", side_effect=capture_step):
            replay = integrate_reference_window_with_stats(
                circuit,
                initial,
                (step, 2.0 * step, 3.5 * step),
                1.5 * step,
            )

        current = replay.evaluations[1]
        previous = replay.evaluations[0]
        next_step = 1.5 * step
        ratio = next_step / step
        expected = [
            state_value
            + next_step
            * (
                (1.0 + 0.5 * ratio) * derivative
                - 0.5 * ratio * previous_derivative
            )
            for state_value, derivative, previous_derivative in zip(
                current.dynamic_state,
                current.derivative,
                previous.derivative,
                strict=True,
            )
        ]
        self.assertEqual(captured_guesses[2], expected)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_reference_replay_uses_quartic_algebraic_guess_on_uniform_steps(self) -> None:
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
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        step = 1.0e-6
        captured_guesses = []

        def capture_step(*args, **kwargs):
            captured_guesses.append(kwargs.get("initial_algebraic_guess"))
            return implicit_step(*args, **kwargs)

        with patch("babcs.integrators.implicit_step", side_effect=capture_step):
            replay = integrate_reference_window_with_stats(
                circuit,
                initial,
                tuple(index * step for index in range(1, 6)),
                step,
            )

        self.assertEqual(captured_guesses[:4], [None] * 4)
        expected = [
            5.0 * current
            - 10.0 * previous
            + 10.0 * older
            - 5.0 * third_previous
            + fourth_previous
            for current, previous, older, third_previous, fourth_previous in zip(
                replay.evaluations[3].algebraic.unknowns,
                replay.evaluations[2].algebraic.unknowns,
                replay.evaluations[1].algebraic.unknowns,
                replay.evaluations[0].algebraic.unknowns,
                initial.algebraic.unknowns,
                strict=True,
            )
        ]
        self.assertEqual(captured_guesses[4], expected)

    def test_bad_algebraic_predictor_restarts_from_current_solution(self) -> None:
        circuit = rc_circuit()
        current = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        result = implicit_step(
            circuit,
            "trapezoidal",
            current,
            1.0e-5,
            initial_algebraic_guess=(math.nan,) * circuit.algebraic_size,
        )

        self.assertTrue(all(math.isfinite(value) for value in result.evaluation.dynamic_state))

    def test_linear_implicit_factorization_is_reused_by_step_shape(self) -> None:
        circuit = rc_circuit()
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        first = implicit_step(circuit, "trapezoidal", initial, 1.0e-5).evaluation
        second = implicit_step(circuit, "trapezoidal", first, 1.0e-5).evaluation
        implicit_step(circuit, "trapezoidal", second, 2.0e-5)

        self.assertEqual(len(circuit._linear_implicit_factorization_cache), 2)

    def test_matching_initial_evaluation_is_reused(self) -> None:
        circuit = rc_circuit()
        current = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        candidate_state = tuple(
            value + 1.0e-4 * derivative
            for value, derivative in zip(
                current.dynamic_state,
                current.derivative,
                strict=True,
            )
        )
        candidate = circuit.evaluate(
            1.0e-4,
            candidate_state,
            current.algebraic.unknowns,
        )

        with patch.object(circuit, "evaluate", wraps=circuit.evaluate) as evaluate:
            result = implicit_step(
                circuit,
                "trapezoidal",
                current,
                1.0e-4,
                initial_guess=candidate_state,
                initial_evaluation=candidate,
            )

        self.assertEqual(evaluate.call_count, result.circuit_evaluations)
        self.assertEqual(result.circuit_evaluations, 1)

        with self.assertRaisesRegex(ValueError, "initial evaluation"):
            implicit_step(
                circuit,
                "trapezoidal",
                current,
                1.0e-4,
                initial_guess=(candidate_state[0] + 1.0e-6,),
                initial_evaluation=candidate,
            )

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_large_nonlinear_implicit_step_uses_sparse_block_update(self) -> None:
        elements = []
        for index in range(8):
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
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        sparse_updates = 0
        original_sparse_update = circuit.sparse_implicit_update

        def count_sparse_update(*args, **kwargs):
            nonlocal sparse_updates
            sparse_updates += 1
            return original_sparse_update(*args, **kwargs)

        def reject_materialized_jacobian(*args, **kwargs):
            raise AssertionError("full differential Jacobian should not be materialized")

        circuit.sparse_implicit_update = count_sparse_update
        circuit.differential_jacobian_at_evaluation = reject_materialized_jacobian
        result = implicit_step(circuit, "trapezoidal", initial, 2.0e-6)

        self.assertGreater(sparse_updates, 0)
        self.assertGreater(result.iterations, 0)
        self.assertEqual(result.algebraic_iterations, 1)
        self.assertLess(result.residual_norm, 1.0e-9)


if __name__ == "__main__":
    unittest.main()
