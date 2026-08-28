# BAB-CS Scaling Improvement Plan

**Prepared:** August 28, 2026  
**Status:** Sparse, fixed-accuracy, operating-profile, runtime bound-coverage, local dual-resolution, global dual-trajectory, refinement-pair, order-aware, signed statewise four-level, native epoch-aligned statewise, and deterministic mode-aligned diagnostic loops implemented; no reference-uncertainty model was promoted, and temporal mode alignment, nonlinear authority, and replay-efficiency work remain open

## Scaling Deficiency

The initial scaling inventory increased repeated circuit channels without adding
stronger interaction between those channels. It measured replication throughput
more directly than general circuit complexity. The original dense BAB-CS backend
also treated increasingly sparse Modified Nodal Analysis (`MNA`) systems as dense
matrices while ngspice used sparse circuit algebra.

Two distinct scaling limitations must remain visible:

1. **Circuit-growth limitation.** The repeated RC and RL banks add identical,
   independent channels. They are useful throughput controls, but they do not add
   new coupled modes, topology changes, event interactions, or nonlinear
   authority stress. The coupled RC ring is more representative, but one linear
   nearest-neighbor family still cannot establish general circuit scaling.
2. **Work-accounting limitation.** The atlas's deterministic work unit counts
   solver events and iterations. It does not weight an event by matrix dimension,
   sparse fill, factorization complexity, or elapsed runtime. RC and RL
   factor-pair work can therefore remain almost unchanged while declared MNA
   unknowns grow substantially. This counter is useful for explaining control
   flow, not for claiming computational scaling.

The benchmark's horizontal axis is a model-declared size coordinate used to keep
the same physical case at one horizontal position. It is not a claim that BAB-CS
and ngspice assemble identical internal equation systems. Both the BAB-CS
declared count and ngspice's reported `Circuit Equations` value remain evidence.

Sparse algebra corrected that implementation bottleneck, but the first
fixed-accuracy run exposed a more important numerical deficiency. The original
active Adams-Bashforth second-order (`AB2`) profile used an implicit reference on
every accepted step and required substantially finer maximum timesteps than
ngspice:

- `rc_bank`: BAB-CS divisor 64 versus ngspice divisor 16;
- `rl_bank`: BAB-CS divisor 32 versus ngspice divisor 16; and
- `coupled_rc_ring`: BAB-CS divisor 32 at size 1 and 128 at sizes 4 and 16,
  versus ngspice divisors 16, 128, and 128.

A divisor of 64 means the baseline maximum timestep was divided by 64. Equal
circuit and stop time therefore did not imply equal numerical work. The initial
profile also retained one reference solve per accepted point, even where an
embedded candidate and recursive bound could safely defer that reference.

## Implemented Correction Loops

### Loop 1: Circuit and Linear-Algebra Scaling

1. Retain repeated resistor-capacitor (`RC`), resistor-inductor (`RL`), diode,
   and switched banks as explicit replication-throughput baselines.
2. Add `coupled_rc_ring`, a grounded nearest-neighbor network in which increasing
   size adds genuine coupled modes.
3. Add explicit `dense`, `scipy`, and `hybrid` installed-wheel backend profiles.
4. Select SciPy sparse algebra at 18 or more declared MNA unknowns in the hybrid
   profile.
5. Record and validate the actual backend used by every row.
6. Reject package-level `auto` selection from benchmark profiles because its
   repeated policy work was slower than an explicit per-case decision.

### Loop 2: Fixed-Accuracy and Authority Qualification

1. Add `fixed_config` and `fixed_accuracy` runtime modes.
2. Sweep BAB-CS and ngspice timesteps independently against one common
   authority and shared evaluation grid.
3. Require analytic authority where available and converged refined authority
   elsewhere.
4. Fail closed when refined authorities do not agree within the declared scaled
   convergence cap.
5. Bound calibration by estimated time points, trace values, and authority trace
   values before launching a child process.
6. Preserve unsuccessful and accuracy-unavailable rows in JSON, CSV, Markdown,
   and Scalable Vector Graphics (`SVG`) output.
7. Correct the switched-bank off resistance from `1e9` to `1e7` ohms so its
   leakage remains above BAB-CS algebraic residual resolution while preserving
   an eight-order on/off resistance ratio.

### Loop 3: Manifest-Owned BAB-CS Operating Profiles

The runtime manifest now owns named BAB-CS profiles instead of relying on a
hard-coded generator configuration:

- `active_heun_deferred4_smooth` uses an active Heun candidate and an implicit
  trapezoidal reference at least every four accepted steps for smooth linear and
  coupled-linear families;
- `active_ab2_deferred4_events` retains AB2 for scheduled switching, where the
  event boundary itself is handled by implicit authority; and
- `active_ab2_reference1_nonlinear` retains a conservative reference-every-step
  policy for diode families until their independent nonlinear authority is
  converged.

Every generated case records its profile identifier and declared overrides. The
installed-wheel worker records the complete effective configuration, and report
validation requires the source case, installed wheel, and manifest profile to
agree exactly.

## Measured Development Evidence

### Sparse-backend gain

At size 64, the earlier one-warm-up, three-repeat development schedule measured
the following BAB-CS dense-to-sparse gains:

| Family | Dense to sparse gain | Dense to hybrid gain |
| --- | ---: | ---: |
| `rc_bank` | 5.71x | 5.64x |
| `coupled_rc_ring` | 4.93x | 4.89x |
| `rl_bank` | 3.59x | 3.61x |
| `diode_rc_bank` | 66.83x | 65.41x |
| `switched_rc_bank` | 10.74x | 10.57x |

### Equal-accuracy operating-profile gain

A bounded quick development schedule used sizes 1, 4, and 16, zero warm-ups,
one timed repeat, one round, the hybrid backend, and a common scaled-error target
of 1. The optimized rows are retained under
`artifacts/runtime/fixed-accuracy-optimized-quick/`. These values are
development evidence, not publication medians. The runtime-gain column comes
from the exploratory before-and-after profile scan; the speedup column comes
from the retained optimized rerun.

| Family | Size | Prior BAB-CS divisor | New divisor | BAB-CS runtime gain | New speedup vs ngspice |
| --- | ---: | ---: | ---: | ---: | ---: |
| `rc_bank` | 1 | 64 | 1 | 5.28x | 0.110x |
| `rc_bank` | 4 | 64 | 1 | 5.13x | 0.079x |
| `rc_bank` | 16 | 64 | 1 | 5.24x | 0.060x |
| `rl_bank` | 1 | 32 | 1 | 2.96x | 0.130x |
| `rl_bank` | 4 | 32 | 1 | 2.94x | 0.104x |
| `rl_bank` | 16 | 32 | 1 | 2.73x | 0.073x |
| `coupled_rc_ring` | 1 | 32 | 1 | 4.20x | 0.170x |
| `coupled_rc_ring` | 4 | 128 | 1 | 9.63x | 0.601x |
| `coupled_rc_ring` | 16 | 128 | 1 | 9.32x | 0.409x |

All nine optimized smooth-family rows met the target for both tools, proved
source-versus-wheel equivalence, and proved that the installed-wheel effective
configuration matched the manifest. The new BAB-CS scaled errors ranged from
approximately 0.024 to 0.406.

At size 16, the retained optimized peak BAB-CS resident-memory samples were:

- `rc_bank`: 68,976 kibibytes;
- `rl_bank`: 68,896 kibibytes; and
- `coupled_rc_ring`: 75,520 kibibytes.

Earlier exploratory samples were larger, especially for the coupled family,
but a publication claim about memory reduction requires repeated paired runs.

The switched profile selected BAB-CS divisor 16 with scaled error 0.995, compared
with divisor 32 under the prior profile. The row remains `accuracy_unavailable`
because ngspice did not reach the target before the bounded calibration limit;
the next attempt would have required an estimated 983,041 output points and
1,966,082 trace values.

The diode row remains `accuracy_unavailable`. Its refined trapezoidal authorities
at factors 512 and 1024 differ by scaled error 6.155, above the convergence cap
of 0.25. No equal-accuracy runtime claim is permitted for that family.

### Runtime-profile bound-coverage evidence

The runtime-profile extension of the BAB-CS Bound Coverage Atlas replays the
manifest-owned profiles at their selected development divisors. Analytic
authorities are exact. Refined authorities are qualified on the same independent
201-point grid used by the fixed-accuracy runtime benchmark before they are
sampled at BAB-CS output times. The retained report is under
`artifacts/atlas/runtime-scaling-optimized/`.

| Family | Qualified cases | Eligible samples | Empirical coverage |
| --- | ---: | ---: | ---: |
| Resistor-capacitor (`RC`) bank | 3 | 1,840 | 93.4% |
| Resistor-inductor (`RL`) bank | 3 | 1,749 | 95.5% |
| Coupled RC ring | 3 | 3,530 | 85.6% |
| Switched RC bank | 1 | 1,030 | 52.9% |
| Diode RC bank | 0 | 0 | unavailable: authority disagreement 6.155 > 0.25 |

Across the qualified rows, embedded-fast steps covered 90.3% of eligible
external-authority drift samples, partial-reference steps covered 71.7%, and all
13 eligible full-reference transfers were uncovered. The recurrence itself
reconciles exactly, but it is explicitly internal and reference-relative. A
reference solve can reduce the internal bound nearly to the residual floor while
the reference method still has nonzero discretization error against analytic or
independently refined trajectory authority.

The component decomposition also changes the interpretation of the near-cap
values:

- maximum propagated prior bound: 91.72;
- maximum embedded defect: 17.14;
- maximum corrected/reference defect: 0.253; and
- maximum normalized residual defect: `8.88e-8`.

Residuals are not driving the cap. Embedded Heun-versus-Euler deviation and
propagated prior uncertainty dominate the internal recurrence, while missing
reference-discretization uncertainty dominates the uncovered external samples.
The bound cap must therefore not be loosened or tightened merely because the
global runtime error is below 1.

## Runtime-Coverage Correction and Next Loops

### Loop 4: Runtime-Profile Bound Coverage — Implemented

- Add manifest-owned runtime profile and divisor selection to the Bound Coverage
  Atlas.
- Qualify refined authorities on the benchmark's independent common grid.
- Preserve unqualified cases without samples or coverage claims.
- Export propagated prior bound, local defect, embedded defect,
  corrected/reference defect, residual defect, uncovered authority gap, and
  coverage by authority-transfer type.
- Generate a dedicated coverage-by-authority-transfer Scalable Vector Graphics
  (`SVG`) chart.

### Loop 5A: Local Dual-Resolution Diagnostic — Implemented, Not Promoted

The default-off `dual_resolution` diagnostic compares one full trapezoidal
reference step with two half steps, accepts the refined endpoint, records the
local discrepancy separately, and carries it across embedded, partial-reference,
full-reference, event, and periodic-reanchor paths. Direct tests prove that late
dynamic checkpoints cannot omit the discrepancy and that independent reanchors
reset the internal recurrence without silently deleting the external term.

Same-source, size-one paired evidence is retained under
`artifacts/atlas/runtime-dual-reference/`:

| Family | Baseline coverage | Experimental total coverage | Gain | Work multiplier | Maximum reference uncertainty |
| --- | ---: | ---: | ---: | ---: | ---: |
| RC bank | 94.09% | 94.24% | +0.15 percentage points | 1.092x | 2.74 |
| RL bank | 96.03% | 96.03% | 0.00 percentage points | 1.081x | 0.00 |
| Coupled RC ring | 73.67% | 81.14% | +7.47 percentage points | 1.092x | 512,661.54 |

The local model fails promotion. RC gains negligible coverage, RL produces no
accepted-step signal, and coupled coverage improves only after scalar
amplification makes the uncertainty non-informative. Each case triples reference
solve count and adds approximately 8% to 10% deterministic work. The headline
runtime profiles and `deferred_reference_bound_cap` therefore remain unchanged.

### Loop 5B: Global Dual-Trajectory Qualification — Implemented, Not Promoted

The offline global diagnostic advances independent factor-2 and factor-4
trapezoidal trajectories across the complete BAB-CS output-time sequence. It
reports raw coarse-versus-refined drift, refined-versus-qualified-authority
error, BAB-CS total coverage, and an explicit safety-factor curve. No tuned
factor is hidden inside a headline result.

| Family | Internal coverage | Raw global total coverage | Raw estimator coverage | Maximum added uncertainty | Median uncertainty/error ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| RC bank | 94.09% | 100.00% | 95.24% | 5,729.13 | 582.29x |
| RL bank | 96.03% | 100.00% | 94.83% | 2,984.42 | 399.30x |
| Coupled RC ring | 73.67% | 93.77% | 93.00% | 14,948.72 | 747.09x |

Global drift is more stable than recursive local amplification and materially
improves coupled coverage, but it also overwhelms the actual authority error by
hundreds of times at the median sample. Larger safety factors approach complete
empirical coverage only by increasing that vacuity. The factor-2/factor-4 model
is therefore retained as an offline diagnostic and not promoted.

### Loop 5C: Refinement-Pair Coverage–Vacuity Pareto Sweep — Implemented, Not Promoted

The retained sweep under
`artifacts/atlas/runtime-global-refinement-pair-sweep/` evaluates factor pairs
2/4, 4/8, 8/16, and 16/32 with safety factors 1, 2, 4, 8, and 16 for RC, RL, and
coupled RC cases at sizes 1, 4, and 16. Every refinement trajectory is cached by
factor, every pair reports independent work, and the atlas publishes both
per-case and common-policy Pareto frontiers.

| Common raw policy | Minimum total coverage | Minimum estimator coverage | Worst median inflation | Worst p95 inflation | Maximum pair work |
| --- | ---: | ---: | ---: | ---: | ---: |
| factor 2/4, safety 1 | 93.77% | 93.00% | 1,033.12x | 207,561.56x | 9,310 |
| factor 4/8, safety 1 | 90.14% | 93.13% | 362.35x | 97,710.36x | 18,060 |
| factor 8/16, safety 1 | 85.86% | 92.74% | 100.65x | 31,602.85x | 35,252 |
| factor 16/32, safety 1 | 83.40% | 84.48% | 31.15x | 6,378.69x | 67,584 |

Finer pairs reduce vacuity but also lose coverage and consume more reference
work. Coarser pairs recover coverage only by adding uncertainty hundreds or
thousands of times larger than actual authority drift. No common pair and safety
factor is both informative and reliably covering, so the model is not promoted.

The sweep also exposes the work-accounting boundary. For repeated RC, factor-2/4
work is 4,982 units at sizes 1 and 4 and remains 4,982 at size 16, even though
declared MNA unknowns grow from 5 to 50. For repeated RL, the same work remains
4,396 units while declared MNA unknowns grow from 4 to 34. Those values count
solver events, not the cost of operating on the larger systems.

### Loop 5D: Order-Aware Reference Qualification — Implemented, Not Promoted

The retained study under `artifacts/atlas/runtime-global-order-aware/` derives
equal-ratio triplets 2/4/8, 4/8/16, and 8/16/32 from the cached factor
trajectories. It estimates observed order, permits Richardson extrapolation only
between declared orders 1 and 3, rejects discrepancies at or below `1e-12`, and
counts every rejected sample or epoch as uncovered in effective coverage.

Pointwise qualification reduces median uncertainty inflation from hundreds of
times to approximately 1.7x to 2.3x, but only 44.86% to 51.88% of the worst-case
samples qualify. Anchor-epoch root-mean-square qualification is more stable:

| Common epoch policy | Minimum qualified-sample fraction | Minimum effective reference coverage | Minimum effective total coverage | Worst median inflation | Worst p95 inflation |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2/4/8 | 69.08% | 45.91% | 67.32% | 1.71x | 17.79x |
| 4/8/16 | 82.62% | 53.57% | 73.54% | 1.56x | 19.19x |
| 8/16/32 | 82.62% | 39.48% | 74.45% | 1.36x | 16.57x |

An epoch envelope applies the largest fine discrepancy in each qualified anchor
window. It raises qualified reference coverage substantially, but median
inflation rises to roughly 3x to 10x and 95th-percentile inflation reaches about
164x. Rejected epochs still remain uncovered. Neither the pointwise estimate,
the epoch estimate, nor the epoch envelope is promoted.

### Loop 5E: Signed Statewise Four-Level Extrapolation — Implemented, Not Promoted

The scalar weighted-root-mean-square discrepancy loses sign and state identity,
so one state can change the apparent order or hide cancellation in another. The
retained study under
`artifacts/atlas/runtime-global-statewise-four-level/` now:

- retain signed per-state differences for four successive refinement levels;
- fit each state's leading error coefficient and observed order separately;
- require sign, order, and coefficient stability before extrapolation;
- compare adjacent extrapolated trajectories as an independent residual check;
- identify interpolation, anchor-reset, and algebraic-solve floors explicitly;
  and
- report fail-closed state and epoch rejection causes without adding a tuned
  family-specific multiplier.

The two common four-level policies produced the following worst-case results
across the nine RC, RL, and coupled-RC scaling cases:

| Common four-level policy | Minimum sample qualification | Minimum state qualification | Minimum effective reference coverage | Minimum effective total coverage | Worst median inflation | Worst p95 inflation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2/4/8/16 | 0.00% | 3.28% | 0.00% | 0.00% | 3.63x | 33.28x |
| 4/8/16/32 | 0.22% | 1.70% | 0.22% | 0.22% | 3.94x | 97.39x |

Only 292 of 14,238 eligible sample-policy evaluations qualified. At state level,
4,233 of 107,640 evaluations qualified. Requiring every state to qualify makes
the system-level qualification rate collapse as coupled state count increases:
the size-16 coupled RC ring qualified zero samples under 2/4/8/16 and three
samples under 4/8/16/32.

The dominant state rejection was signed-difference inconsistency, with 74,173
occurrences. Observed orders outside the declared interval and adjacent-order
instability accounted for most remaining failures. Only 287 state rejections
were direct difference-floor events. All 287 occurred at interpolated refined
samples, 33 also occurred immediately after an anchor reset, and none carried an
algebraic-solve-floor context. However, all 18 all-native policy evaluations also
failed an order or sign gate, so interpolation is a contributor rather than the
sole cause.

The study is not promoted. It is informative because it demonstrates that a
pointwise, every-state asymptotic requirement does not scale with system state
count, even though the uncertainty inflation of the rare qualified samples is
far lower than the original raw refinement-pair estimate.

### Loop 5F: Epoch-Aligned Statewise Coefficient Stability — Implemented, Not Promoted

The retained study under
`artifacts/atlas/runtime-global-statewise-epoch/` preserves statewise signed
information over complete BAB-CS anchor epochs. Each refined trapezoidal
trajectory lands natively at the BAB-CS diagnostic times, uses its declared
refinement factor as the number of local substeps inside every diagnostic
interval, and suppresses redundant periodic replay while retaining forced event
re-anchors. This corrected two implementation defects found during evidence
generation: a runtime minimum-step threshold was inappropriate for
floating-point diagnostic boundary slivers, and merely clipping every factor to
the same dense output schedule erased the intended refinement distinction.

The epoch estimator classifies synchronized sign changes as coherent physical
zero crossings, rejects unmatched sign changes, fits signed order and leading
coefficient vectors, and reports per-state and joint-system qualification. All
samples are native for every refinement factor; no interpolation is used.

| Common four-level policy | Qualified epochs | Qualified state epochs | Qualified samples | Minimum joint qualification | Minimum effective reference coverage | Maximum useful-case median inflation | Maximum useful-case p95 inflation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2/4/8/16 | 13/483 | 85/3,630 | 193/7,119 | 0.00% | 0.00% | 1.00x | 16,532.33x |
| 4/8/16/32 | 49/483 | 412/3,630 | 725/7,119 | 0.00% | 0.00% | 1.00x | 2.60x |

The finer policy qualifies 12 of 40 RL epochs and 3 of 42 RC epochs for every
tested replicated size. Its Richardson estimate is consistently just below the
independent refined-authority error for those families, with median ratios from
approximately 0.99991 to 0.99998, so empirical reference coverage remains zero
without an undeclared safety multiplier. The size-one coupled RC ring qualifies
4 of 52 epochs, with 1.69% effective reference coverage and 6.36% effective total
coverage. Coupled sizes 4 and 16 qualify no complete epoch even though 63 of 368
and 30 of 1,488 individual state epochs respectively pass the finer policy.

No coherent zero crossing was found in these monotone and damped cases. The two
policies recorded 444 and 544 unmatched sign-change intervals. Direction-cosine
failure dominates the finer-policy rejections, followed by unmatched sign
changes and observed order below one. Direct native refinement increases
independent four-level work by approximately 2.87x to 4.82x versus the retained
interpolated Loop 5E study, while eliminating all periodic authority replay.

The study is not promoted. It proves that interpolation was not the root cause:
the remaining limitation is a physically coupled joint-state asymptotic regime,
not merely sample alignment. The common fail-closed frontier is empty because
both policies leave at least one case without a qualified system epoch.

### Loop 5G: Mode-Aligned Epoch Qualification — Implemented, Not Promoted

The retained study under `artifacts/atlas/runtime-global-modal-epoch/` tests
whether Loop 5F's coupled-state sign instability is caused by the physical state
coordinates. Eligible circuits must have homogeneous dynamic units, no nonlinear
devices, no switches, and a symmetric differential Jacobian. A deterministic,
dependency-free Jacobi eigendecomposition must pass declared symmetry,
eigen-residual, orthogonality, and iteration limits. Repeated eigenvalues remain
one modal subspace so arbitrary eigenvector rotations cannot change
qualification.

All nine RC, RL, and coupled-RC cases pass the basis gates. Every retained
Jacobian is exactly symmetric in its recorded floating-point representation, the
maximum eigen residual is `7.46e-12`, and the maximum orthogonality error is
`8.88e-16`. Mixed RLC units,
diodes, and topology-changing switches fail closed before decomposition.

| Common four-level policy | Qualified joint epochs | Qualified modal-group epochs | Qualified samples | Minimum joint qualification | Minimum effective reference coverage | Maximum reported median inflation | Maximum reported p95 inflation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2/4/8/16 | 13/483 | 13/2,154 | 193/7,119 | 0.00% | 0.00% | 1.00x | 16,532.33x |
| 4/8/16/32 | 50/483 | 209/2,154 | 740/7,119 | 0.00% | 0.00% | 1.00x | 9.41x |

Repeated RC and RL banks retain exactly the statewise Loop 5F results, as an
orthogonal transform should. The finer modal policy raises the size-four coupled
RC ring from zero to one qualified joint epoch, covering 15 of 1,368 samples. It
reconstructs 0.51% effective reference coverage and 0.88% effective total
coverage with median inflation 0.71x and 95th-percentile inflation 9.41x. At size
16, modal-group qualification rises from 30 to 96 of 1,488 group epochs, but no
complete system epoch qualifies.

The finer policy records 65 coherent zero-crossing intervals and 2,165 unmatched
sign-change intervals. Direction-cosine failure remains dominant, followed by
unmatched crossings. The common fail-closed frontier is empty. Modal coordinates
therefore explain a small portion of the size-four failure but do not establish a
scalable reference-error enclosure. The study is not promoted, and statewise
Loop 5F remains the fallback for every ineligible or rejected modal basis.

### Loop 5H: Temporally Aligned Modal Epoch Qualification — Implemented, Not Promoted

The retained study under
`artifacts/atlas/runtime-global-temporal-modal-epoch/` tests whether remaining
modal direction failures are one diagnostic sample out of phase. Only scalar
modal groups may shift. Three signed refinement-difference sequences must
provide one unique, monotone, one-to-one zero-crossing match within the common
maximum lag of one sample. Direction cosines use only the published common
retained interval. Observed order, coefficient agreement, extrapolant residual,
error estimation, and conservative state reconstruction remain unshifted.

| Common four-level policy | Qualified joint epochs | Qualified modal-group epochs | Qualified samples | Alignment attempts | Unique crossing matches | Alignments applied | Discarded endpoints |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2/4/8/16 | 13/483 | 13/2,154 | 193/7,119 | 1,861 | 1 | 0 | 3 |
| 4/8/16/32 | 50/483 | 209/2,154 | 740/7,119 | 1,844 | 3 | 0 | 6 |

Every qualification and coverage value is identical to Loop 5G. For the finer
policy, 1,400 attempted groups have no crossing evidence, 304 are rejected for
sign chatter, 128 repeated modal subspaces retain the unshifted fallback, 9 have
no one-to-one crossing match, and the 3 uniquely matched scalar groups still
fail the aligned left-direction cosine gate. The coarse policy shows the same
pattern: 1,379 missing-crossing rejections, 355 chatter rejections, 110
non-scalar fallbacks, 16 failed matches, and one uniquely matched group that
still fails direction.

The common fail-closed frontier remains empty. The evidence rejects the
one-sample timing-shift hypothesis: dominant direction failures are
pre-asymptotic changes in the refinement error field, not merely displaced zero
crossings. Loop 5G remains the authoritative fallback and Loop 5H is not
promoted.

### Loop 5I: Five-Level Two-Term Modal Extrapolation — Implemented, Not Promoted

The retained study under `artifacts/atlas/runtime-global-two-term-modal/` tests
whether two competing truncation terms explain the refinement-direction
reversals that one-term Richardson fitting rejects. Qualified Loop 5G modal
groups retain their existing estimate. Every rejected group fits
`Y_f = Y_inf + C f^-2 + D f^-q` with factors 2, 4, 8, and 16. Factor 32 is
excluded from fitting and used only as a holdout gate and residual envelope.
Secondary orders 3 and 4 are common policies across every family and size.

The deterministic design condition numbers are 230.85 for `q=3` and 269.69 for
`q=4`, both below the common limit of 1,000. The residual estimate adds the
absolute primary contribution, absolute secondary contribution, and a residual
envelope amplified by the exact intercept leverage.

| Common policy | Qualified joint epochs | Qualified modal-group epochs | Qualified samples | Loop 5G fallback groups | Fits attempted | Two-term fits qualified | Maximum training residual ratio | Maximum holdout residual ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `p=2, q=3` | 50/483 | 209/2,154 | 740/7,119 | 209 | 1,945 | 0 | 4.93 | 1,573.78 |
| `p=2, q=4` | 50/483 | 209/2,154 | 740/7,119 | 209 | 1,945 | 0 | 4.76 | 2,025.41 |

For `q=3`, 1,656 attempted groups fail the training-residual gate, 242 fail the
factor-32 holdout gate, 43 have a modeled holdout signal at or below the declared
floor, and 4 epochs contain too few samples. For `q=4`, the corresponding counts
are 1,656, 232, 53, and 4. No rejected Loop 5G group is recovered, so every
qualification, coverage, and inflation result remains identical to Loop 5G.
The common fail-closed frontier remains empty and Loop 5I is not promoted.

### Loop 5J: Finer-Level Asymptotic-Entry Ladder — Next Highest Gain

The next diagnostic shall test whether factor 32 is still pre-asymptotic rather
than adding another fitted term or relaxing a residual gate:

- extend the common native refinement ladder with factors 64 and 128;
- evaluate one-term modal policies 8/16/32/64 and 16/32/64/128;
- evaluate the two-term `q=3` and `q=4` policies using 8, 16, 32, and 64 for
  fitting and factor 128 as the independent holdout;
- publish direct integration work, numerical-floor hits, direction, observed
  order, training residual, holdout residual, coverage, and inflation by size;
- use one ladder and one gate set across all families without tuning a safety
  multiplier; and
- stop the refinement ladder if the finer differences reach the declared
  numerical floor or the independent holdout becomes less predictive.

### Loop 6: Replay-Efficiency Scaling

Even after reducing reference solves by about 75%, periodic replay remains close
to two replay substeps per accepted point on smooth cases. Next work shall:

- measure replay integration, projection, factorization, and retained-state cost
  separately;
- reuse validated anchor-window work where the topology and source segment are
  unchanged;
- evaluate streaming or checkpointed replay so memory does not scale with every
  retained Python simulation object; and
- preserve deterministic reconstruction and exact source-versus-wheel evidence.

### Loop 7: Nonlinear Authority

- Replace the unconverged diode authority with a higher-quality independent
  nonlinear authority.
- Evaluate streaming refinement, higher-order implicit reference, and
  cross-refinement interval agreement without storing unsafe full traces.
- Keep every diode runtime row unavailable until authority convergence is proven.

### Loop 8: Authority-Stress Scaling

- Add coupled nonlinear, switching, and oscillatory families whose increasing
  size can trigger bound failures, rejection, fallback, and replay work.
- Report actual authority error, recursive bound, anchor deviation, phase,
  energy, rejection cause, and fallback cause by size.
- Separate linear-solve scaling from bounded-authority scaling.

## Completion Gates

The scaling deficiency is not closed until:

- independent-channel and genuinely coupled families are both present;
- dense, sparse, hybrid, and BAB-CS operating profiles are named and
  reproducible;
- every row records its actual backend and effective operating profile;
- equal-accuracy rows satisfy the declared target for both tools;
- nonlinear authority is independently converged;
- internal bound coverage and slack are reported by size;
- internal recurrence and external reference-discretization uncertainty are
  reported separately;
- reference transfers do not silently reset external-authority uncertainty to
  the residual floor;
- replay work and memory scaling are bounded and explained;
- authority-stress rows produce and explain nontrivial rejection or fallback
  behavior where expected; and
- the final chart places speedup and accuracy side by side with failed rows and
  unfavorable results preserved.
