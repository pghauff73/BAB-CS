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
TAG = f"v{_project.VERSION}"


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
        release_evidence.write_text(evidence / "SOURCE_COMMIT", SOURCE_COMMIT)
        release_evidence.write_text(evidence / "TAG", TAG)
        release_evidence.write_text(evidence / "PACKAGE_VERSION", _project.VERSION)
        release_evidence.write_text(evidence / "PYTHON_VERSION", "3.14.0")
        release_evidence.write_text(evidence / "source-tests.log", "Ran 174 tests\nOK")
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
