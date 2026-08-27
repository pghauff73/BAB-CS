"""Bounded-Authority-Based-Circuit-Simulation (`babcs`)."""

from .bounded import BABCSConfig, BoundedAdamsBashforthIntegrator, BoundedIntegrator
from .candidates import CANDIDATE_METHODS
from ._project import VERSION as __version__
from .model import (
    Capacitor,
    Circuit,
    CurrentSource,
    Diode,
    Inductor,
    Resistor,
    Switch,
    VoltageSource,
)
from .rootfinding import (
    DerivativeIntervalFunction,
    RootFindingError,
    RootIteration,
    RootResult,
    RootSettings,
    bisection,
    bounded_newton_raphson,
    interval_newton,
    newton_raphson,
    ridders,
    secant,
)
from .simulator import SimulationResult, Simulator
from .waveforms import Constant, PiecewiseLinear, Pulse, Sine

__all__ = [
    "BABCSConfig",
    "BoundedAdamsBashforthIntegrator",
    "BoundedIntegrator",
    "CANDIDATE_METHODS",
    "Capacitor",
    "Circuit",
    "Constant",
    "CurrentSource",
    "Diode",
    "DerivativeIntervalFunction",
    "Inductor",
    "PiecewiseLinear",
    "Pulse",
    "Resistor",
    "RootFindingError",
    "RootIteration",
    "RootResult",
    "RootSettings",
    "SimulationResult",
    "Simulator",
    "Sine",
    "Switch",
    "VoltageSource",
    "__version__",
    "bisection",
    "bounded_newton_raphson",
    "interval_newton",
    "newton_raphson",
    "ridders",
    "secant",
]
