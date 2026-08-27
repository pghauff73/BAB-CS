# Bounded-Authority-Based-Circuit-Simulation Performance Optimization Audit

## Status

This document records a locally validated candidate optimization pass relative
to commit `8dad1f1bb41acf343c36dae8daeb932c137fb268` on August 24, 2026. The
candidate is not a release qualification or publication claim until it is
committed and the repository workflows pass that exact commit.

The pass deliberately preserves the qualified default architecture: active and
shadow modes still compute an implicit reference on every eligible AB step, and
periodic independent replay remains enabled. Replay refinement is now
topology-aware, but no reference solve or anchor interval was removed, made
optional, or evidence-skipping.

## Changes

### Replay correctness

- Independent BDF2 replay now carries the previous differential state and
  previous accepted substep across the full replay window.
- The first replay substep still starts with backward Euler, as required when
  BDF2 history does not yet exist.
- A regression verifies that replayed BDF2 matches explicitly history-fed BDF2
  and no longer collapses to a backward-Euler sequence.
- The replay refinement count remains four for phase-sensitive C+L topologies
  and backward-Euler replay, while other built-in topologies use two substeps by
  default. The fixed-refinement behavior remains available by configuration.
- After replay startup, uniform replay windows use an AB3 extrapolation after
  two matching substeps. Variable or nonmatching substeps retain the
  variable-step AB2 initial guess. Neither predictor changes the reference
  method, residual equation, convergence gate, or backward-Euler startup.

### Repeated Jacobian work

- `BABCSHistory` caches the differential-Jacobian norm associated with its
  stored previous evaluation.
- Regular active/shadow steps calculate one new norm instead of recalculating
  both adjacent-state norms. Startup, event reset, fallback, and independent
  re-anchor paths invalidate the cache rather than reusing uncertain data.
- Standard `Circuit` instances derive the differential Jacobian from exact MNA
  sensitivities at the accepted algebraic solution. This removes perturbed
  circuit evaluations from implicit Newton and bound estimation. Subclasses
  preserve the finite-difference fallback or their own override behavior.

### Nonlinear and implicit solves

- Algebraic Newton line-search trials assemble residuals without allocating or
  stamping an unused dense Jacobian.
- An accepted algebraic trial that already satisfies the configured tolerance
  returns immediately instead of performing a redundant full assembly.
- The implicit integrator returns the evaluation that produced its converged
  residual instead of solving the identical circuit state once more.
- A full-reference correction reuses the existing implicit reference
  evaluation instead of projecting the same differential state again.

### Linear algebra kernels

- Scalar linear systems bypass generic augmented-matrix elimination while
  preserving the same scale-relative pivot rejection rule.
- Dense-system scaling is calculated while the augmented matrix is built,
  removing a separate matrix-norm traversal from every solve.
- Scalar infinity norms and finite-difference Jacobians use direct paths rather
  than allocating general dense structures.
- Infinity norms now propagate `NaN` deterministically instead of depending on
  value ordering inside `max`.

### Reproducible packaging

- The wheel backend now fixes ZIP timestamps and file modes instead of
  inheriting the wall-clock build time.
- A regression builds the wheel twice in independent directories and requires
  byte-identical archives with canonical metadata.

These changes do not relax a residual, contraction, passivity, stiffness,
event, timestep, or re-anchor gate.

## Exact Baseline Comparison

The baseline and candidate were run from separate worktrees on CPython 3.14.6
and an AMD Ryzen 9 7900X. Each round used five warmups followed by 25 timed
executions of the nonlinear `diode_clip` case to `1.0e-3` seconds with a
`4.0e-6` nominal step, active mode, a 50-step anchor interval, and four anchor
substeps.

| Measurement | Baseline | Candidate | Reduction |
| --- | ---: | ---: | ---: |
| Round 1 median | 0.144777326 s | 0.096212455 s | 33.545% |
| Round 2 median | 0.141734707 s | 0.097759334 s | 31.027% |
| Mean of medians | 0.143256017 s | 0.096985895 s | 32.299% |
| Differential Jacobian evaluations | 498 | 254 | 48.996% |
| Per-step reference circuit evaluations | 1,056 | 806 | 23.674% |
| Replay circuit evaluations | 4,248 | 3,248 | 23.540% |

Against the already optimized pre-kernel candidate, the linear-algebra changes
reduced the same benchmark's mean of medians by a further 8.349% without
changing any operation count. The final 100-result numerical matrix is exactly
equal to the pre-kernel candidate matrix, including diagnostics, work counters,
and derived analyses.

The full 100-result method matrix produced identical per-result accuracy,
bound, oscillator, authority, configuration, and selected-step values. Its
convergence analysis was also identical. Work-derived analyses changed because
the measured deterministic work changed:

| Full-matrix work counter | Baseline | Candidate | Reduction |
| --- | ---: | ---: | ---: |
| Differential Jacobian evaluations | 35,680 | 18,682 | 47.640% |
| Per-step reference circuit evaluations | 136,151 | 106,922 | 21.468% |
| Replay circuit evaluations | 333,810 | 263,598 | 21.034% |
| Explicit projections | 35,680 | 33,095 | 7.245% |
| Deterministic work units | 1,020,516 | 918,043 | 10.041% |

## Follow-On Replay and Sensitivity Gain

A controlled follow-on comparison used five warmups and 25 timed runs of the
nonlinear `diode_clip` case to `1.0e-3` seconds with a `2.0e-6` nominal step and
a 50-step anchor interval. The pre-loop path used fixed four-substep replay,
finite-difference differential Jacobians, and Euler replay initialization. The
retained path used topology-aware two-substep replay, exact MNA sensitivities,
and AB2 replay initialization.

| Method | Pre-loop median | Retained median | Reduction |
| --- | ---: | ---: | ---: |
| Active bounded AB2 | 0.194835465 s | 0.115822253 s | 40.554% |
| Fast bounded RK23 | 0.188275857 s | 0.112518345 s | 40.238% |

For active bounded AB2, replay steps fell from 2,001 to 1,000 and replay circuit
evaluations fell from 6,499 to 1,998. Its maximum waveform error against the
same refined authority remained `9.176019653e-4`. For fast bounded RK23, replay
steps fell from 2,000 to 1,000, replay circuit evaluations fell from 6,496 to
1,998, and maximum waveform error changed only from `7.728687513e-5` to
`7.730052969e-5`.

The AB2 replay initial guess is workload-dependent: a separate smooth RC
measurement reduced median runtime by roughly 30-32%, while the diode runtime
was neutral. The optimization remains because it materially reduces linear
reference work without weakening convergence tests.

## Scaling and Factorization Gain

The next optimization loop targeted repeated dense factorization after exact
MNA sensitivities exposed multi-state scaling cost. The retained design:

- solves all sensitivity columns through one multi-right-hand-side
  factorization;
- caches linear differential Jacobians by component values and selected switch
  topology;
- caches algebraic and implicit residual factorizations by topology, method,
  and step shape;
- assembles residual-only systems after a linear algebraic factor is available;
- bounds each cache to 128 entries so long-running adaptive simulations cannot
  accumulate unbounded topology or step-shape state;
- bypasses all caches for diode circuits and preserves finite-difference
  behavior for `Circuit` subclasses.

A controlled comparison used five warmups and 15 timed runs per case. The
pre-loop path used one dense factorization per sensitivity column and no
linear-topology caches. The optimized path includes all retained scaling
changes. Endpoints were bit-identical in every case.

| Workload | Dynamic states | Pre-loop median | Optimized median | Reduction |
| --- | ---: | ---: | ---: | ---: |
| Nonlinear diode clip | 1 | 0.121379363 s | 0.120120340 s | 1.037% |
| RC charge | 1 | 0.055779174 s | 0.041220080 s | 26.101% |
| Parallel RLC | 2 | 0.117980812 s | 0.076879102 s | 34.838% |
| Four independent LC tanks | 8 | 0.100803271 s | 0.028100581 s | 72.123% |
| Eight independent LC tanks | 16 | 0.202783340 s | 0.025254669 s | 87.546% |

Isolated characterization showed multi-right-hand-side sensitivities reducing
the 8-state and 16-state cases by 33.1% and 52.7%; linear Jacobian caching by
34.1% and 49.0%; algebraic factor caching by 19.8% and 24.3%; and implicit
factor caching by 19.4% and 26.0%. These percentages are incremental within
their individual controlled comparisons and must not be added together.

## Optional Sparse Factorization and Compiled Stamping Gain

The next retained loops added an explicit optional SciPy SuperLU backend and
then removed dense assembly from its hot path without changing the
dependency-free `dense` default. `Circuit` now compiles its algebraic CSC
structure, terminal locations, device Jacobian locations, constraint locations,
and differential-sensitivity right-hand sides once. Eligible sparse evaluations
update only the numeric values. The SciPy adapter reuses a validated CSC
template and copies the numeric data before factorization.

`auto` uses sparse reusable factorizations from 16 unknowns, one-shot sparse
solves from 32 unknowns, and the 16-unknown multi-right-hand-side crossover only
when at least eight columns can amortize the backend overhead. Systems above 35%
structural density remain dense. Explicit `scipy` selection is available for
controlled characterization and fails clearly when the optional dependency is
unavailable.

An interleaved local comparison used three warmups and 11 timed executions per
backend for independent LC tanks over `2.0e-4` seconds with a `2.0e-6` nominal
step. The sparse timings are incremental against the already optimized dense
path, not against the original project baseline. Endpoints were bit-identical.

| Dynamic states | Dense median | Auto median | Reduction |
| ---: | ---: | ---: | ---: |
| 8 | 0.029026481 s | 0.029071947 s | -0.157% |
| 16 | 0.053386233 s | 0.042590269 s | 20.222% |
| 32 | 0.118676441 s | 0.067108034 s | 43.453% |
| 64 | 0.344328509 s | 0.124991749 s | 63.700% |

A second interleaved comparison used five warmups and 15 timed executions per
backend for independent driven diode channels over `1.0e-4` seconds with a
`2.0e-6` nominal step. Auto intentionally remained dense below the fresh-factor
crossover; larger nonlinear systems used direct compiled CSC stamping for
Newton and sensitivity solves. Endpoints were bit-identical across every timed
execution and backend.

| Diode channels | Algebraic unknowns | Dense median | Auto median | Reduction |
| ---: | ---: | ---: | ---: | ---: |
| 2 | 8 | 0.017495564 s | 0.017812335 s | -1.811% |
| 4 | 16 | 0.038361584 s | 0.038581474 s | -0.573% |
| 8 | 32 | 0.119441513 s | 0.051047508 s | 57.262% |
| 16 | 64 | 0.500826076 s | 0.073091419 s | 85.406% |
| 32 | 128 | 2.707985152 s | 0.122329999 s | 95.483% |

The small negative rows are retained as crossover evidence, not described as
speedups. The auto policy keeps the underlying dense numerical path there.

An isolated comparison against the preceding sparse-factor candidate, which
still assembled densely and converted each matrix, measured direct-CSC
reductions of 35.974%, 54.299%, and 69.144% at 32, 64, and 128 algebraic
unknowns respectively. Those percentages are incremental implementation gains,
not additional factors to add to the dense-versus-auto table.

The follow-on implicit loop now solves the exact coupled algebraic/dynamic block
system directly instead of explicitly materializing the dense differential
Jacobian and its Schur complement for nonlinear Newton updates. The compiled
block has the form

```text
[ A   -B ] [delta_u] = [        0]
[-hD   aI ] [delta_x]   [-residual]
```

where `A` is the algebraic Jacobian, `A du/dx = B`, `D du/dx` is the dynamic
Jacobian, and `aI - hD A^-1 B` is exactly the prior implicit residual Jacobian.
Structural-equivalence tests compare the block update with the explicitly
formed Schur update. Against the immediately preceding direct-CSC candidate,
the block solve reduced the 32-, 64-, and 128-unknown medians by a further
2.342%, 6.518%, and 23.284%, with bit-identical simulation endpoints in the
measured workload.

The final backend loop reuses one mutable CSC value workspace per structural
pattern and thread instead of allocating and validating a new SciPy matrix for
every factorization. The per-thread cache is bounded to 128 structures, and
regressions verify that previously returned SuperLU factor objects remain
independent after the workspace is reused. An isolated 128-unknown
factorization microbenchmark reduced setup from approximately 55 microseconds
to 20 microseconds. End-to-end medians fell a further 10.918%, 9.826%, and
2.860% at 32, 64, and 128 unknowns respectively.

The final assembly loop splits the sparse full-Jacobian path from the dense and
residual-only paths, then fuses voltage lookup, residual stamping, and compiled
CSC value updates inside each device loop. This removes nested helper dispatch
without vectorizing, changing component mutability, or altering arithmetic
ordering. Against the workspace-reuse candidate, medians fell a further 3.963%,
4.195%, and 6.534% at 32, 64, and 128 unknowns respectively. Existing dense
versus sparse structural-equivalence tests continued to compare every residual
and Jacobian entry exactly.

## Continued Sparse and Replay Gains

The next measured loops retained several independent reductions. Each
percentage below is incremental against the immediately preceding candidate;
the values must not be added together.

### Fill-gated SuperLU ordering

Repeated sparse structures start with `COLAMD`. On the fourth factorization,
the implementation probes `NATURAL` ordering with the same numeric values and
retains it only when the existing singularity gate passes and `L.nnz + U.nnz`
is no greater than the `COLAMD` fill. A failed cached `NATURAL` factorization
permanently falls back to `COLAMD` for that bounded thread-local workspace.

Three balanced rounds with five warmups and 15 paired runs measured reductions
of 1.128%, 2.084%, and 1.997% at 32, 64, and 128 unknowns respectively. The
minimum round reductions were 0.929%, 1.778%, and 1.706%. Endpoints remained
exactly equal.

### Residual and sampled-input assembly

Large sparse residual-only evaluations now stamp directly into the residual
without constructing Jacobian values. Arithmetic order remains
reciprocal-then-multiply so the sparse and original paths remain exactly equal.
Three balanced rounds measured mean reductions of 2.195%, 1.891%, and 2.275%
at 32, 64, and 128 unknowns.

For sparse systems with at least 64 algebraic unknowns, one evaluation samples
each current-source waveform, switch control, and constraint waveform once and
reuses those values through Newton and power accounting. Mutable waveform
objects are still dereferenced on every new evaluation. Mean reductions were
2.263% at 64 unknowns and 2.836% at 128 unknowns; the 32-unknown production path
is intentionally unchanged.

Constraint target positions are also precompiled while their mutable source
objects and state values remain live. Isolated target-construction reductions
ranged from 22.86% to 36.66%. End-to-end results were positive at 32 and 128
unknowns but noisy at 64 unknowns, so this is retained as an isolated kernel
gain rather than claimed as a uniform simulation speedup.

### Higher-order replay initialization

After two matching uniform replay substeps, the Newton initial guess is

```text
x[n] + h * (23 f[n] - 16 f[n-1] + 5 f[n-2]) / 12.
```

The first replay step remains unpredicted and variable replay spacing falls
back to the existing variable-step AB2 formula. The implicit method, residual,
convergence test, and backward-Euler restart are unchanged.

Three balanced rounds measured reductions of 16.394%, 17.628%, and 19.076% at
32, 64, and 128 unknowns, with minimum round reductions of 15.883%, 17.456%,
and 18.762%. Replay Newton iterations fell from 46, 52, and 62 to one, and
replay circuit evaluations fell from 146, 152, and 162 to 101.

The changed predictor intentionally changes tolerance-limited replay endpoints.
Against a refined replay with a `1.25e-7` step, the prior AB2 endpoint had a
maximum error of `6.934961321869437e-08`; the AB3 endpoint error was
`1.4848380275322981e-08`. This supports retaining the change as both a
performance and accuracy improvement rather than treating endpoint equality
with the lower-order initial guess as the criterion.

### Norm-work elimination

An accepted algebraic solution caches its infinity norm only for the exact
accepted tuple object; an equal copied sequence is recomputed. The validated
dynamic-state infinity norm is stored in `CircuitEvaluation` during the
mandatory finite-state scan and reused by the implicit residual gate. These
changes measured mean reductions of 1.622-2.365% and 1.587-2.022%
respectively. In the 128-unknown profile, total infinity-norm calls fell from
1,903 before these changes to 1,251.

### Native sparse differential-Jacobian norm

Eligible large nonlinear built-in circuits now solve all precompiled
differential-sensitivity right-hand sides as one native NumPy array and compute
the induced infinity norm without materializing a Python dense Jacobian. The
result is conservatively rounded upward by a dimension-scaled floating-point
envelope. Dense, small, and subclass paths continue to materialize the existing
Jacobian so extension behavior is unchanged.

Three balanced rounds measured mean reductions of 2.960% at 64 unknowns and
7.508% at 128 unknowns, with minimum round reductions of 2.575% and 7.019%.
The 32-unknown case remains on the original path. Simulation endpoints were
exactly equal; bound metrics differed only by the deliberate conservative
upward rounding.

### Coupled algebraic Newton prediction

The sparse coupled implicit block already solves for both the algebraic update
and the dynamic update. The integrator now retains the algebraic component and
uses its damped value as the algebraic initial guess for the corresponding
dynamic line-search trial. The normal algebraic residual and Newton tolerance
remain authoritative.

Three balanced rounds measured mean reductions of 8.178%, 7.257%, and 6.187%
at 32, 64, and 128 unknowns, with minimum round reductions of 8.005%, 7.070%,
and 5.818%. Reference algebraic iterations fell from 100 to 50. Endpoints and
all non-work metrics were exactly equal in the measured workload.

### Explicit projection and reference reuse

For eligible large sparse explicit candidates, the mandatory current-state
differential-sensitivity factorization now performs one modified-Newton
algebraic projection and carries its conservative Jacobian norm into the
bounded controller. Dense, small, implicit-candidate, and extension paths are
unchanged. This removed all 49 candidate algebraic iterations in the measured
64- and 128-unknown workloads. Three balanced rounds measured 2.108% at 64
unknowns and 0.601% at 128 unknowns; 32 unknowns intentionally remained on the
original path.

The scheduled implicit reference also reuses the candidate's already accepted
circuit evaluation when its time and complete differential state exactly match
the implicit initial guess. This removes a duplicate projection without
changing the implicit residual. Mean reductions were 12.717%, 13.128%, and
12.493% at 32, 64, and 128 unknowns, with minimum round reductions of 12.642%,
12.889%, and 12.030%. Reference circuit evaluations fell from 100 to 51 and
reference algebraic iterations fell from 50 to one. Final dynamic states were
identical; the largest intermediate dynamic delta was `1.68e-14`, and maximum
algebraic and full residual evidence was unchanged.

### Quartic replay algebraic initialization

After four matching uniform replay substeps, eligible large sparse systems
extrapolate accepted algebraic solutions as

```text
5 u[n] - 10 u[n-1] + 10 u[n-2] - 5 u[n-3] + u[n-4].
```

This is only an initial guess. A failed algebraic prediction retries from the
current accepted algebraic solution, and the same Newton tolerance decides
whether the guess is sufficient. Variable, event-reset, small, dense, and
extension paths do not use it.

Three balanced rounds measured mean reductions of 2.996% at 64 unknowns and
2.279% at 128 unknowns, with minimum round reductions of 2.706% and 2.172%.
Replay algebraic iterations fell from 100 to 78. Against an eight-times-refined
trapezoidal authority with tighter Newton tolerances, the predicted replay
endpoint error was approximately 0.14% lower than the prior endpoint error.

### Guarded nonlinear chord prediction

Eligible built-in diode circuits with at least 64 algebraic unknowns retain the
most recently validated sparse algebraic factorization as a chord predictor.
The predictor never bypasses the current residual, line search, Newton
tolerance, or singularity gates. A failed factor solve or an update that does
not strictly reduce the current residual clears the cached factorization and
immediately retries through the original fresh-Jacobian Newton path. The cache
contains at most one factorization per `Circuit`.

Three balanced rounds measured mean reductions of 24.020% at 64 unknowns and
20.109% at 128 unknowns, with minimum round reductions of 23.791% and 19.783%.
Algebraic iteration counts were unchanged. Maximum final-state deltas were
`5.676015213396113e-15` and `7.320533068622126e-15`; the maximum algebraic
unknown delta was below `6.58e-14`, and maximum residual evidence was unchanged.
Against an eight-times-refined trapezoidal authority with tighter Newton
tolerances, the endpoint-error ratios were approximately `1.00000042` and
`1.00000048`.

### Post-chord kernel reductions

Infinity norms of at least 64 values now use two C-level iterator passes: one
to preserve deterministic `NaN` propagation and one to compute the maximum
magnitude. Shorter vectors retain the original scalar loop. Isolated balanced
measurements reduced the 64- and 128-unknown workloads by 1.078% and 1.474%,
with minimum round reductions of 0.934% and 1.136%; the 32-unknown production
path is unchanged and all measured traces were exactly equal.

Large sparse nonlinear evaluations now retain diode currents only when they
were assembled for the exact unknown-vector object accepted by Newton. Power
accounting consumes those currents without evaluating the diode law again.
Dense, subclass, stale-object, and unavailable-cache paths recompute normally.
Three balanced rounds measured reductions of 1.585%, 2.348%, and 2.613% at 32,
64, and 128 unknowns, with minimum round reductions of 1.182%, 2.101%, and
2.441%. Dynamic traces and every recorded source/dissipated-power value were
exactly equal.

Finally, dynamic and algebraic sizes are stored as compiled-topology facts, and
the sparse-Jacobian eligibility decision is cached by backend. Changing the
backend invalidates the decision and is covered by regression. Three balanced
rounds measured reductions of 1.881%, 1.621%, and 1.326% at 32, 64, and 128
unknowns, with minimum round reductions of 1.486%, 0.926%, and 1.129%. Traces
were exactly equal.

The exact base `Circuit` sparse kernels now inline the diode limiting law. The
residual-only path computes current without constructing the unused
conductance, while the full sparse-Jacobian path preserves the original current
and conductance operation order. Subclasses continue through the overridable
device method. Against a preserved pre-kernel package, three balanced rounds
measured reductions of 1.049%, 2.862%, and 2.583% at 32, 64, and 128 unknowns,
with minimum round reductions of 1.029%, 2.069%, and 2.063%. Dynamic traces and
all recorded source/dissipated-power values were exactly equal.

### Accepted inputs and specialized residual assembly

Accepted evaluations now retain the already sampled algebraic inputs that
produced them. Native differential sensitivity and coupled sparse implicit work
reuse those inputs only when the evaluation records the exact owning `Circuit`;
foreign, unavailable, dense, and extension paths resample normally. Three
balanced rounds measured mean reductions of 1.458% at 64 unknowns and 1.155%
at 128 unknowns, with minimum round reductions of 1.132% and 0.812%. The
32-unknown result was within timing noise and its production path is unchanged.
Every measured state, source-power, dissipated-power, and residual value was
exactly equal.

For exact built-in `Circuit` instances on the eligible large sparse path,
topology construction now compiles a residual-only scalar kernel with fixed
validated indices and the original device-group stamping order. The generated
kernel contains no user-provided source text, reads mutable component parameters
and sampled inputs live, and preserves the scalar fallback for subclasses and
ineligible paths. A NumPy residual-buffer prototype was rejected after it made
the isolated kernel approximately 61% slower.

Against the immediately preceding scalar fallback, the specialized kernel
reduced end-to-end simulation time by 5.987% at 64 unknowns and 6.514% at 128
unknowns, with minimum round reductions of 5.096% and 6.226%. Kernel build
overhead was approximately 1.09 ms and 2.25 ms respectively. Timed from circuit
construction through a 50-step simulation, the eager design still reduced total
latency by 3.250% and 1.729%, with minimum round reductions of 3.136% and
1.533%. State and metric traces were exactly equal in every comparison.

The same validated-index design now covers full residual-plus-CSC assembly,
but only after 256 eligible calls on the exact built-in circuit. Eager
compilation was rejected because construction-through-short-simulation latency
regressed by 2.7% to 3.3%. The demand gate leaves the measured 50-step workload
on the existing fallback at 115 to 116 full assemblies, while a 1,000-step
workload demonstrates repeated use before paying compilation cost. On those
long workloads, three balanced rounds measured end-to-end reductions of 1.943%
at 64 unknowns and 1.888% at 128 unknowns, with minimum round reductions of
1.072% and 1.516%. The generated assembly kernel itself reduced direct call
time by approximately 37% to 39%. Residuals, CSC numeric data, states, and
recorded metrics were exactly equal, including after resistor, diode, and
switch parameter mutation.

Evaluation now enters a private algebraic-solve core only after time and
dynamic-state validation has already succeeded, so the public `evaluate`
boundary no longer triggers the same state scan again inside
`solve_algebraic`. Public direct solves retain their original validation. For
noncached algebraic guesses, finiteness checking and infinity-norm calculation
are combined into one scalar pass; the exact last accepted tuple still reuses
its cached norm. Against the exact preceding wheel, three balanced rounds
measured reductions of 1.954%, 1.929%, and 1.987% at 32, 64, and 128 unknowns,
with minimum round reductions of 1.294%, 1.574%, and 1.836%. State and metric
traces were exactly equal, and a public non-finite initial guess continues to
fail closed.

The topology-constant differential-sensitivity right-hand-side matrix is now
converted to a read-only NumPy array only on its first eligible native sparse
use and then reused by identity. Capacitor branch indices are likewise retained
as compiled topology data instead of rebuilt as a NumPy array for every norm.
The 32-unknown path remains below the native-sensitivity gate. Direct repeated
multi-right-hand-side solves were 68% faster at 64 unknowns and 77% faster at
128 unknowns. Against the exact preceding wheel, three balanced end-to-end
rounds measured reductions of 2.697% at 64 unknowns and 6.870% at 128 unknowns,
with minimum round reductions of 1.913% and 6.510%. State and metric traces
were exactly equal. In the warmed 128-unknown profile, aggregate
`numpy.asarray` time fell from 0.046 to 0.014 seconds.

### Final solution materialization and numeric conversion

Algebraic solution construction now consumes the validated unknown sequence
once. The node-voltage dictionary is updated from a shared iterator in compiled
node order, and the branch-current dictionary consumes the remaining values in
compiled branch order. This preserves the public mapping order and tuple/dict
types while removing two redundant indexed dictionary comprehensions. Isolated
construction time fell by approximately 30%, 40%, 48%, and 52% at 32, 64, 128,
and 256 algebraic unknowns. Against the exact preceding wheel, three balanced
end-to-end rounds measured mean reductions of 0.961%, 1.521%, and 1.897% at 32,
64, and 128 unknowns, with exactly equal state and metric traces.

Equivalent tuple/list conversions of already validated numerical sequences now
use the C-level `map(float, ...)` path. Conversion order and exception behavior
remain unchanged. Against the immediately preceding retained candidate, this
was timing-neutral at 32 unknowns and reduced mean end-to-end time by 1.932% at
64 unknowns and 1.269% at 128 unknowns. State and metric traces were exactly
equal.

### Contractively bounded Schur implicit prediction

The native differential-sensitivity path now retains both the algebraic
sensitivity matrix and the exact reduced differential Jacobian used by the
bound calculation. An eligible nonlinear implicit solve may use that prior
evidence to form the reduced Schur system
`(a I - h J) delta_x = -residual`, then recover the algebraic update from the
retained sensitivities. The differential-Jacobian infinity-norm computation and
its outward rounding remain in their original order; a mixed capacitor/inductor
probe produced an exactly equal old and new bound.

The Schur result is only a contractive predictor. It is attempted at most once
per implicit solve, must reduce the residual below 90% of its prior value under
the normal line search, and reserves one iteration for the exact coupled sparse
Newton block. Future sensitivity evidence, changed switch topology, nonfinite
updates, singular reduced systems, and evidence outside the bounded age window
are rejected. A failed contraction restores the base algebraic guess and
recomputes the base residual before the exact path proceeds. Periodic
independent replay remains unchanged.

Direct mixed C+L sparse-update comparisons measured reductions from 35% to 73%
over the exact coupled block across the tested dimensions. Against the exact
preceding candidate, nonlinear capacitor/diode simulations measured mean
end-to-end reductions of 2.957% at 64 algebraic unknowns and 3.692% at 128,
with maximum state delta `1.0408340855860843e-17`. Mixed capacitor/inductor
simulations measured 1.084% at 64 algebraic/32 dynamic unknowns and 0.545% at
128 algebraic/64 dynamic unknowns, with maximum state delta
`4.336808689942018e-19`.

### ULP-aware two-step evidence age

The sensitivity-age guard now evaluates the same mathematical two-step window
with a scale-aware tolerance of eight ULPs. This admits accumulated timestamps
such as `2.0000000000000053` steps without widening the intended age policy.
Future evidence, genuinely older evidence, changed switch topology, failed
contraction, and exact coupled fallback behavior remain unchanged.

Against the immediately preceding fixed-ratio guard, three balanced rounds
measured mean reductions of 3.751% at 64 algebraic unknowns and 2.197% at 128
algebraic unknowns on mixed C+L workloads, with minimum round reductions of
3.558% and 1.959%. Maximum dynamic-state deltas were
`1.734723475976807e-18` and `3.469446951953614e-18`; maximum metric deltas were
`1.681e-10` and `1.531e-10`. Smooth and pulsed controls were timing-neutral
within local noise, while the 64-unknown switched case measured a 0.827% mean
reduction with exact state and a `6.441069899665308e-12` maximum metric delta.

An attempted three-step extension was rejected after correcting the benchmark
baseline. The earlier apparent mixed-workload gain compared three steps with a
stricter ratio test rather than with the implemented ULP-aware two-step guard.
Against the true current guard, the mixed workloads exposed no additional
eligible three-step evidence, while pulsed cases could pay extra predictor cost.
The production policy therefore remains mathematically two steps.

### Compiled simulation breakpoint schedules

For the exact built-in `Circuit` type, `Simulator.run` now compiles the active
breakpoint providers once per run and deduplicates pure built-in waveform
schedules by timing signature. Pulse levels, sine amplitudes, and piecewise-
linear values do not affect their event times, so equivalent schedules share one
provider. Public `Circuit.breakpoints` behavior is unchanged, custom waveforms
remain individually observable, circuit subclasses keep their virtual
`breakpoints` dispatch, and every new simulation run recompiles current element
assignments.

Against the exact ULP-aware baseline, three balanced rounds measured mean
reductions of 11.638% and 16.243% for 16- and 32-channel pulsed diode networks,
with minimum round reductions of 11.322% and 15.635%. Sixteen- and 32-channel
switched networks measured mean reductions of 18.306% and 22.102%, with minimum
round reductions of 17.763% and 21.093%. State traces, reported metrics,
rejection counts, and deterministic candidate-work counts were exactly equal.
An isolated runtime-path check reduced repeated-schedule query time by 98.177%
and also improved unique built-in and custom schedules by 1.285% and 7.961%,
respectively, because the per-run provider list removes repeated element lookup.

### Demand-gated sparse-kernel compile reuse

Generated sparse assembly source depends on topology but reads resistance,
diode, switch, state, and sampled-input values from the live circuit. The
demand-gated sparse kernel therefore now uses a bounded 128-entry source cache
across identical topologies. The startup residual kernel remains per-circuit:
a broader cache was rejected because its source hashing regressed workloads
that never reached the heavy sparse-assembly gate.

Against the breakpoint-optimized baseline, repeated 16- and 32-channel switched
topologies measured incremental mean reductions of 3.973% and 5.938%, with
minimum round reductions of 3.223% and 5.476%. State and metric traces and all
deterministic work counts were exactly equal. Smooth, mixed, and short pulsed
workloads do not invoke this cache; their measured timing variation is therefore
treated as ambient benchmark noise rather than a causal code-path effect.

### Hot-topology sparse-kernel adoption

The source cache above removed repeated Python compilation, but each newly
constructed circuit still repeated the 256-call fallback warmup before asking
for the already compiled function. The retained design now records a compiled
kernel under an exact structural key containing the CSC pattern, device stamps,
constraint stamps, and inductor-state mapping. The registry is a lock-protected
128-entry LRU. The first circuit for a topology still has to satisfy the original
demand gate; later exact built-in `Circuit` instances with the same topology
adopt the proven kernel on their first eligible sparse assembly.

The kernel continues to read resistance, diode, switch, dynamic-state, and
sampled-input values from the receiving circuit. Parameter mutation therefore
remains live. Circuit subclasses, distinct structures, and cold topologies keep
the original fallback and demand-gate behavior. Focused tests cover exact
fallback equivalence, parameter mutation, distinct-topology misses, first-call
hot adoption, and LRU eviction.

Against the source-cache baseline, five balanced rounds of 25 paired runs
measured mean reductions of 3.829% and 4.069% for repeated 16- and 32-channel
switched topologies. Minimum round reductions were 3.636% and 3.602%. State and
metric traces and deterministic work counts were exactly equal.

### Duplicate built-in switch-control sampling

The hot switch profile then showed repeated `Pulse.value` evaluation for 32
numerically identical built-in control waveforms. For exact built-in circuits
with at least 32 switches, construction now compares signed-zero-aware value
keys for immutable built-in controls. Only a plan that actually finds duplicate
values installs a specialized sampler. Unique built-ins, custom waveforms,
smaller circuits, and subclasses execute the original sampling method unchanged.
Custom providers remain observable once per switch. Direct control reassignment
refreshes the plan through a weak callback, so no circuit-to-switch reference
cycle is introduced and changed control topology remains visible to the chord
guard.

Against the hot-topology baseline, five balanced rounds of 25 paired runs on the
32-channel switched workload measured a 1.683% mean reduction with a 1.433%
minimum round reduction. A 32-channel unique-control matrix was neutral at
+0.266% mean with a -0.055% minimum round result. All state and metric traces
were exactly equal. An earlier per-evaluation identity-checking plan was rejected
because its invalidation and mapping overhead erased the waveform-call savings.

Across both retained changes, the same five-round comparison against the exact
pre-loop baseline measured cumulative reductions of 4.114% at 16 channels and
5.985% at 32 channels, with minimum round reductions of 3.646% and 5.832%.
Every state trace, reported metric, rejection count, and deterministic
candidate-work count was exactly equal.

### Bounded SuiteSparse KLU symbolic/numeric reuse

The next profile identified repeated SuperLU symbolic and numeric factorization
inside large batched differential-sensitivity solves. BAB-CS now has an optional
`ctypes` adapter for a compatible system SuiteSparse KLU 2 library. KLU symbolic
analysis and numeric storage live in a bounded 128-entry per-thread LRU. Exact
structure identity avoids repeated tuple hashing in hot circuits, exact
structural equality still permits reuse across separately constructed circuits,
and weak factor references allow eviction without invalidating the public
reusable-factorization contract. A stale or cross-thread factorization restores
its immutable matrix values into an appropriate workspace before solving.

The KLU workspace disables row scaling so its exposed U diagonal remains on the
original matrix scale. Every factor and refactor must pass the existing absolute
minimum-pivot gate, singular and nonfinite results fail closed, and automatic
KLU failure retries with SciPy. Each multi-right-hand-side solve uses a distinct
owned Fortran buffer. An earlier prototype accidentally allowed `ctypes` to
overwrite a transposed view of the read-only cached right-hand sides; the retained
implementation forces a copy and has a direct mutation regression test.

Automatic adoption is deliberately narrow. Generic `auto` factorization keeps
the existing dense/SciPy selection. KLU is selected automatically only for
native sensitivity systems with at least 128 algebraic unknowns and 32 right-
hand sides, where repeated structure and batching amortize the adapter cost.
`linear_backend="klu"` remains available for explicit research use, while a
missing NumPy installation or compatible shared library fails clearly.

Three balanced rounds with four warmups and 15 paired runs per round compared
the retained implementation against commit `259a836`. Mean end-to-end reductions
were 2.048% for the 32-channel sine case, 4.166% for mixed capacitor/inductor
channels, 4.293% for pulsed channels, and 3.140% for switched channels. Minimum
round reductions were 1.484%, 3.674%, 4.191%, and 2.780%, respectively. Every
state trace, reported metric, rejection count, and deterministic candidate-work
count was exactly equal. Final factor-plus-batched-solve kernels were about 22%
faster for the mixed case and 13% faster for the switched case on the local
SuiteSparse KLU 2.3.6 installation.

### KLU hot-path safety and boundary reduction

The first follow-up hypothesis was native sparse numerical-value ownership. A
direct 128-unknown, 32-right-hand-side profile rejected that priority ordering:
list-to-tuple conversion cost about 0.28 microseconds and copying the immutable
tuple into KLU's NumPy value buffer cost about 3.43 microseconds, while the
Python U-pivot scan cost about 37 microseconds and sparse infinity-norm
construction cost about 20 microseconds. The retained work therefore attacks
the measured safety and boundary costs before changing public matrix ownership.

The KLU workspace now calculates the absolute pivot threshold from its owned
numeric values with a vectorized sparse row reduction, rejects nonfinite values
before native factorization, and validates the unscaled U diagonal with a
vectorized finite/minimum scan. This preserves the same absolute singularity
contract. The workspace also retains stable `ctypes` pointers for its structural
and numeric arrays and solves directly into the independent C-order `(nrhs, n)`
result. That same memory is column-major `(n, nrhs)` to KLU, so no intermediate
transpose-copy is needed and later solves cannot mutate earlier results. The
direct layout reduced the isolated solve from about 7.93 to 6.89 microseconds for
capacitor channels and from 13.10 to 10.93 microseconds for mixed channels, with
bit-identical solutions. Against the exact pre-layout wheel, mean end-to-end
reductions were 1.530%, 1.460%, 0.497%, and 1.012% for sine, mixed, pulsed, and
switched workloads. The pulsed minimum round was -0.469%, so this isolated
increment remains small relative to timing noise even though the cumulative
comparison below is stable.

Native sensitivity post-processing now gathers inductor voltage columns in
batches instead of issuing one NumPy operation per inductor. Read-only
capacitance and inductance arrays are reused while live element-value mutation
still refreshes them. Native NumPy right-hand-side matrices are validated from
their two-dimensional shape rather than by iterating over every row; generic
Python sequences retain the original per-row validation.

Against the exact pushed KLU baseline `f21b383`, three balanced rounds with four
warmups and 15 paired runs per round measured mean reductions of 4.131% for
32-channel sine, 6.814% for mixed capacitor/inductor channels, 6.020% for pulsed
channels, and 6.282% for switched channels. Minimum round reductions were
3.768%, 6.466%, 4.958%, and 5.668%, respectively. State traces, metrics,
rejection counts, and deterministic candidate-work counts were exactly equal.
The isolated native sensitivity kernel fell from about 91.7 to 56.8
microseconds for capacitor-only channels and from about 117.1 to 83.3
microseconds for mixed channels in the final local profile; these microsecond
figures remain sensitive to host noise and are not portable guarantees.

### Fused private sparse assembly and KLU factor/solve

The next boundary probe measured the complete generated-kernel-to-sensitivity
path rather than the tuple copy in isolation. At 128 algebraic unknowns and 32
right-hand sides, returning the generated scalar value list directly and
performing factorization plus the first batched solve in one KLU workspace call
reduced the microkernel from about 42.4 to 41.4 microseconds while still
constructing the reusable factorization required by projection correction.
Direct NumPy and `array('d')` stamping were rejected because scalar writes made
the generated arithmetic slower.

The retained implementation keeps the public `SparseMatrix` and stale-factor
contracts unchanged. Only the exact built-in native-sensitivity path may request
raw generated values. KLU copies those values into its owned numeric buffer,
solves the batched sensitivity system, and returns both independent solutions
and an immutable reusable factorization handle. Automatic KLU failure still
reconstructs the sparse matrix and falls back to SciPy.

Across 11 isolated rounds, native sensitivity improved by 3.433% on average for
capacitor-only channels and 3.336% for mixed channels; minimum round reductions
were 0.943% and 1.834%. In the balanced whole-run comparison, the isolated
increment was near timing noise for smooth sine and mixed cases, while pulsed
and switched cases measured 2.241% and 0.978% mean reductions with 1.652% and
0.955% minimum reductions. Every state, metric, rejection, and deterministic
work trace was exactly equal.

### Jacobian-only native sensitivity assembly

The next profile showed that native sensitivity consumed only algebraic
Jacobian values, but the private generated sparse kernel still allocated and
stamped a complete residual, calculated diode currents, and replaced the
accepted diode-current cache. A separate generated Jacobian-only kernel now
stamps the same live resistor, switch, diode, and constraint derivatives without
constructing unused residual evidence. Public residual-plus-Jacobian assembly,
subclass dispatch, limiting rules, topology, and SciPy fallback remain
unchanged. The smaller compiler activates eagerly only at the existing
qualified KLU crossover of at least 128 algebraic unknowns and 32 right-hand
sides; below that crossover the previous demand and fallback paths remain
authoritative.

Against exact commit `351a8e0`, 11 isolated paired rounds reduced 32-channel
native sensitivity by 14.404% on average for capacitor-only channels and
11.506% for mixed channels. Minimum round reductions were 13.225% and 10.787%.
The generated Jacobian values were exactly equal before and after live resistor
and diode parameter mutation, and the kernel does not alter residual or
accepted-current caches.

Three balanced 32-channel rounds measured mean whole-run reductions of 3.742%
for sine, 4.182% for mixed C+L, 7.960% for pulsed, and 0.882% for switched
workloads. Minimum round reductions were 1.165%, 2.885%, 6.608%, and 0.471%.
Two balanced 64-channel rounds measured mean reductions of 3.723%, 4.286%,
6.850%, and 6.171%, with minimum reductions of 2.685%, 4.163%, 6.823%, and
5.480%. State, metric, rejection, and deterministic work traces were exactly
equal in every retained comparison.

### Independent mixed-sensitivity gather ownership

The Jacobian-only profile exposed one remaining large Python-visible copy in
mixed capacitor/inductor systems. NumPy advanced indexing already returns an
independent writable sensitivity gather, but the inductor voltage path copied
that gather a second time before subtracting negative-node columns. Removing
the redundant copy preserves source-array isolation and all public result
ownership while leaving capacitor-only paths unchanged.

Against the exact Jacobian-only candidate, 11 isolated rounds reduced the
32-channel mixed native-sensitivity call by 3.519% on average with a 2.564%
minimum round reduction. Three balanced 32-channel mixed runs measured a 1.133%
mean end-to-end reduction with a 0.539% minimum round reduction. Two balanced
64-channel mixed runs measured a 0.832% mean reduction with a 0.076% minimum.
State, metric, rejection, and deterministic work traces were exactly equal.

### Deferred-reference Jacobian materialization

The next ownership profile separated native sensitivity evidence from dense
dynamic-Jacobian storage. Deferred-reference candidate steps need the batched
algebraic sensitivities and conservative infinity norm, but they do not consume
the dense dynamic Jacobian unless a later stiffness or bound checkpoint forces
implicit authority. At 64 or more dynamic states, unscheduled reference steps
now omit that quadratic allocation and scaling. Scheduled references keep the
previous eager path, and a forced reference materializes the matrix from the
same owned sensitivities before attempting the guarded sparse chord update.

The crossover is deliberately evidence-gated at 64 dynamic states. At 32
channels the whole-run effect remained timing noise. Against exact commit
`a0d67b5`, three balanced 64-channel rounds at a reference interval of eight
reduced mixed, pulsed, and switched workloads by 1.137%, 1.363%, and 1.613% on
average. Minimum round reductions were 0.552%, 0.675%, and 0.992%. Exact state,
metric, accepted/rejected work, and fallback traces were preserved. A
128-channel follow-up remained positive for mixed and pulsed workloads, while
switched timing was inconclusive; the retained 64-state crossover therefore
rests on the all-positive 64-channel evidence rather than a monotonic-scaling
claim.

Instrumentation also ruled out broader cache policy as the next gain. Each
profiled 32- and 64-channel run incurred one KLU workspace miss followed only by
identity hits, zero evictions, one generated Jacobian-kernel compilation, and
one numeric refactor per new sensitivity. Existing symbolic reuse is therefore
already complete for these workloads. The remaining factorization opportunity
is fewer justified numeric refreshes or a different backend interface, not a
larger cache.

### Independent evidence-controlled replay refinement

Direct timing showed that periodic independent replay consumed about 27.1% of
the 32-channel sine run, 42.6% of the mixed C+L run, 16.5% of the pulsed run,
and 22.8% of the switched run at a 16-step anchor interval. Replay still covers
the complete accepted interval; the opportunity was subdivision count, not
anchor omission.

Mixed C+L trapezoidal replay now starts at `minimum_anchor_substeps` and computes
an ordered local quadrature defect from three independent replay derivatives.
If the scaled defect exceeds `anchor_embedded_error_cap`, the complete replay
restarts from the trusted anchor at a cubically predicted finer subdivision.
The original `anchor_substeps` count remains the ceiling and therefore the
fail-closed baseline. Nonfinite evidence rejects the step. Pure-C/L
trapezoidal policies, Backward Euler, ineligible BDF2 topologies, and disabled
adaptivity retain their previous execution without estimator overhead; exact
event boundaries still reset history.

For the 32-channel mixed workload, replay work fell from 322 to 162 steps at a
16-step anchor profile and from 201 to 101 steps at a 50-step anchor. The
corresponding median total times fell from about 87.33 to 72.89 milliseconds
and from 71.53 to 62.24 milliseconds. A three-round balanced comparison against
commit `4511c46` measured a 13.450% mean end-to-end reduction with a 12.850%
minimum round reduction for the mixed workload. Pure sine, pulsed, and switched
cases retained their previous work and remained within local timing noise.

The adaptive mixed endpoint differed from the former four-substep authority by
`1.776e-8` in maximum absolute state and `6.712e-10` in maximum reported metric
for the balanced case. In a separate authority calibration, the adaptive
endpoint was 0.863 weighted RMS from an eight-substep replay, versus 0.091 for
the fixed four-substep replay; its maximum embedded replay evidence was 0.486
against the default cap of 1.25. These are bounded calibration results, not a
claim that two substeps are universally equivalent to eight.

### Qualified switched BDF2 replay refinement

BDF2 replay cannot use only its multistep defect because each independent
window begins without history and therefore takes one Backward Euler startup
step. The retained estimator measures both terms. For startup step `h`, the
state defect is `0.5 h (f_1 - f_0)`. For a variable BDF2 step `h` following a
step `k`, the defect is
`h^2 (h + k) / (3 (k + 2h))` multiplied by
`(f_{n+1} - f_n) / h - (f_n - f_{n-1}) / k`. Both are scaled by the same
absolute and relative state tolerances. The complete replay restarts from the
trusted anchor when the maximum evidence exceeds `anchor_embedded_error_cap`.
Because startup is second order, subdivision prediction uses a square-root
law; the configured fixed count remains the ceiling.

Broad application did not pass the retention gate. A BDF2-only defect that
ignored startup appeared faster on source-pulsed cases but under-reported the
first-step error. Adding the required startup evidence made the pulsed workload
0.296% slower on average. Smooth sine replay was 14.630% slower before the
topology gate, and mixed C+L replay retried to the fixed ceiling. The retained
path is therefore limited to capacitive circuits with a built-in `Pulse` or
piecewise-linear switch control; custom controls, smooth controls, source-only
pulses, inductive circuits, and disabled adaptivity retain fixed replay.

Against exact commit `9a804a3`, three balanced rounds with four warmups and 15
paired samples per round produced the following switched-capacitive results:

| Channels | Mean reduction | Minimum round reduction | Maximum WRMS versus fixed eight |
| ---: | ---: | ---: | ---: |
| 1 | 10.307% | 9.127% | 0.263 |
| 16 | 9.094% | 8.853% | 0.264 |
| 32 | 11.229% | 10.923% | 0.266 |
| 64 | 11.116% | 10.388% | 0.384 |

Replay steps fell from 390 to 263 in every case. Replay circuit evaluations
fell from 393 to 269 through 32 channels and to 271 at 64 channels. Candidate
and scheduled-reference work, rejection counts, accepted time grids, and event
boundaries were unchanged. Maximum adaptive-versus-fixed-four state deltas were
`2.799e-9`, `3.219e-9`, `3.667e-9`, and `1.255e-8` from one through 64
channels. Fixed four remained closer to fixed eight, so the result is a bounded
performance trade rather than a claim of increased reference accuracy.

**Current semantic correction:** the table and replay counts above remain
historical evidence for exact commit `9a804a3`. The current source forces
independent replay at event boundaries before multistep history reset, so event
resets can no longer suppress authority work. The historical timing and replay
counts shall not be promoted as current release evidence without a fresh frozen-
source benchmark.

### Current cumulative scaling

A fresh cumulative comparison used five warmups and 15 paired runs in each of
three balanced rounds. It includes all retained loops above and compares the
current forced-dense and `auto` paths rather than reusing the earlier dense
baseline.

| Algebraic unknowns | Dense mean median | Auto mean median | Mean reduction | Minimum round reduction |
| ---: | ---: | ---: | ---: | ---: |
| 32 | 0.095483697 s | 0.036160544 s | 62.129% | 61.958% |
| 64 | 0.382285888 s | 0.030522380 s | 92.016% | 91.958% |
| 128 | 1.973011725 s | 0.046981886 s | 97.619% | 97.605% |

The 32-unknown traces were exactly equal. Maximum dense-versus-auto dynamic
trace deltas were `2.1104364783530727e-11` at 64 unknowns and
`1.96882926628561e-11` at 128 unknowns; both complete paths pass the same
residual, nonlinear, bound, comparison, and long-horizon qualifications.

The BDF2 replay regression is an intentional correctness change outside the
default trapezoidal reference configuration. Configurations that explicitly use
`reference_method="bdf2"` should therefore expect corrected anchor trajectories
rather than baseline equality.

### Repeated-topology circuit construction

Parameter sweeps, Monte Carlo studies, and comparison matrices repeatedly build
the same structural circuit with different numerical values. Profiling exact
commit `dd8145e` showed that these runs still rebuilt the algebraic CSC pattern,
Jacobian stamps, constraint stamps, differential-sensitivity right-hand sides,
implicit block layout, and generated residual source for every instance. The
retained design now uses bounded 128-entry structural caches whose keys contain
only ordered terminal indices, branch positions, and dynamic-state placement.
Cached values are frozen sparse templates, immutable stamps, read-only tuple
right-hand sides, and compiled functions. Resistance, capacitance, inductance,
source, diode, switch, initial-state, and waveform values remain owned by and
read live from each circuit.

The CSC builder now buckets rows by column instead of repeatedly scanning the
complete position set. The implicit coupled block reuses its immutable layout,
but rebuilds each circuit's `1/C` and signed `1/L` multipliers independently.
Generated residual code is cached by structural stamps before source generation,
so a cache hit does not reconstruct or hash a large source string. Exact built-in
elements use direct dataclass construction during normalized copying; subclasses
retain the general `dataclasses.replace` path and therefore keep their runtime
type and extension semantics.

Five balanced construction rounds and three balanced build-plus-one-evaluation
rounds compared the combined retained path with exact commit `dd8145e`:

| Workload | Construction mean | Construction minimum | Build + evaluation mean | Build + evaluation minimum |
| --- | ---: | ---: | ---: | ---: |
| 16 capacitor/diode channels | 72.491% | 71.965% | 64.058% | 63.728% |
| 32 capacitor/diode channels | 73.529% | 73.265% | 67.010% | 66.067% |
| 64 capacitor/diode channels | 75.787% | 75.619% | 69.352% | 68.968% |
| 64 mixed capacitor/inductor channels | 75.356% | 75.210% | 69.445% | 69.338% |
| 128 capacitor/diode channels | 78.326% | 78.228% | 72.768% | 72.565% |

The topology-cache portion alone reduced construction by 50.993% to 52.508%
against the same baseline. The exact-built-in normalization kernel reduced its
isolated copy loop by 65.719%. A final order-preserving pass fused exact-type
classification, parameter validation, constraint collection, and first-seen node
indexing while retaining independent subclass `isinstance` behavior and duplicate-
name error precedence. A simulation-only comparison deliberately started timing
after construction: all state, metric, rejection, and deterministic work traces
were exactly equal, while mean timing varied from a 0.543% regression to a 0.509%
gain. The retained claim is therefore constructor and ensemble latency, not faster
simulation arithmetic.

## Local Validation

- Focused replay, Jacobian, nonlinear, comparison, accuracy, failure-gate, and
  long-horizon regression groups passed before the full run.
- Full current-source qualification on August 25, 2026 with SciPy 1.18.0 and
  SuiteSparse KLU 2.3.6, `BABCS_LONG_TESTS=1`, and
  `BABCS_VERY_LONG_TESTS=1`: 229 tests passed in 56.596 seconds, with zero skips.
- Two independent `bab_cs-1.1.0-py3-none-any.whl` builds were byte-identical.
- Local candidate wheel SHA-256:
  `761462fd7c451d33a111162e8a55a225920e0646ac72544a542db592ee3dde82`.
- Clean dependency-free installed-wheel qualification: 229 tests passed in
  53.080 seconds with 57 expected optional-backend skips; `pip check` reported
  no broken requirements.
- The same clean installed wheel with SciPy 1.18.1, NumPy 2.5.2, and SuiteSparse
  KLU 2.3.6: all 229 tests passed in 53.433 seconds with zero skips;
  `pip check` reported no broken requirements.
- Earlier source/installed comparison hashes were invalidated by the constructor
  source and test changes. They remain historical evidence and must be regenerated
  from the eventual exact release commit before qualification.
- Fresh `ngspice-46` cross-implementation runs completed for `rc_step`,
  `rl_step`, `diode_clip`, and `switched_rc`.

The external comparison remains cross-implementation evidence for the
generated semantic mapping, not proof that BAB-CS is generally more accurate
or faster than ngspice.

## Remaining High-Value Work

1. **Normalize-and-classify fusion:** the retained classifier removed most
   repeated `isinstance` work, reducing a 20-instance 128-channel profile from
   0.061 to 0.042 seconds. Normalized copying and classification remain separate
   passes. A future fusion may retain the first validation failure while still
   giving duplicate-name errors their existing precedence, but must preserve
   input-object isolation and subclass constructors.
2. **Compact structural-key formation:** cache hits still create terminal-index
   tuples and several small derived tuples per circuit. Any reduction must keep
   first-seen node ordering, branch ordering, exact element-family separation,
   and collision-free topology identity.
3. **Cache diagnostics and policy evidence:** deterministic work reports should
   expose structural, residual, implicit-layout, KLU, and SciPy cache hits,
   misses, evictions, refactors, and fallbacks before cache policy becomes user-
   configurable.
4. **Backend-interface numeric refresh:** KLU symbolic reuse is already complete
   in measured runs. Further solver work should target an interface that can
   refresh numeric factors without unsafe caller-buffer borrowing or redundant
   public-result copies.
5. **Projection residency only after renewed profiling:** current projection
   conversion cost is small relative to solves. Any retained change must remain
   lazy, preserve independent results, and demonstrate an end-to-end gain.
6. **Authority-refresh semantics before scheduling:** a future dynamic anchor
   policy must distinguish event-driven history reset from independently
   recomputed authority, honor exact event boundaries, and enforce a hard maximum
   elapsed authority age. The current probe found no safe performance gain, so
   this is a correctness prerequisite rather than the next optimization.

Reusable KLU scratch/result residency is no longer an active target. Borrowing
the result would violate independent ownership, while a safe scratch-plus-copy
prototype regressed isolated solves by about 3.3% to 12.4%. NumPy weighted-RMS
and 128-device diode batches were also rejected because their isolated vector
gains did not survive balanced whole-run tests. Reactive-value invalidation,
generated residual-plus-norm fusion, and broad projection ownership were already
below their retention thresholds.
An exact-state probe rejected shared accepted-evaluation Jacobian caching: the
stiffness evaluations do not use the same differential states as the preceding
block linearizations. Direct profiling also rejected standalone sparse tuple
ownership; the retained fused path removes only private assembly boundaries and
returns the required reusable handle. Direct cache instrumentation then found
one initial KLU workspace miss, identity hits thereafter, and no evictions in
the qualified workloads, so broader cache policy is not the next performance
gain. Cross-anchor refinement retention reduced replay work but slowed both
measured workloads and was not uniformly closer to eight-substep authority. A
standalone Backward Euler derivative-defect prototype was ordered under
refinement but repeatedly selected the maximum subdivision under the default
cap, increasing RC replay work. Cross-anchor retention and general Backward
Euler adaptation were rejected; the same startup term is retained only inside
the qualified switched BDF2 estimator. Dynamic anchor scheduling was then
rejected as the next replay optimization. Over 256 uninterrupted accepted
steps, fixed replay intervals of 16, 32, 64, and 128 each performed 1,024 replay
steps; fewer anchors simply reintegrated longer complete windows. In the
switched BDF2 workload, intervals above the event spacing appeared 31--34%
faster, but periodic independent replay fell to zero because event handling
reset the step counter and adopted the event state as the next anchor. The
remaining state delta was small, but no independent authority justified it.
Adaptive subdivision does not justify older or omitted authority, and an event
history reset must not be treated as an authority refresh.

The cross-anchor retention prototype reduced one-channel retries from 31 to 17
and replay steps from 3,248 to 3,056, but increased mean elapsed time by 7.382%.
At 32 channels it reduced retries from eight to four and replay steps from 752
to 672, but increased mean elapsed time by 16.226%. Its weighted-RMS distance
to fixed eight-substep authority improved from 688.55 to 595.99 in the first
case and worsened from 359.92 to 367.67 in the second. Lower retry counts were
therefore neither a timing win nor uniform authority improvement.

The Backward Euler prototype used the ordered local defect
`0.5 h (f_n - f_{n-1})` with square-root refinement scaling. On the default RC
qualification, its early anchors repeatedly retried at the configured maximum
four substeps, and total replay work exceeded the existing fixed-four path.
Larger evidence caps could reduce work, but changing the default authority cap
to rescue one estimator would weaken the established policy. The prototype is
not retained as a general Backward Euler policy; its startup defect remains
necessary inside BDF2 replay.

A weak reactive-value invalidation prototype was also rejected. It reduced the
isolated cached-scale check from about 0.97 to 0.11 microseconds for 32 capacitor
channels and from 1.57 to 0.11 microseconds for 32 mixed channels. End-to-end
means improved by only 0.096% to 0.513%, while sine and pulse minimum rounds
regressed by 0.095% and 0.070%. Exact state and metric traces were preserved, but
the gain did not justify adding mutation callbacks to every capacitor and
inductor. The simpler live tuple check remains authoritative.

A NumPy diode-family batch was rejected at the current automatic crossover. For
16 and 32 diodes, scalar arithmetic took about 2.14 and 4.05 microseconds while
the vector form took about 7.62 and 7.74 microseconds. Vector stamping crossed
over only around 64 devices and became materially faster at 128, but NumPy
transcendental and division ordering introduced small nonzero conductance deltas.
The generated scalar kernel therefore remains authoritative for current
32-channel KLU adoption. Any future batch must use a larger evidence-gated
crossover and prove that its numerical deltas do not alter accepted trajectories.

An exact-index evaluation-accounting prototype was also rejected. It reduced
the isolated accounting kernel by 15.6% to 18.9%, but end-to-end measurements
regressed by 0.958% at 32 unknowns and 0.383% at 64 unknowns, while the
128-unknown gain was only 0.260%. The qualified dictionary-backed public result
construction and accounting path is retained.

An exact generated residual-plus-norm prototype was rejected as well. Its
unrolled, single-pass, deterministic `NaN`-propagating norm reduced isolated
64-value residual calls by 6.2%, but was neutral at 128 values and regressed by
1.0% at 256 values. Three balanced end-to-end rounds reduced mean runtime by
only 0.214% at 64 algebraic unknowns and regressed by 0.130% at 128 unknowns,
with a worst round regression of 0.547%. State and metric traces were exactly
equal. The extra generated code and paired private APIs therefore do not meet
the retention threshold; evidence is preserved in
`/tmp/babcs-residual-norm-gain.jsonl`.

A deferred dense differential-Jacobian prototype was also rejected. It retained
the gathered sensitivity blocks after computing the norm and materialized the
dense matrix only when a later chord update reached it. Exact 32-channel traces
were preserved, but sine regressed by 1.411% on average with a 3.378% worst
round. Mixed and pulsed means improved by only 0.419% and 1.099%, and each had a
negative round of 0.472% and 0.653%. Switched runs improved by 0.607% with a
0.487% minimum, which did not justify a switch-only ownership mode and its
additional cached-state semantics. Evidence is preserved under
`/tmp/babcs-lazy-jacobian-benchmark/`.

A direct NumPy KLU right-hand-side clone was rejected too. Replacing the
explicit C-order allocation and assignment with `source.copy(order="C")`
reduced the isolated clone by 28.56% at 32 by 128 values and 12.04% at 64 by
256 values. That local saving did not survive the native solve: 32-channel
capacitor-only and mixed sensitivity means improved by only 0.641% and 0.548%,
with negative rounds of 0.753% and 2.005%. Exact end-to-end traces were also
neutral or worse: sine and mixed means changed by only 0.020% and 0.076%, while
the switched workload regressed by 0.684% on average and 1.965% in its worst
round. The explicit owned buffer remains authoritative. Evidence is preserved
under `/tmp/babcs-klu-copy-benchmark/`.

A cached COLAMD pre-permutation prototype was also rejected. It recovered the
first SuperLU factorization's column ordering, rebuilt the fixed CSC column
layout once, performed later numeric factorizations with `NATURAL` ordering,
and scattered single- and multi-right-hand-side solutions back to original
coordinates. Direct repeated factor-plus-solve workloads improved by 8.324%,
17.385%, and 24.711% at 64, 144, and 256 unknowns. Whole nonlinear simulations,
however, improved by only about 0.3% at 128 unknowns and 0.5% to 1.5% on average
at 256 to 512 unknowns, with negative rounds at every larger size. State deltas
remained at floating-point roundoff and reported metrics were unchanged, but
the mapping and copy complexity did not meet the end-to-end retention gate.
Explicit symbolic/numeric reuse therefore remains a backend-interface
opportunity rather than an in-tree pre-permutation workaround. Evidence is
preserved under `/tmp/babcs-perm-benchmark/`.
