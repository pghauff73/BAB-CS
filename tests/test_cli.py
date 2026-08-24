from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from babcs.cli import main


class CommandLineTests(unittest.TestCase):
    def test_json_case_writes_csv_and_summary(self) -> None:
        case = {
            "elements": [
                {
                    "type": "voltage_source",
                    "name": "V1",
                    "positive": "vin",
                    "negative": "0",
                    "waveform": 1.0,
                },
                {
                    "type": "resistor",
                    "name": "R1",
                    "positive": "vin",
                    "negative": "out",
                    "resistance": 1000.0,
                },
                {
                    "type": "capacitor",
                    "name": "C1",
                    "positive": "out",
                    "negative": "0",
                    "capacitance": 1.0e-6,
                },
            ],
            "simulation": {"stop_time": 5.0e-5, "nominal_step": 1.0e-5},
            "babcs": {"rollout_mode": "shadow", "predictor_reference_cap": 100.0},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "case.json"
            csv_path = root / "trace.csv"
            summary_path = root / "summary.json"
            input_path.write_text(json.dumps(case), encoding="utf-8")
            with redirect_stdout(StringIO()):
                exit_code = main(
                    [
                        "simulate",
                        str(input_path),
                        "--csv",
                        str(csv_path),
                        "--summary",
                        str(summary_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            csv_header = csv_path.read_text(encoding="utf-8").splitlines()[0]
            self.assertIn("voltage:out", csv_header)
            self.assertIn("history_reset_reason", csv_header)
            self.assertIn("reference_circuit_evaluations", csv_header)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertGreater(summary["accepted_steps"], 0)
            self.assertGreater(summary["ab_steps"], 0)
            self.assertGreater(summary["reference_solves"], 0)
            self.assertGreater(summary["reference_circuit_evaluations"], 0)
            self.assertIn("maximum_anchor_reference_error", summary)
            self.assertIn("rejection_reasons", summary)

    def test_candidate_and_fast_path_overrides_are_exposed(self) -> None:
        case = {
            "elements": [
                {
                    "type": "voltage_source",
                    "name": "V1",
                    "positive": "vin",
                    "negative": "0",
                    "waveform": 1.0,
                },
                {
                    "type": "resistor",
                    "name": "R1",
                    "positive": "vin",
                    "negative": "out",
                    "resistance": 1000.0,
                },
                {
                    "type": "capacitor",
                    "name": "C1",
                    "positive": "out",
                    "negative": "0",
                    "capacitance": 1.0e-6,
                },
            ],
            "simulation": {"stop_time": 2.0e-4, "nominal_step": 1.0e-5},
            "babcs": {"rollout_mode": "shadow", "predictor_reference_cap": 1.0e9},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "case.json"
            summary_path = root / "summary.json"
            input_path.write_text(json.dumps(case), encoding="utf-8")
            with redirect_stdout(StringIO()):
                exit_code = main(
                    [
                        "simulate",
                        str(input_path),
                        "--mode",
                        "active",
                        "--candidate",
                        "rk23",
                        "--linear-backend",
                        "auto",
                        "--reference-interval",
                        "4",
                        "--bound-cap",
                        "100",
                        "--summary",
                        str(summary_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["linear_backend"], "auto")
            self.assertGreater(summary["candidate_steps"], 0)
            self.assertLess(summary["reference_solves"], summary["candidate_steps"])


if __name__ == "__main__":
    unittest.main()
