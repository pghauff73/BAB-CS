# Tutorial 10: Semantic Mapping to ngspice

ngspice is an open-source circuit simulator from the Simulation Program with
Integrated Circuit Emphasis (`SPICE`) family. A semantic mapping translates a
BAB-CS case into an ngspice netlist while preserving the meaning of component
values, node orientation, waveforms, initial conditions, and dynamic-state
coordinates.

![Semantic ngspice mapping](html/assets/tutorial-10-ngspice-mapping.svg "BAB-CS JSON is mapped to an ngspice netlist, executed independently, and retained as scoped comparison evidence.")

## What You Will Learn

The external manifest owns 20 mapped cases. A manifest is a machine-readable
inventory that names every required input and its intended role. The suite
covers linear, resonant, nonlinear diode, scheduled switching, and reduced-order
power-stage cases.

## Run the Mapping Exercise

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 10-ngspice-mapping
```

This dependency-light exercise generates every netlist and checks mapping
contracts without requiring ngspice itself.

To execute all 20 comparisons when ngspice is installed:

```bash
PYTHONPATH=src python tools/run_external_suite.py \
  benchmarks/external/manifest.json \
  --output-root artifacts/external
```

## Expected Results

The structural expectation is that all 20 manifest-owned cases translate
without changing component values, waveform schedules, initial conditions, or
canonical state order. The live expectation is not exact waveform identity:
BAB-CS and ngspice use different integration, event, and nonlinear-solve paths.
Smooth linear cases are expected to agree more closely than cases dominated by
scheduled discontinuities or reduced-order switching configurations.

## Observed Data

Both commands were run on August 27, 2026. The structural exercise reported:

| Measurement | Observed value |
| --- | ---: |
| Mapped cases | `20` |
| First-order linear cases | `6` |
| Resonant and resistor-inductor-capacitor (`RLC`) cases | `5` |
| Nonlinear diode cases | `3` |
| Scheduled-switching cases | `3` |
| Reduced-order power-stage cases | `3` |
| Distinct mapped feature types | `14` |
| Total dynamic-state coordinates | `28` |
| External tool treated as an oracle | `false` |

The live suite used `ngspice-46 : Circuit level simulation program`, completed
all 20 cases, and wrote 81 files. Root-mean-square (`RMS`) difference is the
square root of the average squared state difference over the compared samples.

| Case | Maximum absolute difference | RMS absolute difference | Samples |
| --- | ---: | ---: | ---: |
| `rc_step` | `0.0051291682323232057` | `0.0033464012529142739` | `24` |
| `rc_discharge` | `0.0014134357468059688` | `0.00058899739135542708` | `72` |
| `driven_rc` | `0.0014401525975176639` | `0.000611823698698551` | `115` |
| `current_driven_rc` | `6.5365032747677354e-05` | `3.2776060941444924e-05` | `124` |
| `rl_step` | `0.000512916823232323` | `0.00033464012529142994` | `24` |
| `rl_decay` | `0.00014146597091121982` | `4.6017717728039629e-05` | `111` |
| `lc_long` | `0.013130326422457698` | `0.0054753273479576483` | `1211` |
| `lc_offset` | `0.001101557552985015` | `0.00048623547719068655` | `611` |
| `rlc_damped` | `0.0071763452565745123` | `0.0022849129475191704` | `136` |
| `rlc_overdamped` | `0.015911107856226181` | `0.0038731901233796402` | `111` |
| `rlc_driven` | `0.00020125793767961087` | `0.00011724872569275529` | `418` |
| `diode_clip` | `0.0031177968773050506` | `0.0005379440652499948` | `265` |
| `diode_rectifier` | `0.00025825500840270799` | `0.00020269449181182741` | `1011` |
| `diode_bias_recovery` | `0.0018060735306290043` | `0.00031152329235558225` | `523` |
| `switched_rc` | `0.11593356837261994` | `0.033962482648523362` | `96` |
| `switched_rl` | `0.0090394634303352372` | `0.006639984445535505` | `300` |
| `switched_rlc` | `0.025442652271918664` | `0.016758263125078453` | `372` |
| `buck_like_reduced_order` | `0.0055742268408994489` | `0.0027573672746739708` | `411` |
| `h_bridge_rl_reduced_order` | `3.730147981349861` | `0.23016505280206029` | `450` |
| `dc_link_rlc_reduced_order` | `0.018367492321976098` | `0.0075241352548316787` | `281` |

The H-bridge case has the largest maximum difference. That value occurs in a
scheduled reduced-order experiment and is an investigation target around event
handling and independent integration behavior. It is not converted into a
claim that either simulator is universally more accurate. Absolute differences
retain each state coordinate's native unit. In a mixed RLC case, the reported
maximum is the largest difference among voltage and current coordinates, so the
table is evidence for case-by-case review rather than a single cross-case score.

## Expected Versus Actual Results

The structural expectation was met: 20 cases, 14 mapped feature types, and 28
dynamic coordinates completed with preserved state ordering. Smooth first-order
and diode cases showed relatively small native-unit maximum differences. The
scheduled-switching family showed larger differences, and the reduced-order
H-bridge produced the largest maximum difference, `3.730147981349861`, with an
RMS difference of `0.23016505280206029`.

The broad expected pattern was therefore observed, but the H-bridge maximum was
larger than a close-agreement expectation. The retained summary does not locate
the exact sample or prove one cause. Plausible explanations include different
step placement around switch events, different interpolation onto comparison
times, method-specific damping or phase behavior, and small semantic
differences in ideal-switch execution. Identifying the cause requires a
time-localized trace study; it cannot be concluded from the maximum alone.

## Preserve Canonical State Order

BAB-CS stores capacitor voltages first and inductor currents second. The mapper
must export ngspice vectors in that same order. Comparing values in element-file
order can silently compare an inductor current with a capacitor voltage when a
mixed resistor-inductor-capacitor (`RLC`) case lists the inductor first.

The exercise requires every generated state-name tuple to equal the BAB-CS
dynamic-state tuple exactly.

## Preserve Nonlinear Meaning

The BAB-CS diode uses saturation current and thermal voltage in the Shockley
equation. ngspice exposes saturation current and a diode ideality factor. The
mapper converts the declared thermal voltage into the corresponding ideality
factor instead of rejecting or silently changing non-default cases.

Unsupported parameters still fail closed. Fail closed means stop with an
explicit error rather than guess a translation.

## Retain Reproducible Evidence

For every case, the suite retains:

- the generated netlist;
- ngspice raw output;
- the ngspice log;
- the BAB-CS-versus-ngspice report;
- component and artifact Secure Hash Algorithm 256-bit (`SHA-256`)
  fingerprints; and
- the tool version and executed command.

The deterministic `wrdata` vectors create one time column followed by the
canonical state columns.

## Interpret Differences

Agreement supports implementation consistency for the declared mapping. A
large difference identifies a case that needs investigation. Possible causes
include integration method, event interpolation, nonlinear iteration, source
conventions, or device-model details.

ngspice is independent comparison evidence, not an oracle. An oracle would be
an authority assumed to provide the unquestionably correct answer. This
workflow makes no such assumption.

## Theory and Practical Outcomes

The theoretical outcome is cross-implementation falsification: an independent
simulator can expose translation or numerical differences that an internal
reference might share. The practical outcome is a 20-case evidence package with
netlists, logs, raw outputs, state order, tool identity, and measured
differences. Large discrepancies become investigation targets rather than being
discarded or converted into a universal ranking.

## Conclusion

The mapping program met its structural coverage goal and produced complete live
evidence. Numerical agreement is case dependent. The H-bridge result shows why
external comparison is most useful when it preserves disagreement and directs
the next experiment instead of treating either implementation as an oracle.

## Claim Boundary

The mapping exercise proves structural coverage of 20 declared cases. The live
suite proves that ngspice 46 executed all 20 in the measured environment. The
three power-stage cases remain reduced-order numerical experiments, not
production device models.
