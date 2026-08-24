from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from email.parser import BytesParser
from pathlib import Path
from typing import Any, Iterable

from babcs import _project


CONTROL_FILES = {
    "RELEASE_MANIFEST.json",
    "RELEASE_MANIFEST_SHA256",
    "SHA256SUMS",
}
CORE_EVIDENCE_FILES = {
    "SOURCE_COMMIT",
    "TAG",
    "PACKAGE_VERSION",
    "PYTHON_VERSION",
    "PYTHON_IMPLEMENTATION",
    "PLATFORM",
    "OPERATING_SYSTEM",
    "PIP_VERSION",
    "SCIPY_VERSION",
    "NGSPICE_VERSION",
    "QUALIFICATION_CREATED_UTC",
    "WORKFLOW_RUN_ID",
    "WORKFLOW_RUN_URL",
    "WORKFLOW_EVENT",
    "WORKFLOW_REF",
    "WORKFLOW_SHA",
}
ENVIRONMENT_FIELDS = {
    "python_version": "PYTHON_VERSION",
    "python_implementation": "PYTHON_IMPLEMENTATION",
    "platform": "PLATFORM",
    "operating_system": "OPERATING_SYSTEM",
    "pip_version": "PIP_VERSION",
    "scipy_version": "SCIPY_VERSION",
    "ngspice_version": "NGSPICE_VERSION",
}
WORKFLOW_FIELDS = {
    "run_id": "WORKFLOW_RUN_ID",
    "run_url": "WORKFLOW_RUN_URL",
    "event": "WORKFLOW_EVENT",
    "ref": "WORKFLOW_REF",
    "sha": "WORKFLOW_SHA",
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


def normalize_utc_timestamp(value: str | None) -> str:
    if value is None:
        instant = datetime.now(timezone.utc).replace(microsecond=0)
    else:
        try:
            instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ReleaseEvidenceError(f"invalid UTC qualification timestamp: {value!r}") from error
        if instant.tzinfo is None:
            raise ReleaseEvidenceError("qualification timestamp must include a UTC offset")
        instant = instant.astimezone(timezone.utc).replace(microsecond=0)
    return instant.isoformat().replace("+00:00", "Z")


def workflow_run_url() -> str:
    server = os.environ.get("GITHUB_SERVER_URL")
    repository = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if server and repository and run_id:
        return f"{server}/{repository}/actions/runs/{run_id}"
    return "unavailable"


def record_environment(
    output_directory: Path,
    *,
    source_commit: str,
    tag: str,
    created_utc: str | None = None,
    workflow_run_id: str | None = None,
    workflow_run_url_value: str | None = None,
    workflow_event: str | None = None,
    workflow_ref: str | None = None,
    workflow_sha: str | None = None,
) -> None:
    validate_release_identity(source_commit, tag, allow_candidate=True)
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
    write_text(
        output_directory / "QUALIFICATION_CREATED_UTC",
        normalize_utc_timestamp(created_utc),
    )
    write_text(
        output_directory / "WORKFLOW_RUN_ID",
        workflow_run_id or os.environ.get("GITHUB_RUN_ID") or "unavailable",
    )
    write_text(
        output_directory / "WORKFLOW_RUN_URL",
        workflow_run_url_value or workflow_run_url(),
    )
    write_text(
        output_directory / "WORKFLOW_EVENT",
        workflow_event or os.environ.get("GITHUB_EVENT_NAME") or "unavailable",
    )
    write_text(
        output_directory / "WORKFLOW_REF",
        workflow_ref or os.environ.get("GITHUB_REF") or "unavailable",
    )
    write_text(
        output_directory / "WORKFLOW_SHA",
        workflow_sha or os.environ.get("GITHUB_SHA") or "unavailable",
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


def validate_release_identity(
    source_commit: str,
    tag: str,
    *,
    allow_candidate: bool = False,
) -> None:
    validate_source_commit(source_commit)
    validate_tag(tag, _project.VERSION, allow_candidate=allow_candidate)
    if tag.startswith("candidate-") and tag != f"candidate-{source_commit[:12]}":
        raise ReleaseEvidenceError("candidate tag does not match the source commit prefix")


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
    if name == "QUALIFICATION_CREATED_UTC":
        return "qualification_time"
    if name in WORKFLOW_FIELDS.values():
        return "workflow_identity"
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
    if name == "comparison-inspection.json":
        return "comparison_inspection"
    if name.endswith("tests.log"):
        return "test_log"
    if name.endswith("install.log"):
        return "installation_log"
    if name == "compile.log":
        return "build_log"
    if "wheel-build" in name and name.endswith(".log"):
        return "build_log"
    if name.endswith("timing.json"):
        return "timing_report"
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


def read_text_evidence(evidence_directory: Path, name: str) -> str:
    value = (evidence_directory / name).read_text().strip()
    if not value:
        raise ReleaseEvidenceError(f"release evidence is empty: {name}")
    return value


def parse_test_log(path: Path) -> dict[str, Any]:
    content = path.read_text(errors="replace")
    run_matches = re.findall(r"^Ran (\d+) tests? in ([0-9]+(?:\.[0-9]+)?)s\s*$", content, re.MULTILINE)
    outcome_matches = re.findall(r"^OK(?: \(([^)]*)\))?\s*$", content, re.MULTILINE)
    if len(run_matches) != 1 or len(outcome_matches) != 1:
        raise ReleaseEvidenceError(f"test log lacks one successful unittest summary: {path.name}")
    test_count, elapsed_seconds = run_matches[0]
    details = outcome_matches[0]
    skipped_match = re.search(r"skipped=(\d+)", details)
    return {
        "path": path.name,
        "outcome": "passed",
        "tests": int(test_count),
        "skipped": int(skipped_match.group(1)) if skipped_match else 0,
        "elapsed_seconds": float(elapsed_seconds),
    }


def comparison_summary(path: Path, *, timing: bool = False) -> dict[str, Any]:
    report = read_json(path)
    results = report.get("results")
    if not isinstance(results, list) or not results:
        raise ReleaseEvidenceError(f"comparison report has no results: {path.name}")
    if timing:
        repeats = report.get("timing_repeats")
        if not isinstance(repeats, int) or repeats < 1:
            raise ReleaseEvidenceError(f"timing report has invalid repeat count: {path.name}")
        return {
            "path": path.name,
            "kind": "timing",
            "result_count": len(results),
            "timing_repeats": repeats,
        }
    cases = report.get("cases")
    analyses = report.get("analyses")
    if not isinstance(cases, list) or not cases or not isinstance(analyses, dict):
        raise ReleaseEvidenceError(f"numerical comparison report is incomplete: {path.name}")
    return {
        "path": path.name,
        "kind": "numerical",
        "case_count": len(cases),
        "result_count": len(results),
    }


def comparison_result_key(result: object, *, path: Path) -> tuple[str, str, float, int | None]:
    if not isinstance(result, dict):
        raise ReleaseEvidenceError(f"comparison result is not an object: {path.name}")
    case_id = result.get("case_id")
    method = result.get("method")
    nominal_step = result.get("nominal_step")
    anchor_interval = result.get("anchor_interval")
    if not isinstance(case_id, str) or not isinstance(method, str):
        raise ReleaseEvidenceError(f"comparison result identity is invalid: {path.name}")
    if not isinstance(nominal_step, (int, float)) or isinstance(nominal_step, bool):
        raise ReleaseEvidenceError(f"comparison result step is invalid: {path.name}")
    if anchor_interval is not None and (
        not isinstance(anchor_interval, int) or isinstance(anchor_interval, bool)
    ):
        raise ReleaseEvidenceError(f"comparison result anchor interval is invalid: {path.name}")
    return case_id, method, float(nominal_step), anchor_interval


def expected_comparison_keys(manifest_path: Path) -> set[tuple[str, str, float, int | None]]:
    manifest = read_json(manifest_path)
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ReleaseEvidenceError("comparison manifest has no cases")
    expected: set[tuple[str, str, float, int | None]] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ReleaseEvidenceError("comparison manifest contains a non-object case")
        case_id = case.get("id")
        methods = case.get("methods")
        nominal_steps = case.get("nominal_steps")
        anchor_intervals = case.get("anchor_intervals")
        if (
            not isinstance(case_id, str)
            or not isinstance(methods, list)
            or not methods
            or not isinstance(nominal_steps, list)
            or not nominal_steps
            or not isinstance(anchor_intervals, list)
            or not anchor_intervals
        ):
            raise ReleaseEvidenceError(f"comparison manifest case is incomplete: {case_id!r}")
        for method in methods:
            if not isinstance(method, str):
                raise ReleaseEvidenceError(f"comparison manifest method is invalid: {case_id}")
            intervals: list[int | None] = anchor_intervals if method in {"active", "shadow"} else [None]
            for anchor_interval in intervals:
                if anchor_interval is not None and (
                    not isinstance(anchor_interval, int) or isinstance(anchor_interval, bool)
                ):
                    raise ReleaseEvidenceError(
                        f"comparison manifest anchor interval is invalid: {case_id}"
                    )
                for nominal_step in nominal_steps:
                    if not isinstance(nominal_step, (int, float)) or isinstance(nominal_step, bool):
                        raise ReleaseEvidenceError(
                            f"comparison manifest nominal step is invalid: {case_id}"
                        )
                    key = case_id, method, float(nominal_step), anchor_interval
                    if key in expected:
                        raise ReleaseEvidenceError(f"comparison manifest duplicates a result: {key!r}")
                    expected.add(key)
    return expected


def inspect_comparison(
    report_path: Path,
    manifest_path: Path,
    *,
    expected_source_commit: str,
    timing_path: Path | None = None,
) -> dict[str, Any]:
    validate_source_commit(expected_source_commit)
    report = read_json(report_path)
    manifest_hash = sha256_file(manifest_path)
    if report.get("manifest_sha256") != manifest_hash:
        raise ReleaseEvidenceError("comparison report manifest hash does not match")
    runner = report.get("runner")
    if not isinstance(runner, dict) or runner.get("quick") is not False:
        raise ReleaseEvidenceError("release comparison report must be a complete non-quick run")
    source = report.get("source")
    if not isinstance(source, dict):
        raise ReleaseEvidenceError("comparison report source provenance is missing")
    if source.get("commit") != expected_source_commit or source.get("dirty") is not False:
        raise ReleaseEvidenceError("comparison report is not from the clean expected source commit")
    expected = expected_comparison_keys(manifest_path)
    results = report.get("results")
    if not isinstance(results, list):
        raise ReleaseEvidenceError("comparison report results are missing")
    actual_values = [comparison_result_key(result, path=report_path) for result in results]
    if len(actual_values) != len(set(actual_values)):
        raise ReleaseEvidenceError("comparison report contains duplicate results")
    actual = set(actual_values)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ReleaseEvidenceError(
            f"comparison matrix mismatch; missing={missing!r}, unexpected={unexpected!r}"
        )
    cases = report.get("cases")
    expected_case_ids = {key[0] for key in expected}
    if not isinstance(cases, list) or {
        case.get("id") for case in cases if isinstance(case, dict)
    } != expected_case_ids:
        raise ReleaseEvidenceError("comparison report case evidence is incomplete")
    analyses = report.get("analyses")
    if not isinstance(analyses, dict) or any(
        not isinstance(analyses.get(name), list)
        for name in ("convergence", "fixed_accuracy", "fixed_work")
    ):
        raise ReleaseEvidenceError("comparison report analyses are incomplete")
    timing_summary_value = None
    if timing_path is not None:
        timing = read_json(timing_path)
        timing_results = timing.get("results")
        if not isinstance(timing_results, list):
            raise ReleaseEvidenceError("timing report results are missing")
        timing_values = [comparison_result_key(result, path=timing_path) for result in timing_results]
        if len(timing_values) != len(set(timing_values)) or set(timing_values) != expected:
            raise ReleaseEvidenceError("timing report matrix does not match numerical results")
        timing_source = timing.get("source")
        if not isinstance(timing_source, dict) or timing_source != source:
            raise ReleaseEvidenceError("timing report source provenance does not match")
        timing_summary_value = comparison_summary(timing_path, timing=True)
    return {
        "manifest": manifest_path.name,
        "manifest_sha256": manifest_hash,
        "source_commit": expected_source_commit,
        "source_tree_sha256": source.get("source_tree_sha256"),
        "case_count": len(expected_case_ids),
        "method_count": len({key[1] for key in expected}),
        "result_count": len(expected),
        "analysis_counts": {
            name: len(analyses[name])
            for name in ("convergence", "fixed_accuracy", "fixed_work")
        },
        "timing": timing_summary_value,
    }


def build_manifest(
    evidence_directory: Path,
    *,
    source_commit: str,
    tag: str,
    wheel_name: str,
    required_files: Iterable[str],
) -> dict[str, Any]:
    validate_release_identity(source_commit, tag, allow_candidate=True)
    if wheel_name != _project.wheel_filename():
        raise ReleaseEvidenceError("release wheel name does not match package version")
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
    required_values = list(required_files)
    if len(required_values) != len(set(required_values)):
        raise ReleaseEvidenceError("required release evidence contains duplicate paths")
    required = sorted(CORE_EVIDENCE_FILES | set(required_values) | {wheel_name})
    missing = [name for name in required if not (evidence_directory / name).is_file()]
    if missing:
        raise ReleaseEvidenceError(f"required release evidence is missing: {missing!r}")
    created_utc = normalize_utc_timestamp(
        read_text_evidence(evidence_directory, "QUALIFICATION_CREATED_UTC")
    )
    environment = {
        field: read_text_evidence(evidence_directory, name)
        for field, name in ENVIRONMENT_FIELDS.items()
    }
    workflow = {
        field: read_text_evidence(evidence_directory, name)
        for field, name in WORKFLOW_FIELDS.items()
    }
    if workflow["sha"] != "unavailable":
        validate_source_commit(workflow["sha"])
        if workflow["sha"] != source_commit:
            raise ReleaseEvidenceError("workflow SHA does not match source commit")
    if tag == f"v{_project.VERSION}":
        if workflow["event"] != "push" or workflow["ref"] != f"refs/tags/{tag}":
            raise ReleaseEvidenceError("release tag evidence is not from the exact tag push")
        if not workflow["run_id"].isdigit():
            raise ReleaseEvidenceError("release tag evidence lacks a GitHub workflow run ID")
        if not workflow["run_url"].endswith(f"/actions/runs/{workflow['run_id']}"):
            raise ReleaseEvidenceError("release tag evidence workflow URL does not match its run ID")
    elif workflow["run_id"] != "unavailable":
        if workflow["event"] not in {"workflow_dispatch", "local"}:
            raise ReleaseEvidenceError("candidate evidence has an unexpected workflow event")
        if workflow["event"] == "workflow_dispatch" and not workflow["ref"].startswith(
            "refs/heads/"
        ):
            raise ReleaseEvidenceError("candidate workflow evidence is not from a branch ref")
        if workflow["run_url"] != "unavailable" and not workflow["run_url"].endswith(
            f"/actions/runs/{workflow['run_id']}"
        ):
            raise ReleaseEvidenceError("candidate workflow URL does not match its run ID")
    tests = [
        parse_test_log(path)
        for path in sorted(evidence_directory.glob("*tests.log"), key=lambda item: item.name)
    ]
    comparisons = []
    for name in ("source-comparison.json", "installed-wheel-comparison.json"):
        path = evidence_directory / name
        if path.is_file():
            comparisons.append(comparison_summary(path))
    timing_path = evidence_directory / "source-timing.json"
    if timing_path.is_file():
        comparisons.append(comparison_summary(timing_path, timing=True))
    wheel_hash = sha256_file(wheel)
    wheel_hash_path = evidence_directory / "WHEEL_SHA256"
    if wheel_hash_path.is_file():
        recorded_wheel_hash = wheel_hash_path.read_text().strip().partition("  ")[0]
        if recorded_wheel_hash != wheel_hash:
            raise ReleaseEvidenceError("WHEEL_SHA256 does not match the retained wheel")
    inspection_path = evidence_directory / "wheel-inspection.json"
    if inspection_path.is_file():
        inspection = read_json(inspection_path)
        if (
            inspection.get("filename") != wheel_name
            or inspection.get("version") != _project.VERSION
            or inspection.get("sha256") != wheel_hash
            or inspection.get("size") != wheel.stat().st_size
        ):
            raise ReleaseEvidenceError("wheel inspection does not match the retained wheel")
    return {
        "schema": "bab-cs-release-evidence-v1",
        "status": "candidate",
        "qualification": {"created_utc": created_utc},
        "package": {
            "distribution": _project.DISTRIBUTION_NAME,
            "version": _project.VERSION,
            "tag": tag,
            "source_commit": source_commit,
            "wheel": wheel_name,
            "wheel_sha256": wheel_hash,
        },
        "environment": environment,
        "workflow": workflow,
        "tests": tests,
        "comparisons": comparisons,
        "required_files": required,
        "files": manifest_entries(evidence_directory),
    }


def write_manifest(
    evidence_directory: Path,
    *,
    source_commit: str,
    tag: str,
    wheel_name: str,
    required_files: Iterable[str],
) -> dict[str, Any]:
    evidence_directory.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(
        evidence_directory,
        source_commit=source_commit,
        tag=tag,
        wheel_name=wheel_name,
        required_files=required_files,
    )
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
        data = json.loads(
            path.read_text(),
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
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
    validate_release_identity(expected_source_commit, expected_tag, allow_candidate=True)
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
    reconstructed = build_manifest(
        evidence_directory,
        source_commit=expected_source_commit,
        tag=expected_tag,
        wheel_name=wheel_name,
        required_files=required,
    )
    if reconstructed != manifest:
        raise ReleaseEvidenceError("release manifest semantic content does not match evidence")
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


def load_required_files(path: Path, *, wheel_name: str) -> list[str]:
    values = []
    for line in path.read_text().splitlines():
        value = line.strip()
        if not value:
            continue
        value = value.replace("{wheel}", wheel_name)
        if "{" in value or "}" in value or Path(value).name != value:
            raise ReleaseEvidenceError(f"invalid required evidence path: {value!r}")
        values.append(value)
    if not values:
        raise ReleaseEvidenceError("required evidence profile is empty")
    if len(values) != len(set(values)):
        raise ReleaseEvidenceError("required evidence profile contains duplicate paths")
    return values


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
    environment.add_argument("--created-utc")
    environment.add_argument("--workflow-run-id")
    environment.add_argument("--workflow-run-url")
    environment.add_argument("--workflow-event")
    environment.add_argument("--workflow-ref")
    environment.add_argument("--workflow-sha")

    wheel = subparsers.add_parser("inspect-wheel")
    wheel.add_argument("--wheel", required=True)
    wheel.add_argument("--repository-root", default=".")
    wheel.add_argument("--output", required=True)

    compare = subparsers.add_parser("compare-artifacts")
    compare.add_argument("--pair", action="append", required=True)
    compare.add_argument("--output", required=True)

    comparison = subparsers.add_parser("inspect-comparison")
    comparison.add_argument("--report", required=True)
    comparison.add_argument("--manifest", required=True)
    comparison.add_argument("--source-commit", required=True)
    comparison.add_argument("--timing-report")
    comparison.add_argument("--output", required=True)

    manifest = subparsers.add_parser("write-manifest")
    manifest.add_argument("--evidence-dir", required=True)
    manifest.add_argument("--source-commit", required=True)
    manifest.add_argument("--tag", required=True)
    manifest.add_argument("--wheel", required=True)
    manifest.add_argument("--requirements-file")
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
                created_utc=arguments.created_utc,
                workflow_run_id=arguments.workflow_run_id,
                workflow_run_url_value=arguments.workflow_run_url,
                workflow_event=arguments.workflow_event,
                workflow_ref=arguments.workflow_ref,
                workflow_sha=arguments.workflow_sha,
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
        elif arguments.command == "inspect-comparison":
            write_json(
                Path(arguments.output),
                inspect_comparison(
                    Path(arguments.report),
                    Path(arguments.manifest),
                    expected_source_commit=arguments.source_commit,
                    timing_path=Path(arguments.timing_report) if arguments.timing_report else None,
                ),
            )
        elif arguments.command == "write-manifest":
            required_files = list(arguments.require)
            if arguments.requirements_file:
                required_files.extend(
                    load_required_files(
                        Path(arguments.requirements_file),
                        wheel_name=arguments.wheel,
                    )
                )
            write_manifest(
                Path(arguments.evidence_dir),
                source_commit=arguments.source_commit,
                tag=arguments.tag,
                wheel_name=arguments.wheel,
                required_files=required_files,
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
