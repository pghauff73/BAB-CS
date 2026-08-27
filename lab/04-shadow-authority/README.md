# Exercise 4: Shadow Authority

## Objective

Run implicit-only, shadow, and active modes on one RC case and distinguish
candidate diagnostics from accepted state authority.

## Run

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 04-shadow-authority
```

## Questions

1. Which state does shadow mode accept?
2. Why can shadow mode report candidate work without granting candidate
   trajectory authority?
3. What additional claim does active mode make locally, and what does it still
   not prove globally?

## Evidence

The verifier requires the shadow accepted time grid to equal the implicit
reference grid and every accepted state component to match within a recorded
16-ULP solver-roundoff tolerance while candidate diagnostics remain present.
