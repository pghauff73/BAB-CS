from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.bound_coverage_atlas import (
    execute_bound_atlas,
    write_atlas_plots,
    write_sample_csv,
)
from tools.method_observatory import DEFAULT_MANIFEST, execute_observatory


class BoundCoverageAtlasTests(unittest.TestCase):
    def test_quick_rc_atlas_reconciles_and_is_deterministic(self) -> None:
        observatory, _ = execute_observatory(
            DEFAULT_MANIFEST,
            selected_cases={"rc_step"},
            quick=True,
        )
        first = execute_bound_atlas(
            observatory,
            observatory_manifest_path=DEFAULT_MANIFEST,
        )
        second = execute_bound_atlas(
            observatory,
            observatory_manifest_path=DEFAULT_MANIFEST,
        )
        self.assertEqual(
            json.dumps(first, sort_keys=True, allow_nan=False),
            json.dumps(second, sort_keys=True, allow_nan=False),
        )
        self.assertEqual(len(first["aggregates"]), 14)
        self.assertEqual(
            first["sample_count"],
            sum(row["diagnostics"]["accepted_steps"] for row in observatory["results"]),
        )
        self.assertTrue(first["anchors"])
        self.assertTrue(
            all("actual_authority_error" in sample for sample in first["samples"])
        )
        self.assertTrue(
            all("recursive_internal_bound" in sample for sample in first["samples"])
        )
        self.assertTrue(
            all(
                aggregate["empirical_coverage_fraction"] is None
                or 0.0 <= aggregate["empirical_coverage_fraction"] <= 1.0
                for aggregate in first["aggregates"]
            )
        )

    def test_atlas_csv_and_plots_are_written(self) -> None:
        observatory, _ = execute_observatory(
            DEFAULT_MANIFEST,
            selected_cases={"rc_step"},
            quick=True,
        )
        atlas = execute_bound_atlas(
            observatory,
            observatory_manifest_path=DEFAULT_MANIFEST,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "samples.csv"
            plots = root / "plots"
            write_sample_csv(csv_path, atlas)
            write_atlas_plots(plots, atlas)
            self.assertIn("actual_authority_error", csv_path.read_text(encoding="utf-8"))
            self.assertEqual(len(list(plots.glob("*.svg"))), 4)


if __name__ == "__main__":
    unittest.main()
