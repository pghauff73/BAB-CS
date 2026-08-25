# Circuit Engineering and Performance Work in BAB-CS

## Architectural Ownership

BAB-CS is implemented as a set of deliberately separated numerical owners. The
circuit model owns topology, algebraic unknown ordering, device stamping,
projection, energy, and differential sensitivity. Candidate integrators own
only candidate construction and candidate work counters. Implicit integrators
own backward Euler, trapezoidal, BDF2, nonlinear iteration, and refined replay.
The bounded controller owns authority, correction, gates, recursive bounds, and
anchors. The simulator owns event-aligned stepping and rejection recovery
[[23]](REFERENCES.md#ref-23) [[24]](REFERENCES.md#ref-24)
[[25]](REFERENCES.md#ref-25) [[26]](REFERENCES.md#ref-26)
[[28]](REFERENCES.md#ref-28). This ownership model prevents a fast path from
quietly bypassing safety logic.

The `Circuit` constructor normalizes nodes and elements, validates component
parameters, establishes deterministic node and branch ordering, and divides
the model into dynamic and algebraic parts [[25]](REFERENCES.md#ref-25).
Capacitor voltages and inductor currents preserve passive sign conventions.
Voltage sources and inductors introduce branch-current unknowns where needed by
the algebraic equations. That organization follows the purpose of modified
nodal analysis: retain sparse nodal structure while supporting ideal voltage-
defined elements [[1]](REFERENCES.md#ref-1).

At evaluation time, the model samples source and switch inputs, solves the
algebraic equations, derives the differential state derivative, and calculates
stored energy, source power, and dissipated power. The accepted
`CircuitEvaluation` therefore carries both numerical state and the diagnostics
needed by the controller. Algebraic solutions retain node-voltage and branch-
current maps for output, but optimized internal paths operate on deterministic
ordered storage rather than repeatedly rebuilding semantic dictionaries.

Linear algebra is dependency-free at the baseline. The dense path implements
partial pivoting, singularity detection, factored solves, multi-right-hand-side
solves, finite-difference Jacobians, infinity norms, and weighted RMS scaling
[[27]](REFERENCES.md#ref-27). This path is valuable beyond convenience: it gives
small tests and clean-wheel installations an auditable implementation that does
not depend on a compiled external package.

## Sparse Execution

The optional sparse path uses SciPy’s CSC matrices and SuperLU factorization
interface [[7]](REFERENCES.md#ref-7) [[9]](REFERENCES.md#ref-9). A second optional
adapter can use a compatible system SuiteSparse KLU 2 library through `ctypes`
[[35]](REFERENCES.md#ref-35). BAB-CS exposes `dense`, `auto`, `scipy`, and `klu`
backend choices. `auto` is a measured policy rather than an alias for sparse. It
considers problem size, matrix density, whether a structure can be reused, and
whether multiple right-hand sides can amortize setup. Small or dense systems
remain on the dense implementation.

One high-value optimization was to make topology a compiled asset. For eligible
circuits, the model builds the CSC row indices, column pointers, device stamp
locations, constraint locations, and sensitivity right-hand-side structure
once. Repeated evaluations then update numeric values without reconstructing
the sparse graph [[17]](REFERENCES.md#ref-17) [[25]](REFERENCES.md#ref-25).
Mutable resistance, capacitance, inductance, source, diode, and switch values
remain live; compilation records where values belong, not what their future
values must be.

The sparse factorization adapter maintains a bounded thread-local workspace for
each structural pattern. A mutable CSC numeric array can be refilled and passed
to SuperLU without allocating a complete matrix object on every solve. The
cache is capped, and tests verify that previously returned factor objects remain
independent after workspace reuse [[17]](REFERENCES.md#ref-17)
[[27]](REFERENCES.md#ref-27). Bounded cache ownership is important because an
unbounded structural cache would exchange numerical speed for process-level
memory drift.

KLU adds a distinct bounded workspace that retains symbolic analysis and
refactors numeric values for exact repeated CSC patterns. The 128-entry
per-thread LRU has an identity fast path for hot circuit-owned structures and an
exact structural fallback for separately constructed circuits. Reusable factor
objects hold immutable matrix values and weak workspace references, so stale,
evicted, or cross-thread solves can restore the correct factor without allowing
native memory to escape the cache bound. Unscaled U diagonals must pass the same
absolute pivot threshold as the existing solvers, and automatic KLU failure
falls back to SciPy.

Ordering is also evidence-gated. Repeated structures initially use a general
fill-reducing ordering. After enough observations, the implementation may probe
natural ordering and retain it only when the normal singularity gate passes and
the factor fill does not increase. A failed natural-order factorization disables
that choice for the workspace. This turns an optimization hypothesis into a
reversible local policy rather than an unconditional global switch.

Algebraic assembly was split into dense, sparse full-Jacobian, and sparse
residual-only paths. The sparse paths fuse device voltage lookup, residual
stamping, and compiled CSC value updates. Large eligible circuits can use
demand-generated kernels specialized to the exact built-in `Circuit` class
[[17]](REFERENCES.md#ref-17) [[25]](REFERENCES.md#ref-25). Subclasses and
extension points retain generic fallbacks, preventing generated code from
assuming semantics that a derived circuit may override.

Input sampling was reduced without freezing input objects. Current-source
waveforms, switch controls, and constraint waveforms can be sampled once per
eligible algebraic evaluation and reused through Newton iteration and power
accounting. The owning waveform objects are still consulted at each new time
and state evaluation. This preserves mutable test behavior and source semantics
while removing repeated dispatch inside a single evaluation.

Diode evaluation uses overflow-safe Shockley behavior and supplies both current
and conductance. Accepted large nonlinear evaluations can reuse already
validated diode values for accounting rather than evaluating the exponential
again. The implementation keeps subclass overrides and nonstandard device
behavior on the generic path [[25]](REFERENCES.md#ref-25). This is an example of
the project’s general optimization rule: reuse evidence only while its owner,
state, time, and topology remain exact.

Differential Jacobians require sensitivity of the algebraic solution to the
dynamic state. The optimized sparse path forms multiple right-hand sides and
solves them against one factorization, instead of solving each sensitivity
column independently. Native array storage is retained through this batch when
eligible. The resulting differential Jacobian and its norm can be reused by
candidate stages, stiffness detection, and amplification modeling within their
validated scope [[17]](REFERENCES.md#ref-17) [[25]](REFERENCES.md#ref-25).

## Nonlinear and Replay Acceleration

Implicit integration originally expressed nonlinear updates through an
explicitly materialized differential Jacobian and Schur complement. The current
sparse path can instead solve the exact coupled algebraic/dynamic block system.
This preserves the same Newton equation while avoiding dense intermediate
materialization. Structural-equivalence tests compare block and Schur updates,
so the optimization is tied to a mathematical identity rather than endpoint
timing alone [[17]](REFERENCES.md#ref-17) [[26]](REFERENCES.md#ref-26).

The nonlinear solver uses damped Newton iteration and a fail-closed residual
test. An initial differential guess can come from the candidate or replay
history, while an algebraic guess can come from the previous accepted solution
or guarded extrapolation. If a proposed guess increases residual or becomes
nonfinite, the solver restores the accepted base state and continues with the
exact path. Predictor success can reduce work, but predictor failure cannot
relax the convergence criterion.

A guarded chord predictor reuses a previous validated factorization for one
proposal when the evidence is recent, topologically compatible, finite, and
contractive. It does not replace exact Newton iteration. The line search must
show residual reduction, and a failed proposal returns to the untouched base
state [[17]](REFERENCES.md#ref-17). This makes the chord operation analogous to
an initial guess with attached provenance rather than a cached solution.

The contractively bounded Schur predictor extends that idea to an implicit
update. Retained algebraic sensitivity and differential-Jacobian evidence form
a reduced proposal, but the attempt is limited to once per implicit solve and
reserves capacity for the exact coupled solve. Future timestamps, excessive
evidence age, changed switch state, singularity, nonfinite updates, and failed
contraction reject the shortcut. The same mathematical two-step age window now
uses a scale-aware eight-ULP tolerance so accumulated timestamp representation
does not reject exactly two-step-old evidence. A broader three-step policy was
rejected after a corrected baseline showed no additional mixed-workload
eligibility and possible pulsed-workload overhead
[[17]](REFERENCES.md#ref-17).

Replay performance work follows the same authority rule. AB3 differential
extrapolation and quartic algebraic extrapolation improve initial guesses after
enough matching history exists. The first replay step and incompatible spacing
remain conservative. Failed guesses restart from accepted values. Because the
replay interval is still completely reintegrated by the reference method,
initial-guess acceleration does not convert the anchor into extrapolation-only
authority.

Several smaller retained changes remove repeated norm, conversion, and result-
materialization work. Accepted dynamic-state norms are stored after the
mandatory finite scan. Exact accepted algebraic tuple objects can retain an
infinity norm, while copied sequences are recomputed. Specialized result
construction delays public dictionaries until required. These changes are
modest individually, but they matter because circuit simulation repeats the
same kernels many times.

## Measured Performance Evidence

The performance audit records both retained and rejected experiments
[[17]](REFERENCES.md#ref-17). A cumulative local sparse scaling workload reported
mean dense-to-auto reductions of approximately 62.1%, 92.0%, and 97.6% at 32,
64, and 128 algebraic unknowns. Those figures describe one named workload and
environment; they are not portable speed guarantees. Small sparse cases with
negative gains were retained as crossover evidence, which is why the automatic
policy leaves them dense.

Event-heavy performance now has a separate retained optimization. The exact
built-in circuit path compiles breakpoint providers once per simulation run and
deduplicates pure built-in schedules by timing signature. Balanced local runs
reduced pulsed workloads by approximately 11.6% to 16.2% and switched workloads
by 18.3% to 22.1%, with exact state, metric, rejection, and work traces. A
bounded cache for the demand-gated generated sparse assembly kernel added a
further 4.0% to 5.9% on repeated switched topologies while continuing to read
all mutable numerical values from the live circuit. Later circuit instances can
now adopt a previously demand-qualified exact-topology kernel immediately, and
32-or-more-switch circuits can share duplicate immutable built-in control values
while unique and custom controls stay on the original sampler. Together those
two new changes reduced the repeated 16- and 32-channel switched workloads by
4.1% and 6.0% against their exact pre-loop baseline
[[17]](REFERENCES.md#ref-17).

Qualified KLU reuse adds another large-network gain. Automatic adoption is
limited to native sensitivity systems with at least 128 algebraic unknowns and
32 right-hand sides. Balanced local runs reduced 32-channel sine, mixed, pulsed,
and switched workloads by approximately 2.0%, 4.2%, 4.3%, and 3.1%, respectively,
with exact state, metric, rejection, and deterministic work traces. This is a
backend- and host-specific result, not a portable guarantee
[[17]](REFERENCES.md#ref-17).

A second KLU hot-path loop followed the measured costs rather than the initial
ownership hypothesis. Vectorized pivot and matrix-scale checks, batched reactive
sensitivity processing, constant-time native RHS shape validation, stable native
pointers, and direct independent result-buffer solves reduced the same four workload
classes by a further 4.1% to 6.8% against the exact first-KLU baseline, again with
exact traces [[17]](REFERENCES.md#ref-17).

A third boundary loop retained public immutable factorization behavior while
removing unnecessary private assembly objects. The generated sparse kernel can
return its raw scalar value list directly to one combined KLU factor-and-batched-
solve operation, which also returns the reusable factorization required by the
subsequent projection correction. Isolated native sensitivity improved by about
3.3% in both capacitor-only and mixed profiles. Whole-run effects were smaller
and workload-dependent, so the project records the kernel evidence separately
from end-to-end timing [[17]](REFERENCES.md#ref-17).

A fourth KLU loop separated Jacobian authority from residual accounting. Native
sensitivity needs only live algebraic derivatives, so an exact generated
Jacobian-only kernel now omits residual allocation, current stamping, diode-
current materialization, and accepted-cache replacement. The fast path is
limited to the already qualified large KLU crossover. Balanced local runs
against exact commit `351a8e0` reduced 32-channel workloads by approximately
0.9% to 8.0% and 64-channel workloads by 3.7% to 6.9%, with exact state, metric,
rejection, and deterministic work traces [[17]](REFERENCES.md#ref-17).

The mixed inductor path then removed a redundant ownership boundary. Advanced
indexing already creates an independent writable voltage-sensitivity gather, so
copying that gather again added bandwidth without additional isolation. The
one-line removal measured approximately 1.1% mean end-to-end improvement at 32
channels and 0.8% at 64 channels with exact traces
[[17]](REFERENCES.md#ref-17).

Deferred-reference execution then separated sensitivity evidence from storage
that only implicit correction consumes. At 64 or more dynamic states, an
unscheduled reference step retains the batched sensitivities and conservative
Jacobian norm without constructing the dense dynamic matrix. A later forced
reference upgrades the same owned result before chord correction. Balanced
64-channel runs at a reference interval of eight improved mixed, pulsed, and
switched workloads by approximately 1.1%, 1.4%, and 1.6%, with exact state,
metric, rejection, and work traces [[17]](REFERENCES.md#ref-17).

Independent replay was then measured as 17% to 43% of runtime in the profiled
anchor configurations. Mixed C+L trapezoidal replay now starts at the minimum
subdivision and evaluates a three-derivative quadrature defect. Failed evidence
restarts from the trusted anchor at a cubically predicted finer subdivision;
the original fixed `anchor_substeps` resolution remains the fail-closed ceiling.
In the qualified 32-channel mixed workload, replay steps fell from 201 to 101
at a 50-step anchor and balanced end-to-end timing improved by 13.45% on average
with a 12.85% minimum round gain. The adaptive endpoint remained within 0.864
weighted RMS of an eight-substep authority in the calibration run.

The same audit records rejected optimizations. Shared accepted-evaluation
Jacobian caching was rejected because later stiffness evaluations did not own
the same differential state. An exact-index accounting prototype improved an
isolated kernel but regressed end-to-end workloads. A generated residual-plus-
norm kernel produced negligible or negative whole-simulation gains. Preserving
these failures is scientifically useful because it prevents repeated work and
shows that local microbenchmarks do not automatically justify complexity. A
later deferred dense-Jacobian design was rejected for the same reason: switched
runs improved by about 0.6%, but sine regressed by 1.4% on average and mixed and
pulsed cases each contained a negative round. A direct C-order NumPy clone for
KLU right-hand sides was likewise rejected: the isolated copy became faster,
but native solve gains stayed below 0.7%, contained negative rounds, and the
switched end-to-end workload regressed by about 0.7% on average. The explicit
owned allocation and assignment therefore remains the simpler qualified path.

Two replay follow-ups were rejected as well. Carrying a qualified subdivision
across compatible anchors reduced retries from 31 to 17 in a one-channel run
and from eight to four in a 32-channel run, but total time increased by about
7.4% and 16.2%, respectively. It also improved agreement with an eight-substep
authority in the first case while worsening it in the second, so lower replay
work did not establish a uniform accuracy or performance gain. A Backward Euler
derivative-defect estimator was mathematically ordered under refinement, but
the default evidence cap repeatedly forced the maximum replay subdivision and
made the RC replay more expensive than fixed four-substep authority. Neither
prototype is retained.

Deterministic work counters accompany timing. Candidate and reference solves,
circuit evaluations, algebraic iterations, projections, differential Jacobian
evaluations, replay work, accepted steps, and rejected attempts are reported
separately [[15]](REFERENCES.md#ref-15). This makes it possible to explain why a
method is faster or slower without treating wall-clock noise as the only
measurement.

## Remaining Work

The project’s current high-value performance frontier is therefore clear.
Direct instrumentation found one initial KLU workspace miss followed by
identity hits, zero evictions, and one numeric refactor per new sensitivity in
the qualified workloads. Broader cache policy would not remove measured work.
Cross-anchor subdivision retention and the tested Backward Euler estimator have
now failed their retention gates. The next replay opportunity is a method-
specific BDF2 estimator with independent order and authority evidence. Reusable
KLU buffer residency remains a lower-level opportunity only if
caller-owned read-only inputs, independent results, stale-factor replay, and
cross-thread restoration remain exact. Each proposal must retain
source/installed equivalence, nonlinear qualification, bound behavior, and
exact fallback.

Replay subdivision is now independently evidence-controlled for mixed C+L
trapezoidal anchors. Remaining replay research should test BDF2 with its own
method-order evidence and combine any future anchor scheduling with a hard
maximum elapsed authority age. Merely increasing the anchor interval would
still weaken refresh frequency without proving that omitted replay work was
unnecessary [[17]](REFERENCES.md#ref-17).

The engineering result is not a single fast kernel. It is a chain of guarded
specializations whose validity can be traced to topology, state, time,
structure, and residual evidence. Dense and generic paths remain available;
accelerated paths fail back to them; and comparison plus release tooling checks
that packaging does not alter numerical output. This is the practical form of
the BAB-CS design principle: acceleration may propose, but validated numerical
authority must remain explicit.
