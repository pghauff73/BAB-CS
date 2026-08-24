from __future__ import annotations

import math

from babcs import (
    Capacitor,
    Circuit,
    Diode,
    Inductor,
    PiecewiseLinear,
    Pulse,
    Resistor,
    Sine,
    Switch,
    VoltageSource,
)
from babcs.waveforms import Constant


def rc_charge_circuit(
    *,
    resistance: float = 1_000.0,
    capacitance: float = 1.0e-6,
    source_voltage: float = 1.0,
    initial_voltage: float = 0.0,
) -> Circuit:
    return Circuit(
        [
            VoltageSource("V1", "vin", "0", Constant(source_voltage)),
            Resistor("R1", "vin", "out", resistance),
            Capacitor("C1", "out", "0", capacitance, initial_voltage),
        ]
    )


def rl_step_circuit(
    *,
    resistance: float = 10.0,
    inductance: float = 1.0e-3,
    source_voltage: float = 1.0,
    initial_current: float = 0.0,
) -> Circuit:
    return Circuit(
        [
            VoltageSource("V1", "vin", "0", Constant(source_voltage)),
            Resistor("R1", "vin", "out", resistance),
            Inductor("L1", "out", "0", inductance, initial_current),
        ]
    )


def parallel_rlc_circuit(
    *,
    resistance: float = math.inf,
    capacitance: float = 1.0e-6,
    inductance: float = 1.0e-3,
    initial_voltage: float = 1.0,
    initial_current: float = 0.0,
) -> Circuit:
    elements = [
        Capacitor("C1", "tank", "0", capacitance, initial_voltage),
        Inductor("L1", "tank", "0", inductance, initial_current),
    ]
    if math.isfinite(resistance):
        elements.append(Resistor("R1", "tank", "0", resistance))
    return Circuit(elements)


def driven_rc_circuit(
    *,
    resistance: float = 1_000.0,
    capacitance: float = 1.0e-6,
    amplitude: float = 1.0,
    frequency: float = 250.0,
    initial_voltage: float = 0.0,
) -> Circuit:
    return Circuit(
        [
            VoltageSource("V1", "vin", "0", Sine(0.0, amplitude, frequency)),
            Resistor("R1", "vin", "out", resistance),
            Capacitor("C1", "out", "0", capacitance, initial_voltage),
        ]
    )


def pulsed_rc_circuit(
    *,
    rise: float = 0.0,
    fall: float = 0.0,
    delay: float = 5.0e-4,
    width: float = 5.0e-4,
    period: float = 1.5e-3,
) -> Circuit:
    return Circuit(
        [
            VoltageSource(
                "V1",
                "vin",
                "0",
                Pulse(0.0, 1.0, delay, rise, width, fall, period),
            ),
            Resistor("R1", "vin", "out", 1_000.0),
            Capacitor("C1", "out", "0", 1.0e-6),
        ]
    )


def piecewise_linear_rc_circuit() -> Circuit:
    waveform = PiecewiseLinear(
        (
            (0.0, 0.0),
            (2.0e-4, 0.0),
            (2.2e-4, 1.0),
            (2.4e-4, -0.5),
            (4.0e-4, 0.25),
        )
    )
    return Circuit(
        [
            VoltageSource("V1", "vin", "0", waveform),
            Resistor("R1", "vin", "out", 1_000.0),
            Capacitor("C1", "out", "0", 1.0e-6),
        ]
    )


def diode_clip_circuit(*, frequency: float = 1_000.0) -> Circuit:
    return Circuit(
        [
            VoltageSource("V1", "vin", "0", Sine(0.0, 1.0, frequency)),
            Resistor("R1", "vin", "out", 1_000.0),
            Diode("D1", "out", "0"),
            Capacitor("C1", "out", "0", 1.0e-8),
        ]
    )


def diode_recovery_circuit() -> Circuit:
    return Circuit(
        [
            VoltageSource(
                "V1",
                "vin",
                "0",
                Pulse(0.0, 1.0, 1.0e-4, 1.0e-5, 2.0e-4, 1.0e-5, 0.0),
            ),
            Resistor("R1", "vin", "out", 2_000.0),
            Diode("D1", "out", "0"),
            Capacitor("C1", "out", "0", 2.0e-8),
        ]
    )


def switched_rc_circuit(*, period: float = 4.0e-4) -> Circuit:
    return Circuit(
        [
            VoltageSource("V1", "vin", "0", Constant(1.0)),
            Resistor("R1", "vin", "out", 1_000.0),
            Capacitor("C1", "out", "0", 1.0e-6),
            Switch(
                "S1",
                "out",
                "0",
                Pulse(0.0, 1.0, 1.0e-4, 0.0, 1.0e-4, 0.0, period),
                threshold=0.5,
                on_resistance=10.0,
                off_resistance=1.0e9,
            ),
        ]
    )
