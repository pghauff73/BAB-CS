# BAB-CS Teaching and Reproducibility Lab

The dependency-light lab under `lab/` contains ten executable exercises:

1. modified nodal analysis;
2. measured fixed-step convergence;
3. phase versus energy;
4. shadow authority;
5. deterministic wheel packaging;
6. source versus installed-wheel equivalence;
7. exact event alignment and multistep restart;
8. empirical recursive-bound coverage;
9. fallback and rejection forensics; and
10. semantic mapping of 20 ngspice cases.

The complete novice tutorials are separate HTML-tree documents:

1. [Modified nodal analysis and state ownership](tutorials/01_MNA_STATE_OWNERSHIP.md)
2. [Convergence by measured refinement](tutorials/02_CONVERGENCE_BY_REFINEMENT.md)
3. [Phase error versus energy error](tutorials/03_PHASE_VERSUS_ENERGY.md)
4. [Shadow authority](tutorials/04_SHADOW_AUTHORITY.md)
5. [Deterministic packaging](tutorials/05_DETERMINISTIC_PACKAGING.md)
6. [Source versus installed-wheel equivalence](tutorials/06_SOURCE_WHEEL_EQUIVALENCE.md)
7. [Exact event alignment](tutorials/07_EVENT_ALIGNMENT.md)
8. [Empirical bound coverage](tutorials/08_EMPIRICAL_BOUND_COVERAGE.md)
9. [Fallback and rejection forensics](tutorials/09_FALLBACK_AND_REJECTION_FORENSICS.md)
10. [Semantic mapping to ngspice](tutorials/10_SEMANTIC_NGSPICE_MAPPING.md)

Run the core numerical path with:

```bash
PYTHONPATH=src python lab/support/verify.py \
  --exercise 01-mna \
  --exercise 02-convergence \
  --exercise 03-phase-versus-energy \
  --exercise 04-shadow-authority
```

Run the full path from a clean source tree with:

```bash
PYTHONPATH=src python lab/support/verify.py --exercise all \
  --output artifacts/teaching-lab/verification.json
```

Packaging exercises reject a dirty tree unless `--development` is explicit.
Development output is labeled non-release evidence. Source/wheel verification
creates an isolated virtual environment, removes `PYTHONPATH`, asserts the
imported module path is outside the repository, and compares source,
installed-module, and installed-console traces and summaries byte-for-byte for
RC, switched RC, and all three reduced-order power-stage cases. The recorded
isolated-environment path is normalized for deterministic evidence. The same
isolated wheel also runs a quick RC Method Observatory smoke and must reproduce
the source numerical report byte-for-byte.
The shadow-authority exercise separately requires an identical accepted time
grid and records the maximum state delta against a 16-ULP solver-roundoff gate;
candidate diagnostics do not grant accepted-state authority.
The event-alignment exercise proves exact scheduled breakpoints and post-event
startup. The bound-coverage exercise deliberately retains a zero measured
coverage result rather than turning it into a favorable claim. The forensics
exercise separates rejected work, fallback, and accepted completion on a
reduced-order H-bridge. The mapping exercise verifies the canonical state order
and all 20 manifest-owned ngspice translations.

The review-controlled fixture changes only with explicit
`--update-fixtures --exercise all`. The command prints old and new hashes;
regenerating a fixture is not evidence that the changed result is acceptable.

Each exercise README includes objectives, commands, interpretation questions,
evidence, and a conservative claim boundary.
