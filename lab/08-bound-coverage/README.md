# Exercise 8: Empirical Bound Coverage

## Objective

Compare the recursive internal bound with independently calculated
authority-epoch drift error between anchors, then report the empirical coverage
ratio without calling it a proof.

## Run

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 08-bound-coverage
```

## Questions

1. Why is the error measured from the current anchor rather than only from time zero?
2. Why are event and re-anchor samples excluded from ordinary coverage rows?
3. Why can a measured coverage ratio never become a formal enclosure theorem by itself?

## Evidence

The verifier records eligible samples, covered samples, the coverage ratio,
maximum authority-epoch drift error, and maximum recursive internal bound.
