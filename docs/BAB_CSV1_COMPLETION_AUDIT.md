# Bounded-Authority-Based-Circuit-Simulation v1 Completion Audit

Audit date: August 24, 2026

## Scope

This audit evaluates the current `/home/pamela/Projects/BAB-CS` filesystem
against `docs/BAB_CSV1_SPEC.md` and `IMPLEMENTATION_PLAN.md`. The directory is a
standalone source tree and is not currently a Git repository, so the built wheel
hash and deterministic simulation-output hashes are the release evidence.

## Requirement Matrix

### BAB-001 — Dynamic State: Achieved

- `src/babcs/model.py` defines capacitor-voltage and inductor-current ordering,
  names, initial state, derivatives, and stored energy.
- `tests/test_model.py::test_lc_dynamic_coordinates_follow_passive_sign_convention`
  verifies the state convention and derivative signs.

### BAB-002 — Algebraic Projection: Achieved

- `Circuit.solve_algebraic` assembles KCL, voltage constraints, nonlinear device
  Jacobians, damped Newton iteration, and explicit singular/failure exceptions.
- Every model evaluation calls the algebraic solve before derivatives or
  diagnostics are produced.
- RC projection and singular failure are tested in `tests/test_model.py`.

### BAB-003 — Adams-Bashforth Predictor: Achieved

- `variable_step_ab2_predict` implements the required variable-step AB2 formula.
- `BoundedAdamsBashforthIntegrator.step` uses that function only when valid
  previous derivative and step history exists.
- `test_variable_step_ab2_coefficients` directly verifies the coefficient
  contract.

### BAB-004 — Reference Authority: Achieved

- `src/babcs/integrators.py` implements backward Euler, trapezoidal, and
  variable-step BDF2 with damped Newton solution.
- Tests verify the backward-Euler analytic step, trapezoidal second-order
  convergence, and variable-step BDF2 history.

### BAB-005 — Contractive Correction: Achieved

- The active integrator derives a correction gain from the conservative
  predictor amplification and configured target contraction.
- Stiffness or `closed_loop_gain >= 1` transfers full authority to the implicit
  reference.
- Active-mode tests verify every AB step has gain below one and correction does
  not increase reference deviation.

### BAB-006 — Runtime Bounds: Achieved

- `StepMetrics` separately records predictor/reference error,
  corrected/reference error, algebraic residual, full residual, signed energy
  defect, positive injection ratio, stiffness, amplification, closed-loop gain,
  recursive estimated bound, and anchor deviation.
- CSV and JSON outputs preserve these diagnostics.

### BAB-007 — Hard Failure Gates: Achieved

- Predictor, residual, energy, projection, reference, re-anchor, rejection-count,
  minimum-step, and all non-finite metric failures are fail closed.
- `test_hard_predictor_cap_rejects_large_step` and
  `test_non_finite_amplification_fails_closed` exercise hard rejection paths.

### BAB-008 — Independent Re-Anchor: Achieved

- `reanchor_if_due` calls `integrate_reference_window` from the saved trusted
  anchor, using smaller implicit steps rather than the provisional current state.
- The replay endpoint replaces the candidate, previous derivative history is
  rebuilt when available, the recursive bound is cleared, and generation and
  anchor counters are advanced.
- Periodic and forced safety-anchor behavior is covered in `tests/test_babcs.py`.

### BAB-009 — Event Safety: Achieved

- `Simulator.run` splits steps at waveform breakpoints and resets history only
  when the accepted endpoint actually reaches the event.
- Tests verify post-event implicit startup and ensure a rejected shortened step
  is not mislabeled as an event.

### BAB-010 — Stiffness Fallback: Achieved

- Differential Jacobian infinity norms produce the runtime stiffness indicator.
- Exceeding `stiffness_limit` gives full authority to the implicit reference.
- `test_stiffness_gate_uses_implicit_authority` verifies the transition.

### BAB-011 — Passivity Monitor: Achieved

- Circuit evaluation reports capacitor/inductor energy, source power, and
  resistive, switch, and diode dissipation.
- BAB-CS calculates signed discrete energy balance and gates positive numerical
  energy injection.
- The LC regression verifies bounded energy with periodic independent anchors.

### BAB-012 — Rollout Modes: Achieved

- `BABCSConfig.rollout_mode` accepts `disabled`, `shadow`, and `active` and
  defaults to `shadow`.
- Tests prove disabled mode does not execute AB and shadow mode always accepts
  the implicit reference state.

### BAB-013 — Deterministic Diagnostics: Achieved

- The CLI loads JSON circuit cases and writes per-step CSV plus aggregate JSON.
- Two independent installed-wheel executions of every included example produced
  byte-identical CSV and JSON files.
- CLI output and file creation are covered by `tests/test_cli.py`.

### BAB-014 — Fail-Closed Topology Handling: Achieved

- Dense linear solves use partial pivoting and reject singular systems.
- BAB-CS does not add hidden shunts or parasitic components.
- A floating current-source topology deterministically raises
  `CircuitSolveError` in the regression suite.

## Completion Gates

- Variable-step AB2 coefficient test: passed.
- Algebraic KCL and constraint projection: passed.
- Backward Euler analytic result: passed.
- Trapezoidal second-order convergence: passed.
- Variable-step BDF2: passed.
- Contractive active AB steps: passed.
- Hard error and non-finite rejection: passed.
- Independent periodic and safety anchors: passed.
- Breakpoint history reset: passed.
- Stiffness fallback: passed.
- Passive LC energy bound: passed.
- Singular topology failure: passed.
- JSON CLI and installed wheel: passed.
- Deterministic example replay: passed.

## Validation Evidence

Final source-suite command:

```text
PYTHONPATH=src python -m unittest discover -s tests -v
Ran 25 tests in 0.469s
OK
```

Packaging and installed execution:

```text
python -m pip wheel . --no-deps --wheel-dir dist
python -m venv /tmp/babcs-release-venv
/tmp/babcs-release-venv/bin/python -m pip install --no-deps \
  dist/bab_cs-1.0.0-py3-none-any.whl
/tmp/babcs-release-venv/bin/python -m pip check
No broken requirements found.
```

Wheel SHA-256:

```text
242e04db7fa3422f8552f914b7abbf0773cfa51faa5a9d530bbcae9450a1b5ac
```

Deterministic summary SHA-256 values:

```text
rc_step.json    69b38db644fac821b9020d1309a0e4932918b360e8b0e236e5548eef2e67c8c8
lc_tank.json    796436d7e57b2f804a441f5aac31c698da990d760594c64d623a83a716b8543b
pulsed_rc.json  17624f04e5f23bc04c6de9d06d873753391db032f28d37fb9ea251184414c8ca
```

Representative runtime evidence:

- RC: 500 accepted steps, 499 AB steps, 500 contractive steps, zero rejected
  steps, maximum full residual `2.168404344971009e-19`.
- LC: 4,019 accepted steps, 4,017 AB steps, 4,019 contractive steps, 200
  periodic anchors, maximum full residual `1.1102230246251565e-16`.
- Pulsed RC: 318 accepted steps, 298 AB steps, 44 implicit fallbacks, 54
  rejected/reduced attempts, 16 periodic anchors, maximum full residual
  `2.168404344971009e-19`.

## Boundary Statement

BAB-CSv1 is complete for the stated reference-implementation scope. It does not
claim production-scale sparse performance, support for arbitrary higher-index
MNA topologies, arbitrary analog event root finding, or unconditional exact
trajectory bounds. Those remain explicit future-version boundaries rather than
silent partial implementations.
