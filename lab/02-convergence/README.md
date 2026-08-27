# Exercise 2: Convergence

## Objective

Measure error over three fixed-step trapezoidal refinements against the analytic
RC solution and calculate observed order.

## Run

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 02-convergence
```

## Questions

1. Why is one small error not evidence of convergence?
2. Why must the same authority and problem interval be used at every step?
3. Why would diode or switched cases require refined rather than analytic
   authority here?

## Evidence

The verifier requires monotonically decreasing maximum error and second-order
behavior over the measured refinements. This is scoped convergence evidence for
the declared linear RC case.
