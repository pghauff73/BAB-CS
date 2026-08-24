# BAB-CS Release Draft

## Status

- **Proposed release:** `v1.1.0`
- **Status:** Draft; not approved for publication
- **Implementation baseline:**
  `8ae886944f3cd7d051c402d693c5d564d830eb7d`
- **Final release source commit:** to be recorded after the version and release
  documentation commit
- **Current package metadata:** `1.0.0`
- **Required before tagging:** update and verify every version-bearing build field
- **Release authority:** explicit human review of the exact tagged commit and its
  qualification evidence

The proposed `v1.1.0` designation reflects a backward-compatible feature,
qualification, and performance release. It is not yet encoded in
`pyproject.toml` or `build_backend.py`; a wheel built from the current source is
still named `bab_cs-1.0.0-py3-none-any.whl`.

## Release Summary

This candidate expands BAB-CS from a bounded AB2 circuit-simulation prototype
into a reusable bounded multi-method reference implementation. Explicit and
implicit candidate methods share algebraic projection, independent reference
authority, contractive correction, recursive bound tracking, periodic refined
replay, event-boundary history resets, passivity and residual monitoring, and
fail-closed fallback.

The release also adds an optional high-performance sparse path for larger
built-in circuits. The sparse path retains the dependency-free dense backend,
preserves extension fallbacks, and uses acceleration only behind explicit size,
topology, residual, contraction, and finiteness gates.

## Highlights

### Bounded multi-method controller

- Adds explicit Euler, Heun, Bogacki-Shampine RK23, and variable-step AB2
  candidates.
- Adds bounded backward Euler, trapezoidal, and variable-step BDF2 candidates
  paired with a distinct implicit reference.
- Adds embedded fast modes for AB2, Heun, and RK23 with scheduled references,
  dynamic bound checkpoints, and mandatory independent replay.
- Preserves `disabled`, `shadow`, and `active` rollout modes.
- Keeps raw AB2 test-only and unable to bypass production safety gates.

### Projection, correction, and re-anchor behavior

- Projects every candidate endpoint onto the circuit algebraic manifold.
- Applies a contractive candidate/reference correction in active mode.
- Promotes implicit reference authority when contraction, stiffness, residual,
  projection, energy, or recursive-bound gates fail.
- Uses topology-aware replay refinement while preserving complete interval
  coverage.
- Uses AB3 differential extrapolation only as a replay initial guess after two
  matching uniform substeps.
- Uses quartic algebraic extrapolation only as a guarded initial guess on
  eligible large sparse replay windows.
- Restarts cleanly from accepted state after failed extrapolation or topology
  events.

### Sparse and nonlinear execution

- Adds optional SciPy SuperLU support through `linear_backend="auto"` and
  `linear_backend="scipy"`.
- Adds measured dense/sparse crossover rules instead of forcing sparse work on
  small systems.
- Precompiles sparse CSC structures and topology-owned stamping metadata.
- Reuses bounded per-thread sparse workspaces while retaining safe ordering
  fallback.
- Uses native batched differential-sensitivity solves and read-only reusable
  right-hand-side storage.
- Adds demand-gated generated residual and full sparse assembly kernels for the
  exact built-in `Circuit` type.
- Retains mutable component values and sampled inputs at execution time rather
  than embedding them into generated source.

### Guarded nonlinear prediction

- Reuses a previous validated nonlinear factorization only as a chord
  predictor.
- Requires the proposed chord update to reduce the current residual under the
  normal line search.
- Adds a reduced Schur implicit predictor using retained algebraic sensitivity
  and differential-Jacobian evidence.
- Attempts the Schur predictor at most once per implicit solve and reserves an
  iteration for the exact coupled sparse Newton solve.
- Rejects future evidence, changed switch topology, stale evidence, singular
  systems, and nonfinite updates.
- Restores the base algebraic state and residual before exact fallback after a
  failed contraction.

### Determinism and evidence

- Adds deterministic wheel-build regression coverage.
- Expands the comparison manifest across explicit, implicit, bounded, shadow,
  and raw research controls.
- Reports fixed-timestep, fixed-accuracy, and fixed-work evidence separately.
- Records state error, waveform error, oscillator phase and energy behavior,
  recursive bounds, re-anchor evidence, rejection reasons, and deterministic
  work counters.
- Preserves separate `ngspice` cross-implementation evidence and its semantic
  mapping provenance.
- Adds pinned GitHub Actions for source tests, optional sparse qualification,
  comparisons, external evidence, deterministic wheel construction, and release
  qualification.

## Performance Characterization

The local optimization audit records the following cumulative `auto`-backend
reductions against the current forced-dense path on the balanced nonlinear
channel benchmark:

| Algebraic unknowns | Mean reduction | Minimum round reduction |
| ---: | ---: | ---: |
| 32 | 62.129% | 61.958% |
| 64 | 92.016% | 91.958% |
| 128 | 97.619% | 97.605% |

The contractively bounded Schur predictor additionally measured:

- 2.957% mean end-to-end reduction at 64 algebraic unknowns on the nonlinear
  capacitor/diode workload.
- 3.692% mean end-to-end reduction at 128 algebraic unknowns on the nonlinear
  capacitor/diode workload.
- 1.084% mean reduction at 64 algebraic and 32 dynamic unknowns on the mixed
  capacitor/inductor workload.
- 0.545% mean reduction at 128 algebraic and 64 dynamic unknowns on the mixed
  capacitor/inductor workload.
- Approximately 35% to 73% direct sparse-update reduction over the exact
  coupled block across tested mixed dimensions.

These numbers are local characterization for the named workloads and hardware.
They are not a claim that BAB-CS is generally faster than `ngspice` or another
production simulator.

## Current Validation Evidence

The candidate source commit completed the full opt-in local source suite with:

- `BABCS_LONG_TESTS=1`
- `BABCS_VERY_LONG_TESTS=1`
- 174 tests passed
- zero skips
- 40.757 seconds reported by `unittest`

The most recent installed-wheel and deterministic comparison evidence predates
the final Schur and solution-materialization changes. Its wheel hash and report
hashes must not be reused as evidence for this release candidate.

Publication remains blocked on successful normal CI for the final release
commit and tag-triggered qualification of that exact commit.

## Compatibility

- Requires Python 3.11 or newer.
- The default installation has no runtime dependencies.
- Sparse acceleration remains optional through `scipy>=1.11`.
- The default `dense` backend preserves the dependency-free deterministic path.
- Existing JSON cases remain valid unless they relied on behavior now rejected
  by a correctness gate.
- Public rollout modes retain their existing meanings.
- Existing circuit elements remain supported: resistors, capacitors, inductors,
  independent voltage/current sources, Shockley diodes, and time-controlled
  resistive switches.

## Known Limits

- BAB-CS remains a research and deterministic-validation implementation, not a
  production replacement for a sparse SPICE simulator.
- Device coverage is intentionally small.
- Higher-index or singular semiexplicit topologies fail closed instead of being
  silently regularized.
- Switch events come from waveform breakpoints rather than general analog root
  finding.
- Error bounds are relative to the implemented model, reference, and stated
  assumptions; they are not proof against the unknown physical trajectory.
- Empirical anchor-error-to-bound ratios are characterization evidence, not a
  formal coverage proof.
- The sparse backend still performs fresh SuperLU factorization where explicit
  symbolic/numeric factor separation is unavailable.
- Periodic replay corrects the endpoint and rebuilt history; it does not rewrite
  already emitted intermediate samples.

## Deliberately Excluded Follow-up

An ULP-aware sensitivity-age comparison has identified additional mixed C+L
performance by treating representationally two-step-old evidence as exactly
two-step-old. That policy is not implemented in this candidate commit and must
not be described as a `v1.1.0` feature unless it is separately implemented,
tested, committed, and requalified before the release tag is created.

## Release Qualification Procedure

### 1. Select and encode the version

Update all hard-coded package-version locations together:

- `pyproject.toml`
- `_metadata()` in `build_backend.py`
- `_wheel_name()` in `build_backend.py`
- the `.dist-info` names in `build_backend.py`

Confirm that no old version remains:

```bash
rg -n '1\.0\.0|bab_cs-1\.0\.0' pyproject.toml build_backend.py README.md tests
```

Add or update tests so package metadata, wheel filename, and `.dist-info`
directory cannot diverge silently.

### 2. Confirm a clean exact source state

```bash
git status --short --branch
git rev-parse HEAD
git diff --check
```

Record the full source commit. Do not qualify one commit and tag another.

### 3. Run the full source suite

```bash
BABCS_LONG_TESTS=1 BABCS_VERY_LONG_TESTS=1 \
  PYTHONPATH=src python -m unittest discover -s tests -v
```

The final result must contain no failures, errors, or unexpected skips.

### 4. Generate numerical comparison evidence

```bash
mkdir -p artifacts/release
PYTHONPATH=src python tools/compare_methods.py \
  --output artifacts/release/source-comparison.json \
  --csv-output artifacts/release/source-comparison.csv \
  --plot-output artifacts/release/source-comparison.svg \
  | tee artifacts/release/source-comparison.log
```

Review accuracy, bounds, oscillator behavior, rejected attempts, implicit
fallbacks, re-anchor evidence, and deterministic work. A green process exit is
not a substitute for reviewing changed thresholds or numerical baselines.

### 5. Refresh `ngspice` evidence

With `ngspice` installed:

```bash
for case in rc_step rl_step diode_clip switched_rc; do
  PYTHONPATH=src python tools/compare_external.py \
    "benchmarks/cases/${case}.json" \
    --output "artifacts/release/${case}.json" \
    --netlist-output "artifacts/release/${case}.cir" \
    --raw-output "artifacts/release/${case}.dat" \
    --log-output "artifacts/release/${case}.log"
done
```

Review the generated semantic mappings and waveforms. These runs establish
cross-implementation evidence only; they do not prove general superiority.

### 6. Build the wheel twice

```bash
rm -rf dist-a dist-b
python -m pip wheel . --no-deps --wheel-dir dist-a
python -m pip wheel . --no-deps --wheel-dir dist-b
cmp dist-a/*.whl dist-b/*.whl
sha256sum dist-a/*.whl | tee artifacts/release/WHEEL_SHA256
```

The two wheels must be byte-identical.

### 7. Test the installed wheel

```bash
rm -rf /tmp/babcs-release-wheel
python -m venv /tmp/babcs-release-wheel
/tmp/babcs-release-wheel/bin/python -m pip install --no-deps dist-a/*.whl
/tmp/babcs-release-wheel/bin/python -m pip check
/tmp/babcs-release-wheel/bin/python -m unittest discover -s tests -v
/tmp/babcs-release-wheel/bin/python tools/compare_methods.py \
  --output artifacts/release/installed-wheel-comparison.json \
  --csv-output artifacts/release/installed-wheel-comparison.csv \
  --plot-output artifacts/release/installed-wheel-comparison.svg \
  | tee artifacts/release/installed-wheel-comparison.log
```

Compare the source and installed-wheel JSON, CSV, and SVG artifacts byte for
byte. Investigate any difference rather than replacing the expected evidence.

### 8. Record provenance and hashes

```bash
git rev-parse HEAD > artifacts/release/SOURCE_COMMIT
python --version > artifacts/release/PYTHON_VERSION
sha256sum artifacts/release/* > artifacts/release/SHA256SUMS
```

Record the operating system, Python version, SciPy version when used, ngspice
version, source commit, wheel hash, and comparison hashes in the final release
notes.

### 9. Commit the version and release notes

```bash
git add pyproject.toml build_backend.py RELEASE.md tests
git commit -m "Prepare BAB-CS v1.1.0 release"
git push origin main
```

Wait for the exact commit's normal CI checks to complete successfully.

### 10. Create and push the tag

After explicit human approval of the exact commit and evidence:

```bash
git tag -a v1.1.0 -m "BAB-CS v1.1.0"
git push origin v1.1.0
```

The tag starts `.github/workflows/release-qualification.yml`. That workflow
runs the complete source suite, builds the candidate wheel, tests the installed
wheel, generates installed-wheel comparisons, records provenance, and uploads
the `bab-cs-release-qualification` artifact.

### 11. Review tag qualification

Before publication, verify that the downloaded qualification artifact contains:

- the expected wheel filename and SHA-256;
- `SOURCE_COMMIT` equal to the tagged commit;
- the expected Python version;
- installed-wheel JSON, CSV, SVG, and log outputs;
- `SHA256SUMS` covering the wheel and evidence;
- no failed or cancelled workflow job.

### 12. Publish the GitHub release

The current workflow qualifies and uploads an Actions artifact; it does not
create a GitHub release automatically. After human approval, create the GitHub
release for the exact `v1.1.0` tag and attach:

- `bab_cs-1.1.0-py3-none-any.whl`;
- `SHA256SUMS`;
- `SOURCE_COMMIT`;
- comparison JSON, CSV, and SVG artifacts;
- the release-qualification log or a durable evidence archive;
- the reviewed release notes from this document.

Do not publish a wheel rebuilt from a different checkout after qualification.
The released wheel must be the exact qualified artifact.

## Final Approval Checklist

- [ ] Version is `1.1.0` everywhere and no stale `1.0.0` build metadata remains.
- [ ] Release commit is clean, pushed, and identified by full SHA.
- [ ] Full long and very-long source qualification passes.
- [ ] Optional SciPy qualification passes.
- [ ] Numerical comparison changes have been reviewed.
- [ ] `ngspice` mappings and results have been reviewed.
- [ ] Two independent wheel builds are byte-identical.
- [ ] Clean installed-wheel tests pass.
- [ ] Source and installed-wheel comparison artifacts match.
- [ ] Wheel, source, environment, and report hashes are recorded.
- [ ] Tag qualification passes for the exact release commit.
- [ ] Human approval names the exact commit, tag, wheel hash, and evidence set.
- [ ] GitHub release assets are the exact qualified artifacts.

## Suggested GitHub Release Notes

### BAB-CS v1.1.0

BAB-CS v1.1.0 expands the bounded Adams-Bashforth circuit-simulation reference
into a bounded multi-method framework. The release adds explicit Euler, Heun,
RK23, AB2, backward Euler, trapezoidal, and BDF2 candidate configurations under
shared projection, correction, reference, replay, residual, energy, and
fail-closed fallback controls.

The optional sparse backend now includes compiled CSC structures, bounded
workspace reuse, native batched sensitivity solves, specialized residual and
assembly kernels, guarded nonlinear chord prediction, and a contractively
bounded Schur implicit predictor. The dependency-free dense path and extension
fallbacks remain available.

The release also broadens deterministic comparisons, work accounting,
long-horizon qualification, external ngspice evidence, wheel reproducibility,
and GitHub Actions provenance. BAB-CS remains a research implementation with
limited device coverage and is not presented as a replacement for a production
SPICE simulator.

Final source commit, wheel SHA-256, qualification workflow, environment, and
comparison hashes must be inserted here from the approved release evidence.
