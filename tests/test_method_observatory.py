from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.method_observatory import (
    DEFAULT_MANIFEST,
    REQUIRED_CANDIDATES,
    REQUIRED_CASES,
    execute_observatory,
    write_accuracy_by_work_svg,
    write_analysis_csv,
    write_markdown_summary,
)


class MethodObservatoryTests(unittest.TestCase):
    def test_manifest_has_exact_six_case_seven_candidate_coverage(self) -> None:
        manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual({case["id"] for case in manifest["cases"]}, REQUIRED_CASES)
        self.assertEqual(set(manifest["candidate_methods"]), REQUIRED_CANDIDATES)
        self.assertTrue(
            all(set(case["methods"]) == REQUIRED_CANDIDATES for case in manifest["cases"])
        )
        self.assertTrue(all(len(case["nominal_steps"]) >= 3 for case in manifest["cases"]))

    def test_quick_rc_observatory_is_complete_and_deterministic(self) -> None:
        first, _ = execute_observatory(
            DEFAULT_MANIFEST,
            selected_cases={"rc_step"},
            quick=True,
        )
        second, _ = execute_observatory(
            DEFAULT_MANIFEST,
            selected_cases={"rc_step"},
            quick=True,
        )
        self.assertEqual(
            json.dumps(first, sort_keys=True, allow_nan=False),
            json.dumps(second, sort_keys=True, allow_nan=False),
        )
        self.assertEqual(first["coverage"]["expected_row_count"], 14)
        self.assertEqual(first["coverage"]["actual_row_count"], 14)
        self.assertEqual(first["coverage"]["successful_row_count"], 14)
        self.assertFalse(first["coverage"]["missing_rows"])
        self.assertEqual({row["method"] for row in first["results"]}, REQUIRED_CANDIDATES)
        selected_ids = {
            row["selected_row_id"]
            for kind in ("fixed_accuracy", "fixed_work")
            for row in first["analyses"][kind]
            if row["selected_row_id"] is not None
        }
        result_ids = {row["row_id"] for row in first["results"]}
        self.assertLessEqual(selected_ids, result_ids)

    def test_observatory_views_are_written(self) -> None:
        report, _ = execute_observatory(
            DEFAULT_MANIFEST,
            selected_cases={"rc_step"},
            quick=True,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixed_accuracy = root / "fixed-accuracy.csv"
            fixed_work = root / "fixed-work.csv"
            plot = root / "accuracy-by-work.svg"
            markdown = root / "report.md"
            write_analysis_csv(fixed_accuracy, report["analyses"]["fixed_accuracy"])
            write_analysis_csv(fixed_work, report["analyses"]["fixed_work"])
            write_accuracy_by_work_svg(plot, report)
            write_markdown_summary(markdown, report)
            self.assertIn("selected_row_id", fixed_accuracy.read_text(encoding="utf-8"))
            self.assertIn("unused_work_budget", fixed_work.read_text(encoding="utf-8"))
            self.assertIn("<svg", plot.read_text(encoding="utf-8"))
            self.assertIn("BAB-CS Method Observatory Report", markdown.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
