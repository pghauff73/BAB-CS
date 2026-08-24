# BAB-CS Tests and Comparisons Qualification Audit

Audit date: August 24, 2026

## Status

- **Local implementation:** achieved against the working-tree snapshot identified below.
- **Local deterministic qualification:** achieved.
- **Installed-wheel qualification:** achieved.
- **Live external comparison:** achieved with `ngspice-46` for the four declared mappings.
- **Remote GitHub workflow evidence:** pending because this working tree has not been committed and pushed.
- **Release publication approval:** pending human review of the candidate commit, thresholds, and artifacts.

This is an additive qualification audit. It does not rewrite
`docs/BAB_CSV1_COMPLETION_AUDIT.md` or imply that the tests and comparison
program was part of the original v1 release evidence.

## Qualified Snapshot

- Base commit: `46b8ad886bb25445208099b4627f45f6a9da4d5b`
- Working tree: dirty, with the implementation changes listed by `git status`.
- Deterministic source-tree SHA-256:
  `169f81b882e154acf26fe218d8c620cacdbcc437c5fd82e972918e061b87ecfc`
- Source files in hash: 61.
- Hash scope: Git tracked and untracked non-ignored files, excluding generated
  `artifacts/`, `build/`, and `dist/` content and this self-referential audit.
- Comparison manifest SHA-256:
  `7b805a88a1cd86e7569ff0d9fa0dbbd5f9db2b6f3c841808af12062b4866d406`
- Environment: CPython 3.14.6 on
  `Linux-7.1.3-2-cachyos-x86_64-with-glibc2.43`.

`tools/compare_methods.py` and `tools/compare_external.py` record the source
commit, dirty state, source-tree hash, source-file count, scope statement, and
environment in each JSON report.

## Validation Results

### Source Suite

Command:

```bash
python -m compileall -q -f src tests tools
BABCS_LONG_TESTS=1 BABCS_VERY_LONG_TESTS=1 \
  PYTHONPATH=src python -m unittest discover -s tests -v
```

Result: 96 tests passed, zero skipped, in 76.130 seconds.

Test log SHA-256:
`65743138cc593737b26d675bd8a2843edd2101f5d7380b28100468e2bec3cb96`

The default pull-request tier was run across the complete declared Python
matrix. CPython 3.11.15 and 3.13.14 were supplied by `uv`; CPython 3.12.13 and
3.14.6 were already available locally.

```bash
for version in 3.11 3.12 3.13 3.14; do
  "python${version}" -m compileall -q -f src tests tools
  PYTHONPATH=src "python${version}" -m unittest discover -s tests -v
done
```

Each interpreter passed 96 tests with the scheduled and release-only
long-horizon cases skipped, matching the intended pull-request tier.

- CPython 3.11.15 log SHA-256:
  `a18fb328c48d8ea458373b7e356c02f5b3d98288f56eb88c3ae5cccf7658f99e`
- CPython 3.12.13 log SHA-256:
  `dd82dd5a345de700bde7f77e61318d6d7c7bb7b8539b973b88c20c333c2318d5`
- CPython 3.13.14 log SHA-256:
  `1356204a267c0ab4ec4bf65a4c11b63ac236da4e4448d9ac18b7b7d6283b7c1e`
- CPython 3.14.6 installed-wheel log SHA-256:
  `03d5458e0e18894e0ce4b0008146e6d328ba681e8b5e72cd2914ebc09ce2b177`

### Deterministic Method Matrix

The full manifest ran twice without timing. Numerical JSON, CSV, and SVG were
byte-identical. A third run with three timing repeats produced identical
numerical artifacts and a separate timing report.

- Cases: 8.
- Results: 100.
- Methods: active, backward Euler, BDF2, raw AB2, shadow, trapezoidal.
- Authorities: analytic and independent refined replay.
- Convergence analyses: 35.
- Fixed-accuracy analyses: 105.
- Fixed-work analyses: 140.
- Maximum characterized waveform error across the complete mixed-method matrix:
  `0.12802541939866408`; this is characterization, not a universal threshold.
- Maximum deterministic work units: 129596.
- Timing samples: 100 results with three repeats each.
- Median timing range: `1.770298695191741e-05` to
  `1.0386381130083464` seconds; timing is not a correctness gate.

Artifact hashes:

- Numerical JSON:
  `4e96d2868dd5c6db2b74345537a5f439c78b69fc706d7d35476b1408a0242046`
- Flat CSV:
  `0de55953c57faa4ceb6f43570fc1cdd9efacf1aa4b9e0d031bdf30745b433195`
- SVG plot:
  `98742d51cbc017b2dd08d5ec57ad280ed9390b2fd96c4b279ae2e5450a0c843b`
- Timing JSON for this run:
  `04c7ab45da8a3e9cb034dcfce8677cb81da4e59cd5c1b773fe1619ab56da45c8`
- Timed-run log:
  `9b766d333b0b589774c6cab7fd86e621e1b8563ac430f84834708393eaace8e8`

The timing hash is provenance for this run only and is not expected to be
reproducible across machines or loads.

### Long-Horizon Characterization

The no-skip suite includes the 10-, 100-, and 1,000-period LC gates. The full
comparison matrix separately records sampled amplitude error, final phase error,
relative period error, relative energy span, anchor deviation, and empirical
anchor-error-to-pre-reset-bound ratios.

For active LC at the declared matrix points:

- Relative amplitude error ranged from approximately `3.15e-11` to `5.06e-05`.
- Final phase error ranged from approximately `2.24e-04` to `8.97e-04` radians.
- Relative period error ranged from approximately `3.57e-06` to `1.43e-05`.
- Relative energy span ranged from approximately `6.86e-04` to `2.86e-03`.
- Empirical anchor-error/pre-reset-bound ratios were finite but exceeded one in
  some cases. They remain characterization evidence and are not a formal proof
  that the internal bound encloses exact trajectory error.

### External `ngspice` Evidence

All reports identify the same source-tree hash shown above.

| Case | Samples | Maximum absolute difference | Report SHA-256 |
| --- | ---: | ---: | --- |
| `rc_step` | 24 | `0.005129168242569024` | `433103817b3a5bcd42c49096969f1cc606b434c078a87bbb47a1e13409869093` |
| `rl_step` | 24 | `0.0005129168232507718` | `d8f29d403a6336d2b4210517904ec74076af0a4fea02314a9ce549568974fabd` |
| `diode_clip` | 265 | `0.0031176977073201495` | `a4cdb7df0dba59258b198197c733cae7e8d7bace286fce66fb95c31e6a524e33` |
| `switched_rc` | 96 | `0.08037580482940321` | `d2aef014533edd289e1a8ce2b042f7c5342655cabf162fa4635d7d5301b7e1c6` |

Generated-netlist SHA-256 values:

- `rc_step`: `a6d1f07519751a5c19afc49c7f241d09da7bb463181c09264be250ad10018260`
- `rl_step`: `fcedf21e1dfd02529e44170b278aad867d3b840a3a9ef0bd603a864d896c9454`
- `diode_clip`: `791b785413c8e3782becaa4641f75f5b0ad78bc3198850d716f7154b29bb7ac7`
- `switched_rc`: `2d76c7d623bc6684af0317db3c099c085bb78a99927ddd5fcf2f199800512ef4`

Raw-output SHA-256 values:

- `rc_step`: `110e4d3c1da84268614c827168e197757343f3962f7e16630425e5867259c24e`
- `rl_step`: `519cd0827a1dd79861dc1b0dd204e8226972ba4deb6c61a05aee758ac8841a65`
- `diode_clip`: `ebc8ab589bd6aae8b39f12903812e5e74d09b1df4a68da6e0519d6a6a64b6354`
- `switched_rc`: `6e8012748a7bd9a9c9d30f397388634152a82652e40bacb9260372d99b79a628`

External differences are cross-implementation evidence for the generated
semantic mapping. They do not establish exact physical truth or identify which
implementation is responsible for a discrepancy.

### Installed Wheel

- Wheel: `bab_cs-1.0.0-py3-none-any.whl`.
- Wheel SHA-256:
  `df36c9a4e2ac57aff204c62e542ed5cba385c844a7c74e0dcffed0e073ca4338`.
- Import path was verified inside the clean virtual environment rather than from
  `src/`.
- `pip check` reported no broken requirements.
- Installed-wheel fast suite: 96 tests passed, with only the scheduled and
  release long-horizon tests skipped by default.
- Installed-wheel test log SHA-256:
  `03d5458e0e18894e0ce4b0008146e6d328ba681e8b5e72cd2914ebc09ce2b177`.
- Installed-wheel numerical JSON, CSV, and SVG matched the source-run artifacts
  byte-for-byte.

## Work-Package Audit

### TC-001 — Shared Qualification Support: Achieved

- `tests/support/circuits.py` owns reusable circuit constructors.
- `tests/support/analytic.py` provides RC, RL, general parallel RLC, and driven
  RC analytic solutions.
- `tests/support/metrics.py` provides trace validation/interpolation, scaled
  errors, convergence order, zero-crossing period estimation, and sinusoidal
  offset/amplitude/phase fitting.
- `tests/support/raw_ab2.py` provides test-only variable-step AB2.
- `tests/test_support.py` checks initial and selected known analytic points,
  incompatible dimensions, non-monotonic traces, phase fitting, and raw AB2
  convergence.

### TC-002 — Integrator and Configuration Boundaries: Achieved

- `BABCSConfig` and `ImplicitSettings` reject invalid, non-positive, non-finite,
  unsupported, and inconsistent boundaries.
- `tests/test_integrator_boundaries.py` covers AB2 exact-rate cases, dimension
  and step validation, exact ratio endpoints, outside-ratio startup, gain
  monotonicity, and full-reference contraction fallback.

### TC-003 — Hard Failure Gates: Achieved

- Predictor, algebraic residual, full residual, energy, projection fallback,
  implicit nonconvergence, independent replay, non-finite metric/model/state,
  minimum-step, and rejection-budget paths have named regressions.
- Rejected direct steps preserve immutable input state/history; simulator retry
  tests verify bounded termination and event labeling.

### TC-004 — Bound Recurrence Verification: Achieved

- `tests/test_bound_model.py` independently reconstructs residual defect and
  `B_next = q * B_current + delta` from emitted metrics.
- Tests verify finite strict contraction, zero local gain under full implicit
  authority, reset behavior, pre-reset bound retention, and replay work.
- Empirical exact-error coverage is explicitly separated from recurrence
  correctness.

### TC-005 — Analytic Accuracy and Convergence: Achieved

- Backward Euler demonstrates first-order convergence.
- Trapezoidal, BDF2, and test-only raw AB2 demonstrate second-order convergence
  on compatible smooth cases.
- Active BAB-CS error decreases under refinement without claiming a universal
  asymptotic order.
- RC charge/discharge, RL rise/decay, underdamped/overdamped RLC, and driven RC
  amplitude/phase are compared at common times against analytic authority.
- Shadow mode matches its selected implicit authority.

### TC-006 — Long-Horizon Bounds and Passivity: Achieved

- `tests/test_long_horizon.py` covers 10-, 100-, and 1,000-period LC, timestep
  and anchor sweeps, damped RLC decay, passive RC/RL monotonic energy, and active
  versus raw AB2 phase behavior.
- The manifest compares raw AB2, active BAB-CS, and implicit integration.
- Phase, period, amplitude, and energy are separate fields; energy is not
  presented as a phase bound.

### TC-007 — Event and Nonlinear Qualification: Achieved

- Zero-time pulse edges, finite rise/fall, closely spaced PWL points, repeated
  switching, and rejection before an event are covered.
- Tests verify each event time, history reset, and implicit startup after events.
- Diode clipping, diode recovery, and switched RC are compared against refined
  replay with residual and iteration evidence.
- A diode case with intentionally constrained implicit iterations fails closed.

### TC-008 — Comparison Runner: Achieved

- `tools/compare_methods.py` validates `benchmarks/manifest.json`, supports all
  six methods, records complete source/case/configuration/authority provenance,
  and writes stable JSON, CSV, and SVG.
- Fixed-timestep, fixed-accuracy, and deterministic fixed-work analyses are
  emitted.
- Existing outputs are never overwritten without `--overwrite`.
- Two full runs and the numerical section of a timed run reproduced
  byte-for-byte.

### TC-009 — Diagnostic Extension: Achieved

- Production diagnostics add residual ratio, local defect, pre-reset bound,
  accepted-step statistics, rejection/reset categories, reference solve and
  iteration counts, projection counts/iterations, Jacobian evaluations, and
  replay work.
- Fields are additive; existing meanings are retained.
- `tests/test_bound_model.py` and `tests/test_cli.py` verify counters and output.

### TC-010 — Optional External Simulator Comparison: Achieved

- `tools/compare_external.py` is opt-in and not a package dependency or
  pull-request requirement.
- Netlist tests cover component values, initial conditions, state vectors,
  switch control, and unsupported diode semantics.
- Reports preserve tool version, command, source hash, configuration, case,
  netlist, raw-output, and log hashes.
- Four live `ngspice-46` mappings completed successfully.

### TC-011 — CI Qualification Tiers: Implemented; Remote Evidence Pending

- `.github/workflows/ci.yml` covers Python 3.11 through 3.14, the fast suite,
  deterministic examples/comparison smoke, wheel build, and installed-wheel
  smoke.
- `.github/workflows/comparisons.yml` is scheduled/manual and covers the long
  suite, complete matrix, repeated timing, live `ngspice`, hashes, and uploaded
  JSON/CSV/log/plot artifacts.
- `.github/workflows/release-qualification.yml` covers the no-skip source suite,
  wheel build/hash, installed-wheel tests, complete comparison matrix, source
  commit, environment, and report hashes.
- All workflow files parse as valid YAML, and their commands were reproduced
  locally, including the complete Python 3.11 through 3.14 default matrix.
- The repository's current base commit
  `46b8ad886bb25445208099b4627f45f6a9da4d5b` has a successful remote `CI`
  push run (`32719668272`), confirming the existing Actions infrastructure.
- No remote workflow run can identify this exact dirty source snapshot; that
  evidence requires a committed and pushed candidate.

### TC-012 — Documentation and Evidence Audit: Achieved

- `README.md` documents local qualification commands and CI tiers.
- `docs/COMPARISON_PROTOCOL.md` documents authority, controls, metrics,
  determinism, thresholds, performance boundaries, and CI tiers.
- `docs/EXTERNAL_COMPARISON.md` documents mapping, provenance, failure behavior,
  and claim limits.
- This file records the requirement-to-evidence audit without modifying the
  historical completion audit.

## Completion-Gate Audit

- Existing BAB-CSv1 regression requirements: pass within the 96-test no-skip
  suite.
- Isolated hard failure gates: pass.
- Independent recursive-bound recomputation: pass.
- Analytic convergence for authority methods and raw AB2: pass.
- Active accuracy, contraction, fallback, anchor, and sweep evidence: pass.
- Long-horizon phase separated from energy: pass.
- Complete authority and configuration provenance: pass.
- Byte-identical deterministic numerical artifacts: pass.
- Installed candidate wheel comparison: pass.
- Requirement-to-evidence audit: present.
- Exact-candidate remote pull-request, scheduled, and release workflows: pending
  commit/push and remote execution.
- Human review before release publication: pending.

The implementation is locally qualified, but the plan's release-certification
gate is not complete until the source is committed, pushed, all three workflow
tiers pass at that commit, and a human approves any changed threshold, baseline,
or deterministic artifact.

## Known Limitations

- Active BAB-CS performs an implicit reference solve on every eligible AB step
  and is not expected to outperform pure implicit integration in v1.
- Dense algebra limits circuit scale.
- Higher-index and singular topologies fail closed rather than being
  regularized.
- External comparison covers only explicitly equivalent mappings.
- Empirical bound coverage is not a formal exact-trajectory enclosure proof.
- Wall time is characterization only.
- Arbitrary analog threshold root finding and production AB-only operation
  remain deferred.
