from __future__ import annotations

import html
import math
from typing import Any

try:
    from tools.docs_figure_assets import FIGURE_ASSET_NAMES, render_figure_assets
    from tools.docs_tutorial_assets import TUTORIAL_SVG_ASSET_NAMES, render_tutorial_assets
except ModuleNotFoundError:
    from docs_figure_assets import FIGURE_ASSET_NAMES, render_figure_assets
    from docs_tutorial_assets import TUTORIAL_SVG_ASSET_NAMES, render_tutorial_assets


CONCEPTUAL_SVG_ASSET_NAMES = (
    "authority-loop.svg",
    "engineering-workflow.svg",
    "evidence-hierarchy.svg",
    "external-comparison.svg",
    "qualification-surface.svg",
    "software-landscape.svg",
)
SVG_ASSET_NAMES = CONCEPTUAL_SVG_ASSET_NAMES + FIGURE_ASSET_NAMES + TUTORIAL_SVG_ASSET_NAMES


def _svg_document(
    title: str,
    description: str,
    body: str,
    *,
    width: int,
    height: int,
) -> bytes:
    rendered = f'''<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title description" viewBox="0 0 {width} {height}">
  <title id="title">{html.escape(title)}</title>
  <desc id="description">{html.escape(description)}</desc>
  <defs>
    <linearGradient id="brand-gradient" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0b6a82"/>
      <stop offset="1" stop-color="#164e63"/>
    </linearGradient>
    <linearGradient id="warm-gradient" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#d98237"/>
      <stop offset="1" stop-color="#9a4d1d"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#10243a" flood-opacity="0.12"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#477083"/>
    </marker>
    <style>
      .sans {{ font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
      .title {{ fill: #10243a; font-size: 28px; font-weight: 800; letter-spacing: -0.02em; }}
      .subtitle {{ fill: #607386; font-size: 15px; }}
      .label {{ fill: #10243a; font-size: 16px; font-weight: 750; }}
      .small {{ fill: #607386; font-size: 13px; }}
      .micro {{ fill: #718397; font-size: 11px; font-weight: 650; letter-spacing: 0.04em; }}
      .box {{ fill: #ffffff; stroke: #d5e0e9; stroke-width: 1.5; }}
      .soft {{ fill: #edf6f8; stroke: #b8d6df; stroke-width: 1.5; }}
      .warm {{ fill: #fff4e9; stroke: #eac6a4; stroke-width: 1.5; }}
      .line {{ fill: none; stroke: #477083; stroke-width: 2.2; marker-end: url(#arrow); }}
      .dash {{ fill: none; stroke: #a6642e; stroke-width: 2; stroke-dasharray: 6 6; marker-end: url(#arrow); }}
    </style>
  </defs>
{body}
</svg>
'''
    return rendered.encode("utf-8")


def _authority_loop_svg() -> bytes:
    body = '''  <rect width="1200" height="650" rx="28" fill="#f5f8fb"/>
  <text class="sans title" x="60" y="66">Bounded authority turns proposals into inspectable accepted states</text>
  <text class="sans subtitle" x="60" y="100">The candidate may be inexpensive or high-order; acceptance remains owned by independent evidence and explicit gates.</text>

  <g filter="url(#shadow)">
    <rect class="soft" x="60" y="160" width="190" height="112" rx="18"/>
    <rect class="box" x="315" y="160" width="190" height="112" rx="18"/>
    <rect class="warm" x="570" y="160" width="190" height="112" rx="18"/>
    <rect class="box" x="825" y="160" width="190" height="112" rx="18"/>
    <rect class="soft" x="825" y="382" width="250" height="116" rx="18"/>
    <rect class="box" x="490" y="382" width="250" height="116" rx="18"/>
    <rect class="warm" x="155" y="382" width="250" height="116" rx="18"/>
  </g>

  <text class="sans micro" x="84" y="190">PROPOSAL</text>
  <text class="sans label" x="84" y="220">Candidate integrator</text>
  <text class="sans small" x="84" y="244">Euler, Heun, Runge-Kutta,</text>
  <text class="sans small" x="84" y="268">Adams, or implicit methods</text>

  <text class="sans micro" x="339" y="190">MODEL CONSISTENCY</text>
  <text class="sans label" x="339" y="220">Circuit-equation projection</text>
  <text class="sans small" x="339" y="244">Restore node and branch</text>
  <text class="sans small" x="339" y="268">constraints; check mismatch</text>

  <text class="sans micro" x="594" y="190">INDEPENDENT CHECK</text>
  <text class="sans label" x="594" y="220">Implicit authority</text>
  <text class="sans small" x="594" y="244">A distinct converged method</text>
  <text class="sans small" x="594" y="268">owns the local comparison</text>

  <text class="sans micro" x="849" y="190">CONTROL</text>
  <text class="sans label" x="849" y="220">Correction and gates</text>
  <text class="sans small" x="849" y="244">Contraction, residual,</text>
  <text class="sans small" x="849" y="268">passivity, stiffness, work</text>

  <text class="sans micro" x="849" y="414">ACCEPTED EVIDENCE</text>
  <text class="sans label" x="849" y="444">State + recursive bound</text>
  <text class="sans small" x="849" y="470">Deterministic diagnostics retain</text>
  <text class="sans small" x="849" y="493">why the step passed or changed</text>

  <text class="sans micro" x="514" y="414">INDEPENDENT REFRESH</text>
  <text class="sans label" x="514" y="444">Periodic refined replay</text>
  <text class="sans small" x="514" y="470">Replaces provisional endpoints</text>
  <text class="sans small" x="514" y="493">and rebuilds history</text>

  <text class="sans micro" x="179" y="414">FAIL-CLOSED PATH</text>
  <text class="sans label" x="179" y="444">Fallback or rejection</text>
  <text class="sans small" x="179" y="470">Transfer authority, reduce the</text>
  <text class="sans small" x="179" y="493">step, or reject with a cause</text>

  <path class="line" d="M250 212 H315"/>
  <path class="line" d="M505 212 H570"/>
  <path class="line" d="M760 212 H825"/>
  <path class="line" d="M920 272 V382"/>
  <path class="line" d="M825 440 H740"/>
  <path class="line" d="M615 382 V322 H155 V160"/>
  <path class="dash" d="M825 242 C742 320 500 330 405 411"/>

  <rect x="60" y="558" width="1080" height="54" rx="14" fill="url(#brand-gradient)"/>
  <text class="sans" x="600" y="581" fill="#ffffff" font-size="14" font-weight="750" text-anchor="middle">Useful when the numerical decision—not only the final waveform—must be reviewable,</text>
  <text class="sans" x="600" y="607" fill="#ffffff" font-size="14" font-weight="750" text-anchor="middle">reproducible, and bounded by declared authority.</text>'''
    return _svg_document(
        "BAB-CS bounded-authority loop",
        "A process diagram showing candidate integration, circuit-equation projection, independent implicit authority, correction and gates, accepted-state evidence, refined replay, and fail-closed fallback.",
        body,
        width=1200,
        height=650,
    )


def _evidence_hierarchy_svg() -> bytes:
    body = '''  <rect width="1200" height="610" rx="28" fill="#f5f8fb"/>
  <text class="sans title" x="60" y="66">Evidence is layered by role, not collapsed into one “truth” number</text>
  <text class="sans subtitle" x="60" y="100">Each authority answers a different question; agreement strengthens confidence without erasing scope or model limitations.</text>

  <g filter="url(#shadow)">
    <rect class="soft" x="60" y="144" width="510" height="88" rx="17"/>
    <rect class="box" x="630" y="144" width="510" height="88" rx="17"/>
    <rect class="box" x="60" y="252" width="510" height="88" rx="17"/>
    <rect class="warm" x="630" y="252" width="510" height="88" rx="17"/>
    <rect class="box" x="60" y="360" width="510" height="88" rx="17"/>
    <rect class="soft" x="630" y="360" width="510" height="88" rx="17"/>
  </g>

  <text class="sans micro" x="86" y="172">ANALYTIC AUTHORITY</text>
  <text class="sans label" x="86" y="199">Known-form truth on supported canonical cases</text>
  <text class="sans small" x="86" y="225">Best for convergence and exact-case accuracy checks.</text>

  <text class="sans micro" x="656" y="172">REFINED REPLAY</text>
  <text class="sans label" x="656" y="199">A stricter numerical authority on declared cases</text>
  <text class="sans small" x="656" y="225">Useful where closed-form trajectories are unavailable.</text>

  <text class="sans micro" x="86" y="280">IMPLICIT LOCAL AUTHORITY</text>
  <text class="sans label" x="86" y="307">Step-level supervision and fallback ownership</text>
  <text class="sans small" x="86" y="333">Controls candidate comparison, correction, and acceptance.</text>

  <text class="sans micro" x="656" y="280">NGSPICE CROSS-IMPLEMENTATION EVIDENCE</text>
  <text class="sans label" x="656" y="307">Independent mapped-case implementation check</text>
  <text class="sans small" x="656" y="333">Not an oracle; unsupported mappings fail closed.</text>

  <text class="sans micro" x="86" y="388">ANCHOR AND BOUND EVIDENCE</text>
  <text class="sans label" x="86" y="415">Drift, recursive bound, phase, energy, and causes</text>
  <text class="sans small" x="86" y="441">Explains how accepted behavior evolves between refreshes.</text>

  <text class="sans micro" x="656" y="388">PACKAGING EQUIVALENCE</text>
  <text class="sans label" x="656" y="415">Source, installed module, and console agreement</text>
  <text class="sans small" x="656" y="441">Verifies that distribution does not silently change results.</text>

  <path class="line" d="M570 185 H630"/>
  <path class="line" d="M570 293 H630"/>
  <path class="line" d="M570 401 H630"/>

  <rect x="60" y="494" width="1080" height="88" rx="16" fill="#102f43"/>
  <text class="sans" x="84" y="524" fill="#ffffff" font-size="15" font-weight="780">Claim boundary</text>
  <text class="sans" x="84" y="550" fill="#d7e7ef" font-size="12.5">BAB-CS reports evidence against declared models and authorities. It does not claim universal method superiority,</text>
  <text class="sans" x="84" y="574" fill="#d7e7ef" font-size="12.5">exact unknown physical trajectories, or production-device fidelity.</text>'''
    return _svg_document(
        "BAB-CS evidence hierarchy",
        "A diagram separating analytic, refined replay, implicit local, ngspice cross-implementation, anchor and bound, and packaging-equivalence evidence by role.",
        body,
        width=1200,
        height=610,
    )


def _engineering_workflow_svg() -> bytes:
    body = '''  <rect width="1200" height="650" rx="28" fill="#f5f8fb"/>
  <text class="sans title" x="60" y="66">From engineering challenge to reviewable simulation decision</text>
  <text class="sans subtitle" x="60" y="100">BAB-CS is most valuable when the model, numerical authority, evidence, and limits must travel with the result.</text>

  <g filter="url(#shadow)">
    <rect class="warm" x="60" y="150" width="250" height="116" rx="18"/>
    <rect class="box" x="365" y="150" width="250" height="116" rx="18"/>
    <rect class="soft" x="670" y="150" width="250" height="116" rx="18"/>
    <rect class="box" x="890" y="356" width="250" height="116" rx="18"/>
    <rect class="warm" x="530" y="356" width="250" height="116" rx="18"/>
    <rect class="soft" x="170" y="356" width="250" height="116" rx="18"/>
  </g>

  <text class="sans micro" x="84" y="181">1 · ENGINEERING QUESTION</text>
  <text class="sans label" x="84" y="213">Define the decision</text>
  <text class="sans small" x="84" y="238">Ripple, dead time, interruption,</text>
  <text class="sans small" x="84" y="261">phase drift, or solver choice</text>

  <text class="sans micro" x="389" y="181">2 · BOUNDED MODEL</text>
  <text class="sans label" x="389" y="213">Declare the abstraction</text>
  <text class="sans small" x="389" y="238">R, L, C, sources, diode, switch,</text>
  <text class="sans small" x="389" y="261">events, authority, and limits</text>

  <text class="sans micro" x="694" y="181">3 · CANDIDATE STUDY</text>
  <text class="sans label" x="694" y="213">Run the method matrix</text>
  <text class="sans small" x="694" y="238">Fixed-step, fixed-accuracy,</text>
  <text class="sans small" x="694" y="261">and fixed-work comparisons</text>

  <text class="sans micro" x="914" y="387">4 · AUTHORITY EVIDENCE</text>
  <text class="sans label" x="914" y="419">Inspect why steps pass</text>
  <text class="sans small" x="914" y="444">Bounds, anchors, phase, energy,</text>
  <text class="sans small" x="914" y="467">fallbacks, rejections, replay</text>

  <text class="sans micro" x="554" y="387">5 · EXTERNAL CHALLENGE</text>
  <text class="sans label" x="554" y="419">Cross-check mapped cases</text>
  <text class="sans small" x="554" y="444">Preserve ngspice version, netlist,</text>
  <text class="sans small" x="554" y="467">logs, hashes, and differences</text>

  <text class="sans micro" x="194" y="387">6 · DECISION PACKAGE</text>
  <text class="sans label" x="194" y="419">Deliver reproducible evidence</text>
  <text class="sans small" x="194" y="444">Source/wheel equivalence, exact</text>
  <text class="sans small" x="194" y="467">configuration, scope, and limits</text>

  <path class="line" d="M310 208 H365"/>
  <path class="line" d="M615 208 H670"/>
  <path class="line" d="M920 208 H1015 V356"/>
  <path class="line" d="M890 414 H780"/>
  <path class="line" d="M530 414 H420"/>

  <rect x="60" y="538" width="1080" height="68" rx="16" fill="url(#brand-gradient)"/>
  <text class="sans" x="600" y="566" fill="#ffffff" font-size="14" font-weight="760" text-anchor="middle">Engineering value: the design discussion can reference the accepted trajectory, the numerical controls,</text>
  <text class="sans" x="600" y="592" fill="#ffffff" font-size="14" font-weight="760" text-anchor="middle">the external challenge, and the model boundary as one deterministic package.</text>'''
    return _svg_document(
        "BAB-CS engineering simulation workflow",
        "A six-stage engineering workflow from defining a circuit challenge through bounded modeling, candidate method comparison, authority evidence, external comparison, and a reproducible decision package.",
        body,
        width=1200,
        height=650,
    )


def _external_comparison_svg(payload: dict[str, Any]) -> bytes:
    external = payload["siteMetrics"]["external"]
    category_summary = " · ".join(
        f'{name.replace("_", " ")}: {count}'
        for name, count in sorted(external["categories"].items())
    )
    body = f'''  <rect width="1200" height="720" rx="28" fill="#f5f8fb"/>
  <text class="sans title" x="60" y="66">Comparison roles: what each path contributes</text>
  <text class="sans subtitle" x="60" y="100">This is a role comparison, not a universal accuracy or speed ranking.</text>

  <rect x="60" y="132" width="1080" height="62" rx="14" fill="#102f43"/>
  <text class="sans" x="80" y="158" fill="#d7e7ef" font-size="12" font-weight="750">PATH</text>
  <text class="sans" x="322" y="158" fill="#d7e7ef" font-size="12" font-weight="750">PRIMARY USE</text>
  <text class="sans" x="654" y="158" fill="#d7e7ef" font-size="12" font-weight="750">AUTHORITY / INDEPENDENCE</text>
  <text class="sans" x="928" y="158" fill="#d7e7ef" font-size="12" font-weight="750">EVIDENCE RETAINED</text>

  <g filter="url(#shadow)">
    <rect class="box" x="60" y="208" width="1080" height="98" rx="14"/>
    <rect class="soft" x="60" y="320" width="1080" height="112" rx="14"/>
    <rect class="box" x="60" y="446" width="1080" height="98" rx="14"/>
    <rect class="warm" x="60" y="558" width="1080" height="112" rx="14"/>
  </g>

  <text class="sans label" x="80" y="244">Raw candidate method</text>
  <text class="sans small" x="80" y="270">Unsupervised baseline</text>
  <text class="sans small" x="322" y="244">Expose the proposal method’s</text>
  <text class="sans small" x="322" y="270">native behavior and cost.</text>
  <text class="sans small" x="654" y="244">The method owns its own output;</text>
  <text class="sans small" x="654" y="270">no BAB-CS acceptance layer.</text>
  <text class="sans small" x="928" y="244">Trajectory, error, and work</text>
  <text class="sans small" x="928" y="270">for the declared case.</text>

  <text class="sans label" x="80" y="358">BAB-CS active supervision</text>
  <text class="sans small" x="80" y="384">Bounded candidate execution</text>
  <text class="sans small" x="322" y="358">Use flexible candidates while</text>
  <text class="sans small" x="322" y="384">retaining correction, gates,</text>
  <text class="sans small" x="322" y="410">fallback, and replay.</text>
  <text class="sans small" x="654" y="358">Independent local implicit method</text>
  <text class="sans small" x="654" y="384">controls acceptance; candidate</text>
  <text class="sans small" x="654" y="410">never grants its own authority.</text>
  <text class="sans small" x="928" y="358">Bounds, causes, residuals,</text>
  <text class="sans small" x="928" y="384">phase/energy, anchors, and</text>
  <text class="sans small" x="928" y="410">deterministic work.</text>

  <text class="sans label" x="80" y="482">Implicit / refined authority</text>
  <text class="sans small" x="80" y="508">Internal numerical baseline</text>
  <text class="sans small" x="322" y="482">Provide local acceptance or a</text>
  <text class="sans small" x="322" y="508">higher-resolution replay target.</text>
  <text class="sans small" x="654" y="482">Methodologically distinct, but</text>
  <text class="sans small" x="654" y="508">still inside the BAB-CS stack.</text>
  <text class="sans small" x="928" y="482">Convergence, residual, replay,</text>
  <text class="sans small" x="928" y="508">and replacement diagnostics.</text>

  <text class="sans label" x="80" y="596">Mapped ngspice check</text>
  <text class="sans small" x="80" y="622">External implementation</text>
  <text class="sans small" x="322" y="596">Challenge mapped BAB-CS cases</text>
  <text class="sans small" x="322" y="622">with a separate simulator.</text>
  <text class="sans small" x="654" y="596">Cross-implementation evidence;</text>
  <text class="sans small" x="654" y="622">not an oracle or step authority.</text>
  <text class="sans small" x="928" y="596">Version, command, netlist, logs,</text>
  <text class="sans small" x="928" y="622">hashes, and state differences.</text>

  <text class="sans micro" x="80" y="652">SCHEDULED MAPPED SET: {external["cases"]} CASES · {html.escape(category_summary).upper()}</text>'''
    return _svg_document(
        "BAB-CS internal and external comparison roles",
        "A comparison matrix for raw candidate methods, BAB-CS active supervision, implicit or refined internal authority, and mapped ngspice runs.",
        body,
        width=1200,
        height=720,
    )


def _qualification_surface_svg(payload: dict[str, Any]) -> bytes:
    metrics = payload["siteMetrics"]
    values = [
        ("Python test methods", int(metrics["tests"]["methods"]), "syntax-derived"),
        ("Comparison matrix rows", int(metrics["comparison"]["matrixRows"]), "8 canonical cases"),
        ("Observatory fixed-step rows", int(metrics["observatory"]["matrixRows"]), "6 × 7 × 3"),
        ("Power-stage sandbox rows", int(metrics["powerStage"]["matrixRows"]), "reduced-order only"),
        ("Embedded Markdown documents", int(payload["documentCount"]), "complete /docs tree"),
        ("Teaching lab exercises", int(metrics["teachingLab"]["exercises"]), "executable exercises"),
        ("Mapped ngspice cases", int(metrics["external"]["cases"]), "scheduled external set"),
    ]
    maximum = max(value for _, value, _ in values)
    rows: list[str] = []
    for index, (label, value, note) in enumerate(values):
        y = 142 + index * 68
        bar_width = 650 * math.sqrt(value / maximum)
        fill = "url(#brand-gradient)" if index < 4 else "url(#warm-gradient)"
        rows.extend(
            [
                f'  <text class="sans label" x="60" y="{y + 20}">{html.escape(label)}</text>',
                f'  <text class="sans small" x="60" y="{y + 47}">{html.escape(note)}</text>',
                f'  <rect x="350" y="{y}" width="700" height="46" rx="12" fill="#e6edf3"/>',
                f'  <rect x="350" y="{y}" width="{bar_width:.2f}" height="46" rx="12" fill="{fill}"/>',
                f'  <text class="sans" x="1078" y="{y + 31}" fill="#10243a" font-size="23" font-weight="850" text-anchor="end">{value}</text>',
            ]
        )
    body = "\n".join(
        [
            '  <rect width="1200" height="690" rx="28" fill="#f5f8fb"/>',
            '  <text class="sans title" x="60" y="66">Repository-owned qualification surface</text>',
            '  <text class="sans subtitle" x="60" y="100">Counts are derived from current canonical files. Bar lengths use square-root scaling; exact values are printed.</text>',
            *rows,
            '  <text class="sans micro" x="60" y="652">COUNTS DESCRIBE COVERAGE AND EVIDENCE VOLUME—NOT UNIVERSAL ACCURACY, SPEED, OR CERTIFICATION.</text>',
        ]
    )
    return _svg_document(
        "BAB-CS qualification surface graph",
        "A horizontal bar graph of current test methods, comparison rows, observatory rows, power-stage rows, documents, teaching exercises, and mapped ngspice cases.",
        body,
        width=1200,
        height=690,
    )


def _software_landscape_svg() -> bytes:
    body = '''  <rect width="1200" height="720" rx="28" fill="#f5f8fb"/>
  <text class="sans title" x="60" y="66">Simulation software roles across an engineering program</text>
  <text class="sans subtitle" x="60" y="100">The tools overlap, but their official emphasis and best handoff point differ. This is a workflow map, not a ranking.</text>

  <g filter="url(#shadow)">
    <rect class="soft" x="60" y="142" width="1080" height="104" rx="18"/>
    <rect class="box" x="60" y="270" width="510" height="118" rx="18"/>
    <rect class="box" x="630" y="270" width="510" height="118" rx="18"/>
    <rect class="warm" x="60" y="406" width="510" height="118" rx="18"/>
    <rect class="box" x="630" y="406" width="510" height="118" rx="18"/>
  </g>

  <text class="sans micro" x="86" y="172">BAB-CS · NUMERICAL GOVERNANCE AND REPRODUCIBILITY</text>
  <text class="sans label" x="86" y="202">Supervise candidate methods and preserve the evidence behind accepted transients</text>
  <text class="sans small" x="86" y="226">Best fit: bounded method studies, failure-cause analysis, reduced-order switched experiments, qualification, and teaching.</text>

  <text class="sans micro" x="86" y="300">NGSPICE + LTSPICE · DEVICE-ORIENTED CIRCUIT DESIGN</text>
  <text class="sans label" x="86" y="330">Device-oriented analog and mixed-signal workflows</text>
  <text class="sans small" x="86" y="356">Best handoff: detailed models, vendor macromodels,</text>
  <text class="sans small" x="86" y="382">schematic capture, waveform inspection, and mapped checks.</text>

  <text class="sans micro" x="656" y="300">PLECS · POWER-ELECTRONICS SYSTEM DESIGN</text>
  <text class="sans label" x="656" y="330">Converters, controls, switching, thermal, and deployment</text>
  <text class="sans small" x="656" y="356">Best handoff: converter design, control verification,</text>
  <text class="sans small" x="656" y="382">thermal studies, code generation, and real-time controller tests.</text>

  <text class="sans micro" x="86" y="436">SIMSCAPE ELECTRICAL · MULTIPLE-PHYSICS SYSTEMS</text>
  <text class="sans label" x="86" y="466">Electrical, mechanical, thermal, motors, grids, and controls</text>
  <text class="sans small" x="86" y="492">Best handoff: system integration, virtual testing, fault studies,</text>
  <text class="sans small" x="86" y="518">cross-domain control design, code generation, and hardware tests.</text>

  <text class="sans micro" x="656" y="436">XYCE · LARGE-SCALE PARALLEL CIRCUIT SIMULATION</text>
  <text class="sans label" x="656" y="466">SPICE-compatible simulation for extremely large problems</text>
  <text class="sans small" x="656" y="492">Best handoff: high-performance analog networks,</text>
  <text class="sans small" x="656" y="518">very large circuit studies, and serial or parallel execution.</text>

  <path class="line" d="M330 246 V270"/>
  <path class="line" d="M870 246 V270"/>
  <path class="line" d="M330 382 V406"/>
  <path class="line" d="M870 382 V406"/>

  <rect x="60" y="568" width="1080" height="104" rx="18" fill="#102f43"/>
  <text class="sans" x="86" y="600" fill="#ffffff" font-size="15" font-weight="800">Recommended engineering pattern</text>
  <text class="sans" x="86" y="626" fill="#d7e7ef" font-size="13.5">Use BAB-CS to qualify the reduced numerical experiment and its authority chain; move to the specialist simulator when the project requires</text>
  <text class="sans" x="86" y="652" fill="#d7e7ef" font-size="13.5">broader device fidelity, vendor models, multiple-physics plants, hardware-in-the-loop deployment, or very-large-scale parallel execution.</text>'''
    return _svg_document(
        "Engineering simulation software landscape",
        "A role map comparing BAB-CS numerical governance with device-oriented SPICE tools, PLECS power-electronics systems, Simscape Electrical multiple-physics systems, and Xyce large-scale parallel simulation.",
        body,
        width=1200,
        height=720,
    )


def render_svg_assets(payload: dict[str, Any]) -> dict[str, bytes]:
    assets = {
        "authority-loop.svg": _authority_loop_svg(),
        "engineering-workflow.svg": _engineering_workflow_svg(),
        "evidence-hierarchy.svg": _evidence_hierarchy_svg(),
        "external-comparison.svg": _external_comparison_svg(payload),
        "qualification-surface.svg": _qualification_surface_svg(payload),
        "software-landscape.svg": _software_landscape_svg(),
    }
    assets.update(render_figure_assets())
    assets.update(render_tutorial_assets())
    if tuple(assets) != SVG_ASSET_NAMES:
        raise AssertionError("documentation SVG inventory order drifted")
    return assets
