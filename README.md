# BAB-CSv1

[![CI](https://github.com/pghauff73/BAB-CS/actions/workflows/ci.yml/badge.svg)](https://github.com/pghauff73/BAB-CS/actions/workflows/ci.yml)

BAB-CSv1 is a dependency-free Python reference implementation of **Bounded
Adams-Bashforth Circuit Simulation**. It combines a variable-step AB2 predictor
with semiexplicit modified nodal analysis, algebraic projection, an implicit
reference solution, contractive correction, runtime error gates, periodic
independent replay anchors, passivity monitoring, event-boundary history resets,
and fail-closed implicit fallback.

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

## BAB-CS Step

For step ratio `r = h_n / h_(n-1)`, the predictor is

```text
z_ab = z_n + h_n * ((1 + r/2) * f_n - (r/2) * f_(n-1))
```

The predicted differential state is projected by solving the circuit's
algebraic equations. A trapezoidal or BDF2 reference state is then calculated,
and active mode applies

```text
z_corrected = (1 - gamma) * z_ab + gamma * z_reference
```

followed by a second algebraic projection. The correction gain is increased as
needed to target a closed-loop gain below one. Stiffness, projection failure, or
loss of contraction transfers authority to the implicit reference.

Every configured anchor interval, BAB-CS independently replays the interval
from the previous trusted checkpoint using smaller implicit steps. The replay
endpoint replaces the provisional endpoint and rebuilds the AB history.

## Rollout Modes

- `disabled`: only the implicit reference integrator is authoritative.
- `shadow`: AB2 and all diagnostics run, but the implicit reference state is
  always accepted. This is the default.
- `active`: the projected AB2/reference blend may be accepted while every-step
  reference comparison and periodic independent re-anchoring remain enabled.

There is deliberately no unreferenced AB-only production mode in v1.

## Boundedness Meaning

BAB-CS reports separate bounds and must not conflate them:

- Algebraic and full MNA residual caps.
- Scaled AB-predictor/reference deviation.
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
`--mode active`.

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Build a wheel:

```bash
python -m pip wheel . --no-deps --wheel-dir dist
```

## JSON Case Format

```json
{
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
    "anchor_interval_steps": 16
  }
}
```

See `examples/rc_step.json`, `examples/lc_tank.json`, and
`examples/pulsed_rc.json` for complete cases.

## Fail-Closed Behavior

A candidate step is rejected and retried with a smaller step when:

- The AB projection or implicit reference solve fails.
- Predictor/reference deviation exceeds its cap.
- Positive numerical energy injection exceeds its cap.
- Algebraic or full residuals exceed their caps.
- Independent re-anchor replay fails.
- The minimum timestep or rejection budget is exhausted.

Discontinuity breakpoints terminate a step exactly, invalidate AB history, and
force an implicit startup step after the event.

## Current Limits

- Dense Gaussian elimination is used; large sparse circuits are out of scope.
- The semiexplicit element-state formulation rejects higher-index topologies.
- Device coverage is intentionally small.
- Switch events are derived from waveform breakpoints, not arbitrary analog
  threshold root finding.
- Error bounds are relative to the implemented reference and model assumptions,
  not a proof against the unknown exact physical trajectory.
- Periodic anchors replay endpoints and the preceding history state; they do not
  rewrite already emitted intermediate output samples.
