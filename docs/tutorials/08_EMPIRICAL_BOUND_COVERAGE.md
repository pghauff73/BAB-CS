# Tutorial 8: Empirical Bound Coverage

The recursive internal bound is BAB-CS's running estimate of how modeled
numerical error can accumulate between trusted anchors. Empirical coverage asks
how often an independently measured authority-epoch drift error is less than or
equal to that bound.

![Empirical bound coverage](html/assets/tutorial-08-bound-coverage.svg "The measured authority-epoch drift error exceeds the recursive internal bound on the eligible tutorial samples.")

## What You Will Learn

An anchor is a retained accepted state from which an independent replay can
start. An authority epoch is the interval since the current anchor. Drift error
within the epoch compares two changes:

- how far the accepted candidate state moved from the anchor; and
- how far the independent authority moved from its corresponding anchor.

This subtraction matters because the recursive bound describes accumulated
drift from the current anchor, not necessarily total error from time zero.

## Run the Exercise

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 08-bound-coverage
```

The tutorial uses a resistor-capacitor (`RC`) case with an analytic authority.
The state difference is scaled with the same absolute and relative tolerances
used by BAB-CS.

## Expected Results

An optimistic expectation for a conservative recursive bound is that it covers
most or all eligible authority-epoch drift samples. The stricter scientific
expectation is only that the measurement reports coverage honestly and does not
turn empirical evidence into a formal proof. The exercise therefore tests both
the numerical coverage ratio and the integrity of the claim boundary.

## Observed Data

The exercise was run on August 27, 2026.

| Measurement | Observed value |
| --- | ---: |
| Eligible samples | `17` |
| Covered samples | `0` |
| Empirical coverage ratio | `0.0` |
| Maximum authority-epoch drift error | `11512.211750693821` |
| Maximum recursive internal bound | `642.995485991595` |
| Formal enclosure claimed | `false` |

At the largest recorded values, the measured drift error was about
`17.904031990116184` times the internal bound. Coverage was therefore zero, not
because the run lacked eligible samples, but because none of the 17 measured
samples satisfied the coverage inequality. The values are scaled error units,
not volts or amperes, because absolute and relative tolerances normalize each
state component before comparison.

## Expected Versus Actual Results

The optimistic coverage expectation was not met: zero of 17 eligible samples
were covered, and the maximum measured drift was about 17.9 times the maximum
recursive bound. The reporting expectation was met because the verifier
retained the zero ratio and explicitly set the formal-enclosure claim to
`false`.

The current experiment does not isolate one proven cause for the shortfall.
Plausible contributors include incomplete local-to-global error propagation,
anchor-epoch scaling, omitted error sources, or a configuration whose bound
parameters are too small for the measured drift. These are hypotheses for
controlled follow-up experiments, not conclusions established by this one
ratio.

## Understand Eligibility

Not every accepted point is an ordinary coverage sample. The verifier excludes:

- the initial state;
- an event boundary, because the governing schedule changes there; and
- a re-anchor point, because the authority epoch is reset there.

For each remaining point, the verifier records whether:

```text
authority-epoch drift error <= recursive internal bound
```

The empirical coverage ratio is the number of covered samples divided by the
number of eligible samples.

## Interpret the Result Honestly

In the reviewed fixture, none of the 17 eligible samples are covered. This is
not hidden or converted into a favorable score. It is evidence that the current
recursive model, configuration, and scaling do not enclose the independently
measured epoch drift for this tutorial run.

That result is useful. It identifies a concrete research direction: improve the
bound model, change the configuration, narrow the applicability claim, or use a
different authority strategy.

Empirical means observed in experiments. A formal enclosure proof would require
a mathematical argument that covers every allowed state and step under stated
assumptions. A measured ratio—even 100 percent—cannot become that proof by
itself.

## Theory and Practical Outcomes

The theoretical distinction is between an internal modeled bound and an
independently observed error. Coverage measures their relationship; it does not
guarantee enclosure outside the measured samples.

Coverage analysis helps determine whether a numerical bound is conservative
enough for a declared operating region. Grouping results by anchor age,
circuit class, method, or rejection cause can show where the internal model is
strong and where it needs refinement.

## Conclusion

This is the only tutorial in which the optimistic numerical expectation failed.
The practical outcome is still valuable: the recursive bound must remain a
diagnostic quantity for this configuration, and improving or narrowing the
bound model is a clearly identified research task.

## Claim Boundary

This tutorial reports measured coverage for one RC run. It makes no formal
enclosure claim and no statement about unknown physical-model error.
