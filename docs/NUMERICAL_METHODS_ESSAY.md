# Numerical Methods and Error Bounding in Bounded-Authority-Based-Circuit-Simulation

## Five Engineering Decisions BAB-CS Makes Reviewable

Choose a numerical method by asking what engineering decision its evidence must
support. Bounded-Authority-Based-Circuit-Simulation (`BAB-CS`) makes five
questions reviewable:

1. How can a fast method propose a circuit state without being allowed to approve
   its own answer?
2. How does the simulator keep voltages and currents consistent with the circuit
   equations after every timestep?
3. What happens when two methods disagree, a nonlinear solve fails, or a switch
   changes the circuit suddenly?
4. How can phase, stored energy, and error-bound coverage be inspected separately
   instead of being hidden inside one accuracy number?
5. Which claim is justified by the evidence, and which stronger claim remains
   unproved?

These questions matter in engineering projects where an attractive waveform is
not enough. The result must also show why the timestep was accepted, what
independent check challenged it, and what failure path remained available.

## Read BAB-CS as a Supervised Timestep

Bounded-Authority-Based-Circuit-Simulation (`BAB-CS`) separates **proposal** from
**authority**. A candidate numerical method proposes the next circuit state.
Independent equations, reference methods, and gates decide whether that proposal
is accepted, corrected, recomputed, or rejected. This design does not make every
candidate stable or accurate. It makes the candidate’s authority conditional and
observable [[12]](REFERENCES.md#ref-12) [[13]](REFERENCES.md#ref-13).

The word **bound** also has a specific meaning. BAB-CS maintains an internal
estimate of error relative to its implemented numerical authority model. That
estimate is useful for diagnostics and control, but it is not a proof that the
unknown exact physical trajectory lies inside a formal interval. Empirical
coverage is reported separately so readers can see where the implemented bound
does and does not cover independently measured authority error.

## Follow One Timestep from Proposal to Replay

Follow one attempted timestep from start to finish:

1. **A candidate proposes.** A selected numerical formula predicts the next
   capacitor voltages and inductor currents. At this point the values are only a
   proposal, not an accepted result.
2. **Projection restores circuit consistency.** The circuit equations are solved
   so node voltages and branch currents satisfy the declared electrical
   constraints. This prevents an internally inconsistent state from advancing.
3. **An independent reference challenges the proposal.** A different numerical
   method computes its own answer. The disagreement exposes error that the
   candidate cannot measure by comparing only with itself.
4. **The controller corrects or transfers authority.** If the candidate remains
   within the declared model, the controller can move its result toward the
   reference. If contraction cannot be established, the reference receives full
   authority.
5. **Hard gates make the final decision.** Failed projection, excessive equation
   mismatch, invalid history, nonfinite values, failed nonlinear convergence,
   or an energy-rule violation can reject the attempt or invoke a safer fallback.
6. **Replay checks accumulated behavior.** At declared intervals and events, an
   independent recomputation starts from a retained anchor and checks whether the
   accepted path has drifted.

Each control addresses a visible engineering failure: projection addresses
equation inconsistency, method comparison addresses unchecked local error,
contraction addresses error growth, hard gates address invalid states, and
replay addresses accumulated drift. Later sections explain the mathematics
behind each control.

## Circuit Equations and Projection

BAB-CS represents a circuit as a semiexplicit differential-algebraic equation
(`DAE`). A DAE combines differential equations, which describe change with time,
with algebraic equations, which must be satisfied immediately. Conceptually,

```text
z' = f(t, z, y)
0  = g(t, z, y)
```

Here `z` contains capacitor voltages and inductor currents, and `y` contains node
voltages and currents through voltage-defined branches. The prime in `z'` means
the time derivative. The equation `g(t, z, y) = 0` states the circuit constraints.

The equation system follows modified nodal analysis (`MNA`), a standard way to
convert a circuit into equations while retaining useful sparse structure
[[1]](REFERENCES.md#ref-1) [[25]](REFERENCES.md#ref-25). **Sparse** means that
most entries in the equation matrix are zero because each component connects to
only a small part of the circuit.

Given a proposed `z`, BAB-CS performs **projection** by solving
`g(t, z, y) = 0`. In a linear resistor, capacitor, and inductor network, this is
a linear solve. With a diode, it becomes a nonlinear iterative solve. Projection
prevents departure from the circuit-equation surface, but it does not prevent
error along that surface. A state can satisfy Kirchhoff’s laws and still have the
wrong phase, amplitude, or stored energy [[6]](REFERENCES.md#ref-6). Projection
therefore supports authority; it does not replace authority.

## Candidate Methods

BAB-CS supervises seven numerical candidates. A **candidate** is the formula
allowed to propose the next dynamic state.

### Explicit Euler

Explicit Euler uses the present derivative to take one forward step. It is
first-order, meaning its accumulated error normally decreases roughly in
proportion to the timestep. It is simple and useful as a control case, but it
can require very small steps on stiff problems.

### Heun

Heun’s method first makes an Euler proposal and then averages the starting and
ending slopes. It is second-order, so its accumulated error normally decreases
roughly with the square of the timestep. The difference between the Euler and
Heun results supplies an embedded error estimate, meaning two accuracy levels
are obtained from related work [[4]](REFERENCES.md#ref-4).

### Bogacki-Shampine RK23

Bogacki-Shampine order 2/3 (`RK23`) is a Runge-Kutta method. A Runge-Kutta method
samples several intermediate slopes within one timestep. RK23 produces related
second- and third-order results, allowing their difference to estimate local
error [[24]](REFERENCES.md#ref-24).

### Variable-Step AB2

Adams-Bashforth order two (`AB2`) is an explicit multistep method. **Multistep**
means it reuses information from an earlier accepted step. For current timestep
`h_n`, previous timestep `h_(n-1)`, current derivative `f_n`, and previous
derivative `f_(n-1)`, the proposal is

```text
r = h_n / h_(n-1)
z_ab = z_n + h_n [(1 + r/2) f_n - (r/2) f_(n-1)].
```

The ratio `r` changes the coefficients when the timestep changes. BAB-CS rejects
invalid history and excessive step-ratio changes. Startup, rejection, accepted
events, and replay resets transfer authority to an implicit method until safe
multistep history has been rebuilt [[5]](REFERENCES.md#ref-5)
[[23]](REFERENCES.md#ref-23).

### Backward Euler, Trapezoidal, and BDF2

Backward Euler, trapezoidal integration, and backward differentiation formula
order two (`BDF2`) are implicit methods. **Implicit** means that the new state
appears inside the equation being solved. Backward Euler is first-order and
strongly damping. Trapezoidal integration is second-order and often preserves
oscillatory amplitude better. BDF2 is a second-order multistep method and uses
backward Euler when valid history is unavailable [[26]](REFERENCES.md#ref-26).

These methods may serve as candidates or references. An implicit candidate is
paired with a different reference method. Comparing a method with itself would
produce a misleading zero difference rather than independent evidence.

## Amplification, Correction, and Accepted Authority

The controller estimates a conservative candidate amplification `G_c`.
**Amplification** describes how existing error may grow through one numerical
step. The estimate uses the timestep and a norm of the differential Jacobian.
A **Jacobian** is a matrix of local sensitivities: it records how each derivative
changes when each state variable changes. The infinity norm used here is the
largest absolute row sum.

For explicit methods, BAB-CS evaluates a stability-polynomial model at
`h ||J||`, where `h` is the timestep and `J` is the Jacobian. AB2 also includes
the previous Jacobian norm and the step ratio. Implicit amplification estimates
are used only where their denominator models remain valid
[[14]](REFERENCES.md#ref-14). These are conservative runtime models, not exact
spectral decompositions of the circuit transition.

When a candidate state `z_c` and independent reference state `z_r` are
available, the corrected proposal is

```text
z_* = (1 - gamma) z_c + gamma z_r.
```

The correction gain `gamma` determines how far the state moves toward the
reference. BAB-CS chooses it so the modeled corrected propagation
`q = (1 - gamma) G_c` meets the configured contraction target. **Contraction**
means that the model expects inherited error to decrease. If the controller
cannot establish `q < 1`, the reference receives full authority. The corrected
state is projected again before acceptance [[13]](REFERENCES.md#ref-13).

## Recursive Internal Bound

The recursive bound carries modeled uncertainty from one accepted state to the
next. In simplified form,

```text
B_next = q B + delta.
```

`B` is the previous bound, `q` is corrected propagation, and `delta` is the new
local contribution. The contribution can include candidate/reference
disagreement, an embedded lower-order difference, normalized algebraic residual,
and floating-point allowance. A **residual** is the mismatch left when the
circuit equations are evaluated at the computed solution. **Floating-point**
numbers are the finite-precision values used by the computer.

The controller also uses a scaled norm so large and small state components can
be compared against absolute and relative tolerances. A finite bound does not
override hard gates. Nonfinite values, failed projection, excessive residual,
failed nonlinear convergence, invalid history, passivity violations, and replay
failure can all reject a step or transfer authority to a safer method
[[15]](REFERENCES.md#ref-15).

**Passivity** means that a passive circuit model may not create net energy from
nothing. A passivity violation indicates that the numerical result conflicts
with that declared physical property beyond its allowed tolerance.

## Nonlinear Solves

Diodes make the algebraic equations nonlinear. BAB-CS uses Newton iteration,
which repeatedly linearizes the equations around a current guess and solves for
an update. A line search reduces the update when the full Newton step does not
improve the residual. **Convergence** means that the iteration reaches the
declared residual and update tolerances before its iteration limit.

Nonlinear convergence is evidence, not a cosmetic status flag. If the solve
does not converge, the state cannot be accepted merely because the waveform
looks smooth. Candidate and reference solves record iteration counts, residuals,
fallbacks, and rejection causes so an engineer can distinguish physical
clipping from numerical failure [[18]](REFERENCES.md#ref-18).

## Events, Anchors, and Replay

A commanded source or switch breakpoint is an **event**: a declared time at
which the model changes formula or value. BAB-CS shortens the current step so it
lands exactly on the event. Exact event alignment prevents a multistep method
from averaging unknowingly across a discontinuity. After an accepted event,
multistep history is invalidated.

An **anchor** is a retained accepted state used as the start of an independent
check. **Replay** recomputes the interval from that anchor with an implicit
method and smaller internal steps. Replay serves three purposes:

- it challenges accumulated candidate behavior independently;
- it measures anchor deviation, the distance between the accepted path and the
  replayed path; and
- it refreshes authority before the candidate continues.

Current event handling forces independent replay before event-driven history is
cleared. This prevents an event reset from accidentally removing the very
independent check needed at a discontinuity [[28]](REFERENCES.md#ref-28).

## Phase, Energy, and Coverage

One error number cannot explain every engineering failure. BAB-CS therefore
reports several dimensions separately:

- **state error** measures voltage and current disagreement;
- **phase error** measures the timing shift of an oscillation;
- **energy error** measures numerical change in capacitor and inductor energy;
- **anchor deviation** measures disagreement with independent replay;
- **authority age** measures elapsed time since the last independent refresh;
  and
- **empirical coverage** measures how often the recursive bound covers observed
  authority error on eligible samples.

This separation is especially important for an inductor-capacitor (`LC`)
oscillator. A method can preserve total energy while accumulating phase error,
or damp energy while keeping short-term zero crossings close. The correct metric
depends on the engineering decision.

## Where the Numerical Claim Stops

BAB-CS supports a bounded multi-method control claim: candidate authority is
limited by projection, independent reference calculations, correction, hard
gates, and replay. It does not support a claim that raw AB2 has become A-stable,
which would mean stable for every stable linear problem at every timestep,
that the recursive bound encloses exact physical truth, or that one candidate is
best for every circuit.

The Method Observatory and Bound Coverage Atlas are therefore essential. They
show fixed-step, fixed-accuracy, and fixed-work behavior across resistor-
capacitor, resistor-inductor, resistor-inductor-capacitor, inductor-capacitor,
diode, and switched cases. Negative results, weak coverage, fallback causes, and
rejections remain part of the evidence rather than being removed from the
story.
