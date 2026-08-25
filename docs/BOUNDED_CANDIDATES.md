# Bounded Candidate Integrators

BAB-CS keeps one error-bounding controller and attaches it to multiple candidate
integrators. The candidate proposes the differential state; the controller owns
algebraic projection, independent reference authority, correction, residual and
passivity gates, recursive error modeling, event resets, and periodic replay.

## Candidate Set

| Candidate | Nominal order | Candidate work | Embedded estimate | Deferred-reference eligible |
| --- | ---: | --- | --- | --- |
| `explicit_euler` | 1 | one projected endpoint | none | no |
| `heun` | 2 | Euler stage plus projected Heun endpoint | Euler/Heun difference | yes |
| `rk23` | 3 | three projected Bogacki-Shampine stages | embedded order-2 state | yes |
| `ab2` | 2 | one projected endpoint after implicit startup | Euler/AB2 difference | yes |
| `backward_euler` | 1 | one implicit candidate solve | none | no |
| `trapezoidal` | 2 | one implicit candidate solve | none | no |
| `bdf2` | 2 | one implicit candidate solve with BE startup | none | no |

An active implicit candidate must use a different implicit `reference_method`.
This prevents a zero candidate/reference difference from being mislabeled as an
independent defect estimate. The comparison runner uses trapezoidal reference
for backward Euler and BDF2 candidates, and BDF2 reference for trapezoidal.

## Shared Correction

For candidate endpoint `z_c`, independent reference endpoint `z_r`, and
correction gain `gamma`, the accepted differential proposal is

```text
z_* = (1 - gamma) z_c + gamma z_r
```

The circuit then projects `z_*` onto the algebraic MNA manifold. If projection,
passivity, stiffness, amplification, or the recursive bound fails its gate,
`gamma = 1` transfers full authority to `z_r`.

With candidate amplification estimate `G_c`, the corrected propagation model is

```text
G_closed = (1 - gamma) G_c
B_(n+1) = G_closed B_n + d_n
```

where `d_n` is corrected/reference scaled deviation plus the normalized
algebraic/full-residual contribution. The default fixed target chooses `gamma`
so `G_closed <= target_contraction`. Setting `contraction_rate = mu` instead
uses `exp(-mu h)`, making `gamma = O(h)` for a smooth high-order candidate and
avoiding an unnecessary fixed blend that can reduce observed order.

## Amplification Models

Let `x = h L`, where `L` is the differential Jacobian infinity norm multiplied
by `jacobian_safety_factor`. Built-in `Circuit` models calculate this Jacobian
from exact MNA sensitivities at the accepted algebraic solution. Circuit
subclasses retain the finite-difference fallback unless they provide their own
`differential_jacobian` implementation. Linear built-in circuits share one
factorization across all sensitivity columns and reuse Jacobians and algebraic
or implicit factors for matching component values, switch topology, method,
and step shape. Each internal cache is capped at 128 entries.

```text
Euler:       G <= 1 + x
Heun:        G <= 1 + x + x^2/2
RK23:        G <= 1 + x + x^2/2 + x^3/6
AB2:         G <= 1 + h[(1+r/2)L_n + (r/2)L_(n-1)]
Backward E.: G <= 1 / (1 - x)
Trapezoidal: G <= (1 + x/2) / (1 - x/2)
```

For variable-step BDF2, with step ratio `r`, BAB-CS bounds the augmented
two-state recurrence by

```text
G <= [(1+r) + r^2/(1+r)] / [(1+2r)/(1+r) - x]
```

Implicit denominators must remain positive. Otherwise stiffness/reference
authority takes over or the step is rejected and retried smaller. These are
computable conservative norm models, not exact spectral radii.

## Embedded Fast Path

`reference_interval_steps = N > 1` is allowed only for `ab2`, `heun`, and
`rk23`. On a deferred step,

```text
gamma = 0
B_(n+1) = G_c B_n + E_embedded + residual_ratio
```

The step is not labeled contractive when `G_c >= 1`; instead it is bounded over
the finite interval to the next authority checkpoint. A reference is promoted
immediately when any of these conditions holds:

- the configured interval is due;
- stiffness or the amplification domain requires implicit authority;
- the projected or post-correction recursive bound would exceed
  `deferred_reference_bound_cap`;
- shadow mode requires reference authority.

When the hard bound cap triggers, the accepted state is the full reference and
the propagation term resets to zero. Independent refined replay still runs at
`anchor_interval_steps`, replaces the provisional endpoint, rebuilds multistep
history, and resets the recursive bound.

Replay refinement is evidence-controlled but not optional. Pure-C and pure-L
built-in topologies retain the qualified `minimum_anchor_substeps` policy. A
mixed C+L trapezoidal replay starts at that minimum and estimates the local
quadrature defect from three independent replay derivatives. Evidence above
`anchor_embedded_error_cap` restarts the whole replay with a cubically predicted
finer subdivision. Refinement never exceeds `anchor_substeps`; reaching that
value restores the previous fixed-resolution authority even when the estimator
remains conservative. Backward-Euler and BDF2 references retain the full
refinement. `adaptive_anchor_refinement = false` restores one fixed refinement
count for every topology.

After two matching uniform replay substeps, an AB3 extrapolation supplies only
the Newton initial guess. Variable or nonmatching substeps use the existing
variable-step AB2 extrapolation, and the first replay step remains unpredicted.
After four matching uniform substeps, eligible large sparse systems also use a
quartic extrapolation of accepted algebraic solutions. A failed algebraic guess
is retried from the current accepted solution. The implicit reference residual
and convergence gates still decide whether any guess is accepted or corrected.

The fast path is therefore adaptive: smooth regions skip references; nonlinear
or poorly modeled regions automatically spend the reference work.

## Selection Guidance

- Use default `ab2` for backward-compatible BAB-CS behavior and low candidate
  work when one implicit startup is acceptable.
- Use `rk23` when accuracy per accepted timestep matters more than three stage
  projections. It is the strongest embedded fast-path candidate in the current
  implementation.
- Use `heun` when two projections are preferable and second-order accuracy is
  sufficient.
- Use implicit candidates to compare bounded wrappers around familiar circuit
  methods, not as expected speed winners: candidate and reference solves both
  contribute work.
- Keep `reference_interval_steps = 1` for strongest every-step contractive
  evidence. Increase it only for embedded candidates and retain periodic replay.
- Tighten `deferred_reference_bound_cap` for nonlinear devices or when monotone
  refinement is more important than skipped reference solves.

## Local Characterization

The following rows were measured on August 24, 2026 with the repository's quick
comparison cases. Timing is the median of seven RC runs or five diode runs and
is local characterization only. `rk23-fast` uses `reference_interval_steps = 4`
and the default hard deferred bound cap of 100 normalized units.

| Case and step | Method | Maximum absolute error | Deterministic work | Reference solves | Median seconds |
| --- | --- | ---: | ---: | ---: | ---: |
| RC, `5e-5` | bounded RK23 | `2.920279e-4` | 808 | 20 | `0.006604` |
| RC, `5e-5` | bounded RK23 fast | `2.891316e-4` | 724 | 6 | `0.005199` |
| Diode clip, `2e-6` | bounded RK23 | `3.239952e-5` | 25,920 | 500 | `0.219980` |
| Diode clip, `2e-6` | bounded RK23 fast | `7.728687e-5` | 24,071 | 180 | `0.187978` |
| Diode clip, `2e-6` | bounded Heun | `1.032475e-4` | 23,968 | 500 | `0.206141` |
| Diode clip, `2e-6` | bounded Heun fast | `7.729736e-5` | 22,794 | 309 | `0.184959` |
| Diode clip, `2e-6` | active bounded AB2 | `5.659887e-4` | 22,426 | 512 | `0.193724` |
| Diode clip, `2e-6` | bounded AB2 fast | `3.493050e-4` | 21,428 | 314 | `0.176195` |

At the fine RC step, RK23 fast reduced median time by 21.3%, deterministic work
by 10.4%, and reference solves by 70% relative to bounded every-step RK23, with
essentially unchanged error. At the fine nonlinear diode step, it reduced time
by 14.5%, work by 7.1%, and references by 64%; maximum error was 2.39 times the
every-step RK23 error but remained 7.32 times smaller than active bounded AB2.
The maximum recursive bound for every fast diode row remained below the hard
configured cap of 100.

## Claim Boundary

The recursive bound is relative to the implemented local amplification,
embedded/reference defect, residual, and replay model. It does not prove error
against an unknown exact physical trajectory. Fast-path steps can be
noncontractive, but their growth is capped by dynamic reference promotion and a
finite independent replay interval. Benchmark timing is characterization, not a
portable performance guarantee.
