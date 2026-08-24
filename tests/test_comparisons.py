from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.compare_methods import (
    ComparisonConfigurationError,
    execute_manifest,
    load_manifest,
    write_csv_report,
    write_report,
    write_svg_plot,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPOSITORY_ROOT / "benchmarks" / "manifest.json"


class ComparisonRunnerTests(unittest.TestCase):
    def test_manifest_declares_all_standard_methods(self) -> None:
        manifest = load_manifest(MANIFEST)
        methods = {
            method
            for case in manifest["cases"]
            for method in case["methods"]
        }
        self.assertEqual(
            methods,
            {"backward_euler", "trapezoidal", "bdf2", "shadow", "active", "raw_ab2"},
        )

    def test_quick_analytic_report_is_byte_deterministic(self) -> None:
        first, _ = execute_manifest(MANIFEST, selected_cases={"rc_step"}, quick=True)
        second, _ = execute_manifest(MANIFEST, selected_cases={"rc_step"}, quick=True)
        first_bytes = json.dumps(first, indent=2, sort_keys=True, allow_nan=False).encode()
        second_bytes = json.dumps(second, indent=2, sort_keys=True, allow_nan=False).encode()
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(len(first["source"]["source_tree_sha256"]), 64)
        self.assertGreater(first["source"]["source_file_count"], 0)
        self.assertEqual(len(first["results"]), 12)
        self.assertTrue(first["analyses"]["convergence"])
        active = [result for result in first["results"] if result["method"] == "active"]
        self.assertTrue(active)
        self.assertTrue(all(result["bound"]["authority"] != "none" for result in active))
        self.assertTrue(all(result["work"]["reference_solves"] > 0 for result in active))
        self.assertTrue(
            all(result["work"]["deterministic_work_units"] > result["work"]["accepted_steps"] for result in active)
        )

    def test_refined_replay_authority_runs(self) -> None:
        report, _ = execute_manifest(MANIFEST, selected_cases={"diode_clip"}, quick=True)
        self.assertTrue(report["results"])
        self.assertTrue(
            all(result["authority"]["type"] == "refined_replay" for result in report["results"])
        )
        self.assertTrue(
            all(result["accuracy"]["maximum_absolute_error"] >= 0.0 for result in report["results"])
        )

    def test_oscillator_reports_amplitude_phase_and_energy_separately(self) -> None:
        report, _ = execute_manifest(MANIFEST, selected_cases={"lc_long"}, quick=True)
        for result in report["results"]:
            oscillator = result["oscillator"]
            assert oscillator is not None
            self.assertGreaterEqual(oscillator["relative_amplitude_error"], 0.0)
            self.assertGreaterEqual(oscillator["final_phase_error_radians"], 0.0)
            self.assertGreaterEqual(oscillator["relative_period_error"], 0.0)
            self.assertGreaterEqual(oscillator["relative_energy_span"], 0.0)
            if result["method"] == "active":
                self.assertGreater(result["bound"]["anchor_ratio_samples"], 0)
                self.assertIsNotNone(
                    result["bound"]["maximum_empirical_anchor_error_to_pre_reset_bound"]
                )

    def test_timing_is_separate_from_numerical_report(self) -> None:
        numerical, timing = execute_manifest(
            MANIFEST,
            selected_cases={"rc_step"},
            quick=True,
            timing_repeats=2,
        )
        self.assertIn("environment", numerical)
        self.assertNotIn("timing_repeats", numerical)
        self.assertNotIn("elapsed_seconds", json.dumps(numerical, sort_keys=True))
        assert timing is not None
        self.assertEqual(timing["timing_repeats"], 2)
        self.assertEqual(len(timing["results"]), len(numerical["results"]))

    def test_write_report_refuses_unapproved_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            write_report(output, {"value": 1})
            with self.assertRaises(FileExistsError):
                write_report(output, {"value": 2})
            write_report(output, {"value": 2}, overwrite=True)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"value": 2})

    def test_csv_and_svg_outputs_are_deterministic(self) -> None:
        report, _ = execute_manifest(MANIFEST, selected_cases={"rc_step"}, quick=True)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_csv = root / "first.csv"
            second_csv = root / "second.csv"
            first_svg = root / "first.svg"
            second_svg = root / "second.svg"
            write_csv_report(first_csv, report)
            write_csv_report(second_csv, report)
            write_svg_plot(first_svg, report)
            write_svg_plot(second_svg, report)
            self.assertEqual(first_csv.read_bytes(), second_csv.read_bytes())
            self.assertEqual(first_svg.read_bytes(), second_svg.read_bytes())
            self.assertIn(b"maximum_absolute_error", first_csv.read_bytes())
            self.assertIn(b"<svg", first_svg.read_bytes())

    def test_invalid_method_and_raw_mapping_fail_closed(self) -> None:
        base = json.loads(MANIFEST.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = dict(base["cases"][0])
            case["input"] = str(REPOSITORY_ROOT / "benchmarks" / "cases" / "rc_step.json")
            case["methods"] = ["unknown"]
            invalid_method = root / "invalid-method.json"
            invalid_method.write_text(
                json.dumps({"schema_version": 1, "cases": [case]}),
                encoding="utf-8",
            )
            with self.assertRaises(ComparisonConfigurationError):
                load_manifest(invalid_method)

            case["methods"] = ["raw_ab2"]
            case.pop("raw_model", None)
            invalid_raw = root / "invalid-raw.json"
            invalid_raw.write_text(
                json.dumps({"schema_version": 1, "cases": [case]}),
                encoding="utf-8",
            )
            with self.assertRaises(ComparisonConfigurationError):
                load_manifest(invalid_raw)


if __name__ == "__main__":
    unittest.main()
