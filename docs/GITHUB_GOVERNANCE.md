# GitHub Governance Controls

Live governance settings are applied from reviewable payloads in
`.github/governance/`.

## Applied State

Owner API readback on August 27, 2026 confirmed:

- `main` protection is active with strict status checks for Python 3.11,
  Python 3.12, Python 3.13, Python 3.14, validated-wheel construction, and the
  optional SciPy/KLU backend job;
- protected updates use pull-request flow with zero mandatory second-person
  approvals, stale-review dismissal, conversation resolution, and administrator
  enforcement;
- force pushes and branch deletion are disabled;
- repository ruleset `21646558`, `Protect release tags`, is active for
  `refs/tags/v*`, blocks deletion and non-fast-forward updates, and has no
  bypass actor;
- private vulnerability reporting is enabled; and
- the topic set recorded below is applied.

These settings are external mutable state. Re-read them before release rather
than treating this dated record as permanent proof.

## `main` Protection

`.github/governance/main-protection.json` configures:

- the four Python matrix checks;
- validated wheel construction;
- optional SciPy and KLU sparse qualification;
- strict up-to-date status checks;
- pull-request flow with no second-person approval requirement;
- stale-review dismissal and conversation resolution;
- administrator inclusion;
- no force pushes or branch deletion.

Apply and verify with:

```bash
gh api --method PUT \
  repos/pghauff73/Bounded-Authority-Based-Circuit-Simulation/branches/main/protection \
  --input .github/governance/main-protection.json

gh api repos/pghauff73/Bounded-Authority-Based-Circuit-Simulation/branches/main/protection
```

## Release Tag Protection

`.github/governance/release-tag-ruleset.json` prevents deletion and
non-fast-forward updates of tags matching `v*`, while still allowing a new
release tag to be created after exact-hash approval.

```bash
gh api --method POST \
  repos/pghauff73/Bounded-Authority-Based-Circuit-Simulation/rulesets \
  --input .github/governance/release-tag-ruleset.json

gh api repos/pghauff73/Bounded-Authority-Based-Circuit-Simulation/rulesets/21646558
```

Use `POST` only when the named ruleset does not exist. Update an existing
ruleset by its read-back identifier to avoid duplicate policies.

Read back settings after every mutation. GitHub settings are live external
state; the JSON files record intent but do not prove the settings remain
applied.

## Topics and Security Reporting

The intended topic set is:

```text
circuit-simulation
error-bounds
modified-nodal-analysis
numerical-methods
python
reproducible-research
scientific-computing
transient-analysis
```

Private vulnerability reporting is enabled so `SECURITY.md` can direct
sensitive reports away from public issues.
