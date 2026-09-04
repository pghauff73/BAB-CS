# Affine Replay with an Explicit Total-Error Budget

Research direction 1, developed 5 September 2026. Status: mathematical derivation
and executable restricted pilot; not a proof of the existing BAB-CS production
controller, and not a machine-checked proof.

**Main result.** Replaying a window from an uncertain anchor can replace the
window's numerical defect, but must retain the propagated anchor uncertainty.
For a window of length H, the replacement radius is

```text
B_new = G(H) B_anchor + D_replay.
```

Here G bounds the exact system's sensitivity and D_replay bounds the replay
trajectory's accumulated defect. Neither a small candidate/replay difference
nor a derivative-history reset permits setting B_new to zero. This result does
not assert that replay always improves a bound: that requires comparing the
replacement radius with the provisional radius.

The accompanying [pilot](../tools/replay_error_budget.py) makes the proof
quantities rational and computes them independently of the production
`estimated_bound`, `reference_uncertainty`, and interval reachability routines.
The interval underflow finding in the literature review remains a separate,
unrepaired production issue; this experiment does not depend on that routine.

**Literature position.** Logarithmic norms and differential inequalities provide
established routes from local defects and initial uncertainty to global error
bounds. Neumaier's [1993 manuscript](https://arnold-neumaier.at/ms/ode.pdf) develops
rigorous enclosures for dissipative ODEs. Cao and Petzold's
[2004 paper](https://doi.org/10.1137/S1064827503420969) develops adjoint-based
global error estimation. The theorem below is a specialization of standard
variation-of-constants reasoning to an explicit replay ledger. It is not a
claim to have invented global error control. A publishable contribution would
need a stronger algorithmic result or an experimentally established tradeoff.

**Assumptions and scope.**

1. On each segment the exact reduced circuit obeys x' = A x + b, with known,
   constant real A and b. The affine ODE has a unique global solution.
2. Segment boundaries are known scheduled times, landed on exactly. State is
   continuous at the source changes in the pilot. Unknown guards, delay,
   jitter, grazing, and general state-triggered switches are excluded.
3. One fixed norm is used across every segment of an error ledger. A number mu
   is proved to satisfy ||exp(A t)|| <= exp(mu t), t >= 0. Choosing mu from
   eigenvalue real parts alone is insufficient for non-normal matrices.
4. The initial point a approximates the true initial state with
   ||x(t_anchor)-a|| <= B_anchor. Every replay starts at this same a.
5. Each approximation has a specified continuous reconstruction within each
   segment, with a valid bound on its differential defect. Computation and
   endpoint rounding are included in that defect.
6. An extension to an index-1 DAE requires an exact justified reduction or a
   separate enclosure of algebraic solve error and conditioning. This pilot
   uses explicitly written reduced circuit equations, not a certified MNA
   reduction. Uncertain coefficients are not implemented.

The state norm bounds errors in the declared mathematical model, not model
discrepancy from hardware. A change of norm or units requires an explicit
conversion factor; the production controller's state-dependent tolerance norm
cannot be substituted without deriving that factor.

**Segment theorem and proof.** Let p(s), 0 <= s <= h, be a differentiable
reconstruction of the computed segment, p(0)=a and p(h)=c. Define

```text
r(s) = p'(s) - A p(s) - b,
||r(s)|| <= d,
phi(mu,h) = (exp(mu h)-1)/mu     if mu != 0,
phi(0,h) = h.
```

Then, for every s in [0,h],

```text
||x(t+s)-p(s)|| <= exp(mu s) B + phi(mu,s) d.
```

Proof: e(s)=x(t+s)-p(s) satisfies e'=A e-r and ||e(0)||<=B. Variation of
constants gives e(s)=exp(A s)e(0)-integral_0^s exp(A(s-u))r(u) du. Apply the norm,
the semigroup bound, and the uniform defect bound, then integrate the scalar
exponential. This proves the complete segment bound, not just its endpoint.
Replacing exp and phi by enclosing upper bounds preserves the inequality.

For consecutive segments, the endpoint recurrence is

```text
B_(j+1) = G_j B_j + phi_j d_j,
G_j >= exp(mu_j h_j),   phi_j >= phi(mu_j,h_j).
```

Induction proves containment at every endpoint. The dense bound describes the
chosen reconstruction; it is not a claim about an unspecified dense-output
interpolator elsewhere in BAB-CS.

**Replay theorem and proof.** Let a replay consist of m certified segments from
the original anchor point a to a replacement endpoint c_R. With exact growth
factors for readability, expand the preceding recurrence:

```text
G_window = product_(j=0..m-1) G_j,
D_replay = sum_(j=0..m-1) [ product_(k=j+1..m-1) G_k ] phi_j d_j,
B_R = G_window B_anchor + D_replay.
```

The segment theorem applied successively to the replay proves
||x(t_end)-c_R|| <= B_R. The provisional path does not enter this proof; it may
have different local steps or a different method. Both paths approximate the
same unique solution from the same uncertain anchor. Replacing the provisional
endpoint with c_R therefore installs B_R as the new radius. No candidate/replay
distance needs to be added when this separate replay certificate is used.

If a replay certificate is unavailable but the provisional endpoint c_P has
radius B_P, the triangle inequality gives the weaker valid transfer

```text
||x(t_end)-c_R|| <= B_P + ||c_P-c_R||.
```

The distance alone is not a certificate. If two correct bounds are available
at the same center, their minimum is valid. Bounds at different centers cannot
be minimized without transferring centers or intersecting their sets.

Earlier accepted provisional samples retain their original radii. A replay
certificate does not retroactively improve samples whose values were not
replaced. The pilot preserves both the provisional radius at the refresh time
and the new accepted radius; it does not silently rewrite earlier evidence.

**What contraction does and does not guarantee.** If every anchor window has
G_window <= rho < 1 and D_replay <= D_max, repeated replay implies

```text
B_k <= rho^k B_0 + D_max * (1-rho^k)/(1-rho).
```

This gives a finite asymptotic radius D_max/(1-rho), subject to those uniform
assumptions. Here rho describes exact-flow sensitivity in the chosen norm.
It is not the production controller's q=(1-gamma)G_candidate, which measures
its proposal/reference relation.

For a neutral LC flow in energy coordinates, G_window=1 is valid and
B_k <= B_0 + sum D_replay. There is no uniform-in-time accuracy guarantee from
this argument unless cumulative replay defects have a finite bound. Replacing
a numerical endpoint cannot erase physical initial-condition uncertainty.

**Events and algebraic constraints.** At a scheduled source change with
continuous state, carry the radius through unchanged and start the next
segment with the new A,b. Resetting derivative history is a numerical action,
not evidence that the exact-state error disappeared. For a known reset map R
with Lipschitz constant L_R and certified reset computation error epsilon_R,
the extension is B_plus <= L_R B_minus + epsilon_R. This reset extension is
proved by the triangle inequality but is not implemented in the pilot.

Unknown event times require separate guard/transversality and timing-error
terms. For algebraic variables z satisfying g(x,z)=0, a small residual must be
combined with an appropriate inverse-Jacobian/conditioning bound and uniqueness
region before it becomes a state-error contribution. Neither extension is
obtained by merely adding a normalized residual to B.

**Computable defect certificate.** The pilot reconstructs each pair of stored
endpoints with cubic Hermite interpolation. Write s=(t-t_j)/h and
p(s)=c0+c1*s+c2*s^2+c3*s^3, with

```text
c0 = x_j
c1 = h f(x_j)
c2 = 3(x_(j+1)-x_j) - h(2 f(x_j)+f(x_(j+1)))
c3 = 2(x_j-x_(j+1)) + h(f(x_j)+f(x_(j+1))).
```

For constant A,b, p'/h-Ap-b is a cubic polynomial in s. Its power coefficients
are converted exactly to cubic Bernstein coefficients. Bernstein basis
functions are nonnegative and sum to one on [0,1], so the norm of the defect
is bounded by the largest coefficient norm. The infinity norm is computed
exactly; for the Euclidean metric the rational l1 norm provides an upper bound
on each coefficient's l2 norm. This sacrifices tightness without assuming that
l1 and l2 propagation rates are the same.

The reconstruction is independent of whether endpoints came from Euler,
trapezoidal integration, or another proposal method. The pilot uses Euler
proposals and refined trapezoidal replay. For trapezoidal endpoints the
Hermite defect captures higher-order cancellation that a straight line between
endpoints would lose.

**Arithmetic implementation.**

- Coefficients, states, defects, exponential enclosures, and radii use Python
  Fraction. No binary-float primitive contributes to a proof quantity.
- Proposed states are rounded to the nearest rational multiple of 1e-24. The
  reconstruction uses these stored endpoints, so the resulting error enters
  the defect rather than being omitted.
- Radii are rounded upward to multiples of 1e-24. The pilot separately
  propagates inherited anchor uncertainty and fresh replay defect, rounding
  each upward; their sum remains an upper bound.
- For |z|<=1, exp(z) is enclosed using a degree-24 rational Taylor sum for
  |z| and a geometric upper bound on the omitted tail. Negative z uses interval
  reciprocation. phi uses the correct exponential endpoint for the sign of mu.
  Larger |mu*h| is explicitly rejected rather than silently approximated.
- mu_infinity is the exact maximum diagonal-plus-absolute-off-diagonal row
  sum. The two-state Euclidean path checks A+A^T negative semidefinite exactly
  and then uses mu=0. Unsupported matrices fail explicitly.
- Floating-point summary numbers and 80-digit Decimal matrix-series comparisons
  are diagnostics. Exact radii, state coordinates, and times are serialized as
  rational strings. The Decimal comparison is not the proof or an interval
  oracle.

The trusted computing base includes Python's integer/Fraction operations, the
pilot's implementations, and this mathematical argument. This is a small
auditable calculation, not independent formal verification of the program.

**Pilot model and protocol.** The dimensionless cases are RC decay x'=-x;
RL startup x'=-2x+1; damped series RLC v'=i, i'=-v-2i; neutral LC v'=i,
i'=-v; and RC startup followed by a source removal at t=1. RLC/LC use C=L=1
and the Euclidean energy-coordinate norm. The matrix and initial states are
serialized in the report. These are explicitly reduced equations, not an
automatic translation of the repository's differently scaled example files.

The study uses horizon 2, h=1/20 and 1/40, replay intervals 1,4,16, and a
no-replay Euler control. Replay refinement is four, with additional RC
refinement runs at 1,2,8. A nonzero RC initial radius of 1/1000 checks inherited
uncertainty. Pure refined-trapezoidal baselines at h=1/20 omit proposal work.
Every scheduled event and final time closes the replay window. The no-replay
control still respects the known source boundary and carries its radius.

Run from the repository root:

```bash
python -m unittest discover -s tests -p 'test_replay_error_budget.py' -v
python tools/replay_error_budget.py --output /tmp/replay-error-budget.json
```

The output path must be new. The report records hashes of the executable,
theorem, and tests, plus interpreter version, settings, exact traces, inherited
and fresh radius contributions, and candidate/replay work counts. There are no
wall-clock speed claims: exact rational verification has substantial overhead.

**Integration boundary and next criterion.** This pilot neither changes
production acceptance nor replaces `estimated_bound`. To integrate it, BAB-CS
would need a verified affine reduction, fixed-norm policy, replay substep traces
or equivalent defect certificates, explicit anchor radii, event/reset transfer,
and auditable rounding bounds. The current dual-resolution reference estimate
is useful comparative evidence but is not automatically the B_anchor required
by this theorem. Nonlinear and state-triggered extensions remain separate
research tasks.

The next success criterion is a prototype integrated with one actual affine
BAB-CS circuit that preserves this total-error meaning and demonstrates a
better error/work frontier. Increasing replay interval alone is not evidence
of saved reference work: replaying every elapsed interval at the same fine
resolution still processes every fine substep, and adds proposal work.
