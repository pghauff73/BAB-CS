from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from lab.support.verify import EXERCISES, FIXTURE_PATH, LabVerifier


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class TeachingLabTests(unittest.TestCase):
    def test_core_exercises_pass_against_reviewed_fixture(self) -> None:
        exercise_ids = list(EXERCISES[:4])
        verifier = LabVerifier(development=True)
        try:
            report = verifier.run(exercise_ids)
        finally:
            verifier.close()
        expected = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        expected_ids = {exercise["id"] for exercise in expected["exercises"]}
        self.assertEqual({exercise["id"] for exercise in report["exercises"]}, set(exercise_ids))
        self.assertLessEqual(set(exercise_ids), expected_ids)
        self.assertTrue(report["all_passed"])

    def test_full_lab_verifier_includes_packaging_and_equivalence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "verification.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "lab/support/verify.py",
                    "--exercise",
                    "all",
                    "--development",
                    "--output",
                    str(output),
                ],
                cwd=REPOSITORY_ROOT,
                env={**dict(os.environ), "PYTHONPATH": "src"},
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual({item["id"] for item in report["exercises"]}, set(EXERCISES))
            self.assertIn("wheel_hashes_match", completed.stdout)
            equivalence = next(
                item for item in report["exercises"] if item["id"] == "06-source-wheel-equivalence"
            )
            self.assertTrue(equivalence["evidence"]["source_tree_excluded"])

    def test_fixture_update_is_never_implicit(self) -> None:
        before = FIXTURE_PATH.read_bytes()
        subprocess.run(
            [
                sys.executable,
                "lab/support/verify.py",
                "--exercise",
                "01-mna",
                "--development",
            ],
            cwd=REPOSITORY_ROOT,
            env={**dict(os.environ), "PYTHONPATH": "src"},
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(FIXTURE_PATH.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
