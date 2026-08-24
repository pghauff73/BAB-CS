# BAB-CS Performance Optimization Audit

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

## Local Validation

- Focused replay, Jacobian, nonlinear, comparison, accuracy, failure-gate, and
  long-horizon regression groups passed before the full run.
- Full current-source qualification with `BABCS_LONG_TESTS=1` and
  `BABCS_VERY_LONG_TESTS=1`: 174 tests passed in 40.757 seconds, with zero
  skips.
- Most recent pre-Schur qualified wheel: `bab_cs-1.0.0-py3-none-any.whl`.
- Two independent wheel builds were byte-identical.
- Candidate wheel SHA-256:
  `195345cabb6eb24b0e5f2735a4299da8711a7a6bc354af1f746c29190d610125`.
- Clean installed-wheel suite: 169 tests passed in 13.000 seconds, with 31
  opt-in long/very-long and optional-SciPy tests skipped as configured.
- Installed-wheel SciPy qualification: 87 focused sparse, model, integrator,
  candidate, nonlinear, and CLI tests passed with SciPy 1.18.0.
- Source and installed-wheel comparison matrices each completed all 154
  results. Their JSON, CSV, and SVG outputs were byte-identical.
- Source-tree SHA-256 recorded by both reports:
  `669318d940a7eb3193054e5dc128c010e7ef5d6e57bd627cc9ff4df59392a72b`.
- Numerical JSON, CSV, and SVG SHA-256 values were respectively
  `25919dcf9b567840bf3b40d1d17c58c41890d4a4092a6794b07c6c1b3faf712c`,
  `2d66de8be6a7facec86d0c71b296ff7bdb0c514d48544cd9a35156bb38d15b9d`,
  and `4abd0aa8e9e5e9198e59db85d853cf6ac282ede9d8a1753506f6ffefd7252d46`.
- Fresh `ngspice-46` cross-implementation runs completed for `rc_step`,
  `rl_step`, `diode_clip`, and `switched_rc`.

The external comparison remains cross-implementation evidence for the
generated semantic mapping, not proof that BAB-CS is generally more accurate
or faster than ngspice.

## Remaining High-Value Work

1. **ULP-aware evidence age:** the current two-step sensitivity-age gate rejects
   some mathematically two-step-old evidence because accumulated timestamp
   rounding produces ratios such as `2.0000000000000053`. A benchmark-only
   ULP-aware comparison retained the same mathematical two-step window and
   measured mean reductions of 3.518% and 2.624% on the 64- and 128-unknown
   mixed C+L workloads. This remains production follow-up work until the
   complete nonlinear and release qualification is repeated.
2. **Sparse symbolic reuse:** generated CSC stamping removes Python dense
   assembly and conversion, but SuperLU still performs a fresh symbolic and
   numeric factorization. A backend with explicit symbolic-pattern reuse is the
   next large-network factorization opportunity.
3. **Projection state residency:** the constant multi-RHS conversion is removed,
   but target state, accepted state, and accepted algebraic unknowns are still
   converted during sparse projection. Aggregate `numpy.asarray` cost is now
   0.014 of 0.893 internal profiled seconds, so any further residency change
   must remain lazy and demonstrate an end-to-end gain.
4. **Native residual and norm ownership:** the large-vector norm fast path
   reduced traversal cost without changing storage. Further work should fuse
   residual construction and norm evidence only when the residual vector remains
   available to Newton and `NaN` propagation stays deterministic.
5. **Adaptive replay accuracy model:** AB3 initialization has largely removed
   replay Newton corrections, but replay still covers every accepted interval.
   Any substep reduction must be controlled by an independent local accuracy
   estimate, event boundary, maximum elapsed anchor time, and fail-closed retry;
   changing anchor frequency alone does not reduce total replay coverage.
6. **Cache diagnostics:** deterministic work reports should expose cache hits,
   misses, and evictions before cache policy becomes user-configurable.
7. **Evidence-gated anchor scheduling:** a dynamic anchor interval should be
   considered only after the internal recurrence, empirical anchor ratio, event
   boundaries, and maximum elapsed anchor time jointly enforce a fail-closed
   upper bound.

An exact-state probe rejected shared accepted-evaluation Jacobian caching: the
stiffness evaluations do not use the same differential states as the preceding
block linearizations. The next optimization phase should therefore compare
native nonlinear device-value stamping with a backend that exposes symbolic
sparse reuse. Evidence-gated anchor scheduling remains useful for controlling
when evidence is refreshed, but it is not itself a throughput optimization
unless paired with a qualified adaptive replay-step model.

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
