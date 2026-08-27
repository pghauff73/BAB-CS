# Observatory, Atlas, Sandbox, and Lab Implementation Audit

## Audit Status

This audit records the implementation and development qualification state on
August 27, 2026. It covers
`OBSERVATORY_ATLAS_SANDBOX_LAB_IMPLEMENTATION_PLAN.md` and distinguishes
implemented functionality from release promotion.

The automated implementation is complete. The current worktree is dirty, so
the wheel and source/wheel results below are explicitly development evidence,
not release evidence. No exact commit has been selected, no human has approved
the exact source and wheel hashes, and no publication authority is implied.

## Evidence Snapshot

| Field | Value |
| --- | --- |
| Git `HEAD` | `c280b885ce54205805a9046a98430948498a73d9` |
| Source-tree SHA-256 | `74ccc39a853f3410f898a6550268eb85136b58045dba5966907dedcfb1c41657` |
| Source scope | 141 tracked or untracked non-ignored files, excluding generated evidence and evidence-only audit documents |
| Dirty state | `true`; development evidence only |
| Python | CPython 3.14.6 |
| Platform | Linux 7.1.3-2-cachyos, x86-64, glibc 2.43 |
| Optional backends | SciPy available; SuiteSparse KLU available |
| Test surface | 276 test methods in 25 modules |
| Complete suite | 276 passed, zero skipped, 64.203 seconds |

The complete suite ran with both `BABCS_LONG_TESTS=1` and
`BABCS_VERY_LONG_TESTS=1`, so it included the 1,000-period LC qualification as
well as the available SciPy and KLU tests. `compileall` and strict JSON parsing
also passed.

## Requirement-to-Evidence Matrix

| Requirement | Implementation owner | Deterministic verification | Status |
| --- | --- | --- | --- |
| Shared versioned experiment records, stable row IDs, reason taxonomy, applicability, fixed-accuracy and fixed-work selection | `tools/experiment_records.py`, `benchmarks/schemas/` | `tests/test_experiment_records.py`, comparison compatibility tests | Implemented and passed |
| RC, RL, RLC, LC, diode clip, and switched RC across all seven candidates | `benchmarks/observatory/manifest.json`, `tools/method_observatory.py` | 126 expected rows, 126 actual rows, 126 successful rows, no missing, duplicate, or unexpected rows | Implemented and passed |
| Fixed-step, fixed-accuracy, and fixed-work reports without interpolation | Observatory JSON/CSV/SVG/Markdown writers | Every selected summary links to a measured `row_id`; `no_qualifying_row` remains explicit | Implemented and passed |
| Actual authority error, recursive internal bound, anchor deviation, phase, energy, empirical coverage, fallback, and rejection causes | `tools/bound_coverage_atlas.py`, `benchmarks/atlas/manifest.json` | 87,874 accepted samples, 3,934 anchors, 3,040 cause records; exact diagnostic/work reconciliation | Implemented and passed |
| Simplified buck-like converter | `examples/power_stage/buck_like_reduced_order.json` | Event, continuity, residual, energy, authority, determinism, refined-authority, and installed-wheel checks | Implemented and passed |
| Scheduled H-bridge RL load | `examples/power_stage/h_bridge_rl_reduced_order.json` | Dead time, no leg overlap, polarity reversal, event/replay, residual, determinism, refined-authority, and installed-wheel checks | Implemented and passed |
| DC-link RLC startup and interruption | `examples/power_stage/dc_link_rlc_reduced_order.json` | Startup/interruption events, diode conduction, post-interrupt energy decay, residual, determinism, refined-authority, and installed-wheel checks | Implemented and passed |
| Exact reduced-order/non-production classification | Power-stage input metadata, `examples/power_stage/README.md`, `docs/POWER_STAGE_SANDBOX.md` | `tests/test_power_stage_examples.py` requires the exact classification text | Implemented and passed |
| MNA exercise | `lab/01-mna/` | Dynamic/algebraic ownership and residual assertions | Implemented and passed |
| Convergence exercise | `lab/02-convergence/` | Three measured refinements; observed orders 2.00117 and 2.00029 | Implemented and passed |
| Phase-versus-energy exercise | `lab/03-phase-versus-energy/` | Separate phase and energy evidence for backward Euler and trapezoidal over ten LC periods | Implemented and passed |
| Shadow-authority exercise | `lab/04-shadow-authority/` | Identical accepted time grid; maximum state delta `1.3877787807814457e-17` below recorded 16-ULP tolerance `3.552713678800501e-15` | Implemented and passed |
| Deterministic packaging exercise | `lab/05-deterministic-packaging/` | Two byte-identical wheels, fixed timestamps, fixed permissions, canonical member order | Implemented and passed as development evidence |
| Source-versus-wheel equivalence | `lab/06-source-wheel-equivalence/` | Isolated module and console runs match source byte-for-byte for RC, switched RC, and all three power-stage cases; installed-wheel Observatory smoke also matches | Implemented and passed as development evidence |
| Fixture updates are review-controlled | `lab/support/verify.py`, `lab/fixtures/verification-baseline.json` | Updates require `--update-fixtures --exercise all`; ordinary runs do not modify the fixture | Implemented and passed |
| Deterministic integration generation | Observatory, atlas, power-stage, and lab generators | Two independent output directories compared byte-for-byte for every deterministic artifact | Implemented and passed |
| Documentation and claim boundaries | `README.md`, `docs/index.md`, comparison/error/roadmap/reproducibility/current-work documents, `CHANGELOG.md`, `RELEASE.md` | Documentation review plus exact classification and release-boundary tests | Implemented |

## Deterministic Artifact Evidence

Two full runs in separate temporary directories produced byte-identical files.
Principal report hashes are:

| Artifact | SHA-256 |
| --- | --- |
| Method Observatory JSON | `90c5446ece34eec9e61d7a93c40105c83be4907734f5cce2c147103f5ddad5a0` |
| Bound Coverage Atlas JSON | `f24ecff23786ab510bbe91207074742c601c5a53971b5bba3e3ea6aa3d48a0a1` |
| Power-stage comparison JSON | `cfed4ea836e8252dc2f29e1c787767355ea6310942473c4bb03b3e84ef0c36c5` |
| Full teaching-lab JSON | `0b6383a91ee51b6d075eedd0075f34e4b1b601ee61a3c3ea071ebf0e308320de` |
| Review-controlled lab fixture | `ab021d66a32ae6397775eacb2f28bc536b9016fd031aaaaee0a9307198a76100` |
| Development wheel, both builds | `ca5d648e60dfd9923deadc85fb304b45dc9ecf87aecc982a369d3766542806f2` |

The observatory CSV views, observatory SVG and Markdown, atlas sample CSV, all
four atlas SVGs, and power-stage CSV/SVG also matched byte-for-byte. Timing was
not included in deterministic correctness evidence.

## Selection and Rejection Review

The fixed-accuracy view contains 126 target rows: 85 select a measured source
row and 41 report `no_qualifying_row`. The fixed-work view contains 168 budget
rows: 65 select a measured source row and 103 report `no_qualifying_row`.
These are expected outcomes of the declared measured grids. They do not hide a
failed run, and no interpolation or extrapolation fills them.

All 3,040 Observatory rejected attempts are represented in the atlas cause
table with requested and suggested steps:

- 2,972 `candidate_amplification_domain_exceeded` attempts, normalized as
  `candidate_nonconvergence`; and
- 68 `independent_re_anchor_failed` attempts, normalized as `replay_failure`.

The 57 power-stage rows all succeed after controlled retry. Their 3,761 rejected
attempts are retained rather than discarded:

- 3,715 candidate amplification-domain rejections;
- 27 reference-solve failures;
- 14 embedded-candidate-cap rejections;
- 3 independent re-anchor failures; and
- 2 predictor/reference-cap rejections.

These counts characterize the selected experiments. They are not generalized
robustness probabilities.

## Coverage Review

The atlas marks 83,846 samples eligible for empirical recursive-bound coverage;
3,793 are covered. Individual row fractions range from 0.0 to 1.0. This low and
case-dependent measured coverage is intentionally reported, not tuned away.
It confirms that the recursive internal bound is diagnostic evidence under the
implemented model, not a universal formal enclosure. Actual authority error,
authority-epoch drift, anchor deviation, phase, and energy remain separate.

## Qualification and Promotion Boundary

The implementation, source tests, optional-backend tests, long-horizon tests,
deterministic reports, development wheel reproducibility, installed-wheel case
equivalence, and installed-wheel observatory smoke all pass on the exact dirty
source-tree hash recorded above.

The following promotion requirements remain deliberately open:

1. commit the reviewed source so the tree is clean and the exact commit is
   selectable;
2. rerun the complete qualification and deterministic artifact generation on
   that clean exact commit;
3. record the resulting exact source, wheel, manifest, report, workflow, and
   environment hashes in release evidence; and
4. obtain explicit human approval of the exact commit and artifacts.

Therefore the facilities requested by the implementation plan are present and
automatically qualified in development, but `v1.1.0` is not release-qualified,
approved, tagged, or published by this audit.

## 2026-08-27 Expansion Addendum

This audit records the original six-exercise and four-mapping implementation
baseline. It is retained as historical evidence and is not rewritten to imply
that the larger surface existed during that earlier qualification run.

The current additive expansion is owned by
`NGSPICE_AND_TEACHING_TUTORIAL_EXPANSION_PLAN.md`. That plan defines 20
manifest-owned ngspice mappings, ten executable teaching exercises, ten
tutorial documents, and 13 generated tutorial/comparison SVG figures. Current
counts and current validation evidence must be read from that expansion record,
the authoritative manifests, and fresh test output rather than inferred from
the historical counts above.
