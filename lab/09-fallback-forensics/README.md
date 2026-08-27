# Exercise 9: Fallback and Rejection Forensics

## Objective

Use the reduced-order scheduled H-bridge experiment to separate rejected work,
implicit fallback, event resets, and the final accepted trajectory.

## Run

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 09-fallback-forensics
```

## Questions

1. Why is a rejected candidate not an accepted-state failure?
2. Which reason identifies candidate difficulty and which identifies authority difficulty?
3. Why must this example remain labeled a reduced-order numerical experiment?

## Evidence

The verifier requires nonzero rejection and fallback evidence, retains the
classified causes, and confirms that the simulation still reaches the declared
stop time. It makes no production-device claim.
