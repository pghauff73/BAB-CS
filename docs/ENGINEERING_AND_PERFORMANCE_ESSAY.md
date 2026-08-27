# Circuit Engineering and Performance in Bounded-Authority-Based-Circuit-Simulation

## Why Authority Must Survive Optimization

Bounded-Authority-Based-Circuit-Simulation (`BAB-CS`) is engineered so that a
faster numerical path cannot quietly bypass the checks that make a result
reviewable. The project treats performance as an optimization problem inside a
fixed authority architecture. A proposed acceleration is retained only when it
improves complete workloads, preserves numerical behavior, keeps failure modes
visible, and leaves a safe fallback available.

For a novice, the central rule is simple: **the part that runs faster is not
allowed to redefine what counts as correct**. Candidate methods propose states.
The circuit model enforces electrical equations. Independent methods and replay
challenge the proposal. The controller owns acceptance. The simulator owns
event alignment and retry behavior [[23]](REFERENCES.md#ref-23)
[[28]](REFERENCES.md#ref-28).

## Follow One Timestep Through Its Decision Owners

Five owners divide the decisions made during one timestep. An **owner** is the
part of the software allowed to make one specific class of decision.

1. The **simulator** chooses the attempted timestep and shortens it when needed
   to land exactly on a declared source or switch event.
2. A **candidate integrator** applies one numerical formula and proposes the next
   dynamic state. It also records how much numerical work it performed, but it
   cannot accept its own proposal.
3. The **circuit model** applies topology and component equations, projects the
   proposal onto the circuit constraints, and computes stored energy, source
   power, dissipated power, and sensitivity.
4. An **independent integrator** computes a reference or replay result. The
   implicit integrators own backward Euler, trapezoidal integration, backward
   differentiation formula order two (`BDF2`), nonlinear iteration, and replay.
   An implicit method solves an equation that contains the new state itself.
5. The **bounded controller** compares the evidence, applies correction and hard
   gates, updates the recursive error bound, and either accepts, falls back to a
   safer method, or rejects the attempt for retry.

This ownership chain prevents a convenient fast path from changing a circuit
equation, weakening an acceptance rule, or approving its own answer without the
rest of the authority system noticing [[24]](REFERENCES.md#ref-24)
[[25]](REFERENCES.md#ref-25) [[26]](REFERENCES.md#ref-26).

## Build the Circuit in a Repeatable Order

The `Circuit` constructor validates component values, normalizes node names,
establishes a repeatable node and branch order, and separates dynamic variables
from algebraic variables. Capacitor voltages and inductor currents are the
dynamic state because they store electrical memory. Node voltages and currents
through voltage-defined branches are algebraic unknowns because they must satisfy
the circuit equations at each evaluation.

The formulation uses modified nodal analysis (`MNA`), a standard method that
turns a circuit into equations while retaining the sparse connectivity of the
network [[1]](REFERENCES.md#ref-1). **Deterministic ordering** means that the
same declared circuit produces the same internal ordering rather than depending
on incidental container or allocation behavior. That property supports stable
reports, repeatable hashes, and reliable comparison between source and installed
packages.

At each evaluation, the model samples sources and switch controls, solves the
algebraic equations, calculates the dynamic derivative, and reports stored
energy, source power, and dissipated power. The accepted evaluation therefore
contains both the state and the diagnostics required to judge it. Public output
retains meaningful node and branch names; optimized internal paths use ordered
arrays so they do not rebuild dictionaries during every solve.

## Solve Small Systems with the Dense Baseline

BAB-CS solves small systems with dependency-free linear algebra. **Linear
algebra** is the matrix-based mathematics used to solve simultaneous circuit
equations. The dense implementation stores every matrix entry, including zeros,
and provides:

- partial pivoting, which rearranges equations to avoid weak division points;
- singularity detection, which identifies an unsolvable or underdetermined
  equation system;
- factored solves for one or several right-hand sides;
- finite-difference Jacobians, which estimate sensitivities by small input
  changes;
- infinity norms; and
- weighted root-mean-square scaling, which combines component errors after
  applying absolute and relative tolerances [[27]](REFERENCES.md#ref-27).

This path is not merely a convenience. It gives small circuits, tests, and clean
package installations an auditable implementation that does not require a
compiled third-party solver.

## Scale Repeated Solves with Sparse Execution

A **sparse matrix** contains mostly zeros. Larger circuit equations are usually
sparse because each device connects only a few nodes. BAB-CS can use SciPy, a
Python scientific-computing library, to store a matrix in compressed sparse
column (`CSC`) form. CSC stores nonzero values by column rather than storing the
whole matrix. SciPy supplies the SuperLU sparse factorization interface.
**Factorization** rewrites a matrix into parts that make repeated equation solves
more efficient
[[7]](REFERENCES.md#ref-7) [[9]](REFERENCES.md#ref-9).

BAB-CS also supports an optional SuiteSparse KLU adapter. KLU is a sparse linear
solver designed for circuit-like matrices. The adapter reaches a compatible
system library through `ctypes`, Python’s standard interface for calling compiled
C functions [[35]](REFERENCES.md#ref-35). Users may select `dense`, `scipy`,
`klu`, or `auto`. The `auto` policy considers size, density, structural reuse,
and the number of right-hand sides. It does not assume that sparse execution is
always faster.

One important optimization compiles circuit topology once. The compiler records
CSC row indices, column pointers, device stamp locations, constraint locations,
and sensitivity structure. Repeated evaluations then change only numeric values.
Component parameters remain live: compilation records where a value belongs,
not what the future value must be [[17]](REFERENCES.md#ref-17)
[[25]](REFERENCES.md#ref-25).

Sparse workspaces are bounded. A **workspace** is reusable memory associated
with a matrix structure. A bounded cache limits how many workspaces a thread may
retain, preventing a speed optimization from becoming unbounded memory growth.
KLU can reuse symbolic analysis, which studies the nonzero pattern, and then
refactor only new numeric values for the same pattern. If KLU fails in automatic
mode, BAB-CS falls back to SciPy rather than converting an optional accelerator
into a single point of failure.

## Accelerate Nonlinear Solves without Weakening Replay

A diode makes the circuit equations nonlinear. BAB-CS uses Newton iteration,
which repeatedly linearizes the equations and solves for a correction. The
implementation preserves damping, limiting, finite-value checks, iteration
limits, and residual gates while optimizing repeated assembly work. A
**residual** is the remaining equation mismatch at the computed state.

Replay is an independent recomputation from a trusted anchor. Mixed capacitor-
and-inductor trapezoidal replay now uses derivative-defect evidence to decide
whether a complete replay window needs finer internal subdivisions. A
**derivative defect** is disagreement between the derivative behavior implied by
different points or methods. Piecewise-switched BDF2 replay has separate startup,
order, and event evidence because a multistep method cannot safely reuse history
across a discontinuity.

Event handling preserves authority before it preserves speed. An accepted switch
or source breakpoint forces independent replay before multistep history is
cleared. The next startup step uses the reference method. This prevents a fast
event reset from erasing the independent check that should have occurred at the
event.

## Measure the Whole Simulation, Not One Fast Kernel

A **kernel** is a small, frequently executed operation such as assembling a
matrix, calculating a norm, or solving a factored equation. Making a kernel
faster can be valuable, but an engineering project pays for the complete
simulation: setup, candidate work, projection, reference work, replay, event
handling, rejected attempts, report generation, and data movement.

For example, a faster matrix solve may provide little complete-run benefit if it
requires repeated format conversion or causes more reference recomputations. A
cache can reduce setup work but become harmful if it grows without a limit or
reuses data after component values change. BAB-CS therefore retains an
optimization only after end-to-end workloads show a gain and the authority path
still produces equivalent accepted results and failure causes.

For a novice engineer, the practical test is: **did the whole declared workload
become faster while producing the same governed result?** A microbenchmark of one
inner operation cannot answer that question by itself.

## Separate Algorithmic Work from Wall-Clock Time

Wall-clock time changes with processor load, operating-system scheduling,
library versions, and hardware. BAB-CS therefore records **deterministic work
counters** alongside timing. These counters include candidate solves, reference
solves, circuit evaluations, algebraic iterations, projections, Jacobian
evaluations, replay steps, accepted steps, and rejected attempts
[[15]](REFERENCES.md#ref-15).

A fixed-work report compares methods under a declared operation budget. A timing
report measures elapsed time on a named machine and environment. The two answer
different questions. Work counts help explain algorithmic cost. Timing helps
characterize one implementation on one system. Neither is allowed to replace
correctness evidence.

## Keep Only End-to-End Improvements

BAB-CS keeps a chain of guarded improvements rather than one dramatic shortcut.
Retained work includes compiled sparse topology, batched sensitivity solves,
reusable sparse workspaces, bounded KLU reuse, direct access to generated numeric
stamp values, compiled built-in event schedules, and roundoff-aware evidence
windows. A **unit in the last place** (`ULP`) is the gap between adjacent
floating-point numbers near a value; ULP-aware comparisons avoid treating
representational rounding as a large physical difference.

Several plausible optimizations were rejected after end-to-end measurement:

- broad array batching of the current diode workload did not improve the
  qualified 32-channel crossover and changed floating-operation ordering at
  larger sizes;
- carrying replay subdivision choices across anchors reduced some replay counts
  but slowed measured complete workloads and did not improve authority agreement
  consistently;
- a general backward-Euler defect policy over-refined a simple resistor-
  capacitor replay and increased work;
- dynamic anchor intervals appeared faster in some switched runs only because
  event resets suppressed independent replay; and
- several isolated copy, norm, and residual kernels improved microbenchmarks but
  did not produce a reliable full-simulation gain.

These negative results are engineering evidence. They show why a fast inner
operation is not automatically a faster complete simulation or a better
engineering result.

## Prioritize the Remaining Measured Costs

The next performance work should target costs that remain visible in complete
profiles:

1. keep KLU numeric buffers resident without weakening independent factor
   ownership;
2. move residual calculation closer to native factorization so the same matrix
   data does not cross language boundaries repeatedly;
3. expose cache hits, misses, refactors, evictions, and fallbacks before making
   cache policy more automatic;
4. continue method-specific replay research while enforcing a maximum elapsed
   authority age; and
5. expand nonlinear batching only at a larger evidence-gated workload where
   complete simulation gains can be demonstrated.

Each direction must preserve mutable parameters, deterministic failure behavior,
source-versus-installed equivalence, nonlinear qualification, exact event
alignment, and generic fallback.

## Know Where This Engineering Claim Stops

BAB-CS is not presented as the fastest circuit simulator in general. Its current
performance evidence is local to declared workloads, hardware, software, and
backend configurations. It is also not a production semiconductor, thermal,
electromagnetic, or hardware-in-the-loop environment. Hardware-in-the-loop means
testing real controller hardware against a simulated plant.

The engineering contribution is narrower and more defensible: BAB-CS shows how
to accelerate a circuit simulation while preserving a visible chain from model
equations to proposed state, independent authority, accepted result, work report,
artifact identity, and fallback behavior.
