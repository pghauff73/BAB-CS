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
- Scalar bounded Newton-Raphson, interval Newton, bisection, secant, and Ridders
  research APIs with deterministic comparison evidence.
- Machine-readable qualification-surface summary evidence.
- Citation, security, contribution, issue-reporting, architecture, and minimal
  reproducibility documentation.
- Canonical Mozilla Public License 2.0 text and PEP 639 package metadata.

### Changed

- Project identity advanced to package version `1.1.0` while remaining
  unpublished and unapproved.
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
