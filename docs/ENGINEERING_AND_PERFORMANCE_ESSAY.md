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
interface [[7]](REFERENCES.md#ref-7) [[9]](REFERENCES.md#ref-9). BAB-CS exposes
`dense`, `auto`, and `scipy` backend choices. `auto` is a measured policy rather
than an alias for sparse. It considers problem size, matrix density, whether a
structure can be reused, and whether multiple right-hand sides can amortize
setup. Small or dense systems remain on the dense implementation.

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
contraction reject the shortcut. The project intentionally leaves a benchmark-
only ULP-aware age relaxation outside production until full qualification is
repeated [[17]](REFERENCES.md#ref-17).

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

The same audit records rejected optimizations. Shared accepted-evaluation
Jacobian caching was rejected because later stiffness evaluations did not own
the same differential state. An exact-index accounting prototype improved an
isolated kernel but regressed end-to-end workloads. A generated residual-plus-
norm kernel produced negligible or negative whole-simulation gains. Preserving
these failures is scientifically useful because it prevents repeated work and
shows that local microbenchmarks do not automatically justify complexity.

Deterministic work counters accompany timing. Candidate and reference solves,
circuit evaluations, algebraic iterations, projections, differential Jacobian
evaluations, replay work, accepted steps, and rejected attempts are reported
separately [[15]](REFERENCES.md#ref-15). This makes it possible to explain why a
method is faster or slower without treating wall-clock noise as the only
measurement.

## Remaining Work

The project’s current high-value performance frontier is therefore clear.
Sparse symbolic-pattern reuse could remove repeated symbolic factorization that
SuperLU’s exposed path still performs. Projection state residency may reduce
remaining conversions if it stays lazy. Native residual ownership may enable
further fusion if deterministic `NaN` behavior is preserved. Cache hit, miss,
and eviction diagnostics should precede user-configurable cache policy. Each
proposal must retain source/installed equivalence, nonlinear qualification,
bound behavior, and exact fallback.

Adaptive replay is a separate research problem from replay initialization.
AB3 can make each substep cheaper, but replay still covers every accepted
interval. Reducing the number of replay substeps would require an independent
accuracy estimate, maximum elapsed anchor time, event awareness, and fail-
closed retry. Merely increasing the anchor interval would weaken refresh
frequency without proving that the omitted replay work was unnecessary
[[17]](REFERENCES.md#ref-17).

The engineering result is not a single fast kernel. It is a chain of guarded
specializations whose validity can be traced to topology, state, time,
structure, and residual evidence. Dense and generic paths remain available;
accelerated paths fail back to them; and comparison plus release tooling checks
that packaging does not alter numerical output. This is the practical form of
the BAB-CS design principle: acceleration may propose, but validated numerical
authority must remain explicit.
