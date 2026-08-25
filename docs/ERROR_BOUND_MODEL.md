# BAB-CSv1 Error-Bound Model

## Predictor

For an index-1 reduced system `z' = f(t, z)`, variable-step AB2 produces

```text
z_ab = z_n + h * ((1 + r/2) f_n - (r/2) f_(n-1)).
```

The implementation estimates a conservative predictor amplification from the
infinity norms of finite-difference differential Jacobians:

```text
G = max(1, 1 + h * ((1 + r/2) ||J_n|| + (r/2) ||J_(n-1)||)).
```

This is deliberately conservative and is used as a runtime gate rather than a
claim that the estimate is spectrally exact.

## Correction

With correction gain `gamma`, the provisional closed-loop estimate is

```text
q = (1 - gamma) G.
```

The integrator increases `gamma` to target `q <= target_contraction`. If the
configured correction range cannot establish `q < 1`, or if the stiffness gate
fires, the implicit reference receives full authority and `q` becomes zero
relative to that local reference.

## Recursive Bound

The accepted-step estimate is

```text
delta = corrected_reference_error + normalized_residual
B_next = q * B_current + delta.
```

If `q <= q_max < 1` and `delta <= delta_max`, then

```text
B_n <= q_max^n B_0 + delta_max / (1 - q_max).
```

The recorded estimate is reset after independent re-anchoring, events, and
history resets.

## Independent Anchor

The local implicit reference used in each step begins from the accepted current
state and therefore is not fully independent of accumulated trajectory error.
The periodic anchor addresses this by replaying from an earlier trusted
checkpoint using smaller implicit steps.

The anchor deviation is

```text
eta_anchor = ||z_provisional - z_replay||_W.
```

The replay state replaces the provisional state whether the anchor is routine
or exceeds the safety cap. Exceeding the cap is recorded as a safety re-anchor.

For mixed capacitor/inductor circuits using trapezoidal replay, BAB-CS can start
at the configured minimum refinement and estimate the local replay error without
another circuit solve. For consecutive replay derivatives `f_(k-1)`, `f_k`, and
`f_(k+1)` separated by `h_0` and `h_1`, it estimates the trapezoidal quadrature
defect as

```text
d_k = h_1^3 / (6 (h_0 + h_1))
      * ((f_(k+1) - f_k) / h_1 - (f_k - f_(k-1)) / h_0).
```

`||d_k||_W` is scaled with the same state tolerances as the controller. If the
maximum replay defect exceeds `anchor_embedded_error_cap`, the complete replay
restarts from the trusted anchor with a finer subdivision predicted from the
cubic local-error model. The subdivision is capped at `anchor_substeps`; that
cap is the previous fixed-resolution authority, so estimator failure falls back
to the prior design rather than accepting an unqualified coarser replay.
Non-finite replay evidence still rejects the step. Known event boundaries reset
the anchor history and are never crossed by adaptive replay.

## Passivity Defect

For stored energy `H`, source power `P_s`, and dissipated power `P_d`, BAB-CS
uses the trapezoidal work estimate

```text
defect = H_(n+1) - H_n - h/2 * ((P_s,n - P_d,n) + (P_s,n+1 - P_d,n+1)).
```

Only positive defect is treated as artificial numerical energy injection for
the hard passivity gate. Signed balance error is still logged so numerical
damping remains visible.

## Limits

- A small MNA residual does not imply a small trajectory error.
- Bounded energy does not imply bounded oscillator phase.
- A local implicit corrector is not an independent global anchor.
- Chaotic or physically unstable circuits cannot have indefinite exact
  trajectory agreement guaranteed by this mechanism.
- The finite-difference Jacobian norm is a conservative stiffness indicator,
  not a complete absolute-stability analysis.
