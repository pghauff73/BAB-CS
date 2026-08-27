# Minimal Reproducible Research Example

This walkthrough runs the dependency-free RC step case twice, proves the
generated CSV and JSON are byte-identical, and checks core authority fields.

## 1. Record the exact source

```bash
git rev-parse HEAD
git status --short
python --version
```

For publication evidence, use a clean full commit SHA. A dirty tree is suitable
for development evidence only.

## 2. Run the deterministic example twice

```bash
rm -rf /tmp/babcs-minimal-a /tmp/babcs-minimal-b
mkdir -p /tmp/babcs-minimal-a /tmp/babcs-minimal-b

PYTHONPATH=src python -m babcs simulate examples/rc_step.json \
  --mode shadow \
  --csv /tmp/babcs-minimal-a/trace.csv \
  --summary /tmp/babcs-minimal-a/summary.json

PYTHONPATH=src python -m babcs simulate examples/rc_step.json \
  --mode shadow \
  --csv /tmp/babcs-minimal-b/trace.csv \
  --summary /tmp/babcs-minimal-b/summary.json

cmp /tmp/babcs-minimal-a/trace.csv /tmp/babcs-minimal-b/trace.csv
cmp /tmp/babcs-minimal-a/summary.json /tmp/babcs-minimal-b/summary.json
sha256sum /tmp/babcs-minimal-a/trace.csv /tmp/babcs-minimal-a/summary.json
```

## 3. Check the authority summary

```bash
python - <<'PY'
import json
from pathlib import Path

summary = json.loads(Path("/tmp/babcs-minimal-a/summary.json").read_text())
assert summary["accepted_steps"] > 0
assert summary["rejected_steps"] == 0
assert summary["contractive_steps"] == summary["accepted_steps"]
assert summary["implicit_fallbacks"] >= 1
assert summary["periodic_reanchors"] >= 1
assert summary["maximum_algebraic_residual"] >= 0.0
assert summary["maximum_full_residual"] >= 0.0
assert summary["maximum_estimated_bound"] >= 0.0
print(json.dumps(summary, indent=2, sort_keys=True))
PY
```

The startup fallback is expected: AB2 has insufficient history on the first
step, so the implicit reference controls startup. Periodic replay then refreshes
authority and resets the recursive bound.

## 4. Interpret the result conservatively

This example proves deterministic execution and the reported local authority
behavior for one RC input and one exact source state. It does not qualify sparse
backends, nonlinear devices, long-horizon oscillators, external ngspice
agreement, an installed wheel, or a release.

## 5. Extend to the observatory and lab

After the minimal RC check, run the compact numerical teaching path:

```bash
PYTHONPATH=src python lab/support/verify.py \
  --exercise 01-mna \
  --exercise 02-convergence \
  --exercise 03-phase-versus-energy \
  --exercise 04-shadow-authority
```

Then generate the complete Method Observatory and Bound Coverage Atlas using
the commands in `docs/METHOD_OBSERVATORY.md` and
`docs/BOUND_COVERAGE_ATLAS.md`. Full packaging exercises require a clean exact
source commit for release evidence; `--development` labels dirty-tree output as
non-release evidence. Fixture regeneration is explicit and never constitutes
approval by itself.
