# Exercise 6: Source Versus Wheel Equivalence

## Objective

Run RC, switched-RC, and all three reduced-order power-stage cases from source,
an isolated installed module, and the installed console entry point, then
compare deterministic traces and summaries.
The same isolated wheel also runs the quick RC Method Observatory smoke, whose
numerical report must match the source run byte-for-byte.

## Run

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 06-source-wheel-equivalence
```

## Questions

1. Why must the installed interpreter run outside the source tree?
2. Which fields may differ only when provenance is explicitly normalized?
3. Why do two matching cases not prove all optional backends equivalent?

## Evidence

The verifier removes `PYTHONPATH`, asserts the imported module path is inside the
isolated environment, and compares source, installed-module, and console output
byte-for-byte for every selected case. The recorded path is normalized under
`<isolated-venv>` so the evidence itself remains deterministic. The
observatory smoke confirms the experiment-record path against the installed
package without packaging the repository-only research tools into the wheel.
