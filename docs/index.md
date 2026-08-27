# Bounded-Authority-Based-Circuit-Simulation Documentation

Bounded-Authority-Based-Circuit-Simulation (`BAB-CS`) is a transient circuit
simulator for engineering studies in which the reason for trusting a numerical
result must remain visible. A candidate method proposes the next capacitor
voltages and inductor currents. Separate circuit-equation solves, reference
methods, correction rules, rejection gates, and independent replay decide
whether that proposal becomes the accepted state.

BAB-CS is particularly suited to reduced-order models: deliberately simplified
circuits that retain the behavior needed for one engineering question. Current
uses include power-conversion schedule screening, analog and resonant transients,
numerical-method qualification, failure diagnosis, and reproducible comparison
between source code and the installed Python wheel. A wheel is an installable
Python package file.

BAB-CS complements rather than replaces SPICE, power-electronics, multidomain,
hardware-in-the-loop, and large-scale parallel simulation software. SPICE means
*Simulation Program with Integrated Circuit Emphasis*. Hardware-in-the-loop
means testing real controller hardware against a simulated plant. Multidomain
means solving interacting electrical, mechanical, thermal, or other physical
systems together. The BAB-CS bound applies to its implemented numerical error
model, not to the unknown exact physical trajectory.

## Current Work Essays

- [Current project and integrated design](CURRENT_WORK.md)
- [Numerical methods and error bounding](NUMERICAL_METHODS_ESSAY.md)
- [Circuit engineering and performance work](ENGINEERING_AND_PERFORMANCE_ESSAY.md)
- [Validation, release, and claim discipline](VALIDATION_RELEASE_AND_CLAIMS_ESSAY.md)
- [Applications and research roadmap](APPLICATIONS_AND_RESEARCH_ROADMAP.md)
- [Shared bibliography and repository references](REFERENCES.md)

## Start Here

- [Searchable HTML document tree](html/index.html)
- [HTML documentation redesign and rewrite plan](../HTML_DOCUMENT_REDESIGN_AND_REWRITE_PLAN.md)
- [In-text learning guide and novice essay plan](../INTEXT_LEARNING_GUIDE_AND_NOVICE_ESSAY_PLAN.md)
- [OURD Coding Agent-guided visual and grammar redesign plan](../OURD_HTML_TREE_VISUAL_GRAMMAR_REDESIGN_PLAN.md) — the OURD Coding Agent is the governed local advisory agent used for the review; it did not approve or mutate the redesign.
- [SVG circuit and simulation figures implementation plan](../SVG_CIRCUIT_AND_SIMULATION_FIGURES_IMPLEMENTATION_PLAN.md)
- [ngspice and teaching-tutorial expansion plan](../NGSPICE_AND_TEACHING_TUTORIAL_EXPANSION_PLAN.md)
- [Project overview and usage](../README.md)
- [Version 1 normative specification](BAB_CSV1_SPEC.md)
- [Version 1 implementation plan](../IMPLEMENTATION_PLAN.md)
- [Release draft](../RELEASE.md)

## Numerical Design

- [Architecture and authority flow](ARCHITECTURE.md)
- [Error-bound model](ERROR_BOUND_MODEL.md)
- [Bounded candidate integrators](BOUNDED_CANDIDATES.md)
- [Bounded and interval Newton research](BOUNDED_NEWTON.md)
- [Minimal reproducible research example](MINIMAL_REPRODUCIBLE_RESEARCH.md)

## Tests and Comparisons

- [Comparison protocol](COMPARISON_PROTOCOL.md)
- [Method Observatory](METHOD_OBSERVATORY.md)
- [Bound Coverage Atlas](BOUND_COVERAGE_ATLAS.md)
- [Power-Stage Sandbox](POWER_STAGE_SANDBOX.md)
- [Teaching and Reproducibility Lab](TEACHING_AND_REPRODUCIBILITY_LAB.md)
- [ngspice 20-case mapping atlas](NGSPICE_CASE_ATLAS.md)
- [Observatory, atlas, sandbox, and lab implementation audit](OBSERVATORY_ATLAS_SANDBOX_LAB_IMPLEMENTATION_AUDIT.md)
- [ngspice and teaching-tutorial expansion plan](../NGSPICE_AND_TEACHING_TUTORIAL_EXPANSION_PLAN.md)
- [External comparison](EXTERNAL_COMPARISON.md)
- [Tests and comparisons implementation plan](../TESTS_AND_COMPARISONS_IMPLEMENTATION_PLAN.md)
- [Tests and comparisons qualification audit](TESTS_AND_COMPARISONS_AUDIT.md)
- [Performance optimization audit](PERFORMANCE_OPTIMIZATION_AUDIT.md)
- [Qualification summary evidence](QUALIFICATION_SUMMARY.md)

## Teaching Lab Tutorials

- [Scientific results report for Tutorials 1–10](TUTORIAL_SCIENTIFIC_RESULTS_REPORT.md)
- [Tutorial 1: Modified nodal analysis and state ownership](tutorials/01_MNA_STATE_OWNERSHIP.md)
- [Tutorial 2: Convergence by measured refinement](tutorials/02_CONVERGENCE_BY_REFINEMENT.md)
- [Tutorial 3: Phase error versus energy error](tutorials/03_PHASE_VERSUS_ENERGY.md)
- [Tutorial 4: Shadow authority](tutorials/04_SHADOW_AUTHORITY.md)
- [Tutorial 5: Deterministic packaging](tutorials/05_DETERMINISTIC_PACKAGING.md)
- [Tutorial 6: Source versus installed-wheel equivalence](tutorials/06_SOURCE_WHEEL_EQUIVALENCE.md)
- [Tutorial 7: Exact event alignment](tutorials/07_EVENT_ALIGNMENT.md)
- [Tutorial 8: Empirical bound coverage](tutorials/08_EMPIRICAL_BOUND_COVERAGE.md)
- [Tutorial 9: Fallback and rejection forensics](tutorials/09_FALLBACK_AND_REJECTION_FORENSICS.md)
- [Tutorial 10: Semantic mapping to ngspice](tutorials/10_SEMANTIC_NGSPICE_MAPPING.md)

## Qualification and Release

- [Version 1 completion audit](BAB_CSV1_COMPLETION_AUDIT.md)
- [Release qualification plan](../BAB-CS-Release-Qualification-Plan.md)
- [Release qualification implementation plan](../BAB-CS-Release-Qualification-Implementation-Plan.md)
- [Release qualification implementation audit](RELEASE_QUALIFICATION_IMPLEMENTATION_AUDIT.md)
- [Repository audit implementation plan](../REPOSITORY_AUDIT_IMPLEMENTATION_PLAN.md)
- [Licence decision record](LICENCE_DECISION.md)

## Project Policies

- [Citation metadata](../CITATION.cff)
- [Changelog](../CHANGELOG.md)
- [Contribution guide](../CONTRIBUTING.md)
- [Security policy](../SECURITY.md)
