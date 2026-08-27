from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.experiment_records import (
    analyze_experiment_records,
    canonical_row_id,
    classify_reason,
    validate_experiment_record,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ExperimentRecordTests(unittest.TestCase):
    def test_checked_in_fixture_is_valid(self) -> None:
        fixture = json.loads(
            (REPOSITORY_ROOT / "tests/fixtures/experiment-record-v1.json").read_text(
                encoding="utf-8"
            )
        )
        validate_experiment_record(fixture)

    def test_row_identity_is_order_independent_and_semantic(self) -> None:
        common = {
            "case_id": "rc",
            "method": "bounded_heun",
            "nominal_step": 1.0e-4,
            "anchor_interval": 16,
        }
        first = canonical_row_id(
            **common,
            configuration={"candidate": "heun", "limits": {"b": 2, "a": 1}},
        )
        second = canonical_row_id(
            **common,
            configuration={"limits": {"a": 1, "b": 2}, "candidate": "heun"},
        )
        changed = canonical_row_id(
            **common,
            configuration={"candidate": "rk23", "limits": {"a": 1, "b": 2}},
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)

    def test_reason_taxonomy_is_stable(self) -> None:
        self.assertEqual(
            classify_reason("independent re-anchor full residual cap exceeded"),
            "full_residual_cap",
        )
        self.assertEqual(
            classify_reason("energy-injection cap exceeded"),
            "energy_injection_cap",
        )
        self.assertEqual(classify_reason("unrecognized condition"), "unknown")

    def test_selectors_use_measured_rows_and_stable_tie_breaks(self) -> None:
        records = [
            self._record("coarse", 2.0e-4, 0.01, 0.008, 80),
            self._record("balanced", 1.0e-4, 0.001, 0.0008, 100),
            self._record("fine", 5.0e-5, 0.0001, 0.00008, 160),
        ]
        analyses = analyze_experiment_records(
            records,
            accuracy_targets=[0.001],
            work_budgets=[100],
        )
        fixed_accuracy = analyses["fixed_accuracy"][0]
        fixed_work = analyses["fixed_work"][0]
        self.assertEqual(fixed_accuracy["selected_row_id"], records[1]["row_id"])
        self.assertEqual(fixed_work["selected_row_id"], records[1]["row_id"])
        self.assertEqual(fixed_work["unused_work_budget"], 0)

    @staticmethod
    def _record(
        row_id: str,
        step: float,
        maximum_error: float,
        rms_error: float,
        work: int,
    ) -> dict[str, object]:
        return {
            "schema_version": 1,
            "row_id": f"exp-{row_id.encode().hex():0<24}"[:28],
            "case_id": "rc",
            "method": "bounded_heun",
            "nominal_step": step,
            "anchor_interval": 16,
            "authority": {"type": "analytic"},
            "configuration": {"candidate_method": "heun"},
            "accuracy": {
                "maximum_absolute_error": maximum_error,
                "rms_absolute_error": rms_error,
            },
            "bound": {"authority": "internal_reference_and_independent_replay"},
            "diagnostics": {"rejection_reasons": {}},
            "work": {"deterministic_work_units": work},
            "oscillator": None,
            "status": "success",
            "reason_codes": [],
            "applicability": {},
        }


if __name__ == "__main__":
    unittest.main()
