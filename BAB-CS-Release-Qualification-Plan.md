# Bounded-Authority-Based-Circuit-Simulation Release Qualification Plan

## 1. Document Status

- **Proposed release:** `v1.1.0`
- **Plan status:** Executable qualification procedure implemented; release
  execution, approval, tagging, and publication not yet authorized
- **Drafted against repository commit:**
  `26e8c2f289e5e2eba369952031f495c331e1b002`
- **Initial qualification tooling commit:**
  `41782a67a12be4483ab490041e2aed4fa5692990`
- **Current package metadata:** `1.1.0`, owned by `src/babcs/_project.py`
- **Final release commit:** not yet created
- **Final release tag:** not yet created
- **Final wheel SHA-256:** not yet available
- **Qualification decision:** pending

This plan defines the evidence required to qualify, approve, tag, and publish a
BAB-CS release. It does not itself authorize a version change, tag, GitHub
release, or asset upload.

## 2. Purpose

The release process must prove that the published wheel:

1. was built from one exact, reviewed source commit;
2. contains the intended version and package contents;
3. passes source and installed-wheel qualification;
4. preserves the declared numerical, boundedness, robustness, and failure
   behavior;
5. reproduces deterministic comparison evidence;
6. has a recorded and independently checked SHA-256;
7. is the exact artifact attached to the GitHub release; and
8. is published only after an explicit human approval naming the commit, tag,
   wheel hash, and evidence set.

The process is fail-closed. Missing, ambiguous, stale, interrupted, mismatched,
or indirectly inferred evidence means the release is not qualified.

## 3. Governing Sources

The qualification audit must use the following repository sources together:

- `RELEASE.md` for the proposed release scope, notes, compatibility, and manual
  publication procedure.
- `README.md` for supported behavior, rollout modes, commands, limits, and
  automation overview.
- `docs/COMPARISON_PROTOCOL.md` for authority hierarchy, common sampling,
  metrics, threshold policy, fixed-step/fixed-accuracy/fixed-work controls, and
  claim boundaries.
- `docs/BOUNDED_CANDIDATES.md` for supported candidate methods, amplification
  models, fast paths, and selection rules.
- `docs/PERFORMANCE_OPTIMIZATION_AUDIT.md` for locally retained optimizations,
  rejected candidates, measurements, and remaining work.
- `benchmarks/manifest.json` and `benchmarks/cases/` for the canonical numerical
  comparison matrix.
- `.github/workflows/ci.yml`, `.github/workflows/comparisons.yml`, and
  `.github/workflows/release-qualification.yml` for automated evidence.
- `src/babcs/_project.py`, `pyproject.toml`, and `build_backend.py` for canonical
  package and wheel metadata.
- `release-evidence-required.txt` for the complete qualification-bundle file
  profile.
- `tools/release_evidence.py` for workflow/environment recording, wheel and
  comparison inspection, artifact equivalence, deterministic manifest creation,
  checksums, and independent verification.
- `docs/RELEASE_QUALIFICATION_IMPLEMENTATION_AUDIT.md` for the distinction
  between implemented infrastructure and execution-time release evidence.

If these sources disagree, qualification stops until the inconsistency is
resolved in source and revalidated.

## 4. Scope

### 4.1 Included

The `v1.1.0` candidate is expected to qualify:

- bounded explicit Euler, Heun, RK23, and variable-step AB2 candidates;
- bounded backward Euler, trapezoidal, and BDF2 candidates;
- embedded fast AB2, Heun, and RK23 modes;
- disabled, shadow, and active rollout authority;
- algebraic projection and fail-closed projection failure;
- independent implicit references and periodic refined replay;
- recursive error-bound accounting and dynamic reference promotion;
- residual, energy, contraction, finiteness, stiffness, and rejection gates;
- topology and event-boundary history reset behavior;
- dense, automatic, and forced-SciPy linear backends;
- sparse CSC stamping, workspace reuse, specialized kernels, guarded chord
  prediction, contractively bounded Schur prediction, ULP-aware two-step
  sensitivity age, bounded sparse-kernel compile reuse, bounded hot-topology
  kernel adoption, and duplicate exact built-in switch-control sampling;
- per-run built-in breakpoint schedule compilation with custom-waveform and
  subclass compatibility;
- deterministic comparison and wheel construction;
- installed-wheel operation and CLI behavior;
- the documented `ngspice` semantic mappings for `rc_step`, `rl_step`,
  `diode_clip`, and `switched_rc`.

### 4.2 Excluded

The following are not release claims unless separately implemented and added to
the exact release commit before qualification begins:

- production-SPICE device breadth or production-SPICE replacement status;
- formal proof that empirical recursive bounds cover unknown physical error;
- arbitrary analog threshold root finding for switches;
- silent regularization of singular or higher-index circuit topologies;
- performance superiority outside the named workloads, sizes, software, and
  hardware used for the measurement;
- automatic GitHub release publication by the current qualification workflow.

## 5. Release Identity

Before qualification, the operator must create a release identity record with
these immutable fields:

| Field | Required value |
| --- | --- |
| Package name | `bab-cs` |
| Version | `1.1.0` |
| Tag | `v1.1.0` |
| Final source commit | Full 40-character SHA |
| Expected wheel | `bab_cs-1.1.0-py3-none-any.whl` |
| Python requirement | `>=3.11` |
| Optional sparse dependency | `scipy>=1.11` |
| Optional native sparse library | Compatible SuiteSparse KLU 2 shared library |
| Release workflow | `Release Qualification` |
| Qualification artifact | `bab-cs-release-qualification` |
| Human approver | Named person or authenticated GitHub identity |

The source commit, tag target, `SOURCE_COMMIT`, wheel contents, and publication
record must all identify the same source state.

## 6. Roles and Authority

### 6.1 Candidate author

- Prepares code, tests, documentation, metadata, and proposed baselines.
- May run qualification commands and collect evidence.
- Must not treat their own intent or local success as release approval.

### 6.2 Qualification operator

- Executes the documented commands against the exact release candidate.
- Preserves complete logs, exit codes, hashes, and environment metadata.
- Does not alter expected outputs merely to make a failed run pass.

### 6.3 Evidence reviewer

- Confirms each requirement has direct, current, correctly scoped evidence.
- Reviews numerical threshold or baseline changes semantically.
- Confirms failures, warnings, skips, and comparison deltas are understood.

### 6.4 Release approver

- Is the final authority for tagging and publication.
- Approves one exact source SHA, one exact tag, one exact wheel SHA-256, and one
  immutable evidence manifest.
- Must explicitly reject or defer release when evidence is incomplete.

Models, automation, CI, and scripts may produce or summarize evidence. They do
not provide final release approval.

## 7. Qualification State Machine

The release progresses through the following states in order:

1. `DRAFT`
2. `SOURCE_FROZEN`
3. `LOCAL_QUALIFIED`
4. `ARTIFACT_REPRODUCED`
5. `INSTALLED_QUALIFIED`
6. `COMPARISON_REVIEWED`
7. `EXTERNAL_REVIEWED`
8. `TAG_APPROVED`
9. `TAG_QUALIFIED`
10. `PUBLICATION_APPROVED`
11. `PUBLISHED`
12. `POST_PUBLISH_VERIFIED`

Any source, test, threshold, workflow, manifest, documentation, or build change
after `SOURCE_FROZEN` invalidates downstream states. The candidate returns to
`DRAFT` and receives a new final source SHA.

## 8. Qualification Automation Status

The qualification workflow now resolves exact source/tag/version identity,
installs SciPy and `ngspice`, records environment and GitHub run provenance,
compiles all Python sources, runs dependency-free and SciPy long/very-long
suites, generates numerical and timing reports, verifies the full comparison
matrix, executes all four external mappings, builds the wheel twice, inspects
the retained wheel, qualifies it in a clean environment, compares source and
installed artifacts byte-for-byte, and creates and re-verifies a deterministic
evidence manifest.

The original gaps for optional sparse coverage, independent wheel construction,
installed long tiers, source/installed equivalence, external evidence,
environment recording, and evidence manifests are therefore implemented in
source. `release-evidence-required.txt` is the canonical required-file profile,
and `tools/release_evidence.py` fails closed on missing, duplicate, unexpected,
mismatched, nonfinite, incomplete, or identity-inconsistent evidence.

The remaining original publication gap is intentional. The workflow retains
`contents: read`; it cannot approve a release, create or move a tag, publish a
GitHub release, or prove public asset identity. Those remain exact-hash human
and post-publication gates. Implemented automation is not evidence that a final
release commit has already been qualified.

## 9. Requirement-to-Evidence Matrix

| ID | Requirement | Authoritative evidence | Acceptance rule |
| --- | --- | --- | --- |
| `RQ-001` | Version consistency | Search output, metadata tests, wheel inspection | `1.1.0` appears in every authoritative field; no stale `1.0.0` build identity remains |
| `RQ-002` | Clean source freeze | `git status`, full commit SHA | Worktree clean; SHA recorded before tests and unchanged afterward |
| `RQ-003` | Tag identity | `git rev-parse v1.1.0^{commit}` | Tag resolves exactly to approved release commit |
| `RQ-004` | Source compilation | `compileall` log and exit code | All production, tool, and test Python sources compile |
| `RQ-005` | Full source behavior | Long and very-long `unittest` log | Zero failures/errors and zero unexpected skips |
| `RQ-006` | Optional sparse behavior | SciPy/KLU-installed focused and full logs | Sparse/model/integrator/candidate/nonlinear tests pass with recorded SciPy and KLU versions |
| `RQ-007` | Candidate coverage | `tests/test_candidates.py`, discovery log | Every documented candidate executes through the shared bounded controller |
| `RQ-008` | Bound recurrence | Bound-model tests and numerical report | Reported recurrence is reproducible from emitted metrics |
| `RQ-009` | Independent anchors | Long-horizon tests and comparison metrics | Anchors execute, record pre-reset evidence, and reset history as documented |
| `RQ-010` | Fail-closed behavior | Failure-gate tests | Singular, nonfinite, topology, convergence, and cap failures reject or fall back as specified |
| `RQ-011` | Nonlinear behavior | Nonlinear suite | Diode and switched cases remain finite, residual-qualified, and reference-consistent |
| `RQ-012` | Long-horizon behavior | Ten-, hundred-, and thousand-period tests | Phase, energy, finiteness, and contraction assertions pass |
| `RQ-013` | Deterministic wheel | Two independent wheel files and hashes | Wheel bytes and SHA-256 are identical |
| `RQ-014` | Wheel metadata | Wheel filename, METADATA, WHEEL, dist-info inspection | Name, version, Python requirement, dependency extra, and entry point match source metadata |
| `RQ-015` | Clean installation | Fresh virtual-environment log | Install succeeds with `--no-deps`; `pip check` passes |
| `RQ-016` | Installed behavior | Installed-wheel source-independent test log | Tests import the installed package, not `src`; required suite passes |
| `RQ-017` | Source/installed equivalence | Paired JSON, CSV, SVG, and hashes | Deterministic numerical artifacts are byte-identical |
| `RQ-018` | Comparison completeness | Comparison report summary | Every manifest case/method/control result completes or records an approved fail-closed outcome |
| `RQ-019` | Threshold review | Diff, reviewer record, report deltas | Every changed threshold or expected baseline has a written rationale and human approval |
| `RQ-020` | External mapping | Four ngspice case bundles | Netlists, mappings, tool version, logs, and waveforms reviewed for all four cases |
| `RQ-021` | Performance claim scope | Timing report and release wording | Claims name workload, size, backend, environment, statistic, and comparator |
| `RQ-022` | Provenance completeness | `RELEASE_MANIFEST.json` and `SHA256SUMS` | Every release/evidence file has path, size, SHA-256, role, and source commit |
| `RQ-023` | CI identity | GitHub run URL, event, ref, SHA, conclusion | Tag workflow ran on exact tag/SHA and every required job succeeded |
| `RQ-024` | Human approval | Signed or authenticated approval record | Approval explicitly names source SHA, tag, wheel SHA, manifest SHA, and workflow run |
| `RQ-025` | Published asset identity | Downloaded release assets and fresh hashes | Published wheel/evidence bytes equal approved artifacts |
| `RQ-026` | Post-publish install | Fresh download/install log | Wheel downloaded from release installs and passes smoke tests |

No requirement may be marked satisfied by a narrower test than the requirement's
scope.

## 10. Phase A: Source Freeze and Metadata

### A1. Update version-bearing files

Update `src/babcs/_project.py` as the canonical package identity. Keep
`pyproject.toml` declarative metadata aligned; `build_backend.py` and
`babcs.__version__` derive their identity from the canonical module.

Required search:

```bash
rg -n '1\.0\.0|bab_cs-1\.0\.0' \
  pyproject.toml build_backend.py src README.md RELEASE.md tests
```

Any remaining match must be justified as historical text rather than active
build identity.

### A2. Validate metadata consistency

Run tests that assert:

- the project version equals wheel METADATA version;
- the wheel filename contains that version;
- the `.dist-info` directory contains that version;
- `Requires-Python` matches `pyproject.toml`;
- the `sparse` extra matches `pyproject.toml`;
- the console entry point is `babcs = babcs.cli:main`.

```bash
PYTHONPATH=src python -m unittest tests.test_build_backend -v
```

### A3. Create final source commit

```bash
git diff --check
git status --short --branch
git add -A
git commit -m "Prepare BAB-CS v1.1.0 release"
git push origin main
git rev-parse HEAD
```

Record the full SHA as `FINAL_SOURCE_COMMIT`. No later amendment is allowed
without restarting qualification.

## 11. Phase B: Local Source Qualification

### B1. Record environment

```bash
mkdir -p artifacts/release
source_commit="$(git rev-parse HEAD)"
tag="candidate-${source_commit:0:12}"
created_utc="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
PYTHONPATH=src python tools/release_evidence.py record-environment \
  --output-dir artifacts/release \
  --source-commit "${source_commit}" \
  --tag "${tag}" \
  --created-utc "${created_utc}" \
  --workflow-run-id local \
  --workflow-run-url unavailable \
  --workflow-event local \
  --workflow-ref "$(git symbolic-ref -q HEAD || printf detached)" \
  --workflow-sha "${source_commit}"
```

GitHub Actions supplies the authenticated run ID, URL, event, ref, and exact
checked-out SHA instead of the local placeholders.

### B2. Compile sources

```bash
set -o pipefail
python -m compileall -q -f src tools tests build_backend.py \
  2>&1 | tee artifacts/release/compile.log
```

### B3. Run complete source tests

```bash
set -o pipefail
BABCS_LONG_TESTS=1 BABCS_VERY_LONG_TESTS=1 PYTHONPATH=src \
  python -m unittest discover -s tests -v \
  2>&1 | tee artifacts/release/source-tests.log
```

Record the process exit code. An interrupted run has unknown status and must be
repeated from a confirmed clean process state.

### B4. Run optional SciPy/KLU sparse qualification

Use a clean virtual environment:

```bash
sudo apt-get install --yes libsuitesparse-dev
rm -rf /tmp/babcs-source-scipy
python -m venv /tmp/babcs-source-scipy
{
  /tmp/babcs-source-scipy/bin/python -m pip install --upgrade pip
  /tmp/babcs-source-scipy/bin/python -m pip install 'scipy>=1.11'
} 2>&1 | tee artifacts/release/source-scipy-install.log
/tmp/babcs-source-scipy/bin/python -c \
  'import scipy; print(scipy.__version__)' \
  | tee artifacts/release/SCIPY_VERSION
PYTHONPATH=src /tmp/babcs-source-scipy/bin/python -c \
  'from babcs._klu import klu_version; version = klu_version(); assert version is not None; print(".".join(map(str, version)))' \
  | tee artifacts/release/KLU_VERSION
BABCS_LONG_TESTS=1 BABCS_VERY_LONG_TESTS=1 PYTHONPATH=src \
  /tmp/babcs-source-scipy/bin/python -m unittest discover -s tests -v \
  2>&1 | tee artifacts/release/source-scipy-tests.log
```

## 12. Phase C: Numerical Evidence

### C1. Generate source comparisons

```bash
PYTHONPATH=src python tools/compare_methods.py \
  --output artifacts/release/source-comparison.json \
  --csv-output artifacts/release/source-comparison.csv \
  --plot-output artifacts/release/source-comparison.svg \
  --timing-output artifacts/release/source-timing.json \
  --timing-repeats 3 \
  2>&1 | tee artifacts/release/source-comparison.log
PYTHONPATH=src python tools/release_evidence.py inspect-comparison \
  --report artifacts/release/source-comparison.json \
  --manifest benchmarks/manifest.json \
  --source-commit "$(git rev-parse HEAD)" \
  --timing-report artifacts/release/source-timing.json \
  --output artifacts/release/comparison-inspection.json
```

### C2. Audit comparison coverage

Confirm:

- all declared methods are present;
- all canonical cases are present;
- fixed-timestep, fixed-accuracy, and fixed-work controls are complete;
- common sample times and independent authorities are recorded;
- convergence orders are finite where required;
- oscillator amplitude, phase, period, and energy fields are present;
- candidate/reference, corrected/reference, recursive-bound, and anchor fields
  are present;
- rejected attempts and implicit fallback reasons are represented;
- no target or work budget was silently relaxed;
- timing data is not used as a deterministic qualification gate.

`comparison-inspection.json` must report the complete non-quick matrix with no
missing, duplicate, or unexpected case/method/step/anchor combination and must
bind the numerical and timing reports to the clean expected source commit.

### C3. Review threshold and baseline changes

For every changed numerical threshold or expected artifact:

1. identify the source diff;
2. identify the prior and new numerical result;
3. state why the change is mathematically and physically acceptable;
4. show that unrelated cases did not regress;
5. obtain human review before marking the comparison gate complete.

Regenerating a baseline is not evidence that the new baseline is correct.

## 13. Phase D: External ngspice Evidence

Record the tool version:

```bash
ngspice --version | tee artifacts/release/NGSPICE_VERSION
```

Run every supported mapping:

```bash
for case in rc_step rl_step diode_clip switched_rc; do
  PYTHONPATH=src python tools/compare_external.py \
    "benchmarks/cases/${case}.json" \
    --output "artifacts/release/ngspice-${case}.json" \
    --netlist-output "artifacts/release/ngspice-${case}.cir" \
    --raw-output "artifacts/release/ngspice-${case}.dat" \
    --log-output "artifacts/release/ngspice-${case}.log"
done
```

Review each case for:

- element and waveform semantic equivalence;
- node/state mapping correctness;
- timestep and output-time interpretation;
- event and switch behavior;
- finite waveform error metrics;
- complete raw and log provenance.

The conclusion must remain limited to the mapped cases and settings.

## 14. Phase E: Deterministic Artifact Construction

### E1. Build independently

```bash
rm -rf artifacts/build-a artifacts/build-b
mkdir -p artifacts/build-a artifacts/build-b artifacts/release
python -m pip wheel . --no-deps --wheel-dir artifacts/build-a \
  2>&1 | tee artifacts/release/wheel-build-a.log
python -m pip wheel . --no-deps --wheel-dir artifacts/build-b \
  2>&1 | tee artifacts/release/wheel-build-b.log
cmp artifacts/build-a/bab_cs-1.1.0-py3-none-any.whl \
  artifacts/build-b/bab_cs-1.1.0-py3-none-any.whl
cp artifacts/build-a/bab_cs-1.1.0-py3-none-any.whl artifacts/release/
(
  cd artifacts/release
  sha256sum bab_cs-1.1.0-py3-none-any.whl > WHEEL_SHA256
)
```

### E2. Inspect wheel identity

Inspect without modifying the archive:

```bash
python -m zipfile -l artifacts/release/bab_cs-1.1.0-py3-none-any.whl \
  | tee artifacts/release/WHEEL_CONTENTS
PYTHONPATH=src python tools/release_evidence.py inspect-wheel \
  --wheel artifacts/release/bab_cs-1.1.0-py3-none-any.whl \
  --repository-root . \
  --output artifacts/release/wheel-inspection.json
```

Verify:

- only intended `babcs/*.py` files are present;
- the `.dist-info` directory is `bab_cs-1.1.0.dist-info`;
- METADATA contains version `1.1.0`;
- no source tests, caches, secrets, temporary files, or unrelated artifacts are
  packaged;
- archive member order and timestamps remain deterministic.

The retained wheel in `artifacts/release` becomes the sole release candidate
artifact. Do not rebuild it after approval.

## 15. Phase F: Installed-Wheel Qualification

### F1. Dependency-free installation

```bash
rm -rf /tmp/babcs-release-wheel
python -m venv /tmp/babcs-release-wheel
{
  /tmp/babcs-release-wheel/bin/python -m pip install --no-deps \
    artifacts/release/bab_cs-1.1.0-py3-none-any.whl
  /tmp/babcs-release-wheel/bin/python -m pip check
} 2>&1 | tee artifacts/release/installed-wheel-install.log
```

Confirm import provenance:

```bash
/tmp/babcs-release-wheel/bin/python -c \
  'import babcs; print(babcs.__file__)' \
  | tee artifacts/release/INSTALLED_PACKAGE_PATH
```

The reported path must be inside the clean virtual environment and must not be
the repository `src` directory.

### F2. Installed-wheel tests

```bash
set -o pipefail
BABCS_LONG_TESTS=1 BABCS_VERY_LONG_TESTS=1 \
  /tmp/babcs-release-wheel/bin/python -m unittest discover -s tests -v \
  2>&1 | tee artifacts/release/installed-wheel-tests.log
```

### F3. Installed SciPy/KLU sparse tests

```bash
/tmp/babcs-release-wheel/bin/python -m pip install 'scipy>=1.11' \
  2>&1 | tee artifacts/release/installed-wheel-scipy-install.log
/tmp/babcs-release-wheel/bin/python -c \
  'import scipy; print(scipy.__version__)' \
  | tee artifacts/release/INSTALLED_SCIPY_VERSION
/tmp/babcs-release-wheel/bin/python -c \
  'from babcs._klu import klu_version; version = klu_version(); assert version is not None; print(".".join(map(str, version)))' \
  | tee artifacts/release/INSTALLED_KLU_VERSION
BABCS_LONG_TESTS=1 BABCS_VERY_LONG_TESTS=1 \
  /tmp/babcs-release-wheel/bin/python -m unittest discover -s tests -v \
  2>&1 | tee artifacts/release/installed-wheel-scipy-tests.log
```

### F4. Installed comparisons

```bash
/tmp/babcs-release-wheel/bin/python tools/compare_methods.py \
  --output artifacts/release/installed-wheel-comparison.json \
  --csv-output artifacts/release/installed-wheel-comparison.csv \
  --plot-output artifacts/release/installed-wheel-comparison.svg \
  | tee artifacts/release/installed-wheel-comparison.log
```

### F5. Source/installed equivalence

```bash
PYTHONPATH=src python tools/release_evidence.py compare-artifacts \
  --pair artifacts/release/source-comparison.json=artifacts/release/installed-wheel-comparison.json \
  --pair artifacts/release/source-comparison.csv=artifacts/release/installed-wheel-comparison.csv \
  --pair artifacts/release/source-comparison.svg=artifacts/release/installed-wheel-comparison.svg \
  --output artifacts/release/artifact-comparison.json
```

Any difference requires investigation and a fresh qualification cycle.

## 16. Phase G: Evidence Manifest

Create `artifacts/release/RELEASE_MANIFEST.json` containing:

- schema/version identifier;
- package name and version;
- tag;
- full source commit;
- wheel filename, byte size, and SHA-256;
- every evidence filename, role, byte size, and SHA-256;
- operating-system and platform data;
- Python, pip, SciPy, and ngspice versions;
- source and installed test counts and outcomes;
- comparison result count;
- GitHub workflow run ID and URL when available;
- creation time in UTC;
- qualification status `candidate`, never `approved` before human review.

Use the canonical required-file profile. The tool fails if any required file is
missing, any unexpected file lacks a recognized role, test/comparison summaries
are incomplete, workflow/source identity differs, or wheel inspection and
hashes do not match:

```bash
source_commit="$(cat artifacts/release/SOURCE_COMMIT)"
tag="$(cat artifacts/release/TAG)"
PYTHONPATH=src python tools/release_evidence.py write-manifest \
  --evidence-dir artifacts/release \
  --source-commit "${source_commit}" \
  --tag "${tag}" \
  --wheel bab_cs-1.1.0-py3-none-any.whl \
  --requirements-file release-evidence-required.txt
wheel_sha="$(cut -d ' ' -f 1 artifacts/release/WHEEL_SHA256)"
PYTHONPATH=src python tools/release_evidence.py verify \
  --evidence-dir artifacts/release \
  --source-commit "${source_commit}" \
  --tag "${tag}" \
  --wheel-sha256 "${wheel_sha}"
```

`RELEASE_MANIFEST.json` remains byte-deterministic for identical evidence.
`RELEASE_MANIFEST_SHA256` binds the manifest, and sorted `SHA256SUMS` covers the
manifest, its hash record, and every evidence file while excluding itself.

## 17. Phase H: Human Pre-Tag Review

The evidence reviewer completes a requirement-by-requirement audit and assigns
one status to every `RQ-*` item:

- `PROVEN`
- `CONTRADICTED`
- `INCOMPLETE`
- `MISSING`
- `NOT_APPLICABLE`, with rationale

Only `PROVEN` or justified `NOT_APPLICABLE` items may proceed.

The release approver must record:

```text
I approve creation of tag v1.1.0 for source commit
<FULL_SOURCE_SHA> using wheel
bab_cs-1.1.0-py3-none-any.whl with SHA-256
<WHEEL_SHA256> and evidence manifest SHA-256
<MANIFEST_SHA256>.
```

Approval of a branch name, short SHA, mutable workflow artifact, or approximate
wheel name is insufficient.

## 18. Phase I: Tag Qualification

Create the annotated tag only after pre-tag approval:

```bash
git tag -a v1.1.0 <FULL_SOURCE_SHA> -m "BAB-CS v1.1.0"
git show --no-patch --decorate v1.1.0
git push origin v1.1.0
```

Verify remotely:

```bash
git ls-remote origin refs/tags/v1.1.0 refs/tags/v1.1.0^{}
```

The tag-triggered workflow must:

- use the exact tag and commit;
- complete every required job successfully;
- upload a complete, non-expired evidence artifact;
- produce a wheel whose SHA equals the pre-tag candidate wheel, or else stop and
  investigate why the build environments differ.

If the workflow is changed to become the sole artifact builder, the human
approval must instead occur after the tag workflow and before publication. The
workflow-built wheel then becomes the sole approved artifact.

## 19. Phase J: Publication Approval

After tag qualification, the approver records a second decision:

```text
I approve publication of GitHub release v1.1.0 for source commit
<FULL_SOURCE_SHA>. The exact release wheel SHA-256 is <WHEEL_SHA256>,
the evidence manifest SHA-256 is <MANIFEST_SHA256>, and the approved
GitHub Actions run is <RUN_ID_OR_URL>.
```

No publication action occurs before this statement is recorded.

## 20. Phase K: GitHub Release Publication

Create the release for the exact tag and attach only approved artifacts:

- `bab_cs-1.1.0-py3-none-any.whl`
- `SHA256SUMS`
- `SOURCE_COMMIT`
- `RELEASE_MANIFEST.json`
- `RELEASE_MANIFEST_SHA256`
- source and installed comparison JSON, CSV, and SVG files
- source and installed qualification logs
- environment-version files
- the reviewed release notes

Do not:

- rebuild the wheel during publication;
- replace an approved asset with a same-named different file;
- move or recreate the tag;
- omit failed or contradictory evidence from the review bundle;
- describe benchmark-only work as released functionality.

## 21. Phase L: Post-Publication Verification

Download the public assets into a fresh directory and verify them independently:

```bash
sha256sum --check SHA256SUMS
```

Create a fresh environment, install the downloaded wheel, and run at minimum:

```bash
python -m venv /tmp/babcs-public-release
/tmp/babcs-public-release/bin/python -m pip install --no-deps \
  bab_cs-1.1.0-py3-none-any.whl
/tmp/babcs-public-release/bin/python -m pip check
/tmp/babcs-public-release/bin/babcs --help
```

Confirm:

- public tag resolves to the approved source commit;
- downloaded wheel hash equals the approved hash;
- manifest hash equals the approved hash;
- release notes contain the final commit, wheel hash, workflow, environment,
  and claim boundaries;
- no unapproved or duplicate wheel is attached.

Mark the release `POST_PUBLISH_VERIFIED` only after these checks pass.

## 22. Failure and Rollback Policy

### 22.1 Before tag creation

- Fix the source or evidence problem on `main`.
- Create a new source commit.
- Discard all downstream qualification state and artifacts.
- Restart from `SOURCE_FROZEN` with the new SHA.

### 22.2 After tag creation but before publication

If qualification fails, do not publish. Prefer leaving an auditable failed tag
record and creating a new patch candidate/tag after correction. If project
policy permits deleting an unpublished erroneous tag, record the deletion and
never reuse the tag for different source without explicit reviewer approval.

### 22.3 After publication

- Do not replace the wheel silently.
- Do not force-move the tag.
- Mark the release as affected or deprecated when necessary.
- Publish a corrective patch release from a new commit and new tag.
- Use `git revert` for source rollback rather than rewriting published history.
- Preserve the original release assets and evidence for auditability.

### 22.4 Compromised or mismatched artifact

If a published asset hash differs from the approved hash:

1. stop recommending or distributing the release;
2. preserve downloaded evidence of the mismatch;
3. restrict or remove the compromised asset when authorized;
4. document the incident;
5. rotate affected credentials if compromise is suspected;
6. rebuild and qualify from a new source commit and version.

## 23. Evidence Retention

Release evidence must be retained outside short-lived Actions storage. Preserve:

- release assets on GitHub;
- the final approval record;
- workflow run URL and identifiers;
- full logs and environment metadata;
- source and installed comparison artifacts;
- ngspice bundles;
- wheel and manifest hashes;
- the requirement-to-evidence audit.

Actions artifact expiration must not make the release unverifiable.

## 24. Qualification Report Template

```text
BAB-CS Release Qualification Report

Package: bab-cs
Version: 1.1.0
Tag: v1.1.0
Source commit: <FULL_SHA>
Wheel: bab_cs-1.1.0-py3-none-any.whl
Wheel SHA-256: <SHA256>
Manifest SHA-256: <SHA256>
Workflow run: <URL_OR_ID>
Python: <VERSION>
SciPy: <VERSION>
ngspice: <VERSION>

Source tests: <COUNT>, <RESULT>
Installed tests: <COUNT>, <RESULT>
Installed SciPy tests: <COUNT>, <RESULT>
Comparison results: <COUNT>, <RESULT>
External cases: rc_step, rl_step, diode_clip, switched_rc

Requirements proven: <COUNT>/26
Contradicted: <COUNT>
Incomplete: <COUNT>
Missing: <COUNT>

Threshold changes reviewed: <YES/NO>
Baseline changes reviewed: <YES/NO>
Source/installed artifacts identical: <YES/NO>
Wheel builds byte-identical: <YES/NO>
Published assets verified: <YES/NO>

Qualification decision: <APPROVE/REJECT/DEFER>
Reviewer: <IDENTITY>
Approval record: <REFERENCE>
```

## 25. Final Gate Checklist

### Source and identity

- [ ] `1.1.0` is consistent across project and wheel metadata.
- [ ] Final source commit is clean, pushed, and recorded by full SHA.
- [ ] Release tag resolves exactly to that source commit.
- [ ] No source changes occurred after qualification began.

### Tests and numerical behavior

- [ ] Production and test sources compile.
- [ ] Full source suite passes with long and very-long tiers.
- [ ] Optional SciPy source suite passes.
- [ ] Installed-wheel full suite passes.
- [ ] Installed-wheel SciPy suite passes.
- [ ] Candidate, bound, failure, nonlinear, and long-horizon coverage is present.
- [ ] Numerical comparison matrix is complete.
- [ ] Changed thresholds and baselines have human review.
- [ ] All four ngspice mappings are reviewed.

### Artifact integrity

- [ ] Independent wheel builds are byte-identical.
- [ ] Wheel contents and metadata are correct.
- [ ] Installed import provenance points to the clean environment.
- [ ] Source and installed deterministic artifacts are byte-identical.
- [ ] Environment versions are recorded.
- [ ] `RELEASE_MANIFEST.json` covers every evidence and release file.
- [ ] `SHA256SUMS` and manifest hash are recorded.

### Approval and publication

- [ ] All 26 requirements are proven or justified not applicable.
- [ ] Pre-tag human approval names exact SHA and hashes.
- [ ] Tag workflow succeeds for the exact tag and commit.
- [ ] Publication approval names exact SHA, tag, wheel hash, manifest hash, and
      workflow run.
- [ ] GitHub release contains only exact approved assets.
- [ ] Publicly downloaded assets pass checksum and installation verification.
- [ ] Evidence has durable retention beyond Actions artifact expiry.

The release is qualified only when every applicable checkbox is complete and
the final authenticated human decision is `APPROVE`.
