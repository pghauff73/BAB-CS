from __future__ import annotations

import unittest

from babcs import Capacitor, Circuit, CurrentSource, Diode, Inductor, Resistor, Switch, VoltageSource
from babcs.model import CircuitSolveError
from babcs.waveforms import Constant


class CircuitModelTests(unittest.TestCase):
    def test_rc_algebraic_projection_satisfies_kcl(self) -> None:
        circuit = Circuit(
            [
                VoltageSource("V1", "vin", "0", Constant(1.0)),
                Resistor("R1", "vin", "out", 1_000.0),
                Capacitor("C1", "out", "0", 1.0e-6, 0.25),
            ]
        )
        evaluation = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        self.assertAlmostEqual(evaluation.algebraic.node_voltages["out"], 0.25)
        self.assertAlmostEqual(evaluation.derivative[0], 750.0)
        self.assertLess(circuit.full_residual_norm(evaluation), 1.0e-12)

    def test_lc_dynamic_coordinates_follow_passive_sign_convention(self) -> None:
        circuit = Circuit(
            [
                Capacitor("C1", "n", "0", 1.0e-6, 1.0),
                Inductor("L1", "n", "0", 1.0e-3, 0.0),
            ]
        )
        evaluation = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        self.assertAlmostEqual(evaluation.derivative[0], 0.0)
        self.assertAlmostEqual(evaluation.derivative[1], 1_000.0)
        self.assertAlmostEqual(evaluation.stored_energy, 0.5e-6)

    def test_diode_limiting_keeps_large_forward_bias_finite(self) -> None:
        circuit = Circuit(
            [
                VoltageSource("V1", "n", "0", Constant(5.0)),
                Diode("D1", "n", "0"),
            ]
        )
        evaluation = circuit.evaluate(0.0, ())
        self.assertGreater(evaluation.dissipated_power, 0.0)
        self.assertLess(evaluation.algebraic.residual_norm, 1.0e-8)

    def test_floating_current_source_fails_closed(self) -> None:
        circuit = Circuit([CurrentSource("I1", "n", "0", Constant(1.0))])
        with self.assertRaises(CircuitSolveError):
            circuit.evaluate(0.0, ())

    def test_controlled_switch_changes_conductance(self) -> None:
        circuit = Circuit(
            [
                VoltageSource("V1", "vin", "0", Constant(1.0)),
                Resistor("R1", "vin", "out", 1_000.0),
                Switch(
                    "S1",
                    "out",
                    "0",
                    control=Constant(0.0),
                    threshold=0.5,
                    on_resistance=1.0,
                    off_resistance=1.0e9,
                ),
            ]
        )
        off = circuit.evaluate(0.0, ())
        self.assertGreater(off.algebraic.node_voltages["out"], 0.999)

        switched = Circuit(
            [
                VoltageSource("V1", "vin", "0", Constant(1.0)),
                Resistor("R1", "vin", "out", 1_000.0),
                Switch(
                    "S1",
                    "out",
                    "0",
                    control=Constant(1.0),
                    threshold=0.5,
                    on_resistance=1.0,
                    off_resistance=1.0e9,
                ),
            ]
        )
        on = switched.evaluate(0.0, ())
        self.assertLess(on.algebraic.node_voltages["out"], 0.001)


if __name__ == "__main__":
    unittest.main()
