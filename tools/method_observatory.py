from __future__ import annotations

import argparse
import csv
import html
import json
import math
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.compare_methods import (
    execute_manifest,
    load_manifest,
    write_csv_report,
    write_report,
)


DEFAULT_MANIFEST = REPOSITORY_ROOT / "benchmarks/observatory/manifest.json"
REQUIRED_CASES = {
    "rc_step",
    "rl_step",
    "rlc_damped",
    "lc_long",
    "diode_clip",
    "switched_rc",
}
REQUIRED_CANDIDATES = {
    "candidate_explicit_euler",
    "candidate_heun",
    "candidate_rk23",
    "candidate_ab2",
    "candidate_backward_euler",
    "candidate_trapezoidal",
    "candidate_bdf2",
}


def execute_observatory(
    manifest_path: str | Path = DEFAULT_MANIFEST,
    *,
    selected_cases: set[str] | None = None,
    quick: bool = False,
    timing_repeats: int = 0,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    manifest = load_manifest(manifest_path)
    _validate_observatory_manifest(manifest)
    report, timing = execute_manifest(
        manifest_path,
        selected_cases=selected_cases,
        quick=quick,
        timing_repeats=timing_repeats,
    )
    coverage = _coverage_data(
        manifest,
        report["results"],
        selected_cases=selected_cases,
        quick=quick,
    )
    if coverage["missing_rows"] or coverage["duplicate_rows"]:
        raise ValueError("observatory result matrix is incomplete or contains duplicates")
    report["facility"] = "BAB-CS Method Observatory"
    report["coverage"] = coverage
    report["claim_boundary"] = (
        "Fixed-accuracy and fixed-work selections use measured successful rows only; "
        "timing is separate characterization and no method is universally preferred."
    )
    return report, timing


def write_analysis_csv(
    path: str | Path,
    rows: list[dict[str, Any]],
    *,
    overwrite: bool = False,
) -> None:
    output = _prepare_output(path, overwrite)
    fields = sorted({key for row in rows for key in row})
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_accuracy_by_work_svg(
    path: str | Path,
    report: dict[str, Any],
    *,
    overwrite: bool = False,
) -> None:
    output = _prepare_output(path, overwrite)
    rows = [
        row
        for row in report["results"]
        if row["status"] == "success"
        and row["work"]["deterministic_work_units"] > 0
        and row["accuracy"]["maximum_absolute_error"] > 0.0
    ]
    width = 960
    height = 560
    margin = 70
    if not rows:
        raise ValueError("observatory plot requires successful positive rows")
    work_values = [math.log10(row["work"]["deterministic_work_units"]) for row in rows]
    error_values = [math.log10(row["accuracy"]["maximum_absolute_error"]) for row in rows]
    minimum_work, maximum_work = min(work_values), max(work_values)
    minimum_error, maximum_error = min(error_values), max(error_values)
    work_span = max(maximum_work - minimum_work, 1.0)
    error_span = max(maximum_error - minimum_error, 1.0)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<line x1="{margin}" y1="{height-margin}" x2="{width-margin}" '
        f'y2="{height-margin}" stroke="black"/>',
        f'<line x1="{margin}" y1="{margin}" x2="{margin}" '
        f'y2="{height-margin}" stroke="black"/>',
        f'<text x="{width/2}" y="{height-18}" text-anchor="middle" '
        f'font-family="sans-serif">log10 deterministic work</text>',
        f'<text x="18" y="{height/2}" text-anchor="middle" '
        f'transform="rotate(-90 18 {height/2})" font-family="sans-serif">'
        f'log10 maximum authority error</text>',
    ]
    for row in sorted(rows, key=lambda item: item["row_id"]):
        work = math.log10(row["work"]["deterministic_work_units"])
        error = math.log10(row["accuracy"]["maximum_absolute_error"])
        x = margin + (work - minimum_work) / work_span * (width - 2 * margin)
        y = height - margin - (error - minimum_error) / error_span * (height - 2 * margin)
        label = html.escape(f'{row["case_id"]} {row["method"]} {row["row_id"]}')
        lines.append(f'<circle cx="{x:.6f}" cy="{y:.6f}" r="3"><title>{label}</title></circle>')
    lines.append("</svg>\n")
    output.write_text("\n".join(lines), encoding="utf-8")


def write_markdown_summary(
    path: str | Path,
    report: dict[str, Any],
    *,
    overwrite: bool = False,
) -> None:
    output = _prepare_output(path, overwrite)
    coverage = report["coverage"]
    lines = [
        "# BAB-CS Method Observatory Report",
        "",
        "This generated report compares measured configurations. It does not prove",
        "universal superiority of any method, and timing is not a correctness gate.",
        "",
        "## Coverage",
        "",
        f'- Required rows: `{coverage["expected_row_count"]}`',
        f'- Produced rows: `{coverage["actual_row_count"]}`',
        f'- Cases: `{coverage["case_count"]}`',
        f'- Candidate methods: `{coverage["candidate_count"]}`',
        "",
        "## Fixed Accuracy",
        "",
        "| Case | Method | Target | Status | Selected row | Work | Error |",
        "| --- | --- | ---: | --- | --- | ---: | ---: |",
    ]
    for row in report["analyses"]["fixed_accuracy"]:
        lines.append(
            "| {case_id} | {method} | {accuracy_target} | {status} | {selected_row_id} | "
            "{deterministic_work_units} | {maximum_absolute_error} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Fixed Work",
            "",
            "| Case | Method | Budget | Status | Selected row | Work | Error |",
            "| --- | --- | ---: | --- | --- | ---: | ---: |",
        ]
    )
    for row in report["analyses"]["fixed_work"]:
        lines.append(
            "| {case_id} | {method} | {work_budget} | {status} | {selected_row_id} | "
            "{deterministic_work_units} | {maximum_absolute_error} |".format(**row)
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_observatory_manifest(manifest: dict[str, Any]) -> None:
    cases = {str(case["id"]): case for case in manifest["cases"]}
    if set(cases) != REQUIRED_CASES:
        raise ValueError("observatory manifest must contain the canonical six cases")
    declared = set(map(str, manifest.get("candidate_methods", [])))
    if declared != REQUIRED_CANDIDATES:
        raise ValueError("observatory manifest must declare all seven candidate methods")
    for case_id, case in cases.items():
        if set(map(str, case["methods"])) != REQUIRED_CANDIDATES:
            raise ValueError(f"{case_id}: observatory case must run all candidate methods")
        if len(case["nominal_steps"]) < 3:
            raise ValueError(f"{case_id}: observatory case requires three refinements")
        if len(case.get("anchor_intervals", [])) != 1:
            raise ValueError(f"{case_id}: observatory case requires one canonical anchor interval")


def _coverage_data(
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    selected_cases: set[str] | None,
    quick: bool,
) -> dict[str, Any]:
    cases = [
        case
        for case in manifest["cases"]
        if selected_cases is None or str(case["id"]) in selected_cases
    ]
    if quick and selected_cases is None:
        cases = cases[:1]
    expected = []
    for case in cases:
        steps = case["nominal_steps"][:2] if quick else case["nominal_steps"]
        interval = int(case["anchor_intervals"][0])
        for method in case["methods"]:
            for step in steps:
                expected.append((str(case["id"]), str(method), float(step), interval))
    actual = [
        (
            str(row["case_id"]),
            str(row["method"]),
            float(row["nominal_step"]),
            int(row["anchor_interval"]),
        )
        for row in rows
    ]
    expected_set = set(expected)
    actual_set = set(actual)
    return {
        "case_count": len(cases),
        "candidate_count": len(REQUIRED_CANDIDATES),
        "expected_row_count": len(expected),
        "actual_row_count": len(actual),
        "successful_row_count": sum(row["status"] == "success" for row in rows),
        "missing_rows": [list(value) for value in sorted(expected_set - actual_set)],
        "unexpected_rows": [list(value) for value in sorted(actual_set - expected_set)],
        "duplicate_rows": len(actual) - len(actual_set),
    }


def _prepare_output(path: str | Path, overwrite: bool) -> Path:
    output = Path(path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite observatory evidence: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the BAB-CS Method Observatory")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--case", action="append", dest="cases")
    parser.add_argument("--output", required=True)
    parser.add_argument("--fixed-step-csv")
    parser.add_argument("--fixed-accuracy-csv")
    parser.add_argument("--fixed-work-csv")
    parser.add_argument("--plot-output")
    parser.add_argument("--markdown-output")
    parser.add_argument("--timing-output")
    parser.add_argument("--timing-repeats", type=int, default=0)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.timing_repeats and not arguments.timing_output:
        raise ValueError("--timing-repeats requires --timing-output")
    report, timing = execute_observatory(
        arguments.manifest,
        selected_cases=set(arguments.cases) if arguments.cases else None,
        quick=arguments.quick,
        timing_repeats=arguments.timing_repeats,
    )
    write_report(arguments.output, report, overwrite=arguments.overwrite)
    if arguments.fixed_step_csv:
        write_csv_report(arguments.fixed_step_csv, report, overwrite=arguments.overwrite)
    if arguments.fixed_accuracy_csv:
        write_analysis_csv(
            arguments.fixed_accuracy_csv,
            report["analyses"]["fixed_accuracy"],
            overwrite=arguments.overwrite,
        )
    if arguments.fixed_work_csv:
        write_analysis_csv(
            arguments.fixed_work_csv,
            report["analyses"]["fixed_work"],
            overwrite=arguments.overwrite,
        )
    if arguments.plot_output:
        write_accuracy_by_work_svg(arguments.plot_output, report, overwrite=arguments.overwrite)
    if arguments.markdown_output:
        write_markdown_summary(arguments.markdown_output, report, overwrite=arguments.overwrite)
    if timing is not None:
        assert arguments.timing_output is not None
        write_report(arguments.timing_output, timing, overwrite=arguments.overwrite)
    print(
        json.dumps(
            {
                "cases": report["coverage"]["case_count"],
                "candidates": report["coverage"]["candidate_count"],
                "rows": report["coverage"]["actual_row_count"],
                "output": arguments.output,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
