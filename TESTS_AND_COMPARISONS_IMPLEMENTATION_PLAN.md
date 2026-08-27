# Bounded-Authority-Based-Circuit-Simulation Tests and Comparisons Implementation Plan

Plan date: August 24, 2026

## Objective

Extend BAB-CSv1 with a reproducible qualification system that:

- Tests mathematical invariants, fail-closed behavior, accuracy, convergence,
  event handling, long-horizon behavior, and packaging.
- Compares BAB-CS against its implicit authority methods, a test-only raw AB2
  baseline, analytic solutions where available, refined independent replay, and
  optionally an external circuit simulator.
- Measures whether the runtime bound diagnostics track observed deviations
  without overstating them as unconditional exact-trajectory guarantees.
- Produces deterministic evidence suitable for pull requests, scheduled runs,
  and release qualification.

## Compatibility and Claim Boundaries

The work shall preserve the existing BAB-CSv1 specification and public API.

- `disabled`, `shadow`, and `active` remain the only production rollout modes.
- A raw or uncorrected AB2 method may exist only in test or benchmark support;
  it shall not become a production rollout mode.
- Algebraic projection, per-step implicit reference evaluation, contractive
  correction, hard gates, and independent periodic re-anchoring remain enabled
  according to the existing configuration semantics.
- Internal estimated bounds remain relative to the implemented reference and
  model assumptions. Empirical comparisons shall not relabel them as proofs of
  exact physical trajectory error.
- Wall-clock results shall be informational. CI pass/fail decisions shall use
  deterministic numerical results and operation counts rather than timing.
- The released BAB-CSv1 wheel and its completion audit remain historical
  evidence; new qualification evidence shall be additive.

## Current Baseline

The starting repository contains 25 tests covering:

- Variable-step AB2 coefficients.
- Backward Euler, trapezoidal, and variable-step BDF2 behavior.
- Active, shadow, and disabled rollout semantics.
- Predictor caps, non-finite metrics, stiffness fallback, periodic and safety
  re-anchoring, event history reset, and bounded LC energy.
- Algebraic projection, singular topology rejection, basic nonlinear devices,
  waveforms, linear algebra, CLI output, and deterministic example replay.

GitHub Actions currently runs the regression suite on Python 3.11 through 3.14,
replays the included examples twice for deterministic comparison, builds a
wheel, installs it into a clean environment, and performs a CLI smoke test.

## Reference Hierarchy

Every comparison result shall identify its authority source explicitly.

1. **Analytic solution** — highest authority for circuits with a closed form.
2. **Independent refined replay** — implicit integration from a trusted initial
   condition using a separately configured smaller timestep.
3. **External simulator** — optional cross-implementation evidence for circuits
   representable without changing device semantics.
4. **BAB-CS implicit authority** — backward Euler, trapezoidal, or BDF2 under the
   same model and tolerance configuration.
5. **BAB-CS local step reference** — useful for runtime gates, but not an
   independent accumulated-trajectory authority.

Comparison reports shall record the authority level used for each error value.

## Standard Comparison Modes

The comparison harness shall support:

- Backward Euler authority.
- Trapezoidal authority.
- Variable-step BDF2 authority.
- BAB-CS shadow mode.
- BAB-CS active mode.
- Test-only raw variable-step AB2 on compatible reduced systems.

Where useful, controlled ablations may be implemented in test-only support to
compare projected AB2, contractively corrected AB2, and corrected plus anchored
AB2. Ablations shall not weaken the production integrator or enter the public
configuration schema.

## Standard Circuit Matrix

### Analytic Linear Cases

- RC charge and discharge.
- RL current rise and decay.
- Source-free overdamped RLC response.
- Source-free underdamped RLC response.
- Ideal LC oscillation with independently measured phase and energy behavior.
- Sinusoidally driven RC amplitude and phase after startup transients.

### Event and Discontinuity Cases

- Pulsed RC with zero rise and fall time.
- Pulsed RC with finite rise and fall time.
- Piecewise-linear source with multiple closely spaced breakpoints.
- Repeated switch transitions.
- An event reached after one or more rejected shortened attempts.

### Nonlinear Cases

- Diode clipping.
- Diode-capacitor charging and recovery.
- Switched RC load with large conductance ratio.
- Nonlinear solve failure induced by intentionally constrained iteration limits.

### Topology and Failure Cases

- Floating nodes and current sources.
- Conflicting ideal voltage constraints.
- Singular capacitor-loop or inductor-cutset examples within the documented
  unsupported boundary.
- Non-finite model, Jacobian, projection, and reference outputs.

## Required Metrics

### Accuracy

- Final-state absolute and scaled error.
- Maximum and RMS waveform error at common output times.
- Observed convergence ratio under timestep refinement.
- Oscillator amplitude error, phase error, period error, and energy drift.
- Event-time and immediate post-event state error.

### Bound Behavior

- Predictor/reference error.
- Corrected/reference error.
- Recursive estimated bound.
- Independent anchor deviation.
- Observed error divided by the internal bound, clearly labeled as an empirical
  coverage ratio rather than a proof ratio.
- Predictor amplification, correction gain, closed-loop gain, and contraction
  status.

### Robustness

- Accepted and rejected attempts.
- Periodic and safety re-anchors.
- Implicit stiffness fallbacks.
- Minimum, maximum, and mean accepted timestep.
- Failure reason and failure time for fail-closed cases.

### Computational Work

- Algebraic projection count and total iterations.
- Implicit reference solve count and total Newton iterations.
- Independent replay step count and iterations.
- Differential Jacobian evaluation count.
- Accepted steps per simulated interval.
- Median wall time and dispersion over repeated runs, reported separately from
  deterministic acceptance results.

## Work Packages

### TC-001 — Shared Qualification Support

Create reusable helpers for circuit construction, trace interpolation, analytic
solutions, scaled norms, convergence estimates, phase extraction, result
comparison, and deterministic report serialization.

Proposed files:

- `tests/support/circuits.py`
- `tests/support/analytic.py`
- `tests/support/metrics.py`
- `tests/support/raw_ab2.py`
- `tests/support/__init__.py`

Acceptance gates:

- Helpers contain no production authority decisions.
- Analytic functions are directly unit tested at initial conditions and selected
  known points.
- Trace comparisons reject incompatible state dimensions and non-monotonic time
  sequences.

### TC-002 — Integrator and Configuration Boundaries

Add focused unit tests for:

- Invalid tolerances, gains, rollout modes, anchor settings, and rejection
  settings.
- Constant and linearly varying derivative cases for fixed and variable-step
  AB2.
- Positive-step and vector-dimension validation.
- Maximum step-ratio boundaries and implicit restart when AB history is invalid.
- Correction-gain monotonicity and full reference authority when contraction
  cannot be established.

Proposed file:

- `tests/test_integrator_boundaries.py`

Acceptance gates:

- Every configuration validation branch has a deterministic test.
- The exact permitted step-ratio endpoints use AB history; values outside them
  use implicit startup.
- No test requires implementation-private mutation of frozen state objects.

### TC-003 — Hard Failure Gates

Isolate and test each fail-closed path:

- Predictor/reference cap.
- Algebraic residual cap.
- Full residual cap.
- Positive energy-injection cap.
- Projection failure.
- Implicit reference failure.
- Independent replay failure.
- Non-finite state or metric.
- Minimum timestep and maximum rejection exhaustion.

Proposed file:

- `tests/test_failure_gates.py`

Acceptance gates:

- Each test identifies the expected rejection reason.
- A rejected candidate does not commit its state or multistep history.
- Retry behavior reduces the attempted timestep and terminates at the configured
  limit.

### TC-004 — Bound Recurrence Verification

Verify the implemented internal bound model separately from empirical exact-error
comparisons.

Required tests:

- Recompute normalized residual defect from recorded step data.
- Recompute `B_next = q * B_current + delta` for each non-reset step.
- Verify finite `q < 1` whenever `certified_contractive` is true.
- Verify implicit full-authority steps use zero local closed-loop gain.
- Verify events, history resets, and re-anchors clear the recursive bound.
- Verify corrected/reference error does not exceed predictor/reference error for
  accepted active AB steps.

Proposed file:

- `tests/test_bound_model.py`

Acceptance gates:

- The recurrence agrees with emitted metrics within a documented floating-point
  tolerance.
- Tests distinguish recurrence correctness from exact-trajectory coverage.
- Any missing metric needed for independent recomputation is added explicitly to
  diagnostics rather than inferred from unrelated values.

### TC-005 — Analytic Accuracy and Convergence

Implement timestep-refinement tests for the analytic linear circuit matrix.

Required comparisons:

- Backward Euler demonstrates approximately first-order convergence.
- Trapezoidal and BDF2 demonstrate approximately second-order convergence on
  smooth compatible problems.
- Test-only raw AB2 demonstrates approximately second-order convergence on its
  compatible reduced linear cases.
- Active BAB-CS accuracy is measured against the analytic solution and its
  observed order is reported. A strict order gate shall be introduced only after
  correction and re-anchor effects are characterized.
- Shadow mode is compared against the selected implicit authority under
  identical anchor and event settings.

Proposed file:

- `tests/test_accuracy.py`

Acceptance gates:

- Tests use at least three refinement levels where practical.
- Assertions use convergence ranges and physically scaled error tolerances, not
  exact floating-point traces.
- Analytic comparisons share common output times rather than comparing unequal
  adaptive grids directly.

### TC-006 — Long-Horizon Bounds and Passivity

Extend oscillator and dissipative testing beyond short smoke intervals.

Required experiments:

- Ideal LC over 10, 100, and optionally 1,000 periods.
- LC sweeps over timestep and anchor interval.
- Damped RLC energy decay.
- Passive RC and RL monotonic energy behavior.
- Comparison of raw AB2, active BAB-CS, and refined implicit replay.

Proposed files:

- `tests/test_long_horizon.py`
- `benchmarks/cases/lc_long.json`
- `benchmarks/cases/rlc_damped.json`

Acceptance gates:

- Fast 10-period cases run in pull-request CI.
- Longer cases report amplitude, phase, energy, anchor deviation, and empirical
  bound coverage in scheduled CI.
- Energy bounds are never presented as phase bounds.

### TC-007 — Event and Nonlinear Qualification

Add repeated-event and nonlinear comparisons using refined replay authority.

Proposed files:

- `tests/test_events.py`
- `tests/test_nonlinear.py`
- `benchmarks/cases/diode_clip.json`
- `benchmarks/cases/switched_rc.json`

Acceptance gates:

- Every known breakpoint is reached exactly once within the documented time
  tolerance.
- AB history never crosses an event.
- The first accepted step after an event uses implicit startup.
- Nonlinear comparisons report solver convergence, residuals, and iteration
  counts in addition to waveform error.

### TC-008 — Comparison Runner

Create a deterministic command-line runner that executes a declared matrix of
cases, methods, timesteps, anchor intervals, and repeats.

Proposed files:

- `tools/compare_methods.py`
- `benchmarks/manifest.json`
- `benchmarks/cases/`
- `docs/COMPARISON_PROTOCOL.md`

Required behavior:

- Validate the manifest before running simulations.
- Record source commit, Python version, platform, method configuration, circuit
  parameters, authority source, and output schema version.
- Produce a machine-readable JSON result and a flat CSV table.
- Use deterministic ordering and stable float serialization.
- Refuse to overwrite existing release evidence unless explicitly requested.
- Return nonzero only for deterministic numerical qualification failures, not
  wall-clock variation.

Acceptance gates:

- Two identical runs produce byte-identical numerical reports after excluding a
  separately stored timing section.
- Invalid method/circuit combinations fail with an explicit reason.
- The runner can execute a single case locally and the complete manifest in CI.

### TC-009 — Diagnostic Extension

Extend observability only where comparison evidence cannot be computed from
existing outputs.

Candidate additions:

- Maximum anchor deviation in summary output.
- Minimum, maximum, and mean accepted timestep.
- Total reference and projection iterations.
- Reference solve, projection, Jacobian evaluation, and replay-step counts.
- Per-step reset reason and rejection reason categories.

Proposed production files:

- `src/babcs/bounded.py`
- `src/babcs/simulator.py`
- `src/babcs/io.py`

Acceptance gates:

- New output fields are additive.
- Existing CSV columns and summary keys retain their meanings.
- Counters are tested against small cases with manually known operation counts.
- Deterministic output hashes are deliberately regenerated and reviewed rather
  than silently replaced.

### TC-010 — Optional External Simulator Comparison

Add an opt-in adapter for externally validating supported linear and simple
nonlinear circuits.

Proposed files:

- `tools/compare_external.py`
- `benchmarks/external/`
- `docs/EXTERNAL_COMPARISON.md`

Acceptance gates:

- External execution is never required for the default package installation or
  pull-request CI.
- Generated external netlists preserve BAB-CS component values, initial
  conditions, waveform timing, and sign conventions.
- Comparisons interpolate both tools onto declared common output times.
- Tool name, version, command, netlist hash, and raw-output hash are recorded.
- Unsupported semantic mappings fail closed rather than approximating silently.

### TC-011 — CI Qualification Tiers

Split validation by purpose and cost.

#### Pull Request CI

- Existing Python 3.11 through 3.14 regression matrix.
- Unit, hard-gate, recurrence, analytic short-case, and short event tests.
- Deterministic comparison-runner smoke case.
- Wheel build and installed-wheel smoke test.

#### Scheduled CI

- Long-horizon oscillator cases.
- Timestep and anchor-interval sweeps.
- Repeated timing samples.
- Optional external comparison where the runner is available.
- Upload JSON, CSV, logs, and plots as workflow artifacts.

#### Release Qualification

- Full regression and scheduled comparison matrix.
- Installed-wheel execution of the comparison smoke suite.
- Source commit, wheel hash, report hashes, and environment metadata.
- Human review of any changed numerical threshold, baseline, or deterministic
  artifact before release publication.

Proposed workflow files:

- `.github/workflows/ci.yml`
- `.github/workflows/comparisons.yml`

Acceptance gates:

- Pull-request CI remains deterministic and bounded in duration.
- Scheduled jobs do not block unrelated pull requests.
- Release evidence identifies the exact source and wheel under test.

### TC-012 — Documentation and Evidence Audit

Update documentation after the tests and runner exist.

Proposed files:

- `README.md`
- `docs/COMPARISON_PROTOCOL.md`
- `docs/BAB_CSV1_COMPLETION_AUDIT.md` or a new additive qualification audit.

Acceptance gates:

- Documentation distinguishes analytic truth, independent replay, local
  reference, and external comparison.
- Performance results state that BAB-CSv1 performs an implicit reference solve
  on every eligible AB step and is not expected to outperform pure implicit
  integration in its current architecture.
- Claims cite deterministic artifacts and exact source hashes.
- Historical completion evidence is not rewritten to imply that new tests were
  part of the original v1 release.

## Comparison Protocol

Each numerical comparison shall run under three complementary controls.

### Fixed Timestep

Use identical nominal timesteps and event boundaries to expose method behavior
under equal temporal discretization.

### Fixed Accuracy

Refine each method until it reaches a declared error target, then compare
accepted steps, nonlinear iterations, projections, references, and replay work.

### Fixed Work

Compare methods under a declared operation budget, preferably total algebraic
and nonlinear iterations rather than wall time. This prevents faster hardware or
runtime noise from changing the qualification result.

All protocols shall use the same circuit parameters, initial conditions, stop
time, output sample times, error norm, and reference authority.

## Threshold Policy

- Mathematical identities and mode semantics use strict deterministic tests with
  floating-point tolerances derived from machine precision and problem scale.
- Convergence tests use order ranges across multiple refinements.
- Long-horizon physical metrics use explicit absolute and relative tolerances.
- Empirical bound coverage begins as characterization evidence. It becomes a
  hard gate only after a documented derivation justifies the relationship being
  asserted.
- Wall time is never a correctness threshold.
- Threshold changes require an explanation, before/after evidence, and review;
  regenerating expected values alone is insufficient.

## Implementation Sequence

1. Implement TC-001 shared qualification support.
2. Implement TC-002 and TC-003 boundary and failure tests.
3. Implement TC-004 recurrence verification.
4. Implement TC-005 analytic accuracy and convergence.
5. Implement TC-009 diagnostic counters required by comparisons.
6. Implement TC-008 comparison runner and protocol documentation.
7. Implement TC-006 and TC-007 long-horizon, event, and nonlinear suites.
8. Implement TC-011 CI tiers.
9. Implement TC-010 optional external comparison.
10. Complete TC-012 documentation and requirement-to-evidence audit.

## Completion Gates

The tests and comparisons program is complete only when:

- Every existing BAB-CSv1 requirement remains covered and passing.
- Each hard failure gate has an isolated regression test.
- The recursive bound is independently recomputed from emitted diagnostics.
- Analytic linear cases demonstrate the expected convergence behavior for the
  authority integrators and test-only raw AB2.
- Active BAB-CS has documented accuracy, bound, fallback, and anchor behavior
  across timestep and anchor-interval sweeps.
- Long-horizon tests report phase separately from energy.
- Comparison reports identify their authority source and complete configuration.
- Deterministic numerical reports reproduce byte-for-byte.
- Pull-request, scheduled, and release workflows pass at the exact candidate
  source hash.
- The installed release-candidate wheel passes the smoke comparison suite.
- A requirement-to-evidence audit lists every claim, test, artifact, source hash,
  wheel hash, known limitation, and unresolved result.

## Deferred Work

The following are intentionally outside this plan unless separately specified:

- Production sparse matrix infrastructure.
- Large industrial SPICE benchmark suites.
- Arbitrary analog threshold root finding.
- Higher-index MNA regularization.
- A production mode that skips the every-step implicit reference.
- Formal proof that the internal bound encloses exact physical trajectory error
  for every supported nonlinear or discontinuous circuit.
