# Changelog

All notable Bounded-Authority-Based-Circuit-Simulation changes are recorded
here. Release approval remains governed
by `BAB-CS-Release-Qualification-Plan.md`; an entry in this file is not evidence
that a version has been qualified or published.

## [Unreleased] - 1.1.0 candidate

### Added

- Bounded explicit Euler, Heun, RK23, backward Euler, trapezoidal, BDF2, and
  variable-step AB2 candidate supervision.
- Embedded fast paths with dynamic bound-cap promotion and periodic independent
  replay authority.
- Adaptive mixed-energy replay refinement and BDF2 switched-circuit replay
  qualification.
- Optional SciPy SuperLU and SuiteSparse KLU acceleration with guarded fallback.
- Native batched sensitivity assembly, topology-aware caches, sparse workspaces,
  and guarded chord/Schur nonlinear predictors.
- Deterministic comparison, external ngspice, release-evidence, tamper-detection,
  and installed-wheel equivalence tooling.
- A manifest-owned 20-case ngspice mapping suite covering first-order linear,
  resonant, nonlinear diode, scheduled-switching, and reduced-order power-stage
  experiments, with deterministic netlists, waveforms, logs, reports, and a
  stable reference projection.
- Scalar bounded Newton-Raphson, interval Newton, bisection, secant, and Ridders
  research APIs with deterministic comparison evidence.
- Machine-readable qualification-surface summary evidence.
- A six-case, seven-candidate Method Observatory with complete fixed-step,
  fixed-accuracy, and fixed-work reports.
- A Bound Coverage Atlas reporting actual authority error, recursive internal
  bound, anchor deviation, phase, energy, empirical coverage, and stable
  fallback/rejection causes.
- Three explicitly reduced-order power-stage numerical experiments: buck-like,
  scheduled H-bridge RL, and DC-link RLC startup/interruption.
- Ten executable teaching and reproducibility exercises covering MNA,
  convergence, phase versus energy, shadow authority, deterministic packaging,
  isolated source/wheel equivalence, event alignment, empirical bound coverage,
  fallback forensics, and semantic ngspice mapping.
- Ten novice-oriented tutorial documents and 13 generated tutorial/comparison
  SVG figures integrated into the searchable HTML document tree.
- Citation, security, contribution, issue-reporting, architecture, and minimal
  reproducibility documentation.
- Canonical Mozilla Public License 2.0 text and PEP 639 package metadata.

### Changed

- Project identity advanced to package version `1.1.0` while remaining
  unpublished and unapproved.
- Event boundaries now force independent replay before multistep history reset;
  the reset no longer promotes a candidate-only event state or suppresses
  periodic authority age.
- Event replay uses at least eight refinement subdivisions, accumulates energy
  evidence over the actual replay substeps, and reapplies final energy and
  residual gates before accepting the anchored state.
- Post-event implicit startup now uses the configured reference method.
- Reference replay now distinguishes a tiny representable allowed step from an
  already-reached target and uses ULP-scaled replay-time comparisons.
- Simulation time controls and non-standard JSON constants must be finite, and
  compiled element topology fields are immutable after circuit construction.
- Sparse and nonlinear acceleration paths now reuse more validated structure
  without changing residual or fallback authority.
- Release qualification now captures exact workflow, environment, test,
  comparison, wheel, and repository-surface provenance.

### Release Boundary

- `1.1.0` is not a public release until one exact commit passes the complete
  candidate and tag qualification sequence and receives explicit human
  publication approval.
- No DOI is declared until an archive is created after qualification.

## [1.0.0] - 2026-08-24

### Added

- Initial public Bounded-Authority-Based-Circuit-Simulation release with
  variable-step AB2 prediction,
  semiexplicit MNA projection, implicit reference methods, contractive
  correction, stiffness and passivity gates, periodic replay anchors, JSON
  inputs, deterministic diagnostics, and a dependency-free wheel.
