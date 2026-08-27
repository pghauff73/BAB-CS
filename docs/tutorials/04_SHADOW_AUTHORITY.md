# Tutorial 4: Shadow Authority

Shadow authority means that a candidate method runs beside the accepted
numerical authority without owning the accepted state. The candidate produces
diagnostics, cost, and a proposed trajectory. The independent implicit method
still decides the state that the simulation records.

![Shadow authority flow](html/assets/tutorial-04-shadow-authority.svg "Candidate and implicit paths run in parallel while only the implicit path owns the accepted state.")

## What You Will Learn

BAB-CS has three rollout modes:

- **disabled mode** does not execute the candidate and accepts the implicit
  reference result;
- **shadow mode** executes the candidate for observation but still accepts the
  implicit reference result; and
- **active mode** may accept a bounded candidate result after correction and
  independent gates pass.

A candidate method is the numerical formula being studied. Numerical authority
is the independent calculation and rule set that owns acceptance.

## Run the Exercise

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 04-shadow-authority
```

The verifier runs one resistor-capacitor (`RC`) circuit in all three modes.

## Expected Results

Disabled and shadow modes should accept the same implicit trajectory because
the candidate is observational only in shadow mode. Their accepted states are
expected to differ by no more than ordinary solver roundoff. Shadow mode should
still record candidate steps and independent reference solves. Active mode is
expected to report bounded candidate authority when its correction and gates
permit candidate promotion.

## Observed Data

The exercise was run on August 27, 2026.

| Measurement | Observed value |
| --- | --- |
| Disabled-mode accepted authority | implicit method |
| Shadow-mode accepted authority | implicit method |
| Active-mode accepted authority | bounded candidate path |
| Candidate steps observed in shadow mode | `19` |
| Candidate steps used in active mode | `19` |
| Independent reference solves in shadow mode | `20` |
| Maximum shadow-versus-disabled state difference | `1.3877787807814457e-17` |
| Recorded 16-unit-in-the-last-place (`ULP`) tolerance | `3.552713678800501e-15` |
| Shadow match within solver roundoff | `true` |

The maximum state difference was only `0.00390625` of the allowed tolerance,
which is 256 times smaller than the gate. Candidate diagnostics were still
generated for 19 steps, but the shadow candidate did not gain authority over
the accepted state.

## Expected Versus Actual Results

All authority assignments matched the expectation. The shadow and disabled
states were not bit-for-bit identical, but their maximum difference was
`1.3877787807814457e-17`, far below the
`3.552713678800501e-15` tolerance. That nonzero difference is consistent with
minor changes in floating-point evaluation or nonlinear-solve ordering and is
not evidence that the shadow candidate altered acceptance.

## Follow the Accepted State

Shadow mode is designed for safe observation. It can answer questions such as:

- How often would the candidate have been used?
- How expensive is the candidate?
- How large is its defect against the reference?
- Where does it encounter stiffness or nonlinear difficulty?

Stiffness means that fast and slow behavior occur together, forcing some
methods to take very small steps for stability.

The verifier requires the shadow time grid to match disabled mode exactly. It
also compares every accepted state component using a 16-unit-in-the-last-place
gate. A unit in the last place (`ULP`) is the spacing between neighboring
floating-point numbers near a value. The gate allows ordinary solver roundoff
without allowing the candidate to alter the accepted trajectory.

Candidate diagnostics must still be present. Otherwise the run would merely be
disabled mode with a different label.

## Theory and Practical Outcomes

The theoretical outcome is separation of observation from authority. A method
can be measured without allowing its proposal to modify the accepted state.

Shadow operation is useful before enabling a new numerical method in a
qualification or production workflow. Engineers can collect method-specific
evidence on real workloads while preserving the established accepted-state
authority. The same pattern is useful for comparing sparse solvers, nonlinear
strategies, or alternative error estimators.

## Conclusion

The experiment met the expected authority-separation result. Shadow mode
provides a practical migration path for collecting candidate evidence under
real workloads before active acceptance is considered.

## Claim Boundary

Shadow agreement proves that the accepted state remained under the implicit
authority for the measured case. It does not prove that the candidate would be
safe in active mode, because active acceptance introduces additional
correction, bounds, gates, and fallback behavior.
