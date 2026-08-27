# BAB-CS Observatory, Atlas, Sandbox, and Lab Implementation Plan

> **Historical-scope notice:** This plan defines the original six-exercise
> teaching surface. The current ten-exercise lab and the 20-case ngspice
> expansion are additive and are owned by
> `NGSPICE_AND_TEACHING_TUTORIAL_EXPANSION_PLAN.md`. The six-exercise statements
> below remain unchanged because they define the acceptance boundary of this
> earlier plan, not the current repository count.

**Status:** Proposed
**Prepared:** August 27, 2026
**Applies to:** Bounded-Authority-Based-Circuit-Simulation after the current
authority, event, finite-time, and compiled-topology corrections are fully
qualified.

## 1. Objective

Extend BAB-CS with four connected, evidence-producing facilities:

1. a **Method Observatory** that compares every implemented candidate method
   on a common six-case circuit set at fixed step, fixed accuracy, and fixed
   deterministic work;
2. a **Bound Coverage Atlas** that relates independent authority error to the
   recursive internal bound, anchor behavior, phase, energy, fallback, and
   rejection evidence;
3. a **Power-Stage Sandbox** containing three deliberately reduced-order
   switched experiments supported by the current device model; and
4. a **Teaching and Reproducibility Lab** with compact, executable exercises
   covering numerical formulation, authority semantics, deterministic
   packaging, and source-versus-wheel equivalence.

These facilities shall reuse the existing comparison, simulation, provenance,
and release-evidence infrastructure. They shall not create a second solver, a
parallel metric definition, or an ungoverned benchmark path.

## 2. Claim Boundary

The implementation shall preserve the following boundaries in code, generated
reports, and documentation:

- The observatory compares implemented numerical behavior; it does not prove
  universal superiority of one method.
- Fixed-accuracy and fixed-work results are selected from measured rows. The
  reports shall not invent unexecuted configurations through interpolation.
- The recursive bound is internal, reference-relative evidence. Empirical
  coverage against analytic or refined authority is characterization, not a
  formal enclosure theorem.
- Refined replay is independent of the candidate trajectory but can still
  share numerical kernels. Reports shall identify that limitation.
- Phase and energy are separate quantities. Bounded energy shall never be
  described as proof of bounded phase error.
- The power-stage examples are **reduced-order numerical experiments, not
  production device models**. They omit switching loss, parasitics, magnetic
  saturation, semiconductor charge storage, thermal behavior, EMI, control-loop
  dynamics, and hardware safety analysis unless a later governed model adds
  and qualifies those effects.
- Wall-clock timing remains a separate, non-deterministic characterization
  artifact and shall not be a correctness or release gate.
- Generated evidence is valid only for its recorded source tree, manifest,
  environment, and artifact hashes.

## 3. Existing Baseline to Reuse

The current repository already provides most of the required substrate:

- `benchmarks/manifest.json` defines RC, RL, RLC, LC, diode-clip, and
  switched-RC cases, analytic or refined authority, accuracy targets, and work
  budgets.
- `tools/compare_methods.py` runs deterministic method matrices and emits JSON,
  CSV, SVG, fixed-accuracy, and fixed-work analyses.
- `src/babcs/bounded.py` exposes candidate/reference, recursive-bound,
  passivity, replay, fallback, and anchor metrics.
- `src/babcs/simulator.py` records accepted points, event boundaries,
  rejections, and history-reset causes.
- `tools/release_evidence.py` and the build backend provide source, wheel,
  checksum, and qualification evidence.
- The implemented candidate set is `explicit_euler`, `heun`, `rk23`, `ab2`,
  `backward_euler`, `trapezoidal`, and `bdf2`.

The work is therefore primarily a schema, coverage, reporting, experiment, and
teaching extension. Solver changes are allowed only when missing observability
prevents a requested metric from being computed correctly.

## 4. Common Architecture

### 4.1 One canonical experiment record

Create one versioned, deterministic run-record schema owned by a shared
repository-only support module. `tools/compare_methods.py`, the Method
Observatory, and the Bound Coverage Atlas shall consume this schema rather than
recomputing equivalent facts independently.

Proposed files:

- `tools/experiment_records.py`
- `benchmarks/schemas/experiment-record-v1.schema.json`
- `benchmarks/schemas/experiment-manifest-v1.schema.json`
- `tests/fixtures/experiment-record-v1.json`

Each run record shall contain:

- exact case and method identifiers;
- complete `BABCSConfig` values;
- input, manifest, source-tree, and authority hashes;
- success, controlled rejection, or execution-failure status;
- accuracy, bound, phase, energy, robustness, and deterministic-work groups;
- applicability markers for metrics that do not exist for a baseline method;
- stable machine-readable reason codes plus human-readable messages; and
- no wall-clock fields.

Schema evolution shall be additive within a schema version. A breaking field or
semantic change requires a new version and an explicit migration test.

### 4.2 Deterministic and timing evidence remain separate

Every facility shall produce deterministic numerical evidence independently of
timing evidence:

```text
artifacts/
  observatory/
    numerical.json
    fixed-step.csv
    fixed-accuracy.csv
    fixed-work.csv
    accuracy-by-work.svg
  bound-atlas/
    atlas.json
    samples.csv
    coverage.svg
  power-stage/
    <case>/trace.csv
    <case>/summary.json
  teaching-lab/
    verification.json
  timing/
    observatory-timing.json
```

Deterministic artifacts shall reproduce byte-for-byte for an identical source,
manifest, environment, and selected matrix. Timing artifacts shall record
repeats and environment but remain informational.

### 4.3 Authority ownership

Every case shall name exactly one comparison authority:

- **analytic:** RC, RL, linear RLC, and LC where the stated topology has a
  supported closed form;
- **refined replay:** diode clip, switched RC, and the power-stage experiments;
- **external:** optional later evidence only, never silently substituted for a
  missing analytic or refined authority.

Authority traces shall be generated once per case and sample grid, hashed, and
reused by all methods in that experiment. A candidate method shall never
generate its own comparison authority.

### 4.4 Stable reason taxonomy

Replace report-side parsing of free-form rejection text with stable categories
while retaining the original text for diagnosis. Initial categories shall
cover:

- `minimum_step`
- `non_finite_metric`
- `projection_failure`
- `reference_nonconvergence`
- `candidate_nonconvergence`
- `predictor_reference_cap`
- `anchor_reference_cap`
- `recursive_bound_cap`
- `algebraic_residual_cap`
- `full_residual_cap`
- `energy_injection_cap`
- `stiffness_transfer`
- `non_contractive`
- `event_restart`
- `replay_failure`
- `linear_solve_failure`
- `configuration_error`
- `unknown`

Compatibility tests shall prove that existing summary fields and human-readable
messages remain available.

## 5. Work Package MO: BAB-CS Method Observatory

### MO-1. Canonical six-case matrix

Create `benchmarks/observatory/manifest.json` with these required cases:

| Case | Required authority | Primary purpose |
| --- | --- | --- |
| RC step | analytic | first-order decay and startup |
| RL step | analytic | current-state dynamics and stiffness scaling |
| damped RLC | analytic | coupled state and damping |
| lossless LC | analytic | long-horizon phase and energy |
| diode clip | refined replay | nonlinear solve and limiting |
| switched RC | refined replay | event alignment and history restart |

The observatory may reference the existing case JSON files by hash or move them
to a shared case directory in one atomic change. It shall not keep divergent
copies with the same case identifier.

Each case shall define:

- a required step grid with at least three refinements;
- state indices and physical labels;
- authority configuration and sample grid;
- accuracy targets and deterministic-work budgets;
- required and exploratory rows;
- phase and energy applicability;
- expected event count where applicable; and
- explicit maximum matrix size and runtime tier.

### MO-2. Every implemented candidate method

Run all seven candidate methods on all six cases. The bounded controller shall
remain the owner of projection, correction, gates, fallback, and replay.

Use explicit candidate/reference profiles:

| Candidate | Reference method | Startup | Default reference interval |
| --- | --- | --- | ---: |
| `explicit_euler` | `trapezoidal` | `backward_euler` | 1 |
| `heun` | `trapezoidal` | `backward_euler` | 1 |
| `rk23` | `trapezoidal` | `backward_euler` | 1 |
| `ab2` | `trapezoidal` | `backward_euler` | 1 |
| `backward_euler` | `trapezoidal` | `backward_euler` | 1 |
| `trapezoidal` | `bdf2` | `backward_euler` | 1 |
| `bdf2` | `trapezoidal` | `backward_euler` | 1 |

Eligible embedded candidates may have additional named deferred-reference
profiles, but these shall be separate rows rather than replacements for the
every-step reference profile. Raw AB2 and authority-only implicit methods may
remain contextual baselines; they do not satisfy the “all candidate methods”
coverage requirement by themselves.

Required matrix coverage is at least:

```text
6 cases * 7 candidates * 3 step sizes = 126 required fixed-step rows
```

Any omitted candidate/case row is a qualification failure. A coarse exploratory
row may end in a controlled rejection, but every candidate/case pair shall have
at least one required successful row.

### MO-3. Fixed-step report

The fixed-step report shall contain one row per executed configuration and
shall report:

- nominal and accepted step statistics;
- maximum, RMS, final, and per-state authority error;
- observed convergence order where enough successful refinements exist;
- phase, period, amplitude, and energy metrics when applicable;
- recursive-bound and anchor summaries;
- rejection, fallback, event, reset, and replay counts;
- deterministic work by component and in aggregate; and
- execution status and reason code.

The report shall preserve failed and rejected rows. It shall never present only
the successful subset without a visible coverage accounting.

### MO-4. Fixed-accuracy report

For each case, candidate, and configured accuracy target:

1. filter to measured successful rows meeting the target;
2. select the row with minimum deterministic work;
3. break ties by smaller measured error, then smaller step, then stable method
   identifier;
4. report the selected source row identifier; and
5. emit `no_qualifying_row` when the measured grid does not meet the target.

No interpolation or extrapolation is allowed in the qualification report. A
separate explicitly labeled exploratory analysis may fit convergence curves,
but fitted values shall not be used as selected evidence.

### MO-5. Fixed-work report

For each case, candidate, and configured deterministic-work budget:

1. filter to measured successful rows at or below the budget;
2. select the row with minimum maximum authority error;
3. break ties by lower RMS error, then lower work, then stable row identifier;
4. report unused budget and the selected source row; and
5. emit `no_qualifying_row` when no measured row fits.

Work shall use existing deterministic counters, not elapsed time. Any change to
the aggregate work formula requires a schema version change and before/after
report.

### MO-6. Observatory outputs

Implement:

- `tools/method_observatory.py` as a thin CLI over shared experiment records;
- deterministic JSON, flattened CSV, SVG, and generated Markdown summaries;
- `docs/METHOD_OBSERVATORY.md` documenting commands and interpretation; and
- compact quick, full, optional-backend, and release tiers.

The generated Markdown shall link each selected fixed-accuracy and fixed-work
row back to its exact fixed-step row identifier.

### MO acceptance gates

- The manifest names all six required cases and all seven candidates.
- The required fixed-step matrix contains exactly the expected row keys.
- Every candidate/case pair has at least one successful required row.
- Fixed-accuracy and fixed-work selectors use measured rows only.
- Two identical quick runs produce byte-identical JSON, CSV, and SVG.
- Reordering manifest objects without changing semantics does not change row
  identifiers or selection results.
- Timing fields cannot enter deterministic reports.
- Existing comparison reports remain readable or have an explicit migration.

## 6. Work Package BA: BAB-CS Bound Coverage Atlas

### BA-1. Per-sample authority alignment

Generate an authority value at every accepted simulation time, including exact
event boundaries. Store authority generation separately from candidate
execution and record the authority trace hash.

For each accepted bounded step, calculate the following weighted norms with the
same state scaling used by the controller:

```text
actual_authority_error
  = ||z_candidate(t) - z_authority(t)||_W

authority_epoch_drift_error
  = ||(z_candidate(t) - z_candidate(t_anchor))
      - (z_authority(t) - z_authority(t_anchor))||_W

recursive_internal_bound
  = the accepted StepMetrics.estimated_bound
```

The global actual error answers “how far is this state from the declared
authority?” The epoch drift error is the closer empirical comparator for a
bound that resets at independent anchors. Both shall be reported; neither shall
be relabeled as a proof of physical error.

### BA-2. Coverage definitions

For coverage-eligible samples, report:

```text
error_to_bound_ratio
  = authority_epoch_drift_error / recursive_internal_bound

bound_to_error_coverage_ratio
  = recursive_internal_bound / authority_epoch_drift_error

covered
  = authority_epoch_drift_error <= recursive_internal_bound
```

Samples are coverage-eligible only when:

- a bounded candidate step was accepted;
- the recursive bound is positive and finite;
- the authority and epoch anchor are available;
- the point is not the anchor/reset sample itself; and
- no metric is marked not applicable.

Zero-over-zero, zero-bound, non-finite, reset, and unavailable samples shall be
counted separately rather than coerced to zero or infinity.

Aggregate each case/method/profile by:

- eligible sample count;
- empirical coverage fraction;
- median, 95th percentile, and maximum error-to-bound ratio;
- maximum consecutive uncovered samples;
- coverage by anchor age bucket;
- coverage immediately before reanchor; and
- coverage before and after events.

These fields are empirical characterization only. The generated report shall
repeat that limitation next to every aggregate coverage table.

### BA-3. Anchor evidence

Report for every periodic, event-forced, and safety anchor:

- anchor generation and authority age;
- pre-reset recursive bound;
- provisional-to-replay anchor deviation;
- actual authority error before and after replacement;
- replay method, subdivisions, retries, embedded evidence, and work;
- replay-native energy balance and maximum injection ratio;
- final algebraic and full residuals; and
- whether any hard cap changed authority or rejected the attempt.

Event history reset and authority refresh shall remain separately identifiable.
The atlas shall not infer an independent anchor from a multistep-history reset.

### BA-4. Phase and energy evidence

For LC and applicable RLC rows, report:

- instantaneous and final phase error;
- relative period error;
- amplitude error;
- stored-energy range and relative energy span;
- cumulative signed energy-balance defect;
- maximum positive energy-injection ratio; and
- phase error at equal-energy-error bands.

For RC, RL, diode, switched, and power-stage cases, report available stored
energy, source work, dissipation, and passivity defect without fabricating a
phase metric. Non-applicable fields shall be explicit nulls with an
applicability reason.

### BA-5. Fallback and rejection causes

Emit both sample-level and aggregate cause evidence:

- attempts, accepted steps, and rejected attempts;
- stable primary and contributing reason codes;
- requested and suggested step;
- candidate and effective method;
- implicit authority transfers and bound fallbacks;
- dynamic reference checkpoints;
- event and other history-reset causes;
- periodic and safety reanchors; and
- first and last occurrence times.

If one attempt crosses more than one gate, preserve all observed contributing
causes and name the primary cause that determined control flow.

### BA-6. Atlas outputs

Implement:

- `tools/bound_coverage_atlas.py`;
- `benchmarks/atlas/manifest.json`, referencing observatory cases by stable ID;
- `docs/BOUND_COVERAGE_ATLAS.md`;
- deterministic aggregate JSON and sample-level CSV; and
- SVG views for error versus bound, coverage versus anchor age, phase versus
  energy, and rejection/fallback categories.

The atlas shall consume the observatory run records when configurations match.
It shall not rerun a hidden variant with the same row identifier.

### BA acceptance gates

- Analytic cases match direct analytic evaluations at accepted times.
- Refined authorities land exactly on declared events and stop time.
- Global actual error, epoch drift error, and internal bound remain distinct.
- Coverage denominators exclude and count reset/non-applicable samples.
- Anchor rows expose pre- and post-replacement evidence.
- Phase and energy are reported independently.
- All rejection and fallback records have stable categories.
- Aggregate counts reconcile exactly with sample records and simulation
  summaries.
- Double generation is byte-identical.

## 7. Work Package PS: BAB-CS Power-Stage Sandbox

### PS-1. General constraints

Add the examples under `examples/power_stage/` with a directory README that
begins with this statement:

> These are reduced-order numerical experiments, not production device models.

Each case shall use only currently supported, qualified element semantics:
resistors, capacitors, inductors, independent voltage/current sources, Shockley
diodes, scheduled resistive switches, and existing waveforms. No case may imply
an unimplemented MOSFET, IGBT, body-diode, transformer, saturation, thermal, or
control-loop model.

Each example shall include metadata naming:

- educational purpose;
- omitted physical effects;
- intended event schedule;
- authority configuration;
- expected qualitative behavior;
- safe numerical parameter range; and
- non-production claim text.

### PS-2. Simplified buck-like converter

Proposed topology:

```text
Vdc -> scheduled high-side resistive switch -> switch node -> L -> output
ground -> freewheel Shockley diode -> switch node
output -> C || Rload -> ground
```

The schedule shall contain repeated on/off intervals with exact breakpoints.
The experiment shall demonstrate inductor-current continuity, output-capacitor
ripple, diode conduction during the off interval, event-aligned history
restart, and independent replay.

Required checks:

- no accepted point crosses a switch event;
- all states and powers remain finite;
- KCL and full residuals remain below configured caps;
- inductor current and capacitor voltage remain continuous at scheduled events;
- replay authority exists at every event;
- source work, dissipation, and stored-energy change reconcile within the
  declared reduced-order tolerance; and
- a refined authority run bounds the reported waveform error.

### PS-3. Scheduled H-bridge RL load

Proposed topology:

- one DC source;
- four scheduled resistive switches forming two bridge legs;
- one series RL load between leg midpoints; and
- piecewise gate schedules with explicit dead time and polarity reversal.

This case intentionally models switch conduction as scheduled resistance. It
does not model transistor charge, body diodes, shoot-through physics, or a PWM
controller.

Required checks:

- no upper/lower switch pair in one leg is simultaneously scheduled on;
- declared dead-time intervals are present in the compiled breakpoint set;
- load current remains continuous through polarity transitions;
- applied load voltage follows the scheduled bridge state;
- event count and event times match the manifest exactly;
- fallback/rejection causes are reported rather than hidden; and
- refined replay produces a deterministic comparison trace.

### PS-4. DC-link RLC startup and interruption

Proposed topology:

```text
Vdc -> scheduled connection switch -> series R-L -> dc-link node
dc-link node -> C || Rload -> ground
```

The connection closes for startup and opens at a declared interruption time,
leaving the stored energy to decay through the qualified reduced-order path.

Required checks:

- startup and interruption are exact event boundaries;
- capacitor voltage and inductor current are continuous at switching times;
- startup overshoot, ringing, and decay are separately reported;
- phase is reported only during a qualified oscillatory interval;
- energy before and after interruption is accounted for without claiming
  hardware fault behavior; and
- the refined authority trace and event schedule are deterministic.

### PS-5. Sandbox artifacts and tests

Add:

- `examples/power_stage/buck_like_reduced_order.json`
- `examples/power_stage/h_bridge_rl_reduced_order.json`
- `examples/power_stage/dc_link_rlc_reduced_order.json`
- `examples/power_stage/README.md`
- `benchmarks/power_stage/manifest.json`
- `tests/test_power_stage_examples.py`
- `docs/POWER_STAGE_SANDBOX.md`

The examples shall be runnable through the normal `babcs simulate` CLI. The
benchmark manifest shall add refined authority and observatory/atlas profiles
without changing the human-readable examples.

### PS acceptance gates

- All three examples parse and run through the public CLI.
- Metadata and docs contain the exact reduced-order/non-production label.
- Event schedules are deterministic and fully asserted.
- Continuity, residual, finite-state, and energy checks pass.
- Two runs of every example produce identical trace and summary files.
- Source and installed-wheel runs agree under the equivalence protocol.
- Optional external comparisons, if added later, are explicitly mapped and do
  not become implicit authority.

## 8. Work Package TL: BAB-CS Teaching and Reproducibility Lab

### TL-1. Dependency-light lab structure

Use Markdown, JSON cases, the public CLI, and small standard-library checkers.
Do not require notebooks, a browser, SciPy, or plotting packages for the core
lab.

Proposed layout:

```text
lab/
  README.md
  01-mna/
  02-convergence/
  03-phase-versus-energy/
  04-shadow-authority/
  05-deterministic-packaging/
  06-source-wheel-equivalence/
  support/
    verify.py
```

Every exercise shall contain:

- learning objective;
- prerequisite concepts;
- one compact case or manifest;
- exact commands;
- questions requiring interpretation rather than copying output;
- deterministic assertions;
- expected evidence files; and
- a conservative claim boundary.

### TL-2. Exercise 1: Modified nodal analysis

Use a small RC or RL circuit to identify dynamic and algebraic unknowns, derive
KCL/constraint equations, inspect compiled topology, and compare the derived
equations with one BAB-CS evaluation.

Checks shall cover node indexing, dynamic-state labels, algebraic residual, and
the distinction between state variables and node voltages.

### TL-3. Exercise 2: Convergence

Run at least three fixed-step refinements for RC and one second-order method.
Calculate maximum and RMS authority error plus observed order from generated
records.

The exercise shall show that a single small error is not convergence evidence
and that event/nonlinear cases require different authority treatment.

### TL-4. Exercise 3: Phase versus energy

Use the LC case to compare at least two methods over multiple periods. Plotting
is optional; the required checker shall report phase error, period error,
amplitude error, and relative energy span numerically.

The completion question shall require the learner to explain why small energy
span does not imply small phase error.

### TL-5. Exercise 4: Shadow authority

Run the same case in implicit-only, shadow, and active modes. Demonstrate that
shadow mode computes candidate diagnostics while accepted state authority
remains implicit.

Checks shall verify rollout mode, candidate usage metrics, accepted-state
equivalence where promised, reference work, and the absence of a claim that a
shadow candidate controlled the trajectory.

### TL-6. Exercise 5: Deterministic packaging

Build the wheel twice from one clean source state, compare wheel hashes, inspect
the archive ordering/timestamps, and record the exact source commit and source
tree hash.

The exercise shall fail closed on a dirty source tree unless explicitly run in
development mode, where the result must be labeled non-release evidence.

### TL-7. Exercise 6: Source versus wheel equivalence

Run the same compact RC and switched-RC cases from:

1. `PYTHONPATH=src`;
2. a clean environment containing only the built wheel; and
3. the installed console/module entry point.

Normalize only provenance fields that are intentionally different. Trace,
summary, selected numerical report rows, schema version, case hash, and method
configuration shall otherwise match byte-for-byte.

The exercise shall explain that equivalent output for selected cases is scoped
evidence, not proof that every source path and optional backend is equivalent.

### TL-8. Lab verification

Implement `python lab/support/verify.py --exercise all` with machine-readable
results. It shall never modify checked-in expected files without an explicit
`--update-fixtures` option, and that option shall print a review warning and the
changed hashes.

Add `tests/test_teaching_lab.py` to verify commands, fixtures, clean temporary
directories, and failure messages. Core lab verification shall run in pull
request CI; wheel-building exercises may run in the installed-wheel job.

### TL acceptance gates

- All six requested topics have one independently runnable exercise.
- Every exercise has deterministic assertions and a claim boundary.
- Core exercises run without optional dependencies.
- Packaging exercises record source and artifact hashes.
- Source-versus-wheel comparison uses isolated execution environments.
- Fixture updates cannot occur accidentally.
- The lab README gives one short path and one full path through the material.

## 9. Cross-Cutting Validation Plan

### 9.1 Unit tests

Add focused tests for:

- manifest and schema validation;
- exact candidate/case matrix coverage;
- stable row identifiers;
- fixed-accuracy and fixed-work tie-breaking;
- reason-code compatibility;
- authority trace alignment at events;
- coverage eligibility and zero-bound handling;
- anchor pre/post accounting;
- power-stage event schedules and continuity; and
- lab fixture and verifier behavior.

### 9.2 Deterministic integration tests

Run quick observatory, atlas, sandbox, and lab generation twice in separate
temporary directories. Compare every deterministic output byte-for-byte and
verify all embedded hashes.

### 9.3 Numerical qualification

After focused tests pass:

1. run the complete dependency-free test suite;
2. run optional SciPy and KLU qualification;
3. run long and very-long LC tests;
4. execute the full observatory matrix;
5. execute the full bound atlas;
6. execute all power-stage refined authorities;
7. run all teaching-lab checks; and
8. review every controlled rejection and `no_qualifying_row` result.

No report is qualified merely because its generator exits zero. Matrix
coverage, authority hashes, selection provenance, and reconciliation checks
must also pass.

### 9.4 Packaging qualification

- Build two wheels from the same clean exact source commit.
- Require byte-identical wheel hashes.
- Install one wheel in a clean environment without the source tree on
  `PYTHONPATH`.
- Run the public examples, sandbox examples, observatory smoke, and lab
  source-wheel exercise.
- Record source commit, source-tree hash, wheel hash, manifests, reports, and
  environment in release evidence.

### 9.5 Documentation and claim audit

Update:

- `README.md`
- `docs/index.md`
- `docs/COMPARISON_PROTOCOL.md`
- `docs/ERROR_BOUND_MODEL.md`
- `docs/APPLICATIONS_AND_RESEARCH_ROADMAP.md`
- `docs/MINIMAL_REPRODUCIBLE_RESEARCH.md`
- `docs/CURRENT_WORK.md`
- `CHANGELOG.md`

Run a requirement-to-evidence audit mapping every requirement in this plan to
source, tests, deterministic artifacts, and unresolved limitations. Historical
measurements shall remain historical; current reports shall not silently reuse
stale counts, timing, or hashes.

## 10. Implementation Sequence

### Phase 0: Qualify the current authority corrections

- Finish and document the current event/authority reset, replay-energy,
  finite-time, representable-time, and compiled-topology corrections.
- Run full source and optional-backend qualification.
- Freeze the new metric semantics before building atlas evidence on them.

**Gate:** no known stale authority, event, energy, or time-boundary metric.

### Phase 1: Shared experiment records

- Extract canonical record construction from `tools/compare_methods.py`.
- Add schemas, reason codes, row IDs, applicability, and reconciliation tests.
- Preserve existing comparison output through compatibility tests.

**Gate:** old comparison smoke passes and new records are byte-deterministic.

### Phase 2: Method Observatory

- Add the six-case/all-candidate manifest.
- Implement fixed-step, fixed-accuracy, and fixed-work views.
- Add coverage accounting and generated documentation.

**Gate:** 126 required fixed-step rows are accounted for and every
candidate/case pair has a successful required row.

### Phase 3: Bound Coverage Atlas

- Add accepted-time authority traces and epoch-aligned error.
- Add coverage, anchor, phase/energy, and cause outputs.
- Reconcile sample and aggregate reports.

**Gate:** all atlas aggregates derive exactly from deterministic sample rows.

### Phase 4: Power-Stage Sandbox

- Add and tune one experiment at a time: buck-like, H-bridge RL, then DC-link
  RLC.
- Add refined authority and continuity/event/energy tests before proceeding to
  the next case.

**Gate:** all three cases satisfy the reduced-order claim and numerical gates.

### Phase 5: Teaching and Reproducibility Lab

- Build exercises in conceptual order.
- Reuse observatory and release-evidence commands.
- Add isolated source/wheel checks last.

**Gate:** a clean user can run the short path without optional dependencies and
the full path reproduces the recorded evidence.

### Phase 6: Full qualification and promotion

- Run all source, optional-backend, long-horizon, deterministic, and packaging
  tiers.
- Generate the requirement-to-evidence audit.
- Obtain human review of claim language, changed thresholds, exact source hash,
  and exact wheel hash before release promotion.

**Gate:** deterministic evidence is complete and a human approves the exact
artifacts. Automated success alone does not authorize publication.

## 11. Recommended Pull-Request Slices

1. **Experiment records and reason taxonomy** — schema and compatibility only.
2. **Method Observatory** — six-case/all-candidate matrix and three report
   views.
3. **Bound Coverage Atlas** — authority alignment and coverage evidence.
4. **Buck-like sandbox experiment** — first reduced-order example and shared
   sandbox conventions.
5. **H-bridge and DC-link experiments** — remaining power-stage cases.
6. **Teaching Lab fundamentals** — MNA, convergence, phase/energy, shadow.
7. **Packaging Lab and final qualification** — deterministic wheel and
   source/wheel equivalence.

Each slice shall be independently reviewable, preserve deterministic fixtures,
and include its own requirement-to-test mapping. Do not combine solver semantic
changes with report formatting unless the semantic change is necessary to
produce a correct requested metric.

## 12. Principal Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Comparison authority shares a kernel with a candidate | Record authority method and refinement; keep analytic cases; allow explicit external evidence later |
| Matrix size obscures missing rows | Compute expected row keys before execution and fail on omissions or duplicates |
| Fixed-accuracy/work summaries hide failure | Preserve all fixed-step rows and link every selected summary row to its source |
| Recursive bound is compared to the wrong error | Report global error and anchor-epoch drift separately; define coverage eligibility |
| Event points distort coverage | Require exact event alignment and exclude/reset-label anchor samples explicitly |
| Free-form errors make cause counts unstable | Introduce stable reason codes with compatibility messages |
| Power examples are mistaken for hardware models | Put the reduced-order/non-production label in metadata, README, generated reports, and tests |
| Timing contaminates deterministic qualification | Keep timing in a separate artifact and schema |
| Generated fixtures are refreshed without review | Require explicit fixture-update command and report changed hashes |
| Source/wheel comparison accidentally imports source | Use isolated environments and assert imported module paths |

## 13. Definition of Done

This plan is complete only when:

- all six observatory cases run all seven candidates with complete fixed-step,
  fixed-accuracy, and fixed-work evidence;
- the atlas reports actual authority error, recursive internal bound, anchor
  deviation, phase, energy, empirical coverage, fallback, and rejection causes
  with documented semantics;
- the three reduced-order power-stage examples pass event, continuity,
  residual, energy, authority, determinism, and installed-wheel checks;
- the six teaching exercises run from documented commands and produce
  deterministic verification evidence;
- numerical JSON, CSV, SVG, and lab evidence reproduce byte-for-byte;
- full source, optional-backend, long-horizon, wheel, and source/wheel
  qualification pass for one exact source state;
- documentation retains every claim boundary in this plan; and
- a requirement-to-evidence audit identifies no unimplemented requirement or
  unsupported completion claim.
