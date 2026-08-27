# Bounded-Authority-Based-Circuit-Simulation Release Qualification Implementation Plan

## Status

- **Target specification:** `BAB-CS-Release-Qualification-Plan.md`
- **Implementation status:** Implemented; this does not qualify or approve the
  proposed release
- **Initial implementation commit:**
  `41782a67a12be4483ab490041e2aed4fa5692990`
- **Proposed package version:** `1.1.0`
- **Tagging/publication:** explicitly excluded from implementation authority;
  both remain exact-hash human-approved actions

## Objective

Implement the repository-owned machinery needed to execute the release
qualification plan reproducibly. The implementation must close the documented
workflow gaps, centralize release identity, generate deterministic provenance,
verify artifacts, and expose direct tests for the qualification contract.

## Non-Goals

- Do not create or push `v1.1.0`.
- Do not create a GitHub release.
- Do not upload or replace release assets.
- Do not mark the release approved.
- At the time of this implementation plan, do not implement the benchmark-only
  ULP-aware sensitivity-age policy. That historical scope boundary was later
  superseded by a separately tested and requalified implementation on August
  25, 2026; it does not alter the plan's tagging or publication non-authority.
- Do not convert empirical bound characterization into a formal coverage claim.

## Requirements

### IP-1: Canonical package metadata

1. Add one repository-owned metadata module containing package name, version,
   summary, Python requirement, optional sparse requirement, wheel tag, and
   console entry point.
2. Make `build_backend.py` derive METADATA, wheel filename, and `.dist-info`
   identity from that module.
3. Expose `babcs.__version__` from the same canonical version.
4. Set the candidate package version to `1.1.0` without creating a tag.
5. Add tests proving `pyproject.toml`, canonical metadata, wheel filename,
   METADATA, `.dist-info`, and entry point agree.

### IP-2: Deterministic evidence manifest

1. Add `tools/release_evidence.py` with commands to:
   - write environment/provenance files;
   - inspect and verify a wheel;
   - compare source and installed artifacts byte-for-byte;
   - validate the complete case/method/step/anchor comparison matrix;
   - build a deterministic `RELEASE_MANIFEST.json`;
   - build `SHA256SUMS` without self-inclusion;
   - verify a completed evidence directory against expected version, source
     commit, tag, and wheel hash.
2. Manifest entries must contain relative path, role, size, and SHA-256.
3. Manifest output must be byte-deterministic for identical inputs.
4. The manifest status remains `candidate`; tooling must not synthesize human
   approval.
5. Verification must fail closed on missing, duplicate, mismatched, unlisted,
   nonfinite, failed-test, incomplete-comparison, or workflow/source-identity
   evidence.

### IP-3: Qualification workflow closure

Update `.github/workflows/release-qualification.yml` to:

1. require an exact `v<package-version>` tag for tag-triggered runs;
2. support manual workflow dispatch for candidate evidence without publication;
3. install SciPy and ngspice;
4. record OS, Python, pip, SciPy, and ngspice versions;
5. compile source and tools;
6. run full long and very-long source tests with SciPy available;
7. generate source comparisons;
8. run all four external ngspice cases;
9. build the wheel twice and compare bytes;
10. inspect wheel identity and contents;
11. install the exact retained wheel into a clean environment;
12. run full long and very-long installed-wheel tests;
13. generate installed-wheel comparisons;
14. compare source and installed JSON, CSV, and SVG artifacts byte-for-byte;
15. generate and verify the evidence manifest and checksums;
16. upload the complete evidence set with extended retention;
17. retain `contents: read` and perform no release publication.

### IP-4: CI and test coverage

1. Run canonical metadata and release-evidence tests in normal CI.
2. Add unit tests for deterministic manifest generation, checksum ordering,
   wheel validation, version/tag validation, artifact equality, missing-file
   rejection, and unexpected-file rejection.
3. Keep tests dependency-free unless they are explicitly optional-SciPy or
   external-ngspice tests.
4. Ensure tests operate in temporary directories and do not alter repository
   evidence.

### IP-5: Documentation alignment

1. Update `RELEASE.md` to reference canonical metadata and implemented tooling.
2. Update `BAB-CS-Release-Qualification-Plan.md` where commands are replaced by
   repository tooling.
3. Update `README.md` qualification automation notes.
4. Add a completion audit mapping `RQ-001` through `RQ-026` to implemented
   sources and remaining execution-time evidence.
5. Distinguish implemented qualification infrastructure from an actually
   qualified or approved release.

## File Plan

| File | Change |
| --- | --- |
| `src/babcs/_project.py` | Add canonical distribution metadata usable by the backend, package, tests, and tools |
| `pyproject.toml` | Set `1.1.0` and keep values aligned with canonical metadata tests |
| `build_backend.py` | Derive wheel and METADATA identity from canonical metadata |
| `src/babcs/__init__.py` | Export `__version__` |
| `tools/release_evidence.py` | Implement provenance, wheel, manifest, checksum, comparison, and verification commands |
| `release-evidence-required.txt` | Declare the complete evidence bundle once for workflow and manual execution |
| `tests/test_build_backend.py` | Expand package metadata and wheel identity coverage |
| `tests/test_release_evidence.py` | Add deterministic and fail-closed qualification-tool tests |
| `.github/workflows/ci.yml` | Include release-evidence tooling tests in normal qualification |
| `.github/workflows/release-qualification.yml` | Implement the complete exact-artifact qualification pipeline |
| `README.md` | Document the implemented release tooling and non-publication boundary |
| `RELEASE.md` | Replace manual duplicated commands with canonical tool invocations where appropriate |
| `BAB-CS-Release-Qualification-Plan.md` | Align the executable procedure with implemented commands |
| `docs/RELEASE_QUALIFICATION_IMPLEMENTATION_AUDIT.md` | Record requirement-to-source and requirement-to-test evidence |

## Implementation Sequence

### Phase 1: Metadata authority

1. Create canonical metadata.
2. Refactor the wheel backend.
3. Export runtime version.
4. Update version to `1.1.0`.
5. Add metadata consistency tests.

**Gate:** two wheel builds are byte-identical and every version-bearing output
is `1.1.0`.

### Phase 2: Evidence tool

1. Define manifest schema and deterministic JSON encoding.
2. Implement SHA-256 and evidence-role collection.
3. Implement environment and source provenance recording.
4. Implement wheel inspection and identity validation.
5. Implement source/installed artifact comparison.
6. Implement manifest/checksum verification.
7. Add dependency-free unit tests.

**Gate:** focused tests prove deterministic output and fail-closed behavior for
all declared mismatch classes.

### Phase 3: Workflow integration

1. Install optional and external dependencies.
2. Run source qualification and comparisons.
3. Run ngspice evidence.
4. Build and compare two wheels.
5. Qualify the installed retained wheel.
6. Generate, verify, and upload the complete evidence set.

**Gate:** workflow syntax is valid, command paths exist, and local equivalents
complete successfully where the environment supports them.

### Phase 4: Documentation and audit

1. Replace duplicated or stale release commands.
2. Document exact inputs and outputs of release tooling.
3. Map all 26 qualification requirements to implementation evidence.
4. Identify requirements that remain execution-time or human-approval gates.

**Gate:** no document claims that infrastructure implementation equals release
qualification, tagging, approval, or publication.

### Phase 5: Full validation

1. Run `git diff --check`.
2. Run focused metadata and evidence-tool tests.
3. Run the complete source test suite.
4. Run long and very-long tests.
5. Build two wheels and compare bytes.
6. Install the retained wheel and run installed tests.
7. Generate a temporary source/installed comparison pair and verify equality.
8. Generate and verify a temporary release manifest.
9. Audit `RQ-001` through `RQ-026` against current source.

**Gate:** all implementation requirements are proven; release-execution and
human-approval requirements remain explicitly pending rather than falsely
completed.

## Completion Criteria

Implementation is complete when:

- every `IP-*` requirement has direct source and test evidence;
- the normal CI and release workflow reference only existing commands;
- version metadata cannot diverge silently;
- release evidence is deterministic and independently verifiable;
- exact tag/source/wheel mismatches fail closed;
- the full current source suite passes;
- an installed candidate wheel passes qualification;
- source and installed comparison artifacts match;
- the completion audit classifies all `RQ-*` requirements accurately; and
- no tag, approval, or publication has been performed without the required
  human exact-hash gate.
