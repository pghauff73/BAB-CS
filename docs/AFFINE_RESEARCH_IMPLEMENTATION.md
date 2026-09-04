# Four affine research directions: implementation

Implemented 5 September 2026. These are executable research tools and an offline
production-trace auditor. They do not change the production controller's acceptance
logic or establish a certificate for arbitrary circuits, nonlinear devices, MNA
algebraic variables, uncertain components, or hardware.

The [updated literature review](../exa-results/babcs-literature-review-updated-2026-09-05/REVIEW.md)
provides the research context. The [earlier theorem](REPLAY_ERROR_BUDGET_THEOREM.md)
and its frozen pilot remain intact. [Results](AFFINE_RESEARCH_RESULTS.md) describe
both improvements and negative findings.

## 1. Actual production replay traces

`tools/audit_affine_replay.py` runs the real `Simulator(BoundedIntegrator(...))`
with the checked-in RC and switched-RC inputs. Temporary wrappers collect the
actual implicit replay substeps, including their original anchor and returned
endpoint. A second uninstrumented run must produce an identical digest of state,
time, step metrics, event sources, and rejection reasons. Wrappers restore their
original functions on exit, including exceptions. This instrumentation is intended
for a serial, isolated process.

The topology extractor accepts only a grounded capacitor driven by a constant
voltage source through one resistor and optionally one series pulse-controlled
resistive switch. It checks device counts and connections. Component values are
interpreted as the exact real values of their binary floating-point inputs. The
ideal pulse schedule uses rational arithmetic on those values. This makes the
mathematical model explicit, including tiny differences from floating-point event
time calculations in the solver.

For each accepted output interval, the auditor constructs a cubic Hermite curve
from the actual endpoint states and exact affine vector field. It splits at ideal
scheduled switching times; inserted states are linearly interpolated before each
piece's Hermite construction. This is a declared reconstruction of the output,
not a claim about production dense-output semantics. Zero-time changes add their
state displacement to the uncertainty radius.

For a segment of length h with reconstruction defect bounded by d, the ledger is

```
B_end <= exp(mu h) B_start + phi(mu,h) d
phi(mu,h) = integral from 0 to h of exp(mu s) ds.
```

Exact rational polynomial coefficients, Bernstein convex-hull bounds and the
frozen pilot's outward rational exponential bounds evaluate these quantities.
The exponential routine's domain is enforced by subdividing audit spans.
Actual floating-point state/solve errors appear in the reconstruction defect;
they do not require treating the numerical solver as exact.

A selected replay starts with the previously established uncertainty at its
original anchor. Its inherited contribution and fresh defect contribution are
reported separately. At the common endpoint, the smaller of the direct and
replay radii is valid. Earlier output intervals keep their original full-path
bounds: replay does not retroactively certify a narrower provisional path.
Every selected replay must have a captured endpoint and a known anchor.

An independent piecewise closed-form scalar exponential enclosure cross-checks
every nominal accepted state. Passing this diagnostic supports the implementation;
the defect theorem supplies the trajectory argument. A failed cross-check alone
would require diagnosis because an overly wide independent enclosure could also
prevent the sufficient comparison from passing. Production `estimated_bound`
values are retained as scaled diagnostics, not equated with physical volts.

## 2. Verified weighted norms

`tools/affine_research.py` supports the infinity norm and quadratic norms
`||v||_P = sqrt(v^T P v)` in dimensions one and two. It verifies, in exact rational
arithmetic,

```
alpha I <= P <= beta I,
A^T P + P A <= 2 mu P,
alpha > 0.
```

Positive semidefiniteness is checked with the diagonal entries and determinant.
The segment certifier revalidates the metric against its actual A. Square roots
are rounded upward on a rational grid. Coordinate errors are at most
`B_P / sqrt(alpha)`; an initial Euclidean ball of radius epsilon is embedded using
`sqrt(beta) epsilon`. Thus the reported comparison includes norm conversion.

For normalized damped RLC, the experiment uses

```
A = [[0, 1], [-1, -2]]
P = [[3/2, 1/2], [1/2, 1/2]]
alpha = 1/4, beta = 2, mu = -1/4.
```

Here `A^T P + P A = -I`. The same rational trapezoidal state trace is certified
under P and Euclidean norms. Horizons 2, 10 and 20 expose the short-horizon
conversion cost and long-horizon contraction benefit. The tests reject a false
strict contraction claim for undamped LC.

## 3. Adaptive verification effort

The adaptive harness compares Heun, trapezoidal reference, and Heun with a
trapezoidal fallback across five normalized affine systems, two tolerances, and
six system/metric combinations: 36 configurations. Initial uncertainty is zero.
Each accepted *whole Hermite segment* must fit the physical tolerance. A simple
nonexpansive allocation also requires its fresh contribution to be no greater
than `(metric tolerance) h / T`. Rejected trials cannot advance accepted state.
Trials halve the step on failure and may grow it when their allocation is
underused. Steps stop exactly at prescribed source discontinuities.

The mixed fallback uses two implicit substeps and retains the midpoint as an
accepted output. Consequently its certificate covers the actual selected
reconstruction. Attempt budgets or minimum-step exhaustion return UNKNOWN.
All attempted candidate steps, reference solves, certificate evaluations, and
rejected trials are counted, including discarded partial fallbacks. The reported
RHS counter counts the two explicit Heun vector-field evaluations; implicit
steps are represented by linear solves, with their defect verification counted
separately. These are operation categories, not a hardware cost model.

This experiment is adaptive reference fallback, not an implementation of an
adaptive checkpoint-replay controller. Its role is to establish the accuracy/work
comparison before integrating such a controller. There is no wall-time speedup
claim, and fewer implicit solves alone are insufficient evidence of an advantage.

## 4. Crossing completeness and timing uncertainty

The event classifier recursively subdivides the reconstruction's Bernstein
controls, enlarged by the state-error tube. A cell is discarded only when the
guard enclosure excludes zero. Every remaining possible root cell is retained,
including cells left when the resource budget is exhausted.

A grouped window earns CROSSING only when endpoint enclosures have opposite
strict signs and the exact vector field's guard derivative has one strict sign
throughout the window. This proves exactly one crossing per admissible trajectory
and fixed threshold in the declared interval. Grazing, unresolved existence,
segment-boundary uncertainty, and exhaustion retain UNKNOWN. Requested tolerance
controls subdivision cell width; merged windows may be wider because state or
threshold uncertainty cannot be removed by time subdivision.

Manufactured examples include two crossings hidden between positive endpoints,
grazing, no crossing, uncertain initial state, and uncertain threshold. The
production RC traces are also scanned at 0.5 V. Across accepted segments, candidate
windows are retained individually: touching windows may refer to the same event
and are not counted as separate physical crossings.

Delay and jitter intervals are added to crossing windows by interval addition.
Overlapping transition windows report unresolved ordering. These time enclosures
do not certify post-transition trajectories, reset maps, uncertain switching
branches, or saltation effects. Those require further hybrid-flow analysis.

## Reproduction and validation

From the repository root:

```sh
PYTHONPATH=src python -m unittest tests.test_affine_research tests.test_replay_error_budget
python tools/run_affine_research.py --output-directory /tmp/babcs-affine-research-new
```

The output directory must not already exist. Reports retain rational certificate
quantities, accepted states, replay inventories, operation counts, and source/report
SHA-256 hashes. The current evidence is in
`artifacts/affine-research-2026-09-05/`. No historical benchmark has been overwritten.

The known extreme-scale interval-underflow issue documented in the literature
review remains outside this work. These tools use a separate rational certificate
path and do not establish that production interval reachability is sound.

### Commit provenance

The published experiment reports preserve the development-workspace source hashes
from their original run. That workspace included solver changes outside this
research commit; the reports are historical evidence, not an assertion that a
clean checkout reproduces identical numerical traces. The auditor now accepts
both the committed solver metadata and the newer optional event/authority fields.
After this compatibility adjustment, all 31 research tests also pass in an
isolated copy of the parent commit with only this research work overlaid. Rerun
the command above to create evidence and source hashes for any new checkout.
