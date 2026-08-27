# Exercise 5: Deterministic Packaging

## Objective

Build the wheel twice from one source state, compare hashes, and inspect archive
timestamps, permissions, and member ordering.

## Run

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 05-deterministic-packaging
```

Use `--development` only for an explicitly non-release dirty-tree exercise.

## Questions

1. Why is a clean exact source commit required for release evidence?
2. Why do fixed ZIP timestamps matter?
3. What does a matching wheel hash prove, and what does it not prove?

## Evidence

The verifier records both wheel hashes, requires byte identity, and checks the
backend contract: sorted source modules followed by the fixed metadata and
record sequence. Development mode is labeled and never promoted to release
evidence.
