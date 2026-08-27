# Tutorial 3: Phase Error Versus Energy Error

Phase error measures whether an oscillation is early or late. Energy error
measures whether the simulated stored electrical energy is too high or too low.
They are related in an oscillator, but they are not interchangeable.

![Phase and energy comparison](html/assets/tutorial-03-phase-energy.svg "Backward Euler and trapezoidal integration show different phase and energy behavior.")

## What You Will Learn

The exercise uses an inductor-capacitor (`LC`) tank. An inductor stores magnetic
energy and a capacitor stores electric-field energy. In an ideal lossless LC
model, energy moves back and forth between them while the total remains
constant.

Two implicit methods are compared:

- **backward Euler**, which uses the state rate at the end of the timestep and
  usually adds strong numerical damping; and
- **trapezoidal integration**, which averages beginning and ending rates and
  often preserves oscillatory energy much better.

Numerical damping means that the method removes simulated energy even when the
declared model contains no resistor.

## Run the Exercise

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 03-phase-versus-energy
```

The verifier runs ten oscillation periods. A period is the time required for
one complete oscillation.

## Expected Results

For a lossless linear inductor-capacitor oscillator, backward Euler is expected
to damp the numerical oscillation because its amplification magnitude is less
than one on a purely oscillatory problem. Trapezoidal integration is expected
to preserve the oscillator's energy much more closely, but its approximate
rotation angle still permits phase error. The expected qualitative result is
therefore strong backward-Euler energy loss, near-roundoff trapezoidal energy
drift, and nonzero phase error for both methods.

## Observed Data

The exercise was run on August 27, 2026 over ten periods.

| Method | Final phase error | Final relative energy error | Relative energy span |
| --- | ---: | ---: | ---: |
| Backward Euler | `0.08248810247463056` radians, or about `4.7262` degrees | `0.9805531365134604` | `0.9805531365134604` |
| Trapezoidal | `0.020658618955850548` radians, or about `1.1837` degrees | `6.352747104407253e-16` | `4.658681209898652e-15` |

A relative error of `0.980553` means that backward Euler lost about 98.1
percent of the ideal stored energy by the final sample. Trapezoidal integration
kept energy variation at the scale of floating-point roundoff, but its phase
still shifted by about 1.18 degrees. Floating-point roundoff is the small
arithmetic error caused by storing real numbers with a finite number of binary
digits. The data therefore demonstrates why phase and energy must remain
separate measurements.

## Expected Versus Actual Results

The actual behavior matches the theoretical expectation. Backward Euler lost
about 98.1 percent of the ideal stored energy and accumulated about 4.73 degrees
of phase error. Trapezoidal integration retained energy to floating-point
roundoff while accumulating about 1.18 degrees of phase error.

The important difference from a naive expectation is that near-perfect energy
retention did not imply perfect timing. Trapezoidal integration maps the ideal
continuous rotation to a discrete rotation with nearly unit magnitude but a
slightly different angle. That angle error accumulates over repeated periods
even while energy remains nearly constant.

## Read the Two Measurements Separately

The final phase error is calculated from the simulated capacitor voltage and
inductor current, then compared with the known oscillator angle. The relative
energy span is the difference between the largest and smallest stored-energy
values divided by the initial energy.

Backward Euler strongly reduces energy in this exercise. Trapezoidal
integration keeps the energy span near floating-point roundoff, but its phase
error remains nonzero. Floating-point roundoff is the tiny arithmetic error
caused by representing real numbers with a finite number of binary digits.

This distinction matters:

- small energy drift does not prove small timing error;
- strong damping may make a trace look calm while moving it away from the
  declared lossless model; and
- a phase-accurate method could still violate an energy requirement.

## Theory and Practical Outcomes

The theoretical outcome separates amplification magnitude from phase angle.
One controls numerical energy behavior; the other controls oscillation timing.

Separate phase and energy reporting is important for resonant converters,
filters, oscillators, motor-current models, and grid-frequency studies. A
control design may depend on zero-crossing time even when stored energy looks
reasonable. A protection study may depend on peak energy even when phase looks
reasonable.

BAB-CS therefore retains phase and energy as separate evidence channels. It
does not collapse them into one score that hides which engineering property
changed.

## Conclusion

The experiment confirms that phase and energy are independent engineering
requirements. Trapezoidal integration is preferable for this ideal energy
study, but its remaining phase error must still be measured when timing,
zero-crossings, or synchronization matter.

## Claim Boundary

This exercise uses an ideal lossless LC model. Real inductors and capacitors
have resistance, saturation, dielectric loss, temperature effects, and
frequency-dependent behavior that are outside this tutorial model.
