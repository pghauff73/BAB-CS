from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from babcs import BoundedIntegrator, Simulator
from babcs.io import load_case, summary_data, write_csv, write_summary
from tools.compare_methods import execute_manifest, load_manifest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ROOT = REPOSITORY_ROOT / "examples/power_stage"
MANIFEST = REPOSITORY_ROOT / "benchmarks/power_stage/manifest.json"
CASES = (
    EXAMPLE_ROOT / "buck_like_reduced_order.json",
    EXAMPLE_ROOT / "h_bridge_rl_reduced_order.json",
    EXAMPLE_ROOT / "dc_link_rlc_reduced_order.json",
)
CLASSIFICATION = "reduced-order numerical experiment, not a production device model"


class PowerStageExampleTests(unittest.TestCase):
    def test_examples_have_exact_reduced_order_classification(self) -> None:
        for path in CASES:
            with self.subTest(path=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data["experiment"]["classification"], CLASSIFICATION)
                self.assertTrue(data["experiment"]["omitted_effects"])
        self.assertIn(
            "These are reduced-order numerical experiments, not production device models.",
            (EXAMPLE_ROOT / "README.md").read_text(encoding="utf-8"),
        )

    def test_examples_are_deterministic_event_aligned_and_bounded(self) -> None:
        for path in CASES:
            with self.subTest(path=path.name):
                first_circuit, simulation, config = load_case(path)
                first = Simulator(BoundedIntegrator(config)).run(first_circuit, **simulation)
                second_circuit, second_simulation, second_config = load_case(path)
                second = Simulator(BoundedIntegrator(second_config)).run(
                    second_circuit,
                    **second_simulation,
                )
                self.assertEqual(first, second)
                expected_events = first_circuit.breakpoints(
                    simulation["start_time"],
                    simulation["stop_time"],
                )
                event_points = [point for point in first.points if point.event_boundary]
                self.assertEqual([point.time for point in event_points], expected_events)
                self.assertTrue(event_points)
                for point in event_points:
                    assert point.metrics is not None
                    self.assertTrue(point.metrics.periodic_reanchor)
                    self.assertGreaterEqual(point.metrics.replay_refinement_substeps, 8)
                    self.assertGreater(point.metrics.reference_solve_count, 0)
                    dynamic_state = point.state.evaluation.dynamic_state
                    left = first_circuit.evaluate(math.nextafter(point.time, -math.inf), dynamic_state)
                    right = first_circuit.evaluate(math.nextafter(point.time, math.inf), dynamic_state)
                    self.assertEqual(left.dynamic_state, right.dynamic_state)
                for point in first.points:
                    values = (
                        point.state.evaluation.dynamic_state
                        + point.state.evaluation.derivative
                        + (
                            point.state.evaluation.stored_energy,
                            point.state.evaluation.source_power,
                            point.state.evaluation.dissipated_power,
                        )
                    )
                    self.assertTrue(all(math.isfinite(value) for value in values))
                summary = summary_data(first)
                self.assertLessEqual(summary["maximum_algebraic_residual"], config.algebraic_residual_cap)
                self.assertLessEqual(summary["maximum_full_residual"], config.full_residual_cap)
                self.assertLessEqual(summary["maximum_energy_injection_ratio"], config.energy_injection_cap)

                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    first_csv = root / "first.csv"
                    second_csv = root / "second.csv"
                    first_summary = root / "first.json"
                    second_summary = root / "second.json"
                    write_csv(first_csv, first_circuit, first)
                    write_csv(second_csv, second_circuit, second)
                    write_summary(first_summary, first)
                    write_summary(second_summary, second)
                    self.assertEqual(first_csv.read_bytes(), second_csv.read_bytes())
                    self.assertEqual(first_summary.read_bytes(), second_summary.read_bytes())

    def test_buck_and_dc_link_freewheel_diodes_conduct(self) -> None:
        for name in ("buck_like_reduced_order.json", "dc_link_rlc_reduced_order.json"):
            with self.subTest(name=name):
                circuit, simulation, config = load_case(EXAMPLE_ROOT / name)
                result = Simulator(BoundedIntegrator(config)).run(circuit, **simulation)
                diode = circuit.diodes[0]
                diode_voltages = [
                    circuit.branch_voltage(
                        point.state.evaluation.algebraic,
                        diode.positive,
                        diode.negative,
                    )
                    for point in result.points
                ]
                self.assertGreater(max(diode_voltages), 0.5)

    def test_h_bridge_schedule_has_dead_time_and_polarity_reversal(self) -> None:
        circuit, simulation, config = load_case(EXAMPLE_ROOT / "h_bridge_rl_reduced_order.json")
        switches = {switch.name: switch for switch in circuit.switches}
        sample_times = [index * 5.0e-6 for index in range(81)]
        dead_time_seen = False
        for time in sample_times:
            left_high = switches["S_LEFT_HIGH"].control.value(time) >= 0.5
            left_low = switches["S_LEFT_LOW"].control.value(time) >= 0.5
            right_high = switches["S_RIGHT_HIGH"].control.value(time) >= 0.5
            right_low = switches["S_RIGHT_LOW"].control.value(time) >= 0.5
            self.assertFalse(left_high and left_low)
            self.assertFalse(right_high and right_low)
            dead_time_seen |= not any((left_high, left_low, right_high, right_low))
        self.assertTrue(dead_time_seen)
        result = Simulator(BoundedIntegrator(config)).run(circuit, **simulation)
        positive = min(result.points, key=lambda point: abs(point.time - 5.0e-5))
        negative = min(result.points, key=lambda point: abs(point.time - 1.5e-4))
        positive_voltage = (
            positive.state.evaluation.algebraic.node_voltages["left"]
            - positive.state.evaluation.algebraic.node_voltages["right"]
        )
        negative_voltage = (
            negative.state.evaluation.algebraic.node_voltages["left"]
            - negative.state.evaluation.algebraic.node_voltages["right"]
        )
        self.assertGreater(positive_voltage, 0.0)
        self.assertLess(negative_voltage, 0.0)

    def test_dc_link_stored_energy_decays_after_interruption(self) -> None:
        circuit, simulation, config = load_case(EXAMPLE_ROOT / "dc_link_rlc_reduced_order.json")
        result = Simulator(BoundedIntegrator(config)).run(circuit, **simulation)
        interruption = min(result.points, key=lambda point: abs(point.time - 2.2e-4))
        self.assertGreater(interruption.state.evaluation.stored_energy, 0.0)
        self.assertLess(
            result.points[-1].state.evaluation.stored_energy,
            interruption.state.evaluation.stored_energy,
        )

    def test_power_stage_manifest_has_refined_authority_profiles(self) -> None:
        manifest = load_manifest(MANIFEST)
        self.assertEqual(len(manifest["cases"]), 3)
        for case in manifest["cases"]:
            self.assertEqual(case["authority"]["type"], "refined_replay")
            self.assertGreaterEqual(len(case["nominal_steps"]), 3)
            self.assertTrue(all(method.startswith("candidate_") for method in case["methods"]))
        report, _ = execute_manifest(
            MANIFEST,
            selected_cases={"buck_like_reduced_order"},
            quick=True,
        )
        self.assertTrue(report["results"])
        self.assertTrue(all(row["status"] == "success" for row in report["results"]))


if __name__ == "__main__":
    unittest.main()
