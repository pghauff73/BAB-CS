# Bounded and Interval Newton Research

BAB-CS includes two scalar bounded-Newton research paths that apply the
project's candidate/authority pattern to root finding:

- `bounded_newton_raphson` uses ordinary endpoint Newton proposals, while a
  sign-changing bracket and mandatory midpoint step retain authority.
- `interval_newton` accepts a derivative enclosure over the complete current
  bracket and uses the interval-Newton operator to contract both sides at once.
  The contraction controls the result only when it earns at least the same
  half-width reduction as bisection; otherwise bisection takes authority.

This is deliberately separate from the circuit solver's vector Newton systems.
The scalar methods establish one-dimensional enclosure results under their
stated assumptions; they do not turn damped MNA Newton iteration into an
interval proof.

## Algorithm

For a continuous real function `f`, derivative `f'`, and initial bracket
`[a_0, b_0]` satisfying

```text
a_0 < b_0
f(a_0) f(b_0) < 0,
```

one bounded Newton iteration performs the following operations:

1. Order the two bracket endpoints by increasing `|f|`.
2. Try an ordinary Newton proposal from the better endpoint,
   `x_N = x - f(x) / f'(x)`.
3. If that derivative is zero or nonfinite, or `x_N` is outside the bracket,
   try the other endpoint. If neither proposal is admissible, skip Newton.
4. If an admissible Newton proposal is finite and strictly inside the bracket,
   evaluate it and retain the sign-changing sub-bracket.
5. Evaluate the midpoint of the resulting bracket and again retain the
   sign-changing sub-bracket.

An exact sampled zero terminates immediately. Invalid derivative evidence never
controls the result; the method falls back to bisection. Invalid function
evaluations fail closed because the sign argument is then unavailable.

The implementation is `bounded_newton_raphson` in
`src/babcs/rootfinding.py`. The same module provides `interval_newton`, pure
Newton-Raphson, secant, bisection, and Ridders methods with common deterministic
diagnostics.

## Bracket Invariant and Global Bound

**Theorem 1.** Let `f` be continuous on `[a_0, b_0]` with opposite nonzero
endpoint signs. If bounded Newton-Raphson completes `k` authority iterations
without sampling an exact zero, then its brackets are nested, each bracket
contains at least one zero of `f`, and

```text
b_k - a_k <= 2^(-k) (b_0 - a_0).
```

**Proof.** The intermediate value theorem gives at least one zero in the
initial bracket. An accepted Newton point lies strictly inside the current
bracket. Replacing the endpoint with the same sign as the new point preserves a
sign change and cannot increase the width. The mandatory midpoint then divides
that retained bracket into two equal halves; choosing the sign-changing half
preserves a zero and reduces the width by at least one half. Induction gives the
stated nesting and width bound. The nested-interval theorem and continuity then
give convergence of the enclosures to a zero. No uniqueness claim follows from
the sign change alone.

For the returned rounded midpoint `m_k`, BAB-CS reports

```text
E_k = max(m_k - a_k, b_k - m_k).
```

Therefore every mathematical zero retained in the numerical bracket is within
`E_k` of the returned point. Using the maximum rounded side rather than the
symbolic half-width avoids a one-ULP understatement when the floating midpoint
is not exactly centered.

The theorem is intentionally simpler and more conservative than Brent's method
or high-order enclosing algorithms. Brent combines interpolation with
bisection, giving guaranteed convergence and usually superlinear practical
behavior [[37]](REFERENCES.md#ref-37). Bus and Dekker established explicit
worst-case evaluation bounds for related interpolation/bisection hybrids
[[38]](REFERENCES.md#ref-38). Algorithm 748 goes further by proving high-order
convergence of enclosing-interval diameters [[40]](REFERENCES.md#ref-40).

## Highest-Gain Direction: Interval Newton

The highest-gain extension found in the research audit is not a more permissive
clip for an ordinary endpoint Newton point. It is an interval-Newton contractor
that can move both enclosure endpoints from one center evaluation. For current
interval `X = [a, b]`, center `m`, and a derivative enclosure `D(X)` that
contains every derivative value on `X` and excludes zero, define

```text
N(X) = m - f(m) / D(X)
X_new = X intersect N(X).
```

BAB-CS widens the scalar division and subtraction endpoints by one
`math.nextafter` step. It accepts `X_new` only when

```text
width(X_new) <= width(X) / 2.
```

An invalid derivative interval, an interval containing zero, an empty or
stagnant operator result, or a contraction weaker than one half cannot control
the result. The implementation recovers any unsampled endpoint signs and takes
a midpoint bisection step instead.

**Theorem 2.** Let `f` be differentiable on `X`, let `alpha` be a zero in `X`,
and let `D(X)` contain `f'(x)` for every `x` in `X`, with `0` not in `D(X)`.
Then `alpha` is in `N(X)`, so `X intersect N(X)` retains the zero. Every
completed BAB-CS interval-Newton authority iteration also satisfies

```text
width(X_(k+1)) <= width(X_k) / 2.
```

**Proof.** The mean value theorem gives a point `xi` between `m` and `alpha`
such that

```text
f(m) - f(alpha) = f'(xi) (m - alpha).
```

Since `f(alpha) = 0` and `f'(xi)` is in `D(X)`, rearrangement places `alpha` in
`m - f(m) / D(X)`. Intersecting with `X` therefore retains it. The
implementation accepts that interval only when its width is at most one half
of the prior width. Every other completed iteration is a sign-preserving
bisection step, which has the same width bound. Induction gives nested
root-containing enclosures and the stated global contraction. Because the
derivative enclosure excludes zero, it also establishes uniqueness inside that
specific interval under the oracle assumptions. This is the scalar
mean-value/interval-Newton construction developed in the interval literature
[[42]](REFERENCES.md#ref-42) [[45]](REFERENCES.md#ref-45).

## Local Newton Rate

Suppose `alpha` is a simple zero, `|f'(x)| >= m > 0` near `alpha`, and `f'` is
Lipschitz there with constant `L`. For an accepted ordinary Newton proposal,
Taylor's theorem gives

```text
|x_(n+1) - alpha| <= L / (2m) |x_n - alpha|^2.
```

Thus the Newton proposal subsequence can retain the classical local quadratic
rate when the endpoint is close enough and the proposal remains inside the
bracket. The certified enclosure radius is different: this implementation only
claims the unconditional geometric factor from Theorem 1. A fast point estimate
must not be mislabeled as a quadratically shrinking enclosure.

Kantorovich's theorem supplies a stronger semilocal Newton result when an
invertible derivative, a derivative-Lipschitz bound, and a sufficiently small
initial Newton correction are available [[36]](REFERENCES.md#ref-36). Those
hypotheses can prove existence, uniqueness in a specified neighborhood,
well-defined iterates, and computable error bounds, but they are problem data,
not properties that a step clip creates automatically.

## Work Bound

After the two endpoint evaluations, each completed bounded-Newton authority
iteration uses at most:

- two derivative evaluations, because both endpoints may be tried;
- one Newton-candidate function evaluation;
- one midpoint function evaluation.

For `k` completed iterations and one final midpoint evaluation,

```text
function evaluations   <= 3 + 2k
derivative evaluations <= 2k.
```

This bound is deterministic, but bounded Newton is not guaranteed to be the
cheapest bracketed method. Its purpose is a transparent Newton-plus-authority
construction whose proof mirrors BAB-CS candidate/reference separation.

For interval Newton, the accepted fast path uses one center function evaluation
and one derivative-interval evaluation per completed authority iteration. With
two initial endpoint evaluations and one final midpoint evaluation, a run of
`k` continuously accepted contractions satisfies

```text
function evaluations            <= 3 + k
derivative-interval evaluations <= k.
```

If a fallback follows an accepted interval contraction, up to two unsampled
endpoint values are recovered before bisection. The conservative general bound
is therefore `3 + 3k` function evaluations, although repeated bisection from an
already sampled sign bracket still uses only one new function value per
iteration.

## Method Comparison

| Method | Derivative | Retains bracket | Broad guarantee | Local behavior near a simple root |
| --- | --- | --- | --- | --- |
| Newton-Raphson | yes | no | local only without globalization assumptions | quadratic |
| Secant | no | no | local; denominator and basin failures remain possible | superlinear |
| Bisection | no | yes | geometric enclosure for a continuous sign change | linear, factor `1/2` |
| Bounded Newton-Raphson | yes | yes | geometric enclosure, factor at most `1/2` per authority iteration | quadratic Newton proposals, linearly certified enclosure |
| BAB-CS interval Newton | derivative enclosure | yes | interval-operator retention plus factor at most `1/2` per authority iteration | often rapid two-sided contraction; bisection when the derivative interval includes zero |
| Ridders | no | yes | bracket retained; original analysis gives quadratic or better local rate | quadratic or better [[39]](REFERENCES.md#ref-39) |
| Brent | no | yes | guaranteed convergence with a bisection-class safeguard | usually superlinear [[37]](REFERENCES.md#ref-37) |
| Interval Newton/Krawczyk | interval Jacobian | interval box | can verify existence, uniqueness, and error bounds under interval hypotheses | often rapid local contraction [[42]](REFERENCES.md#ref-42) [[43]](REFERENCES.md#ref-43) |

For vector nonlinear systems, residual-decreasing line searches and trust
regions are globalizations, not root enclosures. Eisenstat and Walker prove
conditional global convergence results for inexact Newton methods with adequate
progress tests [[41]](REFERENCES.md#ref-41). Interval Newton and Krawczyk
operators provide the stronger existence/uniqueness machinery when rigorous
interval Jacobians are available [[42]](REFERENCES.md#ref-42). Merely clipping a
vector Newton step does not establish either theorem
[[43]](REFERENCES.md#ref-43).

## Ranked Research Directions

1. **Interval Newton with an explicit derivative enclosure — implemented.** It
   offers the largest measured reduction because one center evaluation can
   contract both sides, and it strengthens the mathematical oracle from a point
   derivative to a complete derivative range.
2. **Minmax-projected Newton/ITP safeguard — retained as future work.** The ITP
   result characterizes non-midpoint queries that preserve bisection's minmax
   iteration bound [[44]](REFERENCES.md#ref-44). Applying that projection to an
   endpoint Newton point saves a mandatory midpoint evaluation in principle,
   but it can repeatedly tighten only the near-root side while leaving the
   opposite enclosure endpoint wide. It was therefore not selected as the
   primary bounded-Newton upgrade.
3. **Algorithm 748 or Brent-class derivative-free fallback — future work.** A
   high-order enclosing fallback could reduce the multiple-root and
   zero-containing-derivative cases where interval Newton must currently
   bisect, at the cost of materially more state and proof complexity
   [[37]](REFERENCES.md#ref-37) [[40]](REFERENCES.md#ref-40).
4. **Vector Krawczyk/Hansen-Sengupta authority — separate project.** This is the
   appropriate direction for existence and uniqueness of full nonlinear MNA
   systems, but it requires interval Jacobians, outward-rounded linear algebra,
   and box-level validation rather than a scalar API retrofit
   [[43]](REFERENCES.md#ref-43) [[45]](REFERENCES.md#ref-45).

## Deterministic Experiments

Run the comparison with:

```bash
PYTHONPATH=src python tools/compare_rootfinders.py \
  --output /tmp/babcs-rootfinders.json \
  --csv-output /tmp/babcs-rootfinders.csv
```

The August 27, 2026 working-tree run used absolute, relative, and residual
tolerances of `1e-12` with an 80-iteration budget. The columns below are
`iterations / function evaluations / derivative evaluations`.

| Case | Newton | Bounded Newton | Interval Newton | Secant | Bisection | Ridders |
| --- | --- | --- | --- | --- | --- | --- |
| `square_root_two` | `5 / 6 / 5` | `6 / 14 / 7` | `5 / 8 / 5` | `7 / 9 / 0` | `39 / 42 / 0` | `6 / 15 / 0` |
| `exponential_root` | `5 / 6 / 5` | `7 / 16 / 8` | `5 / 8 / 5` | `8 / 10 / 0` | `39 / 42 / 0` | `5 / 13 / 0` |
| `newton_cycle` | failed budget | `5 / 11 / 5` | `5 / 8 / 5` | `50 / 52 / 0` | `39 / 42 / 0` | `7 / 16 / 0` |
| `multiple_root` | `22 / 23 / 22` | `33 / 69 / 33` | `39 / 42 / 39` | `30 / 32 / 0` | `39 / 42 / 0` | `32 / 67 / 0` |
| `diode_operating_point` | failed budget | `33 / 44 / 61` | `9 / 12 / 9` | failed denominator | `39 / 42 / 0` | `13 / 23 / 0` |

The comparison exposes three important boundaries:

1. Pure Newton is cheapest on the smooth easy roots, but the selected cubic
   cycles and the diode initial value exhaust its budget.
2. A residual-only stop is not a position certificate at a multiple root. Pure
   Newton stopped with about `6.68e-5` position error because cubing makes the
   residual tiny; the bracketed methods returned approximately `1e-12`
   enclosures.
3. Across these five fixed cases, interval Newton reduced function evaluations
   from `154` to `78` (`49.4%`) and equally weighted total oracle calls from
   `268` to `141` (`47.4%`) versus bounded Newton. On the diode case alone, the
   reductions were `44` to `12` function evaluations and `105` to `21` total
   calls.
4. The multiple root is the important limitation. Its derivative enclosure
   contains zero at every retained interval, so interval Newton correctly
   degenerates to bisection. It still returns a positional enclosure, but it
   provides no interval-Newton acceleration there.

These are deterministic case results, not a universal ranking.

## Proof Boundary

The sign-bracket methods assume a continuous mathematical function and
trustworthy finite signs. `interval_newton` additionally assumes that every
returned derivative interval encloses the complete mathematical derivative
range on the requested bracket. A wrong enclosure can invalidate root
retention; the callback is authority-bearing problem evidence, not a heuristic.

The implementation widens the interval division and subtraction results by one
floating-point step to prevent a correctly rounded simple-root contraction from
collapsing spuriously to an uncertified singleton. Python `float` evaluation of
`f(m)` and the user callback is still not an outward-rounded interval extension
of arbitrary code. The returned bracket is therefore a numerical enclosure
under the stated function and oracle assumptions, not a machine-checked proof
against all rounding error. A proof-producing extension would need
interval-valued function and derivative evaluation with directed rounding,
followed by the interval Newton or Krawczyk inclusion machinery from the cited
literature [[42]](REFERENCES.md#ref-42) [[43]](REFERENCES.md#ref-43).
