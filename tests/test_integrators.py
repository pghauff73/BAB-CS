from __future__ import annotations

import math
import unittest

from babcs import Capacitor, Circuit, Resistor, VoltageSource
from babcs.integrators import implicit_step
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
    def test_backward_euler_matches_closed_form_step(self) -> None:
        circuit = rc_circuit()
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        result = implicit_step(circuit, "backward_euler", initial, 1.0e-4)
        self.assertAlmostEqual(result.evaluation.dynamic_state[0], 1.0 / 11.0, places=10)

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


if __name__ == "__main__":
    unittest.main()

