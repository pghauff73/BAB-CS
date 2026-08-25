# Applications and Research Roadmap for BAB-CS

## Current Applications

BAB-CS is immediately applicable as a research simulator for small transient
circuits whose capacitor voltages and inductor currents determine a unique
algebraic operating state. The present device library supports passive RLC
networks, independent sources, diodes, and time-controlled resistive switches
[[11]](REFERENCES.md#ref-11) [[25]](REFERENCES.md#ref-25). Within that boundary,
the project can study accuracy, stability, drift, event handling, nonlinear
convergence, and the computational cost of bounded candidate methods.

The first application area is numerical-method comparison. Because explicit
Euler, Heun, RK23, AB2, backward Euler, trapezoidal, and BDF2 share one
controller, researchers can change the candidate while retaining the same
projection, reference, correction, replay, residual, energy, and diagnostic
rules [[14]](REFERENCES.md#ref-14). This controls more variables than comparing
independent solver programs whose event, tolerance, and output policies differ.

The second area is long-horizon oscillator research. LC and lightly damped RLC
circuits expose the distinction between energy drift, amplitude drift, phase
drift, and residual consistency. BAB-CS records these quantities separately and
periodically replays from trusted anchors [[15]](REFERENCES.md#ref-15). This
makes it useful for studying how multistep history, correction strength, anchor
spacing, and replay refinement affect cumulative phase behavior.

The third area is nonlinear transient experimentation. Diode clipping and
recovery cases exercise Newton convergence, projection, line search, event
interaction, and reference promotion. The current nonlinear scope is narrow,
but it is sufficient to compare every-step reference control with embedded
fast paths and guarded nonlinear prediction [[17]](REFERENCES.md#ref-17)
[[18]](REFERENCES.md#ref-18). The project is especially useful when the research
question concerns numerical authority rather than a broad device library.

The fourth area is switched-system analysis with known schedules. Pulse and
piecewise-linear breakpoints are reached exactly, and multistep history is reset
at accepted events [[28]](REFERENCES.md#ref-28). This supports controlled
experiments with sampled switching, pulsed RC networks, and predetermined
converter-like waveforms. It does not yet support general state-triggered
switching or arbitrary threshold root finding, so production power-electronics
claims would be premature.

The fifth area is runtime assurance. Shadow mode executes candidate logic and
diagnostics while preserving implicit reference authority. A new method can
therefore be observed under realistic circuit steps before it is allowed to
change the accepted state [[12]](REFERENCES.md#ref-12). This pattern is useful
for staged numerical deployment: disabled establishes a reference baseline,
shadow collects evidence, and active grants bounded authority only after the
candidate’s behavior is understood.

The sixth area is deterministic benchmarking. BAB-CS counts candidate,
reference, projection, Jacobian, algebraic, and replay work independently of
wall time [[15]](REFERENCES.md#ref-15). Researchers can ask whether an embedded
method saves reference solves, whether a sparse optimization reduces
factorization setup, or whether replay initialization reduces Newton work
without letting machine load decide the result.

The seventh area is sparse-solver research for repeated circuit structures.
The optional backend compiles CSC topology, reuses bounded workspaces, batches
sensitivities, reuses KLU symbolic/numeric state for qualified large batched
systems, and compares dense and sparse crossover behavior
[[17]](REFERENCES.md#ref-17) [[27]](REFERENCES.md#ref-27)
[[35]](REFERENCES.md#ref-35). This provides a compact environment for testing
ordering policy, state residency, block factorization, cache diagnostics, and
safe backend fallback before attempting the same ideas in a full production
simulator.

The eighth area is reproducible scientific packaging. The project can build a
deterministic wheel, inspect its metadata and members, qualify the installed
artifact, compare source and installed numerical reports byte-for-byte, and bind
the evidence with a deterministic manifest and checksums
[[20]](REFERENCES.md#ref-20) [[31]](REFERENCES.md#ref-31). This makes BAB-CS a
case study in treating a numerical release as an evidence object rather than
only a version number.

The ninth area is education. The codebase is small enough for students to trace
modified nodal equations, explicit and implicit integration, Newton iteration,
projection, event resets, passivity, sparse factorization, and release evidence
within one repository. Historical SPICE and MNA sources provide the circuit-
simulation background [[1]](REFERENCES.md#ref-1)
[[2]](REFERENCES.md#ref-2), while Dahlquist and Bogacki–Shampine provide the
numerical-method context [[3]](REFERENCES.md#ref-3)
[[4]](REFERENCES.md#ref-4).

The tenth area is regression-oracle design. BAB-CS explicitly ranks analytic
solutions, refined replay, external comparison, internal implicit authority,
and local step reference [[15]](REFERENCES.md#ref-15). That hierarchy can inform
other scientific software: a local corrector should not be labeled independent
truth, and an external simulator should not be used without checking semantic
mapping.

## Transfer Possibilities

Beyond circuit simulation, the architecture may apply to semiexplicit
differential-algebraic systems with a solvable algebraic manifold. A candidate
ODE-like method could advance differential coordinates, a projection could
restore constraints, an implicit method could provide reference authority, and
periodic replay could refresh the accumulated trajectory. Projection research
in constrained systems supports the general relevance of this pattern
[[6]](REFERENCES.md#ref-6). BAB-CS does not yet implement these other domains,
so this is a research transfer hypothesis rather than a current feature.

Constrained mechanical systems are one possible extension. Positions or
momenta could form the differential state while holonomic constraints define
an algebraic manifold. A bounded candidate would need a domain-appropriate
projection, energy and momentum diagnostics, and an independent replay method.
The present circuit energy gate could not simply be copied; its source,
dissipation, and storage terms are circuit-specific.

Power-system differential-algebraic models are another possible extension.
Generator dynamics, controls, and network algebraic equations share a
differential/algebraic structure, but practical power models introduce scale,
index, discontinuity, and stiffness requirements beyond the present code. A
transfer would require sparse symbolic reuse, robust event localization,
domain-specific residual scaling, and much broader model qualification before
the controller could claim operational value.

Electrochemical, thermal-electrical, and multiphysics reduced models may also
benefit from bounded candidate/reference separation. These systems often have
slow states coupled to algebraic constraints or fast local solves. An embedded
RK or multistep candidate could propose the slow evolution while an implicit
reference and periodic replay limit accumulated error. The central design rule
would remain: the reference must be sufficiently independent to justify its
authority.

Real-time and hardware-in-the-loop simulation is an attractive but demanding
future application. BAB-CS fast paths show how reference work can be scheduled
or promoted dynamically, which is relevant to a fixed compute budget. However,
the current Python implementation, variable rejection work, and mandatory
replay do not provide hard real-time guarantees. A real-time version would need
worst-case execution analysis, bounded allocation, deterministic sparse
factorization, deadline-aware fallback, and explicit treatment of missed
deadlines as numerical failures.

Digital-twin monitoring is another plausible direction. Shadow mode could run
one or more candidate methods beside an authoritative model, while bound,
residual, energy, and anchor deviations become health signals. This could help
distinguish integrator degradation from model mismatch. The current project
does not include parameter estimation, sensor assimilation, or uncertainty
quantification, so a digital-twin claim would require substantial additional
work.

Safety-oriented simulation is a natural conceptual application because BAB-CS
records why authority changed. Nonfinite values, stiffness, residual failure,
energy injection, projection failure, reference failure, and replay failure
remain separate outcomes [[12]](REFERENCES.md#ref-12). Yet this transparency is
not equivalent to safety certification. Certification would require a defined
hazard model, requirements traceability, independent verification, toolchain
qualification, and domain-specific evidence outside the current project.

The error-bounding controller can also serve as a method-screening framework.
New embedded Runge–Kutta pairs, stabilized explicit methods, Rosenbrock-like
candidates, exponential integrators, or predictor stages from production
simulators could be evaluated if they expose a projectable endpoint and a
defensible defect or amplification estimate. The controller should not be
attached mechanically: each method requires a candidate-specific stability
model, work accounting, history policy, and independent reference pairing.

Bounded Adams–Bashforth is most compelling when derivative reuse matters and
the circuit remains in a smooth nonstiff region for several steps. Bounded RK23
is compelling when a stronger embedded estimate justifies its projected stages.
Heun offers a lower-stage second-order alternative. Implicit candidates are
most useful as controlled comparisons or when their different damping and
stability properties are themselves the subject of study
[[14]](REFERENCES.md#ref-14). No one candidate is expected to dominate every
topology and tolerance.

## Research Timeline

The project’s research timeline begins with a completed foundation phase. That
phase established the semiexplicit circuit model, variable-step AB2,
projection, implicit startup and reference methods, contractive correction,
recursive bound reporting, periodic replay, event resets, passivity monitoring,
rollout modes, deterministic diagnostics, and fail-closed topology handling
[[12]](REFERENCES.md#ref-12). The completion audit records the original
requirement mapping [[34]](REFERENCES.md#ref-34).

The second completed phase generalized the controller. Explicit Euler, Heun,
RK23, backward Euler, trapezoidal, and BDF2 candidates were attached to the
same authority architecture. Embedded fast paths, dynamic reference promotion,
evidence-controlled adaptive replay refinement, and candidate-specific
amplification models were added [[14]](REFERENCES.md#ref-14). This phase
established that “bounded
Adams–Bashforth” could become a bounded multi-method design.

The third completed phase expanded evidence. Analytic support, raw AB2 research
controls, deterministic comparison outputs, fixed-step/fixed-accuracy/fixed-
work analyses, nonlinear refined replay, long-horizon cases, oscillator metrics,
and ngspice mappings were implemented [[15]](REFERENCES.md#ref-15)
[[16]](REFERENCES.md#ref-16). The test and comparison audit records the
qualification work packages [[18]](REFERENCES.md#ref-18).

The fourth completed phase optimized execution. It reduced repeated Jacobian,
projection, replay, nonlinear, and linear-algebra work; introduced optional
sparse execution; compiled topology and CSC stamps; reused workspaces; batched
sensitivities; added bounded KLU symbolic/numeric reuse, guarded chord and Schur
predictors; and retained only changes that survived end-to-end measurement and regression checks
[[17]](REFERENCES.md#ref-17).

The fifth completed infrastructure phase built release qualification. Canonical
metadata, deterministic wheel construction, exact source and environment
recording, source/installed equivalence, complete evidence manifests, checksum
verification, and pinned CI workflows are implemented
[[20]](REFERENCES.md#ref-20) [[33]](REFERENCES.md#ref-33). The scientific and
human release decision remains intentionally outside that infrastructure.

The immediate next phase should complete the governed `v1.1.0` release process.
One clean source commit must be frozen, the full dependency-free and SciPy/KLU
qualification tiers must run, the comparison and ngspice evidence must be
reviewed, two wheel builds must match, the installed wheel must reproduce source
reports, and a human approver must name the exact hashes before tagging or
publication [[19]](REFERENCES.md#ref-19) [[21]](REFERENCES.md#ref-21).

The next performance phase should prioritize compiled nonlinear device assembly
and cache observability. Direct profiling found the immutable tuple-to-NumPy KLU
copy substantially smaller than Python U-pivot scanning, sparse norm construction,
and nonlinear stamping; the first two are now vectorized and the native boundary
reuses stable pointers, accepts private generated scalar values, and returns a
reusable factorization from the combined first solve. A
broad NumPy diode batch is rejected at the current 32-channel crossover because
it is slower there and changes floating-operation ordering at larger sizes. The
next prototype should instead test a much larger evidence-gated nonlinear batch
while preserving live parameter mutation, limiting, deterministic nonfinite
behavior, and generic fallback.
Cache hit, miss, eviction, refactor, and fallback metrics should be added before
cache policy becomes configurable or automatic KLU adoption broadens.
The implemented ULP-aware two-step evidence window, compiled built-in breakpoint
schedules, bounded sparse-kernel source and hot-topology caches, duplicate built-
in switch-control sampling, and qualified KLU adapter provide the new baselines;
the corrected three-step extension remains rejected
[[17]](REFERENCES.md#ref-17).

Mixed C+L trapezoidal replay now has independently controlled subdivision
adaptivity: a three-derivative defect selects finer complete-window retries and
falls back to the former fixed refinement ceiling. The next numerical phase
should generalize method-specific replay evidence, preserve exact event
boundaries, and add a hard maximum elapsed authority age. Evidence-gated anchor
scheduling could then decide when refresh is needed without weakening the
independent replay authority.

The next modeling phase should add devices and events in a deliberately ordered
way. State-dependent switch root finding is a higher priority than indiscriminate
device count because event timing directly affects multistep validity. Controlled
sources, additional diode semantics, and selected transistor models could
follow, each with analytic, refined, or external authority cases. Higher-index
topologies should remain rejected until a mathematically explicit formulation
and qualification plan exists.

The longer-term theory phase should strengthen the relationship between the
recursive internal bound and observed independent anchor error. This may
include calibrated local Lipschitz estimates, componentwise or energy-weighted
norms, probabilistic coverage models, or rigorous enclosures for restricted
linear circuit classes. Any stronger claim must identify its assumptions and
must not generalize empirical coverage to arbitrary nonlinear physical error.

The final long-term direction is transfer to other DAE domains or lower-level
execution environments. Such work should begin only after the circuit version
has stable authority semantics, release evidence, and replay adaptivity. The
portable contribution is not the present device list; it is the disciplined
separation of candidate speed, constraint consistency, local correction,
independent refresh, diagnostics, and human-controlled claims.

The roadmap can therefore be summarized as a progression from bounded
experimentation to qualified infrastructure, then from qualified infrastructure
to broader numerical and modeling capability. Each phase has a fail-closed
gate: no new optimization without end-to-end gain, no new candidate without an
amplification and history model, no new device without authority cases, no
adaptive anchor policy without independent replay control, and no release claim
without exact artifact approval.
