from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import zipfile
from email.parser import BytesParser
from pathlib import Path
from typing import Any, Iterable

from babcs import _project


CONTROL_FILES = {
    "RELEASE_MANIFEST.json",
    "RELEASE_MANIFEST_SHA256",
    "SHA256SUMS",
}


class ReleaseEvidenceError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip("\n") + "\n")


def command_output(command: list[str], *, fallback: str = "unavailable") -> str:
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return fallback
    return (completed.stdout or completed.stderr).strip() or fallback


def record_environment(
    output_directory: Path,
    *,
    source_commit: str,
    tag: str,
) -> None:
    validate_source_commit(source_commit)
    validate_tag(tag, _project.VERSION, allow_candidate=True)
    output_directory.mkdir(parents=True, exist_ok=True)
    write_text(output_directory / "SOURCE_COMMIT", source_commit)
    write_text(output_directory / "TAG", tag)
    write_text(output_directory / "PACKAGE_VERSION", _project.VERSION)
    write_text(output_directory / "PYTHON_VERSION", platform.python_version())
    write_text(output_directory / "PYTHON_IMPLEMENTATION", platform.python_implementation())
    write_text(output_directory / "PLATFORM", platform.platform())
    write_text(output_directory / "OPERATING_SYSTEM", command_output(["uname", "-a"]))
    write_text(
        output_directory / "PIP_VERSION",
        command_output([sys.executable, "-m", "pip", "--version"]),
    )
    try:
        import scipy
    except ImportError:
        scipy_version = "unavailable"
    else:
        scipy_version = scipy.__version__
    write_text(output_directory / "SCIPY_VERSION", scipy_version)
    write_text(
        output_directory / "NGSPICE_VERSION",
        command_output(["ngspice", "--version"]),
    )


def validate_source_commit(source_commit: str) -> None:
    if len(source_commit) != 40 or any(character not in "0123456789abcdef" for character in source_commit):
        raise ReleaseEvidenceError("source commit must be a full lowercase 40-character SHA")


def validate_tag(tag: str, version: str, *, allow_candidate: bool = False) -> None:
    expected = f"v{version}"
    if tag == expected:
        return
    if allow_candidate and tag.startswith("candidate-") and len(tag) > len("candidate-"):
        return
    raise ReleaseEvidenceError(f"tag {tag!r} does not match package version {version!r}")


def expected_metadata() -> dict[str, str]:
    return {
        "Name": _project.DISTRIBUTION_NAME,
        "Version": _project.VERSION,
        "Summary": _project.SUMMARY,
        "Requires-Python": _project.REQUIRES_PYTHON,
    }


def inspect_wheel(wheel: Path, repository_root: Path) -> dict[str, Any]:
    if wheel.name != _project.wheel_filename():
        raise ReleaseEvidenceError(
            f"wheel filename {wheel.name!r} does not match {_project.wheel_filename()!r}"
        )
    if not wheel.is_file():
        raise ReleaseEvidenceError(f"wheel does not exist: {wheel}")
    dist_info = _project.dist_info_directory()
    expected_package_members = {
        f"babcs/{path.name}"
        for path in (repository_root / "src" / "babcs").glob("*.py")
        if path.is_file()
    }
    expected_dist_members = {
        f"{dist_info}/METADATA",
        f"{dist_info}/WHEEL",
        f"{dist_info}/entry_points.txt",
        f"{dist_info}/RECORD",
    }
    expected_members = expected_package_members | expected_dist_members
    with zipfile.ZipFile(wheel) as archive:
        information = archive.infolist()
        names = [item.filename for item in information]
        if len(names) != len(set(names)):
            raise ReleaseEvidenceError("wheel contains duplicate archive members")
        if set(names) != expected_members:
            missing = sorted(expected_members - set(names))
            unexpected = sorted(set(names) - expected_members)
            raise ReleaseEvidenceError(
                f"wheel content mismatch; missing={missing!r}, unexpected={unexpected!r}"
            )
        if any(item.date_time != (1980, 1, 1, 0, 0, 0) for item in information):
            raise ReleaseEvidenceError("wheel contains nondeterministic member timestamps")
        if any(item.external_attr >> 16 != 0o100644 for item in information):
            raise ReleaseEvidenceError("wheel contains unexpected member permissions")
        metadata_bytes = archive.read(f"{dist_info}/METADATA")
        metadata = BytesParser().parsebytes(metadata_bytes)
        for field, expected in expected_metadata().items():
            if metadata[field] != expected:
                raise ReleaseEvidenceError(
                    f"wheel METADATA {field}={metadata[field]!r}, expected {expected!r}"
                )
        if metadata.get_all("Provides-Extra") != ["sparse"]:
            raise ReleaseEvidenceError("wheel sparse extra metadata is missing or duplicated")
        if metadata.get_all("Requires-Dist") != [
            f'{_project.SPARSE_REQUIREMENT}; extra == "sparse"'
        ]:
            raise ReleaseEvidenceError("wheel sparse dependency metadata does not match")
        wheel_data = archive.read(f"{dist_info}/WHEEL").decode()
        if f"Tag: {_project.WHEEL_TAG}\n" not in wheel_data:
            raise ReleaseEvidenceError("wheel compatibility tag does not match")
        entry_points = archive.read(f"{dist_info}/entry_points.txt").decode()
        expected_entry_points = f"[console_scripts]\n{_project.CONSOLE_SCRIPT}\n"
        if entry_points != expected_entry_points:
            raise ReleaseEvidenceError("wheel console entry point does not match")
    return {
        "filename": wheel.name,
        "sha256": sha256_file(wheel),
        "size": wheel.stat().st_size,
        "member_count": len(expected_members),
        "dist_info": dist_info,
        "version": _project.VERSION,
    }


def compare_artifacts(pairs: Iterable[tuple[Path, Path]]) -> list[dict[str, Any]]:
    results = []
    for source, installed in pairs:
        if not source.is_file() or not installed.is_file():
            raise ReleaseEvidenceError(
                f"comparison artifact is missing: {source} or {installed}"
            )
        source_hash = sha256_file(source)
        installed_hash = sha256_file(installed)
        if source_hash != installed_hash or source.read_bytes() != installed.read_bytes():
            raise ReleaseEvidenceError(
                f"source and installed artifacts differ: {source} != {installed}"
            )
        results.append(
            {
                "source": source.name,
                "installed": installed.name,
                "sha256": source_hash,
                "size": source.stat().st_size,
            }
        )
    return results


def evidence_role(name: str) -> str:
    if name.endswith(".whl"):
        return "release_wheel"
    if name in {"SOURCE_COMMIT", "TAG", "PACKAGE_VERSION"}:
        return "release_identity"
    if name in {
        "PYTHON_VERSION",
        "PYTHON_IMPLEMENTATION",
        "PLATFORM",
        "OPERATING_SYSTEM",
        "PIP_VERSION",
        "SCIPY_VERSION",
        "NGSPICE_VERSION",
        "INSTALLED_PACKAGE_PATH",
        "INSTALLED_SCIPY_VERSION",
    }:
        return "environment"
    if name in {"WHEEL_SHA256", "WHEEL_CONTENTS"}:
        return "wheel_provenance"
    if name == "wheel-inspection.json":
        return "wheel_inspection"
    if name == "artifact-comparison.json":
        return "artifact_equivalence"
    if name.endswith("tests.log"):
        return "test_log"
    if "wheel-build" in name and name.endswith(".log"):
        return "build_log"
    if name.endswith("comparison.json"):
        return "numerical_report"
    if name.endswith("comparison.csv"):
        return "numerical_table"
    if name.endswith("comparison.svg"):
        return "numerical_plot"
    if name.endswith("comparison.log"):
        return "numerical_log"
    if name.startswith("ngspice-") and name.endswith(".json"):
        return "external_report"
    if name.startswith("ngspice-") and name.endswith(".cir"):
        return "external_netlist"
    if name.startswith("ngspice-") and name.endswith(".dat"):
        return "external_raw"
    if name.startswith("ngspice-") and name.endswith(".log"):
        return "external_log"
    raise ReleaseEvidenceError(f"unrecognized release evidence file: {name}")


def manifest_entries(evidence_directory: Path) -> list[dict[str, Any]]:
    entries = []
    for path in sorted(evidence_directory.iterdir(), key=lambda item: item.name):
        if path.name in CONTROL_FILES:
            continue
        if not path.is_file():
            raise ReleaseEvidenceError(f"release evidence contains a non-file entry: {path.name}")
        entries.append(
            {
                "path": path.name,
                "role": evidence_role(path.name),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return entries


def write_manifest(
    evidence_directory: Path,
    *,
    source_commit: str,
    tag: str,
    wheel_name: str,
    required_files: Iterable[str],
) -> dict[str, Any]:
    validate_source_commit(source_commit)
    validate_tag(tag, _project.VERSION, allow_candidate=True)
    evidence_directory.mkdir(parents=True, exist_ok=True)
    source_file = evidence_directory / "SOURCE_COMMIT"
    tag_file = evidence_directory / "TAG"
    version_file = evidence_directory / "PACKAGE_VERSION"
    if source_file.read_text().strip() != source_commit:
        raise ReleaseEvidenceError("SOURCE_COMMIT does not match manifest source commit")
    if tag_file.read_text().strip() != tag:
        raise ReleaseEvidenceError("TAG does not match manifest tag")
    if version_file.read_text().strip() != _project.VERSION:
        raise ReleaseEvidenceError("PACKAGE_VERSION does not match project version")
    wheel = evidence_directory / wheel_name
    if not wheel.is_file():
        raise ReleaseEvidenceError(f"release wheel is missing: {wheel_name}")
    required = sorted(set(required_files))
    missing = [name for name in required if not (evidence_directory / name).is_file()]
    if missing:
        raise ReleaseEvidenceError(f"required release evidence is missing: {missing!r}")
    entries = manifest_entries(evidence_directory)
    manifest = {
        "schema": "bab-cs-release-evidence-v1",
        "status": "candidate",
        "package": {
            "distribution": _project.DISTRIBUTION_NAME,
            "version": _project.VERSION,
            "tag": tag,
            "source_commit": source_commit,
            "wheel": wheel_name,
            "wheel_sha256": sha256_file(wheel),
        },
        "required_files": required,
        "files": entries,
    }
    payload = json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n"
    manifest_path = evidence_directory / "RELEASE_MANIFEST.json"
    manifest_path.write_text(payload)
    write_text(
        evidence_directory / "RELEASE_MANIFEST_SHA256",
        f"{sha256_file(manifest_path)}  {manifest_path.name}",
    )
    write_checksums(evidence_directory)
    return manifest


def write_checksums(evidence_directory: Path) -> None:
    lines = []
    for path in sorted(evidence_directory.iterdir(), key=lambda item: item.name):
        if path.name == "SHA256SUMS":
            continue
        if not path.is_file():
            raise ReleaseEvidenceError(f"release evidence contains a non-file entry: {path.name}")
        lines.append(f"{sha256_file(path)}  {path.name}")
    write_text(evidence_directory / "SHA256SUMS", "\n".join(lines))


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise ReleaseEvidenceError(f"invalid JSON evidence {path}: {error}") from error
    if not isinstance(data, dict):
        raise ReleaseEvidenceError(f"JSON evidence must be an object: {path}")
    return data


def verify_checksums(evidence_directory: Path) -> None:
    checksum_path = evidence_directory / "SHA256SUMS"
    lines = checksum_path.read_text().splitlines()
    expected_names = sorted(
        path.name
        for path in evidence_directory.iterdir()
        if path.is_file() and path.name != "SHA256SUMS"
    )
    parsed_names = []
    for line in lines:
        digest, separator, name = line.partition("  ")
        if not separator or len(digest) != 64:
            raise ReleaseEvidenceError(f"invalid checksum line: {line!r}")
        path = evidence_directory / name
        if not path.is_file() or sha256_file(path) != digest:
            raise ReleaseEvidenceError(f"checksum mismatch for {name}")
        parsed_names.append(name)
    if parsed_names != expected_names:
        raise ReleaseEvidenceError("SHA256SUMS does not cover every evidence file exactly once")


def verify_manifest(
    evidence_directory: Path,
    *,
    expected_source_commit: str,
    expected_tag: str,
    expected_wheel_sha256: str | None = None,
) -> dict[str, Any]:
    validate_source_commit(expected_source_commit)
    validate_tag(expected_tag, _project.VERSION, allow_candidate=True)
    manifest_path = evidence_directory / "RELEASE_MANIFEST.json"
    manifest = read_json(manifest_path)
    if manifest.get("schema") != "bab-cs-release-evidence-v1":
        raise ReleaseEvidenceError("release manifest schema does not match")
    if manifest.get("status") != "candidate":
        raise ReleaseEvidenceError("release tooling may verify only candidate manifests")
    package = manifest.get("package")
    if not isinstance(package, dict):
        raise ReleaseEvidenceError("release manifest package section is missing")
    expected_package = {
        "distribution": _project.DISTRIBUTION_NAME,
        "version": _project.VERSION,
        "tag": expected_tag,
        "source_commit": expected_source_commit,
    }
    for field, expected in expected_package.items():
        if package.get(field) != expected:
            raise ReleaseEvidenceError(
                f"release manifest package {field}={package.get(field)!r}, expected {expected!r}"
            )
    wheel_name = package.get("wheel")
    wheel_sha256 = package.get("wheel_sha256")
    if wheel_name != _project.wheel_filename():
        raise ReleaseEvidenceError("release manifest wheel name does not match package version")
    if expected_wheel_sha256 is not None and wheel_sha256 != expected_wheel_sha256:
        raise ReleaseEvidenceError("release manifest wheel hash does not match approval input")
    if sha256_file(evidence_directory / wheel_name) != wheel_sha256:
        raise ReleaseEvidenceError("release wheel hash does not match manifest")
    files = manifest.get("files")
    if not isinstance(files, list):
        raise ReleaseEvidenceError("release manifest files list is missing")
    listed = []
    for entry in files:
        if not isinstance(entry, dict):
            raise ReleaseEvidenceError("release manifest contains a non-object file entry")
        name = entry.get("path")
        if not isinstance(name, str) or name in listed or name in CONTROL_FILES:
            raise ReleaseEvidenceError("release manifest contains an invalid or duplicate path")
        path = evidence_directory / name
        if not path.is_file():
            raise ReleaseEvidenceError(f"manifest evidence is missing: {name}")
        if entry.get("role") != evidence_role(name):
            raise ReleaseEvidenceError(f"manifest evidence role does not match: {name}")
        if entry.get("size") != path.stat().st_size or entry.get("sha256") != sha256_file(path):
            raise ReleaseEvidenceError(f"manifest evidence digest or size does not match: {name}")
        listed.append(name)
    actual = sorted(
        path.name
        for path in evidence_directory.iterdir()
        if path.is_file() and path.name not in CONTROL_FILES
    )
    if sorted(listed) != actual:
        raise ReleaseEvidenceError("release manifest does not list every evidence file exactly once")
    required = manifest.get("required_files")
    if not isinstance(required, list) or any(not isinstance(name, str) for name in required):
        raise ReleaseEvidenceError("release manifest required_files is invalid")
    missing = [name for name in required if name not in listed]
    if missing:
        raise ReleaseEvidenceError(f"required manifest evidence is unlisted: {missing!r}")
    manifest_hash_line = (evidence_directory / "RELEASE_MANIFEST_SHA256").read_text().strip()
    expected_manifest_hash_line = f"{sha256_file(manifest_path)}  {manifest_path.name}"
    if manifest_hash_line != expected_manifest_hash_line:
        raise ReleaseEvidenceError("release manifest hash record does not match")
    verify_checksums(evidence_directory)
    return manifest


def parse_pairs(values: Iterable[str]) -> list[tuple[Path, Path]]:
    pairs = []
    for value in values:
        source, separator, installed = value.partition("=")
        if not separator or not source or not installed:
            raise ReleaseEvidenceError(f"artifact pair must be SOURCE=INSTALLED: {value!r}")
        pairs.append((Path(source), Path(installed)))
    if not pairs:
        raise ReleaseEvidenceError("at least one artifact pair is required")
    return pairs


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and verify BAB-CS release evidence")
    subparsers = parser.add_subparsers(dest="command", required=True)

    environment = subparsers.add_parser("record-environment")
    environment.add_argument("--output-dir", required=True)
    environment.add_argument("--source-commit", required=True)
    environment.add_argument("--tag", required=True)

    wheel = subparsers.add_parser("inspect-wheel")
    wheel.add_argument("--wheel", required=True)
    wheel.add_argument("--repository-root", default=".")
    wheel.add_argument("--output", required=True)

    compare = subparsers.add_parser("compare-artifacts")
    compare.add_argument("--pair", action="append", required=True)
    compare.add_argument("--output", required=True)

    manifest = subparsers.add_parser("write-manifest")
    manifest.add_argument("--evidence-dir", required=True)
    manifest.add_argument("--source-commit", required=True)
    manifest.add_argument("--tag", required=True)
    manifest.add_argument("--wheel", required=True)
    manifest.add_argument("--require", action="append", default=[])

    verify = subparsers.add_parser("verify")
    verify.add_argument("--evidence-dir", required=True)
    verify.add_argument("--source-commit", required=True)
    verify.add_argument("--tag", required=True)
    verify.add_argument("--wheel-sha256")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        if arguments.command == "record-environment":
            record_environment(
                Path(arguments.output_dir),
                source_commit=arguments.source_commit,
                tag=arguments.tag,
            )
        elif arguments.command == "inspect-wheel":
            write_json(
                Path(arguments.output),
                inspect_wheel(Path(arguments.wheel), Path(arguments.repository_root)),
            )
        elif arguments.command == "compare-artifacts":
            write_json(
                Path(arguments.output),
                {"artifacts": compare_artifacts(parse_pairs(arguments.pair))},
            )
        elif arguments.command == "write-manifest":
            write_manifest(
                Path(arguments.evidence_dir),
                source_commit=arguments.source_commit,
                tag=arguments.tag,
                wheel_name=arguments.wheel,
                required_files=arguments.require,
            )
        else:
            verify_manifest(
                Path(arguments.evidence_dir),
                expected_source_commit=arguments.source_commit,
                expected_tag=arguments.tag,
                expected_wheel_sha256=arguments.wheel_sha256,
            )
    except (ReleaseEvidenceError, OSError, zipfile.BadZipFile) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
