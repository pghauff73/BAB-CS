# BAB-CS ngspice and Teaching-Tutorial Expansion Plan

Date: 2026-08-27

## Purpose

This additive plan expands the Bounded-Authority-Based-Circuit-Simulation
(`BAB-CS`) external-comparison and teaching surfaces without replacing the
accepted Method Observatory, Bound Coverage Atlas, Power-Stage Sandbox, or
their historical evidence. BAB-CS is a circuit simulator in which a fast
candidate method may propose a step, but separate checks decide whether that
step becomes authoritative.

The expansion has four linked outcomes:

1. map exactly 20 canonical BAB-CS cases into ngspice;
2. execute exactly ten teaching and reproducibility exercises;
3. publish exactly ten novice-oriented tutorial documents in the generated
   HyperText Markup Language (`HTML`) document tree; and
4. generate accessible Scalable Vector Graphics (`SVG`) diagrams and graphs
   from authoritative repository evidence.

ngspice is an open-source member of the Simulation Program with Integrated
Circuit Emphasis (`SPICE`) family. It is an independent implementation used for
mapped comparison evidence. It is not treated as an oracle, which means BAB-CS
does not assume that every ngspice result is automatically the exact physical
truth.

## Authoritative Owners

| Surface | Authoritative owner | Required count |
| --- | --- | ---: |
| ngspice mapping inventory | `benchmarks/external/manifest.json` | 20 cases |
| Normalized comparison reference | `benchmarks/external/reference-results.json` | 20 reports |
| Executable lab inventory | `lab/support/verify.py` and `lab/[01-10]-*/` | 10 exercises |
| Review-controlled lab evidence | `lab/fixtures/verification-baseline.json` | 10 exercise records |
| Tutorial inventory | `docs/tutorials/*.md` | 10 documents |
| Tutorial and external figure inventory | `tools/docs_tutorial_assets.py` | 13 SVG files |
| Generated HTML tree | `tools/build_docs_html.py` | all current Markdown documents |

A **manifest** is a machine-readable inventory that names the intended cases
and their source files. A **normalized reference** removes incidental temporary
paths while retaining the tool version, case identity, state order, hashes, and
measured differences needed for review.

## Twenty ngspice Cases

### First-Order Linear Cases

1. `rc_step`
2. `rc_discharge`
3. `driven_rc`
4. `current_driven_rc`
5. `rl_step`
6. `rl_decay`

`RC` means a resistor-capacitor circuit. `RL` means a resistor-inductor circuit.
These cases test charging, discharging, source interpretation, and one-state
time constants.

### Resonant and RLC Cases

7. `lc_long`
8. `lc_offset`
9. `rlc_damped`
10. `rlc_overdamped`
11. `rlc_driven`

`LC` means an inductor-capacitor circuit. `RLC` means a circuit containing a
resistor, inductor, and capacitor. These cases separate phase behavior, stored
energy, damping, mixed initial conditions, and driven response.

### Nonlinear Diode Cases

12. `diode_clip`
13. `diode_rectifier`
14. `diode_bias_recovery`

A **nonlinear** device does not respond in direct proportion to its input. The
diode cases test clipping, rectification, and recovery from a changed bias while
preserving the declared BAB-CS diode parameters in the ngspice model.

### Scheduled-Switching Cases

15. `switched_rc`
16. `switched_rl`
17. `switched_rlc`

A **scheduled switch** changes resistance at declared times. These cases test
exact event placement, state continuity, and multistep-history restart around a
known circuit change.

### Reduced-Order Power-Stage Cases

18. `buck_like_reduced_order`
19. `h_bridge_rl_reduced_order`
20. `dc_link_rlc_reduced_order`

A **reduced-order model** deliberately omits device detail that is not needed
for the numerical question. These three cases are numerical experiments, not
production semiconductor, magnetic, thermal, protection, or safety models.

## Ten Teaching Exercises

1. modified nodal analysis and state ownership;
2. convergence by measured refinement;
3. phase error versus energy error;
4. shadow authority;
5. deterministic packaging;
6. source-versus-wheel equivalence;
7. exact event alignment and multistep restart;
8. empirical recursive-bound coverage;
9. fallback and rejection forensics; and
10. semantic mapping of 20 ngspice cases.

**Convergence** means that the computed result approaches a stable value as the
timestep is refined. **Phase error** is timing displacement in an oscillation.
**Energy error** is an incorrect gain or loss of stored circuit energy.
**Fallback** means replacing a rejected candidate step with a permitted
independent method. **Forensics** means retaining enough evidence to explain why
a step was rejected or replaced.

## Ten Tutorial Documents

Each tutorial must include:

- a novice opening that defines the new concept or acronym;
- a command that executes the corresponding evidence path;
- a generated SVG graph or diagram;
- an explanation of what the evidence does and does not establish;
- an engineering application; and
- a claim boundary that prevents educational evidence from becoming an
  unsupported production claim.

The tutorial filenames are numbered `01` through `10` under `docs/tutorials/`.
The generated HTML tree must preserve that ordering and must expose the nested
tutorial directory as a navigable branch.

## SVG Requirements

The 13 expansion figures consist of ten tutorial figures plus an ngspice case
atlas, mapped-feature coverage graph, and maximum-difference overview. Every
figure must:

- contain an SVG title and description for assistive technology;
- be generated from the same authoritative inputs used by the reports;
- avoid text collisions and viewport clipping at its declared view box;
- remain readable in desktop and narrow-screen HTML layouts; and
- appear in at least one generated HTML document.

## Acceptance Gates

The expansion is complete only when all of the following are true:

- [x] the external manifest owns exactly 20 unique case identifiers;
- [x] all 20 cases execute through the live ngspice suite runner;
- [x] the suite produces four artifacts per case plus `suite.json`, for 81
  files in total;
- [x] the lab verifier owns and executes exactly ten exercises;
- [x] the review-controlled fixture contains exactly ten exercise records;
- [x] exactly ten tutorial Markdown documents exist;
- [x] exactly 13 expansion SVG figures are generated;
- [x] the generated HTML metrics report 20 mappings and ten exercises;
- [x] browser-level collision and clipping review passes for every generated
  SVG figure;
- [x] desktop and narrow-screen review passes for the generated HTML tree;
- [x] focused external, lab, documentation, and release-evidence tests pass;
- [x] the complete repository test suite passes; and
- [x] current documentation contains no active four-case or six-exercise claim.

## Completion Evidence

The following validation was completed against the current working tree on
2026-08-27:

- `tools/run_external_suite.py` executed all 20 manifest cases with ngspice 46
  and wrote 81 files: four per case plus `suite.json`;
- `lab/support/verify.py --exercise all --development` executed all ten lab
  exercises and reported `all_passed: true`;
- focused external, lab, documentation, and release-evidence discovery ran 60
  tests with no failure or skip;
- complete standard discovery ran 306 tests in 33.774 seconds and reported
  `OK`; its two default skips were the intentionally scheduled long and
  very-long tiers;
- those scheduled tiers were then enabled explicitly and all seven
  long-horizon tests passed in 42.079 seconds, including the thousand-period
  inductor-capacitor (`LC`) case;
- the generated site contains 38 Markdown documents and 42 SVG assets, of
  which 13 belong to this expansion;
- the transform-aware browser audit found zero text overlaps, zero near-text
  collisions, and zero clipped text elements across all 42 SVG assets;
- desktop and 430-pixel-wide browser checks found ten tutorial navigation
  links, no horizontal overflow, and no broken or undecoded figures; and
- the active-document scan found no live four-mapping or six-exercise claim.

The authoritative external-manifest SHA-256 is
`a7938743be86e0d236fe468136fa76c24045df4e4783bdcd888865e8da679748`.
The normalized ngspice reference SHA-256 is
`b9edb942fe077741525d1d0dfa8e0fbf281b9d24d23622f25cbc401da2a848ff`,
and it records the same manifest hash. The review-controlled ten-exercise lab
fixture SHA-256 is
`f1acbe3ec83c505af0bdd7042eb1657310e88c1581cadd0b1e49d1894c8bc26c`.

This is development evidence for the current source state. It does not make the
dirty working tree release-qualified and does not replace exact-commit human
approval.

## Claim Boundary

Passing this plan proves that the declared numerical experiments, mappings,
teaching exercises, generated documents, and deterministic evidence paths work
for the exact reviewed source. It does not prove transistor-level fidelity,
electromagnetic compatibility, thermal safety, hardware certification, or
universal superiority over ngspice, LTspice, PLECS, Simscape Electrical, Xyce,
or other specialist simulation software.

Release qualification remains a separate exact-commit, exact-artifact, and
human-approval process.
