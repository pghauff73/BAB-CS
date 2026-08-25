# Validation, Comparison, Release, and Claim Discipline

## Test Hierarchy

BAB-CS treats validation as a hierarchy of evidence rather than a single test
command. Formula tests establish local implementation facts. Analytic circuit
solutions establish convergence on selected linear models. Refined replay
provides an independent numerical authority for supported nonlinear cases.
Long-horizon tests expose phase, energy, and recursive-bound behavior.
Cross-implementation runs compare explicit semantic mappings with ngspice.
Packaging tests establish that installed code is the code that was examined
[[15]](REFERENCES.md#ref-15) [[18]](REFERENCES.md#ref-18). No one layer is
allowed to imply all the others.

The current test tree contains 211 test methods across nineteen modules
[[32]](REFERENCES.md#ref-32). Coverage includes circuit construction,
projection, waveform breakpoints, dense and sparse linear algebra, implicit
methods, all bounded candidates, error recurrence, rollout modes, events,
failure gates, nonlinear devices, analytic accuracy, long-horizon behavior,
comparison generation, external mapping, deterministic wheel construction, and
release-evidence verification. The count describes the current source surface;
qualification still depends on the required tiers running successfully in the
intended environment.

A local source-tree validation run on August 25, 2026 used SciPy 1.18.0 with
both `BABCS_LONG_TESTS=1` and `BABCS_VERY_LONG_TESTS=1`. All 211 tests passed in
43.751 seconds with zero skips. This establishes that the essay set was updated
against a live green source tree; it does not replace the clean-environment,
installed-wheel, exact-artifact, workflow, and human-review requirements of
release qualification.

Direct numerical tests begin with exact formulas and invariants. Variable-step
AB2 coefficients are checked independently. Backward Euler, trapezoidal, and
BDF2 startup and history behavior are exercised. Candidate aliases, orders,
embedded defects, amplification models, correction gains, and fast-path
checkpoints are tested. Circuit tests verify state sign conventions, unknown
ordering, residual construction, dense/sparse structural equivalence, and
fail-closed singularity behavior.

Accuracy tests use closed-form RC, RL, RLC, and driven-RC solutions where the
project can define the authority without another simulator. The comparison
support code samples every method on common times and reports final-state,
maximum-waveform, RMS, and scaled state error. Observed order is calculated
from declared timestep sequences rather than inferred from one run
[[15]](REFERENCES.md#ref-15) [[29]](REFERENCES.md#ref-29). A method that fails a
target remains a failure; the target is not relaxed after seeing results.

Oscillators are evaluated with separate amplitude, phase, period, and energy
metrics. This separation matters because a numerical solution can conserve an
energy-like quantity while drifting in phase, or damp amplitude while keeping
period approximately correct. The long LC case therefore does not reduce
quality to one scalar error or to the internal bound alone.

Nonlinear diode and switched cases use refined implicit replay as their
authority. The authority method, maximum replay step, state indices, and common
sample times are declared in the benchmark manifest
[[22]](REFERENCES.md#ref-22). Nonlinear tests also force constrained iteration
budgets and recovery across events so that nonconvergence becomes an explicit
failure rather than an unnoticed waveform discrepancy.

The hard-gate tests inject isolated failures. They distinguish algebraic from
full residual violations, projection failure from reference failure, energy
rejection from stiffness fallback, replay failure from ordinary step rejection,
and minimum-step exhaustion from rejection-budget exhaustion
[[32]](REFERENCES.md#ref-32). These tests are essential because a simulator can
look accurate on nominal cases while committing partial state during an error
path.

Long-horizon qualification is opt-in so normal development remains practical.
The scheduled tier enables extended cases, and the release tier additionally
enables the very-long cases. These tests examine ten-, hundred-, and thousand-
period behavior, periodic re-anchors, bound resets, phase evolution, and
passivity diagnostics [[18]](REFERENCES.md#ref-18)
[[33]](REFERENCES.md#ref-33). A skipped opt-in tier is not counted as a pass for
release qualification.

## Numerical and External Comparisons

The canonical comparison manifest contains eight case families: RC and RL
steps, underdamped and overdamped RLC, driven RC, long LC, diode clipping, and
switched RC [[22]](REFERENCES.md#ref-22). Across those cases it names fifteen
method configurations, including pure implicit authorities, shadow and active
AB2, bounded explicit and implicit candidates, embedded fast paths, and a
test-only raw AB2 control. Not every method is meaningful for every case, so the
manifest declares the applicable subset explicitly.

The comparison protocol establishes an authority hierarchy. Analytic solutions
are preferred when available. Independent refined replay is next. External
simulators provide cross-implementation evidence when device semantics can be
mapped without alteration. BAB-CS implicit authorities support method
comparison, while a same-step local reference is used for runtime gating rather
than described as independent accumulated-trajectory truth
[[15]](REFERENCES.md#ref-15).

Three comparison views prevent one-sided conclusions. Fixed-timestep results
show behavior under equal temporal discretization. Fixed-accuracy analysis
selects the least deterministic work that reaches a declared target. Fixed-work
analysis selects the most accurate result within a declared operation budget.
Wall-clock timing is emitted to a separate report, because hardware, runtime,
cache, and operating-system noise should not change the numerical qualification
record [[15]](REFERENCES.md#ref-15) [[29]](REFERENCES.md#ref-29).

Bound evidence is reported in components. Candidate/reference deviation,
embedded error, corrected/reference deviation, recursive bound, pre-reset bound,
dynamic checkpoints, anchor deviation, residual ratios, and anchor-to-bound
ratios remain distinct. The empirical relationship between anchor deviations
and pre-reset bounds is characterization evidence, not a formal coverage proof
[[13]](REFERENCES.md#ref-13) [[15]](REFERENCES.md#ref-15).

External ngspice comparison has a narrower purpose. The tool generates a
netlist from a BAB-CS case, runs the selected ngspice executable, parses the raw
waveform, and compares common states [[30]](REFERENCES.md#ref-30). Four cases are
included in automated evidence: RC, RL, diode clipping, and switched RC. The
tool records the generated netlist, raw data, simulator log, version, and report
so the mapping can be reviewed rather than treated as an opaque oracle.

Semantic mismatch fails closed. For example, a diode configuration whose
thermal-voltage semantics cannot be represented by the supported ngspice
mapping is rejected rather than approximated silently
[[16]](REFERENCES.md#ref-16). Switch controls receive explicit generated sources,
and initial capacitor and inductor conditions are preserved. This discipline is
why the external evidence can support the mapped cases without becoming a
claim that BAB-CS duplicates all ngspice devices or algorithms
[[8]](REFERENCES.md#ref-8).

## CI and Release Qualification

Normal continuous integration runs on the supported Python version matrix,
compiles source and tools, executes the regression suite, compares repeated
example outputs byte-for-byte, performs a deterministic comparison smoke test,
builds and installs a wheel, and runs an optional SciPy/KLU sparse qualification
job [[33]](REFERENCES.md#ref-33). Actions are pinned to exact revisions so changes
in third-party workflow code do not enter qualification unnoticed.

The scheduled workflow extends this with long-horizon tests, the full numerical
matrix, timing evidence, and all four ngspice mappings. Numerical JSON, CSV, SVG,
timing, logs, and checksums are uploaded as artifacts
[[33]](REFERENCES.md#ref-33). Scheduled evidence is useful for regression
detection, but it does not by itself approve a release because it may run on a
moving branch and has no human decision tied to a frozen artifact.

Release qualification is designed around exact identity. The package’s
canonical metadata defines distribution name, package name, version, Python
requirement, sparse extra, wheel tag, and console entry point. The build backend,
runtime version, project metadata, tests, and evidence tool are required to
agree [[20]](REFERENCES.md#ref-20). The wheel follows the standard Python binary
distribution format [[10]](REFERENCES.md#ref-10).

The release workflow records the complete source SHA, candidate or tag identity,
Python, operating system, pip, SciPy, SuiteSparse KLU, ngspice, workflow event,
workflow ref, and workflow run. It compiles source, runs dependency-free and
SciPy/KLU source suites,
generates source comparisons, produces external evidence, builds the wheel
twice, and compares the wheel bytes. It then installs the retained wheel into a
fresh environment and repeats the required suites and comparisons
[[19]](REFERENCES.md#ref-19) [[31]](REFERENCES.md#ref-31)
[[33]](REFERENCES.md#ref-33).

Source and installed-wheel numerical reports are compared byte-for-byte in
JSON, CSV, and SVG forms. This is stronger than importing the installed package
and observing one smoke result: it requires the packaged implementation to
reproduce the complete declared numerical evidence. Wheel inspection also
checks filename, metadata, entry point, members, timestamps, and modes
[[20]](REFERENCES.md#ref-20) [[31]](REFERENCES.md#ref-31).

The evidence bundle has a canonical required-file profile. A deterministic
manifest records file roles, sizes, hashes, source and package identity,
environment data, test summaries, and comparison summaries. Verification
rejects missing, duplicate, modified, unexpected, nonfinite, failed, or
identity-mismatched evidence. A sorted checksum file binds the bundle’s public
contents without including itself recursively [[31]](REFERENCES.md#ref-31).

Automation deliberately stops before publication. The release workflow has
read-only repository contents permission and uploads qualification artifacts;
it does not create a GitHub release. Human approval must identify one exact
source SHA, `v1.1.0` tag, wheel SHA-256, manifest SHA-256, workflow run, and
reviewed evidence set [[19]](REFERENCES.md#ref-19)
[[21]](REFERENCES.md#ref-21). A branch name, short hash, mutable artifact link,
or successful status badge is insufficient release authority.

The repository currently encodes package version `1.1.0`, but the draft release
document explicitly states that the final release source has not been selected
or approved [[21]](REFERENCES.md#ref-21). The existing `v1.0.0` tag is therefore
not evidence that the `1.1.0` candidate has been published. Qualification
infrastructure may be complete while candidate execution, semantic review,
tagging, release publication, public checksum verification, and fresh public
installation remain pending.

Performance claims follow the same discipline. The performance audit names
workloads, sizes, backends, environments, warmups, repetitions, comparators, and
retained or rejected candidates [[17]](REFERENCES.md#ref-17). Timing does not
serve as a correctness gate. A local reduction is not generalized to other
hardware or circuits, and incremental optimization percentages are not added as
though they were independent factors.

## Claim Boundary

The strongest current claims are therefore structural. BAB-CS has a bounded
multi-method controller; projection and periodic independent replay are
implemented; fail-closed gates are directly tested; deterministic comparison
and packaging tools exist; and a release evidence pipeline can bind source,
wheel, environment, tests, and reports. Claims that remain outside the evidence
include production-SPICE replacement, universal speed superiority, formal
exact-trajectory enclosures, arbitrary device coverage, and automatic release
approval.

This claim discipline is part of the research contribution. Numerical software
often collapses “the test passed,” “the method was accurate on one case,” “the
wheel built,” and “the release is scientifically justified” into one informal
status. BAB-CS keeps those statements separate and records the evidence needed
for each. That separation makes negative results, skipped tiers, semantic
mappings, and human authority visible rather than converting them into implied
success.
