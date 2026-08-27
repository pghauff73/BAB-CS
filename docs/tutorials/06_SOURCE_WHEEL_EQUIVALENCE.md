# Tutorial 6: Source Versus Installed-Wheel Equivalence

Source-versus-wheel equivalence asks whether the repository code and the
installed package produce the same declared numerical artifacts. The wheel is
the installable Python package produced in Tutorial 5.

![Source and installed-wheel equivalence](html/assets/tutorial-06-source-wheel-equivalence.svg "Source, isolated module, and installed console paths must reproduce the same selected artifacts.")

## What You Will Learn

Three execution paths are compared:

1. the package imported directly from the repository source tree;
2. the package imported from an isolated installed wheel; and
3. the installed `babcs` console command.

A console command is the user-facing command-line entry point. The command-line
interface (`CLI`) is the text-based interface used to invoke it. The application
programming interface (`API`) is the Python interface imported by code.

## Run the Exercise

From a clean source tree:

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 06-source-wheel-equivalence
```

The exercise builds the wheel if Tutorial 5 has not already done so. It creates
an isolated virtual environment, removes `PYTHONPATH`, and runs outside the
repository. A virtual environment is a separate Python installation directory
used to prevent imports from leaking in from the development tree.

For an explicitly non-release experiment in a dirty tree, add `--development`:

```bash
PYTHONPATH=src python lab/support/verify.py \
  --exercise 06-source-wheel-equivalence \
  --development
```

## Expected Results

The source module, isolated installed module, and installed console command are
expected to produce byte-identical waveform and summary artifacts for every
selected deterministic case. The imported module path should resolve inside
the isolated virtual environment, and the quick Method Observatory report
should also match. Development mode is expected to mark the result as
non-release evidence.

## Observed Data

The development-mode command was run on August 27, 2026. Secure Hash Algorithm
256-bit (`SHA-256`) values identify the exact compared output bytes. The case
names use resistor-capacitor (`RC`), resistor-inductor (`RL`), and
resistor-inductor-capacitor (`RLC`) to name their component families.
`summary.json` is a JavaScript Object Notation (`JSON`) summary file, and
`trace.csv` is a comma-separated values (`CSV`) waveform table.

| Case | `summary.json` SHA-256 | `trace.csv` SHA-256 | All three paths match |
| --- | --- | --- | --- |
| RC step | `117e0894bbf6de91245c9194e6d5041a0c3aae08587361d89ca43fe35f643721` | `8be378115e723467d723077c83b500c247277eb5bb266d22764e5bd4b5b7c8fe` | `true` |
| Switched RC | `2c40ae734a64d44688ff53969579d3132909819f0d27d29afce803e2f4e725db` | `8481e2c2c90f0498d4b2495988108a01d95d85d391d8e3f84122bc1939f41679` | `true` |
| Buck-like reduced order | `75623566cec8bc832da44f3881e7369b5fb23f9bd0723de0a3e5d224f9c5f88c` | `3a01ac1cf5df963883a04af2f90cf97bc02b28abd4f0d4520422efa9bde48221` | `true` |
| H-bridge RL reduced order | `e2bb0ec5ca71ceb79ca6266bf1f7cb870c2f238d1c53d1909863f32479914300` | `fbbe47484d4228515896e188dff40a70421224e01287d6c96837a69dc1ff29ae` | `true` |
| DC-link RLC reduced order | `cc05c2ed46bb3f959425095e0c403e221531dcc1ab7d5011029073c3949016e1` | `c1497960280b0fbf1b8a81c3397c11b51546f96c66e4f692cba47023fce04a5d` | `true` |

The quick Method Observatory report also matched byte-for-byte. The Method
Observatory is the deterministic matrix that compares numerical methods under
declared work and accuracy controls. Its complete report hash is intentionally
not copied into this tutorial because the report records source provenance, so
editing this tutorial correctly changes that hash. The command output remains
the authoritative value for the exact source state being checked.

The installed module path resolved to
`<isolated-venv>/lib/python3.14/site-packages/babcs/__init__.py`, and the verifier
reported `source_tree_excluded: true`. These values show that the installed
module and console did not silently import the repository copy.

## Expected Versus Actual Results

All five selected simulations and the Method Observatory smoke report matched
byte-for-byte, so the behavioral expectation was met. The isolated path also
confirmed that the installed package, rather than the repository source, was
executed.

One result differs from a naive expectation: the complete Observatory report
hash is not stable after an unrelated source-provenance change. That behavior is
intentional because the report records which source state produced it. The
scientifically stable claim is that source and installed reports match for the
same source state, not that one provenance-bearing report hash remains constant
after the repository changes.

## Why Isolation Is Necessary

Running an installed package while the current directory is the repository can
accidentally import the source tree. That produces a false equivalence result:
the command appears to test the wheel but actually runs the development files.

The verifier therefore checks the imported module path and requires it to live
inside the isolated environment. It then compares trace files and summary files
byte-for-byte.

The selected cases include a resistor-capacitor (`RC`) transient, a switched RC
transient, and three reduced-order power-stage experiments. Reduced order means
that the model intentionally keeps only the behavior needed for the stated
numerical question.

The quick Method Observatory smoke is also compared. The Method Observatory is
the deterministic matrix that runs candidate methods under fixed-step,
fixed-accuracy, and fixed-work views.

## Read the Evidence

The verifier reports whether every selected artifact matches and whether the
source tree was excluded. Environment-specific temporary paths are normalized
to a stable placeholder before evidence is compared.

Normalization is allowed only for declared provenance fields. Numerical values,
accepted time grids, method diagnostics, and output ordering must not be
silently normalized.

## Theory and Practical Outcomes

The theoretical outcome is observational equivalence across three delivery
paths under fixed inputs. The practical test closes two common loopholes:
accidentally importing the source tree and testing only one entry point.

This exercise detects packaging omissions, import-path leaks, console-option
drift, and source-versus-distribution behavior changes. It is valuable before a
release candidate is reviewed or an experiment is shared with another team.

## Conclusion

The selected source, installed module, and installed console paths were
equivalent for the measured artifacts. This supports distribution confidence
for the declared cases while preserving a separate release-qualification gate.

## Claim Boundary

The result proves equivalence for the selected deterministic cases and the
measured package. It does not prove equivalence for every optional sparse
backend, Python version, operating system, or user configuration.
