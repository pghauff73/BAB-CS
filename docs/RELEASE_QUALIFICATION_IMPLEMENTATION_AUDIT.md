# Bounded-Authority-Based-Circuit-Simulation Release Qualification Implementation Audit

Audit date: August 24, 2026

## Scope

This audit evaluates the repository implementation of
`BAB-CS-Release-Qualification-Plan.md`. It does not approve `v1.1.0`, select a
final source commit, authorize a tag, publish a GitHub release, or treat local
implementation validation as release qualification.

The implementation boundary is deliberate:

- automation may build, test, inspect, hash, compare, summarize, and verify;
- the evidence manifest status is always `candidate`;
- threshold and mapping review remain semantic human decisions;
- tag creation and publication require exact-hash human approval; and
- public asset identity and installation are post-publication observations.

## Implementation Requirements

### IP-1 — Canonical package metadata: Implemented

- `src/babcs/_project.py` owns distribution name, package name, version,
  summary, Python requirement, sparse extra, wheel tag, and console entry point.
- `build_backend.py` derives wheel and `.dist-info` identity plus METADATA,
  WHEEL, and entry-point content from that module.
- `src/babcs/__init__.py` exports the same version as `babcs.__version__`.
- `pyproject.toml` declares `1.1.0`, with consistency enforced by
  `tests/test_build_backend.py`.

### IP-2 — Deterministic evidence manifest: Implemented

- `tools/release_evidence.py` records environment and workflow identity,
  validates exact source/tag binding, inspects wheels, validates the complete
  comparison matrix, compares artifacts byte-for-byte, parses successful test
  and comparison summaries, writes deterministic manifests and checksums, and
  reconstructs the manifest during verification.
- `release-evidence-required.txt` is the canonical complete-bundle profile.
- Duplicate requirements, missing files, unexpected roles, modified or
  unlisted files, nonfinite JSON, failed test summaries, incomplete comparison
  matrices, mismatched workflow/source SHAs, and incorrect wheel identity fail
  closed.
- The tool cannot emit an `approved` manifest.

### IP-3 — Qualification workflow closure: Implemented

`.github/workflows/release-qualification.yml` now:

- validates exact `v<package-version>` tags and exact candidate/SHA prefixes;
- supports non-publishing manual candidate runs;
- installs SciPy, SuiteSparse KLU, and `ngspice`;
- records UTC creation time, OS, platform, Python, pip, SciPy, KLU, `ngspice`,
  and GitHub workflow identity;
- compiles production, tool, test, and backend sources;
- runs dependency-free and SciPy/KLU long/very-long source suites;
- generates numerical and timing evidence and inspects the full matrix;
- runs all four external mappings;
- builds the wheel twice and compares exact bytes;
- inspects and retains one exact wheel;
- performs dependency-free and SciPy/KLU installed-wheel qualification;
- compares source and installed JSON, CSV, and SVG bytes;
- writes and re-verifies the complete evidence manifest; and
- uploads the evidence with 90-day Actions retention while retaining
  `contents: read` and performing no publication.

### IP-4 — CI and tests: Implemented

- Normal CI compiles `build_backend.py` with source, tests, and tools.
- Normal unittest discovery includes metadata and release-evidence tests.
- `tests/test_release_evidence.py` uses temporary directories and covers
  deterministic output, checksum ordering, wheel identity, exact
  source/candidate binding, complete comparison matrices, artifact equality,
  missing and duplicate requirements, unexpected files, modified evidence,
  nonfinite JSON, failed test logs, workflow SHA mismatch, and the canonical
  required-file profile.

### IP-5 — Documentation alignment: Implemented

- `README.md` documents canonical identity, the complete workflow, evidence
  tooling, required-file profile, and non-publication boundary.
- `RELEASE.md` describes the current `1.1.0` candidate and exact lifecycle from
  frozen commit through public-download verification.
- `BAB-CS-Release-Qualification-Plan.md` uses the implemented commands and no
  longer describes resolved workflow gaps as current deficiencies.
- This audit maps every `RQ-*` requirement to implementation and remaining
  execution authority.

## Release Requirement Matrix

The `Implementation` column evaluates whether the repository now contains a
correctly scoped mechanism for the requirement. The `Release evidence` column
states what is still required for an actual `v1.1.0` decision.

| ID | Implementation | Direct implementation evidence | Release evidence state |
| --- | --- | --- | --- |
| `RQ-001` | Implemented | `src/babcs/_project.py`, `build_backend.py`, `pyproject.toml`, `tests/test_build_backend.py`, wheel inspection | Pending final frozen-commit search, test log, and retained-wheel inspection |
| `RQ-002` | Implemented with operator gate | Workflow records full checked-out SHA; comparison inspection rejects dirty source; manifest binds workflow and source SHA | Pending selection of one clean pushed final SHA and proof it remained unchanged |
| `RQ-003` | Implemented with human gate | `validate_release_identity` accepts only `v1.1.0` or exact `candidate-<SHA-prefix>` identity | Pending annotated tag creation after approval and remote tag resolution |
| `RQ-004` | Implemented | Workflow writes `compile.log` from forced `compileall` over `src`, `tests`, `tools`, and `build_backend.py` | Pending final exact-commit workflow log |
| `RQ-005` | Implemented | Workflow enables both long tiers; manifest parser requires one successful unittest summary | Pending final source test log and reviewer confirmation of skips |
| `RQ-006` | Implemented | Clean SciPy environment, installed system KLU, recorded versions, install log, and full source suite | Pending final SciPy/KLU source evidence |
| `RQ-007` | Implemented | `tests/test_candidates.py`, comparison manifest, complete-matrix inspector | Pending final discovery and comparison reports |
| `RQ-008` | Implemented | `tests/test_bound_model.py` reconstructs recurrence; comparison reports retain bound metrics | Pending final test and numerical evidence |
| `RQ-009` | Implemented | BAB-CS and long-horizon tests cover replay, pre-reset evidence, history rebuild, and reset; comparison metrics retain anchors | Pending final test and comparison evidence |
| `RQ-010` | Implemented | `tests/test_failure_gates.py`, model/integrator boundary tests, and fail-closed evidence verification | Pending final suite log |
| `RQ-011` | Implemented | `tests/test_nonlinear.py` and external diode/switch cases | Pending final source, installed, and external evidence review |
| `RQ-012` | Implemented | `tests/test_long_horizon.py` includes ten-, hundred-, and thousand-period cases | Pending final long/very-long logs |
| `RQ-013` | Implemented | Deterministic backend test plus workflow double build, byte comparison, retained hash, and manifest binding | Pending two wheel files and hashes from the final commit |
| `RQ-014` | Implemented | Canonical metadata tests and `inspect-wheel` validate filename, members, METADATA, WHEEL, entry point, timestamps, and modes | Pending retained final-wheel inspection |
| `RQ-015` | Implemented | Workflow creates a fresh venv and records `--no-deps` installation plus `pip check` in `installed-wheel-install.log` | Pending final installation log |
| `RQ-016` | Implemented | Workflow records `INSTALLED_PACKAGE_PATH` and runs full installed-wheel long tiers without `PYTHONPATH=src` | Pending final installed-wheel logs and provenance review |
| `RQ-017` | Implemented | `compare-artifacts` requires byte equality for source/installed JSON, CSV, and SVG and records `artifact-comparison.json` | Pending final paired artifacts |
| `RQ-018` | Implemented | `inspect-comparison` derives every expected case/method/step/anchor key from `benchmarks/manifest.json`, rejects omissions/duplicates, and checks analysis sections | Pending final `comparison-inspection.json` and semantic report review |
| `RQ-019` | Evidence support implemented; approval cannot be automated | Deterministic reports, source diff, retained thresholds, hashes, and manifest support review | Pending human rationale and approval for every changed threshold or baseline |
| `RQ-020` | Evidence generation implemented; semantic review remains human | Workflow produces JSON, netlist, raw waveform, and log bundles for all four cases and records `ngspice` version | Pending exact-commit execution and human mapping/waveform review |
| `RQ-021` | Implemented with claim-review gate | Separate `source-timing.json`, recorded environment, scoped wording in `RELEASE.md`, and no timing correctness gate | Pending final timing report and human confirmation that each published claim names workload, size, backend, environment, statistic, and comparator |
| `RQ-022` | Implemented | Canonical required-file profile; deterministic manifest records path, role, size, hash, package/source identity, environment, workflow, tests, and comparisons; manifest hash and checksums bind control files | Pending final complete bundle and independent verification |
| `RQ-023` | Implemented; tag execution pending | Workflow records run ID, URL, event, ref, and exact checked-out SHA; manifest requires and verifies them | Pending successful tag-triggered run for exact `v1.1.0` commit |
| `RQ-024` | Human-only authority | Plan and release draft define exact SHA, tag, wheel hash, manifest hash, and workflow-run approval text; tooling never synthesizes approval | Pending authenticated human approval record |
| `RQ-025` | Publication and observation gate | Procedure forbids rebuild/replacement and requires exact approved assets | Pending publication approval, release creation, download, and fresh hash comparison |
| `RQ-026` | Post-publication observation gate | Procedure specifies fresh downloaded-wheel environment, `pip check`, and CLI smoke | Pending public release and fresh download/install log |

## Release-State Conclusion

The implementation can produce and independently verify the evidence required
through candidate and tag qualification. It correctly leaves semantic review,
approval, tagging, publication, durable retention, public checksum comparison,
and public installation outside automation authority.

Therefore the qualification implementation can be complete while the proposed
release remains `DRAFT`. No `RQ-*` item that requires a final frozen commit,
human decision, tag-triggered run, published asset, or public download is marked
`PROVEN` by this document.
