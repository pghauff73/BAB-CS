# Exercise 10: Semantic ngspice Mapping

## Objective

Inspect the 20-case external manifest, generate every netlist, and prove that
the exported state order matches BAB-CS capacitor-voltage-then-inductor-current
ownership.

## Run

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 10-ngspice-mapping
```

## Questions

1. Why must a mapping preserve state order as well as component values?
2. How does the diode ideality factor preserve a declared thermal voltage?
3. Why is cross-implementation agreement evidence rather than oracle truth?

## Evidence

The verifier requires exactly 20 unique cases, deterministic `wrdata` output,
matching dynamic-state names, source hashes, category counts, and explicit
non-oracle scope.
