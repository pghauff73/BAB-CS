# BAB-CS Release Draft

## Status

- **Proposed release:** `v1.1.0`
- **Status:** Draft; not approved for publication
- **Initial qualification tooling commit:**
  `41782a67a12be4483ab490041e2aed4fa5692990`
- **Final release source commit:** not yet selected or approved
- **Current package metadata:** `1.1.0`, owned by `src/babcs/_project.py`
- **Required before tagging:** complete exact-commit qualification and human
  review of every `RQ-*` requirement
- **Release authority:** explicit human review of the exact tagged commit and its
  qualification evidence

The proposed `v1.1.0` designation reflects a backward-compatible feature,
qualification, and performance release. The package version is encoded as
`1.1.0`; the deterministic candidate wheel is
`bab_cs-1.1.0-py3-none-any.whl`. Encoding the version does not qualify, approve,
tag, or publish the release.

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
- Uses independent derivative-defect evidence to reduce mixed C+L trapezoidal
  replay refinement, with complete-interval restart and fixed-resolution
  fallback.
- Uses AB3 differential extrapolation only as a replay initial guess after two
  matching uniform substeps.
- Uses quartic algebraic extrapolation only as a guarded initial guess on
  eligible large sparse replay windows.
- Restarts cleanly from accepted state after failed extrapolation or topology
  events.

### Sparse and nonlinear execution

- Adds optional SciPy SuperLU support through `linear_backend="auto"` and
  `linear_backend="scipy"`.
- Adds an optional `linear_backend="klu"` adapter for compatible system
  SuiteSparse KLU 2 libraries and narrowly adopts it in `auto` for qualified
  large batched sensitivity systems.
- Adds measured dense/sparse crossover rules instead of forcing sparse work on
  small systems.
- Precompiles sparse CSC structures and topology-owned stamping metadata.
- Reuses bounded per-thread sparse workspaces while retaining safe ordering
  fallback.
- Reuses KLU symbolic analysis and numeric storage through a bounded 128-entry
  per-thread LRU with exact-structure, stale-factor, eviction, and cross-thread
  restoration.
- Preserves the absolute singularity gate with unscaled KLU U-pivot checks,
  vectorizes finite and minimum-pivot validation, owns every overwritten right-
  hand-side buffer, and falls back to SciPy when automatic KLU execution fails.
- Reuses stable KLU structural/value pointers and solves directly into independent
  row-major result arrays without an intermediate transpose-copy.
- Lets the generated sparse kernel expose private raw numerical values to a
  combined KLU factor-and-batched-solve operation while returning the reusable
  factorization required by projection correction.
- Uses native batched differential-sensitivity solves and read-only reusable
  right-hand-side storage, batched inductor voltage gathering, and mutation-aware
  reactive scale arrays.
- Adds demand-gated generated residual and full sparse assembly kernels for the
  exact built-in `Circuit` type.
- Reuses demand-gated sparse assembly compilation across identical topologies
  through a bounded source cache while keeping numerical component values live.
- Lets later exact-topology circuit instances adopt a previously demand-qualified
  sparse assembly kernel on their first eligible call through a bounded LRU.
- Shares duplicate immutable built-in control values for exact circuits with at
  least 32 switches while preserving unique, custom, reassigned, and subclass
  sampling semantics.
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
- Treats representationally two-step-old sensitivity evidence as exactly two
  steps old through a scale-aware ULP tolerance without widening the age bound.
- Restores the base algebraic state and residual before exact fallback after a
  failed contraction.

### Event scheduling performance

- Compiles breakpoint providers once per simulation run for the exact built-in
  `Circuit` type.
- Deduplicates pure built-in waveform schedules by event timing while preserving
  custom waveform calls, live assignments between runs, and subclass overrides.
- Preserves exact event endpoints, history reset, and post-event implicit
  startup behavior.

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

Qualified automatic KLU reuse additionally measured mean end-to-end reductions
of 2.048%, 4.166%, 4.293%, and 3.140% on 32-channel sine, mixed, pulsed, and
switched workloads. Minimum round reductions were 1.484%, 3.674%, 4.191%, and
2.780%. State, metric, rejection, and deterministic work traces were exactly
equal to commit `259a836` in every retained comparison.

KLU hot-path follow-up work measured a further 4.131%, 6.814%, 6.020%, and
6.282% mean reduction on the same sine, mixed, pulsed, and switched workload
classes against exact commit `f21b383`. Minimum round reductions were 3.768%,
6.466%, 4.958%, and 5.668%. State, metric, rejection, and deterministic work
traces were again exactly equal.

Jacobian-only native sensitivity assembly measured another 3.742%, 4.182%,
7.960%, and 0.882% mean reduction on 32-channel sine, mixed, pulsed, and
switched workloads against exact commit `351a8e0`; minimum round reductions
were 1.165%, 2.885%, 6.608%, and 0.471%. At 64 channels the corresponding mean
reductions were 3.723%, 4.286%, 6.850%, and 6.171%. State, metric, rejection,
and deterministic work traces were exactly equal in every comparison.

Removing a second copy of NumPy's already independent mixed-inductor
sensitivity gather measured a further 1.133% mean reduction at 32 channels and
0.832% at 64 channels, again with exact state, metric, rejection, and work
traces.

Deferred-reference candidate steps now omit dense dynamic-Jacobian storage at
64 or more dynamic states and upgrade the same sensitivity result only if a
later checkpoint forces implicit authority. Against exact commit `a0d67b5`,
64-channel mixed, pulsed, and switched workloads at a reference interval of
eight improved by 1.137%, 1.363%, and 1.613% on average; minimum round gains
were 0.552%, 0.675%, and 0.992%. State, metric, rejection, fallback, and
deterministic work traces were exactly equal.

These numbers are local characterization for the named workloads and hardware.
They are not a claim that BAB-CS is generally faster than `ngspice` or another
production simulator.

## Current Validation Evidence

Implementation validation has exercised the canonical metadata, deterministic
wheel, release-evidence tooling, complete long and very-long source suite, and
workflow command surface. These runs validate the infrastructure while it is
being implemented; they are not release evidence for a final frozen commit.

The exact candidate must still be selected, qualified from a clean full SHA,
reviewed requirement-by-requirement, explicitly approved, tagged, requalified
by the tag-triggered workflow, approved for publication, published, and checked
from freshly downloaded public assets. No earlier wheel hash or report hash may
be reused after a source, test, workflow, threshold, manifest, or documentation
change.

## Compatibility

- Requires Python 3.11 or newer.
- The default installation has no runtime dependencies.
- Sparse acceleration remains optional through `scipy>=1.11`.
- KLU acceleration additionally requires NumPy and a compatible system
  SuiteSparse KLU 2 shared library; it is not bundled into the wheel.
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
- Generic `auto` sparse solves still use fresh SuperLU factorization. Automatic
  KLU symbolic/numeric reuse is intentionally limited to large batched native
  sensitivity systems until broader solve classes have independent positive
  evidence.
- Periodic replay corrects the endpoint and rebuilt history; it does not rewrite
  already emitted intermediate samples.

## Qualified Follow-up Incorporated

The ULP-aware sensitivity-age policy is now implemented as the same
mathematical two-step window with a scale-aware representational tolerance. It
has direct regression coverage and passed the August 25, 2026 source-tree run
of all 222 tests in 53.167 seconds with long, very-long, SciPy, and KLU tiers
enabled. This local run
does not replace exact-commit wheel, comparison, workflow, or human-approval
requirements.

## Release Qualification Procedure

### 1. Verify canonical identity

`src/babcs/_project.py` is the package-identity owner. Verify that the project,
runtime package, build backend, wheel, optional dependency, entry point, and
compatibility tag remain aligned:

```bash
PYTHONPATH=src python -m unittest tests.test_build_backend -v
rg -n '1\.0\.0|bab_cs-1\.0\.0' \
  pyproject.toml build_backend.py src README.md RELEASE.md tests
```

Historical audit references may retain `1.0.0`; no active build identity may.

### 2. Freeze one exact source commit

Commit and push all intended source, test, workflow, threshold, manifest, and
documentation changes. Confirm a clean worktree, normal CI success, and record
the full 40-character SHA. Any later change invalidates all downstream
qualification evidence.

### 3. Produce candidate qualification evidence

Run `.github/workflows/release-qualification.yml` with `workflow_dispatch` on
the exact frozen commit. The workflow uses candidate identity
`candidate-<first-12-source-SHA>` and performs all source, SciPy, comparison,
timing, `ngspice`, deterministic wheel, installed-wheel, and source/installed
equivalence work without publishing anything.

The required bundle contents are declared once in
`release-evidence-required.txt`. `tools/release_evidence.py` records the
environment and workflow identity, inspects the wheel and comparison matrix,
writes the deterministic candidate manifest, generates sorted checksums, and
re-verifies the complete bundle.

### 4. Verify the candidate bundle

After downloading the `bab-cs-release-qualification` Actions artifact, verify
it independently with the exact candidate SHA, candidate tag, and reviewed
wheel hash:

```bash
PYTHONPATH=src python tools/release_evidence.py verify \
  --evidence-dir artifacts/release \
  --source-commit <FULL_SOURCE_SHA> \
  --tag candidate-<FIRST_12_SOURCE_SHA> \
  --wheel-sha256 <WHEEL_SHA256>
```

Review `comparison-inspection.json`, all test and installation summaries,
source and installed numerical artifacts, the four `ngspice` bundles, timing
claim scope, threshold or baseline changes, and the requirement audit. Tooling
success is not semantic approval.

### 5. Record pre-tag human approval

Only after every applicable `RQ-001` through `RQ-022` item is proven may the
release approver authorize one exact full source SHA, `v1.1.0`, wheel SHA-256,
and manifest SHA-256. A branch name, short SHA, mutable artifact reference, or
approximate filename is insufficient.

### 6. Create and push the approved tag

```bash
git tag -a v1.1.0 <FULL_SOURCE_SHA> -m "BAB-CS v1.1.0"
git push origin v1.1.0
```

The tag-triggered workflow must reproduce the complete evidence bundle for the
exact tag and commit. Its wheel must match the approved candidate wheel or the
release stops for investigation.

### 7. Review tag qualification and approve publication

Verify the GitHub run ID, URL, event, ref, full SHA, conclusion, wheel hash,
manifest hash, complete required-file profile, and every job result. The human
publication approval must explicitly name those exact identifiers.

### 8. Publish only approved bytes

The qualification workflow retains `contents: read` and cannot create a GitHub
release. After publication approval, attach only the exact qualified wheel,
manifest, manifest hash, checksum file, environment identity, source and
installed reports, logs, `ngspice` bundles, and reviewed release notes. Never
rebuild the wheel during publication.

### 9. Verify public assets

Download the public assets into a fresh directory, run
`sha256sum --check SHA256SUMS`, verify the tag and manifest hashes, install the
downloaded wheel into a fresh environment, run `pip check` and `babcs --help`,
and preserve the final approval and evidence outside expiring Actions storage.

## Final Approval Checklist

- [ ] Version is `1.1.0` everywhere and no stale `1.0.0` build metadata remains.
- [ ] Release commit is clean, pushed, and identified by full SHA.
- [ ] Full long and very-long source qualification passes.
- [ ] Optional SciPy/KLU qualification passes with both versions recorded.
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
