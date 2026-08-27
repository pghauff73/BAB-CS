# Bounded-Authority-Based-Circuit-Simulation v1 Implementation Plan

## Objective

Create a bounded variable-step Adams-Bashforth circuit integrator with
projection, an implicit reference, contractive correction, independent periodic
re-anchoring, passivity monitoring, event-safe history management, and
fail-closed fallback.

## Milestones

1. **Normative specification** — define supported circuits, bounds, failure
   semantics, and rollout modes.
2. **Semiexplicit MNA core** — solve algebraic KCL and constraint equations from
   capacitor-voltage and inductor-current state.
3. **Implicit authority** — implement backward Euler, trapezoidal, and
   variable-step BDF2 reference steps.
4. **AB2 predictor** — implement fixed/variable-step history, startup, and
   history invalidation.
5. **Projection and correction** — project predictions, calculate a reference,
   apply contractive correction, and project again.
6. **Bound monitor** — enforce predictor, residual, energy, contraction, and
   minimum-step gates.
7. **Independent anchor** — replay from a trusted checkpoint with smaller
   implicit steps and rebuild AB history.
8. **Events and stiffness** — split at breakpoints, reset history, and transfer
   authority to the implicit solver for stiff steps.
9. **Observability** — emit per-step CSV metrics and aggregate JSON summaries.
10. **Qualification** — verify analytic, nonlinear, stiff, oscillatory, event,
    singular, CLI, and packaging behavior.

## Promotion Sequence

1. `disabled`: implicit authority only.
2. `shadow`: AB diagnostics with implicit state authority.
3. `active`: bounded AB/reference correction with every-step reference.

An unreferenced periodically corrected production mode is not part of v1.

## Completion Gates

- Variable-step AB2 coefficients are tested.
- Algebraic projection satisfies KCL and voltage constraints.
- Reference methods pass analytic convergence tests.
- Every accepted active AB step has closed-loop gain below one.
- Hard caps reject and reduce unsafe steps.
- Independent replay anchors replace provisional state and rebuild history.
- Event boundaries reset multistep history.
- Stiffness transfers state authority to the implicit solver.
- Passive LC energy remains bounded while phase is handled by re-anchoring.
- Singular algebraic systems fail closed.
- Source execution, wheel build, tests, and example simulations pass.
