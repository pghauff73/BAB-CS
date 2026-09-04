from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.docs_concepts import (
    CONCEPT_GLOSSARY,
    concept_ids_for_markdown,
    unexplained_prose_acronyms,
)
from tools.build_docs_html import (
    DOCS_ROOT,
    SVG_ASSET_NAMES,
    build_payload,
    document_kind,
    document_summary,
    render_documents_js,
    render_svg_assets,
)
from tools.docs_figure_assets import (
    CASE_PATHS,
    FIGURE_ASSET_NAMES,
)
from tools.docs_site_assets import CONCEPTUAL_SVG_ASSET_NAMES
from tools.docs_tutorial_assets import TUTORIAL_SVG_ASSET_NAMES


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
HTML_ROOT = DOCS_ROOT / "html"
EXTERNAL_MANIFEST = REPOSITORY_ROOT / "benchmarks/external/manifest.json"
EXTERNAL_REFERENCE = REPOSITORY_ROOT / "benchmarks/external/reference-results.json"


class DocumentationHtmlTests(unittest.TestCase):
    def test_payload_covers_every_docs_markdown_file_once(self) -> None:
        payload = build_payload()
        expected = {
            path.relative_to(DOCS_ROOT).as_posix()
            for path in DOCS_ROOT.rglob("*.md")
            if "html" not in path.relative_to(DOCS_ROOT).parts
        }
        actual = [document["path"] for document in payload["documents"]]
        tree_paths = [
            path
            for category in payload["categories"]
            for path in category["documents"]
        ]

        self.assertEqual(payload["documentCount"], len(expected))
        self.assertEqual(set(actual), expected)
        self.assertEqual(len(actual), len(set(actual)))
        self.assertCountEqual(tree_paths, expected)

    def test_index_hierarchy_and_automatic_additional_documents(self) -> None:
        payload = build_payload()
        categories = {
            category["name"]: category["documents"]
            for category in payload["categories"]
        }

        self.assertEqual(categories["Documentation Home"], ["index.md"])
        self.assertEqual(categories["Current Work Essays"][0], "CURRENT_WORK.md")
        self.assertIn("METHOD_OBSERVATORY.md", categories["Tests and Comparisons"])
        self.assertIn("GITHUB_GOVERNANCE.md", categories["Additional Documents"])

    def test_generated_payload_is_current_and_byte_deterministic(self) -> None:
        first = render_documents_js(build_payload())
        second = render_documents_js(build_payload())

        self.assertEqual(first, second)
        self.assertEqual(first, (HTML_ROOT / "documents.js").read_bytes())
        self.assertNotIn(b"generatedAt", first)

    def test_long_hero_summaries_end_at_a_word_boundary(self) -> None:
        markdown = "# Title\n\n" + ("alpha " * 39) + "boundaryword follows"
        summary = document_summary(markdown)

        self.assertLessEqual(len(summary), 240)
        self.assertTrue(summary.endswith("alpha…"))
        self.assertNotIn("bou…", summary)

    def test_every_document_has_deterministic_plain_language_concept_coverage(self) -> None:
        payload = build_payload()
        glossary_ids = [concept["id"] for concept in payload["conceptGlossary"]]

        self.assertEqual(payload["schemaVersion"], 3)
        self.assertEqual(payload["conceptGlossary"], list(CONCEPT_GLOSSARY))
        self.assertEqual(len(glossary_ids), len(set(glossary_ids)))
        self.assertGreaterEqual(len(glossary_ids), 60)
        for concept in payload["conceptGlossary"]:
            self.assertTrue(concept["term"])
            self.assertTrue(concept["aliases"])
            self.assertGreaterEqual(len(concept["definition"]), 40)

        glossary_id_set = set(glossary_ids)
        for document in payload["documents"]:
            with self.subTest(path=document["path"]):
                self.assertTrue(document["conceptIds"])
                self.assertEqual(
                    document["conceptIds"],
                    concept_ids_for_markdown(document["markdown"]),
                )
                self.assertTrue(set(document["conceptIds"]).issubset(glossary_id_set))

    def test_every_document_has_a_deterministic_navigation_role(self) -> None:
        payload = build_payload()

        expected_roles = {
            "index.md": "Overview",
            "CURRENT_WORK.md": "Essay",
            "BAB_CSV1_SPEC.md": "Design",
            "METHOD_OBSERVATORY.md": "Evidence",
            "VALIDATION_RELEASE_AND_CLAIMS_ESSAY.md": "Essay",
            "REFERENCES.md": "Reference",
            "GITHUB_GOVERNANCE.md": "Policy",
        }

        for document in payload["documents"]:
            with self.subTest(path=document["path"]):
                self.assertTrue(document["kind"])
                self.assertEqual(
                    document["kind"],
                    document_kind(document["path"], document["category"]),
                )
        actual_roles = {
            document["path"]: document["kind"]
            for document in payload["documents"]
        }
        for path, role in expected_roles.items():
            self.assertEqual(actual_roles[path], role)

    def test_glossary_covers_core_acronyms_used_by_the_document_tree(self) -> None:
        aliases = {
            alias
            for concept in CONCEPT_GLOSSARY
            for alias in concept["aliases"]
        }

        for acronym in (
            "BAB-CS",
            "MNA",
            "DAE",
            "SPICE",
            "RC",
            "RL",
            "RLC",
            "LC",
            "AB2",
            "AB3",
            "BDF2",
            "RK23",
            "CSC",
            "KLU",
            "COLAMD",
            "LRU",
            "RMS",
            "WRMS",
            "ULP",
            "JSON",
            "CSV",
            "SVG",
            "SHA-256",
            "CI",
            "CLI",
            "API",
            "URL",
            "UTC",
            "YAML",
            "HTML",
            "ZIP",
            "PYTHONPATH",
            "DOI",
            "SPDX",
            "MPL-2.0",
            "HIL",
        ):
            with self.subTest(acronym=acronym):
                self.assertIn(acronym, aliases)

    def test_short_uppercase_acronyms_do_not_match_ordinary_words(self) -> None:
        self.assertNotIn("be", concept_ids_for_markdown("This can be skipped."))
        self.assertNotIn("identifier", concept_ids_for_markdown("The idea is clear."))
        self.assertIn("be", concept_ids_for_markdown("Use BE for startup."))
        self.assertIn("identifier", concept_ids_for_markdown("Record the ID."))

    def test_no_document_contains_an_unexplained_prose_acronym(self) -> None:
        for path in sorted(DOCS_ROOT.glob("*.md")):
            with self.subTest(path=path.name):
                self.assertEqual(
                    unexplained_prose_acronyms(path.read_text(encoding="utf-8")),
                    [],
                )

    def test_html_css_and_javascript_expose_the_document_tree_features(self) -> None:
        html = (HTML_ROOT / "index.html").read_text(encoding="utf-8")
        css = (HTML_ROOT / "styles.css").read_text(encoding="utf-8")
        javascript = (HTML_ROOT / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="document-tree"', html)
        self.assertIn('id="document-search"', html)
        self.assertIn('id="table-of-contents"', html)
        self.assertIn('id="toc-progress"', html)
        self.assertIn('id="stage-progress-bar"', html)
        self.assertIn('class="authority-monitor-status"', html)
        self.assertIn('id="landing-dashboard"', html)
        self.assertIn('src="documents.js"', html)
        self.assertIn('src="app.js"', html)
        self.assertIn('html[data-theme="dark"]', css)
        self.assertIn("@media print", css)
        self.assertIn(".engineering-project-grid", css)
        self.assertIn(".project-filters", css)
        self.assertIn(".comparison-table", css)
        self.assertIn("--authority:", css)
        self.assertIn("--boundary:", css)
        self.assertIn(".stage-progress", css)
        self.assertIn(".toc-progress", css)
        self.assertIn(".tree-link-kind", css)
        self.assertIn(".authority-monitor-status", css)
        self.assertIn("function renderMarkdown", javascript)
        self.assertIn("function renderSearchResults", javascript)
        self.assertIn("function renderLandingDashboard", javascript)
        self.assertIn("function removeRepeatedHeroSummary", javascript)
        self.assertIn("removeRepeatedHeroSummary(documentProse, doc)", javascript)
        self.assertIn("function annotateConceptIntroductions", javascript)
        self.assertIn("const caseSensitive = /^[A-Z]", javascript)
        self.assertNotIn("function renderDocumentLearningGuide", javascript)
        self.assertIn('closest("h1, code, pre, a, abbr, .intext-learning-note")', javascript)
        self.assertIn('note.className = "intext-learning-note"', javascript)
        self.assertIn('label.textContent = "Plain words"', javascript)
        self.assertIn('setAttribute("aria-describedby", note.id)', javascript)
        self.assertIn("introducedConceptIds.add(concept.id)", javascript)
        self.assertIn("annotateConceptIntroductions(elements.summary, doc)", javascript)
        self.assertIn("annotateConceptIntroductions(documentProse, doc, introducedConceptIds)", javascript)
        self.assertIn('const block = parent.closest("table")', javascript)
        self.assertIn('tableContainer.insertAdjacentElement("beforebegin", note)', javascript)
        self.assertNotIn('["LI", "TD", "TH", "DD"]', javascript)
        self.assertIn("Make engineering simulation decisions", javascript)
        self.assertIn("Plain-Language Guide", javascript)
        self.assertIn("Candidate method", javascript)
        self.assertIn("Numerical authority", javascript)
        self.assertIn("Reduced-order model", javascript)
        self.assertIn("function applyProjectFilter", javascript)
        self.assertIn("category.documents.length", javascript)
        self.assertIn("document.kind", javascript)
        self.assertIn("tree-link-kind", javascript)
        self.assertIn("function updateTocProgress", javascript)
        self.assertIn("elements.stageProgress.style.width", javascript)
        self.assertIn("ngspice", javascript)
        self.assertIn("not an oracle", javascript.lower())
        self.assertIn("data-doc-path", javascript)
        self.assertIn("reference-link", javascript)
        self.assertIn(".reference-link", css)
        self.assertNotIn(".document-learning-guide", css)
        self.assertIn(".concept-introduction", css)
        self.assertIn(".intext-learning-note", css)
        self.assertIn(".intext-learning-label", css)

    def test_engineering_portfolio_and_software_comparison_are_explicitly_scoped(self) -> None:
        javascript = (HTML_ROOT / "app.js").read_text(encoding="utf-8")

        for project in (
            "Buck-converter control schedule screening",
            "H-bridge dead-time and resistor-inductor load reversal",
            "Direct-current link startup and interruption qualification",
            "Diode-clamped sensor or interface transient",
            "Inductor-capacitor phase and energy retention study",
            "Numerical-method selection for a simplified digital twin",
            "Solver, dependency, or packaging regression qualification",
            "Reproducible circuit-equation and convergence laboratory",
        ):
            self.assertIn(project, javascript)
        for official_url in (
            "https://ngspice.sourceforge.io/",
            "https://www.analog.com/en/resources/design-tools-and-calculators/ltspice-simulator.html",
            "https://www.plexim.com/products",
            "https://www.mathworks.com/products/simscape-electrical.html",
            "https://xyce.sandia.gov/",
        ):
            self.assertIn(official_url, javascript)
        self.assertIn("workflow map, not a ranking", javascript.lower())
        self.assertIn("not a production semiconductor", javascript.lower())
        self.assertIn("does not replace production semiconductor models", javascript)

    def test_current_work_essays_define_core_terms_for_novice_readers(self) -> None:
        required_phrases = {
            "CURRENT_WORK.md": (
                "Bounded-Authority-Based-Circuit-Simulation",
                "modified nodal analysis",
                "differential-algebraic equation",
                "reduced-order numerical experiments",
            ),
            "NUMERICAL_METHODS_ESSAY.md": (
                "Five Engineering Decisions BAB-CS Makes Reviewable",
                "Follow One Timestep from Proposal to Replay",
                "A DAE combines differential equations",
                "A Jacobian is a matrix of local sensitivities",
                "empirical coverage",
            ),
            "ENGINEERING_AND_PERFORMANCE_ESSAY.md": (
                "Why Authority Must Survive Optimization",
                "Follow One Timestep Through Its Decision Owners",
                "Measure the Whole Simulation, Not One Fast Kernel",
                "fast inner operation",
                "compressed sparse column",
                "A workspace is reusable memory",
                "unit in the last place",
            ),
            "VALIDATION_RELEASE_AND_CLAIMS_ESSAY.md": (
                "Why Does Validation Need Layers?",
                "How Does the Evidence Ladder Build Confidence?",
                "publication makes an approved tag",
                "Continuous integration",
                "Secure Hash Algorithm 256-bit",
                "A Python wheel is an installable package file",
            ),
            "APPLICATIONS_AND_RESEARCH_ROADMAP.md": (
                "Plain-Language Scope",
                "Engineering Projects Suited to BAB-CS",
                "workflow map, not a product ranking",
                "Hardware-in-the-loop",
            ),
        }

        for path, phrases in required_phrases.items():
            essay = (DOCS_ROOT / path).read_text(encoding="utf-8")
            normalized = " ".join(essay.replace("**", "").split()).lower()
            for phrase in phrases:
                with self.subTest(path=path, phrase=phrase):
                    self.assertIn(phrase.lower(), normalized)

    def test_selected_essays_follow_the_ourd_grammar_contract(self) -> None:
        numerical = (DOCS_ROOT / "NUMERICAL_METHODS_ESSAY.md").read_text(
            encoding="utf-8"
        )
        engineering = (DOCS_ROOT / "ENGINEERING_AND_PERFORMANCE_ESSAY.md").read_text(
            encoding="utf-8"
        )
        validation = (DOCS_ROOT / "VALIDATION_RELEASE_AND_CLAIMS_ESSAY.md").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("This essay explains", numerical)
        self.assertNotIn("## Engineering Purpose", engineering)
        self.assertNotIn("## Fast Inner Operation Versus Fast Complete Simulation", engineering)
        validation_headings = [
            line.removeprefix("## ")
            for line in validation.splitlines()
            if line.startswith("## ")
        ]
        self.assertEqual(len(validation_headings), 11)
        self.assertTrue(all(heading.endswith("?") for heading in validation_headings))

    def test_site_metrics_are_derived_from_canonical_repository_owners(self) -> None:
        metrics = build_payload()["siteMetrics"]

        self.assertEqual(metrics["comparison"]["cases"], 8)
        self.assertEqual(metrics["comparison"]["methods"], 15)
        self.assertEqual(metrics["comparison"]["assignments"], 51)
        self.assertEqual(metrics["comparison"]["matrixRows"], 154)
        self.assertEqual(metrics["observatory"]["cases"], 6)
        self.assertEqual(metrics["observatory"]["methods"], 7)
        self.assertEqual(metrics["observatory"]["matrixRows"], 126)
        self.assertEqual(metrics["powerStage"]["cases"], 3)
        self.assertEqual(metrics["powerStage"]["matrixRows"], 57)
        self.assertEqual(
            metrics["external"]["caseIds"],
            [
                "rc_step",
                "rc_discharge",
                "driven_rc",
                "current_driven_rc",
                "rl_step",
                "rl_decay",
                "lc_long",
                "lc_offset",
                "rlc_damped",
                "rlc_overdamped",
                "rlc_driven",
                "diode_clip",
                "diode_rectifier",
                "diode_bias_recovery",
                "switched_rc",
                "switched_rl",
                "switched_rlc",
                "buck_like_reduced_order",
                "h_bridge_rl_reduced_order",
                "dc_link_rlc_reduced_order",
            ],
        )
        self.assertEqual(metrics["external"]["cases"], 20)
        self.assertEqual(metrics["external"]["mappedFeatures"], 14)
        self.assertEqual(metrics["teachingLab"]["exercises"], 10)
        self.assertEqual(len(metrics["sourceSha256"]), 64)

    def test_generated_svg_diagrams_are_current_accessible_and_self_contained(self) -> None:
        payload = build_payload()
        first = render_svg_assets(payload)
        second = render_svg_assets(payload)

        self.assertEqual(tuple(first), SVG_ASSET_NAMES)
        self.assertEqual(len(first), 43)
        self.assertTrue(set(FIGURE_ASSET_NAMES).issubset(first))
        self.assertTrue(set(TUTORIAL_SVG_ASSET_NAMES).issubset(first))
        self.assertEqual(first, second)
        for name, rendered in first.items():
            self.assertEqual(rendered, (HTML_ROOT / "assets" / name).read_bytes())
            root = ET.fromstring(rendered)
            namespace = {"svg": "http://www.w3.org/2000/svg"}
            self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
            self.assertIsNotNone(root.find("svg:title", namespace))
            self.assertIsNotNone(root.find("svg:desc", namespace))
            self.assertNotIn(b"<script", rendered.lower())
            self.assertNotIn(b"https://", rendered.lower())

        graph = first["qualification-surface.svg"]
        self.assertIn(str(payload["siteMetrics"]["tests"]["methods"]).encode(), graph)
        self.assertIn(b"154", graph)
        self.assertIn(b"126", graph)
        self.assertIn(b"57", graph)

        blueprint = first["speedup-accuracy-by-size-blueprint.svg"]
        self.assertIn(b"HOW FAST?", blueprint)
        self.assertIn(b"HOW ACCURATE?", blueprint)
        self.assertIn(b"1\xc3\x97", blueprint)
        self.assertIn(b"not measured benchmark results", blueprint)

    def test_generated_svg_text_layout_regressions_are_fixed(self) -> None:
        assets = render_svg_assets(build_payload())
        namespace = {"svg": "http://www.w3.org/2000/svg"}

        dc_link = ET.fromstring(assets["circuit-dc-link-rlc.svg"])
        dc_link_text = {
            "".join(element.itertext()): element
            for element in dc_link.findall(".//svg:text", namespace)
        }
        bleed_x = float(dc_link_text["R_PRELINK_BLEED"].attrib["x"])
        capacitor_x = float(dc_link_text["C_LINK"].attrib["x"])
        self.assertEqual(dc_link_text["R_PRELINK_BLEED"].attrib["text-anchor"], "start")
        self.assertEqual(dc_link_text["C_LINK"].attrib["text-anchor"], "start")
        self.assertGreaterEqual(capacitor_x - bleed_x, 200)

        diode = assets["circuit-diode-clip.svg"]
        self.assertIn(b"1 V sine \xc2\xb7 1 kHz", diode)
        self.assertNotIn(b"1000 Hz", diode)

        observatory = assets["result-observatory-accuracy-work.svg"]
        self.assertIn(b"log10 work units", observatory)
        for name in (
            "result-observatory-accuracy-work.svg",
            "result-coverage-by-age.svg",
            "result-rejection-causes.svg",
        ):
            with self.subTest(asset=name):
                self.assertIn(b'transform="rotate(-90', assets[name])

        self.assertIn(b"Mapped ngspice check", assets["external-comparison.svg"])
        self.assertIn(b"20 CASES", assets["external-comparison.svg"])

    def test_ten_tutorial_documents_embed_ten_owned_svg_explanations(self) -> None:
        tutorial_paths = sorted((DOCS_ROOT / "tutorials").glob("*.md"))
        self.assertEqual(len(tutorial_paths), 10)
        tutorial_assets = TUTORIAL_SVG_ASSET_NAMES[:10]
        observed_data_markers = (
            "Initial capacitor-voltage derivative",
            "2.0011734866053392",
            "0.9805531365134604",
            "1.3877787807814457e-17",
            "ca5d648e60dfd9923deadc85fb304b45dc9ecf87aecc982a369d3766542806f2",
            "source_tree_excluded: true",
            "0.0009000000000000001",
            "17.904031990116184",
            "Rejected candidate steps",
            "3.730147981349861",
        )
        for index, (path, asset) in enumerate(
            zip(tutorial_paths, tutorial_assets, strict=True),
            start=1,
        ):
            with self.subTest(tutorial=index, path=path.name, asset=asset):
                markdown = path.read_text(encoding="utf-8")
                self.assertIn(f"html/assets/{asset}", markdown)
                self.assertIn("## What You Will Learn", markdown)
                self.assertIn("## Run", markdown)
                self.assertIn("## Expected Results", markdown)
                self.assertIn("## Observed Data", markdown)
                self.assertIn("## Expected Versus Actual Results", markdown)
                self.assertIn("## Theory and Practical Outcomes", markdown)
                self.assertIn("## Conclusion", markdown)
                self.assertIn("August 27, 2026", markdown)
                self.assertIn(observed_data_markers[index - 1], markdown)
                self.assertIn("## Claim Boundary", markdown)

        report = (DOCS_ROOT / "TUTORIAL_SCIENTIFIC_RESULTS_REPORT.md").read_text(
            encoding="utf-8"
        )
        for heading in (
            "## Abstract",
            "## Expected Results",
            "## Actual Results",
            "## Reasons Expected and Actual Results Differed",
            "## Theory and Practical Outcomes",
            "## Conclusions",
            "## Claim Boundary",
        ):
            with self.subTest(scientific_report_heading=heading):
                self.assertIn(heading, report)
        self.assertIn("0` of `17", report)
        self.assertIn("3.730147981349861", report)
        self.assertIn("all_passed: true", report)
        self.assertIn("release qualification", report)
        for asset in (
            "authority-loop.svg",
            "tutorial-02-convergence.svg",
            "tutorial-03-phase-energy.svg",
            "tutorial-08-bound-coverage.svg",
            "tutorial-09-fallback-forensics.svg",
            "ngspice-error-overview.svg",
        ):
            with self.subTest(scientific_report_svg=asset):
                self.assertIn(f"html/assets/{asset}", report)

        mapping_tutorial = tutorial_paths[-1].read_text(encoding="utf-8")
        manifest = json.loads(EXTERNAL_MANIFEST.read_text(encoding="utf-8"))
        for case in manifest["cases"]:
            with self.subTest(mapped_case=case["id"]):
                self.assertIn(f"| `{case['id']}` |", mapping_tutorial)
        reference = json.loads(EXTERNAL_REFERENCE.read_text(encoding="utf-8"))
        mapping_rows = {}
        for line in mapping_tutorial.splitlines():
            if not line.startswith("| `"):
                continue
            cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
            if len(cells) == 4 and cells[0] in {case["id"] for case in reference["cases"]}:
                mapping_rows[cells[0]] = cells[1:]
        for case in reference["cases"]:
            with self.subTest(mapped_case_data=case["id"]):
                maximum, rms, samples = mapping_rows[case["id"]]
                self.assertTrue(
                    math.isclose(
                        float(maximum),
                        case["maximum_absolute_error"],
                        rel_tol=1.0e-15,
                        abs_tol=1.0e-18,
                    )
                )
                self.assertTrue(
                    math.isclose(
                        float(rms),
                        case["maximum_rms_absolute_error"],
                        rel_tol=1.0e-15,
                        abs_tol=1.0e-18,
                    )
                )
                self.assertEqual(int(samples), case["sample_count"])

        atlas = (DOCS_ROOT / "NGSPICE_CASE_ATLAS.md").read_text(encoding="utf-8")
        for asset in TUTORIAL_SVG_ASSET_NAMES[10:]:
            self.assertIn(f"html/assets/{asset}", atlas)
        self.assertIn("20 cases", atlas)
        self.assertIn("81 files", atlas)

    def test_circuit_and_result_figures_retain_source_and_claim_boundaries(self) -> None:
        assets = render_svg_assets(build_payload())
        paired_assets = {
            "rc_step": ("circuit-rc-step.svg", "result-rc-step.svg"),
            "rl_step": ("circuit-rl-step.svg", "result-rl-step.svg"),
            "rlc_damped": ("circuit-rlc-damped.svg", "result-rlc-damped.svg"),
            "lc_long": ("circuit-lc-long.svg", "result-lc-long.svg"),
            "diode_clip": ("circuit-diode-clip.svg", "result-diode-clip.svg"),
            "switched_rc": ("circuit-switched-rc.svg", "result-switched-rc.svg"),
            "buck_like": ("circuit-buck-like.svg", "result-buck-like.svg"),
            "h_bridge_rl": ("circuit-h-bridge-rl.svg", "result-h-bridge-rl.svg"),
            "dc_link_rlc": ("circuit-dc-link-rlc.svg", "result-dc-link-rlc.svg"),
        }

        for case_id, names in paired_assets.items():
            source_path = CASE_PATHS[case_id]
            source_sha = hashlib.sha256(
                (REPOSITORY_ROOT / source_path).read_bytes()
            ).hexdigest()[:16]
            for name in names:
                with self.subTest(case=case_id, asset=name):
                    rendered = assets[name]
                    self.assertIn(source_path.as_posix().encode(), rendered)
                    self.assertIn(source_sha.encode(), rendered)
            self.assertIn(b"METHOD", assets[names[1]])
            self.assertIn(b"NOMINAL STEP", assets[names[1]])
            self.assertIn(b"ACCEPTED POINTS", assets[names[1]])

        for name in (
            "circuit-buck-like.svg",
            "result-buck-like.svg",
            "circuit-h-bridge-rl.svg",
            "result-h-bridge-rl.svg",
            "circuit-dc-link-rlc.svg",
            "result-dc-link-rlc.svg",
            "result-rejection-causes.svg",
        ):
            with self.subTest(asset=name):
                self.assertIn(b"reduced-order", assets[name].lower())

        self.assertIn(b"actual authority error", assets["result-bound-coverage.svg"])
        self.assertIn(b"recursive internal bound", assets["result-bound-coverage.svg"])
        self.assertIn(b"empirical coverage", assets["result-coverage-by-age.svg"])
        self.assertIn(b"phase error", assets["result-phase-energy.svg"])
        self.assertIn(b"relative energy error", assets["result-phase-energy.svg"])
        self.assertIn(b"candidate nonconvergence", assets["result-rejection-causes.svg"])
        self.assertIn(b"reference nonconvergence", assets["result-rejection-causes.svg"])

    def test_document_pages_embed_all_generated_circuit_and_result_figures(self) -> None:
        markdown_by_path = {
            "METHOD_OBSERVATORY.md": (DOCS_ROOT / "METHOD_OBSERVATORY.md").read_text(
                encoding="utf-8"
            ),
            "BOUND_COVERAGE_ATLAS.md": (
                DOCS_ROOT / "BOUND_COVERAGE_ATLAS.md"
            ).read_text(encoding="utf-8"),
            "POWER_STAGE_SANDBOX.md": (
                DOCS_ROOT / "POWER_STAGE_SANDBOX.md"
            ).read_text(encoding="utf-8"),
        }
        expected_by_path = {
            "METHOD_OBSERVATORY.md": FIGURE_ASSET_NAMES[:12]
            + ("result-observatory-accuracy-work.svg",),
            "BOUND_COVERAGE_ATLAS.md": FIGURE_ASSET_NAMES[19:23],
            "POWER_STAGE_SANDBOX.md": FIGURE_ASSET_NAMES[12:18],
        }

        for path, expected_names in expected_by_path.items():
            for name in expected_names:
                with self.subTest(document=path, asset=name):
                    self.assertIn(f"html/assets/{name}", markdown_by_path[path])

        javascript = (HTML_ROOT / "app.js").read_text(encoding="utf-8")
        stylesheet = (HTML_ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertIn("standaloneImage", javascript)
        self.assertIn("function imageSource", javascript)
        self.assertIn('replace(/^(?:\\.\\/)?html\\//i, "")', javascript)
        self.assertIn("document-figure", javascript)
        self.assertIn("<figcaption>", javascript)
        self.assertIn("window.document.getElementById(section)", javascript)
        self.assertIn("function scrollDocumentTarget", javascript)
        self.assertIn('root.style.scrollBehavior = "auto"', javascript)
        self.assertIn(".document-figure", stylesheet)
        self.assertGreaterEqual(stylesheet.count("scroll-margin-top: 90px"), 2)

    def test_landing_page_links_every_featured_document_and_diagram(self) -> None:
        payload = build_payload()
        javascript = (HTML_ROOT / "app.js").read_text(encoding="utf-8")
        documents_javascript = (HTML_ROOT / "documents.js").read_text(encoding="utf-8")

        for path in payload["featuredDocuments"]:
            self.assertIn(path, javascript)
        for asset in CONCEPTUAL_SVG_ASSET_NAMES:
            self.assertIn(f'assets/{asset}', javascript)
        for asset in FIGURE_ASSET_NAMES:
            self.assertIn(f'html/assets/{asset}', documents_javascript)
        for asset in TUTORIAL_SVG_ASSET_NAMES:
            self.assertIn(f'html/assets/{asset}', documents_javascript)

    def test_all_bracketed_reference_citations_have_renderer_support(self) -> None:
        payload = build_payload()
        citation_count = sum(
            document["markdown"].count("](REFERENCES.md#ref-")
            for document in payload["documents"]
        )
        javascript = (HTML_ROOT / "app.js").read_text(encoding="utf-8")

        self.assertGreater(citation_count, 0)
        self.assertIn(r"\[\[([^\]]+)\]\]\(([^)]+)\)", javascript)

    def test_generator_check_mode_accepts_the_committed_payload(self) -> None:
        completed = subprocess.run(
            [sys.executable, "tools/build_docs_html.py", "--check"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn('"assets": 43', completed.stdout)
        self.assertIn('"documents": 40', completed.stdout)

    def test_redesign_plan_records_requirements_issue_loop_and_completion_gates(self) -> None:
        plan = (REPOSITORY_ROOT / "HTML_DOCUMENT_REDESIGN_AND_REWRITE_PLAN.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## Requirements", plan)
        self.assertIn("## Educational Contract", plan)
        self.assertIn("## Issue and Correction Loop", plan)
        self.assertIn("## Completion Criteria", plan)
        self.assertIn("## Completion Audit", plan)
        self.assertIn("every `docs/*.md` file", plan)
        self.assertIn("zero unexplained acronyms", plan)

    def test_intext_learning_plan_records_review_rewrite_and_fix_loop(self) -> None:
        plan_path = REPOSITORY_ROOT / "INTEXT_LEARNING_GUIDE_AND_NOVICE_ESSAY_PLAN.md"
        plan = plan_path.read_text(encoding="utf-8")
        docs_index = (DOCS_ROOT / "index.md").read_text(encoding="utf-8")

        self.assertIn("## Current-State Review", plan)
        self.assertIn("## In-Text Educational Contract", plan)
        self.assertIn("## Selected Essay Rewrite", plan)
        self.assertIn("## Problem and Fix Loop", plan)
        self.assertIn("## Completion Criteria", plan)
        self.assertIn("NUMERICAL_METHODS_ESSAY.md", plan)
        self.assertIn("ENGINEERING_AND_PERFORMANCE_ESSAY.md", plan)
        self.assertIn("VALIDATION_RELEASE_AND_CLAIMS_ESSAY.md", plan)
        self.assertIn("INTEXT_LEARNING_GUIDE_AND_NOVICE_ESSAY_PLAN.md", docs_index)

    def test_ngspice_runtime_plan_records_fairness_metrics_and_chart_contract(self) -> None:
        plan_path = REPOSITORY_ROOT / "BABCS_NGSPICE_RUNTIME_BENCHMARK_PLAN.md"
        plan = plan_path.read_text(encoding="utf-8")
        docs_index = (DOCS_ROOT / "index.md").read_text(encoding="utf-8")

        for heading in (
            "## Purpose",
            "## Non-Negotiable Comparison Contract",
            "## Benchmark Inventory",
            "## Measurement Model",
            "## Required Metrics",
            "## The Headline Chart",
            "## Implementation Work Packages",
            "## Tests",
            "## Completion Criteria",
            "## Claim Boundary",
        ):
            with self.subTest(runtime_plan_heading=heading):
                self.assertIn(heading, plan)
        for requirement in (
            "same physical machine",
            "same stop time",
            "median_ngspice_analysis_seconds / median_babcs_analysis_seconds",
            "### Accepted and output points",
            "### Solver work",
            "### Peak memory",
            "### Trajectory accuracy",
            "How fast?",
            "How accurate?",
            "1×",
            "maximum resident set size",
            "rusage all",
            "speedup-accuracy-by-size.svg",
            "speedup-accuracy-by-size-blueprint.svg",
        ):
            with self.subTest(runtime_plan_requirement=requirement):
                self.assertIn(requirement, plan)
        self.assertIn("BABCS_NGSPICE_RUNTIME_BENCHMARK_PLAN.md", docs_index)

    def test_svg_figure_plan_records_inventory_loop_and_completion_audit(self) -> None:
        plan = (
            REPOSITORY_ROOT / "SVG_CIRCUIT_AND_SIMULATION_FIGURES_IMPLEMENTATION_PLAN.md"
        ).read_text(encoding="utf-8")

        self.assertIn("## Figure Inventory", plan)
        self.assertIn("## Report and Correction Loop", plan)
        self.assertIn("## Completion Criteria", plan)
        self.assertIn("## Completion Audit", plan)
        self.assertIn("23 new SVG figures", plan)
        self.assertIn("29 SVG assets", plan)
        self.assertIn("300 tests", plan)
        self.assertIn("Problem and Correction Record", plan)
        self.assertIn("reduced-order numerical experiments", plan)

    def test_ourd_redesign_plan_records_governed_review_and_completion_gates(self) -> None:
        plan_path = REPOSITORY_ROOT / "OURD_HTML_TREE_VISUAL_GRAMMAR_REDESIGN_PLAN.md"
        plan = plan_path.read_text(encoding="utf-8")
        docs_index = (DOCS_ROOT / "index.md").read_text(encoding="utf-8")

        self.assertIn("## Governed OURD Review", plan)
        self.assertIn("Instrument Panel for Bounded Authority", plan)
        self.assertIn("## Visual Design Contract", plan)
        self.assertIn("## Grammar Contract", plan)
        self.assertIn("## Problems and Adjustments", plan)
        self.assertIn("## Completion Criteria", plan)
        self.assertIn("## Completion Audit", plan)
        self.assertIn("passes 297 tests with 2 intentional skips", plan)
        self.assertIn("no mutation authority", plan)
        self.assertIn("OURD_HTML_TREE_VISUAL_GRAMMAR_REDESIGN_PLAN.md", docs_index)


if __name__ == "__main__":
    unittest.main()
