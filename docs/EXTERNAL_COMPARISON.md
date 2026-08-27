# Bounded-Authority-Based-Circuit-Simulation External Comparison

## Scope

`tools/compare_external.py` compares one BAB-CS JSON case with `ngspice` when
the circuit can be translated without changing its modeled semantics. This is
cross-implementation evidence, not an oracle and not proof of exact physical
trajectory error.

The adapter currently maps resistors, capacitors, inductors, independent
voltage/current sources, constant/sine/pulse/PWL waveforms, Shockley diodes with
thermal voltage preserved through ngspice ideality, and time-controlled
resistive switches. Unsupported element or parameter mappings fail closed.

## Prerequisite

Install `ngspice` and verify it is available:

```bash
ngspice --version
```

The executable can be overridden with `--executable PATH`.

## Run

```bash
PYTHONPATH=src python tools/run_external_suite.py \
  benchmarks/external/manifest.json \
  --output-root artifacts/external
```

The manifest owns 20 cases across first-order linear, resonant and RLC,
nonlinear diode, scheduled switching, and reduced-order power-stage families.
See the [20-case mapping atlas](NGSPICE_CASE_ATLAS.md) for every case, graph,
engineering question, and claim boundary. Output paths refuse overwrite unless
`--overwrite` is provided.

## Translation Contract

The generated netlist uses the case's nominal step and stop time, preserves
initial capacitor voltage and inductor current, and evaluates the same dynamic
state coordinates used by BAB-CS. Capacitor voltages are exported before
inductor currents to match BAB-CS canonical state ownership even when the input
elements are listed in another order. Explicit `bab_state_N` vectors are
created after `tran` so `wrdata` has a stable one-time-column-plus-state-columns
shape.

The adapter validates finite, strictly increasing output times and the exact
column count. Missing executables, failed processes, malformed output,
unsupported devices, or non-equivalent parameters terminate the comparison.

## Evidence Record

The JSON report contains:

- `ngspice` version and executed command.
- Source commit, dirty state, deterministic source-tree SHA-256, and environment.
- Input-case SHA-256.
- Generated-netlist SHA-256.
- Raw-output and external-log SHA-256 values.
- State names and sample count.
- Per-state final, maximum, RMS, and scaled differences.
- Complete BAB-CS and simulation configuration.
- BAB-CS diagnostic summary.
- An explicit claim-boundary statement.

The suite writes those four files for every case plus `suite.json`: 81 files for
the complete 20-case set. Preserve the JSON, generated netlist, raw data, and
log together. Hash the files and associate them with the exact source commit
before using them in a release review.

## Interpretation

Differences may arise from integration method, event conventions, nonlinear
iteration, source interpolation, or device-model details. A small difference
supports implementation consistency for the mapped case. A large difference
requires investigation; it does not by itself identify which implementation is
wrong.

External comparison is intentionally separate from analytic truth and refined
replay. It must not replace analytic convergence tests, independent anchor
checks, runtime failure-gate tests, or installed-wheel qualification.
