from __future__ import annotations

import math
import unittest
from unittest.mock import patch

from babcs import Capacitor, Circuit, CurrentSource, Diode, Inductor, Resistor, Switch, VoltageSource
from babcs.linalg import (
    LinearBackendUnavailableError,
    SingularMatrixError,
    SparseMatrix,
    factor_linear,
    klu_sparse_available,
    matrix_inf_norm,
    scipy_sparse_available,
    solve_factored,
    solve_linear,
)
from babcs.model import (
    MAXIMUM_COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES,
    CircuitSolveError,
    _clear_compiled_sparse_algebraic_topologies,
    _compile_sparse_algebraic_jacobian_kernel,
    _compile_sparse_algebraic_kernel,
    _lookup_compiled_sparse_algebraic_topology,
    _store_compiled_sparse_algebraic_topology,
    _within_ulp_time_window,
)
from babcs.waveforms import Constant, Pulse, Sine


def _diode_channel_elements(count: int):
    elements = []
    for index in range(count):
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
    return elements


class CircuitModelTests(unittest.TestCase):
    def test_algebraic_solution_maps_follow_compiled_unknown_order(self) -> None:
        circuit = Circuit(
            [
                VoltageSource("Vb", "b", "0", Constant(0.0)),
                VoltageSource("Va", "a", "0", Constant(0.0)),
                Capacitor("Cb", "b", "0", 1.0e-6),
                Capacitor("Ca", "a", "0", 1.0e-6),
            ]
        )
        unknowns = tuple(index + 0.25 for index in range(circuit.algebraic_size))

        solution = circuit._make_algebraic_solution(unknowns, 3.25, 1.0e-12, 2)

        self.assertEqual(tuple(solution.node_voltages), ("0", *circuit.nodes))
        self.assertEqual(tuple(solution.branch_currents), tuple(circuit.branch_index))
        self.assertEqual(
            solution.node_voltages,
            {"0": 0.0, **{node: unknowns[index] for node, index in circuit.node_index.items()}},
        )
        self.assertEqual(
            solution.branch_currents,
            {name: unknowns[index] for name, index in circuit.branch_index.items()},
        )

    def test_evaluation_carries_validated_dynamic_state_norm(self) -> None:
        circuit = Circuit(
            [
                VoltageSource("V1", "vin1", "0", Constant(0.0)),
                Resistor("R1", "vin1", "n1", 1_000.0),
                Capacitor("C1", "n1", "0", 1.0e-6, -2.0),
                VoltageSource("V2", "vin2", "0", Constant(0.0)),
                Resistor("R2", "vin2", "n2", 1_000.0),
                Capacitor("C2", "n2", "0", 1.0e-6, 3.0),
            ]
        )

        evaluation = circuit.evaluate(0.0, circuit.initial_dynamic_state())

        self.assertEqual(evaluation.dynamic_state_norm, 3.0)

    def test_simulation_breakpoint_compilation_preserves_live_waveforms(self) -> None:
        class CustomWaveform:
            def value(self, time: float) -> float:
                del time
                return 0.0

            def breakpoints(self, start: float, end: float) -> list[float]:
                del start, end
                return []

        shared_schedule_a = Pulse(0.0, 1.0, 1.0e-4, 1.0e-6, 2.0e-5, 1.0e-6, 5.0e-5)
        shared_schedule_b = Pulse(0.0, 2.0, 1.0e-4, 1.0e-6, 2.0e-5, 1.0e-6, 5.0e-5)
        first_custom = CustomWaveform()
        second_custom = CustomWaveform()
        circuit = Circuit(
            [
                VoltageSource("V1", "n1", "0", shared_schedule_a),
                VoltageSource("V2", "n2", "0", shared_schedule_b),
                CurrentSource("I1", "n1", "0", first_custom),
                CurrentSource("I2", "n2", "0", second_custom),
            ]
        )

        compiled = circuit._simulation_breakpoint_waveforms()

        self.assertEqual(compiled, (shared_schedule_a, first_custom, second_custom))

        replacement = Pulse(0.0, 3.0, 2.0e-4, 1.0e-6, 2.0e-5, 1.0e-6, 5.0e-5)
        circuit.voltage_sources[1].waveform = replacement
        self.assertEqual(
            circuit._simulation_breakpoint_waveforms(),
            (shared_schedule_a, replacement, first_custom, second_custom),
        )

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_evaluation_samples_each_waveform_once_across_newton_and_accounting(self) -> None:
        class CountingWaveform:
            def __init__(self, value: float) -> None:
                self.output = value
                self.calls = 0

            def value(self, time: float) -> float:
                self.calls += 1
                return self.output

            def breakpoints(self, start: float, end: float) -> list[float]:
                return []

        voltages = [CountingWaveform(1.0 + 0.01 * index) for index in range(16)]
        current = CountingWaveform(1.0e-6)
        control = CountingWaveform(0.0)
        elements = []
        for index, voltage in enumerate(voltages):
            source = f"vin{index}"
            output = f"out{index}"
            elements.extend(
                [
                    VoltageSource(f"V{index}", source, "0", voltage),
                    Resistor(f"R{index}", source, output, 1_000.0),
                    Diode(f"D{index}", output, "0"),
                    Capacitor(f"C{index}", output, "0", 1.0e-6),
                ]
            )
        elements.extend(
            [
                CurrentSource("Iextra", "out0", "0", current),
                Switch("Sextra", "out0", "0", control),
            ]
        )
        circuit = Circuit(elements, linear_backend="auto")

        evaluation = circuit.evaluate(
            2.5e-5,
            circuit.initial_dynamic_state(),
            [0.0] * circuit.algebraic_size,
        )

        self.assertGreater(evaluation.algebraic.iterations, 0)
        self.assertTrue(all(voltage.calls == 1 for voltage in voltages))
        self.assertEqual((current.calls, control.calls), (1, 1))

        replacement = CountingWaveform(2.0)
        circuit.voltage_sources[0].waveform = replacement
        updated = circuit.evaluate(
            2.5e-5,
            circuit.initial_dynamic_state(),
            evaluation.algebraic.unknowns,
        )
        self.assertEqual(replacement.calls, 1)
        self.assertEqual(updated.algebraic.node_voltages["vin0"], 2.0)

    def test_repeated_builtin_switch_controls_share_live_value_sampling(self) -> None:
        controls = [Pulse(0.0, 1.0, 1.0e-5, 0.0, 1.0e-5, 0.0, 2.0e-5) for _ in range(32)]
        circuit = Circuit(
            Switch(
                f"S{index}",
                "n",
                "0",
                control,
                threshold=0.5,
                on_resistance=10.0 + index,
                off_resistance=1.0e9,
            )
            for index, control in enumerate(controls)
        )
        calls = 0
        original_value = Pulse.value

        def counting_value(waveform: Pulse, time: float) -> float:
            nonlocal calls
            calls += 1
            return original_value(waveform, time)

        with patch.object(Pulse, "value", counting_value):
            self.assertEqual(
                circuit._sample_algebraic_inputs(1.5e-5, ()).switch_resistances,
                tuple(10.0 + index for index in range(32)),
            )
            self.assertEqual(calls, 1)

            circuit.switches[0].control = Pulse(
                0.0,
                0.0,
                1.0e-5,
                0.0,
                1.0e-5,
                0.0,
                2.0e-5,
            )
            self.assertEqual(
                circuit._sample_algebraic_inputs(1.5e-5, ()).switch_resistances,
                (1.0e9, *(10.0 + index for index in range(1, 32))),
            )
            self.assertEqual(calls, 3)

    def test_unique_and_custom_switch_controls_preserve_direct_sampling(self) -> None:
        unique_controls = [
            Pulse(0.0, 1.0 + 0.1 * index, 1.0e-5, 0.0, 1.0e-5, 0.0, 2.0e-5)
            for index in range(32)
        ]
        unique_circuit = Circuit(
            Switch(f"S{index}", "n", "0", control)
            for index, control in enumerate(unique_controls)
        )
        pulse_calls = 0
        original_value = Pulse.value

        def counting_value(waveform: Pulse, time: float) -> float:
            nonlocal pulse_calls
            pulse_calls += 1
            return original_value(waveform, time)

        with patch.object(Pulse, "value", counting_value):
            unique_circuit._sample_algebraic_inputs(1.5e-5, ())
        self.assertEqual(pulse_calls, 32)

        class CountingControl:
            def __init__(self) -> None:
                self.calls = 0

            def value(self, time: float) -> float:
                del time
                self.calls += 1
                return 1.0

            def breakpoints(self, start: float, end: float) -> list[float]:
                del start, end
                return []

        custom = CountingControl()
        custom_circuit = Circuit(
            Switch(f"S{index}", "n", "0", custom)
            for index in range(32)
        )
        custom_circuit._sample_algebraic_inputs(0.0, ())
        self.assertEqual(custom.calls, 32)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_sparse_follow_on_work_reuses_owned_evaluation_inputs(self) -> None:
        class CountingWaveform:
            def __init__(self, value: float) -> None:
                self.output = value
                self.calls = 0

            def value(self, time: float) -> float:
                self.calls += 1
                return self.output

            def breakpoints(self, start: float, end: float) -> list[float]:
                return []

        voltages = [CountingWaveform(1.0 + 0.01 * index) for index in range(16)]
        elements = []
        for index, voltage in enumerate(voltages):
            source = f"vin{index}"
            output = f"out{index}"
            elements.extend(
                [
                    VoltageSource(f"V{index}", source, "0", voltage),
                    Resistor(f"R{index}", source, output, 1_000.0),
                    Diode(f"D{index}", output, "0"),
                    Capacitor(f"C{index}", output, "0", 1.0e-6),
                ]
            )
        circuit = Circuit(elements, linear_backend="auto")
        evaluation = circuit.evaluate(2.5e-5, circuit.initial_dynamic_state())

        self.assertTrue(all(voltage.calls == 1 for voltage in voltages))
        self.assertIsNotNone(circuit._native_differential_sensitivity(evaluation))
        self.assertIsNotNone(
            circuit.sparse_implicit_update(
                evaluation,
                1.0,
                1.0e-6,
                [0.0] * circuit.dynamic_size,
            )
        )
        self.assertTrue(all(voltage.calls == 1 for voltage in voltages))

        foreign = Circuit(elements, linear_backend="auto")
        foreign._native_differential_sensitivity(evaluation)
        self.assertTrue(all(voltage.calls == 2 for voltage in voltages))

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_large_nonlinear_evaluation_reuses_accepted_diode_currents(self) -> None:
        circuit = Circuit(_diode_channel_elements(16), linear_backend="auto")
        diode_calls = 0
        calls_at_solution = None
        original_diode = circuit._diode_current_and_conductance
        original_solution = circuit._make_algebraic_solution

        def count_diode(diode, voltage):
            nonlocal diode_calls
            diode_calls += 1
            return original_diode(diode, voltage)

        def record_solution(*args, **kwargs):
            nonlocal calls_at_solution
            calls_at_solution = diode_calls
            return original_solution(*args, **kwargs)

        circuit._diode_current_and_conductance = count_diode
        circuit._make_algebraic_solution = record_solution
        evaluation = circuit.evaluate(2.5e-5, circuit.initial_dynamic_state())

        self.assertIsNotNone(calls_at_solution)
        self.assertEqual(diode_calls, calls_at_solution)
        self.assertGreater(evaluation.dissipated_power, 0.0)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_large_nonlinear_subclass_preserves_diode_override(self) -> None:
        class CustomCircuit(Circuit):
            def __init__(self, *args, **kwargs) -> None:
                self.diode_calls = 0
                super().__init__(*args, **kwargs)

            def _diode_current_and_conductance(self, diode, voltage):
                self.diode_calls += 1
                return super()._diode_current_and_conductance(diode, voltage)

        circuit = CustomCircuit(_diode_channel_elements(16), linear_backend="auto")
        circuit.evaluate(2.5e-5, circuit.initial_dynamic_state())

        self.assertGreater(circuit.diode_calls, 0)

    def test_unknown_linear_backend_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "linear backend"):
            Circuit(linear_backend="unknown")

    @unittest.skipUnless(klu_sparse_available(), "optional KLU backend unavailable")
    def test_explicit_klu_backend_runs_large_nonlinear_circuit(self) -> None:
        circuit = Circuit(_diode_channel_elements(16), linear_backend="klu")

        evaluation = circuit.evaluate(2.5e-5, circuit.initial_dynamic_state())

        self.assertLess(circuit.full_residual_norm(evaluation), 1.0e-10)

    def test_explicit_klu_backend_fails_when_library_is_missing(self) -> None:
        with patch("babcs._klu._klu_components", return_value=None):
            with self.assertRaises(LinearBackendUnavailableError):
                Circuit(linear_backend="klu")

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

    def test_newton_line_search_uses_residual_only_trials(self) -> None:
        class CountingCircuit(Circuit):
            def __init__(self) -> None:
                super().__init__(
                    [
                        VoltageSource("V1", "vin", "0", Constant(1.0)),
                        Resistor("R1", "vin", "out", 1_000.0),
                        Diode("D1", "out", "0"),
                    ]
                )
                self.full_assemblies = 0
                self.residual_only_assemblies = 0

            def _algebraic_residual_and_jacobian(self, *args, **kwargs):
                self.full_assemblies += 1
                return super()._algebraic_residual_and_jacobian(*args, **kwargs)

            def _algebraic_residual(self, *args, **kwargs):
                self.residual_only_assemblies += 1
                return super()._algebraic_residual(*args, **kwargs)

        circuit = CountingCircuit()
        evaluation = circuit.evaluate(0.0, ())

        self.assertEqual(circuit.full_assemblies, evaluation.algebraic.iterations)
        self.assertGreater(circuit.residual_only_assemblies, 0)
        self.assertLess(evaluation.algebraic.residual_norm, 1.0e-8)

    def test_differential_jacobian_reuses_matching_base_evaluation(self) -> None:
        class CountingCircuit(Circuit):
            def __init__(self) -> None:
                super().__init__(
                    [
                        VoltageSource("V1", "vin", "0", Constant(1.0)),
                        Resistor("R1", "vin", "out", 1_000.0),
                        Capacitor("C1", "out", "0", 1.0e-6),
                    ]
                )
                self.evaluations = 0

            def evaluate(self, *args, **kwargs):
                self.evaluations += 1
                return super().evaluate(*args, **kwargs)

        circuit = CountingCircuit()
        state = circuit.initial_dynamic_state()
        base = circuit.evaluate(0.0, state)
        circuit.evaluations = 0

        circuit.differential_jacobian_at_evaluation(base)

        self.assertEqual(circuit.evaluations, circuit.dynamic_size)
        with self.assertRaises(ValueError):
            circuit.differential_jacobian(
                1.0,
                state,
                base.algebraic.unknowns,
                base_evaluation=base,
            )

    def test_builtin_differential_jacobian_matches_rc_and_lc_dynamics(self) -> None:
        rc = Circuit(
            [
                VoltageSource("V1", "vin", "0", Constant(1.0)),
                Resistor("R1", "vin", "out", 1_000.0),
                Capacitor("C1", "out", "0", 1.0e-6),
            ]
        )
        rc_evaluation = rc.evaluate(0.0, rc.initial_dynamic_state())
        self.assertAlmostEqual(rc.differential_jacobian_at_evaluation(rc_evaluation)[0][0], -1_000.0)

        lc = Circuit(
            [
                Capacitor("C1", "n", "0", 1.0e-6, 1.0),
                Inductor("L1", "n", "0", 1.0e-3),
            ]
        )
        lc_evaluation = lc.evaluate(0.0, lc.initial_dynamic_state())
        self.assertEqual(
            lc.differential_jacobian_at_evaluation(lc_evaluation),
            [[0.0, -1.0e6], [1.0e3, 0.0]],
        )

    def test_differential_sensitivity_right_hand_sides_are_precompiled(self) -> None:
        circuit = Circuit(
            [
                Capacitor("C1", "n", "0", 1.0e-6),
                Inductor("L1", "n", "0", 1.0e-3),
            ]
        )

        self.assertEqual(
            circuit._differential_sensitivity_right_hand_sides,
            ((0.0, 1.0), (-1.0, 0.0)),
        )

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_native_sensitivity_reuses_read_only_right_hand_side_array(self) -> None:
        circuit = Circuit(_diode_channel_elements(16), linear_backend="auto")
        evaluation = circuit.evaluate(2.5e-5, circuit.initial_dynamic_state())

        from babcs.model import solve_factored_multiple_array as model_solve_multiple

        self.assertIsNone(circuit._native_differential_sensitivity_right_hand_sides)
        with patch(
            "babcs.model.solve_factored_multiple_array",
            wraps=model_solve_multiple,
        ) as solve_multiple:
            self.assertIsNotNone(circuit._native_differential_sensitivity(evaluation))
            first = solve_multiple.call_args.args[1]
            self.assertIsNotNone(circuit._native_differential_sensitivity(evaluation))
            second = solve_multiple.call_args.args[1]

        self.assertIs(first, second)
        self.assertIs(
            first,
            circuit._native_differential_sensitivity_right_hand_sides,
        )
        self.assertFalse(first.flags.writeable)
        with self.assertRaises(ValueError):
            first[0, 0] = 1.0

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_native_sensitivity_batches_inductors_and_tracks_reactive_values(self) -> None:
        elements = _diode_channel_elements(16)
        elements.extend(
            Inductor(
                f"L{index}",
                "0" if index % 3 == 1 else f"out{index}",
                f"out{index}" if index % 3 == 1 else (f"vin{index}" if index % 3 == 2 else "0"),
                1.0e-3 + index * 1.0e-5,
            )
            for index in range(16)
        )
        circuit = Circuit(elements, linear_backend="auto")
        evaluation = circuit.evaluate(2.5e-5, circuit.initial_dynamic_state())

        first = circuit._native_differential_sensitivity(evaluation)
        self.assertIsNotNone(first)
        assert first is not None
        first_capacitances = circuit._native_capacitances
        first_inductances = circuit._native_inductances
        self.assertFalse(first_capacitances.flags.writeable)
        self.assertFalse(first_inductances.flags.writeable)

        expected_voltages = first.numpy.zeros(
            (circuit.dynamic_size, len(circuit.inductors)),
            dtype=float,
        )
        for column, inductor in enumerate(circuit.inductors):
            positive_index = circuit.node_index.get(inductor.positive)
            negative_index = circuit.node_index.get(inductor.negative)
            if positive_index is not None:
                expected_voltages[:, column] += first.sensitivities[:, positive_index]
            if negative_index is not None:
                expected_voltages[:, column] -= first.sensitivities[:, negative_index]
        expected_inductor_rows = expected_voltages.transpose() / first_inductances[:, None]
        self.assertTrue(
            first.numpy.array_equal(
                first.differential_jacobian[len(circuit.capacitors) :, :],
                expected_inductor_rows,
            )
        )

        unchanged = circuit._native_differential_sensitivity(evaluation)
        self.assertIsNotNone(unchanged)
        self.assertIs(first_capacitances, circuit._native_capacitances)
        self.assertIs(first_inductances, circuit._native_inductances)

        circuit.capacitors[0].capacitance *= 2.0
        circuit.inductors[0].inductance *= 3.0
        changed = circuit._native_differential_sensitivity(evaluation)
        self.assertIsNotNone(changed)
        self.assertIsNot(first_capacitances, circuit._native_capacitances)
        self.assertIsNot(first_inductances, circuit._native_inductances)
        self.assertEqual(circuit._native_capacitances[0], 2.0e-6)
        self.assertEqual(circuit._native_inductances[0], 3.0e-3)

    def test_linear_differential_jacobian_cache_tracks_switch_topology(self) -> None:
        circuit = Circuit(
            [
                VoltageSource("V1", "vin", "0", Constant(1.0)),
                Resistor("R1", "vin", "out", 1_000.0),
                Capacitor("C1", "out", "0", 1.0e-6),
                Switch(
                    "S1",
                    "out",
                    "0",
                    Pulse(0.0, 1.0, 1.0e-4, 0.0, 1.0e-4, 0.0),
                    threshold=0.5,
                    on_resistance=10.0,
                    off_resistance=1.0e9,
                ),
            ]
        )
        state = circuit.initial_dynamic_state()
        off = circuit.differential_jacobian_at_evaluation(circuit.evaluate(0.0, state))
        off[0][0] = 0.0
        cached_off = circuit.differential_jacobian_at_evaluation(circuit.evaluate(0.0, state))
        on = circuit.differential_jacobian_at_evaluation(circuit.evaluate(1.5e-4, state))

        self.assertAlmostEqual(cached_off[0][0], -1_000.001)
        self.assertAlmostEqual(on[0][0], -101_000.0)
        self.assertEqual(len(circuit._linear_differential_jacobian_cache), 2)
        self.assertEqual(len(circuit._linear_algebraic_factorization_cache), 2)

    def test_linear_caches_track_resistance_mutation(self) -> None:
        circuit = Circuit(
            [
                VoltageSource("V1", "vin", "0", Constant(1.0)),
                Resistor("R1", "vin", "out", 1_000.0),
                Capacitor("C1", "out", "0", 1.0e-6),
            ]
        )
        state = circuit.initial_dynamic_state()
        first = circuit.evaluate(0.0, state)
        first_jacobian = circuit.differential_jacobian_at_evaluation(first)
        circuit.resistors[0].resistance = 2_000.0
        second = circuit.evaluate(0.0, state)
        second_jacobian = circuit.differential_jacobian_at_evaluation(second)

        self.assertAlmostEqual(first.derivative[0], 1_000.0)
        self.assertAlmostEqual(second.derivative[0], 500.0)
        self.assertAlmostEqual(first_jacobian[0][0], -1_000.0)
        self.assertAlmostEqual(second_jacobian[0][0], -500.0)
        self.assertEqual(len(circuit._linear_differential_jacobian_cache), 2)
        self.assertEqual(len(circuit._linear_algebraic_factorization_cache), 2)

    def test_cached_linear_solve_assembles_residual_without_jacobian(self) -> None:
        circuit = Circuit(
            [
                VoltageSource("V1", "vin", "0", Constant(1.0)),
                Resistor("R1", "vin", "out", 1_000.0),
                Capacitor("C1", "out", "0", 1.0e-6),
            ]
        )
        full_assemblies = 0
        residual_assemblies = 0
        original_full = circuit._algebraic_residual_and_jacobian
        original_residual = circuit._algebraic_residual

        def counted_full(*args, **kwargs):
            nonlocal full_assemblies
            full_assemblies += 1
            return original_full(*args, **kwargs)

        def counted_residual(*args, **kwargs):
            nonlocal residual_assemblies
            residual_assemblies += 1
            return original_residual(*args, **kwargs)

        circuit._algebraic_residual_and_jacobian = counted_full  # type: ignore[method-assign]
        circuit._algebraic_residual = counted_residual  # type: ignore[method-assign]
        state = circuit.initial_dynamic_state()
        first = circuit.evaluate(0.0, state)
        circuit.evaluate(1.0e-5, state, first.algebraic.unknowns)

        self.assertEqual(full_assemblies, 1)
        self.assertGreater(residual_assemblies, 1)

    def test_accepted_unknown_norm_cache_preserves_public_guess_validation(self) -> None:
        circuit = Circuit(
            [
                VoltageSource("V1", "vin", "0", Constant(1.0)),
                Resistor("R1", "vin", "out", 1_000.0),
                Capacitor("C1", "out", "0", 1.0e-6),
            ]
        )
        state = circuit.initial_dynamic_state()
        first = circuit.evaluate(0.0, state)

        from babcs.model import norm_inf as model_norm_inf

        with patch("babcs.model.norm_inf", wraps=model_norm_inf) as cached_norm:
            circuit.solve_algebraic(0.0, state, first.algebraic.unknowns)
        self.assertEqual(cached_norm.call_count, 1)

        with patch("babcs.model.norm_inf", wraps=model_norm_inf) as copied_norm:
            copied = circuit.solve_algebraic(0.0, state, list(first.algebraic.unknowns))
        self.assertEqual(copied_norm.call_count, 1)
        self.assertEqual(copied.unknowns, first.algebraic.unknowns)

        invalid_guess = list(first.algebraic.unknowns)
        invalid_guess[-1] = math.nan
        with self.assertRaisesRegex(CircuitSolveError, "initial guess must be finite"):
            circuit.solve_algebraic(0.0, state, invalid_guess)

    def test_linear_topology_caches_have_bounded_capacity(self) -> None:
        circuit = Circuit(
            [
                VoltageSource("V1", "vin", "0", Constant(1.0)),
                Resistor("R1", "vin", "out", 1_000.0),
                Capacitor("C1", "out", "0", 1.0e-6),
            ]
        )
        state = circuit.initial_dynamic_state()
        for index in range(140):
            circuit.resistors[0].resistance = 1_000.0 + index
            evaluation = circuit.evaluate(0.0, state)
            circuit.differential_jacobian_at_evaluation(evaluation)
            circuit.linear_implicit_factorization(
                evaluation,
                1.0,
                1.0e-6 * (index + 1),
            )

        self.assertLessEqual(len(circuit._linear_algebraic_factorization_cache), 128)
        self.assertLessEqual(len(circuit._linear_differential_jacobian_cache), 128)
        self.assertLessEqual(len(circuit._linear_implicit_factorization_cache), 128)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_auto_backend_uses_sparse_factors_for_large_linear_circuit(self) -> None:
        elements = []
        for index in range(8):
            node = f"tank{index}"
            elements.extend(
                [
                    Capacitor(f"C{index}", node, "0", 1.0e-6, 1.0 / (index + 1)),
                    Inductor(f"L{index}", node, "0", 1.0e-3),
                ]
            )
        circuit = Circuit(elements, linear_backend="auto")
        evaluation = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        factorization = circuit.linear_implicit_factorization(evaluation, 1.0, 1.0e-6)

        self.assertIsNotNone(factorization)
        assert factorization is not None
        self.assertEqual(factorization.backend, "scipy")
        self.assertLess(circuit.full_residual_norm(evaluation), 1.0e-12)

    @unittest.skipUnless(
        scipy_sparse_available() and klu_sparse_available(),
        "optional sparse backends unavailable",
    )
    def test_auto_backend_uses_klu_for_large_native_sensitivity(self) -> None:
        circuit = Circuit(_diode_channel_elements(32), linear_backend="auto")

        evaluation = circuit.evaluate(2.5e-5, circuit.initial_dynamic_state())
        native = circuit._native_differential_sensitivity(evaluation)
        self.assertIsNotNone(native)
        assert native is not None
        self.assertEqual(native.factorization.backend, "klu")

    @unittest.skipUnless(
        scipy_sparse_available() and klu_sparse_available(),
        "optional sparse backends unavailable",
    )
    def test_auto_native_sensitivity_falls_back_when_klu_fails(self) -> None:
        circuit = Circuit(_diode_channel_elements(32), linear_backend="auto")
        evaluation = circuit.evaluate(2.5e-5, circuit.initial_dynamic_state())
        real_factor_linear = factor_linear
        attempted_backends = []

        def fail_klu(*args, **kwargs):
            del args, kwargs
            attempted_backends.append("klu")
            raise SingularMatrixError("forced KLU failure")

        def track_factor(matrix, pivot_tolerance=1.0e-14, *, backend="dense"):
            attempted_backends.append(backend)
            return real_factor_linear(
                matrix,
                pivot_tolerance,
                backend=backend,
            )

        with patch(
            "babcs.model._factor_and_solve_klu_sparse_values_multiple_array",
            side_effect=fail_klu,
        ), patch("babcs.model.factor_linear", side_effect=track_factor):
            native = circuit._native_differential_sensitivity(evaluation)

        self.assertIsNotNone(native)
        assert native is not None
        self.assertEqual(native.factorization.backend, "scipy")
        self.assertEqual(attempted_backends, ["klu", "scipy"])

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_sparse_backend_decision_tracks_backend_changes(self) -> None:
        circuit = Circuit(_diode_channel_elements(16), linear_backend="auto")

        self.assertTrue(circuit._uses_sparse_algebraic_jacobian())
        circuit.linear_backend = "dense"
        self.assertFalse(circuit._uses_sparse_algebraic_jacobian())
        circuit.linear_backend = "auto"
        self.assertTrue(circuit._uses_sparse_algebraic_jacobian())

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_compiled_sparse_jacobian_matches_dense_stamping(self) -> None:
        elements = _diode_channel_elements(8)
        dense_circuit = Circuit(elements, linear_backend="dense")
        sparse_circuit = Circuit(elements, linear_backend="auto")
        dynamic_state = dense_circuit.initial_dynamic_state()
        dense_evaluation = dense_circuit.evaluate(2.5e-5, dynamic_state)

        dense_residual, dense_jacobian = dense_circuit._algebraic_residual_and_jacobian(
            2.5e-5,
            dynamic_state,
            dense_evaluation.algebraic.unknowns,
        )
        sparse_residual, sparse_jacobian = sparse_circuit._algebraic_residual_and_jacobian(
            2.5e-5,
            dynamic_state,
            dense_evaluation.algebraic.unknowns,
        )

        self.assertIsInstance(sparse_jacobian, SparseMatrix)
        assert isinstance(sparse_jacobian, SparseMatrix)
        self.assertEqual(sparse_residual, dense_residual)
        self.assertEqual(sparse_jacobian.to_dense(), dense_jacobian)
        self.assertEqual(
            sparse_circuit._algebraic_residual(
                2.5e-5,
                dynamic_state,
                dense_evaluation.algebraic.unknowns,
            ),
            dense_circuit._algebraic_residual(
                2.5e-5,
                dynamic_state,
                dense_evaluation.algebraic.unknowns,
            ),
        )

    @unittest.skipUnless(klu_sparse_available(), "optional KLU backend unavailable")
    def test_compiled_sparse_kernel_feeds_atomic_native_klu_sensitivity(self) -> None:
        circuit = Circuit(_diode_channel_elements(32), linear_backend="klu")
        state = circuit.initial_dynamic_state()
        evaluation = circuit.evaluate(2.5e-5, state)
        inputs = evaluation._algebraic_inputs
        kernel = circuit._build_compiled_sparse_algebraic_kernel()
        circuit._compiled_sparse_algebraic_kernel = kernel

        residual, matrix = kernel(
            circuit,
            evaluation.time,
            state,
            evaluation.algebraic.unknowns,
            inputs,
        )
        raw_residual, raw_data = kernel(
            circuit,
            evaluation.time,
            state,
            evaluation.algebraic.unknowns,
            inputs,
            True,
        )
        self.assertEqual(raw_residual, residual)
        self.assertIsInstance(raw_data, list)
        self.assertEqual(tuple(raw_data), matrix.data)

        jacobian_kernel = circuit._build_compiled_sparse_algebraic_jacobian_kernel()
        assembled_unknowns = (123.0,)
        assembled_diode_currents = (456.0,)
        circuit._last_assembled_unknowns = assembled_unknowns
        circuit._last_assembled_diode_currents = assembled_diode_currents
        jacobian_data = jacobian_kernel(
            circuit,
            evaluation.algebraic.unknowns,
            inputs,
        )
        self.assertEqual(tuple(jacobian_data), matrix.data)
        self.assertIs(circuit._last_assembled_unknowns, assembled_unknowns)
        self.assertIs(
            circuit._last_assembled_diode_currents,
            assembled_diode_currents,
        )

        circuit.resistors[0].resistance = 1_500.0
        circuit.diodes[0].saturation_current = 2.0e-12
        circuit.diodes[0].thermal_voltage = 0.03
        mutated_residual, mutated_matrix = kernel(
            circuit,
            evaluation.time,
            state,
            evaluation.algebraic.unknowns,
            inputs,
        )
        del mutated_residual
        mutated_jacobian_data = jacobian_kernel(
            circuit,
            evaluation.algebraic.unknowns,
            inputs,
        )
        self.assertEqual(tuple(mutated_jacobian_data), mutated_matrix.data)
        circuit._compiled_sparse_algebraic_kernel = None
        circuit._compiled_sparse_algebraic_jacobian_kernel = None

        from babcs.model import (
            _factor_and_solve_klu_sparse_values_multiple_array as model_atomic_solve,
        )

        with (
            patch.object(
                circuit,
                "_build_compiled_sparse_algebraic_jacobian_kernel",
                wraps=circuit._build_compiled_sparse_algebraic_jacobian_kernel,
            ) as build_jacobian_kernel,
            patch(
                "babcs.model._factor_and_solve_klu_sparse_values_multiple_array",
                wraps=model_atomic_solve,
            ) as atomic_solve,
        ):
            native = circuit._native_differential_sensitivity(evaluation)

        self.assertIsNotNone(native)
        self.assertEqual(build_jacobian_kernel.call_count, 1)
        self.assertEqual(atomic_solve.call_count, 1)
        self.assertIsInstance(atomic_solve.call_args.args[1], list)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_specialized_residual_kernel_matches_fallback_and_tracks_mutation(self) -> None:
        class FallbackCircuit(Circuit):
            pass

        elements = _diode_channel_elements(16)
        elements.extend(
            [
                CurrentSource("Iextra", "out0", "0", Constant(1.0e-6)),
                Switch("Sextra", "out1", "0", Constant(1.0)),
                Inductor("Lextra", "out2", "0", 1.0e-3),
            ]
        )
        dense = Circuit(elements, linear_backend="dense")
        specialized = Circuit(elements, linear_backend="auto")
        fallback = FallbackCircuit(elements, linear_backend="auto")
        state = dense.initial_dynamic_state()
        unknowns = dense.evaluate(2.5e-5, state).algebraic.unknowns

        self.assertIsNotNone(specialized._compiled_algebraic_residual_kernel)
        self.assertIsNone(fallback._compiled_algebraic_residual_kernel)

        def residual(circuit):
            inputs = circuit._sample_algebraic_inputs(2.5e-5, state)
            return circuit._assemble_compiled_algebraic_residual(
                2.5e-5,
                state,
                unknowns,
                inputs,
            )

        self.assertEqual(residual(specialized), residual(fallback))

        for circuit in (specialized, fallback):
            circuit.resistors[0].resistance = 1_500.0
            circuit.diodes[0].saturation_current = 2.0e-12
            circuit.diodes[0].thermal_voltage = 0.03
            circuit.switches[0].on_resistance = 2.0e-3
        self.assertEqual(residual(specialized), residual(fallback))

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_specialized_sparse_kernel_is_demand_gated_and_tracks_mutation(self) -> None:
        class FallbackCircuit(Circuit):
            pass

        _clear_compiled_sparse_algebraic_topologies()
        elements = _diode_channel_elements(16)
        elements.extend(
            [
                CurrentSource("Iextra", "out0", "0", Constant(1.0e-6)),
                Switch("Sextra", "out1", "0", Constant(1.0)),
                Inductor("Lextra", "out2", "0", 1.0e-3),
            ]
        )
        dense = Circuit(elements, linear_backend="dense")
        specialized = Circuit(elements, linear_backend="auto")
        fallback = FallbackCircuit(elements, linear_backend="auto")
        state = dense.initial_dynamic_state()
        unknowns = dense.evaluate(2.5e-5, state).algebraic.unknowns

        def assembly(circuit):
            inputs = circuit._sample_algebraic_inputs(2.5e-5, state)
            residual, jacobian = circuit._assemble_sparse_algebraic(
                2.5e-5,
                state,
                unknowns,
                inputs,
            )
            return residual, jacobian.data

        self.assertIsNone(specialized._compiled_sparse_algebraic_kernel)
        self.assertIsNone(fallback._compiled_sparse_algebraic_kernel)
        with patch("babcs.model.COMPILED_SPARSE_ALGEBRAIC_MINIMUM_CALLS", 2):
            self.assertEqual(assembly(specialized), assembly(fallback))
            self.assertIsNone(specialized._compiled_sparse_algebraic_kernel)
            self.assertEqual(specialized._compiled_sparse_algebraic_calls, 1)

            self.assertEqual(assembly(specialized), assembly(fallback))
            self.assertIsNotNone(specialized._compiled_sparse_algebraic_kernel)
            self.assertEqual(specialized._compiled_sparse_algebraic_calls, 2)

            for circuit in (specialized, fallback):
                circuit.resistors[0].resistance = 1_500.0
                circuit.diodes[0].saturation_current = 2.0e-12
                circuit.diodes[0].thermal_voltage = 0.03
                circuit.switches[0].on_resistance = 2.0e-3
            self.assertEqual(assembly(specialized), assembly(fallback))

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_hot_sparse_topology_reuses_kernel_without_repeating_demand_gate(self) -> None:
        class FallbackCircuit(Circuit):
            pass

        _clear_compiled_sparse_algebraic_topologies()
        first_elements = _diode_channel_elements(16)
        first = Circuit(first_elements, linear_backend="auto")
        first_fallback = FallbackCircuit(first_elements, linear_backend="auto")
        second_elements = _diode_channel_elements(16)
        second_elements[1].resistance = 2_000.0
        second = Circuit(second_elements, linear_backend="auto")
        second_fallback = FallbackCircuit(second_elements, linear_backend="auto")
        state = first.initial_dynamic_state()
        unknowns = first.evaluate(2.5e-5, state).algebraic.unknowns

        def assembly(circuit):
            inputs = circuit._sample_algebraic_inputs(2.5e-5, state)
            residual, jacobian = circuit._assemble_sparse_algebraic(
                2.5e-5,
                state,
                unknowns,
                inputs,
            )
            return residual, jacobian.data

        with patch("babcs.model.COMPILED_SPARSE_ALGEBRAIC_MINIMUM_CALLS", 2):
            self.assertEqual(assembly(first), assembly(first_fallback))
            self.assertEqual(assembly(first), assembly(first_fallback))
            self.assertIsNotNone(first._compiled_sparse_algebraic_kernel)

            self.assertEqual(assembly(second), assembly(second_fallback))
            self.assertIs(
                second._compiled_sparse_algebraic_kernel,
                first._compiled_sparse_algebraic_kernel,
            )
            self.assertEqual(second._compiled_sparse_algebraic_calls, 0)

            second.resistors[0].resistance = 1_500.0
            second_fallback.resistors[0].resistance = 1_500.0
            self.assertEqual(assembly(second), assembly(second_fallback))

            distinct = Circuit(_diode_channel_elements(17), linear_backend="auto")
            distinct_state = distinct.initial_dynamic_state()
            distinct_unknowns = (0.0,) * distinct.algebraic_size
            distinct_inputs = distinct._sample_algebraic_inputs(
                2.5e-5,
                distinct_state,
            )
            distinct._assemble_sparse_algebraic(
                2.5e-5,
                distinct_state,
                distinct_unknowns,
                distinct_inputs,
            )
            self.assertIsNone(distinct._compiled_sparse_algebraic_kernel)
            self.assertEqual(distinct._compiled_sparse_algebraic_calls, 1)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_sparse_kernel_compilation_is_shared_by_topology(self) -> None:
        _compile_sparse_algebraic_kernel.cache_clear()
        _compile_sparse_algebraic_jacobian_kernel.cache_clear()
        first = Circuit(_diode_channel_elements(16), linear_backend="auto")
        second_elements = _diode_channel_elements(16)
        second_elements[1].resistance = 2_000.0
        second = Circuit(second_elements, linear_backend="auto")

        first_kernel = first._build_compiled_sparse_algebraic_kernel()
        second_kernel = second._build_compiled_sparse_algebraic_kernel()
        first_jacobian_kernel = (
            first._build_compiled_sparse_algebraic_jacobian_kernel()
        )
        second_jacobian_kernel = (
            second._build_compiled_sparse_algebraic_jacobian_kernel()
        )

        self.assertIs(first_kernel, second_kernel)
        self.assertIs(first_jacobian_kernel, second_jacobian_kernel)
        cache_info = _compile_sparse_algebraic_kernel.cache_info()
        self.assertEqual(
            (cache_info.hits, cache_info.misses, cache_info.maxsize),
            (1, 1, 128),
        )
        jacobian_cache_info = _compile_sparse_algebraic_jacobian_kernel.cache_info()
        self.assertEqual(
            (
                jacobian_cache_info.hits,
                jacobian_cache_info.misses,
                jacobian_cache_info.maxsize,
            ),
            (1, 1, 128),
        )

    def test_compiled_sparse_topology_cache_is_bounded_lru(self) -> None:
        _clear_compiled_sparse_algebraic_topologies()
        kernels = [object() for _ in range(MAXIMUM_COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES + 2)]
        try:
            for index, kernel in enumerate(kernels[:-1]):
                _store_compiled_sparse_algebraic_topology((index,), kernel)

            self.assertIsNone(_lookup_compiled_sparse_algebraic_topology((0,)))
            self.assertIs(
                _lookup_compiled_sparse_algebraic_topology((1,)),
                kernels[1],
            )

            _store_compiled_sparse_algebraic_topology(
                (len(kernels),),
                kernels[-1],
            )
            self.assertIsNone(_lookup_compiled_sparse_algebraic_topology((2,)))
            self.assertIs(
                _lookup_compiled_sparse_algebraic_topology((1,)),
                kernels[1],
            )
        finally:
            _clear_compiled_sparse_algebraic_topologies()

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_sparse_implicit_block_matches_explicit_schur_update(self) -> None:
        circuit = Circuit(_diode_channel_elements(8), linear_backend="auto")
        evaluation = circuit.evaluate(2.5e-5, circuit.initial_dynamic_state())
        state_coefficient = 1.0
        derivative_coefficient = 1.0e-6
        residual = tuple(0.01 * (index + 1) for index in range(circuit.dynamic_size))
        differential_jacobian = circuit.differential_jacobian_at_evaluation(evaluation)
        schur_jacobian = [
            [
                (state_coefficient if row == column else 0.0)
                - derivative_coefficient * differential_jacobian[row][column]
                for column in range(circuit.dynamic_size)
            ]
            for row in range(circuit.dynamic_size)
        ]
        expected = solve_linear(
            schur_jacobian,
            [-value for value in residual],
            backend="auto",
        )

        actual = circuit.sparse_implicit_update(
            evaluation,
            state_coefficient,
            derivative_coefficient,
            residual,
        )

        self.assertIsNotNone(actual)
        assert actual is not None
        for actual_value, expected_value in zip(
            actual.dynamic_update,
            expected,
            strict=True,
        ):
            self.assertAlmostEqual(actual_value, expected_value, places=13)

        _, algebraic_jacobian = circuit._algebraic_residual_and_jacobian(
            evaluation.time,
            evaluation.dynamic_state,
            evaluation.algebraic.unknowns,
        )
        assert isinstance(algebraic_jacobian, SparseMatrix)
        dense_algebraic_jacobian = algebraic_jacobian.to_dense()
        for row in range(circuit.algebraic_size):
            linearized_residual = sum(
                dense_algebraic_jacobian[row][column]
                * actual.algebraic_update[column]
                for column in range(circuit.algebraic_size)
            )
            linearized_residual -= sum(
                right_hand_side[row] * actual.dynamic_update[state_index]
                for state_index, right_hand_side in enumerate(
                    circuit._differential_sensitivity_right_hand_sides
                )
            )
            self.assertAlmostEqual(linearized_residual, 0.0, places=13)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_sparse_chord_schur_matches_exact_same_evaluation_update(self) -> None:
        elements = _diode_channel_elements(16)
        elements.extend(
            Inductor(f"L{index}", f"out{index}", "0", 1.0e-3)
            for index in range(16)
        )
        circuit = Circuit(elements, linear_backend="auto")
        evaluation = circuit.evaluate(2.5e-5, circuit.initial_dynamic_state())
        self.assertIsNotNone(circuit._native_differential_sensitivity(evaluation))
        residual = tuple(0.001 * (index + 1) for index in range(circuit.dynamic_size))

        chord = circuit.sparse_implicit_update(
            evaluation,
            1.0,
            1.0e-6,
            residual,
        )
        exact = circuit.sparse_implicit_update(
            evaluation,
            1.0,
            1.0e-6,
            residual,
            allow_chord=False,
        )

        self.assertIsNotNone(chord)
        self.assertIsNotNone(exact)
        assert chord is not None and exact is not None
        self.assertTrue(chord.requires_contraction)
        for chord_value, exact_value in zip(
            chord.dynamic_update,
            exact.dynamic_update,
            strict=True,
        ):
            self.assertAlmostEqual(chord_value, exact_value, places=13)
        for chord_value, exact_value in zip(
            chord.algebraic_update,
            exact.algebraic_update,
            strict=True,
        ):
            self.assertAlmostEqual(chord_value, exact_value, places=13)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_sparse_chord_marks_previous_sensitivity_as_contractive(self) -> None:
        circuit = Circuit(_diode_channel_elements(16), linear_backend="auto")
        state = circuit.initial_dynamic_state()
        source = circuit.evaluate(2.5e-5, state)
        self.assertIsNotNone(circuit._native_differential_sensitivity(source))
        target = circuit.evaluate(2.6e-5, state, source.algebraic.unknowns)

        update = circuit.sparse_implicit_update(
            target,
            1.0,
            1.0e-6,
            [0.001] * circuit.dynamic_size,
        )

        self.assertIsNotNone(update)
        assert update is not None
        self.assertTrue(update.requires_contraction)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_sparse_chord_uses_ulp_aware_two_step_evidence_age(self) -> None:
        circuit = Circuit(_diode_channel_elements(16), linear_backend="auto")
        state = circuit.initial_dynamic_state()
        step = 1.0e-6
        times = [0.0]
        for _ in range(123):
            times.append(times[-1] + step)
        source_time = times[121]
        target_time = times[123]
        age_ratio = (target_time - source_time) / step
        self.assertGreater(age_ratio, 2.000000000000001)
        self.assertTrue(_within_ulp_time_window(source_time, target_time, 2.0 * step))

        source = circuit.evaluate(source_time, state)
        self.assertIsNotNone(circuit._native_differential_sensitivity(source))
        target = circuit.evaluate(target_time, state, source.algebraic.unknowns)
        accepted = circuit.sparse_implicit_update(
            target,
            1.0,
            step,
            [0.001] * circuit.dynamic_size,
        )
        self.assertIsNotNone(accepted)
        assert accepted is not None
        self.assertTrue(accepted.requires_contraction)

        stale_time = source_time + 2.0 * step
        for _ in range(16):
            stale_time = math.nextafter(stale_time, math.inf)
        self.assertFalse(_within_ulp_time_window(source_time, stale_time, 2.0 * step))
        stale = circuit.evaluate(stale_time, state, source.algebraic.unknowns)
        rejected = circuit.sparse_implicit_update(
            stale,
            1.0,
            step,
            [0.001] * circuit.dynamic_size,
        )
        self.assertIsNotNone(rejected)
        assert rejected is not None
        self.assertFalse(rejected.requires_contraction)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_sparse_chord_rejects_changed_switch_topology(self) -> None:
        elements = _diode_channel_elements(16)
        switch = Switch("Sextra", "out0", "0", Constant(0.0))
        elements.append(switch)
        circuit = Circuit(elements, linear_backend="auto")
        state = circuit.initial_dynamic_state()
        source = circuit.evaluate(2.5e-5, state)
        self.assertIsNotNone(circuit._native_differential_sensitivity(source))
        circuit.switches[0].control = Constant(1.0)
        target = circuit.evaluate(2.6e-5, state, source.algebraic.unknowns)

        update = circuit.sparse_implicit_update(
            target,
            1.0,
            1.0e-6,
            [0.001] * circuit.dynamic_size,
        )

        self.assertIsNotNone(update)
        assert update is not None
        self.assertFalse(update.requires_contraction)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_native_differential_jacobian_norm_conservatively_bounds_materialized_norm(self) -> None:
        circuit = Circuit(_diode_channel_elements(16), linear_backend="auto")
        evaluation = circuit.evaluate(2.5e-5, circuit.initial_dynamic_state())

        materialized = matrix_inf_norm(
            circuit.differential_jacobian_at_evaluation(evaluation)
        )
        native = circuit.differential_jacobian_norm_at_evaluation(evaluation)

        self.assertGreaterEqual(native, materialized)
        self.assertLessEqual(native - materialized, materialized * 1.0e-12)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_large_nonlinear_solve_reuses_guarded_chord_factorization(self) -> None:
        circuit = Circuit(_diode_channel_elements(16), linear_backend="auto")
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        second_state = tuple(
            value + 1.0e-6 * derivative
            for value, derivative in zip(
                initial.dynamic_state,
                initial.derivative,
                strict=True,
            )
        )
        second = circuit.evaluate(
            1.0e-6,
            second_state,
            initial.algebraic.unknowns,
        )
        self.assertIsNotNone(circuit._last_nonlinear_algebraic_factorization)
        third_state = tuple(
            value + 1.0e-6 * derivative
            for value, derivative in zip(
                second.dynamic_state,
                second.derivative,
                strict=True,
            )
        )

        with patch("babcs.model.factor_linear", wraps=factor_linear) as factor:
            third = circuit.evaluate(
                2.0e-6,
                third_state,
                second.algebraic.unknowns,
            )

        self.assertEqual(factor.call_count, 0)
        self.assertEqual(third.algebraic.iterations, 1)
        self.assertLessEqual(third.algebraic.residual_norm, 1.0e-9)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_stale_chord_factorization_falls_back_to_fresh_newton(self) -> None:
        circuit = Circuit(_diode_channel_elements(16), linear_backend="auto")
        initial = circuit.evaluate(0.0, circuit.initial_dynamic_state())
        second_state = tuple(
            value + 1.0e-6 * derivative
            for value, derivative in zip(
                initial.dynamic_state,
                initial.derivative,
                strict=True,
            )
        )
        second = circuit.evaluate(
            1.0e-6,
            second_state,
            initial.algebraic.unknowns,
        )
        stale_factorization = circuit._last_nonlinear_algebraic_factorization
        assert stale_factorization is not None
        third_state = tuple(
            value + 1.0e-6 * derivative
            for value, derivative in zip(
                second.dynamic_state,
                second.derivative,
                strict=True,
            )
        )
        original_solve_factored = solve_factored
        stale_failure_injected = False

        def fail_stale_once(factorization, right_hand_side):
            nonlocal stale_failure_injected
            if factorization is stale_factorization and not stale_failure_injected:
                stale_failure_injected = True
                raise SingularMatrixError("forced stale chord failure")
            return original_solve_factored(factorization, right_hand_side)

        with patch("babcs.model.solve_factored", side_effect=fail_stale_once):
            third = circuit.evaluate(
                2.0e-6,
                third_state,
                second.algebraic.unknowns,
            )

        self.assertTrue(stale_failure_injected)
        self.assertIsNot(circuit._last_nonlinear_algebraic_factorization, stale_factorization)
        self.assertLessEqual(third.algebraic.residual_norm, 1.0e-9)

    @unittest.skipUnless(scipy_sparse_available(), "optional scipy backend unavailable")
    def test_auto_backend_keeps_small_nonlinear_jacobian_dense(self) -> None:
        circuit = Circuit(_diode_channel_elements(4), linear_backend="auto")
        dynamic_state = circuit.initial_dynamic_state()
        evaluation = circuit.evaluate(0.0, dynamic_state)
        _, jacobian = circuit._algebraic_residual_and_jacobian(
            0.0,
            dynamic_state,
            evaluation.algebraic.unknowns,
        )

        self.assertIsInstance(jacobian, list)

    def test_floating_current_source_fails_closed(self) -> None:
        circuit = Circuit([CurrentSource("I1", "n", "0", Constant(1.0))])
        with self.assertRaises(CircuitSolveError):
            circuit.evaluate(0.0, ())

    def test_conflicting_voltage_constraints_fail_closed(self) -> None:
        circuit = Circuit(
            [
                VoltageSource("V1", "n", "0", Constant(1.0)),
                VoltageSource("V2", "n", "0", Constant(2.0)),
            ]
        )
        with self.assertRaises(CircuitSolveError):
            circuit.evaluate(0.0, ())

    def test_unsupported_capacitor_loop_and_inductor_cutset_fail_closed(self) -> None:
        circuits = (
            Circuit(
                [
                    Capacitor("C1", "a", "b", 1.0e-6, 1.0),
                    Capacitor("C2", "b", "a", 1.0e-6, 1.0),
                ]
            ),
            Circuit(
                [
                    Inductor("L1", "n", "0", 1.0e-3, 1.0),
                    Inductor("L2", "n", "0", 1.0e-3, 1.0),
                ]
            ),
        )
        for circuit in circuits:
            with self.subTest(dynamic_names=circuit.dynamic_names), self.assertRaises(
                CircuitSolveError
            ):
                circuit.evaluate(0.0, circuit.initial_dynamic_state())

    def test_non_finite_model_and_state_inputs_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            Circuit([Resistor("R1", "n", "0", math.nan)])
        circuit = Circuit([Capacitor("C1", "n", "0", 1.0e-6)])
        with self.assertRaises(CircuitSolveError):
            circuit.evaluate(0.0, (math.nan,))

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
