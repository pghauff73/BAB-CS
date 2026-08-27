# Bounded-Authority-Based-Circuit-Simulation Tests and Comparisons Qualification Audit

Audit date: August 24, 2026

## Status

- **Local implementation:** achieved against the committed source snapshot identified below.
- **Local deterministic qualification:** achieved.
- **Installed-wheel qualification:** achieved.
- **Live external comparison:** achieved locally with `ngspice-46` and remotely
  with `ngspice-42` for the four declared mappings.
- **Remote GitHub workflow evidence:** achieved for the exact implementation
  commit through CI, scheduled comparisons, and release qualification.
- **Release publication:** not performed by this qualification change; publishing
  remains a separate human-approved action.

This is an additive qualification audit. It does not rewrite
`docs/BAB_CSV1_COMPLETION_AUDIT.md` or imply that the tests and comparison
program was part of the original v1 release evidence.

## Qualified Snapshot

- Implementation base commit: `46b8ad886bb25445208099b4627f45f6a9da4d5b`
- Qualified implementation commit:
  `3dafe404d5a7d134c26f3a0d7fc73d7e3777dd95`
- Working tree at qualification: clean.
- Deterministic source-tree SHA-256:
  `55b3a7464a2f76b2ddad157096b7eb348e4e85aeec0eb0f37166f2ec490e4458`
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

Result: 97 tests passed, zero skipped, in 78.596 seconds.

Test log SHA-256:
`ef4be34f7be96c5ff2328cebf24e6d6b945603bd331a0804568dac97ec31686c`

The default pull-request tier was run across the complete declared Python
matrix in remote CI.

```bash
for version in 3.11 3.12 3.13 3.14; do
  "python${version}" -m compileall -q -f src tests tools
  PYTHONPATH=src "python${version}" -m unittest discover -s tests -v
done
```

Each CPython 3.11 through 3.14 job passed 97 tests with the scheduled and
release-only long-horizon cases skipped, matching the intended pull-request
tier. The exact run is recorded under TC-011.

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

The performance range above is from the local timed run. Final remote artifact
hashes at the qualified implementation commit are:

- Numerical JSON:
  `d5f63ea03cff855952b2158ab447a97163ed25f4aab06f93e5881421e86e8e4e`
- Flat CSV:
  `0de55953c57faa4ceb6f43570fc1cdd9efacf1aa4b9e0d031bdf30745b433195`
- SVG plot:
  `98742d51cbc017b2dd08d5ec57ad280ed9390b2fd96c4b279ae2e5450a0c843b`
- Timing JSON for this run:
  `f26b12458dbbfa83bbfc0dbab453eec8944ccbeec90d49c9e4b885db3e7991e8`
- Timed-run log:
  `4686cb36196522a712671ba92ddc0198bad224137d22fbd1cb1fd9a29b6d5963`

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

The table below records the final remote `ngspice-42` reports. All four reports
identify the qualified commit, report `dirty: false`, and identify the same
source-tree hash shown above.

| Case | Samples | Maximum absolute difference | Report SHA-256 |
| --- | ---: | ---: | --- |
| `rc_step` | 24 | `0.005129168242569024` | `ca42d5e482c78de3fca6ea08606ee10fc955656d3c1c376913b05d1f2d29cb03` |
| `rl_step` | 24 | `0.0005129168232507718` | `09892144ed19049e29c38d19f29dafe976b8160e9f79ac151d51e04f803bde9d` |
| `diode_clip` | 264 | `0.0030983774729334713` | `8bc1b1e6ed3d47525cd4705003262504746696568270562c41757b6478d7932e` |
| `switched_rc` | 101 | `0.07878138132636461` | `2ed0cf45ebfa6119d257610b25a4b078840ede4b107c7f5d262828d58a901fdf` |

Generated-netlist SHA-256 values:

- `rc_step`: `a6d1f07519751a5c19afc49c7f241d09da7bb463181c09264be250ad10018260`
- `rl_step`: `fcedf21e1dfd02529e44170b278aad867d3b840a3a9ef0bd603a864d896c9454`
- `diode_clip`: `791b785413c8e3782becaa4641f75f5b0ad78bc3198850d716f7154b29bb7ac7`
- `switched_rc`: `2d76c7d623bc6684af0317db3c099c085bb78a99927ddd5fcf2f199800512ef4`

Raw-output SHA-256 values:

- `rc_step`: `58f24ba7758753d34ba84bcd15e1ff0da164d13844aaedd9436366379a9df3af`
- `rl_step`: `a1f8de03d35bd4f1f8acdf2820c9ec9fbfa3f8fd9ad2c25492b914c3ef2ddb4c`
- `diode_clip`: `92403432105ea523745bd881f4f5da4dc727a2987cb71786b80fee41a5d71f32`
- `switched_rc`: `1d461a433f332111b6e05bcbb8782c73791c1918cefc451ea6f5f21473c31c4e`

External differences are cross-implementation evidence for the generated
semantic mapping. They do not establish exact physical truth or identify which
implementation is responsible for a discrepancy.

### Installed Wheel

- Wheel: `bab_cs-1.0.0-py3-none-any.whl`.
- Wheel SHA-256:
  `c4293b66d2dd27000da1e3b060690f460ad13fa2cc1285381221cbe981e2c791`.
- Import path was verified inside the clean virtual environment rather than from
  `src/`.
- `pip check` reported no broken requirements.
- Installed-wheel fast suite: 97 tests passed, with only the scheduled and
  release long-horizon tests skipped by default.
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

### TC-011 — CI Qualification Tiers: Achieved

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
- `CI` push run `32729607872` passed at the qualified implementation commit,
  including CPython 3.11 through 3.14 and the wheel job.
- `Scheduled Comparisons` dispatch run `32729633142` passed at the same commit,
  including the no-skip long-horizon suite, complete deterministic method
  matrix, and all four live `ngspice` mappings.
- `Release Qualification` dispatch run `32729636093` passed at the same commit,
  including the no-skip source suite, candidate-wheel build, installed-wheel
  verification, provenance capture, and artifact upload.
- The release-qualification wheel SHA-256 is
  `c4293b66d2dd27000da1e3b060690f460ad13fa2cc1285381221cbe981e2c791`.
- The scheduled numerical CSV and SVG matched the installed-wheel CSV and SVG
  byte-for-byte, with SHA-256 values
  `0de55953c57faa4ceb6f43570fc1cdd9efacf1aa4b9e0d031bdf30745b433195`
  and `98742d51cbc017b2dd08d5ec57ad280ed9390b2fd96c4b279ae2e5450a0c843b`.
- The remote reports record source-tree SHA-256
  `55b3a7464a2f76b2ddad157096b7eb348e4e85aeec0eb0f37166f2ec490e4458`
  and manifest SHA-256
  `7b805a88a1cd86e7569ff0d9fa0dbbd5f9db2b6f3c841808af12062b4866d406`.
- All four external reports record `dirty: false`; generated evidence no longer
  contaminates source-cleanliness provenance.

### TC-012 — Documentation and Evidence Audit: Achieved

- `README.md` documents local qualification commands and CI tiers.
- `docs/COMPARISON_PROTOCOL.md` documents authority, controls, metrics,
  determinism, thresholds, performance boundaries, and CI tiers.
- `docs/EXTERNAL_COMPARISON.md` documents mapping, provenance, failure behavior,
  and claim limits.
- This file records the requirement-to-evidence audit without modifying the
  historical completion audit.

## Completion-Gate Audit

- Existing BAB-CSv1 regression requirements: pass within the 97-test no-skip
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
- Exact-candidate remote CI, scheduled, and release workflows: pass at
  `3dafe404d5a7d134c26f3a0d7fc73d7e3777dd95`.
- Human review before release publication: retained as a separate gate; no new
  release was published by this qualification run.

The implementation and comparison program are qualified locally and remotely.
The audit itself is excluded from the deterministic source-tree hash, so this
evidence-only update does not alter the qualified implementation snapshot.
Publishing or replacing a GitHub release still requires an explicit human
decision after reviewing the candidate commit, thresholds, and artifacts.

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
