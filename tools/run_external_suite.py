from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from tools.compare_external import run_external_comparison
except ModuleNotFoundError:
    from compare_external import run_external_comparison


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPOSITORY_ROOT / "benchmarks" / "external" / "manifest.json"


class ExternalSuiteError(RuntimeError):
    pass


def load_external_manifest(path: str | Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest_path = Path(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ExternalSuiteError("external manifest must be a schema-version 1 object")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ExternalSuiteError("external manifest requires a non-empty cases list")
    required = {"id", "title", "category", "input", "engineering_question", "mapped_features"}
    identifiers: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or not required.issubset(case):
            raise ExternalSuiteError("each external case requires identity, scope, and mapping metadata")
        case_id = str(case["id"])
        if case_id in identifiers:
            raise ExternalSuiteError(f"duplicate external case id: {case_id}")
        identifiers.add(case_id)
        input_path = (manifest_path.parent / str(case["input"])).resolve()
        if not input_path.is_file():
            raise ExternalSuiteError(f"external case input is missing: {input_path}")
        features = case["mapped_features"]
        if not isinstance(features, list) or not features:
            raise ExternalSuiteError(f"{case_id}: mapped_features must be a non-empty list")
    return manifest


def run_external_suite(
    manifest_path: str | Path,
    output_root: str | Path,
    *,
    executable: str = "ngspice",
    mode: str = "active",
    overwrite: bool = False,
    filename_prefix: str = "",
) -> dict[str, Any]:
    resolved_manifest = Path(manifest_path).resolve()
    manifest = load_external_manifest(resolved_manifest)
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    external_version = "unknown"
    for case in manifest["cases"]:
        case_id = str(case["id"])
        input_path = (resolved_manifest.parent / str(case["input"])).resolve()
        report, netlist, raw_output, external_log = run_external_comparison(
            input_path,
            executable=executable,
            mode=mode,
        )
        base_name = f"{filename_prefix}{case_id}"
        artifacts = {
            "report": root / f"{base_name}.json",
            "netlist": root / f"{base_name}.cir",
            "raw": root / f"{base_name}.dat",
            "log": root / f"{base_name}.log",
        }
        _write_text(
            artifacts["report"],
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
            overwrite=overwrite,
        )
        _write_text(artifacts["netlist"], netlist, overwrite=overwrite)
        _write_text(artifacts["raw"], raw_output, overwrite=overwrite)
        _write_text(artifacts["log"], external_log, overwrite=overwrite)
        external_version = str(report["external_tool"]["version"])
        state_metrics = list(report["accuracy"].values())
        results.append(
            {
                "id": case_id,
                "title": str(case["title"]),
                "category": str(case["category"]),
                "input": str(case["input"]),
                "engineering_question": str(case["engineering_question"]),
                "mapped_features": [str(feature) for feature in case["mapped_features"]],
                "reduced_order": bool(case.get("reduced_order", False)),
                "case_sha256": str(report["case_sha256"]),
                "netlist_sha256": str(report["netlist_sha256"]),
                "raw_output_sha256": str(report["raw_output_sha256"]),
                "external_log_sha256": str(report["external_log_sha256"]),
                "state_names": list(report["state_names"]),
                "sample_count": int(report["sample_count"]),
                "maximum_absolute_error": max(
                    float(metric["maximum_absolute_error"]) for metric in state_metrics
                ),
                "maximum_scaled_error": max(
                    float(metric["maximum_scaled_error"]) for metric in state_metrics
                ),
                "maximum_rms_absolute_error": max(
                    float(metric["rms_absolute_error"]) for metric in state_metrics
                ),
                "artifact_sha256": {
                    name: _sha256(path.read_bytes()) for name, path in artifacts.items()
                },
            }
        )
    suite = {
        "schema_version": 1,
        "manifest": resolved_manifest.relative_to(REPOSITORY_ROOT).as_posix(),
        "manifest_sha256": _sha256(resolved_manifest.read_bytes()),
        "external_tool": {"name": "ngspice", "version": external_version},
        "mode": mode,
        "case_count": len(results),
        "cases": results,
        "claim_boundary": str(manifest["claim_boundary"]),
    }
    _write_text(
        root / f"{filename_prefix}suite.json",
        json.dumps(suite, indent=2, sort_keys=True, allow_nan=False) + "\n",
        overwrite=overwrite,
    )
    return suite


def reference_projection(suite: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "manifest": suite["manifest"],
        "manifest_sha256": suite["manifest_sha256"],
        "external_tool": suite["external_tool"],
        "mode": suite["mode"],
        "case_count": suite["case_count"],
        "cases": [
            {
                key: case[key]
                for key in (
                    "id",
                    "title",
                    "category",
                    "input",
                    "engineering_question",
                    "mapped_features",
                    "reduced_order",
                    "case_sha256",
                    "netlist_sha256",
                    "state_names",
                    "sample_count",
                    "maximum_absolute_error",
                    "maximum_scaled_error",
                    "maximum_rms_absolute_error",
                )
            }
            for case in suite["cases"]
        ],
        "claim_boundary": suite["claim_boundary"],
    }


def _write_text(path: Path, content: str, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite external suite evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the manifest-owned BAB-CS ngspice suite")
    parser.add_argument("manifest", nargs="?", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--reference-output")
    parser.add_argument("--executable", default="ngspice")
    parser.add_argument("--mode", choices=("disabled", "shadow", "active"), default="active")
    parser.add_argument("--filename-prefix", default="")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    suite = run_external_suite(
        arguments.manifest,
        arguments.output_root,
        executable=arguments.executable,
        mode=arguments.mode,
        overwrite=arguments.overwrite,
        filename_prefix=arguments.filename_prefix,
    )
    if arguments.reference_output:
        _write_text(
            Path(arguments.reference_output),
            json.dumps(reference_projection(suite), indent=2, sort_keys=True, allow_nan=False)
            + "\n",
            overwrite=arguments.overwrite,
        )
    print(
        json.dumps(
            {
                "case_count": suite["case_count"],
                "external_tool": suite["external_tool"],
                "output_root": str(arguments.output_root),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
