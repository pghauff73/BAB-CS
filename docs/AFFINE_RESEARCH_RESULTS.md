# Results: all four affine research directions

5 September 2026. All four directions now have executable research implementations.
The strongest positive finding is long-horizon tightening from a verified weighted
norm. The adaptive mixed policy does not show a clear work advantage, and the
switched-RC event audit correctly retains unresolved crossing evidence.

See the [implementation and assumptions](AFFINE_RESEARCH_IMPLEMENTATION.md),
[updated literature review](../exa-results/babcs-literature-review-updated-2026-09-05/REVIEW.md),
and [evidence manifest](../artifacts/affine-research-2026-09-05/manifest.json).

## 1. Production replay audit

Both actual BAB-CS traces pass every independent nominal closed-form endpoint
cross-check. Instrumented and uninstrumented runs have identical numerical trace
digests. Bounds include propagated anchor uncertainty and fresh replay defects.

| Input | Accepted steps | Selected replay windows | Maximum endpoint radius (V) | Maximum reconstruction tube radius (V) | Maximum nominal error upper bound (V) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `examples/rc_step.json` | 500 | 31 | 0.0000985165 | 0.000183050 | 0.0000491762 |
| `switched_rc_bank-n001.json` | 468 | 32 | 0.00622897 | 0.0107397 | 0.00311449 |

These maxima can occur at different times. Tube bounds concern the explicitly
constructed piecewise Hermite reconstruction, not an unspecified production dense
output. The switched example comes from the existing runtime stress case family;
this is a new audit of its current source/input snapshot, not a reclassification
of historical authority-stress results. The larger switched bound is retained.

The result advances the earlier standalone pilot to real accepted states and
real replay substeps. It still leaves production acceptance decisions unchanged.
The tests additionally exercise both inputs with nonzero initial uncertainty and
check that selected replay paths retain a positive inherited contribution.

Evidence: [production-replay.json](../artifacts/affine-research-2026-09-05/production-replay.json).

## 2. Weighted norm comparison

The same damped-RLC trapezoidal state trace, step 0.05 and initial Euclidean radius
0.001, is certified with both norms. Reported radii include conversion back to a
physical Euclidean/coordinate bound.

| Horizon | Euclidean endpoint radius | Verified P-norm converted radius | Euclidean / converted radius |
| ---: | ---: | ---: | ---: |
| 2 | 0.00196231 | 0.00248357 | 0.79 |
| 10 | 0.00203826 | 0.000368611 | 5.53 |
| 20 | 0.00203849 | 0.0000302961 | 67.29 |

The weighted norm is worse at horizon 2. At horizons 10 and 20 its proved
contraction outweighs conversion cost. This supports investigating verified
metrics for long stable replay horizons; it does not imply improved numerical
states, since both columns use exactly the same trace.

Evidence: [weighted-norms.json](../artifacts/affine-research-2026-09-05/weighted-norms.json).

## 3. Adaptive verification effort

All **36/36** requested configurations complete with certified full reconstruction
radii below their declared tolerances, 0.001 or 0.0001, over horizon 2. Cases are RC
decay, RL step, damped RLC, neutral LC and RC with a scheduled source change. RLC
is tested in both Euclidean and verified weighted norms.

Representative operation counts for tolerance 0.001:

| Case / policy | Attempted Heun steps | Attempted implicit solves | Certificate evaluations |
| --- | ---: | ---: | ---: |
| RC / Heun | 54 | 0 | 54 |
| RC / reference | 0 | 35 | 35 |
| RC / mixed | 18 | 33 | 51 |
| Damped RLC, Euclidean / Heun | 82 | 0 | 82 |
| Damped RLC, Euclidean / reference | 0 | 55 | 55 |
| Damped RLC, Euclidean / mixed | 29 | 56 | 85 |
| Neutral LC / reference | 0 | 42 | 42 |
| Neutral LC / mixed | 21 | 41 | 62 |

Counts include failed attempts. Mixed fallback sometimes saves one or two implicit
solves while adding explicit work and many certificate evaluations; in other
cases it uses more solves too. There is no demonstrated general work or wall-time
advantage. These policies satisfy a common tolerance, but their achieved errors
are unequal, so a future cost-to-achieved-accuracy curve would give a stronger
comparison.

This is an adaptive reference-fallback experiment. An adaptive checkpoint-replay
controller remains a subsequent production integration task. Before that step,
the evidence favors improving allocation efficiency and testing a measured cost
model rather than claiming faster certification.

Evidence: [adaptive-effort.json](../artifacts/affine-research-2026-09-05/adaptive-effort.json).

## 4. Event completeness and uncertain times

The manufactured affine parabola has two roots at 0.25 and 0.75 despite positive
values at both interval endpoints. The classifier encloses both and proves their
opposite crossing directions. Grazing is UNKNOWN; the strictly positive example
is NO_CROSSING. Threshold uncertainty produces a crossing-time enclosure covering
the full prescribed threshold range. Resource exhaustion produces UNKNOWN.
Delay/jitter interval addition is implemented, and overlapping transitions retain
unresolved order.

On actual accepted output reconstructions at threshold 0.5 V:

| Case | Result | Candidate time enclosure (seconds) |
| --- | --- | --- |
| RC | One proved rising crossing | [0.00069314453125, 0.000693154296875] |
| Switched RC | UNKNOWN across adjacent segments | [0.00119169471264, 0.00119366166592] |

Displayed endpoints are rounded for reading; exact rational endpoints are in the
JSON. The switched interval is the union of two touching candidate windows, not
a proof of two events. A cross-segment existence/uniqueness argument could resolve
this example; the current implementation deliberately preserves its uncertainty.
Event-time envelopes do not yet propagate uncertainty through post-event modes
or reset maps.

Evidence: [events.json](../artifacts/affine-research-2026-09-05/events.json) and the
threshold-event sections of production-replay.json.

## Validation and research interpretation

**31 tests pass**: 17 new tests plus the frozen pilot's 14 tests. They exercise
outward square roots, exact metric inequalities, false-contraction rejection,
nonzero inherited uncertainty, same-sign paired crossings, grazing, threshold
uncertainty, exhaustion, timing/order, rejected adaptive trials, scheduled event
alignment, wrapper restoration, and both actual production replay audits.
A second complete research run produces byte-identical JSON reports and manifest.

The novelty candidate remains the combination of an explicit inherited-error
ledger with real replay paths, verified metric conversion, honest work accounting,
and unresolved event evidence. Individual ingredients have established literature:
[Hermite defect control](https://doi.org/10.1137/0912053),
[logarithmic norms](https://www.kybernetika.cz/content/2012/5/865), and
[event-time error estimation](https://arxiv.org/abs/2001.11139).
These experiments establish feasibility in restricted affine models, not
publication-level novelty or general hybrid certification.

The next substantive research steps are cross-segment event proofs and
post-transition uncertainty propagation, sharper adaptive allocation with measured
costs, and integration of this ledger into a production acceptance policy.
The existing extreme-scale interval-underflow finding remains unrepaired and is
not exercised by the separate rational certificate path used here.
