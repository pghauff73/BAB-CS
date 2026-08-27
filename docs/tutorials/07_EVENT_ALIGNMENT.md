# Tutorial 7: Exact Event Alignment

An event is a declared time at which a source, switch, or other scheduled input
changes its behavior. Event alignment means that the simulator lands exactly on
that time rather than stepping past it and treating the change as if it occurred
somewhere inside a long timestep.

![Exact event alignment timeline](html/assets/tutorial-07-event-alignment.svg "Five switch events are reached exactly and followed by multistep startup behavior.")

## What You Will Learn

The exercise uses a scheduled switched resistor-capacitor (`RC`) circuit. The
switch control is a pulse waveform: a repeating low and high schedule with
declared transition times.

Adams-Bashforth is a multistep method. A multistep method uses information from
earlier accepted steps to propose the next state. That history becomes invalid
when a switch changes the circuit equations.

## Run the Exercise

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 07-event-alignment
```

The nominal timestep is deliberately chosen so that ordinary steps do not land
naturally on every scheduled transition. The simulator must shorten a step when
necessary.

## Expected Results

The pulse schedule contains five transitions within the simulated interval.
The simulator is expected to accept a point at every declared transition,
record five event history resets, and restart the multistep method after the
first four events. The fifth event coincides with the stop time, so no startup
step is expected after it.

## Observed Data

The exercise was run on August 27, 2026.

| Event | Scheduled time | Accepted boundary time | Exact match |
| ---: | ---: | ---: | --- |
| 1 | `0.0001` seconds | `0.0001` seconds | `true` |
| 2 | `0.0002` seconds | `0.0002` seconds | `true` |
| 3 | `0.0005` seconds | `0.0005` seconds | `true` |
| 4 | `0.0006000000000000001` seconds | `0.0006000000000000001` seconds | `true` |
| 5 | `0.0009000000000000001` seconds | `0.0009000000000000001` seconds | `true` |

The report recorded five event history resets and four startup steps after
events. The fifth event is the stop time, so the simulation ends there and does
not need another startup step.

## Expected Versus Actual Results

The event count, accepted times, history-reset count, and startup count matched
the expectation exactly. The displayed values
`0.0006000000000000001` and `0.0009000000000000001` differ from the shorter
human decimal forms `0.0006` and `0.0009` only because those decimals do not have
exact finite binary floating-point representations. Scheduled and accepted
values use the same representation and therefore still match exactly under the
declared comparison.

## Follow One Event

At each switch transition, BAB-CS performs this sequence:

1. identify the next breakpoint, meaning the next declared event time;
2. shorten the proposed step so its endpoint equals the event;
3. solve and accept the event-boundary state under the declared authority;
4. record `history_reset_reason = event`; and
5. take a startup step before using multistep history again.

The verifier compares the scheduled and accepted event lists to an absolute
tolerance of one femtosecond. A femtosecond is `10^-15` seconds. The tight gate
is appropriate because these event times are declared inputs, not measured
physical events with uncertainty.

## Why Interpolation Is Not Enough

If a step crosses a switch event, the differential equations used before and
after the transition are different. Interpolating a state backward from the end
of the step does not undo the fact that the wrong equations were integrated
over part of the interval.

Exact alignment is therefore both a numerical and an engineering requirement.
It supports repeatable switching loss studies, dead-time studies, protection
logic experiments, and controller schedule screening.

## Read the Evidence

The exercise reports five scheduled events, five accepted event boundaries,
five history resets, and four post-event startup steps. The last event is also
the simulation stop time, so no step follows it.

## Theory and Practical Outcomes

The theoretical requirement is piecewise integration: each smooth interval is
integrated under one circuit configuration, and the step ends before the
configuration changes. The practical outcome is a reproducible event boundary
that supports switching schedules, dead-time experiments, and controller
timing studies without hiding a transition inside a longer step.

## Conclusion

The experiment met every event-alignment expectation. It demonstrates that
scheduled changes are treated as integration boundaries and that invalid
multistep history is discarded immediately after each change.

## Claim Boundary

Exact schedule alignment proves timing consistency for the declared ideal
switch model. It does not model contact bounce, semiconductor transition
dynamics, propagation delay, thermal behavior, or uncertain hardware timing.
