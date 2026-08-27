from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

try:
    from tools.docs_concepts import CONCEPT_GLOSSARY, concept_ids_for_markdown
    from tools.docs_site_assets import SVG_ASSET_NAMES, render_svg_assets
except ModuleNotFoundError:
    from docs_concepts import CONCEPT_GLOSSARY, concept_ids_for_markdown
    from docs_site_assets import SVG_ASSET_NAMES, render_svg_assets


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPOSITORY_ROOT / "docs"
DEFAULT_OUTPUT = DOCS_ROOT / "html" / "documents.js"

BENCHMARK_MANIFEST = REPOSITORY_ROOT / "benchmarks" / "manifest.json"
OBSERVATORY_MANIFEST = REPOSITORY_ROOT / "benchmarks" / "observatory" / "manifest.json"
POWER_STAGE_MANIFEST = REPOSITORY_ROOT / "benchmarks" / "power_stage" / "manifest.json"
EXTERNAL_MANIFEST = REPOSITORY_ROOT / "benchmarks" / "external" / "manifest.json"
EXTERNAL_REFERENCE = REPOSITORY_ROOT / "benchmarks" / "external" / "reference-results.json"
COMPARISON_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "comparisons.yml"
TESTS_ROOT = REPOSITORY_ROOT / "tests"
LAB_ROOT = REPOSITORY_ROOT / "lab"

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
INDEX_LINK_PATTERN = re.compile(r"^\s*-\s+\[([^]]+)]\(([^)]+)\)\s*$")
WORD_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_'’-]*")


def slugify(value: str) -> str:
    plain = re.sub(r"[`*_~]", "", value).strip().lower()
    plain = re.sub(r"[^a-z0-9\s-]", "", plain)
    return re.sub(r"[-\s]+", "-", plain).strip("-") or "section"


def document_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        match = HEADING_PATTERN.match(line)
        if match and len(match.group(1)) == 1:
            return match.group(2).strip()
    return fallback


def document_summary(markdown: str) -> str:
    paragraphs: list[str] = []
    in_fence = False
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped:
            if paragraphs:
                break
            continue
        if HEADING_PATTERN.match(line) or stripped.startswith(("- ", "* ", ">", "|")):
            if paragraphs:
                break
            continue
        paragraphs.append(stripped)
    summary = " ".join(paragraphs)
    summary = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", summary)
    summary = re.sub(r"[`*~]", "", summary)
    if len(summary) > 240:
        shortened = summary[:237].rsplit(" ", 1)[0].rstrip(" ,;:-")
        summary = shortened + "…"
    return summary


def document_kind(path: str, category: str) -> str:
    if path == "index.md":
        return "Overview"
    if path == "REFERENCES.md":
        return "Reference"
    if "LICENCE" in path or "GOVERNANCE" in path:
        return "Policy"
    if path.endswith("_SPEC.md"):
        return "Design"
    if category == "Current Work Essays":
        return "Essay"
    if category == "Start Here":
        return "Guide"
    if category == "Numerical Design":
        return "Design"
    if category == "Tests and Comparisons":
        return "Evidence"
    if category == "Qualification and Release":
        return "Audit"
    return "Guide"


def document_headings(markdown: str) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    in_fence = False
    for line in markdown.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_PATTERN.match(line)
        if not match:
            continue
        level = len(match.group(1))
        text = match.group(2).strip()
        base = slugify(text)
        occurrence = counts.get(base, 0)
        counts[base] = occurrence + 1
        identifier = base if occurrence == 0 else f"{base}-{occurrence + 1}"
        headings.append({"level": level, "text": text, "id": identifier})
    return headings


def _markdown_paths(docs_root: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(
            path
            for path in docs_root.rglob("*.md")
            if "html" not in path.relative_to(docs_root).parts
        )
    )


def _index_categories(docs_root: Path, available: set[str]) -> list[dict[str, Any]]:
    categories: list[dict[str, Any]] = [
        {"name": "Documentation Home", "documents": ["index.md"]}
    ]
    assigned = {"index.md"}
    current: dict[str, Any] | None = None
    index_path = docs_root / "index.md"
    for line in index_path.read_text(encoding="utf-8").splitlines():
        heading = HEADING_PATTERN.match(line)
        if heading and len(heading.group(1)) == 2:
            current = {"name": heading.group(2).strip(), "documents": []}
            categories.append(current)
            continue
        link = INDEX_LINK_PATTERN.match(line)
        if current is None or not link:
            continue
        raw_target = link.group(2).split("#", 1)[0]
        target = (docs_root / raw_target).resolve()
        try:
            relative = target.relative_to(docs_root.resolve()).as_posix()
        except ValueError:
            continue
        if relative in available and relative not in assigned:
            current["documents"].append(relative)
            assigned.add(relative)
    categories = [category for category in categories if category["documents"]]
    remaining = sorted(available - assigned)
    if remaining:
        categories.append({"name": "Additional Documents", "documents": remaining})
    return categories


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _test_surface(tests_root: Path) -> dict[str, int]:
    modules = sorted(tests_root.glob("test_*.py"))
    method_count = 0
    for path in modules:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        method_count += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test")
            for node in ast.walk(tree)
        )
    return {"methods": method_count, "modules": len(modules)}


def _comparison_matrix_count(manifest: dict[str, Any]) -> int:
    keys: set[tuple[str, str, float, int | None]] = set()
    for case in manifest["cases"]:
        case_id = str(case["id"])
        for method_value in case["methods"]:
            method = str(method_value)
            intervals: list[int | None] = (
                [int(value) for value in case.get("anchor_intervals", [16])]
                if method in {"active", "shadow"} or method.startswith("candidate_")
                else [None]
            )
            for anchor_interval in intervals:
                for nominal_step in case["nominal_steps"]:
                    keys.add((case_id, method, float(nominal_step), anchor_interval))
    return len(keys)


def _manifest_surface(path: Path) -> dict[str, Any]:
    manifest = _read_json(path)
    cases = manifest["cases"]
    methods = sorted({str(method) for case in cases for method in case["methods"]})
    return {
        "cases": len(cases),
        "caseIds": [str(case["id"]) for case in cases],
        "methods": len(methods),
        "methodIds": methods,
        "assignments": sum(len(case["methods"]) for case in cases),
        "matrixRows": _comparison_matrix_count(manifest),
    }


def _external_surface(manifest_path: Path, reference_path: Path) -> dict[str, Any]:
    manifest = _read_json(manifest_path)
    reference = _read_json(reference_path)
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"external comparison manifest has no cases: {manifest_path}")
    case_ids = [str(case["id"]) for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError(f"external comparison manifest has duplicate cases: {manifest_path}")
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    if reference.get("manifest_sha256") != manifest_sha:
        raise ValueError("external reference results do not match the current manifest")
    if int(reference.get("case_count", -1)) != len(case_ids):
        raise ValueError("external reference result count does not match the manifest")
    category_counts: dict[str, int] = {}
    for case in cases:
        category = str(case["category"])
        category_counts[category] = category_counts.get(category, 0) + 1
    return {
        "cases": len(case_ids),
        "caseIds": case_ids,
        "categories": category_counts,
        "mappedFeatures": len(
            {
                str(feature)
                for case in cases
                for feature in case.get("mapped_features", [])
            }
        ),
        "referenceTool": dict(reference["external_tool"]),
    }


def _teaching_exercises(lab_root: Path) -> list[str]:
    return [
        path.name
        for path in sorted(lab_root.iterdir())
        if path.is_dir() and re.fullmatch(r"\d{2}-[a-z0-9-]+", path.name)
    ]


def _metrics_source_sha256(paths: list[Path], repository_root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        relative = path.relative_to(repository_root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def build_site_metrics(repository_root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    benchmark_manifest = repository_root / BENCHMARK_MANIFEST.relative_to(REPOSITORY_ROOT)
    observatory_manifest = repository_root / OBSERVATORY_MANIFEST.relative_to(REPOSITORY_ROOT)
    power_stage_manifest = repository_root / POWER_STAGE_MANIFEST.relative_to(REPOSITORY_ROOT)
    external_manifest = repository_root / EXTERNAL_MANIFEST.relative_to(REPOSITORY_ROOT)
    external_reference = repository_root / EXTERNAL_REFERENCE.relative_to(REPOSITORY_ROOT)
    comparison_workflow = repository_root / COMPARISON_WORKFLOW.relative_to(REPOSITORY_ROOT)
    tests_root = repository_root / TESTS_ROOT.relative_to(REPOSITORY_ROOT)
    lab_root = repository_root / LAB_ROOT.relative_to(REPOSITORY_ROOT)

    tests = _test_surface(tests_root)
    comparison = _manifest_surface(benchmark_manifest)
    observatory = _manifest_surface(observatory_manifest)
    power_stage = _manifest_surface(power_stage_manifest)
    external = _external_surface(external_manifest, external_reference)
    teaching_exercises = _teaching_exercises(lab_root)
    source_paths = [
        benchmark_manifest,
        observatory_manifest,
        power_stage_manifest,
        external_manifest,
        external_reference,
        comparison_workflow,
        *sorted(tests_root.glob("test_*.py")),
        *sorted(
            path / "README.md"
            for path in lab_root.iterdir()
            if (path / "README.md").is_file()
        ),
    ]
    return {
        "tests": tests,
        "comparison": comparison,
        "observatory": observatory,
        "powerStage": power_stage,
        "external": external,
        "teachingLab": {
            "exercises": len(teaching_exercises),
            "exerciseIds": teaching_exercises,
        },
        "sourceSha256": _metrics_source_sha256(source_paths, repository_root),
    }


def build_payload(
    docs_root: Path = DOCS_ROOT,
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, Any]:
    paths = _markdown_paths(docs_root)
    available = {path.relative_to(docs_root).as_posix() for path in paths}
    categories = _index_categories(docs_root, available)
    category_by_path: dict[str, str] = {}
    order_by_path: dict[str, int] = {}
    for category in categories:
        for order, relative in enumerate(category["documents"]):
            category_by_path[relative] = category["name"]
            order_by_path[relative] = order

    source_digest = hashlib.sha256()
    documents: list[dict[str, Any]] = []
    for path in paths:
        relative = path.relative_to(docs_root).as_posix()
        markdown = path.read_text(encoding="utf-8")
        encoded_path = relative.encode("utf-8")
        encoded_content = markdown.encode("utf-8")
        source_digest.update(len(encoded_path).to_bytes(8, "big"))
        source_digest.update(encoded_path)
        source_digest.update(len(encoded_content).to_bytes(8, "big"))
        source_digest.update(encoded_content)
        words = len(WORD_PATTERN.findall(markdown))
        title = document_title(markdown, path.stem.replace("_", " ").title())
        documents.append(
            {
                "path": relative,
                "title": title,
                "summary": document_summary(markdown),
                "category": category_by_path[relative],
                "kind": document_kind(relative, category_by_path[relative]),
                "order": order_by_path[relative],
                "wordCount": words,
                "readingMinutes": max(1, math.ceil(words / 220)),
                "sha256": hashlib.sha256(encoded_content).hexdigest(),
                "headings": document_headings(markdown),
                "conceptIds": concept_ids_for_markdown(markdown),
                "markdown": markdown,
            }
        )
    documents.sort(key=lambda item: (item["category"], item["order"], item["path"]))
    return {
        "schemaVersion": 3,
        "project": "Bounded-Authority-Based-Circuit-Simulation",
        "shortName": "BAB-CS",
        "documentCount": len(documents),
        "sourceSha256": source_digest.hexdigest(),
        "siteMetrics": build_site_metrics(repository_root),
        "featuredDocuments": [
            "ARCHITECTURE.md",
            "METHOD_OBSERVATORY.md",
            "BOUND_COVERAGE_ATLAS.md",
            "EXTERNAL_COMPARISON.md",
            "POWER_STAGE_SANDBOX.md",
            "TEACHING_AND_REPRODUCIBILITY_LAB.md",
        ],
        "diagramAssets": list(SVG_ASSET_NAMES),
        "conceptGlossary": list(CONCEPT_GLOSSARY),
        "categories": categories,
        "documents": documents,
    }


def render_documents_js(payload: dict[str, Any]) -> bytes:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    return f"window.BABCS_DOCUMENTS = {serialized};\n".encode("utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the deterministic BAB-CS HTML documentation payload"
    )
    parser.add_argument("--docs-root", type=Path, default=DOCS_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--assets-directory", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    payload = build_payload(arguments.docs_root.resolve())
    rendered = render_documents_js(payload)
    assets = render_svg_assets(payload)
    output = arguments.output.resolve()
    assets_directory = (
        arguments.assets_directory.resolve()
        if arguments.assets_directory is not None
        else output.parent / "assets"
    )
    if arguments.check:
        if not output.is_file() or output.read_bytes() != rendered:
            raise SystemExit(f"documentation payload is stale: {output}")
        for name, content in assets.items():
            asset_path = assets_directory / name
            if not asset_path.is_file() or asset_path.read_bytes() != content:
                raise SystemExit(f"documentation SVG is stale: {asset_path}")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(rendered)
        assets_directory.mkdir(parents=True, exist_ok=True)
        for name, content in assets.items():
            (assets_directory / name).write_bytes(content)
    print(
        json.dumps(
            {
                "assets": len(assets),
                "documents": payload["documentCount"],
                "output": str(output),
                "source_sha256": payload["sourceSha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
