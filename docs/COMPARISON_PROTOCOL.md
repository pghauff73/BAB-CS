# BAB-CS Comparison Protocol

## Purpose

The comparison harness characterizes accuracy, boundedness, robustness, and
deterministic work for BAB-CS and its authority integrators. It does not turn a
local predictor/reference deviation into a proof of exact physical trajectory
error.

The canonical matrix is `benchmarks/manifest.json`; circuit inputs are under
`benchmarks/cases/`. The runner is `tools/compare_methods.py`.

## Authority Hierarchy

Every reported error names its authority source.

1. **Analytic solution** for supported closed-form linear circuits.
2. **Independent refined replay** from the trusted initial condition with a
   separately configured smaller implicit timestep.
3. **External simulator** as optional cross-implementation evidence when device
   semantics can be mapped without alteration.
4. **BAB-CS implicit authority** using backward Euler, trapezoidal, or BDF2.
5. **BAB-CS local step reference** for runtime gating only; it is not an
   independent accumulated-trajectory authority.

The deterministic runner currently uses analytic or refined-replay authorities.
External results are produced separately by `tools/compare_external.py` so that
their toolchain and semantic-mapping provenance remain explicit.

## Compared Methods

- `backward_euler`: production implicit reference in disabled rollout mode.
- `trapezoidal`: production implicit reference in disabled rollout mode.
- `bdf2`: production variable-step BDF2 reference in disabled rollout mode.
- `shadow`: AB2 diagnostics run while the implicit reference remains
  authoritative.
- `active`: projected and contractively corrected AB2 with every-step implicit
  reference and independent periodic replay anchors.
- `bounded_explicit_euler`, `bounded_heun`, and `bounded_rk23`: explicit
  candidates using the shared every-step reference/correction controller.
- `bounded_backward_euler`, `bounded_trapezoidal`, and `bounded_bdf2`: implicit
  candidates paired with a distinct implicit reference.
- `bounded_ab2_fast`, `bounded_heun_fast`, and `bounded_rk23_fast`: embedded
  candidates with four-step scheduled references, dynamic bound checkpoints,
  and periodic independent replay.
- `raw_ab2`: test-only reduced-system variable-step AB2. It is not a production
  rollout mode and cannot bypass production safety gates.

The manifest rejects unknown methods, missing inputs, duplicate case IDs,
invalid authorities, and unsupported raw-model mappings.

## Circuit Matrix

The standard matrix includes RC and RL steps, underdamped and overdamped RLC,
sinusoidally driven RC, ideal LC long-horizon oscillation, diode clipping, and a
repeated switched RC case. Unit and qualification tests additionally cover
charge/discharge, pulse and PWL boundaries, closely spaced events, nonlinear
recovery, topology failures, and isolated hard-gate failures.

## Common Sampling

For each case, every method uses the same circuit parameters, initial state,
start and stop times, event boundaries, selected state indices, and common
output sample times. Method traces are interpolated only for evaluation at those
common times. Authority construction is independent of the candidate method.

## Three Controls

### Fixed Timestep

Results with equal `nominal_step` expose method behavior under equal temporal
discretization. Event boundaries are still reached exactly.

### Fixed Accuracy

For each declared target in `accuracy_targets`, the report selects the least
deterministic-work result that reaches the target. Failure to reach a target is
reported rather than silently relaxed.

### Fixed Work

For each declared `work_budgets` value, the report selects the most accurate
result within the budget. Deterministic work is the sum of accepted steps,
candidate and reference circuit evaluations and algebraic iterations,
predictor/corrected projection iterations, differential Jacobian evaluations,
and replay steps, circuit evaluations, and algebraic iterations. Each source
counter is also reported independently. Wall time is excluded so hardware noise
cannot change qualification.

## Metrics

Accuracy fields include final-state maximum absolute error, maximum waveform
error, RMS waveform error, per-state scaled error, and observed convergence
order. Oscillator cases report sampled amplitude error, final phase error,
relative period error, and relative energy span as separate quantities.

Bound fields include candidate/reference error, embedded error,
corrected/reference error, recursive estimated bound, dynamic reference
checkpoints, pre-reset bound, independent anchor deviation, and the empirical
anchor-error-to-pre-reset-bound ratio. That ratio is characterization evidence,
not a formal coverage proof.

Robustness fields include accepted/rejected attempts, rejection categories,
history-reset reasons, implicit fallbacks, periodic/safety anchors, and accepted
timestep statistics.

Work fields include candidate solves/evaluations/iterations, projection counts
and iterations, reference solves, reference Newton and algebraic iterations,
replay work, differential Jacobian evaluations, and a deterministic aggregate
work unit.

## Determinism and Provenance

Run the complete matrix:

```bash
PYTHONPATH=src python tools/compare_methods.py \
  --output artifacts/numerical.json \
  --csv-output artifacts/numerical.csv \
  --plot-output artifacts/error-by-step.svg
```

Add separate timing characterization:

```bash
PYTHONPATH=src python tools/compare_methods.py \
  --output artifacts/numerical.json \
  --timing-output artifacts/timing.json \
  --timing-repeats 3
```

Use `--case CASE_ID` repeatedly to select cases and `--quick` for the smallest
configured timestep/anchor subset. Outputs fail closed on overwrite unless
`--overwrite` is explicit.

The numerical report records the source commit, dirty state, deterministic
source-tree SHA-256, manifest hash, runner identity, interpreter/platform
metadata, case input hashes, circuit elements, simulation settings, complete
method configuration, and authority. The source-tree hash covers Git tracked and
untracked non-ignored files while excluding generated build/evidence directories
and the self-referential qualification and performance audit documents.
It contains no wall-clock measurements. Under an identical environment, the
numerical JSON, flattened CSV, and SVG are expected to reproduce byte-for-byte.

The timing report records repeated elapsed samples separately. Wall time is
never a correctness or release threshold.

## Threshold Policy

- Mathematical identities and mode semantics use deterministic tolerances
  derived from machine precision and problem scale.
- Convergence is gated by an order range across refinements, not one golden
  output value.
- Long-horizon phase, energy, and bound checks use explicit tolerances.
- Empirical bound coverage remains characterization until a documented
  derivation supports a hard relationship.
- Threshold or baseline changes require rationale, before/after evidence, and
  human review; regenerating expected output alone is insufficient.

## Performance Boundary

The default active mode performs an implicit reference solve on every candidate
step and may also perform candidate/correction projections, differential
Jacobian evaluation, and periodic refined replay. Built-in circuits use exact
MNA sensitivity Jacobians plus bounded topology/factorization caches; extension
subclasses retain a finite-difference fallback unless they provide an override.
The deterministic default uses the built-in dense solver. An explicit optional
`auto` backend uses SciPy SuperLU only beyond measured matrix-size, sparsity, and
right-hand-side crossovers; `scipy` forces that backend. Diode circuits bypass
the linear caches but may use the optional sparse backend for sufficiently large
fresh Newton systems. Embedded AB2, Heun, and RK23
variants may defer references, but dynamic bound checkpoints deliberately
restore reference work in difficult regions. Work comparisons describe the cost
of bounded, inspectable behavior; timing rows remain local characterization, not
a general speed claim.

## Qualification Tiers

- Pull-request CI runs Python 3.11 through 3.14 tests, deterministic examples,
  a deterministic comparison smoke, optional SciPy backend qualification, and
  installed-wheel smoke.
- Scheduled CI enables `BABCS_LONG_TESTS=1`, runs the full comparison/timing
  matrix, runs `ngspice` mappings, hashes evidence, and uploads artifacts.
- Release qualification enables both `BABCS_LONG_TESTS=1` and
  `BABCS_VERY_LONG_TESTS=1`, builds the wheel, runs tests with the installed
  wheel, generates comparison evidence, and records exact hashes.

Release publication still requires human review of changed thresholds,
baselines, and deterministic artifacts.
