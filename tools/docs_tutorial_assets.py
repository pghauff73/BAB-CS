from __future__ import annotations

import hashlib
import html
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_MANIFEST = REPOSITORY_ROOT / "benchmarks/external/manifest.json"
EXTERNAL_REFERENCE = REPOSITORY_ROOT / "benchmarks/external/reference-results.json"
LAB_FIXTURE = REPOSITORY_ROOT / "lab/fixtures/verification-baseline.json"

TUTORIAL_SVG_ASSET_NAMES = (
    "tutorial-01-mna.svg",
    "tutorial-02-convergence.svg",
    "tutorial-03-phase-energy.svg",
    "tutorial-04-shadow-authority.svg",
    "tutorial-05-deterministic-packaging.svg",
    "tutorial-06-source-wheel-equivalence.svg",
    "tutorial-07-event-alignment.svg",
    "tutorial-08-bound-coverage.svg",
    "tutorial-09-fallback-forensics.svg",
    "tutorial-10-ngspice-mapping.svg",
    "ngspice-case-atlas.svg",
    "ngspice-feature-coverage.svg",
    "ngspice-error-overview.svg",
)


def _svg_document(
    title: str,
    description: str,
    body: str,
    *,
    width: int = 1200,
    height: int = 650,
) -> bytes:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title description" viewBox="0 0 {width} {height}">
  <title id="title">{html.escape(title)}</title>
  <desc id="description">{html.escape(description)}</desc>
  <defs>
    <linearGradient id="brand" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b7185"/><stop offset="1" stop-color="#174e63"/></linearGradient>
    <linearGradient id="warm" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e1883b"/><stop offset="1" stop-color="#a6501d"/></linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="7" stdDeviation="9" flood-color="#10243a" flood-opacity="0.13"/></filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="#4c7283"/></marker>
    <style>
      .sans {{ font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
      .title {{ fill:#10243a; font-size:29px; font-weight:820; letter-spacing:-0.02em; }}
      .subtitle {{ fill:#60758a; font-size:15px; }}
      .label {{ fill:#10243a; font-size:16px; font-weight:760; }}
      .small {{ fill:#5e7388; font-size:13px; }}
      .micro {{ fill:#74879a; font-size:10.5px; font-weight:720; letter-spacing:0.045em; }}
      .box {{ fill:#fff; stroke:#d2dee8; stroke-width:1.5; }}
      .soft {{ fill:#ebf6f8; stroke:#add3dd; stroke-width:1.5; }}
      .warm {{ fill:#fff2e6; stroke:#edbd8f; stroke-width:1.5; }}
      .line {{ fill:none; stroke:#4c7283; stroke-width:2.2; marker-end:url(#arrow); }}
      .grid {{ stroke:#d9e4ec; stroke-width:1; }}
    </style>
  </defs>
{body}
</svg>
'''.encode("utf-8")


def _flow_asset(
    title: str,
    subtitle: str,
    stages: list[tuple[str, str, str]],
    footer_title: str,
    footer_lines: tuple[str, str],
) -> bytes:
    width = 1200
    card_width = 240
    gap = 45
    start = 52
    parts = [
        '<rect width="1200" height="650" rx="28" fill="#f5f8fb"/>',
        f'<text class="sans title" x="60" y="66">{html.escape(title)}</text>',
        f'<text class="sans subtitle" x="60" y="100">{html.escape(subtitle)}</text>',
    ]
    for index, (micro, label, explanation) in enumerate(stages):
        x = start + index * (card_width + gap)
        card_class = "soft" if index in {0, 3} else "box"
        parts.extend(
            [
                f'<rect class="{card_class}" x="{x}" y="178" width="{card_width}" height="170" rx="18" filter="url(#shadow)"/>',
                f'<text class="sans micro" x="{x + 20}" y="210">{html.escape(micro)}</text>',
                f'<text class="sans label" x="{x + 20}" y="244">{html.escape(label)}</text>',
                f'<text class="sans small" x="{x + 20}" y="276">{html.escape(explanation)}</text>',
            ]
        )
        if index < len(stages) - 1:
            parts.append(
                f'<path class="line" d="M{x + card_width} 263 H{x + card_width + gap - 10}"/>'
            )
    parts.extend(
        [
            '<rect x="60" y="430" width="1080" height="140" rx="18" fill="#11344a"/>',
            f'<text class="sans" x="88" y="468" fill="#ffffff" font-size="16" font-weight="800">{html.escape(footer_title)}</text>',
            f'<text class="sans" x="88" y="505" fill="#d8e7ef" font-size="14">{html.escape(footer_lines[0])}</text>',
            f'<text class="sans" x="88" y="535" fill="#d8e7ef" font-size="14">{html.escape(footer_lines[1])}</text>',
        ]
    )
    return _svg_document(title, subtitle, "\n  ".join(parts), width=width, height=650)


def _fixture_exercise(exercise_id: str) -> dict[str, Any]:
    fixture = json.loads(LAB_FIXTURE.read_text(encoding="utf-8"))
    return next(item["evidence"] for item in fixture["exercises"] if item["id"] == exercise_id)


def _mna_svg() -> bytes:
    return _flow_asset(
        "Tutorial 1 · Modified nodal analysis state ownership",
        "Modified nodal analysis separates stored-energy state from node-voltage and branch-current constraints.",
        [
            ("DECLARED CIRCUIT", "R, C, and source", "Components define equations."),
            ("DYNAMIC STATE", "Capacitor voltage", "Stored energy advances in time."),
            ("ALGEBRAIC SOLVE", "Nodes and source current", "Constraints restore consistency."),
            ("DERIVATIVE", "State rate", "The consistent slope feeds the integrator."),
        ],
        "Why the separation matters",
        (
            "A node voltage may equal a capacitor voltage in one simple circuit, but the concepts are not interchangeable.",
            "BAB-CS supervises the dynamic state while projection keeps the complete circuit equations consistent.",
        ),
    )


def _convergence_svg() -> bytes:
    evidence = _fixture_exercise("02-convergence")
    steps = [float(value) for value in evidence["steps"]]
    errors = [float(value) for value in evidence["maximum_errors"]]
    left, right, top, bottom = 130.0, 1080.0, 175.0, 500.0
    x_values = [math.log10(value) for value in steps]
    y_values = [math.log10(value) for value in errors]
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)

    def x_coord(value: float) -> float:
        return left + (value - x_min) / (x_max - x_min) * (right - left)

    def y_coord(value: float) -> float:
        return bottom - (value - y_min) / (y_max - y_min) * (bottom - top)

    points = [(x_coord(x), y_coord(y)) for x, y in zip(x_values, y_values, strict=True)]
    path = " ".join(
        ("M" if index == 0 else "L") + f"{x:.2f} {y:.2f}"
        for index, (x, y) in enumerate(points)
    )
    body = [
        '<rect width="1200" height="650" rx="28" fill="#f5f8fb"/>',
        '<text class="sans title" x="60" y="66">Tutorial 2 · Convergence by measured refinement</text>',
        '<text class="sans subtitle" x="60" y="100">A convergence claim requires a repeated error trend as the fixed timestep becomes smaller.</text>',
        '<rect class="box" x="60" y="138" width="1080" height="420" rx="18"/>',
    ]
    for index in range(5):
        y = top + index * (bottom - top) / 4
        body.append(f'<path class="grid" d="M{left} {y:.2f} H{right}"/>')
    body.append(f'<path d="{path}" fill="none" stroke="#0b7185" stroke-width="4"/>')
    for index, ((x, y), step, error) in enumerate(zip(points, steps, errors, strict=True), start=1):
        body.extend(
            [
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="9" fill="#d9782d"/>',
                f'<text class="sans small" x="{x:.2f}" y="{y - 18:.2f}" text-anchor="middle">h{index}: {step:.2g} s</text>',
                f'<text class="sans micro" x="{x:.2f}" y="{y + 28:.2f}" text-anchor="middle">error {error:.3g}</text>',
            ]
        )
    body.extend(
        [
            '<text class="sans small" x="605" y="542" text-anchor="middle">log10 fixed timestep</text>',
            '<text class="sans small" x="92" y="340" text-anchor="middle" transform="rotate(-90 92 340)">log10 maximum error</text>',
            f'<text class="sans label" x="760" y="166">Measured orders: {", ".join(f"{value:.3f}" for value in evidence["observed_orders"])}</text>',
        ]
    )
    return _svg_document(
        "Tutorial 2 convergence graph",
        "A log-scale graph of maximum RC error decreasing over three fixed-step refinements, with measured convergence orders.",
        "\n  ".join(body),
    )


def _phase_energy_svg() -> bytes:
    methods = _fixture_exercise("03-phase-versus-energy")["methods"]
    body = '''  <rect width="1200" height="650" rx="28" fill="#f5f8fb"/>
  <text class="sans title" x="60" y="66">Tutorial 3 · Phase error and energy error answer different questions</text>
  <text class="sans subtitle" x="60" y="100">Phase measures timing around an oscillation; energy measures stored electrical quantity.</text>
  <rect class="box" x="60" y="145" width="520" height="390" rx="18"/>
  <rect class="soft" x="620" y="145" width="520" height="390" rx="18"/>
  <text class="sans label" x="90" y="185">Final phase error</text>
  <text class="sans label" x="650" y="185">Relative energy behavior</text>'''
    parts = [body]
    method_items = list(methods.items())
    phase_max = max(float(values["final_phase_error_radians"]) for _, values in method_items)
    energy_max = max(float(values["relative_energy_span"]) for _, values in method_items)
    colors = ("#d9782d", "#0b7185")
    for index, ((method, values), color) in enumerate(zip(method_items, colors, strict=True)):
        y = 240 + index * 125
        phase_width = 390 * float(values["final_phase_error_radians"]) / phase_max
        energy_width = 390 * float(values["relative_energy_span"]) / energy_max
        parts.extend(
            [
                f'<text class="sans small" x="90" y="{y}">{html.escape(method.replace("_", " "))}</text>',
                f'<rect x="90" y="{y + 18}" width="390" height="28" rx="8" fill="#e4edf3"/>',
                f'<rect x="90" y="{y + 18}" width="{phase_width:.2f}" height="28" rx="8" fill="{color}"/>',
                f'<text class="sans micro" x="500" y="{y + 39}" text-anchor="end">{float(values["final_phase_error_radians"]):.5g} rad</text>',
                f'<text class="sans small" x="650" y="{y}">{html.escape(method.replace("_", " "))}</text>',
                f'<rect x="650" y="{y + 18}" width="390" height="28" rx="8" fill="#e4edf3"/>',
                f'<rect x="650" y="{y + 18}" width="{energy_width:.2f}" height="28" rx="8" fill="{color}"/>',
                f'<text class="sans micro" x="1060" y="{y + 39}" text-anchor="end">span {float(values["relative_energy_span"]):.5g}</text>',
            ]
        )
    parts.append('<text class="sans small" x="600" y="590" text-anchor="middle">Low energy drift does not imply zero phase drift, and damping may reduce energy while changing timing.</text>')
    return _svg_document(
        "Tutorial 3 phase and energy comparison",
        "Side-by-side bars compare phase error and relative energy span for backward Euler and trapezoidal integration.",
        "\n  ".join(parts),
    )


def _shadow_svg() -> bytes:
    return _flow_asset(
        "Tutorial 4 · Shadow authority keeps observation separate from acceptance",
        "Shadow mode runs a candidate for diagnostics while the implicit reference still owns every accepted state.",
        [
            ("CURRENT STATE", "Trusted input", "One accepted state starts both paths."),
            ("CANDIDATE LANE", "Proposal only", "Work and defects are observed."),
            ("IMPLICIT LANE", "Accepted authority", "The independent solve owns state."),
            ("EVIDENCE", "Compare without promotion", "Diagnostics remain visible."),
        ],
        "Plain-language rule",
        (
            "Seeing a candidate trajectory is not the same as accepting it.",
            "Shadow mode supports method study without silently transferring authority to the method under study.",
        ),
    )


def _packaging_svg() -> bytes:
    return _flow_asset(
        "Tutorial 5 · Deterministic packaging",
        "A deterministic wheel repeats byte-for-byte when the declared source and build contract are unchanged.",
        [
            ("FROZEN SOURCE", "One exact tree", "Files, modes, and version are fixed."),
            ("BUILD A", "Wheel archive A", "Sorted members and fixed metadata."),
            ("BUILD B", "Wheel archive B", "Independent repeat of the build."),
            ("HASH CHECK", "Bytes must match", "SHA-256 identifies exact content."),
        ],
        "What matching hashes prove",
        (
            "They prove the two package files are byte-identical under the measured build conditions.",
            "They do not prove numerical correctness, release approval, or equivalence on every optional backend.",
        ),
    )


def _equivalence_svg() -> bytes:
    return _flow_asset(
        "Tutorial 6 · Source and installed-wheel equivalence",
        "The same declared cases run through source, an isolated installed module, and the installed console command.",
        [
            ("SOURCE RUN", "Repository module", "Run outside packaging shortcuts."),
            ("WHEEL MODULE", "Isolated import", "No repository path may leak in."),
            ("CONSOLE RUN", "Installed command", "Exercise the user-facing entry point."),
            ("ARTIFACT CHECK", "Trace and summary", "Every compared byte must agree."),
        ],
        "Why three paths are useful",
        (
            "A correct source run can still be packaged incorrectly or exposed through a different console configuration.",
            "Equivalence evidence closes those distribution seams for the selected cases, not for all possible environments.",
        ),
    )


def _event_svg() -> bytes:
    evidence = _fixture_exercise("07-event-alignment")
    events = [float(value) for value in evidence["accepted_event_times"]]
    left, right, y = 110.0, 1090.0, 315.0
    stop = max(events)
    parts = [
        '<rect width="1200" height="650" rx="28" fill="#f5f8fb"/>',
        '<text class="sans title" x="60" y="66">Tutorial 7 · Exact event alignment and restart</text>',
        '<text class="sans subtitle" x="60" y="100">A scheduled topology change is an integration boundary, not an ordinary point inside a long step.</text>',
        '<rect class="box" x="60" y="150" width="1080" height="340" rx="18"/>',
        f'<path d="M{left} {y} H{right}" stroke="#4c7283" stroke-width="4"/>',
    ]
    for index, event in enumerate(events, start=1):
        x = left + event / stop * (right - left)
        parts.extend(
            [
                f'<path d="M{x:.2f} 220 V410" stroke="#d9782d" stroke-width="3" stroke-dasharray="7 6"/>',
                f'<circle cx="{x:.2f}" cy="{y}" r="9" fill="#0b7185"/>',
                f'<text class="sans micro" x="{x:.2f}" y="200" text-anchor="middle">EVENT {index}</text>',
                f'<text class="sans small" x="{x:.2f}" y="438" text-anchor="middle">{event * 1e6:.0f} µs</text>',
            ]
        )
    parts.extend(
        [
            '<text class="sans label" x="110" y="535">At each event</text>',
            '<text class="sans small" x="110" y="566">Land exactly → accept the boundary solve → reset multistep history → take a startup step.</text>',
            f'<text class="sans micro" x="1090" y="535" text-anchor="end">{evidence["event_count"]} aligned events · {evidence["startup_steps_after_events"]} post-event startup steps</text>',
        ]
    )
    return _svg_document(
        "Tutorial 7 event-alignment timeline",
        "A timeline marks five exact switch events and explains the multistep-history restart sequence.",
        "\n  ".join(parts),
    )


def _coverage_svg() -> bytes:
    evidence = _fixture_exercise("08-bound-coverage")
    maximum_error = float(evidence["maximum_authority_epoch_drift_error"])
    maximum_bound = float(evidence["maximum_recursive_internal_bound"])
    maximum = max(maximum_error, maximum_bound)
    error_height = 265 * maximum_error / maximum
    bound_height = 265 * maximum_bound / maximum
    body = f'''  <rect width="1200" height="650" rx="28" fill="#f5f8fb"/>
  <text class="sans title" x="60" y="66">Tutorial 8 · Empirical coverage is measured, not assumed</text>
  <text class="sans subtitle" x="60" y="100">The authority-epoch drift error is compared with the recursive internal bound only on eligible samples.</text>
  <rect class="box" x="60" y="145" width="680" height="390" rx="18"/>
  <rect class="soft" x="780" y="145" width="360" height="390" rx="18"/>
  <path class="grid" d="M130 470 H670"/>
  <rect x="235" y="{470 - error_height:.2f}" width="130" height="{error_height:.2f}" rx="12" fill="#d9782d"/>
  <rect x="455" y="{470 - bound_height:.2f}" width="130" height="{bound_height:.2f}" rx="12" fill="#0b7185"/>
  <text class="sans label" x="300" y="505" text-anchor="middle">actual drift error</text>
  <text class="sans label" x="520" y="505" text-anchor="middle">recursive bound</text>
  <text class="sans micro" x="300" y="{455 - error_height:.2f}" text-anchor="middle">{maximum_error:.4g}</text>
  <text class="sans micro" x="520" y="{455 - bound_height:.2f}" text-anchor="middle">{maximum_bound:.4g}</text>
  <text class="sans micro" x="960" y="205" text-anchor="middle">ELIGIBLE SAMPLES</text>
  <text class="sans" x="960" y="285" fill="#10243a" font-size="58" font-weight="850" text-anchor="middle">{evidence["eligible_samples"]}</text>
  <text class="sans micro" x="960" y="345" text-anchor="middle">COVERED SAMPLES</text>
  <text class="sans" x="960" y="425" fill="#d9782d" font-size="58" font-weight="850" text-anchor="middle">{evidence["covered_samples"]}</text>
  <text class="sans small" x="600" y="585" text-anchor="middle">A low measured ratio is diagnostic evidence that the current internal model is not a formal enclosure.</text>'''
    return _svg_document(
        "Tutorial 8 empirical bound-coverage graph",
        "Bars compare the maximum authority-epoch drift error with the recursive internal bound, alongside eligible and covered sample counts.",
        body,
    )


def _fallback_svg() -> bytes:
    evidence = _fixture_exercise("09-fallback-forensics")
    values = [
        ("rejected steps", int(evidence["rejected_steps"]), "#d9782d"),
        ("implicit fallbacks", int(evidence["implicit_fallbacks"]), "#0b7185"),
        ("event resets", int(evidence["history_resets"]["event"]), "#6856a8"),
        ("periodic reanchors", int(evidence["history_resets"]["periodic_reanchor"]), "#2f8f68"),
    ]
    maximum = max(value for _, value, _ in values)
    parts = [
        '<rect width="1200" height="650" rx="28" fill="#f5f8fb"/>',
        '<text class="sans title" x="60" y="66">Tutorial 9 · Rejection and fallback forensics</text>',
        '<text class="sans subtitle" x="60" y="100">Rejected proposals remain evidence; the accepted reduced-order H-bridge trajectory continues under bounded authority.</text>',
        '<rect class="box" x="60" y="145" width="1080" height="390" rx="18"/>',
    ]
    for index, (label, value, color) in enumerate(values):
        y = 195 + index * 78
        width = 750 * value / maximum
        parts.extend(
            [
                f'<text class="sans label" x="95" y="{y + 25}">{html.escape(label)}</text>',
                f'<rect x="315" y="{y}" width="760" height="42" rx="10" fill="#e4edf3"/>',
                f'<rect x="315" y="{y}" width="{width:.2f}" height="42" rx="10" fill="{color}"/>',
                f'<text class="sans label" x="1095" y="{y + 27}" text-anchor="end">{value}</text>',
            ]
        )
    causes = ", ".join(
        f"{name}: {count}" for name, count in evidence["rejection_causes"].items()
    )
    parts.extend(
        [
            f'<text class="sans small" x="80" y="575">Observed rejection causes: {html.escape(causes)}.</text>',
            '<text class="sans micro" x="1120" y="575" text-anchor="end">REDUCED-ORDER NUMERICAL EXPERIMENT · NOT A PRODUCTION DEVICE MODEL</text>',
        ]
    )
    return _svg_document(
        "Tutorial 9 fallback-forensics graph",
        "Horizontal bars show rejected steps, implicit fallbacks, event resets, and periodic reanchors for the reduced-order H-bridge exercise.",
        "\n  ".join(parts),
    )


def _mapping_svg() -> bytes:
    return _flow_asset(
        "Tutorial 10 · Semantic mapping to ngspice",
        "Twenty declared BAB-CS cases are translated without changing state ownership, component values, waveforms, or initial conditions.",
        [
            ("BAB-CS JSON", "Declared model", "Components, schedule, and state."),
            ("MAPPER", "Preserve semantics", "Fail closed on unsupported input."),
            ("NGSPICE NETLIST", "Independent program", "Write matching state vectors."),
            ("COMPARISON", "Retain differences", "Report values, hashes, and scope."),
        ],
        "Cross-implementation evidence",
        (
            "Agreement supports implementation consistency for the declared mapping; disagreement identifies work to investigate.",
            "Neither outcome makes ngspice an oracle, and the three power-stage cases remain reduced-order experiments.",
        ),
    )


def _case_atlas_svg() -> bytes:
    manifest = json.loads(EXTERNAL_MANIFEST.read_text(encoding="utf-8"))
    category_labels = {
        "first_order_linear": "First-order linear",
        "resonant_and_rlc": "Resonant and RLC",
        "nonlinear_diode": "Nonlinear diode",
        "scheduled_switching": "Scheduled switching",
        "reduced_order_power_stage": "Reduced-order power stage",
    }
    category_colors = {
        "first_order_linear": "#eaf6f8",
        "resonant_and_rlc": "#eef0fa",
        "nonlinear_diode": "#fff2e6",
        "scheduled_switching": "#eef7f1",
        "reduced_order_power_stage": "#f7edf4",
    }
    parts = [
        '<rect width="1400" height="1030" rx="28" fill="#f5f8fb"/>',
        '<text class="sans title" x="60" y="66">BAB-CS ngspice mapping atlas · 20 declared cases</text>',
        '<text class="sans subtitle" x="60" y="100">Each card names the engineering question class; mapped evidence remains scoped to the declared model and translation.</text>',
    ]
    for index, case in enumerate(manifest["cases"]):
        column = index % 4
        row = index // 4
        x = 55 + column * 337
        y = 135 + row * 158
        category = str(case["category"])
        reduced = bool(case.get("reduced_order", False))
        parts.extend(
            [
                f'<rect x="{x}" y="{y}" width="305" height="130" rx="16" fill="{category_colors[category]}" stroke="#cbd9e4" stroke-width="1.5" filter="url(#shadow)"/>',
                f'<text class="sans micro" x="{x + 18}" y="{y + 26}">{html.escape(category_labels[category].upper())}</text>',
                f'<text class="sans label" x="{x + 18}" y="{y + 56}">{html.escape(str(case["title"]))}</text>',
                f'<text class="sans small" x="{x + 18}" y="{y + 86}">{len(case["mapped_features"])} mapped features · {"reduced order" if reduced else "canonical case"}</text>',
                f'<text class="sans micro" x="{x + 18}" y="{y + 112}">{html.escape(str(case["id"]).upper())}</text>',
            ]
        )
    parts.append('<text class="sans small" x="700" y="982" text-anchor="middle">Coverage spans constant, sine, pulse, and piecewise-linear sources; R, L, C, diode, switch, and mixed initial-state mappings.</text>')
    return _svg_document(
        "BAB-CS ngspice 20-case mapping atlas",
        "A twenty-card atlas groups mapped cases into first-order linear, resonant RLC, nonlinear diode, scheduled switching, and reduced-order power-stage categories.",
        "\n  ".join(parts),
        width=1400,
        height=1030,
    )


def _feature_coverage_svg() -> bytes:
    manifest = json.loads(EXTERNAL_MANIFEST.read_text(encoding="utf-8"))
    counts = Counter(
        str(feature)
        for case in manifest["cases"]
        for feature in case["mapped_features"]
    )
    values = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    maximum = max(counts.values())
    parts = [
        '<rect width="1200" height="900" rx="28" fill="#f5f8fb"/>',
        '<text class="sans title" x="60" y="66">Semantic feature coverage across the 20 mapped cases</text>',
        '<text class="sans subtitle" x="60" y="100">Counts show how many declared cases exercise each translation feature; they are coverage volume, not correctness scores.</text>',
    ]
    for index, (feature, count) in enumerate(values):
        y = 135 + index * 50
        width = 700 * count / maximum
        parts.extend(
            [
                f'<text class="sans small" x="60" y="{y + 25}">{html.escape(feature.replace("_", " "))}</text>',
                f'<rect x="330" y="{y}" width="730" height="34" rx="9" fill="#e2ecf2"/>',
                f'<rect x="330" y="{y}" width="{width:.2f}" height="34" rx="9" fill="url(#brand)"/>',
                f'<text class="sans label" x="1110" y="{y + 24}" text-anchor="end">{count}</text>',
            ]
        )
    return _svg_document(
        "ngspice semantic feature coverage",
        "A horizontal bar graph counts the mapping features exercised by the twenty-case external comparison manifest.",
        "\n  ".join(parts),
        height=900,
    )


def _error_overview_svg() -> bytes:
    reference = json.loads(EXTERNAL_REFERENCE.read_text(encoding="utf-8"))
    actual_manifest_hash = hashlib.sha256(EXTERNAL_MANIFEST.read_bytes()).hexdigest()
    if reference["case_count"] != 20 or reference["manifest_sha256"] != actual_manifest_hash:
        raise ValueError("external reference results do not match the 20-case manifest")
    values = [
        (str(case["id"]), float(case["maximum_absolute_error"]), str(case["category"]))
        for case in reference["cases"]
    ]
    logs = [math.log10(max(value, 1.0e-15)) for _, value, _ in values]
    minimum = math.floor(min(logs))
    maximum = math.ceil(max(logs))
    colors = {
        "first_order_linear": "#0b7185",
        "resonant_and_rlc": "#6856a8",
        "nonlinear_diode": "#d9782d",
        "scheduled_switching": "#2f8f68",
        "reduced_order_power_stage": "#b34e63",
    }
    parts = [
        '<rect width="1400" height="1080" rx="28" fill="#f5f8fb"/>',
        '<text class="sans title" x="60" y="66">Observed maximum absolute differences in the ngspice-46 reference run</text>',
        '<text class="sans subtitle" x="60" y="100">The logarithmic axis makes small and large differences visible together; lower is not a universal tool ranking.</text>',
    ]
    for tick in range(minimum, maximum + 1):
        x = 420 + (tick - minimum) / (maximum - minimum) * 820
        parts.extend(
            [
                f'<path class="grid" d="M{x:.2f} 130 V930"/>',
                f'<text class="sans micro" x="{x:.2f}" y="960" text-anchor="middle">10^{tick}</text>',
            ]
        )
    for index, (case_id, value, category) in enumerate(values):
        y = 135 + index * 39
        width = (math.log10(max(value, 1.0e-15)) - minimum) / (maximum - minimum) * 820
        parts.extend(
            [
                f'<text class="sans small" x="60" y="{y + 23}">{html.escape(case_id)}</text>',
                f'<rect x="420" y="{y}" width="820" height="27" rx="7" fill="#e4edf3"/>',
                f'<rect x="420" y="{y}" width="{max(width, 2.0):.2f}" height="27" rx="7" fill="{colors[category]}"/>',
                f'<text class="sans micro" x="1280" y="{y + 20}" text-anchor="end">{value:.4g}</text>',
            ]
        )
    parts.extend(
        [
            '<text class="sans small" x="700" y="1005" text-anchor="middle">Large differences—especially near switched events—are investigation targets, not hidden failures or proof that one program is wrong.</text>',
            f'<text class="sans micro" x="700" y="1035" text-anchor="middle">REFERENCE: {html.escape(reference["external_tool"]["version"])} · ACTIVE BAB-CS MODE · 20 CASES</text>',
        ]
    )
    return _svg_document(
        "ngspice reference-run error overview",
        "A logarithmic horizontal bar graph shows maximum absolute BAB-CS versus ngspice differences for all twenty mapped cases.",
        "\n  ".join(parts),
        width=1400,
        height=1080,
    )


def render_tutorial_assets() -> dict[str, bytes]:
    assets = {
        "tutorial-01-mna.svg": _mna_svg(),
        "tutorial-02-convergence.svg": _convergence_svg(),
        "tutorial-03-phase-energy.svg": _phase_energy_svg(),
        "tutorial-04-shadow-authority.svg": _shadow_svg(),
        "tutorial-05-deterministic-packaging.svg": _packaging_svg(),
        "tutorial-06-source-wheel-equivalence.svg": _equivalence_svg(),
        "tutorial-07-event-alignment.svg": _event_svg(),
        "tutorial-08-bound-coverage.svg": _coverage_svg(),
        "tutorial-09-fallback-forensics.svg": _fallback_svg(),
        "tutorial-10-ngspice-mapping.svg": _mapping_svg(),
        "ngspice-case-atlas.svg": _case_atlas_svg(),
        "ngspice-feature-coverage.svg": _feature_coverage_svg(),
        "ngspice-error-overview.svg": _error_overview_svg(),
    }
    if tuple(assets) != TUTORIAL_SVG_ASSET_NAMES:
        raise AssertionError("tutorial SVG inventory order drifted")
    return assets
