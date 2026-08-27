# Exercise 1: Modified Nodal Analysis

## Objective

Identify the capacitor voltage as a dynamic state, node voltages and source
current as algebraic unknowns, and KCL/voltage constraints as the projection
problem.

## Run

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 01-mna
```

## Questions

1. Why is `v(C1)` a state while `voltage:out` is algebraic output?
2. Which equation constrains `vin` to the source waveform?
3. Why does a small algebraic residual not prove small trajectory error?

## Evidence

The verifier reports dynamic names, node order, algebraic size, initial
derivative, and residual. The exercise proves formulation consistency for this
one RC circuit, not general high-index DAE support.
