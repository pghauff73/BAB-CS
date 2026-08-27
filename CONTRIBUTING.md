# Contributing to Bounded-Authority-Based-Circuit-Simulation

Bounded-Authority-Based-Circuit-Simulation welcomes reproducible defect reports,
numerical evidence, documentation improvements, and carefully bounded algorithm
proposals.

## Development Setup

The project requires Python 3.11 or later and has no mandatory runtime
dependency.

```bash
git clone https://github.com/pghauff73/Bounded-Authority-Based-Circuit-Simulation.git
cd Bounded-Authority-Based-Circuit-Simulation
PYTHONPATH=src python -m unittest discover -s tests -v
```

Install the optional sparse stack when working on SciPy or KLU paths:

```bash
python -m pip install ".[sparse]"
```

## Change Discipline

- Preserve the separation between speculative candidates and authoritative
  acceptance evidence.
- Do not weaken residual, contraction, passivity, replay, topology, or release
  gates to make a benchmark pass.
- Keep acceleration paths subordinate to validated fallback paths.
- Add deterministic tests for every new semantic branch or failure mode.
- State whether evidence is local source, installed wheel, optional backend,
  long-horizon, cross-implementation, or full release qualification.
- Do not describe a clean test run as release approval.
- Do not change frozen comparison fixtures or thresholds without explaining the
  authority and expected effect.

## Pull Requests

Before opening a pull request:

1. Run the focused tests for the changed code.
2. Run the full default suite:

   ```bash
   PYTHONPATH=src python -m unittest discover -s tests -v
   ```

3. Run long or optional backend tiers when the change can affect them.
4. Run `git diff --check`.
5. Document any test, backend, environment, or evidence tier that was not run.
6. Keep unrelated dirty work out of the patch.

Pull-request descriptions should identify the requirement, implementation,
validation evidence, claim boundary, and rollback path. Review conversations
must be resolved before merge.

## Numerical Evidence

Useful numerical reports include:

- the exact source commit or release asset hash;
- complete input files and command line;
- Python, platform, SciPy, KLU, and ngspice versions where relevant;
- deterministic JSON/CSV/SVG artifacts or minimal extracts;
- expected authority and observed behavior;
- error, residual, energy, phase, iteration, and work metrics separately.

## Release Authority

Contributors may prepare release evidence, but only an explicit human decision
naming the exact source SHA, tag, wheel hash, manifest hash, and reviewed
requirements can approve publication. Pull requests, models, CI, and automation
remain advisory to that decision.
