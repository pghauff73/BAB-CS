# Bounded-Authority-Based-Circuit-Simulation v1 Normative Specification

## Requirements

### BAB-001 — Dynamic State

The canonical differential state shall consist of capacitor voltages followed
by inductor currents. Algebraic node voltages and voltage-defined branch
currents shall be recomputed from the circuit constraints.

### BAB-002 — Algebraic Projection

Every predicted, corrected, implicit, and re-anchored differential state shall
be projected by solving the algebraic circuit equations. Failure or singularity
shall reject the operation without committing partial state.

### BAB-003 — Adams-Bashforth Predictor

The active predictor shall be variable-step AB2:

```text
z_(n+1) = z_n + h_n * ((1 + r/2) f_n - (r/2) f_(n-1))
r = h_n / h_(n-1)
```

AB history shall be invalid until two consistent accepted derivative samples
exist.

### BAB-004 — Reference Authority

Backward Euler shall be available for startup and recovery. Trapezoidal and
variable-step BDF2 shall be available as second-order reference methods.

### BAB-005 — Contractive Correction

Active mode shall correct the AB state toward the implicit reference. If the
estimated corrected transition is not contractive, the implicit reference
shall receive full state authority.

### BAB-006 — Runtime Bounds

The implementation shall separately report predictor/reference error,
corrected/reference error, algebraic residual, full residual, positive energy
injection, stiffness, amplification, closed-loop gain, and recursive estimated
bound.

### BAB-007 — Hard Failure Gates

Non-finite metrics, exceeded predictor caps, exceeded residual caps, excessive
positive energy injection, failed projection, failed reference solve, and
failed independent replay shall reject the candidate step.

### BAB-008 — Independent Re-Anchor

At the configured interval, the solver shall reintegrate from the previous
trusted anchor with smaller implicit steps. It shall replace the provisional
endpoint, rebuild the previous derivative state when available, clear the
recursive bound, and increment the anchor generation.

### BAB-009 — Event Safety

Known waveform breakpoints shall terminate integration steps exactly. No AB
history may cross an event boundary. Before multistep history is cleared, the
solver shall independently replay from the trusted anchor to the exact event
time, replace the provisional event state, and reapply energy and residual
gates. Event replay shall use at least eight refinement subdivisions. The next
step shall use the configured reference method for implicit startup. An event
history reset shall not, by itself, advance authority generation or replace the
trusted anchor.

### BAB-010 — Stiffness Fallback

When the timestep multiplied by the differential Jacobian norm exceeds the
configured stiffness limit, the implicit reference shall receive full state
authority.

### BAB-011 — Passivity Monitor

Stored capacitor and inductor energy, source work, and resistive/device
dissipation shall be used to detect positive numerical energy injection. The
energy monitor shall not be represented as a phase-error bound.

### BAB-012 — Rollout Modes

The implementation shall provide `disabled`, `shadow`, and `active` modes.
`shadow` shall be the default and shall never accept an AB-predicted state.

### BAB-013 — Deterministic Diagnostics

The CLI shall write deterministic CSV step metrics and a JSON summary containing
accepted steps, rejected steps, anchors, safety anchors, implicit fallbacks,
maximum errors, maximum residuals, and contractive/AB step counts.

### BAB-014 — Fail-Closed Topology Handling

Unsupported or singular circuit topologies shall raise an explicit solve error.
BAB-CSv1 shall not silently add shunt conductance or parasitic storage.

## Bound Semantics

For the augmented AB history error `E_n`, BAB-CS records a recurrence

```text
B_(n+1) = q_n B_n + delta_n
```

where `q_n` is the estimated corrected transition gain and `delta_n` contains
the measured corrected/reference deviation plus normalized residual defect.
`certified_contractive` may be true only when `q_n < 1` and the bound is finite.

This is an internal numerical bound relative to the implemented reference
system. It is not an unconditional proof of exact physical trajectory error.

## Supported Topology Boundary

The semiexplicit formulation supports circuits for which capacitor voltages and
inductor currents determine a unique algebraic operating state. Capacitor loops,
inductor cutsets, conflicting ideal voltage constraints, floating nodes, and
other singular or higher-index structures may be rejected.
