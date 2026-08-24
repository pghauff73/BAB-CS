from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import build_backend
from babcs import _project
from tools import release_evidence


SOURCE_COMMIT = "0123456789abcdef0123456789abcdef01234567"
TAG = f"candidate-{SOURCE_COMMIT[:12]}"
CREATED_UTC = "2026-08-24T03:04:05Z"


class ReleaseEvidenceTests(unittest.TestCase):
    def build_wheel(self, directory: Path) -> Path:
        wheel_directory = directory / "wheel-build"
        wheel_directory.mkdir()
        return wheel_directory / build_backend.build_wheel(str(wheel_directory))

    def create_evidence(self, directory: Path) -> tuple[Path, Path]:
        evidence = directory / "evidence"
        evidence.mkdir()
        wheel = self.build_wheel(directory)
        retained_wheel = evidence / wheel.name
        shutil.copyfile(wheel, retained_wheel)
        release_evidence.record_environment(
            evidence,
            source_commit=SOURCE_COMMIT,
            tag=TAG,
            created_utc=CREATED_UTC,
            workflow_run_id="123456",
            workflow_run_url_value="https://example.invalid/actions/runs/123456",
            workflow_event="workflow_dispatch",
            workflow_ref="refs/heads/main",
            workflow_sha=SOURCE_COMMIT,
        )
        release_evidence.write_text(
            evidence / "source-tests.log",
            "Ran 186 tests in 46.424s\n\nOK",
        )
        release_evidence.write_json(
            evidence / "source-comparison.json",
            {
                "analyses": {"convergence": []},
                "cases": [{"id": "rc_step"}],
                "results": [{"case_id": "rc_step", "method": "active"}],
            },
        )
        release_evidence.write_json(
            evidence / "source-timing.json",
            {
                "timing_repeats": 3,
                "results": [{"case_id": "rc_step", "method": "active"}],
            },
        )
        inspection = release_evidence.inspect_wheel(retained_wheel, Path.cwd())
        release_evidence.write_json(evidence / "wheel-inspection.json", inspection)
        return evidence, retained_wheel

    def test_wheel_inspection_validates_identity_and_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wheel = self.build_wheel(root)
            inspection = release_evidence.inspect_wheel(wheel, Path.cwd())
            self.assertEqual(inspection["filename"], _project.wheel_filename())
            self.assertEqual(inspection["version"], _project.VERSION)
            self.assertEqual(len(inspection["sha256"]), 64)

    def test_wheel_inspection_rejects_wrong_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wheel = self.build_wheel(root)
            wrong = wheel.with_name("bab_cs-9.9.9-py3-none-any.whl")
            wheel.rename(wrong)
            with self.assertRaisesRegex(
                release_evidence.ReleaseEvidenceError,
                "wheel filename",
            ):
                release_evidence.inspect_wheel(wrong, Path.cwd())

    def test_artifact_comparison_requires_byte_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.json"
            installed = root / "installed.json"
            source.write_text('{"value": 1}\n')
            installed.write_bytes(source.read_bytes())
            results = release_evidence.compare_artifacts([(source, installed)])
            self.assertEqual(results[0]["sha256"], release_evidence.sha256_file(source))
            installed.write_text('{"value": 2}\n')
            with self.assertRaisesRegex(
                release_evidence.ReleaseEvidenceError,
                "artifacts differ",
            ):
                release_evidence.compare_artifacts([(source, installed)])

    def test_comparison_inspection_requires_complete_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = root / "manifest.json"
            report_path = root / "comparison.json"
            timing_path = root / "timing.json"
            release_evidence.write_json(
                manifest_path,
                {
                    "cases": [
                        {
                            "id": "case",
                            "methods": ["active", "trapezoidal"],
                            "nominal_steps": [0.1, 0.05],
                            "anchor_intervals": [4, 8],
                        }
                    ]
                },
            )
            keys = sorted(release_evidence.expected_comparison_keys(manifest_path))
            source = {
                "commit": SOURCE_COMMIT,
                "dirty": False,
                "source_tree_sha256": "f" * 64,
            }
            results = [
                {
                    "case_id": case_id,
                    "method": method,
                    "nominal_step": nominal_step,
                    "anchor_interval": anchor_interval,
                }
                for case_id, method, nominal_step, anchor_interval in keys
            ]
            release_evidence.write_json(
                report_path,
                {
                    "manifest_sha256": release_evidence.sha256_file(manifest_path),
                    "runner": {"quick": False},
                    "source": source,
                    "cases": [{"id": "case"}],
                    "results": results,
                    "analyses": {
                        "convergence": [],
                        "fixed_accuracy": [],
                        "fixed_work": [],
                    },
                },
            )
            release_evidence.write_json(
                timing_path,
                {
                    "source": source,
                    "timing_repeats": 3,
                    "results": results,
                },
            )
            inspection = release_evidence.inspect_comparison(
                report_path,
                manifest_path,
                expected_source_commit=SOURCE_COMMIT,
                timing_path=timing_path,
            )
            self.assertEqual(inspection["result_count"], 6)
            report = json.loads(report_path.read_text())
            report["results"].pop()
            release_evidence.write_json(report_path, report)
            with self.assertRaisesRegex(
                release_evidence.ReleaseEvidenceError,
                "comparison matrix mismatch",
            ):
                release_evidence.inspect_comparison(
                    report_path,
                    manifest_path,
                    expected_source_commit=SOURCE_COMMIT,
                )

    def test_manifest_is_deterministic_and_verifiable(self) -> None:
        manifests = []
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            for temporary in (first, second):
                evidence, wheel = self.create_evidence(Path(temporary))
                manifest = release_evidence.write_manifest(
                    evidence,
                    source_commit=SOURCE_COMMIT,
                    tag=TAG,
                    wheel_name=wheel.name,
                    required_files=(wheel.name, "source-tests.log", "wheel-inspection.json"),
                )
                verified = release_evidence.verify_manifest(
                    evidence,
                    expected_source_commit=SOURCE_COMMIT,
                    expected_tag=TAG,
                    expected_wheel_sha256=release_evidence.sha256_file(wheel),
                )
                self.assertEqual(verified, manifest)
                self.assertEqual(manifest["qualification"]["created_utc"], CREATED_UTC)
                self.assertEqual(manifest["workflow"]["sha"], SOURCE_COMMIT)
                self.assertEqual(manifest["tests"][0]["tests"], 186)
                self.assertEqual(manifest["tests"][0]["skipped"], 0)
                self.assertEqual(
                    [summary["kind"] for summary in manifest["comparisons"]],
                    ["numerical", "timing"],
                )
                manifests.append((evidence / "RELEASE_MANIFEST.json").read_bytes())
            self.assertEqual(manifests[0], manifests[1])

    def test_manifest_rejects_missing_required_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, wheel = self.create_evidence(Path(temporary))
            with self.assertRaisesRegex(
                release_evidence.ReleaseEvidenceError,
                "required release evidence is missing",
            ):
                release_evidence.write_manifest(
                    evidence,
                    source_commit=SOURCE_COMMIT,
                    tag=TAG,
                    wheel_name=wheel.name,
                    required_files=("missing.log",),
                )

    def test_manifest_rejects_duplicate_required_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, wheel = self.create_evidence(Path(temporary))
            with self.assertRaisesRegex(
                release_evidence.ReleaseEvidenceError,
                "duplicate paths",
            ):
                release_evidence.write_manifest(
                    evidence,
                    source_commit=SOURCE_COMMIT,
                    tag=TAG,
                    wheel_name=wheel.name,
                    required_files=("source-tests.log", "source-tests.log"),
                )

    def test_required_evidence_profile_is_complete_and_recognized(self) -> None:
        required = release_evidence.load_required_files(
            Path("release-evidence-required.txt"),
            wheel_name=_project.wheel_filename(),
        )
        self.assertIn(_project.wheel_filename(), required)
        self.assertTrue(release_evidence.CORE_EVIDENCE_FILES.issubset(required))
        self.assertIn("comparison-inspection.json", required)
        self.assertIn("source-timing.json", required)
        for name in required:
            release_evidence.evidence_role(name)

    def test_manifest_rejects_unrecognized_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, wheel = self.create_evidence(Path(temporary))
            (evidence / "unreviewed.txt").write_text("unexpected\n")
            with self.assertRaisesRegex(
                release_evidence.ReleaseEvidenceError,
                "unrecognized release evidence file",
            ):
                release_evidence.write_manifest(
                    evidence,
                    source_commit=SOURCE_COMMIT,
                    tag=TAG,
                    wheel_name=wheel.name,
                    required_files=(),
                )
            release_evidence.write_text(
                evidence / "source-tests.log",
                "Ran 186 tests in 46.424s\n\nOK",
            )
            release_evidence.write_text(
                evidence / "WORKFLOW_SHA",
                "abcdef0123456789abcdef0123456789abcdef01",
            )
            with self.assertRaisesRegex(
                release_evidence.ReleaseEvidenceError,
                "workflow SHA does not match",
            ):
                release_evidence.write_manifest(
                    evidence,
                    source_commit=SOURCE_COMMIT,
                    tag=TAG,
                    wheel_name=wheel.name,
                    required_files=(),
                )

    def test_manifest_verification_rejects_modified_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, wheel = self.create_evidence(Path(temporary))
            release_evidence.write_manifest(
                evidence,
                source_commit=SOURCE_COMMIT,
                tag=TAG,
                wheel_name=wheel.name,
                required_files=("source-tests.log",),
            )
            (evidence / "source-tests.log").write_text("modified\n")
            with self.assertRaisesRegex(
                release_evidence.ReleaseEvidenceError,
                "digest or size does not match",
            ):
                release_evidence.verify_manifest(
                    evidence,
                    expected_source_commit=SOURCE_COMMIT,
                    expected_tag=TAG,
                )

    def test_manifest_verification_rejects_unlisted_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, wheel = self.create_evidence(Path(temporary))
            release_evidence.write_manifest(
                evidence,
                source_commit=SOURCE_COMMIT,
                tag=TAG,
                wheel_name=wheel.name,
                required_files=(),
            )
            release_evidence.write_text(evidence / "installed-wheel-tests.log", "OK")
            release_evidence.write_checksums(evidence)
            with self.assertRaisesRegex(
                release_evidence.ReleaseEvidenceError,
                "does not list every evidence file",
            ):
                release_evidence.verify_manifest(
                    evidence,
                    expected_source_commit=SOURCE_COMMIT,
                    expected_tag=TAG,
                )

    def test_manifest_json_rejects_nonfinite_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.json"
            path.write_text('{"value": NaN}\n')
            with self.assertRaisesRegex(
                release_evidence.ReleaseEvidenceError,
                "invalid JSON evidence",
            ):
                release_evidence.read_json(path)

    def test_release_identity_rejects_short_sha_and_wrong_tag(self) -> None:
        with self.assertRaisesRegex(
            release_evidence.ReleaseEvidenceError,
            "full lowercase 40-character SHA",
        ):
            release_evidence.validate_source_commit("0123456")
        with self.assertRaisesRegex(
            release_evidence.ReleaseEvidenceError,
            "does not match package version",
        ):
            release_evidence.validate_tag("v9.9.9", _project.VERSION)
        with self.assertRaisesRegex(
            release_evidence.ReleaseEvidenceError,
            "candidate tag does not match",
        ):
            release_evidence.validate_release_identity(
                SOURCE_COMMIT,
                "candidate-deadbeefdead",
                allow_candidate=True,
            )

    def test_manifest_rejects_failed_test_log_and_mismatched_workflow_sha(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, wheel = self.create_evidence(Path(temporary))
            release_evidence.write_text(
                evidence / "source-tests.log",
                "Ran 186 tests in 46.424s\n\nFAILED (failures=1)",
            )
            with self.assertRaisesRegex(
                release_evidence.ReleaseEvidenceError,
                "successful unittest summary",
            ):
                release_evidence.write_manifest(
                    evidence,
                    source_commit=SOURCE_COMMIT,
                    tag=TAG,
                    wheel_name=wheel.name,
                    required_files=(),
                )

    def test_release_tag_manifest_requires_exact_tag_workflow_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, wheel = self.create_evidence(Path(temporary))
            release_evidence.write_text(evidence / "TAG", f"v{_project.VERSION}")
            with self.assertRaisesRegex(
                release_evidence.ReleaseEvidenceError,
                "exact tag push",
            ):
                release_evidence.write_manifest(
                    evidence,
                    source_commit=SOURCE_COMMIT,
                    tag=f"v{_project.VERSION}",
                    wheel_name=wheel.name,
                    required_files=(),
                )
            release_evidence.write_text(evidence / "WORKFLOW_EVENT", "push")
            release_evidence.write_text(
                evidence / "WORKFLOW_REF",
                f"refs/tags/v{_project.VERSION}",
            )
            manifest = release_evidence.write_manifest(
                evidence,
                source_commit=SOURCE_COMMIT,
                tag=f"v{_project.VERSION}",
                wheel_name=wheel.name,
                required_files=(),
            )
            self.assertEqual(manifest["workflow"]["event"], "push")

    def test_checksums_are_sorted_and_do_not_include_themselves(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, _ = self.create_evidence(Path(temporary))
            release_evidence.write_checksums(evidence)
            lines = (evidence / "SHA256SUMS").read_text().splitlines()
            names = [line.partition("  ")[2] for line in lines]
            self.assertEqual(names, sorted(names))
            self.assertNotIn("SHA256SUMS", names)
            release_evidence.verify_checksums(evidence)


if __name__ == "__main__":
    unittest.main()
