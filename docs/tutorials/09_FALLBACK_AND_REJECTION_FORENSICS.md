# Tutorial 9: Fallback and Rejection Forensics

A rejection means that one proposed step did not satisfy the declared rules. A
fallback means that BAB-CS transferred the step to an implicit authority rather
than accepting the candidate proposal. Neither event automatically means that
the complete simulation failed.

![Fallback and rejection forensics](html/assets/tutorial-09-fallback-forensics.svg "Rejected work, implicit fallbacks, event resets, and periodic reanchors remain separately visible.")

## What You Will Learn

The exercise uses the scheduled H-bridge resistor-inductor (`RL`) load. An
H-bridge is a four-switch arrangement that can apply either voltage polarity to
a load. The example is a reduced-order numerical experiment: it represents
scheduled resistive switches and an RL load without claiming transistor,
dead-time, thermal, protection, or electromagnetic device fidelity.

## Run the Exercise

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 09-fallback-forensics
```

## Expected Results

The scheduled reduced-order H-bridge contains discontinuous switch changes and
is expected to challenge the candidate method. Some rejected attempts,
fallbacks, event resets, and periodic reanchors are therefore expected. The
complete simulation is still expected to reach `0.0004` seconds, and every
rejection should retain a stable cause rather than disappear from the work
record.

## Observed Data

The exercise was run on August 27, 2026.

| Evidence channel | Observed count or value |
| --- | ---: |
| Rejected candidate steps | `9` |
| Implicit fallbacks | `8` |
| Event history resets | `8` |
| Periodic reanchors | `12` |
| Embedded-candidate-cap rejections | `8` |
| Reference-solve failures | `1` |
| Accepted stop time | `0.0004` seconds |
| Reduced-order numerical experiment | `true` |
| Production device claim | `false` |

Eight of the nine rejected attempts were associated with the embedded
candidate cap, and one was associated with a reference-solve failure. The run
still reached its declared stop time because controlled retries and eight
implicit fallbacks supplied accepted states where candidate proposals could not
be promoted.

## Expected Versus Actual Results

The run matched the qualitative expectation and reached the stop time. It
recorded nine rejected attempts but eight implicit fallbacks. These counts are
not expected to be equal because a rejected attempt is not an accepted step: a
smaller retry can succeed, and one accepted state can follow several attempts.
The evidence attributes eight rejections to the embedded candidate cap and one
to a reference-solve failure.

The actual counts show that candidate difficulty dominated this run, while the
independent reference encountered one failed attempt. The data does not prove
that the same proportions will occur under another schedule, timestep, device
model, or solver configuration.

## Separate the Evidence Channels

The reviewed run records:

- rejected candidate steps;
- implicit fallbacks;
- exact event resets;
- periodic reanchors;
- candidate-cap causes; and
- a reference-solve cause.

The embedded candidate cap is a limit on the candidate method's own local error
estimate. When that estimate is too large, BAB-CS can reduce the step, retry, or
transfer authority.

A reference-solve failure is different. It means the independent implicit solve
did not meet its nonlinear convergence contract at the attempted time and
step. Nonlinear convergence means that repeated Newton iterations reduced the
circuit-equation mismatch and update size below declared tolerances.

## Why Rejected Work Must Stay Visible

Counting only accepted steps makes a difficult method look cheaper than it was.
Rejected attempts still used circuit evaluations, linear solves, and nonlinear
iterations. They also identify operating regions that challenge the candidate
or authority.

BAB-CS retains causes instead of reducing everything to a generic “solver
failed” message. Engineering teams can then distinguish:

- candidate instability;
- nonlinear device difficulty;
- event-related restart;
- overly strict gates;
- minimum-step exhaustion; and
- authority nonconvergence.

## Theory and Practical Outcomes

The theoretical outcome is fail-closed authority transfer: a rejected proposal
does not become accepted merely because work has already been spent on it. The
practical outcome is an auditable cost and failure record.

Forensics are useful when selecting a method for converter schedules, load
interruption, fault studies, or controller testing. A method with a low accepted
step count may still perform poorly if it creates many expensive retries.

## Conclusion

The reduced-order H-bridge completed successfully through controlled retries
and fallback. The experiment confirms that rejected work and its causes remain
visible, which is necessary for honest method-cost and robustness comparisons.

## Claim Boundary

The verifier proves that the reduced-order example reaches its declared stop
time while preserving rejection and fallback evidence. It does not validate a
production H-bridge, semiconductor stress, hardware safety, or control-system
certification.
