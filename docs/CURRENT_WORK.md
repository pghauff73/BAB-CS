# BAB-CS Current Work: Project Position and Integrated Design

## Present Position

BAB-CS began with a narrow question: can an Adams–Bashforth circuit integrator
be made useful over long simulations without pretending that an explicit
multistep formula is unconditionally stable? The present project answers by
changing the unit of design. Instead of treating AB2 as a self-sufficient
solver, BAB-CS treats it as one candidate inside a supervisory numerical
system. Projection, independent implicit authority, correction, recursive
error accounting, passivity checks, event handling, and periodic replay are the
system; Adams–Bashforth is one economical proposal mechanism within it
[[12]](REFERENCES.md#ref-12) [[23]](REFERENCES.md#ref-23).

This position is deliberately different from claiming a new universally
stable Adams method. Classical stability results place hard limits on linear
multistep formulas, and explicit Adams–Bashforth methods retain bounded
stability regions rather than becoming A-stable through naming or tuning
[[3]](REFERENCES.md#ref-3). BAB-CS therefore does not modify the mathematical
stability region of raw AB2. It limits the authority of AB2 by comparing,
correcting, replacing, and periodically rebuilding its trajectory. The project
is best understood as an error-bounded control architecture around several
candidate integrators, not as a proof that an explicit method has acquired the
properties of an implicit one.

The circuit formulation follows the modified-nodal tradition established for
general circuit equations and developed into the SPICE family of simulators
[[1]](REFERENCES.md#ref-1) [[2]](REFERENCES.md#ref-2). BAB-CS uses capacitor
voltages and inductor currents as its differential coordinates. Node voltages
and voltage-defined branch currents are algebraic unknowns. Every state
evaluation solves Kirchhoff current balance and voltage constraints before
derivatives, energy, or diagnostic quantities are accepted
[[12]](REFERENCES.md#ref-12) [[25]](REFERENCES.md#ref-25). This semiexplicit
partition keeps the dynamic state physically interpretable while making the
algebraic consistency problem explicit.

The currently implemented device set is intentionally small but complete
enough for controlled transient experiments. It includes resistors,
capacitors, inductors, independent current and voltage sources, Shockley
diodes, and time-controlled resistive switches. Source and control waveforms
may be constant, sinusoidal, pulsed, or piecewise linear. Initial capacitor
voltages and inductor currents are preserved as dynamic initial conditions
[[11]](REFERENCES.md#ref-11) [[25]](REFERENCES.md#ref-25). Unsupported singular,
floating, conflicting, or higher-index topologies fail explicitly rather than
being silently regularized with hidden conductances or storage.

AB2 remains the default candidate because it reuses previous derivative
information and requires only one new projected endpoint once its history is
valid. The implemented predictor is variable-step AB2, with its coefficients
changing according to the ratio of the current and previous steps. Step-ratio
limits prevent damaged history from being reused after abrupt timestep
changes, and startup or invalid history transfers authority to an implicit
method [[5]](REFERENCES.md#ref-5) [[23]](REFERENCES.md#ref-23). This makes the
history policy part of correctness rather than an incidental optimization.

## Bounded Numerical System

The project now extends the same controller to explicit Euler, Heun,
Bogacki–Shampine RK23, backward Euler, trapezoidal, and BDF2 candidates
[[4]](REFERENCES.md#ref-4) [[14]](REFERENCES.md#ref-14). This extension is a
major current result because it demonstrates that the bounding architecture is
not intrinsically tied to Adams–Bashforth. Each candidate supplies a proposed
differential endpoint and work metrics; the controller retains ownership of
projection, independent reference selection, correction, residual gates,
passivity, re-anchoring, and state authority.

The ordinary active step computes a candidate and an implicit reference from
the same accepted state. It then blends the candidate toward the reference with
a gain selected from a conservative amplification estimate. If the resulting
closed-loop estimate cannot be made contractive, the reference receives full
authority. A second projection ensures that the corrected differential state
is accompanied by a consistent algebraic solution
[[13]](REFERENCES.md#ref-13) [[23]](REFERENCES.md#ref-23). This correction is not
presented as a substitute for exact error analysis; it is a runtime mechanism
for limiting propagation relative to the implemented reference model.

The recursive bound records the effect of previous estimated error and the new
local defect. In simplified form, the project tracks `B_next = q B + delta`,
where `q` is the corrected propagation estimate and `delta` combines the
candidate/reference or embedded defect with normalized residual evidence. If
`q` remains below one and the local defect remains bounded, the recurrence has
a finite geometric envelope. When a deferred-reference fast path is used,
`q` may temporarily exceed one, so the design instead enforces a finite
checkpoint interval and a hard bound cap that promotes reference authority
before unbounded modeled growth is allowed [[13]](REFERENCES.md#ref-13)
[[14]](REFERENCES.md#ref-14).

Independent periodic replay addresses a separate weakness. A local implicit
reference begins from the already accepted state and is therefore not
independent of accumulated trajectory error. BAB-CS periodically returns to a
trusted anchor and reintegrates the complete interval with smaller implicit
steps. The replay endpoint replaces the provisional endpoint, the recursive
bound resets, and multistep history is rebuilt. This design follows the broader
principle that projection and correction control local consistency, while an
independent reconstruction limits inherited drift [[6]](REFERENCES.md#ref-6)
[[26]](REFERENCES.md#ref-26).

Replay is always authoritative but has been engineered to avoid unnecessary
Newton work. After sufficient uniform replay history exists, an AB3
extrapolation supplies only the differential initial guess. On eligible large
sparse systems, a quartic extrapolation may also supply an algebraic initial
guess. Neither extrapolation decides acceptance: a failed guess is discarded,
and the same implicit residual and convergence gates remain in force
[[17]](REFERENCES.md#ref-17) [[26]](REFERENCES.md#ref-26). This separation of
prediction from authority is a recurring design rule throughout the project.

Known source discontinuities are handled as numerical events. The simulator
clips an integration step so that pulse and piecewise-linear breakpoints are
reached exactly. When an accepted endpoint reaches a breakpoint, multistep
history and its bound are reset, and the next step restarts implicitly
[[28]](REFERENCES.md#ref-28). A rejected shortened step is not mislabeled as an
event. The current implementation does not yet perform arbitrary analog root
finding for state-dependent thresholds; its event guarantee applies to known
waveform breakpoints.

The passivity monitor gives the controller a physical diagnostic that is
independent of algebraic residual size. BAB-CS compares the change in stored
capacitor and inductor energy with trapezoidally integrated source work and
dissipation. Positive unexplained energy is normalized and gated, while signed
energy balance remains visible so numerical damping is not hidden
[[13]](REFERENCES.md#ref-13). The project explicitly avoids interpreting this
quantity as a phase-error bound: an oscillator may preserve energy while
accumulating phase error.

The rollout model separates experimentation from authority. In `disabled`
mode, only the implicit integrator is used. In `shadow` mode, candidate steps
and diagnostics are evaluated but the implicit reference is always accepted.
In `active` mode, a bounded candidate/reference result may be accepted if every
gate passes. Shadow is the default, and there is no unanchored candidate-only
production mode [[11]](REFERENCES.md#ref-11) [[12]](REFERENCES.md#ref-12). This
allows a new candidate to be characterized before it can affect a trajectory.

## Engineering and Tooling

The embedded fast path is the clearest present route to useful speed. Heun,
RK23, and AB2 expose lower-order companion estimates that can support selected
steps without an immediate implicit reference. Scheduled reference checks,
stiffness detection, amplification-domain checks, a hard deferred-bound cap,
and mandatory independent replay constrain that saving
[[14]](REFERENCES.md#ref-14). Current local characterization identifies bounded
RK23 as the strongest accuracy-oriented explicit candidate and bounded AB2 as
the lower-work historical baseline, but those measurements are workload-
specific rather than universal rankings.

The implementation remains dependency-free by default. A dense partial-
pivoting solver supports small cases, while `auto` and `scipy` backends can use
SciPy’s SuperLU interface for eligible sparse systems
[[7]](REFERENCES.md#ref-7) [[9]](REFERENCES.md#ref-9) [[27]](REFERENCES.md#ref-27).
A compatible system SuiteSparse KLU 2 library adds bounded symbolic/numeric
refactorization through `auto` for qualified large batched sensitivities or
through explicit `klu` selection [[35]](REFERENCES.md#ref-35). The automatic
policy considers matrix size, structural density, reuse, and multi-right-hand-
side opportunity rather than sending every circuit through a sparse solver.
Unavailable explicit backends fail clearly; automatic KLU failure restores
SciPy.

Substantial current engineering work targets sparse and nonlinear overhead.
The circuit compiles CSC structure and device stamp locations, reuses bounded
thread-local numeric workspaces, probes fill-reducing versus natural ordering,
specializes residual and Jacobian assembly for built-in circuits, samples
mutable inputs once per evaluation, batches differential sensitivities, and
uses exact coupled block or guarded Schur updates where qualified
[[17]](REFERENCES.md#ref-17) [[25]](REFERENCES.md#ref-25). These optimizations
are guarded by structural, finiteness, residual, contraction, topology, and
fallback checks rather than being allowed to alter authority.

The KLU adapter retains symbolic and numeric state in a bounded 128-entry
per-thread LRU, checks unscaled U pivots against the existing singularity
threshold with vectorized finite/minimum scans, owns every overwritten right-
hand-side buffer, and can restore stale, evicted, or cross-thread factors from
immutable matrix data. Stable native pointers and a direct independent result
buffer reduce adapter overhead without exposing mutable results. Native sensitivity
also batches inductor column gathering and reuses mutation-aware reactive scale
arrays. Automatic use is limited to sensitivity matrices with at least 128
algebraic unknowns and 32 right-hand sides. Against the first pushed KLU baseline,
paired local runs reduced four 32-channel workloads by about 4.1% to 6.8% with
exact state, metric, rejection, and work traces [[17]](REFERENCES.md#ref-17).
At the same crossover, a separate generated Jacobian-only kernel now avoids
constructing the residual and diode-current cache that native sensitivity does
not consume. Against exact commit `351a8e0`, balanced local runs reduced the
four 32-channel workloads by 0.9% to 8.0% and the 64-channel workloads by 3.7%
to 6.9%, with exact state, metric, rejection, and deterministic work traces
[[17]](REFERENCES.md#ref-17).
Mixed native sensitivity also reuses the independent writable array already
created by NumPy advanced indexing instead of copying it again. This smaller
follow-up reduced the 32-channel mixed workload by 1.1% and the 64-channel
mixed workload by 0.8% on average with exact traces
[[17]](REFERENCES.md#ref-17).

The current simulator also compiles pure built-in breakpoint schedules once per
run, deduplicating identical timing while preserving custom waveform calls and
subclass dispatch. The mathematical two-step Schur evidence window is now
ULP-aware. Demand-gated sparse assembly kernels are shared by exact structural
topology, later circuit instances can adopt a previously qualified hot kernel on
their first eligible assembly, and 32-or-more-switch circuits can share exact
immutable built-in control values without changing custom-provider observability
[[17]](REFERENCES.md#ref-17).

The CLI reads JSON circuit descriptions, permits rollout, candidate,
reference, backend, contraction, interval, and bound-cap overrides, and writes
deterministic JSON summaries and CSV step histories [[11]](REFERENCES.md#ref-11).
The output includes accepted and rejected work, projection and reference
iterations, candidate and replay effort, residuals, energy defects,
amplification, contraction, bound evolution, anchor deviations, event resets,
and fallback counts. The aim is to make numerical decisions auditable rather
than to expose only a final waveform.

## Evidence and Release State

The qualification surface now comprises 219 test methods across model,
linear-algebra, integrator, candidate, nonlinear, event, long-horizon,
comparison, packaging, and release-evidence modules [[32]](REFERENCES.md#ref-32).
Long and very-long tests are opt-in tiers, and optional sparse tests execute
when SciPy or KLU is available. The suite includes direct formula checks, analytic
convergence, refined-replay comparisons, failure injection, topology rejection,
event-history behavior, energy and phase separation, deterministic output, and
evidence-tampering rejection.

The canonical comparison manifest contains eight circuit families and fifteen
named method configurations [[22]](REFERENCES.md#ref-22). Analytic authorities
are used for supported linear circuits, while nonlinear diode and switch cases
use separately configured refined replay. The runner reports fixed-step,
fixed-accuracy, and fixed-work views, and separates numerical outputs from wall-
clock timing so qualification does not depend on hardware noise
[[15]](REFERENCES.md#ref-15) [[29]](REFERENCES.md#ref-29).

Ngspice comparison is retained as cross-implementation evidence rather than a
competition claim. Four mapped cases generate an ngspice netlist, raw waveform,
tool log, and comparison report. The mapping rejects unsupported semantic
differences, including diode parameters that cannot be represented faithfully
[[8]](REFERENCES.md#ref-8) [[16]](REFERENCES.md#ref-16)
[[30]](REFERENCES.md#ref-30). Agreement supports the mapped cases; it does not
prove general superiority over ngspice’s much broader production simulator.

Continuous integration mirrors these layers. Normal CI spans supported Python
versions, deterministic examples, comparison smoke, wheel construction, clean
installation, and optional SciPy/KLU sparse qualification. Scheduled workflows run the
longer matrix and external comparisons. The release-qualification workflow
records exact source and environment identity, runs full source and installed-
wheel suites, builds the wheel twice, compares source and installed numerical
artifacts byte-for-byte, constructs a manifest, verifies checksums, and uploads
evidence without publishing a release [[33]](REFERENCES.md#ref-33).

The proposed package version is `1.1.0`, but the release remains a draft. The
repository contains the qualification infrastructure, not an automatic grant
of release authority. Tagging, approval, publication, and post-publication
download verification require human review tied to an exact source commit,
tag, wheel hash, manifest hash, workflow run, and evidence set
[[19]](REFERENCES.md#ref-19) [[20]](REFERENCES.md#ref-20)
[[21]](REFERENCES.md#ref-21). This distinction prevents a successful script
from being mistaken for a scientific or release decision.

## Significance, Limits, and Next Work

BAB-CS is currently remarkable where observability and bounded authority are
more valuable than device breadth. It offers one controller across explicit,
implicit, one-step, and multistep candidates; preserves an independent replay
path; exposes deterministic work and bound diagnostics; and treats rejected
optimizations as evidence rather than silently discarding them. That makes the
project useful as a research platform for numerical integration, circuit-model
experiments, runtime assurance, and reproducible simulator qualification.

Its limits are equally important. The device library is small, arbitrary analog
event localization is absent, unsupported higher-index topologies fail closed,
the recursive bound is not an interval proof of unknown physical error, and
performance evidence is local to named workloads. BAB-CS should therefore be
described as a bounded multi-method circuit-simulation reference implementation,
not as a replacement for SPICE, a formal verifier, or a universal cure for
long-time numerical error [[11]](REFERENCES.md#ref-11)
[[15]](REFERENCES.md#ref-15).

The next research phase follows directly from this current position. Private
raw sparse values now feed a combined KLU factor-and-solve handle, native
sensitivity has an independent Jacobian-only assembly kernel, and mixed C+L
trapezoidal replay uses derivative-defect evidence with complete-window retry.
The highest-value remaining paths are KLU right-hand-side and result residency,
diagnostics for factorization and generated-kernel cache policy, native residual
ownership, and evidence-gated anchor scheduling with a maximum elapsed authority
age. Device expansion, state-dependent event localization, broader DAE topology
handling, and stronger bound-coverage arguments remain larger scientific
programs rather than small optimizations [[17]](REFERENCES.md#ref-17).
