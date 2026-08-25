# BAB-CSv1

[![CI](https://github.com/pghauff73/BAB-CS/actions/workflows/ci.yml/badge.svg)](https://github.com/pghauff73/BAB-CS/actions/workflows/ci.yml)

BAB-CSv1 is a dependency-free-by-default Python reference implementation of
**Bounded Adams-Bashforth Circuit Simulation** with a reusable error-bounding
controller. SciPy is an optional acceleration dependency for larger sparse
linear systems, and a compatible system SuiteSparse KLU 2 library can add
bounded symbolic/numeric reuse.
The controller can wrap explicit Euler, Heun, Bogacki-Shampine RK23,
variable-step AB2, backward Euler, trapezoidal, or BDF2 candidates. It combines
semiexplicit modified nodal analysis, algebraic projection, an independent
implicit reference, contractive correction, embedded estimators where
available, runtime error gates, periodic replay anchors, passivity monitoring,
event-boundary history resets, and fail-closed implicit fallback.

BAB-CSv1 is intended for algorithm development and deterministic small-circuit
validation. It is not a replacement for a production sparse SPICE simulator.

## Implemented Circuit Model

The dynamic coordinates are capacitor voltages and inductor currents. At every
state evaluation the solver projects those coordinates onto the circuit's
algebraic manifold by solving KCL plus voltage constraints.

Implemented elements:

- Resistors.
- Capacitors with initial voltage.
- Inductors with initial current.
- Independent voltage and current sources.
- Constant, sine, pulse, and piecewise-linear waveforms.
- Shockley diodes with overflow-safe limiting.
- Time-controlled resistive switches.

Circuits whose algebraic system is singular or whose semiexplicit partition is
not solvable are rejected rather than regularized silently.

## Bounded Candidate Step

For step ratio `r = h_n / h_(n-1)`, the predictor is

```text
z_ab = z_n + h_n * ((1 + r/2) * f_n - (r/2) * f_(n-1))
```

AB2 remains the default candidate. Every candidate endpoint is projected by
solving the circuit's algebraic equations. An independent implicit reference is
then calculated, and active mode applies

```text
z_corrected = (1 - gamma) * z_candidate + gamma * z_reference
```

followed by a second algebraic projection. The correction gain is increased as
needed to target a closed-loop gain below one. Stiffness, projection failure,
excessive recursive bound, or loss of contraction transfers authority to the
implicit reference.

Heun, RK23, and AB2 also expose embedded lower-order estimates. Setting
`reference_interval_steps` above one enables an embedded fast path: intermediate
steps accumulate a recursive bound without an implicit reference, while a hard
`deferred_reference_bound_cap` dynamically promotes full reference authority.
Periodic independent replay remains mandatory and resets the accumulated bound.

Every configured anchor interval, BAB-CS independently replays the interval
from the previous trusted checkpoint using smaller implicit steps. The replay
endpoint replaces the provisional endpoint and rebuilds the AB history. The
default replay refinement is topology-aware: phase-sensitive circuits that
contain both capacitors and inductors retain `anchor_substeps = 4`, while
non-oscillatory built-in topologies use `minimum_anchor_substeps = 2`.
Backward-Euler replay also retains the full configured refinement. Set
`adaptive_anchor_refinement = false` to require `anchor_substeps` everywhere.

Independent replay uses an AB3 extrapolation only as the initial guess after
two matching uniform substeps. Variable or nonmatching substeps use the
variable-step AB2 extrapolation, and the first substep remains unpredicted. The
configured implicit reference method, residual tolerance, and fail-closed
Newton behavior remain authoritative. Eligible large sparse replay windows also
use a quartic extrapolation of the five most recent accepted algebraic
solutions. This is only an algebraic initial guess; a failed guess restarts from
the current accepted algebraic solution, and the same Newton residual gate
decides acceptance.

## Rollout Modes

- `disabled`: only the implicit reference integrator is authoritative.
- `shadow`: the configured candidate and all diagnostics run, but the implicit reference state is
  always accepted. This is the default.
- `active`: the projected candidate/reference blend may be accepted. The
  default performs an every-step reference; embedded AB2, Heun, and RK23 may
  defer selected references while the hard dynamic bound cap and periodic
  independent re-anchor remain enabled.

There is deliberately no unanchored candidate-only production mode in v1.

## Boundedness Meaning

BAB-CS reports separate bounds and must not conflate them:

- Algebraic and full MNA residual caps.
- Scaled candidate/reference deviation.
- Embedded candidate-pair deviation where available.
- Corrected/reference deviation.
- Positive discrete energy-injection defect.
- Conservative predictor amplification and closed-loop gain.
- A recursive internal bound estimate.
- Independent anchor/replay deviation.

The implementation does **not** claim exact indefinite trajectory accuracy for
unstable, chaotic, discontinuous, or neutrally oscillating circuits. For an
ideal LC tank, re-anchoring bounds phase deviation relative to the independent
reference; an energy bound alone would not do so.

## Run From Source

```bash
cd /home/pamela/Projects/BAB-CS
PYTHONPATH=src python -m babcs simulate examples/rc_step.json \
  --csv /tmp/babcs-rc.csv \
  --summary /tmp/babcs-rc-summary.json
```

Override the case's rollout mode with `--mode disabled`, `--mode shadow`, or
`--mode active`. Candidate controls are also available directly:

```bash
PYTHONPATH=src python -m babcs simulate examples/rc_step.json \
  --mode active \
  --candidate rk23 \
  --linear-backend auto \
  --reference-method trapezoidal \
  --reference-interval 4 \
  --bound-cap 100 \
  --contraction-rate 10
```

The default `dense` backend preserves the dependency-free deterministic path.
Install the optional sparse backend with `python -m pip install ".[sparse]"`,
then select `--linear-backend auto`. Auto mode retains dense solves below the
measured crossover and uses SciPy SuperLU for eligible sparse systems. When
NumPy and a compatible system SuiteSparse KLU 2 shared library are also present,
auto mode uses bounded KLU symbolic/numeric reuse only for large batched native
sensitivity systems and falls back to SciPy on any KLU failure.
`--linear-backend scipy` forces SuperLU. `--linear-backend klu` forces KLU and
fails clearly when NumPy or the compatible shared library is unavailable. Large
sparse nonlinear solves may reuse the previous validated factorization only as
a guarded chord predictor. Its proposed update must reduce the current residual
under the normal line search; any factor or line-search failure clears it and
immediately restores a fresh Jacobian solve.

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Run the scheduled long-horizon tier locally:

```bash
BABCS_LONG_TESTS=1 PYTHONPATH=src python -m unittest discover -s tests -v
```

Run the complete release-qualification tier, including the 1,000-period LC
case:

```bash
BABCS_LONG_TESTS=1 BABCS_VERY_LONG_TESTS=1 \
  PYTHONPATH=src python -m unittest discover -s tests -v
```

Generate deterministic method-comparison evidence:

```bash
PYTHONPATH=src python tools/compare_methods.py \
  --output /tmp/babcs-comparison.json \
  --csv-output /tmp/babcs-comparison.csv \
  --plot-output /tmp/babcs-comparison.svg \
  --timing-output /tmp/babcs-timing.json \
  --timing-repeats 3
```

The numerical JSON, CSV, and SVG exclude wall-clock measurements and are
byte-reproducible for the same source, manifest, interpreter, and platform.
Timing is written separately because it is characterization evidence, not a
correctness threshold.

When `ngspice` is installed, generate optional cross-implementation evidence:

```bash
PYTHONPATH=src python tools/compare_external.py \
  benchmarks/cases/rc_step.json \
  --output /tmp/babcs-ngspice.json \
  --netlist-output /tmp/babcs-ngspice.cir \
  --raw-output /tmp/babcs-ngspice.dat \
  --log-output /tmp/babcs-ngspice.log
```

See `docs/COMPARISON_PROTOCOL.md` and `docs/EXTERNAL_COMPARISON.md` for the
authority hierarchy, metrics, fixed-timestep/fixed-accuracy/fixed-work
interpretation, and claim boundaries.

See `docs/PERFORMANCE_OPTIMIZATION_AUDIT.md` for the latest locally validated
solver hot-path improvements, exact baseline comparison, and remaining
high-value scaling work.

See `docs/BOUNDED_CANDIDATES.md` for candidate formulas, amplification models,
fast-path rules, selection guidance, and measured linear/nonlinear tradeoffs.

Build a wheel:

```bash
python -m pip wheel . --no-deps --wheel-dir dist
```

Package identity is owned by `src/babcs/_project.py`. The build backend,
runtime `babcs.__version__`, `pyproject.toml`, wheel filename, wheel METADATA,
optional sparse dependency, compatibility tag, and console entry point are
checked together by `tests/test_build_backend.py`.

## JSON Case Format

```json
{
  "linear_backend": "auto",
  "elements": [
    {
      "type": "voltage_source",
      "name": "V1",
      "positive": "vin",
      "negative": "0",
      "waveform": 1.0
    },
    {
      "type": "resistor",
      "name": "R1",
      "positive": "vin",
      "negative": "out",
      "resistance": 1000.0
    },
    {
      "type": "capacitor",
      "name": "C1",
      "positive": "out",
      "negative": "0",
      "capacitance": 1e-6,
      "initial_voltage": 0.0
    }
  ],
  "simulation": {
    "start_time": 0.0,
    "stop_time": 0.005,
    "nominal_step": 0.00001
  },
  "babcs": {
    "rollout_mode": "active",
    "candidate_method": "rk23",
    "reference_method": "trapezoidal",
    "reference_interval_steps": 4,
    "deferred_reference_bound_cap": 100.0,
    "anchor_interval_steps": 16,
    "anchor_substeps": 4,
    "minimum_anchor_substeps": 2,
    "adaptive_anchor_refinement": true
  }
}
```

`linear_backend` may be `dense`, `auto`, `scipy`, or `klu`; it defaults to
`dense`.
See `examples/rc_step.json`, `examples/lc_tank.json`, and
`examples/pulsed_rc.json` for complete cases.

## Fail-Closed Behavior

A candidate step is rejected and retried with a smaller step when:

- The candidate projection/solve or implicit reference solve fails.
- Predictor/reference deviation exceeds its cap.
- An embedded estimate or deferred recursive bound exceeds its cap.
- Positive numerical energy injection exceeds its cap.
- Algebraic or full residuals exceed their caps.
- Independent re-anchor replay fails.
- The minimum timestep or rejection budget is exhausted.

Discontinuity breakpoints terminate a step exactly and invalidate multistep
history. AB2 then takes an implicit startup step; one-step candidates restart
directly from the event state.

## Current Limits

- Dense Gaussian elimination remains the deterministic dependency-free
  backend. In `auto` mode, eligible larger sparse systems use precompiled CSC
  stamping, reusable bounded workspaces, and native batched sensitivity solves.
  A compatible KLU 2 library is used only for qualified large batched
  sensitivities; otherwise auto uses SuperLU or dense fallback. Small,
  structurally dense, and extension-circuit paths remain dense.
- The semiexplicit element-state formulation rejects higher-index topologies.
- Device coverage is intentionally small.
- Switch events are derived from waveform breakpoints, not arbitrary analog
  threshold root finding.
- Error bounds are relative to the implemented reference and model assumptions,
  not a proof against the unknown exact physical trajectory.
- Periodic anchors replay endpoints and the preceding history state; they do not
  rewrite already emitted intermediate output samples.
- Non-embedded and implicit candidates perform an independent implicit
  reference solve on every active step. Embedded AB2, Heun, and RK23 can defer
  references, but dynamic checkpoints may intentionally remove the speedup on
  difficult nonlinear intervals.

## Qualification Automation

- `.github/workflows/ci.yml` runs the bounded pull-request matrix, deterministic
  examples and comparison smoke, optional SciPy backend qualification, then
  builds and smoke-tests the wheel.
- `.github/workflows/comparisons.yml` runs weekly long-horizon, full method,
  repeated timing, and optional `ngspice` evidence jobs without blocking pull
  requests.
- `.github/workflows/release-qualification.yml` runs the complete source suite,
  installs SciPy and `ngspice`, records exact workflow and environment identity,
  generates numerical and timing evidence, validates the complete comparison
  matrix, builds the wheel twice, qualifies the retained wheel in a clean
  environment, verifies source/installed artifact identity, and uploads a
  deterministic release-evidence bundle.
- `release-evidence-required.txt` is the canonical required-file profile for the
  qualification bundle.
- `tools/release_evidence.py` records provenance, inspects wheel identity,
  validates comparison completeness, compares artifacts byte-for-byte, writes
  `RELEASE_MANIFEST.json` and `SHA256SUMS`, and independently re-verifies the
  complete bundle.

Any changed numerical threshold, baseline, or deterministic artifact requires
human review before release publication. Qualification automation retains
`contents: read`; it does not create a tag, approve a release, publish a GitHub
release, or upload release assets. See
`docs/RELEASE_QUALIFICATION_IMPLEMENTATION_AUDIT.md` for the distinction between
implemented infrastructure and execution-time release evidence.
