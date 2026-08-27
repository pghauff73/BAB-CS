# Engineering Applications and Research Roadmap for BAB-CS

## Plain-Language Scope

Bounded-Authority-Based-Circuit-Simulation (`BAB-CS`) is best used when an
engineering team needs to understand not only *what waveform appeared*, but also
*why each numerical step was trusted*. A candidate method proposes the next
capacitor voltages and inductor currents. Independent circuit solves, reference
methods, correction, gates, and replay decide whether that proposal becomes the
accepted state.

The current simulator is deliberately a **reduced-order** environment. A
reduced-order model is a simplified model that retains the behavior needed for a
specific question while leaving out detail that does not belong to that study.
This makes BAB-CS useful for numerical qualification, early engineering
screening, and reproducible research. It does not make the present examples
production semiconductor, magnetic, thermal, electromagnetic, protection, or
safety models [[11]](REFERENCES.md#ref-11)
[[25]](REFERENCES.md#ref-25).

## Engineering Projects Suited to BAB-CS

### 1. Buck-Converter Schedule Screening

A buck converter reduces a direct-current voltage by switching energy through
an inductor and capacitor. BAB-CS can study a simplified scheduled converter to
check event alignment, inductor-current continuity, output ripple, diode
conduction, stored energy, fallback, and replay. The useful result is not only a
voltage trace; it is a record of which candidate method proposed each state and
which independent authority accepted it.

Use this project before detailed semiconductor loss, magnetic saturation,
electromagnetic-interference, and thermal studies. The sandbox example is a
**reduced-order numerical experiment, not a production device model**.

### 2. H-Bridge Dead Time and Load Reversal

An H-bridge is a four-switch arrangement that can apply positive or negative
voltage to a load. **Dead time** is a short interval in which opposing switches
are both off to avoid a direct supply short. The scheduled H-bridge experiment
uses a resistor-inductor (`RL`) load and can expose polarity changes, current
continuity, exact event arrival, history resets, rejected steps, and replay work.

This is suitable for testing numerical handling of a declared switching
schedule. It does not model body diodes, gate-driver timing uncertainty,
shoot-through, motor mechanics, device parasitics, or hardware faults.

### 3. Direct-Current-Link Startup and Interruption

A direct-current link, often called a DC link, is the energy-storage path between
parts of a power system. The BAB-CS example uses a simplified resistor-inductor-
capacitor (`RLC`) circuit with a declared path for continuing current after an
interruption. It supports studies of startup inrush, stored energy, interruption
timing, decay, phase, and candidate robustness.

Use it to qualify the numerical experiment and the commanded event schedule.
Do not use it as a contactor, battery, fuse, insulation, arc, fault-current, or
hardware-safety model.

### 4. Diode-Clamped Interface Transient

A diode clamp limits a voltage by conducting strongly after the voltage crosses
its operating region. The idealized Shockley diode in BAB-CS supplies a compact
nonlinear case. **Nonlinear** means that output is not proportional to input and
the circuit equations require iteration.

This project can compare candidate methods, Newton convergence, residuals,
timestep refinement, safer-method fallback, and mapped ngspice results. A
**residual** is the remaining mismatch in the circuit equations. Production work
requiring manufacturer models, package parasitics, temperature corners, or
electrostatic-discharge signoff belongs in a specialist SPICE workflow. SPICE
means *Simulation Program with Integrated Circuit Emphasis*.

### 5. Resonant Phase and Energy Retention

An inductor-capacitor (`LC`) circuit exchanges energy between a magnetic field
and an electric field. It is useful for separating **phase drift**, the numerical
shift in oscillation timing, from **energy drift**, numerical gain or loss of
stored energy not caused by the declared model.

BAB-CS reports phase, energy, state error, recursive bound, anchor deviation,
and time since independent authority refresh separately. This makes it suitable
for long-horizon studies where one combined error norm would hide the reason a
trajectory is unacceptable.

### 6. Numerical-Method Selection

The Method Observatory runs all seven candidate methods under the same authority
controller. A team can compare:

- fixed-step behavior, where every method receives the same nominal timestep;
- fixed-accuracy behavior, where rows are selected against a declared target;
  and
- fixed-work behavior, where rows are compared under a deterministic operation
  budget.

This supports selecting a method for a simplified simulation component or early
digital-twin prototype. A **digital twin** is software intended to represent and
possibly track a physical system. A successful reduced-order method study does
not by itself validate an operational digital twin.

### 7. Solver and Packaging Regression Qualification

A **regression** is an unintended change in behavior after source, dependency,
solver, or packaging work. BAB-CS can determine whether a change altered
trajectories, residuals, fallback causes, work counts, deterministic reports, or
accepted authority.

The release tooling compares the source checkout with an isolated installation
of the built Python wheel. A **wheel** is an installable Python package file.
Source-versus-wheel equivalence checks that the packaged implementation
reproduces the declared source evidence rather than merely importing
successfully [[20]](REFERENCES.md#ref-20)
[[31]](REFERENCES.md#ref-31).

### 8. Teaching and Reproducibility

The Teaching and Reproducibility Lab connects modified nodal analysis (`MNA`),
a standard way to turn circuits into equations, with measured convergence,
phase versus energy, shadow authority, deterministic packaging, and isolated
wheel checks. **Convergence** describes how error decreases when the timestep is
refined. **Shadow authority** means a candidate runs and records evidence while
a trusted reference still owns the accepted state.

The lab is suitable for numerical methods, circuit simulation, software
qualification, and reproducible research courses. It is not a substitute for
production device-design or safety-validation training.

## Choosing BAB-CS or Another Simulator

The tools below overlap, but their strongest roles differ. This is a workflow
map, not a product ranking.

| Environment | Strongest role | Relationship to BAB-CS | Prefer it when |
|---|---|---|---|
| BAB-CS | Inspectable proposal, independent authority, replay, failure causes, deterministic work, and reproducible reduced-order experiments | Primary environment for bounded numerical-method studies | The decision depends on why a timestep passed, changed authority, replayed, or failed |
| ngspice | Open-source SPICE simulation with device, behavioral, scripting, and mixed-signal capabilities | Current independent comparison implementation for 20 manifest-owned BAB-CS cases | Broader device and analysis coverage or a cross-implementation challenge is needed |
| LTspice | Interactive schematic capture, SPICE simulation, waveform viewing, and vendor models | Complementary device-design and schematic environment | Engineers need vendor macromodels, rapid schematic exploration, and production-oriented analog investigation |
| PLECS | Complete power-electronics systems, controls, thermal behavior, code generation, and hardware-in-the-loop work | Natural handoff after a bounded simplified converter study | The project needs system-level converter design, controller deployment, or real-time testing |
| Simscape Electrical | Electrical systems connected to mechanical, thermal, hydraulic, control, motor, and grid models | Broader multidomain environment | Electrical behavior must interact with other physical domains or a larger virtual plant |
| Xyce | SPICE-compatible simulation of extremely large circuits on serial and parallel computers | Complementary scale-oriented environment | Circuit scale and parallel execution exceed the intended BAB-CS qualification surface |

**Hardware-in-the-loop** means testing real controller hardware against a
simulated plant. **Multidomain** means that several kinds of physics, such as
electrical and mechanical behavior, are solved together. BAB-CS should hand off
to these environments when required model fidelity, deployment, or scale grows
beyond its declared boundary.

## Current Research Facilities

### Method Observatory

The observatory covers resistor-capacitor (`RC`), RL, RLC, LC, diode-clip, and
switched-RC cases across explicit Euler, Heun, Bogacki-Shampine order 2/3
(`RK23`), Adams-Bashforth order two (`AB2`), backward Euler, trapezoidal
integration, and backward differentiation formula order two (`BDF2`). RK23 is a
Runge-Kutta method with paired second- and third-order estimates. AB2 is an
explicit two-step predictor. BDF2 is an implicit two-step method.

### Bound Coverage Atlas

The atlas reports actual authority error, recursive internal bound, authority-
epoch drift, anchor deviation, phase, energy, empirical coverage, fallback, and
rejection causes. An **authority epoch** is the interval since the current
independent authority basis was established. **Empirical coverage** is the
measured fraction of eligible samples for which the internal bound covered the
observed authority error. It is not a formal enclosure theorem.

### Power-Stage Sandbox

The sandbox contains the three bounded examples described above: buck-like,
scheduled H-bridge RL, and DC-link RLC. Their classification is fixed:
**reduced-order numerical experiments, not production device models**.

### Teaching and Reproducibility Lab

The ten exercises cover MNA, fixed-step convergence, phase versus energy,
shadow authority, deterministic wheel packaging, isolated source-versus-wheel
equivalence, event alignment, empirical bound coverage, fallback forensics, and
semantic mapping of 20 ngspice cases. Each exercise includes conservative
interpretation prompts so students distinguish evidence from a claim.

## Near-Term Roadmap

### Release One Exact Candidate

The immediate release objective is to qualify version `1.1.0` from one clean,
frozen source commit. The complete dependency-free and optional SciPy/KLU tiers
must run on that commit. Numerical reports, ngspice comparisons, two wheel
builds, installed-wheel results, manifests, and checksums must be reviewed. A
human approver must name the exact source and artifact hashes before tagging or
publication [[19]](REFERENCES.md#ref-19)
[[21]](REFERENCES.md#ref-21).

### Strengthen Event Authority

The next modeling priority is state-triggered event location. A state-triggered
event occurs when a simulated quantity crosses a condition, rather than at a
time known in advance. Root finding would locate that crossing accurately.
This work is more important than indiscriminate device count because event timing
directly affects multistep history and accepted authority.

### Improve Replay Evidence

Replay subdivision is already method-specific for selected capacitor-and-
inductor and switched BDF2 cases. The next step is to preserve independent event
refresh, enforce a maximum elapsed authority age, and generalize evidence without
letting an adaptive schedule silently omit replay.

### Advance Measured Performance

The next performance studies should focus on resident KLU numeric buffers,
native residual calculation, and cache observability. KLU is a sparse matrix
solver specialized for circuit-like systems. Cache observability means reporting
hits, misses, refactors, evictions, and fallbacks so a cache policy can be judged
rather than assumed [[17]](REFERENCES.md#ref-17)
[[35]](REFERENCES.md#ref-35).

## Medium-Term Roadmap

Device expansion should be ordered by evidence needs. Controlled sources,
additional diode behavior, and selected transistor models can follow after
state-triggered event handling. Every new device should arrive with analytic,
refined-authority, or external comparison cases. Unsupported higher-index
differential-algebraic equations should continue to fail closed until a clear
formulation and qualification plan exists.

The Bound Coverage Atlas should be used to investigate why the recursive bound
covers some cases and misses others. Possible research includes local Lipschitz
estimates, which bound how strongly derivatives change; componentwise bounds,
which treat state variables separately; energy-weighted norms; probabilistic
coverage models; and rigorous enclosures for restricted linear circuit classes.
Any stronger claim must state its assumptions and may not generalize measured
coverage to arbitrary nonlinear physical error.

## Long-Term Roadmap

Once circuit authority semantics, event behavior, and release evidence are
stable, the architecture may transfer to other differential-algebraic domains.
The portable contribution is not the present device list. It is the separation
of fast proposal, constraint consistency, independent correction, replay,
diagnostics, deterministic artifacts, and human-controlled claims.

Future work should preserve the same fail-closed gates:

- no new candidate without an amplification and history model;
- no new device without authority cases;
- no adaptive anchor policy without independent replay control;
- no optimization without end-to-end gain and numerical equivalence; and
- no release claim without exact artifact review and human approval.

This roadmap keeps BAB-CS focused on its critical engineering value: making the
reason for numerical trust as reviewable as the waveform itself.
