# Tutorial 1: Modified Nodal Analysis and State Ownership

Modified nodal analysis (`MNA`) is a way to write circuit equations using node
voltages plus the extra branch currents required by elements such as ideal
voltage sources. In plain words, it turns a circuit drawing into a system of
equations that a computer can solve. This tutorial shows why the values that
store energy are not always the same thing as the complete set of unknowns in
those equations.

![Modified nodal analysis state ownership](html/assets/tutorial-01-mna.svg "Modified nodal analysis separates dynamic state, algebraic projection, and derivative evaluation.")

## What You Will Learn

You will distinguish four ideas:

1. a **dynamic state**, meaning a value that carries stored energy from one
   time to the next;
2. an **algebraic unknown**, meaning a value solved from the circuit constraints
   at the current time;
3. a **projection**, meaning the solve that makes a proposed state consistent
   with all circuit equations; and
4. a **derivative**, meaning the instantaneous rate at which the dynamic state
   is changing.

The exercise uses a resistor-capacitor (`RC`) circuit. A resistor-capacitor
circuit contains a resistor, which dissipates energy, and a capacitor, which
stores electric-field energy.

## Run the Exercise

```bash
PYTHONPATH=src python lab/support/verify.py --exercise 01-mna
```

`PYTHONPATH=src` tells Python to import the BAB-CS package from the repository's
`src` directory. The command runs a deterministic verifier rather than asking
you to judge a plot by eye.

## Expected Results

The circuit has one capacitor, so theory predicts one dynamic state:
`v(C1)`. Modified nodal analysis should require additional algebraic unknowns
for node voltages and ideal-source branch current. With a 1-volt source, a
1000-ohm resistor, a 1-microfarad capacitor, and zero initial capacitor voltage,
the expected initial derivative is:

```text
(1 volt - 0 volts) / (1000 ohms × 0.000001 farads) = 1000 volts per second
```

The algebraic residual is expected to be zero or below the declared numerical
tolerance if projection solves the initial circuit constraints correctly.

## Observed Data

The exercise was run on August 27, 2026. It returned the following values:

| Measurement | Observed value |
| --- | --- |
| Dynamic-state name | `v(C1)` |
| Ordered circuit nodes | `vin`, `out` |
| Dynamic-state dimension | `1` |
| Algebraic dimension | `4` |
| Initial capacitor-voltage derivative | `1000.0000000000001` volts per second |
| Algebraic residual | `0.0` |
| Dynamic state differs from the node-voltage vector | `true` |

The one dynamic coordinate stores the capacitor's memory. The four algebraic
coordinates reconstruct the two node voltages and the additional branch
currents needed by the modified nodal analysis equations. The zero residual
means the algebraic equations were satisfied to the reported numerical
precision at the initial evaluation. The derivative means the capacitor voltage
initially rises by about 1000 volts per second; it does not mean the voltage
will continue rising at that constant rate.

## Expected Versus Actual Results

The state dimensions, state name, node order, and zero residual matched the
expectation exactly. The computed derivative was
`1000.0000000000001` rather than the decimal value `1000`. The difference is
approximately `1.1e-13` volts per second and is caused by binary
floating-point representation, not by a physically meaningful circuit error.
No discrepancy requiring a model or solver correction was observed.

## Follow the Equation Ownership

The declared capacitor voltage, `v(C1)`, is the only dynamic state in this
example. It must be retained because the capacitor's next current depends on
how its voltage changes over time.

The node voltages and ideal-source branch current are algebraic unknowns. They
are reconstructed at each evaluation so that Kirchhoff current law (`KCL`) is
satisfied. Kirchhoff current law means that current entering a node must balance
current leaving that node.

The algebraic projection therefore answers a different question from the time
integrator. The time integrator asks, “What state should be proposed next?” The
projection asks, “If that state were used, can the complete circuit equations
be satisfied?” BAB-CS keeps these responsibilities separate so that a candidate
method cannot approve an inconsistent state merely because its time-update
formula returned a number.

## Read the Evidence

The verifier reports:

- the dynamic-state names;
- the ordered circuit nodes;
- the dynamic and algebraic dimensions;
- the initial state derivative; and
- the algebraic residual.

A residual is the equation mismatch left after a solve. A small algebraic
residual proves that the circuit constraints were solved closely for that
evaluation. It does **not** prove that the transient trajectory is accurate over
the complete time interval.

## Theory and Practical Outcomes

The theoretical outcome is that stored-energy coordinates and instantaneous
circuit constraints have distinct ownership. Time integration advances the
capacitor voltage, while projection reconstructs a constraint-consistent
algebraic solution. This separation is necessary for circuit equations that
combine derivatives with simultaneous algebraic constraints.

State ownership matters when a circuit contains several capacitors, inductors,
ideal sources, controlled switches, or nonlinear devices. Confusing a node
voltage with a canonical state coordinate can reorder data, compare the wrong
quantities, or hide an invalid external mapping. The 20-case ngspice work in
Tutorial 10 uses the same rule: capacitor voltages come before inductor currents
in the exported BAB-CS state vector.

## Conclusion

The experiment supports the expected modified-nodal-analysis ownership model.
It provides a practical baseline for interpreting every later tutorial because
external mappings, error measurements, and authority comparisons are valid only
when they compare the same canonical state coordinates.

## Claim Boundary

This exercise proves formulation consistency for one small RC model. It does
not establish support for every differential-algebraic equation, every circuit
topology, or every physical parasitic effect.
