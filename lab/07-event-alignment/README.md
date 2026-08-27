# Exercise 7: Event Alignment

## Objective

Show that a scheduled switch transition is reached exactly, recorded as an
event boundary, and followed by a startup step that does not reuse stale
multistep history.

## Run

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 07-event-alignment
```

## Questions

1. Why is stepping past a switch time and interpolating backward unsafe?
2. Why must Adams-Bashforth history restart after a topology change?
3. Why does exact event timing not prove the switch model is physically complete?

## Evidence

The verifier compares scheduled and accepted event times to a one-femtosecond
tolerance, checks event history-reset reasons, and counts startup steps after
events.
