# Bounded-Authority-Based-Circuit-Simulation: Current Work

## Why This Work Matters

Bounded-Authority-Based-Circuit-Simulation (`BAB-CS`) is a transient circuit
simulator designed for engineering studies in which the numerical decision must
remain inspectable after the waveform has been produced. A transient simulation
calculates how voltages and currents change with time. In an ordinary workflow,
one numerical method often proposes the next state and effectively approves its
own answer. BAB-CS separates those roles: a **candidate method** proposes the
next state, while independent calculations decide whether that proposal may
become the accepted result.

This separation matters because a waveform can look plausible while hiding a
numerical failure. A switching event may be crossed at the wrong time. A
nonlinear device solve may stop before its equations are consistent. A resonant
waveform may gradually shift in time, which is called **phase drift**. Stored
electrical energy may grow or decay because of the numerical method rather than
the circuit. A packaged release may also produce different evidence from the
source tree used to qualify it. BAB-CS makes these risks visible through
event-aligned steps, convergence checks, separate phase and energy reports,
independent replay, deterministic work counts, and source-versus-package
comparison.

The project began with Adams-Bashforth order two (`AB2`), an explicit two-step
integration formula that uses present and previous derivative information to
predict the next state. **Explicit** means that the formula directly computes a
proposal from known information. AB2 is economical, but it has a limited
stability region and is not A-stable, meaning it cannot remain stable for every
stable linear problem at every timestep [[3]](REFERENCES.md#ref-3). BAB-CS does
not claim to change that mathematics. It limits how much authority AB2 receives
by checking, correcting, replacing, or independently rebuilding its proposed
trajectory [[12]](REFERENCES.md#ref-12) [[23]](REFERENCES.md#ref-23).

## The Circuit Model in Plain Words

BAB-CS follows **modified nodal analysis** (`MNA`), a standard method for turning
a circuit diagram into equations for node voltages and selected branch currents
[[1]](REFERENCES.md#ref-1). MNA is part of the historical foundation of SPICE,
whose name means *Simulation Program with Integrated Circuit Emphasis*, a widely
used family of circuit simulators [[2]](REFERENCES.md#ref-2).

The simulator separates two kinds of unknowns:

- **Differential state** contains quantities that store memory: capacitor
  voltages and inductor currents.
- **Algebraic state** contains quantities that must satisfy the circuit
  equations immediately: node voltages and currents through voltage-defined
  branches.

This combination is a **differential-algebraic equation** (`DAE`): part of the
model evolves through derivatives, while another part must satisfy simultaneous
constraints. BAB-CS performs **projection**, which means solving the circuit
constraints for every proposed state before that state can be accepted. A
projection can restore Kirchhoff current and voltage consistency, but it cannot
by itself prove that the trajectory is accurate. The simulator therefore keeps
projection, local error evidence, independent authority, energy checks, and
periodic replay as separate controls [[6]](REFERENCES.md#ref-6)
[[25]](REFERENCES.md#ref-25).

The current device set is intentionally bounded. It includes resistors,
capacitors, inductors, independent voltage and current sources, idealized
Shockley diodes, and time-controlled resistive switches. A Shockley diode is a
simple exponential diode model used to study nonlinear circuit behavior.
Sources and controls can be constant, sinusoidal, pulsed, or piecewise linear.
Unsupported floating, singular, conflicting, or mathematically higher-index
topologies—systems whose constraints require extra differentiation before a
standard time step can be computed—fail explicitly rather than being changed through hidden
conductances or hidden energy storage [[11]](REFERENCES.md#ref-11).

## The Authority Loop

BAB-CS currently supervises seven candidate methods:

1. explicit Euler, a first-order one-step proposal;
2. Heun, a second-order predictor-corrector proposal;
3. Bogacki-Shampine order 2/3 (`RK23`), a Runge-Kutta method with paired
   second- and third-order estimates;
4. variable-step AB2;
5. backward Euler, a first-order implicit method;
6. trapezoidal integration, a second-order implicit method; and
7. backward differentiation formula order two (`BDF2`), a second-order
   implicit multistep method [[4]](REFERENCES.md#ref-4)
   [[14]](REFERENCES.md#ref-14).

An **implicit method** solves an equation containing the new unknown state. It
usually costs more per step than a simple explicit proposal, but it is valuable
as an independent reference when the problem is stiff. **Stiffness** means that
a model contains fast and slow behavior together, forcing some methods to use
very small timesteps for stability rather than for visible waveform detail.

For an ordinary active step, BAB-CS performs this sequence:

1. The candidate method proposes the next capacitor voltages and inductor
   currents.
2. Projection solves the circuit equations associated with that proposal.
3. A different implicit method computes an independent reference state.
4. The controller estimates how errors may amplify through the candidate.
5. The candidate is blended toward the reference when correction can make the
   modeled propagation contractive. **Contractive** means that the model expects
   earlier error to shrink rather than grow.
6. A second projection restores circuit consistency after correction.
7. Residual, convergence, finiteness, passivity, and error gates decide whether
   to accept, retry with a smaller step, or give full authority to the reference.

**Passivity** means that a passive declared model may not create net energy from
nothing. A passivity gate checks that numerical behavior does not contradict
that property beyond the configured allowance.

The accepted state therefore belongs to the controller, not to the candidate.
An implicit candidate is paired with a different implicit reference so that a
zero difference cannot be manufactured by comparing a method with itself
[[13]](REFERENCES.md#ref-13) [[23]](REFERENCES.md#ref-23).

## Bounds, Anchors, and Replay

The controller carries a **recursive internal bound**, a running estimate of
how previously modeled error and the newest local defect may combine. A
**defect** is the measured disagreement between a proposal and an independent
or lower-order calculation. In simplified form, the update is
`B_next = q B + delta`, where `B` is the previous bound, `q` is the modeled
propagation factor after correction, and `delta` is the new local contribution.
The production implementation also includes normalized circuit-equation
residuals and roundoff protection [[13]](REFERENCES.md#ref-13)
[[15]](REFERENCES.md#ref-15).

This bound is intentionally limited. It applies to the implemented numerical
error model relative to declared internal authority. It is not a mathematical
interval guaranteed to contain the unknown exact physical trajectory. The
Bound Coverage Atlas reports how often the recursive bound covers independently
measured authority error so that weak coverage is visible rather than hidden.

An **anchor** is a previously accepted state from which BAB-CS can independently
recompute a recent interval. That recomputation is called **replay**. Replay uses
an implicit method and controlled subdivisions, meaning smaller internal steps,
to challenge the accumulated candidate path. It measures anchor deviation,
refreshes authority, and can expose errors that a local candidate/reference
comparison did not reveal. Scheduled source and switch breakpoints are reached
exactly, and each accepted event forces independent replay before multistep
history is cleared [[5]](REFERENCES.md#ref-5)
[[28]](REFERENCES.md#ref-28).

## Engineering Evidence Surfaces

Four connected facilities make the current behavior reviewable.

### Method Observatory

The BAB-CS Method Observatory runs resistor-capacitor (`RC`),
resistor-inductor (`RL`), resistor-inductor-capacitor (`RLC`),
inductor-capacitor (`LC`), diode-clip, and switched-RC cases across all seven
candidate profiles. It produces:

- **fixed-step reports**, where methods receive the same nominal timestep;
- **fixed-accuracy reports**, where rows are selected against a declared error
  target; and
- **fixed-work reports**, where methods are compared under a deterministic
  operation budget rather than variable wall-clock time.

The observatory does not declare one universal winner. It preserves the exact
configuration and measured row used for each engineering conclusion.

### Bound Coverage Atlas

The Bound Coverage Atlas aligns actual authority error, recursive internal
bound, anchor deviation, phase, energy, empirical coverage ratio, and the causes
of fallback or rejection. **Empirical coverage ratio** means the measured
fraction of eligible samples for which the internal bound was at least as large
as the independently observed authority error. It is characterization of the
declared cases, not a formal proof for arbitrary circuits.

### Power-Stage Sandbox

The Power-Stage Sandbox provides a simplified buck-like converter, a scheduled
H-bridge with an RL load, and a direct-current-link RLC startup and interruption
case. An H-bridge is a four-switch arrangement that can apply positive or
negative voltage to a load. These are **reduced-order numerical experiments,
not production device models**. A reduced-order model is a deliberate
simplification that retains only the behavior required for the numerical
question. Semiconductor switching loss, magnetic saturation, electromagnetic
interference, detailed thermal behavior, protection hardware, and safety signoff
remain outside these examples.

### Teaching and Reproducibility Lab

The Teaching and Reproducibility Lab contains ten compact exercises covering
modified nodal analysis (`MNA`), measured convergence, phase versus energy,
shadow authority, deterministic packaging, source-versus-wheel equivalence,
exact event alignment, empirical bound coverage, fallback and rejection
forensics, and semantic mapping to ngspice. **Shadow authority** means that a
candidate runs and records evidence while a trusted reference still owns the
accepted state. A Python **wheel** is an installable package file. Source-versus-
wheel equivalence checks that the source checkout and the isolated installed
package produce the same declared numerical evidence. **Event alignment** means
ending a numerical step exactly where a scheduled circuit change occurs.
**Empirical coverage** means the measured fraction of eligible samples for
which the recorded internal bound was at least as large as the independently
measured authority error; it is observed evidence, not a formal proof.
**Semantic mapping** means translating the meaning and state order of a BAB-CS
case into another simulator rather than merely copying similarly named fields.

## Engineering Projects Suited to BAB-CS

The current system is especially useful for the following bounded projects:

- screening a commanded buck-converter switching schedule before detailed
  semiconductor and thermal modeling;
- checking H-bridge dead time, polarity reversal, current continuity, and event
  handling in a simplified RL load;
- studying direct-current-link inrush, stored energy, interruption, and decay;
- comparing diode-clamp convergence, residuals, fallback, and timestep
  sensitivity;
- separating phase drift from energy drift in LC or lightly damped RLC systems;
- selecting a candidate method under fixed-step, fixed-accuracy, or fixed-work
  constraints;
- qualifying whether a solver backend or packaging change altered numerical
  evidence; and
- teaching circuit equations and reproducible numerical claims in an executable
  laboratory.

BAB-CS complements rather than replaces specialist simulation software.
ngspice supplies an independent SPICE implementation for mapped comparison
cases. LTspice is better suited to interactive schematic work and vendor device
models. PLECS is designed for broad power-electronics systems and real-time
controller workflows. Simscape Electrical supports larger multidomain plants,
where electrical behavior interacts with mechanical, thermal, or control
systems. Xyce targets very large SPICE-compatible circuit simulation, including
parallel execution. BAB-CS adds value when the engineering question depends on
why a numerical step passed, changed authority, replayed, or failed.

## Current Limits and Next Work

The strongest current result is architectural: multiple proposal methods share
one explicit authority system, independent replay path, failure taxonomy, and
deterministic evidence surface. The strongest limits are also explicit. The
device library is small, general state-triggered event location is not yet
implemented, higher-index DAEs fail closed, the recursive bound is not a formal
physical enclosure, and performance measurements apply only to named workloads.

Sparse execution is available through SciPy and an optional SuiteSparse KLU
adapter. SciPy is a Python scientific-computing library. KLU is a sparse linear
solver specialized for circuit-like matrices. The highest-value performance
work remains measured rather than speculative: preserve resident solver data,
move residual ownership closer to native factorization, improve cache
observability, and retain an optimization only when complete simulations gain
without weakening authority [[7]](REFERENCES.md#ref-7)
[[17]](REFERENCES.md#ref-17) [[35]](REFERENCES.md#ref-35).

Release automation builds and checks evidence, but it cannot approve a release.
The proposed `1.1.0` release still requires one clean source commit, complete
qualification on that exact commit, hashes that identify the source and built
artifacts, and explicit human approval [[19]](REFERENCES.md#ref-19)
[[21]](REFERENCES.md#ref-21). In BAB-CS, a passing script is evidence; it is not
scientific, engineering, or publication authority by itself.
