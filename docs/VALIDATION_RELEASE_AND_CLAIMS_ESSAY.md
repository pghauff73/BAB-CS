# Validation, Release, and Claim Discipline in BAB-CS

## Why Does Validation Need Layers?

Bounded-Authority-Based-Circuit-Simulation (`BAB-CS`) treats validation as a
hierarchy of questions rather than one pass/fail label. A unit test can show that
one formula behaves as expected. A comparison can show that one declared case
agrees with an independent result. A package check can show that the installable
artifact reproduces the source evidence. A human release decision can approve
one exact set of artifacts. These are related, but they are not interchangeable.

For a novice, **validation** means collecting evidence that a declared behavior
matches a declared expectation. It does not mean proving that every future use
is correct. **Qualification** means running a specified evidence process for a
specific source and environment. **Certification** is an independent formal
approval process; BAB-CS does not claim certification.

## How Does the Evidence Ladder Build Confidence?

Treat evidence as a ladder. Each rung answers a larger question, but a convincing
higher-level plot cannot replace a lower-level check.

1. **Formula test — was one calculation implemented correctly?** A small test
   checks a coefficient, matrix operation, component equation, or failure rule
   in isolation.
2. **Circuit test — do the parts cooperate in a complete simulation path?** A
   circuit-level test exercises proposal, projection, reference comparison,
   acceptance, fallback, rejection, events, and reporting together.
3. **Analytic or refined authority — is the accepted trajectory close to an
   independently justified result?** An analytic solution is a known formula. A
   refined authority is a more carefully recomputed numerical result.
4. **External comparison — does a separately implemented simulator agree on the
   same translated engineering case?** This checks for shared behavior without
   treating the external tool as unquestionable truth.
5. **Source-versus-wheel equivalence — does the installable package reproduce the
   checked-out source evidence?** A wheel is the installable Python package file
   delivered to users.
6. **Exact-hash human approval — should this precise source and artifact set be
   published?** A cryptographic hash is a digital fingerprint that identifies
   exact bytes. Automation prepares this evidence; a person retains release
   authority.

The ladder prevents a common mistake: turning “one test passed” into “the product
is ready.” Each step records both what has been demonstrated and what remains
outside the claim.

## What Does Each Test Layer Prove?

The repository uses several layers of automated tests.

### Formula and Component Tests

Small tests check variable-step Adams-Bashforth order two (`AB2`) coefficients,
implicit-method startup, backward differentiation formula order two (`BDF2`)
history, waveform breakpoints, component validation, matrix operations, and
failure messages. These tests isolate one behavior so a regression can be
located precisely.

### Circuit and Controller Tests

Integration tests run complete circuit paths. They cover projection, candidate
and reference pairing, correction, recursive bounds, nonlinear convergence,
passivity, event alignment, replay, fallback, rejection, and work counters.
**Passivity** means that a passive declared circuit may not create net energy
from nothing. A **fallback** transfers authority to a safer method. A
**rejection** refuses the current attempt and normally retries with a smaller
timestep.

### Analytic and Refined-Authority Tests

Some resistor-capacitor (`RC`), resistor-inductor (`RL`), and resonant circuits
have known analytic solutions, meaning formulas can calculate the expected
trajectory directly. Other cases use refined implicit replay, which recomputes
the same interval with smaller trusted steps. Analytic truth and refined replay
are kept as different evidence types because they have different assumptions.

### Long-Horizon and Optional-Backend Tests

Long-horizon tests inspect accumulated phase, energy, authority age, and replay
behavior. Optional-backend tests exercise SciPy and SuiteSparse KLU. SciPy is a
Python scientific-computing library. KLU is a sparse matrix solver specialized
for circuit-like equation systems. A skipped optional test is recorded as a
missing qualification tier, not silently treated as a pass.

### Fail-Closed Tests

**Fail closed** means refusing to produce an accepted result when required
evidence is missing or invalid. Tests deliberately trigger nonfinite values,
singular equations, unsupported topologies, failed nonlinear iteration,
excessive residuals, invalid multistep history, passivity violations, and replay
failure. These tests are essential because an error message is part of the
simulator’s safety boundary.

## Which Question Does Each Numerical Comparison Answer?

The canonical comparison matrix covers linear, nonlinear, switched, and
long-horizon cases. It includes raw methods, bounded candidates, reference
methods, active BAB-CS, and shadow BAB-CS. **Shadow mode** runs candidate logic
and records diagnostics while the trusted reference retains accepted-state
authority. This supports staged adoption of a new method without allowing it to
change the official trajectory immediately [[15]](REFERENCES.md#ref-15).

Reports provide three views:

- **fixed-step**, where methods receive the same nominal timestep;
- **fixed-accuracy**, where rows are selected against a declared error target;
  and
- **fixed-work**, where methods are compared under a deterministic operation
  budget.

These views answer different engineering questions. Fixed-step isolates method
behavior at a common resolution. Fixed-accuracy asks what work is required to
reach a target. Fixed-work asks what result can be achieved for a controlled
algorithmic cost. No one view proves universal superiority.

## What Can External Comparison Show?

BAB-CS maps four cases to ngspice: RC step, RL step, diode clip, and switched RC.
ngspice is an open-source implementation in the SPICE family; SPICE means
*Simulation Program with Integrated Circuit Emphasis*. The comparison requires a
documented semantic translation: topology, source waveform, switch schedule,
initial state, output quantity, sample grid, and comparison norm must represent
the same engineering case [[16]](REFERENCES.md#ref-16).

ngspice provides independent evidence, not unquestionable truth or BAB-CS
accepted-state authority. Agreement can increase confidence in a mapped case.
Disagreement directs the engineer to inspect modeling semantics, tolerances,
event handling, interpolation, and numerical behavior. Two plots do not provide
validation when the underlying models are not equivalent.

## How Does Deterministic Evidence Support Review?

BAB-CS produces machine-readable JavaScript Object Notation (`JSON`) and
comma-separated-value (`CSV`) reports, plus Scalable Vector Graphics (`SVG`)
figures. JSON records structured data, CSV records tables, and SVG records vector
graphics. Deterministic generation means that the same declared source,
configuration, and environment reproduces the same required artifact bytes where
the format is defined as deterministic.

Work counts are kept separate from timing. Timing is local characterization and
can vary with the machine. Deterministic work counts identify how many candidate,
reference, projection, Jacobian, algebraic, and replay operations occurred. A
performance claim must name its workload, backend, hardware, software, warmup,
repetition policy, and comparator [[17]](REFERENCES.md#ref-17).

## Does the Installed Wheel Match the Source?

A Python **wheel** is an installable package file. Source-versus-wheel
equivalence compares the checked-out source with an isolated installation of the
built wheel. The release process does more than import the wheel and run one
example. It rebuilds evidence from the installed artifact and compares required
JSON, CSV, and SVG outputs with the source results [[20]](REFERENCES.md#ref-20)
[[31]](REFERENCES.md#ref-31).

Wheel inspection also checks the filename, metadata, command-line entry point,
included files, timestamps, and file modes. Building twice and comparing bytes
tests **reproducible packaging**, meaning the build process creates the same
artifact from the same frozen inputs.

## What Can Continuous Integration Prove?

Continuous integration (`CI`) is automated testing triggered by repository
events. The pull-request workflow runs the dependency-free suite, static
compilation checks, generation checks, package installation, and an optional
SciPy/KLU tier. Third-party workflow actions are pinned to exact revisions so
their code cannot change unnoticed [[33]](REFERENCES.md#ref-33).

Scheduled workflows add long-horizon tests, the complete numerical matrix,
timing evidence, and all mapped ngspice cases. They upload reports, figures,
logs, and checksums. Scheduled evidence is useful for regression detection, but
it may run on a moving branch. It does not approve a release.

## How Do Exact Hashes Identify Artifacts?

A cryptographic hash is a fixed-length fingerprint of digital content. BAB-CS
uses Secure Hash Algorithm 256-bit (`SHA-256`) values to identify source and
artifacts. If one byte changes, the fingerprint should change. A deterministic
manifest records file roles, sizes, hashes, source identity, package identity,
environment data, test summaries, and comparison summaries.

The verifier rejects missing, duplicate, modified, unexpected, nonfinite,
failed, or identity-mismatched evidence. A sorted checksum file binds the public
contents of the evidence bundle without attempting to include its own checksum
recursively [[31]](REFERENCES.md#ref-31).

## Why Do Humans Retain Release Authority?

Four words describe different stages and must not be blurred:

- **validation** collects evidence that a declared behavior meets a declared
  expectation;
- **qualification** runs a named validation process for an exact source,
  environment, and artifact set;
- **certification** is an independent formal approval against an external
  standard, which BAB-CS does not claim; and
- **publication** makes an approved tag, package, release, or evidence bundle
  available to others.

Automation deliberately stops before publication. A successful workflow may
show that a candidate satisfied the declared mechanical checks. It cannot decide
that the scientific interpretation, engineering scope, release notes, and claim
boundary are acceptable.

Release approval must identify one exact source commit, the intended version
tag, the wheel SHA-256 value, the manifest SHA-256 value, the workflow run, and
the reviewed evidence set [[19]](REFERENCES.md#ref-19)
[[21]](REFERENCES.md#ref-21). A branch name, short hash, mutable artifact link,
green status badge, or previous tag is not enough.

The repository may encode version `1.1.0` and contain complete qualification
infrastructure while the actual `1.1.0` release remains unapproved. The states
must stay separate:

1. implementation exists;
2. local tests pass;
3. exact-commit qualification runs;
4. evidence is reviewed;
5. a human approves exact hashes;
6. the tag and release are published; and
7. the public artifact is downloaded and independently checked.

## Where Does the Claim Stop?

Current evidence supports these structural claims:

- BAB-CS supervises multiple explicit and implicit candidate methods;
- projection and independent replay are implemented;
- failure gates and cause reporting are tested;
- deterministic comparison and packaging tools exist; and
- a release-evidence pipeline can bind source, wheel, environment, tests, and
  reports.

Current evidence does not support claims of production-SPICE replacement,
universal speed superiority, arbitrary device coverage, formal enclosure of the
unknown exact physical trajectory, hardware safety approval, or automatic
release authority.

This separation is part of the project’s value. “A test passed,” “one case was
accurate,” “the package built,” and “the release is justified” are different
statements. BAB-CS records the evidence and authority required for each instead
of compressing them into one informal success label.
