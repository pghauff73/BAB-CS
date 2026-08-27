# BAB-CS Teaching and Reproducibility Lab

The lab is a dependency-light sequence of executable exercises. Core exercises
use Markdown, JSON, the public BAB-CS API/CLI, and the Python standard library.

## Short Path

Run the four foundational numerical exercises:

```bash
PYTHONPATH=src python lab/support/verify.py \
  --exercise 01-mna \
  --exercise 02-convergence \
  --exercise 03-phase-versus-energy \
  --exercise 04-shadow-authority
```

## Full Path

Run all ten exercises, including wheel construction, isolated installation,
event handling, bound coverage, failure forensics, and external semantic
mapping:

```bash
PYTHONPATH=src python lab/support/verify.py --exercise all
```

A dirty source tree is rejected by the packaging exercises unless
`--development` is explicit. Development mode is not release evidence.

The ten exercises are:

1. modified nodal analysis;
2. convergence by measured refinement;
3. phase versus energy;
4. shadow authority;
5. deterministic packaging;
6. source versus wheel equivalence;
7. exact event alignment and multistep restart;
8. empirical recursive-bound coverage;
9. fallback and rejection forensics; and
10. semantic mapping of 20 ngspice cases.

`lab/fixtures/verification-baseline.json` is review-controlled. The verifier
never changes it unless `--update-fixtures` is explicitly supplied; fixture
updates print old and new hashes and remain subject to human review.
