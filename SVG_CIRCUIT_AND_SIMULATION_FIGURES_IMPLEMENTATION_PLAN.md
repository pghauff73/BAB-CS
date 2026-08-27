# SVG Circuit and Simulation Figures Implementation Plan

Date: August 27, 2026

## Objective

Add deterministic, accessible Scalable Vector Graphics (`SVG`) circuit
schematics beside the documentation descriptions of each implemented
Observatory and Power-Stage case. Add graphs of BAB-CS simulation results where
the documentation discusses waveforms, phase, energy, method comparison, or
bound coverage. Generate every figure from canonical repository inputs and the
current simulator rather than drawing untraceable decorative approximations.

## Requirements

1. Generate circuit schematics for resistor-capacitor (`RC`),
   resistor-inductor (`RL`), damped resistor-inductor-capacitor (`RLC`),
   lossless inductor-capacitor (`LC`), diode clip, switched RC, simplified
   buck-like converter, scheduled H-bridge RL load, and direct-current-link RLC
   startup and interruption.
2. Place each schematic directly beside its matching Markdown circuit
   description as a semantic HTML figure with alternative text and a visible
   caption.
3. Generate representative BAB-CS result graphs for all nine cases from the
   exact checked-in JSON inputs.
4. Generate one Method Observatory fixed-step accuracy-versus-work graph and
   one Bound Coverage Atlas authority-error-versus-recursive-bound graph.
5. Label every power-stage figure as a reduced-order numerical experiment, not
   a production device model.
6. Keep graph axes, units, candidate method, nominal timestep, event boundaries,
   input path, and input SHA-256 visible or available in the SVG metadata.
7. Preserve deterministic generation: repeated builds from the same source
   must produce byte-identical SVG files.
8. Keep every SVG self-contained, script-free, accessible through `title` and
   `desc`, and valid XML.
9. Preserve mobile horizontal scrolling, dark-mode framing, print behavior, and
   the existing plain-language concept annotations.

## Authoritative Inputs

| Figure group | Canonical owner |
|---|---|
| Observatory schematics and traces | `benchmarks/cases/*.json` and `benchmarks/observatory/manifest.json` |
| Power-stage schematics and traces | `examples/power_stage/*.json` and `benchmarks/power_stage/manifest.json` |
| Candidate execution | `src/babcs/` through `load_case`, `Simulator`, and `BoundedAdamsBashforthIntegrator` |
| Bound metric | The same weighted root-mean-square authority error and `estimated_bound` semantics used by `tools/bound_coverage_atlas.py` |
| Document placement | `docs/METHOD_OBSERVATORY.md`, `docs/BOUND_COVERAGE_ATLAS.md`, and `docs/POWER_STAGE_SANDBOX.md` |
| Generated asset inventory | `tools/docs_site_assets.py` and `tools/build_docs_html.py` |

## Figure Inventory

### Method Observatory Cases

- `circuit-rc-step.svg` and `result-rc-step.svg`;
- `circuit-rl-step.svg` and `result-rl-step.svg`;
- `circuit-rlc-damped.svg` and `result-rlc-damped.svg`;
- `circuit-lc-long.svg` and `result-lc-long.svg`;
- `circuit-diode-clip.svg` and `result-diode-clip.svg`; and
- `circuit-switched-rc.svg` and `result-switched-rc.svg`.

### Power-Stage Cases

- `circuit-buck-like.svg` and `result-buck-like.svg`;
- `circuit-h-bridge-rl.svg` and `result-h-bridge-rl.svg`; and
- `circuit-dc-link-rlc.svg` and `result-dc-link-rlc.svg`.

### Cross-Case Evidence

- `result-observatory-accuracy-work.svg`; and
- `result-bound-coverage.svg`;
- `result-coverage-by-age.svg`;
- `result-phase-energy.svg`; and
- `result-rejection-causes.svg`.

The new inventory contains 23 figures. Together with the existing six
architecture and evidence diagrams, the generated HTML asset set contains 29
SVG files.

## Implementation Design

### Circuit Figure Generator

Create a dedicated generator with reusable conventional schematic primitives
for sources, resistors, capacitors, inductors, diodes, scheduled switches,
grounds, nodes, wires, current arrows, and bounded-model notes. Each named
layout must load the matching JSON file, require the expected elements, and use
their exact values in labels. A topology rename or missing component must fail
generation rather than silently producing a stale diagram.

### Simulation Figure Generator

Run the checked-in BAB-CS configuration for each case. Plot accepted simulation
points, use separate panels when voltage and current units differ, and mark
accepted event boundaries with restrained orange rules. Graphs must state that
they are numerical results from the declared reduced-order model, not measured
physical-device data.

### Observatory and Atlas Figures

Run all seven candidate profiles for one declared fixed-step RC comparison and
plot maximum authority error against deterministic work. For the Atlas figures,
compare RC and lossless LC simulation states with analytic authority using the
same weighted root-mean-square scaling and anchor-age buckets as the Atlas. Plot
error against recursive bound, empirical coverage by authority age, phase and
relative energy separately, and classified rejection causes from the scheduled
H-bridge case. These figures illustrate the referenced report semantics without
claiming to replace the complete 126-row Observatory or full Atlas report.

### Markdown Figure Rendering

Extend the local Markdown renderer so a standalone image written as
`![alternative text](path "caption")` becomes a `<figure>` with the existing
`.diagram-frame` treatment and a visible `<figcaption>`. Inline images remain
inline. This keeps the Markdown readable outside the generated site while
providing semantic figures in HTML.

## Report and Correction Loop

| Iteration | Check | Required response |
|---|---|---|
| 1 | Compare the generated inventory with the 23 required figure names. | Add missing assets or remove undocumented extras. |
| 2 | Parse every SVG and inspect title, description, scripts, external URLs, dimensions, and deterministic bytes. | Fail closed on inaccessible or non-self-contained output. |
| 3 | Compare figure labels with canonical JSON values and input hashes. | Correct the generator owner, never hand-edit generated SVG files. |
| 4 | Render Observatory, Atlas, and Power-Stage pages on desktop and mobile. | Correct clipping, unreadable axes, missing captions, or weak figure placement. |
| 5 | Inspect dark and print-oriented presentations. | Correct framing and contrast without altering the SVG evidence itself. |
| 6 | Run focused documentation tests, generator check mode, JavaScript syntax validation, and the complete repository suite. | Record every failure and correction before claiming completion. |

## Completion Criteria

Completion requires all 23 new SVG figures to be generated and embedded beside
the matching descriptions, every referenced result view to show current
simulation evidence, all assets to be deterministic and accessible, desktop and
mobile browser inspection to pass, and the full repository suite to pass. The
completion audit must report exact asset counts, source owners, hashes, commands,
test results, browser views, discovered problems, and applied corrections.

## Completion Audit

Audit date: August 27, 2026.

### Implemented Inventory

- Generated 23 new self-contained SVG figures: nine circuit schematics, nine
  matching BAB-CS result graphs, one Method Observatory comparison graph, and
  four Bound Coverage Atlas graphs.
- Preserved the six existing conceptual diagrams, producing an exact generated
  inventory of 29 SVG assets for 27 Markdown documents.
- Embedded the figures semantically through standalone Markdown images rendered
  as `<figure>`, `<img>`, and `<figcaption>` elements.
- Kept all three power-stage cases explicitly labelled as "reduced-order numerical experiments"
  rather than production device models.
- Recorded source path, input SHA-256 prefix, method, nominal step, and accepted
  point count in the applicable generated figure metadata and visible footer.

The 23-figure deterministic manifest SHA-256 is
`31f89e4eff742c672e21bf3fdc45811f62b6f7a81992530fc7e8bd77776ed498`.
The SHA-256 of the sorted 29-asset checksum manifest is
`c94b42decfbcc91167b5185ea01ddfe46d95daa9dc1eb12b540c6e8db2902f01`.

### Canonical Input Hashes

| Case | Canonical input | SHA-256 |
|---|---|---|
| RC step | `benchmarks/cases/rc_step.json` | `5431d8f89b06afdc20558725a5415ff176e411b7802796744925faee708a2d73` |
| RL step | `benchmarks/cases/rl_step.json` | `409e82b4b5b32f85c2f32a4bcf2a6d5ceea450ebd5421291005dce6f77f29bcf` |
| Damped RLC | `benchmarks/cases/rlc_damped.json` | `3d4ddaf9257d97db8ba8945b01e12207feb1639b362a4583a0d58f253c11cadb` |
| Lossless LC | `benchmarks/cases/lc_long.json` | `5af8aea635c93ea38f93300800eaf10ce9303300711349b453dd50ce7d42bd70` |
| Diode clip | `benchmarks/cases/diode_clip.json` | `7e0bd8068d5931b1bfa6d0cd0e47c8b6d4398fea847063db06bcfe6ca13907a4` |
| Switched RC | `benchmarks/cases/switched_rc.json` | `6980909a519ca6087111c3005add11997c7ae482c4cbbd987f8e513898d16195` |
| Buck-like | `examples/power_stage/buck_like_reduced_order.json` | `09281a85110d4d45d8e21871e462833e1067c32a9bf06f78f044127c6ca87b4a` |
| H-bridge RL | `examples/power_stage/h_bridge_rl_reduced_order.json` | `fb3d4143d2a4009ae54ccb66d9b659de3eeba3fd39b056395cf88eaebe61d77c` |
| DC-link RLC | `examples/power_stage/dc_link_rlc_reduced_order.json` | `f60ba5b539f3932b61f2e556c65b7cf730814bcb0b21ec73c439511dae2a088a` |

### Validation Evidence

- `PYTHONPATH=src python tools/build_docs_html.py --check` passed with 29
  assets, 27 documents, documentation source SHA-256
  `a6273943f545db6c0a3f8e5bd80ed64d4a6700d8692e638adb9e6fe15b4b3551`,
  and 1.39 seconds measured elapsed time.
- `node --check docs/html/app.js` passed.
- `PYTHONPATH=src python -m unittest tests.test_docs_html -v` passed 24
  focused documentation tests.
- `PYTHONPATH=src python -m unittest discover -s tests -v` passed 300 tests
  with two declared skips.
- `git diff --check` passed for the plan, generators, generated-site sources,
  embedded Markdown pages, and documentation tests.
- Repeated in-process rendering produced byte-identical assets; every SVG parsed
  as XML, contained a title and description, and contained no scripts or
  external HTTPS references.

### Browser Review

Firefox 152 headless review used a local HTTP server and WebDriver BiDi, the
browser's bidirectional remote-control protocol, to wait for rendering, inspect
image state, scroll exact figures into view, and capture screenshots.

| View | Result |
|---|---|
| Method Observatory circuit and result, 1440 by 1200 | Both images loaded completely; each figure used a 730-pixel client and scroll width; captions and adjacent descriptions remained visible. |
| Bound Coverage Atlas bound graph, 1440 by 1200 | Authority error and recursive bound remained distinct; corrected footer rows no longer collided with the time axis. |
| Power-Stage buck-like circuit and result, 1440 by 1200 | Reduced-order warning, switching-event rules, voltage trace, current trace, metadata, and caption remained legible. |
| Method Observatory circuit, 430 by 900 | Figure client width was 394 pixels and scroll width was 620 pixels, confirming deliberate mobile horizontal scrolling without page-width expansion. |
| Power-Stage result, 430 by 900 | Both result panels, metadata, reduced-order claim boundary, and sticky caption remained visible in the horizontally scrollable frame. |
| Atlas phase and energy, dark mode, 1440 by 1200 | Phase and energy panels, footer evidence, caption, and following rejection-cause graph retained sufficient contrast. |

All final inspected figures loaded from `assets/*.svg` with HTTP status 200. The
90-pixel scroll margin kept figure titles below the sticky navigation bar.

### Problem and Correction Record

| Problem observed | Correction applied | Closure evidence |
|---|---|---|
| The first direct generator build imported analytic helpers through test-only modules. | Moved the exact RC and parallel-RLC formulas and reason taxonomy into the documentation generator while retaining canonical production simulation APIs. | Direct build and check mode pass without importing `tests`. |
| Documentation tests assumed the old six-asset inventory and required every asset on the landing page. | Updated the inventory to 29 and separated six landing diagrams from 23 document-embedded figures. | Focused documentation suite passes. |
| Test edits changed the evidence-owner hash and made `documents.js` stale. | Regenerated after each evidence-owner change until check mode passed from a frozen state. | Payload byte-determinism and check-mode tests pass. |
| Browser inspection returned HTTP 404 for `html/assets/*.svg`. | Added one `imageSource` resolver that maps Markdown-owned `html/assets` paths to generated-site `assets` paths while preserving external and other relative images. | Final browser requests return HTTP 200. |
| Initial section links used a shadowed `document` name and CSS smooth scrolling prevented true instant placement. | Resolved headings through `window.document` and added `scrollDocumentTarget` with a temporary non-smooth initial path. | Deep-link regression assertions and browser scroll measurements pass. |
| Sticky navigation could cover figure titles when a figure was programmatically selected. | Reused the established 90-pixel heading offset for document figures. | Final captures place figures 90 pixels below the viewport top. |
| Result metadata shared vertical space with time-axis labels and switching-event legends. | Derived dedicated metadata, event-legend, and claim-note footer rows from the final panel bottom. | Corrected desktop, mobile, and dark-mode captures show separated rows. |
| Port 8765 was already occupied during local review. | Isolated validation on port 8766 without terminating an unrelated process. | Local site and all inspected assets served successfully. |
| The first standalone hash helper omitted `PYTHONPATH=src`. | Repeated the exact manifest command with the declared source import path. | Both aggregate hashes were produced and recorded above. |
| Early WebDriver BiDi probes retained one session and one inspection expression contained an extra parenthesis. | Restarted the isolated browser, ended sessions explicitly, and corrected the probe expression. | Seven final remote captures and structured load metrics completed successfully. |

### SVG Text Collision Review

On August 27, 2026, a transform-aware Firefox 152 audit measured every rendered
`text` element against every other text element and against its SVG view box.
The first pass found two true overlaps, four clipped labels, and 46 text pairs
with less than the declared visual safety gap. The affected content included
the DC-link bleed-resistor and capacitor labels, Observatory axis and legend
text, three vertical bar-chart axis labels, the diode source caption, and
several tightly spaced conceptual-diagram lines.

The generators were corrected rather than patching generated files. Component
labels were moved to unambiguous sides, frequency text now uses compact
engineering notation, vertical axes use true rotated text, plot and footer rows
have dedicated spacing, and conceptual cards use wider line separation or
shorter wording where needed. No font was reduced below the existing 10.5-pixel
minimum.

The final browser-rendered audit covered all 29 generated SVG assets and
reported zero overlaps, zero clipped labels, and zero near-pair warnings. A
representative visual review covered the DC-link RLC and diode-clip circuits;
Observatory accuracy-versus-work, coverage-by-age, and rejection-cause graphs;
and the evidence hierarchy, external comparison, qualification surface, and
software landscape diagrams. The focused documentation suite also contains a
regression test for the repaired label placement, engineering frequency
notation, rotated axes, and shortened mapped-ngspice wording.

### Claim Boundary

This audit establishes deterministic documentation figures and representative
results for the checked-in reduced-order cases. It does not convert those cases
into production semiconductor, thermal, electromagnetic, protection, contactor,
fault, or hardware-fidelity models, and it does not make the empirical coverage
plots formal mathematical enclosure proofs.
