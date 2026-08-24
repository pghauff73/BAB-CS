from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace

from .linalg import SingularMatrixError, finite_difference_jacobian, norm_inf, solve_linear
from .waveforms import Constant, Waveform


GROUND = "0"


class CircuitSolveError(RuntimeError):
    pass


def normalize_node(node: str) -> str:
    node_name = str(node).strip()
    return GROUND if node_name.lower() in {"0", "gnd", "ground"} else node_name


@dataclass
class Resistor:
    name: str
    positive: str
    negative: str
    resistance: float


@dataclass
class Capacitor:
    name: str
    positive: str
    negative: str
    capacitance: float
    initial_voltage: float = 0.0


@dataclass
class Inductor:
    name: str
    positive: str
    negative: str
    inductance: float
    initial_current: float = 0.0


@dataclass
class CurrentSource:
    name: str
    positive: str
    negative: str
    waveform: Waveform


@dataclass
class VoltageSource:
    name: str
    positive: str
    negative: str
    waveform: Waveform


@dataclass
class Diode:
    name: str
    positive: str
    negative: str
    saturation_current: float = 1.0e-12
    thermal_voltage: float = 0.02585


@dataclass
class Switch:
    name: str
    positive: str
    negative: str
    control: Waveform
    threshold: float = 0.5
    on_resistance: float = 1.0e-3
    off_resistance: float = 1.0e9


Element = Resistor | Capacitor | Inductor | CurrentSource | VoltageSource | Diode | Switch


@dataclass(frozen=True)
class AlgebraicSolution:
    unknowns: tuple[float, ...]
    node_voltages: dict[str, float]
    branch_currents: dict[str, float]
    residual_norm: float
    iterations: int


@dataclass(frozen=True)
class CircuitEvaluation:
    time: float
    dynamic_state: tuple[float, ...]
    derivative: tuple[float, ...]
    algebraic: AlgebraicSolution
    stored_energy: float
    source_power: float
    dissipated_power: float


class Circuit:
    def __init__(self, elements: Iterable[Element] = ()) -> None:
        self.elements = [self._normalize_element(element) for element in elements]
        self._validate()

        self.capacitors = [element for element in self.elements if isinstance(element, Capacitor)]
        self.inductors = [element for element in self.elements if isinstance(element, Inductor)]
        self.voltage_sources = [element for element in self.elements if isinstance(element, VoltageSource)]
        self.current_sources = [element for element in self.elements if isinstance(element, CurrentSource)]
        self.resistors = [element for element in self.elements if isinstance(element, Resistor)]
        self.diodes = [element for element in self.elements if isinstance(element, Diode)]
        self.switches = [element for element in self.elements if isinstance(element, Switch)]

        node_names: list[str] = []
        for element in self.elements:
            for node in (element.positive, element.negative):
                if node != GROUND and node not in node_names:
                    node_names.append(node)
        self.nodes = tuple(node_names)
        self.node_index = {node: index for index, node in enumerate(self.nodes)}

        self.constraint_branches = [
            element for element in self.elements if isinstance(element, (VoltageSource, Capacitor))
        ]
        self.branch_index = {
            element.name: len(self.nodes) + index for index, element in enumerate(self.constraint_branches)
        }
        self.capacitor_state_index = {
            element.name: index for index, element in enumerate(self.capacitors)
        }
        self.inductor_state_index = {
            element.name: len(self.capacitors) + index for index, element in enumerate(self.inductors)
        }

    @staticmethod
    def _normalize_element(element: Element) -> Element:
        return replace(
            element,
            positive=normalize_node(element.positive),
            negative=normalize_node(element.negative),
        )

    def _validate(self) -> None:
        names = [element.name for element in self.elements]
        if len(names) != len(set(names)):
            raise ValueError("element names must be unique")
        for element in self.elements:
            if not element.name:
                raise ValueError("element names must not be empty")
            if element.positive == element.negative:
                raise ValueError(f"{element.name}: element terminals must differ")
            if isinstance(element, Resistor) and element.resistance <= 0.0:
                raise ValueError(f"{element.name}: resistance must be positive")
            if isinstance(element, Capacitor) and element.capacitance <= 0.0:
                raise ValueError(f"{element.name}: capacitance must be positive")
            if isinstance(element, Inductor) and element.inductance <= 0.0:
                raise ValueError(f"{element.name}: inductance must be positive")
            if isinstance(element, Diode):
                if element.saturation_current <= 0.0 or element.thermal_voltage <= 0.0:
                    raise ValueError(f"{element.name}: diode parameters must be positive")
            if isinstance(element, Switch):
                if element.on_resistance <= 0.0 or element.off_resistance <= 0.0:
                    raise ValueError(f"{element.name}: switch resistances must be positive")

    @property
    def dynamic_size(self) -> int:
        return len(self.capacitors) + len(self.inductors)

    @property
    def algebraic_size(self) -> int:
        return len(self.nodes) + len(self.constraint_branches)

    @property
    def dynamic_names(self) -> tuple[str, ...]:
        capacitor_names = tuple(f"v({element.name})" for element in self.capacitors)
        inductor_names = tuple(f"i({element.name})" for element in self.inductors)
        return capacitor_names + inductor_names

    def initial_dynamic_state(self) -> tuple[float, ...]:
        return tuple(element.initial_voltage for element in self.capacitors) + tuple(
            element.initial_current for element in self.inductors
        )

    def breakpoints(self, start: float, end: float) -> list[float]:
        points: set[float] = set()
        for element in (*self.voltage_sources, *self.current_sources):
            points.update(element.waveform.breakpoints(start, end))
        for element in self.switches:
            points.update(element.control.breakpoints(start, end))
        return sorted(points)

    def evaluate(
        self,
        time: float,
        dynamic_state: Sequence[float],
        algebraic_guess: Sequence[float] | None = None,
        *,
        newton_absolute_tolerance: float = 1.0e-11,
        newton_relative_tolerance: float = 1.0e-9,
        newton_max_iterations: int = 30,
    ) -> CircuitEvaluation:
        state = tuple(float(value) for value in dynamic_state)
        if len(state) != self.dynamic_size:
            raise ValueError(f"expected {self.dynamic_size} dynamic values, received {len(state)}")
        algebraic = self.solve_algebraic(
            time,
            state,
            algebraic_guess,
            absolute_tolerance=newton_absolute_tolerance,
            relative_tolerance=newton_relative_tolerance,
            max_iterations=newton_max_iterations,
        )

        derivative: list[float] = []
        for capacitor in self.capacitors:
            derivative.append(algebraic.branch_currents[capacitor.name] / capacitor.capacitance)
        for inductor in self.inductors:
            voltage = self.branch_voltage(algebraic, inductor.positive, inductor.negative)
            derivative.append(voltage / inductor.inductance)

        stored_energy = 0.0
        for capacitor in self.capacitors:
            voltage = state[self.capacitor_state_index[capacitor.name]]
            stored_energy += 0.5 * capacitor.capacitance * voltage * voltage
        for inductor in self.inductors:
            current = state[self.inductor_state_index[inductor.name]]
            stored_energy += 0.5 * inductor.inductance * current * current

        source_power = 0.0
        for source in self.voltage_sources:
            voltage = self.branch_voltage(algebraic, source.positive, source.negative)
            current = algebraic.branch_currents[source.name]
            source_power -= voltage * current
        for source in self.current_sources:
            voltage = self.branch_voltage(algebraic, source.positive, source.negative)
            source_power -= voltage * source.waveform.value(time)

        dissipated_power = 0.0
        for resistor in self.resistors:
            voltage = self.branch_voltage(algebraic, resistor.positive, resistor.negative)
            dissipated_power += voltage * voltage / resistor.resistance
        for switch in self.switches:
            voltage = self.branch_voltage(algebraic, switch.positive, switch.negative)
            resistance = (
                switch.on_resistance
                if switch.control.value(time) >= switch.threshold
                else switch.off_resistance
            )
            dissipated_power += voltage * voltage / resistance
        for diode in self.diodes:
            voltage = self.branch_voltage(algebraic, diode.positive, diode.negative)
            current, _ = self._diode_current_and_conductance(diode, voltage)
            dissipated_power += voltage * current

        return CircuitEvaluation(
            time=time,
            dynamic_state=state,
            derivative=tuple(derivative),
            algebraic=algebraic,
            stored_energy=stored_energy,
            source_power=source_power,
            dissipated_power=dissipated_power,
        )

    def solve_algebraic(
        self,
        time: float,
        dynamic_state: Sequence[float],
        initial_guess: Sequence[float] | None = None,
        *,
        absolute_tolerance: float = 1.0e-11,
        relative_tolerance: float = 1.0e-9,
        max_iterations: int = 30,
    ) -> AlgebraicSolution:
        if initial_guess is None:
            unknowns = [0.0] * self.algebraic_size
            for branch in self.constraint_branches:
                if isinstance(branch, VoltageSource):
                    target_voltage = branch.waveform.value(time)
                else:
                    target_voltage = dynamic_state[self.capacitor_state_index[branch.name]]
                if branch.negative == GROUND and branch.positive != GROUND:
                    unknowns[self.node_index[branch.positive]] = target_voltage
                elif branch.positive == GROUND and branch.negative != GROUND:
                    unknowns[self.node_index[branch.negative]] = -target_voltage
        else:
            unknowns = [float(value) for value in initial_guess]
            if len(unknowns) != self.algebraic_size:
                raise ValueError("algebraic initial guess has the wrong size")

        if self.algebraic_size == 0:
            return AlgebraicSolution((), {GROUND: 0.0}, {}, 0.0, 0)

        for iteration in range(max_iterations + 1):
            residual, jacobian = self._algebraic_residual_and_jacobian(time, dynamic_state, unknowns)
            residual_norm = norm_inf(residual)
            tolerance = absolute_tolerance + relative_tolerance * max(norm_inf(unknowns), 1.0)
            if residual_norm <= tolerance:
                return self._make_algebraic_solution(unknowns, residual_norm, iteration)
            if iteration == max_iterations:
                break
            try:
                delta = solve_linear(jacobian, [-value for value in residual])
            except SingularMatrixError as error:
                raise CircuitSolveError(f"algebraic solve failed: {error}") from error

            accepted = False
            damping = 1.0
            for _ in range(14):
                trial = [value + damping * update for value, update in zip(unknowns, delta, strict=True)]
                trial_residual, _ = self._algebraic_residual_and_jacobian(time, dynamic_state, trial)
                if norm_inf(trial_residual) < residual_norm:
                    unknowns = trial
                    accepted = True
                    break
                damping *= 0.5
            if not accepted:
                raise CircuitSolveError(
                    f"algebraic Newton line search failed at t={time:.17g}, residual={residual_norm:.6g}"
                )

        raise CircuitSolveError(
            f"algebraic Newton solve did not converge at t={time:.17g}, residual={residual_norm:.6g}"
        )

    def _make_algebraic_solution(
        self,
        unknowns: Sequence[float],
        residual_norm: float,
        iterations: int,
    ) -> AlgebraicSolution:
        node_voltages = {GROUND: 0.0}
        node_voltages.update({node: unknowns[index] for node, index in self.node_index.items()})
        branch_currents = {
            element.name: unknowns[self.branch_index[element.name]] for element in self.constraint_branches
        }
        return AlgebraicSolution(
            unknowns=tuple(unknowns),
            node_voltages=node_voltages,
            branch_currents=branch_currents,
            residual_norm=residual_norm,
            iterations=iterations,
        )

    def _algebraic_residual_and_jacobian(
        self,
        time: float,
        dynamic_state: Sequence[float],
        unknowns: Sequence[float],
    ) -> tuple[list[float], list[list[float]]]:
        size = self.algebraic_size
        residual = [0.0] * size
        jacobian = [[0.0] * size for _ in range(size)]

        def voltage(node: str) -> float:
            return 0.0 if node == GROUND else unknowns[self.node_index[node]]

        def add_known_current(positive: str, negative: str, current: float) -> None:
            if positive != GROUND:
                residual[self.node_index[positive]] += current
            if negative != GROUND:
                residual[self.node_index[negative]] -= current

        def add_conductance(positive: str, negative: str, current: float, conductance: float) -> None:
            add_known_current(positive, negative, current)
            positive_index = self.node_index.get(positive)
            negative_index = self.node_index.get(negative)
            if positive_index is not None:
                jacobian[positive_index][positive_index] += conductance
                if negative_index is not None:
                    jacobian[positive_index][negative_index] -= conductance
            if negative_index is not None:
                if positive_index is not None:
                    jacobian[negative_index][positive_index] -= conductance
                jacobian[negative_index][negative_index] += conductance

        for resistor in self.resistors:
            branch_voltage = voltage(resistor.positive) - voltage(resistor.negative)
            conductance = 1.0 / resistor.resistance
            add_conductance(resistor.positive, resistor.negative, conductance * branch_voltage, conductance)

        for switch in self.switches:
            resistance = (
                switch.on_resistance
                if switch.control.value(time) >= switch.threshold
                else switch.off_resistance
            )
            branch_voltage = voltage(switch.positive) - voltage(switch.negative)
            conductance = 1.0 / resistance
            add_conductance(switch.positive, switch.negative, conductance * branch_voltage, conductance)

        for diode in self.diodes:
            branch_voltage = voltage(diode.positive) - voltage(diode.negative)
            current, conductance = self._diode_current_and_conductance(diode, branch_voltage)
            add_conductance(diode.positive, diode.negative, current, conductance)

        for source in self.current_sources:
            add_known_current(source.positive, source.negative, source.waveform.value(time))

        for inductor in self.inductors:
            current = dynamic_state[self.inductor_state_index[inductor.name]]
            add_known_current(inductor.positive, inductor.negative, current)

        for branch in self.constraint_branches:
            branch_unknown_index = self.branch_index[branch.name]
            branch_current = unknowns[branch_unknown_index]
            add_known_current(branch.positive, branch.negative, branch_current)
            if branch.positive != GROUND:
                jacobian[self.node_index[branch.positive]][branch_unknown_index] += 1.0
            if branch.negative != GROUND:
                jacobian[self.node_index[branch.negative]][branch_unknown_index] -= 1.0

            if isinstance(branch, VoltageSource):
                target_voltage = branch.waveform.value(time)
            else:
                target_voltage = dynamic_state[self.capacitor_state_index[branch.name]]
            residual[branch_unknown_index] = voltage(branch.positive) - voltage(branch.negative) - target_voltage
            if branch.positive != GROUND:
                jacobian[branch_unknown_index][self.node_index[branch.positive]] += 1.0
            if branch.negative != GROUND:
                jacobian[branch_unknown_index][self.node_index[branch.negative]] -= 1.0

        return residual, jacobian

    @staticmethod
    def _diode_current_and_conductance(diode: Diode, voltage: float) -> tuple[float, float]:
        exponent = voltage / diode.thermal_voltage
        if exponent > 40.0:
            base = math.exp(40.0)
            exponential = base * (1.0 + exponent - 40.0)
            derivative = base
        elif exponent < -40.0:
            exponential = math.exp(-40.0)
            derivative = exponential
        else:
            exponential = math.exp(exponent)
            derivative = exponential
        current = diode.saturation_current * (exponential - 1.0)
        conductance = diode.saturation_current * derivative / diode.thermal_voltage
        return current, conductance

    @staticmethod
    def branch_voltage(solution: AlgebraicSolution, positive: str, negative: str) -> float:
        return solution.node_voltages[positive] - solution.node_voltages[negative]

    def full_residual_norm(
        self,
        evaluation: CircuitEvaluation,
        derivative: Sequence[float] | None = None,
    ) -> float:
        derivative_values = evaluation.derivative if derivative is None else derivative
        dynamic_residuals: list[float] = []
        for capacitor in self.capacitors:
            index = self.capacitor_state_index[capacitor.name]
            current = evaluation.algebraic.branch_currents[capacitor.name]
            dynamic_residuals.append(capacitor.capacitance * derivative_values[index] - current)
        for inductor in self.inductors:
            index = self.inductor_state_index[inductor.name]
            voltage = self.branch_voltage(evaluation.algebraic, inductor.positive, inductor.negative)
            dynamic_residuals.append(inductor.inductance * derivative_values[index] - voltage)
        return max(evaluation.algebraic.residual_norm, norm_inf(dynamic_residuals))

    def differential_jacobian(
        self,
        time: float,
        dynamic_state: Sequence[float],
        algebraic_guess: Sequence[float] | None = None,
    ) -> list[list[float]]:
        base = self.evaluate(time, dynamic_state, algebraic_guess)

        def derivative(candidate: list[float]) -> list[float]:
            return list(self.evaluate(time, candidate, base.algebraic.unknowns).derivative)

        return finite_difference_jacobian(derivative, dynamic_state, base.derivative)


def voltage_source(
    name: str,
    positive: str,
    negative: str,
    value: float,
) -> VoltageSource:
    return VoltageSource(name, positive, negative, Constant(value))


def current_source(
    name: str,
    positive: str,
    negative: str,
    value: float,
) -> CurrentSource:
    return CurrentSource(name, positive, negative, Constant(value))
