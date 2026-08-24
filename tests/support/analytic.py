from __future__ import annotations

import math


def rc_voltage(
    time: float,
    *,
    resistance: float,
    capacitance: float,
    source_voltage: float,
    initial_voltage: float,
) -> float:
    time_constant = resistance * capacitance
    return source_voltage + (initial_voltage - source_voltage) * math.exp(-time / time_constant)


def rl_current(
    time: float,
    *,
    resistance: float,
    inductance: float,
    source_voltage: float,
    initial_current: float,
) -> float:
    steady_current = source_voltage / resistance
    time_constant = inductance / resistance
    return steady_current + (initial_current - steady_current) * math.exp(-time / time_constant)


def parallel_rlc_state(
    time: float,
    *,
    resistance: float,
    capacitance: float,
    inductance: float,
    initial_voltage: float,
    initial_current: float,
) -> tuple[float, float]:
    conductance = 0.0 if math.isinf(resistance) else 1.0 / resistance
    alpha = conductance / (2.0 * capacitance)
    omega_zero = math.sqrt(1.0 / (inductance * capacitance))
    initial_derivative = -(initial_current + conductance * initial_voltage) / capacitance
    discriminant = alpha * alpha - omega_zero * omega_zero

    if abs(discriminant) <= 1.0e-14 * omega_zero * omega_zero:
        coefficient = initial_derivative + alpha * initial_voltage
        exponential = math.exp(-alpha * time)
        voltage = (initial_voltage + coefficient * time) * exponential
        derivative = (coefficient - alpha * (initial_voltage + coefficient * time)) * exponential
    elif discriminant < 0.0:
        omega_damped = math.sqrt(-discriminant)
        coefficient = (initial_derivative + alpha * initial_voltage) / omega_damped
        cosine = math.cos(omega_damped * time)
        sine = math.sin(omega_damped * time)
        exponential = math.exp(-alpha * time)
        voltage = exponential * (initial_voltage * cosine + coefficient * sine)
        derivative = exponential * (
            (-alpha * initial_voltage + coefficient * omega_damped) * cosine
            + (-alpha * coefficient - initial_voltage * omega_damped) * sine
        )
    else:
        root = math.sqrt(discriminant)
        first_root = -alpha + root
        second_root = -alpha - root
        first_coefficient = (initial_derivative - second_root * initial_voltage) / (
            first_root - second_root
        )
        second_coefficient = initial_voltage - first_coefficient
        first_term = first_coefficient * math.exp(first_root * time)
        second_term = second_coefficient * math.exp(second_root * time)
        voltage = first_term + second_term
        derivative = first_root * first_term + second_root * second_term

    current = -capacitance * derivative - conductance * voltage
    return voltage, current


def driven_rc_voltage(
    time: float,
    *,
    resistance: float,
    capacitance: float,
    amplitude: float,
    frequency: float,
    initial_voltage: float,
) -> float:
    time_constant = resistance * capacitance
    angular_frequency = 2.0 * math.pi * frequency
    phase_lag = math.atan(angular_frequency * time_constant)
    steady_amplitude = amplitude / math.sqrt(1.0 + (angular_frequency * time_constant) ** 2)

    def steady_state(at_time: float) -> float:
        return steady_amplitude * math.sin(angular_frequency * at_time - phase_lag)

    transient_amplitude = initial_voltage - steady_state(0.0)
    return steady_state(time) + transient_amplitude * math.exp(-time / time_constant)
