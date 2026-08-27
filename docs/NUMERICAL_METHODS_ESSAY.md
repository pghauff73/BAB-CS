# Numerical Methods and Error Bounding in Bounded-Authority-Based-Circuit-Simulation

## Constrained Circuit State

The central numerical idea of BAB-CS is that bounded behavior should be created
by a hierarchy of independent controls rather than inferred from one favorable
local error estimate. A candidate integrator advances the differential state,
algebraic projection restores circuit consistency, an implicit method provides
reference authority, a correction limits modeled propagation, hard gates reject
unsafe transitions, and periodic replay independently reconstructs the recent
trajectory [[12]](REFERENCES.md#ref-12) [[13]](REFERENCES.md#ref-13). Each layer
addresses a different failure mode, so none is allowed to stand in for all the
others.

The semiexplicit state is written conceptually as

```text
z' = f(t, z, y)
0  = g(t, z, y),
```

where `z` contains capacitor voltages followed by inductor currents, and `y`
contains algebraic node voltages and voltage-defined branch currents. Given a
candidate `z`, the circuit solves `g(t, z, y) = 0` before evaluating `f`. This is
a modified-nodal construction specialized around physically meaningful dynamic
coordinates [[1]](REFERENCES.md#ref-1) [[25]](REFERENCES.md#ref-25). The
projection is a nonlinear solve for diode circuits and a linear solve for purely
linear circuits.

Projection prevents one kind of drift: departure from the algebraic manifold.
It does not by itself prevent error that lies along the manifold. Projection
methods for constrained systems similarly distinguish constraint satisfaction
from accumulated trajectory accuracy [[6]](REFERENCES.md#ref-6). BAB-CS therefore
uses projection after prediction and correction, but still requires reference,
bound, energy, and replay evidence.

## Candidate Methods

For valid history, variable-step AB2 proposes

```text
r = h_n / h_(n-1)
z_ab = z_n + h_n [(1 + r/2) f_n - (r/2) f_(n-1)].
```

The implementation rejects nonpositive steps, invalid dimensions, and history
whose step ratio exceeds configured bounds. After startup, rejection, events,
or a replay reset, implicit integration rebuilds authority before AB history is
trusted again [[5]](REFERENCES.md#ref-5) [[23]](REFERENCES.md#ref-23). This is
important because changing a multistep timestep alters more than the simple
constant-step truncation-error scaling.

Explicit Euler supplies a first-order one-stage control candidate. Heun uses an
Euler stage and a second projected endpoint, with their difference serving as
an embedded estimate. Bogacki–Shampine RK23 uses a third-order endpoint and a
second-order companion state derived from its stages
[[4]](REFERENCES.md#ref-4) [[24]](REFERENCES.md#ref-24). These methods make the
controller’s generality testable: the same authority rules must work when the
candidate has no history, one-step embedded history, or multistep history.

Backward Euler, trapezoidal, and variable-step BDF2 are available both as
candidate methods and as implicit references [[26]](REFERENCES.md#ref-26). An
active implicit candidate must be paired with a different reference method.
Otherwise, a zero candidate/reference difference would say only that the same
calculation was repeated, not that an independent defect estimate had been
obtained. BDF2 falls back to backward Euler when its history is unavailable.

Classical stability theory explains why the implicit methods remain essential.
Backward Euler and trapezoidal behavior is suitable for stiff authority roles,
whereas explicit Adams–Bashforth retains a bounded stability region
[[3]](REFERENCES.md#ref-3). BAB-CS does not override that fact. Its stiffness
indicator and amplification-domain checks transfer authority to an implicit
reference when the candidate’s local model is not credible.

## Correction and Recursive Bounds

For each candidate, BAB-CS estimates a conservative amplification `G_c`. For
explicit methods this estimate applies the method’s stability polynomial to
`h ||J||` using the infinity norm of the differential Jacobian. AB2 also uses
the previous Jacobian norm and variable-step coefficients. Implicit estimates
are accepted only where the corresponding denominator model remains valid
[[14]](REFERENCES.md#ref-14) [[24]](REFERENCES.md#ref-24). The estimate is a
runtime upper model, not a spectral decomposition of the exact transition.

When an implicit reference is present, the corrected differential proposal is

```text
z_* = (1 - gamma) z_c + gamma z_r,
```

where `z_c` is the candidate and `z_r` is the reference. The controller chooses
`gamma` within configured limits so that

```text
q = (1 - gamma) G_c
```

meets the target contraction. If it cannot establish `q < 1`, the reference is
accepted with full authority. The blended state is then projected again
[[13]](REFERENCES.md#ref-13) [[23]](REFERENCES.md#ref-23).

The fixed contraction target is easy to interpret but can impose a nonvanishing
blend on a high-order method as `h` decreases. BAB-CS therefore also supports a
rate form, `q_target = exp(-mu h)`. For smooth problems this allows the required
correction gain to shrink with the timestep, reducing the risk that a fixed
blend masks the observed order of a higher-order candidate
[[14]](REFERENCES.md#ref-14).

The per-step recursive model is

```text
B_(n+1) = q_n B_n + delta_n,
```

where `delta_n` includes corrected/reference deviation and normalized algebraic
or full-residual defect. Under uniform bounds `q_n <= q_max < 1` and
`delta_n <= delta_max`, iteration gives

```text
B_n <= q_max^n B_0 + delta_max (1 - q_max^n) / (1 - q_max).
```

The asymptotic envelope is therefore at most `delta_max / (1 - q_max)` within
the model [[13]](REFERENCES.md#ref-13). This is the mathematical reason a
contractive corrected recurrence does not exhibit indefinite modeled drift.

That conclusion has a strict claim boundary. `B_n` is expressed in the
project’s weighted norm and is driven by implemented defect and residual
estimates. It is not an interval enclosure of the unknown physical solution,
and it can be optimistic if the amplification or local-defect model omits
important dynamics. BAB-CS reports `certified_contractive` only for its local
recurrence conditions; it does not use that label to claim a global theorem
about the physical circuit [[13]](REFERENCES.md#ref-13)
[[15]](REFERENCES.md#ref-15).

The embedded fast path changes the model because no same-step implicit
reference is available on a deferred step. For an embedded candidate, the
controller records

```text
B_(n+1) = G_c B_n + E_embedded + residual_ratio.
```

This step is not called contractive when `G_c >= 1`. Instead, bounded operation
depends on a finite interval to the next reference checkpoint and on a hard
cap. If the projected bound would cross that cap, reference authority is
promoted immediately and the propagation term resets
[[14]](REFERENCES.md#ref-14).

Scheduled reference intervals and dynamic checkpoints serve different
purposes. The schedule ensures regular comparison even in smooth regions. The
dynamic checkpoint reacts to unexpectedly rapid modeled growth. Stiffness,
invalid amplification domains, shadow mode, and nonfinite quantities can also
force reference authority before the scheduled interval. This makes the fast
path opportunistic rather than permissive.

## Independent Replay and Physical Gates

Periodic replay is independent of the same-step reference schedule. At an
anchor, the solver starts from the previous trusted checkpoint and covers the
entire accepted interval using smaller implicit steps. The endpoint deviation

```text
eta_anchor = ||z_provisional - z_replay||_W
```

is retained as evidence, and the replay endpoint becomes authoritative even
when the deviation is below the safety threshold
[[13]](REFERENCES.md#ref-13) [[26]](REFERENCES.md#ref-26). A large deviation is
classified as a safety re-anchor rather than ignored.

Replay refinement is topology-aware. Circuits containing both capacitors and
inductors retain the full configured refinement because long-time phase error
is a central risk. Other built-in topologies may use a smaller minimum
refinement, while backward-Euler reference replay retains the full value because
of its lower order [[14]](REFERENCES.md#ref-14). This is a cost policy, not a
removal of replay coverage.

AB3 extrapolation during replay is used only to initialize Newton’s method:

```text
z_guess = z_n + h (23 f_n - 16 f_(n-1) + 5 f_(n-2)) / 12.
```

It activates only after matching uniform substeps. Variable spacing falls back
to variable-step AB2, and the first replay substep remains unpredicted. The
implicit formula, nonlinear residual, damping, and convergence tests still
decide acceptance [[17]](REFERENCES.md#ref-17) [[26]](REFERENCES.md#ref-26).
The extrapolation can therefore improve solver work without weakening replay
authority.

The energy monitor is based on the discrete balance

```text
defect = H_(n+1) - H_n
       - h/2 [(P_s,n - P_d,n) + (P_s,n+1 - P_d,n+1)].
```

Only positive normalized defect counts as artificial energy injection for the
hard gate. Negative defect remains visible as numerical damping. This diagnostic
is especially valuable for nominally passive or lossless circuits, but it does
not identify waveform phase displacement [[13]](REFERENCES.md#ref-13).

Algebraic residual and full circuit residual are also distinct. The former
measures the projected KCL and voltage-constraint solve. The latter includes
the complete evaluated circuit state. Small values establish equation
consistency at the sampled endpoint but do not establish small accumulated
trajectory error. BAB-CS records both and rejects either cap independently
[[12]](REFERENCES.md#ref-12) [[25]](REFERENCES.md#ref-25).

Event resets prevent multistep history from crossing a known discontinuity.
When a waveform breakpoint is reached, previous derivatives, step history,
Jacobian history, and recursive bound ownership are reset to the accepted event
state. The next step uses implicit startup [[28]](REFERENCES.md#ref-28). This is
mathematically preferable to applying a smooth-history extrapolation across a
jump that invalidates its assumptions.

## Portability and Limits

The hard-gate structure is fail closed. Nonfinite metrics, failed projection,
failed implicit solves, excessive residual, excessive positive energy
injection, predictor/reference caps, failed replay, minimum-step exhaustion,
and rejection-budget exhaustion prevent partial state commitment
[[12]](REFERENCES.md#ref-12) [[32]](REFERENCES.md#ref-32). A fallback is not
counted as evidence that the candidate succeeded; diagnostics preserve the
authority transfer.

The resulting bounded design can attach to other methods when three conditions
hold. First, the method must expose a candidate endpoint that can be projected.
Second, the controller must have a defensible amplification or local-defect
model. Third, an independent reference and replay path must remain available.
The existing explicit, implicit, one-step, and multistep candidates demonstrate
this portability, while also showing that different candidates incur different
cost and evidence quality [[14]](REFERENCES.md#ref-14).

A bounded embedded RK23 is especially attractive because its third-order
candidate and second-order companion provide an error signal without an
additional implicit solve. It spends three projected stages, so it is not
automatically cheaper than AB2, but it can reduce reference frequency while
retaining a direct embedded defect estimate. The current local characterization
shows that this trade can be favorable for smooth RC and nonlinear diode cases,
subject to the stated workload and timing limits [[14]](REFERENCES.md#ref-14).

No finite numerical architecture can promise indefinite exact trajectory
agreement for every circuit. Physically unstable systems amplify real
perturbations, chaotic systems separate nearby trajectories, uncertain device
models limit correspondence to hardware, and finite precision remains finite.
BAB-CS instead makes a narrower and testable promise: within its supported
topologies, it will expose and bound its internal error model, refresh authority
independently, transfer control when evidence degrades, and fail explicitly
rather than silently continue outside declared limits.
