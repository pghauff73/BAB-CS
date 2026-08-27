# Exercise 3: Phase Versus Energy

## Objective

Compare backward Euler and trapezoidal LC trajectories over ten periods while
reporting final phase error and relative energy span separately.

## Run

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 03-phase-versus-energy
```

## Questions

1. Which method damps stored energy more strongly?
2. Can a small energy span coexist with nonzero phase error?
3. Why is passivity evidence not a phase-error bound?

## Evidence

The verifier reports method-specific phase and energy metrics. It does not claim
that either quantity alone encloses exact long-horizon trajectory error.
