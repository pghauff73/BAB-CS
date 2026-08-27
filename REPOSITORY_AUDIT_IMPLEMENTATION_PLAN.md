# Bounded-Authority-Based-Circuit-Simulation Repository Audit Implementation Plan

## Status

Implementation started on August 27, 2026 against local `HEAD`
`dd8145eb170c00db752dad239b0e295a37b2f2de` with an intentionally dirty
working tree containing validated post-`HEAD` solver, root-finding, test, and
documentation changes.

Initial live GitHub inspection confirmed that:

- `main` resolved to `dd8145eb170c00db752dad239b0e295a37b2f2de`;
- `main` was not protected and the repository had no rulesets;
- the latest public release is `v1.0.0`;
- the authenticated owner has repository administration permission.

During implementation, the owner advanced live `main` to
`2eab2dc2306a7ccd9e034b2f1343d1afd559dd22` and selected the Mozilla Public
License 2.0. The local implementation preserves that authority, corrects the
licence file to Mozilla's canonical text, and adds SPDX/PEP 639 package
metadata. The owner also selected the public name
`Bounded-Authority-Based-Circuit-Simulation`; stable Python identifiers remain
unchanged for compatibility.

Implementation subsequently applied and read back `main` protection, active
`v*` release-tag ruleset `21646558`, private vulnerability reporting, and the
documented repository topics. The applied state is recorded in
`docs/GITHUB_GOVERNANCE.md`.

This plan does not reinterpret a dirty tree as a frozen release candidate. A
release candidate exists only after the complete intended tree is committed and
one exact full SHA is selected.

## Objective

Implement the repository-audit recommendations that can be made authoritative
in source, automate facts that currently drift in prose, prepare and apply
appropriate repository governance controls, implement the owner's explicit
name and licence decisions, and leave tagging, publication, and exact-hash
approval explicitly human-controlled.

## Requirements

### RA-1: Exact-release qualification boundary

1. Preserve the existing release sequence: freeze, ordinary CI, manually
   dispatched exact-SHA qualification, independent evidence verification,
   requirement-by-requirement human review, annotated tag, tag qualification,
   publication approval, exact-byte publication, and public-download
   verification.
2. Do not tag, publish, or claim `v1.1.0` qualified from the current dirty tree.
3. Add machine-readable qualification summary evidence so the selected commit,
   package identity, test surface, method surface, benchmark surface, Python
   versions, workflow identity, and latest public release are captured by the
   workflow rather than copied manually.

### RA-2: Repository and tag protection

1. Protect `main` against force pushes and deletion.
2. Require current CI status checks before protected updates.
3. Require pull-request review flow without requiring a second approving person
   for solo maintenance.
4. Require conversation resolution and include administrators where supported.
5. Protect `v*` tags from update and deletion.
6. Record the exact live settings after application.

### RA-3: Licence authority

1. Do not select a licence automatically.
2. Record the owner's exact licence decision and authority.
3. Provide a short owner decision record covering permissive, reciprocal,
   source-visible reserved, and dual-licence options.
4. Add the chosen licence only after the owner makes that legal/commercial
   decision.

### RA-4: Qualification-summary automation

1. Generate deterministic JSON from repository and workflow evidence.
2. Count tests from Python syntax rather than manually maintained prose.
3. Count bounded candidate methods and benchmark cases/configurations from
   their canonical source files.
4. Record package version, wheel filename, Python requirement, CI Python
   versions, exact commit, dirty state, workflow run identity, candidate tag,
   and latest public release.
5. Include the summary in the required release-evidence profile, manifest, and
   tamper-verification path.
6. Add focused tests for determinism, source counting, invalid inputs, and
   manifest recognition.

### RA-5: Public research envelope

1. Add `CITATION.cff` without inventing a DOI or release approval.
2. Add `SECURITY.md` with a private-reporting path and supported-version policy.
3. Add `CONTRIBUTING.md` with deterministic validation and claim-boundary rules.
4. Add issue templates for defects, numerical-evidence reports, and research
   proposals.
5. Add `CHANGELOG.md` separating `v1.0.0` from unreleased `1.1.0` work.
6. Add a concise architecture diagram using repository-native Markdown/Mermaid.
7. Add a minimal reproducible RC research walkthrough using an existing
   deterministic example.
8. Add repository topics after confirming the exact topic set.
9. Treat DOI archival as a post-qualification publication task; do not fabricate
   an archive identifier.

## File Plan

- `tools/release_evidence.py`: qualification-summary construction and CLI.
- `tests/test_release_evidence.py`: summary and evidence-profile coverage.
- `.github/workflows/release-qualification.yml`: generate summary evidence.
- `release-evidence-required.txt`: require the summary artifact.
- `CITATION.cff`: citation metadata for the software and current unreleased
  version.
- `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`: governance and public-use
  policy.
- `.github/ISSUE_TEMPLATE/`: structured issue forms.
- `docs/ARCHITECTURE.md`: concise authority-flow diagram.
- `docs/MINIMAL_REPRODUCIBLE_RESEARCH.md`: deterministic RC walkthrough.
- `docs/LICENCE_DECISION.md`: explicit owner decision gate.
- `docs/QUALIFICATION_SUMMARY.md`: generated-field definitions and usage.
- `README.md`, `docs/index.md`, `RELEASE.md`, `docs/CURRENT_WORK.md`: links and
  claim-boundary alignment.

## Implementation Sequence

### Phase 1: Evidence automation

1. Define qualification-summary schema and canonical field owners.
2. Implement source/test/benchmark/workflow discovery.
3. Add CLI generation and workflow integration.
4. Add the artifact to the required evidence profile and manifest roles.
5. Add deterministic and failure-path tests.

### Phase 2: Public repository envelope

1. Add citation, security, contribution, changelog, and issue-template files.
2. Add architecture and minimal-reproduction documentation.
3. Add the licence decision record without choosing a licence before owner
   authority exists; after selection, package the canonical text and metadata.
4. Link the new material from the README and documentation index.

### Phase 3: Live governance controls

1. Discover exact current CI check names from GitHub.
2. Apply a solo-maintainer-compatible `main` protection configuration.
3. Apply a `v*` tag ruleset if the repository plan/API supports it.
4. Enable private vulnerability reporting if available.
5. Apply a conservative, research-specific topic set.
6. Read back every setting and record the result.

### Phase 4: Validation and completion audit

1. Run focused release-evidence and governance-file checks.
2. Run the complete default test suite.
3. Run deterministic qualification-summary generation twice and compare bytes.
4. Build and inspect the wheel.
5. Audit RA-1 through RA-5 against current source and live GitHub state.
6. Keep exact-SHA qualification, human approval, tagging, DOI archival, and
   publication explicitly pending unless separately approved and evidenced.

## Completion Criteria

Repository implementation is complete when:

- the qualification summary is generated, required, manifested, and tested;
- public citation, security, contribution, issue, changelog, architecture, and
  reproducibility material exists and is linked;
- `main` and `v*` protection plus private reporting and topics are applied or a
  precise platform limitation is evidenced;
- the full default suite and deterministic artifact checks pass;
- no source file claims that the dirty tree or an unreviewed commit is release
  qualified;
- the remaining freeze, qualification, tag, approval, DOI, and publication
  gates are named as pending human/external actions rather than silently treated
  as complete.

## Implementation Audit — August 27, 2026

| Requirement | Implemented evidence | Remaining authority |
| --- | --- | --- |
| RA-1 exact-release boundary | Existing ordered release sequence retained; generated qualification surface added; no tag or publication claim made | Select the final clean commit, run ordinary CI and exact-SHA qualification, review `RQ-001` through `RQ-022`, tag, requalify, approve, publish, and verify public bytes |
| RA-2 repository protection | Strict `main` checks, pull-request flow, administrator enforcement, conversation resolution, force-push/deletion denial, active `v*` tag ruleset `21646558`, private vulnerability reporting, and topics applied and read back | Re-read mutable GitHub settings before release |
| RA-3 licence authority | Owner selected MPL-2.0 at `2eab2dc2306a7ccd9e034b2f1343d1afd559dd22`; canonical Mozilla text, SPDX metadata, CFF metadata, and wheel licence inclusion implemented | Requalify the changed source and wheel bytes |
| RA-4 qualification summary | Deterministic summary generation, canonical source discovery, workflow integration, required evidence role, manifest validation, and focused tests implemented | Generate the retained artifact in exact-SHA qualification |
| RA-5 public research envelope | Citation, security, contribution, issue, changelog, architecture, reproducibility, governance, topic, and licence records implemented | Create a DOI-backed archive only after approved publication |

Pre-commit local validation passed:

- focused build, release-evidence, and CLI suite: 23 tests;
- complete default suite: 246 tests passed, with 2 intentional skips;
- deterministic double wheel build: byte-identical;
- wheel inspection: 19 members, Core Metadata 2.4, `MPL-2.0`, canonical
  `LICENSE` bytes, and installed CLI smoke with 500 accepted steps;
- canonical licence SHA-256:
  `3f3d9e0024b1921b067d6f7f88deb4a60cbe7a78e76c64e3f1d7fc3b779b9d04`;
- deterministic wheel SHA-256:
  `f431ea7e2abd58736b475b9c3d474deef7a3a2b201e2ddc8e22b5c34ca88dce4`;
- JSON, YAML, TOML, bytecode compilation, minimal reproducibility, and
  whitespace checks passed.

These results validate the local implementation state. They do not replace the
post-push CI run or the exact-commit release qualification workflow.
