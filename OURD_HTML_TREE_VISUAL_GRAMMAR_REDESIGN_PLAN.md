# OURD-Guided HTML Tree Visual and Grammar Redesign Plan

Date: August 27, 2026

## Objective

Redesign the complete generated HTML documentation tree as a professional
engineering observatory while making every current-work essay direct,
consistent, and useful to novice engineers. Preserve every technical
claim, formula, reference, document, accessibility feature, deterministic
artifact rule, and release boundary.

## Governed OURD Review

The local OURD coding agent was used as a read-only advisory reviewer with:

- model `qwen3.8-27b-fast`;
- model digest
  `07cb98f8840ce491fc28c04a5ecc13c4dec5fd23d9a4732878bc3c02acb5b005`;
- evidence dossier SHA-256
  `94c3bfd05c5b6862c028fbfb45872f95897c6ef0868a2b26d9c9ca010d73cbde`;
- advisory review SHA-256
  `c756f7d9ac77eac6723497c2ba3941af64a11d2648c8aacc1fd749eee9c6a209`;
  and
- no mutation authority.

The review named the direction **Instrument Panel for Bounded Authority**. It
recommended using visual hierarchy to communicate document role, reading
position, and evidence status, while reserving the orange accent for limits and
boundaries rather than general decoration.

## Problems and Adjustments

| Iteration | Problem | Adjustment |
|---|---|---|
| 1 | Direct review of all HTML and essay owners exceeded the configured 6,000-token OURD input budget. | Split visual and grammatical evidence and instruct the agent to use narrow reads. |
| 2 | Narrow direct reads still expanded to 10,009 estimated tokens because tool schemas and accumulated excerpts remained in context. | Generate a frozen, hash-labeled evidence packet instead of allowing broad source exploration. |
| 3 | The first evidence packet still exceeded the input budget after governance overhead. | Reduce it to a 602-word dossier containing exact source hashes, selector facts, heading facts, browser observations, and non-negotiable constraints. |
| 4 | The compact run exceeded the artificial budget by 15 estimated tokens. | Raise only the agent input cap from 6,000 to 6,500 while retaining the model's verified 8,192-token context and a bounded 1,100-token output. |
| 5 | The final governed review completed without mutation authority. | Treat it as advisory design evidence; implement and validate changes through repository sources and deterministic tests. |

## Visual Design Contract

### Navigation Instrumentation

- add a document count to every navigation category;
- classify every document with a compact role label such as Overview, Essay,
  Guide, Design, Evidence, Audit, Policy, or Reference;
- preserve every document exactly once and keep reading time visible; and
- make the active item look selected without motion or excessive decoration.

### Reading Position

- retain the global reading-progress bar;
- add a restrained stage-level progress rule below the topbar;
- show the active section as `current / total` in the right table of contents;
  and
- keep all progress indicators non-authoritative and `aria-hidden` where they do
  not carry document meaning.

### Engineering Observatory Style

- retain the serif/sans/monospace hierarchy and readable line length;
- tighten oversized document titles so long technical names wrap deliberately;
- use teal for governed or active states and orange only for boundary cues;
- restyle the home critical-use card as an instrument tile rather than a
  promotional card;
- strengthen table headers, code labels, metadata, and section rhythm; and
- preserve dark mode, mobile flow, print output, and visible in-text definitions.

## Grammar Contract

### Current Work and Applications Essays

- preserve their already direct engineering narrative, project portfolio,
  specialist-software handoff, and novice definitions;
- align them with the same active, evidence-first grammar used by the redesigned
  interface; and
- retain every implemented capability, limitation, and roadmap boundary.

### Numerical Methods Essay

- replace essay-about-itself language with the engineering decisions the reader
  must make;
- rename novice guidance and timestep headings as direct actions; and
- retain all candidate descriptions, equations, references, and claim limits.

### Engineering and Performance Essay

- use active headings that describe what the simulator or engineer does;
- replace abstract openings such as `The implementation` and `The baseline` with
  concrete ownership or computation actions; and
- preserve every retained and rejected optimization result.

### Validation, Release, and Claims Essay

- use one consistent question-led heading grammar;
- tighten repeated `means`, `asks whether`, and `does not` constructions; and
- preserve exact validation, qualification, certification, publication, and
  release-authority boundaries.

## Implementation Sequence

1. Add navigation counts and document-role labels.
2. Add stage and section progress instrumentation.
3. Apply the engineering-observatory visual treatment.
4. Audit all five narrative essays and rewrite the three structures that still
   use indirect or inconsistent grammar.
5. Update deterministic tests for the new contracts.
6. Regenerate the embedded document payload and SVG metrics.
7. Inspect desktop, mobile, long-table, dark-mode, and print-oriented views.
8. Run the complete repository test suite and record the completion audit.

## Rejected Changes

- removing or hiding `Plain words` notes;
- replacing the serif/sans pairing;
- widening prose beyond the established readable measure;
- animating active navigation selections;
- changing landmark or skip-link order;
- changing formulas, references, evidence tables, or claim boundaries; and
- treating the OURD model as approval authority.

## Completion Criteria

Completion requires current evidence that all 27 documents remain reachable,
navigation roles and counts are correct, section progress is accurate, the
instrument-panel visual system works across desktop/mobile/dark/print views, the
five current-work narrative documents follow the grammar contract, deterministic generation is
current, all reported problems are fixed, and the complete suite passes.

## Completion Audit

Completed on August 27, 2026 against the current working tree.

| Requirement | Evidence | Result |
|---|---|---|
| Complete tree | Generator payload contains 27 Markdown documents exactly once; navigation categories display deterministic counts. | Pass |
| Document roles | Schema version 3 assigns Overview, Essay, Guide, Design, Evidence, Audit, Policy, or Reference labels through one generator owner. | Pass |
| Reading position | Global and stage progress rules are present; the table of contents reports active section position as `current / total`. | Pass |
| Hero and engineering portfolio | The home hero states the critical simulation problem, eight suitable engineering projects remain filterable, and the specialist-software comparison remains explicitly non-ranking. | Pass |
| Novice definitions | The glossary includes the OURD Coding Agent and more than 60 technical concepts; deterministic scanning reports zero unexplained prose acronyms across `docs/*.md`. | Pass |
| Essay grammar | Current Work and Applications retain their direct evidence-first rewrites; Numerical Methods, Engineering and Performance, and Validation/Release use the new active and question-led structures. | Pass |
| Light desktop | Firefox 152.0.5 at 1440 by 1200 pixels confirmed hierarchy, navigation counts, role labels, hero instrumentation, metadata, and table-of-contents progress. | Pass |
| Mobile | Firefox 152.0.5 at 390 by 1600 pixels confirmed single-column hero flow, readable critical-use instrumentation, stacked actions, and bounded card layouts. | Pass |
| Dark mode | A forced dark-theme browser inspection exposed a light cyan critical card caused by theme-dependent brand mixing; the card now uses a fixed deep-teal surface with readable text. | Pass after correction |
| Long content and comparison tables | Tall Firefox captures confirmed essay flow, in-text definitions, the complete project portfolio, engineering workflow diagrams, and the horizontally scrollable software comparison table. | Pass |
| Print-oriented rules | Static inspection confirmed navigation, progress, action, and copy controls are removed; definitions and content remain printable with page-break safeguards. | Pass |
| Deterministic generation | `PYTHONPATH=src python tools/build_docs_html.py --check` accepts the generated JavaScript payload and six self-contained SVG assets. | Pass |
| JavaScript syntax | `node --check docs/html/app.js` completes successfully. | Pass |
| Focused documentation tests | `PYTHONPATH=src python -m unittest tests.test_docs_html -v` passes 21 tests. | Pass |
| Complete repository suite | `PYTHONPATH=src python -m unittest discover -s tests -v` passes 297 tests with 2 intentional skips. | Pass |

No model output served as approval authority. The OURD review remained advisory,
and repository sources, deterministic generation, browser inspection, and the
complete test suite own the final evidence.
