# Tutorial 2: Convergence by Measured Refinement

Convergence means that a numerical result approaches an independent authority
as the timestep becomes smaller. A timestep is the amount of simulated time
advanced in one accepted step. One small error at one timestep is not a
convergence result because it does not show a trend.

![Convergence by measured refinement](html/assets/tutorial-02-convergence.svg "Maximum resistor-capacitor error decreases over three fixed-step refinements.")

## What You Will Learn

This tutorial measures a fixed-step trapezoidal method on a resistor-capacitor
(`RC`) charging problem. Trapezoidal integration uses the average of the state
rate at the beginning and end of a timestep. For a smooth linear problem, its
global error is expected to decrease approximately with the square of the
timestep.

The analytic authority is the closed-form RC charging equation. Analytic means
that the reference value comes from a known mathematical formula rather than a
second numerical run.

## Run the Exercise

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 02-convergence
```

The verifier runs the same circuit and time interval with three progressively
smaller fixed timesteps. Every run uses the same analytic authority and the
same error measurement.

## Expected Results

Trapezoidal integration has second-order global accuracy on this smooth linear
problem. The theoretical error model is proportional to the square of the
timestep. Halving the timestep should therefore reduce the maximum error by
approximately four, and the observed order should approach `2`.

## Observed Data

The exercise was run on August 27, 2026. A microsecond is one millionth of a
second.

| Fixed timestep | Maximum voltage error | Error reduction from previous run |
| ---: | ---: | ---: |
| `100` microseconds | `3.068987885731511e-4` volts | not applicable |
| `50` microseconds | `7.666231473091312e-5` volts | `4.003254919322154` times smaller |
| `25` microseconds | `1.9161684994717376e-5` volts | `4.000812807018167` times smaller |

| Refinement interval | Observed order |
| --- | ---: |
| `100` to `50` microseconds | `2.0011734866053392` |
| `50` to `25` microseconds | `2.000293128382485` |

Each halving reduces the maximum error by approximately four. That repeated
ratio produces an observed order near two, which is the measured evidence for
second-order behavior on this smooth case.

## Expected Versus Actual Results

The expected and actual trends agree. The measured reduction factors were
`4.003254919322154` and `4.000812807018167`, slightly larger than the ideal
factor of four. The corresponding orders were `2.0011734866053392` and
`2.000293128382485`, slightly above two.

The small difference from exactly second order is expected in a finite
refinement study. The total error contains the leading square-of-timestep term,
smaller higher-order terms, and floating-point effects. As the timestep becomes
smaller, the higher-order contribution changes the ratio slightly before the
eventual roundoff floor is reached.

## Understand the Refinement Test

The exercise records the maximum voltage error over the complete accepted
trajectory. It then calculates observed order from neighboring refinements:

```text
observed order = log(coarse error / fine error) / log(2)
```

The denominator uses `log(2)` because each refinement halves the timestep. If
halving the timestep reduces error by roughly four, the observed order is near
two.

The test requires both of these conditions:

1. every finer run has a smaller maximum error; and
2. the measured order remains consistent with second-order behavior.

This is stronger than reporting the finest error alone. It can reveal a
mistaken reference, a coding defect, a changed method, or a regime where the
expected asymptotic trend has not yet appeared.

## Why Fixed Inputs Matter

A refinement study becomes misleading if several things change at once. Do not
change the model, stop time, authority, tolerance scaling, or measured state
while claiming that only the timestep caused the difference.

Nonlinear diode and switched cases usually do not have a convenient exact
formula over the whole run. For them, BAB-CS uses a refined replay: a separate
numerical recomputation with a declared implicit method and smaller internal
steps. That is useful evidence, but it must be labeled numerical rather than
analytic.

## Theory and Practical Outcomes

The theoretical outcome is a measured confirmation of the method's expected
global order for a smooth resistor-capacitor transient. It does not rely on one
small error value; it relies on a repeatable refinement slope.

Convergence studies help choose a timestep for filter startup, resonant
transients, switching schedules, and controller test models. They also reveal
when a method's formal order is not being achieved because discontinuities,
nonlinear solves, or event handling dominate the error.

## Conclusion

The experiment met its expected second-order result. In practice, the data
supports using refinement studies to select a timestep and to detect when a
method, reference, or implementation no longer exhibits its expected behavior.

## Claim Boundary

The measured second-order trend applies to this declared smooth RC case and
these three timesteps. It does not prove second-order behavior for every
circuit, switching event, nonlinear solve, or adaptive execution path.
