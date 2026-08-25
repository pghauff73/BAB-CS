from __future__ import annotations

import math
import threading
from collections import OrderedDict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from functools import lru_cache
from typing import Any
from weakref import WeakMethod

from .linalg import (
    _numpy_component,
    _scipy_sparse_components,
    _factor_and_solve_klu_sparse_values_multiple_array,
    LinearBackendUnavailableError,
    LinearMatrix,
    ReusableLinearFactorization,
    SCIPY_SPARSE_MAXIMUM_DENSITY,
    SCIPY_SPARSE_REUSABLE_MINIMUM_SIZE,
    SCIPY_SPARSE_SINGLE_SOLVE_MINIMUM_SIZE,
    SparseMatrix,
    SingularMatrixError,
    factor_linear,
    finite_difference_jacobian,
    matrix_inf_norm,
    norm_inf,
    klu_sparse_available,
    scipy_sparse_available,
    sparse_linear_available,
    solve_factored,
    solve_factored_multiple_array,
    solve_linear,
    solve_linear_multiple,
    validate_linear_backend,
)
from .waveforms import (
    Constant,
    Waveform,
    _breakpoint_schedule_key,
    _waveform_value_key,
)


GROUND = "0"
MAXIMUM_LINEAR_CACHE_ENTRIES = 128
REUSABLE_ALGEBRAIC_INPUT_MINIMUM_SIZE = 64
KLU_NATIVE_SENSITIVITY_MINIMUM_ALGEBRAIC_SIZE = 128
KLU_NATIVE_SENSITIVITY_MINIMUM_RIGHT_HAND_SIDES = 32
COMPILED_SPARSE_ALGEBRAIC_MINIMUM_CALLS = 256
DEDUPLICATED_SWITCH_CONTROL_MINIMUM_COUNT = 32
MAXIMUM_COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES = 128
_COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES: OrderedDict[
    tuple[object, ...], Any
] = OrderedDict()
_COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES_LOCK = threading.Lock()


class CircuitSolveError(RuntimeError):
    pass


def _within_ulp_time_window(
    source_time: float,
    target_time: float,
    maximum_age: float,
) -> bool:
    time_delta = target_time - source_time
    if time_delta < 0.0 or maximum_age < 0.0:
        return False
    if maximum_age == 0.0:
        return time_delta == 0.0
    scale = max(abs(source_time), abs(target_time), maximum_age)
    tolerance = 8.0 * math.ulp(scale)
    return time_delta <= maximum_age + tolerance


@lru_cache(maxsize=128)
def _compile_sparse_algebraic_kernel(source: str) -> Any:
    namespace = {
        "exp": math.exp,
        "exp40": math.exp(40.0),
        "exp_neg40": math.exp(-40.0),
    }
    exec(compile(source, "<babcs-sparse-algebraic>", "exec"), namespace)
    return namespace["kernel"]


@lru_cache(maxsize=128)
def _compile_sparse_algebraic_jacobian_kernel(source: str) -> Any:
    namespace = {
        "exp": math.exp,
        "exp40": math.exp(40.0),
        "exp_neg40": math.exp(-40.0),
    }
    exec(compile(source, "<babcs-sparse-algebraic-jacobian>", "exec"), namespace)
    return namespace["kernel"]


def _lookup_compiled_sparse_algebraic_topology(
    topology: tuple[object, ...],
) -> Any | None:
    with _COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES_LOCK:
        kernel = _COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES.pop(topology, None)
        if kernel is not None:
            _COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES[topology] = kernel
        return kernel


def _store_compiled_sparse_algebraic_topology(
    topology: tuple[object, ...],
    kernel: Any,
) -> None:
    with _COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES_LOCK:
        _COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES.pop(topology, None)
        _COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES[topology] = kernel
        while (
            len(_COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES)
            > MAXIMUM_COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES
        ):
            _COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES.popitem(last=False)


def _clear_compiled_sparse_algebraic_topologies() -> None:
    with _COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES_LOCK:
        _COMPILED_SPARSE_ALGEBRAIC_TOPOLOGIES.clear()


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

    def __setattr__(self, name: str, value: object) -> None:
        object.__setattr__(self, name, value)
        if name == "control":
            callback = getattr(self, "_control_change_callback", None)
            if callback is not None:
                refresh = callback()
                if refresh is not None:
                    refresh()


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
    dynamic_state_norm: float
    derivative: tuple[float, ...]
    algebraic: AlgebraicSolution
    stored_energy: float
    source_power: float
    dissipated_power: float
    _algebraic_inputs: _AlgebraicInputs | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    _input_owner: Circuit | None = field(default=None, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class SparseImplicitUpdate:
    algebraic_update: tuple[float, ...]
    dynamic_update: tuple[float, ...]
    requires_contraction: bool = False


@dataclass(frozen=True, slots=True)
class _JacobianStamp:
    row: int
    column: int
    sparse_index: int
    multiplier: float


@dataclass(frozen=True, slots=True)
class _TerminalStamp:
    positive_index: int | None
    negative_index: int | None
    jacobian_entries: tuple[_JacobianStamp, ...] = ()


@dataclass(frozen=True, slots=True)
class _ConstraintStamp:
    terminal: _TerminalStamp
    branch_index: int


@dataclass(frozen=True, slots=True)
class _ImplicitBlockStamp:
    sparse_index: int
    multiplier: float


@dataclass(frozen=True, slots=True)
class _AlgebraicInputs:
    current_source_values: tuple[float, ...]
    switch_resistances: tuple[float, ...]
    constraint_targets: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class _SwitchControlSamplingPlan:
    waveforms: tuple[Waveform, ...]
    value_indices: tuple[int, ...]
    deduplicates: bool


_DIRECT_SWITCH_CONTROL_SAMPLING_PLAN = _SwitchControlSamplingPlan((), (), False)


@dataclass(frozen=True, slots=True)
class _AlgebraicProjection:
    unknowns: tuple[float, ...]
    inputs: _AlgebraicInputs
    differential_jacobian_norm: float


@dataclass(frozen=True, slots=True)
class _NativeDifferentialSensitivity:
    factorization: ReusableLinearFactorization
    sensitivities: Any
    differential_jacobian: Any
    differential_jacobian_norm: float
    numpy: Any


class Circuit:
    def __init__(
        self,
        elements: Iterable[Element] = (),
        *,
        linear_backend: str = "dense",
    ) -> None:
        self.linear_backend = validate_linear_backend(linear_backend)
        if self.linear_backend == "scipy" and not scipy_sparse_available():
            raise LinearBackendUnavailableError(
                "the scipy linear backend requires the optional scipy dependency"
            )
        if self.linear_backend == "klu" and not klu_sparse_available():
            raise LinearBackendUnavailableError(
                "the KLU linear backend requires NumPy and a compatible "
                "SuiteSparse KLU 2 library"
            )
        self.elements = [self._normalize_element(element) for element in elements]
        self._validate()

        self.capacitors = [element for element in self.elements if isinstance(element, Capacitor)]
        self.inductors = [element for element in self.elements if isinstance(element, Inductor)]
        self.voltage_sources = [element for element in self.elements if isinstance(element, VoltageSource)]
        self.current_sources = [element for element in self.elements if isinstance(element, CurrentSource)]
        self.resistors = [element for element in self.elements if isinstance(element, Resistor)]
        self.diodes = [element for element in self.elements if isinstance(element, Diode)]
        self.switches = [element for element in self.elements if isinstance(element, Switch)]
        self._dynamic_size = len(self.capacitors) + len(self.inductors)

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
        self._algebraic_size = len(self.nodes) + len(self.constraint_branches)
        self.capacitor_state_index = {
            element.name: index for index, element in enumerate(self.capacitors)
        }
        self.inductor_state_index = {
            element.name: len(self.capacitors) + index for index, element in enumerate(self.inductors)
        }
        self._voltage_constraint_targets = tuple(
            (target_index, branch)
            for target_index, branch in enumerate(self.constraint_branches)
            if isinstance(branch, VoltageSource)
        )
        self._capacitor_constraint_targets = tuple(
            (target_index, self.capacitor_state_index[branch.name])
            for target_index, branch in enumerate(self.constraint_branches)
            if isinstance(branch, Capacitor)
        )
        (
            self._algebraic_sparse_row_indices,
            self._algebraic_sparse_column_pointers,
            self._algebraic_sparse_position_index,
        ) = self._build_algebraic_sparse_pattern()
        self._algebraic_sparse_template = SparseMatrix(
            self.algebraic_size,
            (0.0,) * len(self._algebraic_sparse_row_indices),
            self._algebraic_sparse_row_indices,
            self._algebraic_sparse_column_pointers,
        )
        self._resistor_stamps = tuple(
            self._make_conductance_stamp(element) for element in self.resistors
        )
        self._switch_stamps = tuple(
            self._make_conductance_stamp(element) for element in self.switches
        )
        self._diode_stamps = tuple(
            self._make_conductance_stamp(element) for element in self.diodes
        )
        self._current_source_stamps = tuple(
            self._make_terminal_stamp(element) for element in self.current_sources
        )
        self._inductor_stamps = tuple(
            self._make_terminal_stamp(element) for element in self.inductors
        )
        self._constraint_stamps = tuple(
            self._make_constraint_stamp(element) for element in self.constraint_branches
        )
        self._differential_sensitivity_right_hand_sides = (
            self._build_differential_sensitivity_right_hand_sides()
        )
        self._capacitor_branch_indices = tuple(
            self.branch_index[capacitor.name] for capacitor in self.capacitors
        )
        self._inductor_positive_sensitivity_columns = tuple(
            column
            for column, inductor in enumerate(self.inductors)
            if inductor.positive != GROUND
        )
        self._inductor_positive_sensitivity_nodes = tuple(
            self.node_index[inductor.positive]
            for inductor in self.inductors
            if inductor.positive != GROUND
        )
        self._inductor_negative_sensitivity_columns = tuple(
            column
            for column, inductor in enumerate(self.inductors)
            if inductor.negative != GROUND
        )
        self._inductor_negative_sensitivity_nodes = tuple(
            self.node_index[inductor.negative]
            for inductor in self.inductors
            if inductor.negative != GROUND
        )
        self._native_differential_sensitivity_right_hand_sides: Any | None = None
        self._native_differential_scale_values: (
            tuple[tuple[float, ...], tuple[float, ...]] | None
        ) = None
        self._native_capacitances: Any | None = None
        self._native_inductances: Any | None = None
        self._latest_native_differential_sensitivity_evaluation: (
            CircuitEvaluation | None
        ) = None
        self._latest_native_differential_sensitivity: (
            _NativeDifferentialSensitivity | None
        ) = None
        (
            self._implicit_block_sparse_template,
            self._implicit_block_algebraic_positions,
            self._implicit_block_derivative_stamps,
            self._implicit_block_diagonal_positions,
        ) = self._build_implicit_block_sparse_structure()
        self._linear_differential_jacobian_cache: dict[
            tuple[tuple[float, ...], ...],
            tuple[tuple[float, ...], ...],
        ] = {}
        self._linear_algebraic_factorization_cache: dict[
            tuple[tuple[float, ...], ...],
            ReusableLinearFactorization,
        ] = {}
        self._linear_implicit_factorization_cache: dict[
            tuple[object, ...],
            ReusableLinearFactorization,
        ] = {}
        self._last_algebraic_unknowns: tuple[float, ...] | None = None
        self._last_algebraic_unknown_norm = 0.0
        self._last_assembled_unknowns: Sequence[float] | None = None
        self._last_assembled_diode_currents: tuple[float, ...] = ()
        self._last_algebraic_diode_currents: tuple[float, ...] | None = None
        self._sparse_algebraic_backend: str | None = None
        self._sparse_algebraic_enabled: bool | None = None
        self._compiled_algebraic_residual_kernel: Any | None = None
        self._compiled_sparse_algebraic_kernel: Any | None = None
        self._compiled_sparse_algebraic_jacobian_kernel: Any | None = None
        self._compiled_sparse_algebraic_topology: tuple[object, ...] | None = None
        self._compiled_sparse_algebraic_calls = 0
        self._switch_control_sampling_plan = _DIRECT_SWITCH_CONTROL_SAMPLING_PLAN
        if (
            type(self) is Circuit
            and len(self.switches) >= DEDUPLICATED_SWITCH_CONTROL_MINIMUM_COUNT
        ):
            for switch in self.switches:
                object.__setattr__(
                    switch,
                    "_control_change_callback",
                    WeakMethod(self._refresh_switch_control_sampling_plan),
                )
            self._refresh_switch_control_sampling_plan()
        self._last_nonlinear_algebraic_factorization: (
            ReusableLinearFactorization | None
        ) = None
        if type(self) is Circuit and self._uses_reusable_algebraic_inputs():
            self._compiled_algebraic_residual_kernel = (
                self._build_compiled_algebraic_residual_kernel()
            )

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
            if isinstance(element, Resistor) and (
                not math.isfinite(element.resistance) or element.resistance <= 0.0
            ):
                raise ValueError(f"{element.name}: resistance must be positive and finite")
            if isinstance(element, Capacitor):
                if not math.isfinite(element.capacitance) or element.capacitance <= 0.0:
                    raise ValueError(f"{element.name}: capacitance must be positive and finite")
                if not math.isfinite(element.initial_voltage):
                    raise ValueError(f"{element.name}: initial voltage must be finite")
            if isinstance(element, Inductor):
                if not math.isfinite(element.inductance) or element.inductance <= 0.0:
                    raise ValueError(f"{element.name}: inductance must be positive and finite")
                if not math.isfinite(element.initial_current):
                    raise ValueError(f"{element.name}: initial current must be finite")
            if isinstance(element, Diode):
                if (
                    not math.isfinite(element.saturation_current)
                    or not math.isfinite(element.thermal_voltage)
                    or element.saturation_current <= 0.0
                    or element.thermal_voltage <= 0.0
                ):
                    raise ValueError(f"{element.name}: diode parameters must be positive and finite")
            if isinstance(element, Switch):
                if (
                    not math.isfinite(element.on_resistance)
                    or not math.isfinite(element.off_resistance)
                    or element.on_resistance <= 0.0
                    or element.off_resistance <= 0.0
                ):
                    raise ValueError(f"{element.name}: switch resistances must be positive and finite")
                if not math.isfinite(element.threshold):
                    raise ValueError(f"{element.name}: switch threshold must be finite")

    @property
    def dynamic_size(self) -> int:
        return self._dynamic_size

    @property
    def algebraic_size(self) -> int:
        return self._algebraic_size

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

    def _simulation_breakpoint_waveforms(self) -> tuple[Waveform, ...]:
        waveforms: list[Waveform] = []
        schedules: set[tuple[object, ...]] = set()
        for element in (*self.voltage_sources, *self.current_sources):
            waveform = element.waveform
            schedule = _breakpoint_schedule_key(waveform)
            if schedule is None or schedule not in schedules:
                waveforms.append(waveform)
                if schedule is not None:
                    schedules.add(schedule)
        for element in self.switches:
            waveform = element.control
            schedule = _breakpoint_schedule_key(waveform)
            if schedule is None or schedule not in schedules:
                waveforms.append(waveform)
                if schedule is not None:
                    schedules.add(schedule)
        return tuple(waveforms)

    @staticmethod
    def _breakpoints_from_waveforms(
        waveforms: Sequence[Waveform],
        start: float,
        end: float,
    ) -> list[float]:
        points: set[float] = set()
        for waveform in waveforms:
            points.update(waveform.breakpoints(start, end))
        return sorted(points)

    def _sample_algebraic_inputs(
        self,
        time: float,
        dynamic_state: Sequence[float],
    ) -> _AlgebraicInputs:
        return _AlgebraicInputs(
            current_source_values=tuple(
                source.waveform.value(time) for source in self.current_sources
            ),
            switch_resistances=tuple(
                switch.on_resistance
                if switch.control.value(time) >= switch.threshold
                else switch.off_resistance
                for switch in self.switches
            ),
            constraint_targets=self._constraint_targets(time, dynamic_state),
        )

    def _refresh_switch_control_sampling_plan(self) -> None:
        plan = self._build_switch_control_sampling_plan()
        self._switch_control_sampling_plan = plan
        if plan.deduplicates:
            self._sample_algebraic_inputs = (
                self._sample_algebraic_inputs_deduplicated_switch_controls
            )
        else:
            self.__dict__.pop("_sample_algebraic_inputs", None)

    def _sample_algebraic_inputs_deduplicated_switch_controls(
        self,
        time: float,
        dynamic_state: Sequence[float],
    ) -> _AlgebraicInputs:
        plan = self._switch_control_sampling_plan
        switch_values = tuple(waveform.value(time) for waveform in plan.waveforms)
        return _AlgebraicInputs(
            current_source_values=tuple(
                source.waveform.value(time) for source in self.current_sources
            ),
            switch_resistances=tuple(
                switch.on_resistance
                if switch_values[value_index] >= switch.threshold
                else switch.off_resistance
                for switch, value_index in zip(
                    self.switches,
                    plan.value_indices,
                    strict=True,
                )
            ),
            constraint_targets=self._constraint_targets(time, dynamic_state),
        )

    def _build_switch_control_sampling_plan(self) -> _SwitchControlSamplingPlan:
        value_indices: list[int] = []
        waveforms: list[Waveform] = []
        builtin_indices: dict[tuple[object, ...], int] = {}
        deduplicates = False
        for switch in self.switches:
            waveform = switch.control
            value_key = _waveform_value_key(waveform)
            value_index = None if value_key is None else builtin_indices.get(value_key)
            if value_index is None:
                value_index = len(waveforms)
                waveforms.append(waveform)
                if value_key is not None:
                    builtin_indices[value_key] = value_index
            else:
                deduplicates = True
            value_indices.append(value_index)
        return _SwitchControlSamplingPlan(
            tuple(waveforms),
            tuple(value_indices),
            deduplicates,
        )

    def _constraint_targets(
        self,
        time: float,
        dynamic_state: Sequence[float],
    ) -> tuple[float, ...]:
        targets = [0.0] * len(self.constraint_branches)
        for target_index, source in self._voltage_constraint_targets:
            targets[target_index] = source.waveform.value(time)
        for target_index, state_index in self._capacitor_constraint_targets:
            targets[target_index] = dynamic_state[state_index]
        return tuple(targets)

    def _uses_reusable_algebraic_inputs(self) -> bool:
        return (
            self.algebraic_size >= REUSABLE_ALGEBRAIC_INPUT_MINIMUM_SIZE
            and self._uses_sparse_algebraic_jacobian()
        )

    def evaluate(
        self,
        time: float,
        dynamic_state: Sequence[float],
        algebraic_guess: Sequence[float] | None = None,
        *,
        newton_absolute_tolerance: float = 1.0e-11,
        newton_relative_tolerance: float = 1.0e-9,
        newton_max_iterations: int = 30,
        _algebraic_inputs: _AlgebraicInputs | None = None,
    ) -> CircuitEvaluation:
        if not math.isfinite(time):
            raise ValueError("evaluation time must be finite")
        state = tuple(map(float, dynamic_state))
        if len(state) != self.dynamic_size:
            raise ValueError(f"expected {self.dynamic_size} dynamic values, received {len(state)}")
        state_norm = 0.0
        for value in state:
            if not math.isfinite(value):
                raise CircuitSolveError("dynamic state must be finite")
            magnitude = abs(value)
            if magnitude > state_norm:
                state_norm = magnitude
        algebraic_inputs = _algebraic_inputs
        if algebraic_inputs is None and self._uses_reusable_algebraic_inputs():
            algebraic_inputs = self._sample_algebraic_inputs(time, state)
        algebraic = self._solve_algebraic_validated(
            time,
            state,
            algebraic_guess,
            absolute_tolerance=newton_absolute_tolerance,
            relative_tolerance=newton_relative_tolerance,
            max_iterations=newton_max_iterations,
            _inputs=algebraic_inputs,
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
        if algebraic_inputs is None:
            for source in self.current_sources:
                voltage = self.branch_voltage(algebraic, source.positive, source.negative)
                source_power -= voltage * source.waveform.value(time)
        else:
            for source, current in zip(
                self.current_sources,
                algebraic_inputs.current_source_values,
                strict=True,
            ):
                voltage = self.branch_voltage(algebraic, source.positive, source.negative)
                source_power -= voltage * current

        dissipated_power = 0.0
        for resistor in self.resistors:
            voltage = self.branch_voltage(algebraic, resistor.positive, resistor.negative)
            dissipated_power += voltage * voltage / resistor.resistance
        if algebraic_inputs is None:
            for switch in self.switches:
                voltage = self.branch_voltage(algebraic, switch.positive, switch.negative)
                resistance = (
                    switch.on_resistance
                    if switch.control.value(time) >= switch.threshold
                    else switch.off_resistance
                )
                dissipated_power += voltage * voltage / resistance
        else:
            for switch, resistance in zip(
                self.switches,
                algebraic_inputs.switch_resistances,
                strict=True,
            ):
                voltage = self.branch_voltage(algebraic, switch.positive, switch.negative)
                dissipated_power += voltage * voltage / resistance
        cached_diode_currents = (
            self._last_algebraic_diode_currents
            if type(self) is Circuit and algebraic.unknowns is self._last_algebraic_unknowns
            else None
        )
        if cached_diode_currents is not None and len(cached_diode_currents) == len(self.diodes):
            for current, stamp in zip(
                cached_diode_currents,
                self._diode_stamps,
                strict=True,
            ):
                positive_voltage = (
                    0.0
                    if stamp.positive_index is None
                    else algebraic.unknowns[stamp.positive_index]
                )
                negative_voltage = (
                    0.0
                    if stamp.negative_index is None
                    else algebraic.unknowns[stamp.negative_index]
                )
                dissipated_power += (positive_voltage - negative_voltage) * current
        else:
            for diode in self.diodes:
                voltage = self.branch_voltage(algebraic, diode.positive, diode.negative)
                current, _ = self._diode_current_and_conductance(diode, voltage)
                dissipated_power += voltage * current

        return CircuitEvaluation(
            time=time,
            dynamic_state=state,
            dynamic_state_norm=state_norm,
            derivative=tuple(derivative),
            algebraic=algebraic,
            stored_energy=stored_energy,
            source_power=source_power,
            dissipated_power=dissipated_power,
            _algebraic_inputs=algebraic_inputs,
            _input_owner=self,
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
        _inputs: _AlgebraicInputs | None = None,
    ) -> AlgebraicSolution:
        if not math.isfinite(time) or any(not math.isfinite(value) for value in dynamic_state):
            raise CircuitSolveError("algebraic solve inputs must be finite")
        return self._solve_algebraic_validated(
            time,
            dynamic_state,
            initial_guess,
            absolute_tolerance=absolute_tolerance,
            relative_tolerance=relative_tolerance,
            max_iterations=max_iterations,
            _inputs=_inputs,
        )

    def _solve_algebraic_validated(
        self,
        time: float,
        dynamic_state: Sequence[float],
        initial_guess: Sequence[float] | None = None,
        *,
        absolute_tolerance: float = 1.0e-11,
        relative_tolerance: float = 1.0e-9,
        max_iterations: int = 30,
        _inputs: _AlgebraicInputs | None = None,
    ) -> AlgebraicSolution:
        cached_unknown_norm = (
            self._last_algebraic_unknown_norm
            if initial_guess is self._last_algebraic_unknowns
            else None
        )
        if _inputs is None and self._uses_reusable_algebraic_inputs():
            _inputs = self._sample_algebraic_inputs(time, dynamic_state)
        if initial_guess is None:
            unknowns = [0.0] * self.algebraic_size
            constraint_targets = (
                _inputs.constraint_targets
                if _inputs is not None
                else self._constraint_targets(time, dynamic_state)
            )
            for branch, target_voltage in zip(
                self.constraint_branches,
                constraint_targets,
                strict=True,
            ):
                if branch.negative == GROUND and branch.positive != GROUND:
                    unknowns[self.node_index[branch.positive]] = target_voltage
                elif branch.positive == GROUND and branch.negative != GROUND:
                    unknowns[self.node_index[branch.negative]] = -target_voltage
        else:
            unknowns = list(map(float, initial_guess))
            if len(unknowns) != self.algebraic_size:
                raise ValueError("algebraic initial guess has the wrong size")
        if cached_unknown_norm is None:
            unknown_norm = 0.0
            for value in unknowns:
                if not math.isfinite(value):
                    raise CircuitSolveError("algebraic initial guess must be finite")
                magnitude = abs(value)
                if magnitude > unknown_norm:
                    unknown_norm = magnitude
        else:
            unknown_norm = cached_unknown_norm

        if self.algebraic_size == 0:
            return AlgebraicSolution((), {GROUND: 0.0}, {}, 0.0, 0)

        def try_update(
            base_unknowns: Sequence[float],
            base_residual_norm: float,
            delta: Sequence[float],
        ) -> tuple[list[float], float, float] | None:
            damping = 1.0
            for _ in range(14):
                trial = [
                    value + damping * update
                    for value, update in zip(base_unknowns, delta, strict=True)
                ]
                trial_residual = self._algebraic_residual(
                    time,
                    dynamic_state,
                    trial,
                    _inputs,
                )
                trial_residual_norm = norm_inf(trial_residual)
                if trial_residual_norm < base_residual_norm:
                    return trial, norm_inf(trial), trial_residual_norm
                damping *= 0.5
            return None

        chord_eligible = (
            type(self) is Circuit
            and bool(self.diodes)
            and self._uses_reusable_algebraic_inputs()
        )
        completed_iterations = 0
        chord_factorization = (
            self._last_nonlinear_algebraic_factorization
            if chord_eligible and max_iterations > 0
            else None
        )
        if chord_factorization is not None:
            residual = self._algebraic_residual(
                time,
                dynamic_state,
                unknowns,
                _inputs,
            )
            residual_norm = norm_inf(residual)
            tolerance = absolute_tolerance + relative_tolerance * max(unknown_norm, 1.0)
            if residual_norm <= tolerance:
                return self._make_algebraic_solution(
                    unknowns,
                    unknown_norm,
                    residual_norm,
                    0,
                )
            try:
                chord_delta = solve_factored(
                    chord_factorization,
                    [-value for value in residual],
                )
            except SingularMatrixError:
                self._last_nonlinear_algebraic_factorization = None
            else:
                chord_update = try_update(unknowns, residual_norm, chord_delta)
                if chord_update is None:
                    self._last_nonlinear_algebraic_factorization = None
                else:
                    unknowns, unknown_norm, residual_norm = chord_update
                    completed_iterations = 1
                    tolerance = absolute_tolerance + relative_tolerance * max(
                        unknown_norm,
                        1.0,
                    )
                    if residual_norm <= tolerance:
                        return self._make_algebraic_solution(
                            unknowns,
                            unknown_norm,
                            residual_norm,
                            completed_iterations,
                        )

        for iteration in range(completed_iterations, max_iterations + 1):
            factorization_key = self._linear_algebraic_factorization_cache_key(
                time,
                None if _inputs is None else _inputs.switch_resistances,
            )
            factorization = (
                None
                if factorization_key is None
                else self._linear_algebraic_factorization_cache.get(factorization_key)
            )
            if factorization is None:
                residual, jacobian = self._algebraic_residual_and_jacobian(
                    time,
                    dynamic_state,
                    unknowns,
                    _inputs,
                )
            else:
                residual = self._algebraic_residual(
                    time,
                    dynamic_state,
                    unknowns,
                    _inputs,
                )
                jacobian = None
            residual_norm = norm_inf(residual)
            tolerance = absolute_tolerance + relative_tolerance * max(unknown_norm, 1.0)
            if residual_norm <= tolerance:
                return self._make_algebraic_solution(
                    unknowns,
                    unknown_norm,
                    residual_norm,
                    iteration,
                )
            if iteration == max_iterations:
                break
            try:
                if factorization_key is None:
                    assert jacobian is not None
                    if chord_eligible:
                        factorization = factor_linear(
                            jacobian,
                            backend=self.linear_backend,
                        )
                        self._last_nonlinear_algebraic_factorization = factorization
                        delta = solve_factored(
                            factorization,
                            [-value for value in residual],
                        )
                    else:
                        delta = solve_linear(
                            jacobian,
                            [-value for value in residual],
                            backend=self.linear_backend,
                        )
                else:
                    if factorization is None:
                        assert jacobian is not None
                        factorization = factor_linear(
                            jacobian,
                            backend=self.linear_backend,
                        )
                        self._store_linear_cache_entry(
                            self._linear_algebraic_factorization_cache,
                            factorization_key,
                            factorization,
                        )
                    delta = solve_factored(
                        factorization,
                        [-value for value in residual],
                    )
            except SingularMatrixError as error:
                raise CircuitSolveError(f"algebraic solve failed: {error}") from error

            accepted_update = try_update(unknowns, residual_norm, delta)
            if accepted_update is None:
                if chord_eligible:
                    self._last_nonlinear_algebraic_factorization = None
                raise CircuitSolveError(
                    f"algebraic Newton line search failed at t={time:.17g}, residual={residual_norm:.6g}"
                )
            unknowns, unknown_norm, trial_residual_norm = accepted_update
            trial_tolerance = absolute_tolerance + relative_tolerance * max(
                unknown_norm,
                1.0,
            )
            if trial_residual_norm <= trial_tolerance:
                return self._make_algebraic_solution(
                    unknowns,
                    unknown_norm,
                    trial_residual_norm,
                    iteration + 1,
                )

        raise CircuitSolveError(
            f"algebraic Newton solve did not converge at t={time:.17g}, residual={residual_norm:.6g}"
        )

    def _make_algebraic_solution(
        self,
        unknowns: Sequence[float],
        unknown_norm: float,
        residual_norm: float,
        iterations: int,
    ) -> AlgebraicSolution:
        unknown_values = tuple(unknowns)
        diode_currents = (
            self._last_assembled_diode_currents
            if unknowns is self._last_assembled_unknowns
            else None
        )
        node_voltages = {GROUND: 0.0}
        remaining_values = iter(unknown_values)
        node_voltages.update(zip(self.nodes, remaining_values))
        branch_currents = dict(zip(self.branch_index, remaining_values, strict=True))
        self._last_algebraic_unknowns = unknown_values
        self._last_algebraic_unknown_norm = unknown_norm
        self._last_algebraic_diode_currents = diode_currents
        return AlgebraicSolution(
            unknowns=unknown_values,
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
        inputs: _AlgebraicInputs | None = None,
    ) -> tuple[list[float], LinearMatrix]:
        residual, jacobian = self._assemble_algebraic(
            time,
            dynamic_state,
            unknowns,
            include_jacobian=True,
            inputs=inputs,
        )
        assert jacobian is not None
        return residual, jacobian

    def _algebraic_residual(
        self,
        time: float,
        dynamic_state: Sequence[float],
        unknowns: Sequence[float],
        inputs: _AlgebraicInputs | None = None,
    ) -> list[float]:
        residual, _ = self._assemble_algebraic(
            time,
            dynamic_state,
            unknowns,
            include_jacobian=False,
            inputs=inputs,
        )
        return residual

    def _assemble_algebraic(
        self,
        time: float,
        dynamic_state: Sequence[float],
        unknowns: Sequence[float],
        *,
        include_jacobian: bool,
        inputs: _AlgebraicInputs | None = None,
    ) -> tuple[list[float], LinearMatrix | None]:
        if inputs is None:
            inputs = self._sample_algebraic_inputs(time, dynamic_state)
        if self._uses_sparse_algebraic_jacobian():
            if include_jacobian:
                return self._assemble_sparse_algebraic(
                    time,
                    dynamic_state,
                    unknowns,
                    inputs,
                )
            return self._assemble_compiled_algebraic_residual(
                time,
                dynamic_state,
                unknowns,
                inputs,
            ), None
        size = self.algebraic_size
        residual = [0.0] * size
        dense_jacobian = (
            [[0.0] * size for _ in range(size)]
            if include_jacobian
            else None
        )

        def voltage(stamp: _TerminalStamp) -> float:
            positive_voltage = (
                0.0
                if stamp.positive_index is None
                else unknowns[stamp.positive_index]
            )
            negative_voltage = (
                0.0
                if stamp.negative_index is None
                else unknowns[stamp.negative_index]
            )
            return positive_voltage - negative_voltage

        def add_known_current(stamp: _TerminalStamp, current: float) -> None:
            if stamp.positive_index is not None:
                residual[stamp.positive_index] += current
            if stamp.negative_index is not None:
                residual[stamp.negative_index] -= current

        def add_jacobian(stamp: _TerminalStamp, scale: float) -> None:
            assert dense_jacobian is not None
            for entry in stamp.jacobian_entries:
                dense_jacobian[entry.row][entry.column] += entry.multiplier * scale

        def add_conductance(
            stamp: _TerminalStamp,
            current: float,
            conductance: float,
        ) -> None:
            add_known_current(stamp, current)
            if not include_jacobian:
                return
            add_jacobian(stamp, conductance)

        for resistor, stamp in zip(self.resistors, self._resistor_stamps, strict=True):
            branch_voltage = voltage(stamp)
            conductance = 1.0 / resistor.resistance
            add_conductance(stamp, conductance * branch_voltage, conductance)

        for resistance, stamp in zip(
            inputs.switch_resistances,
            self._switch_stamps,
            strict=True,
        ):
            branch_voltage = voltage(stamp)
            conductance = 1.0 / resistance
            add_conductance(stamp, conductance * branch_voltage, conductance)

        for diode, stamp in zip(self.diodes, self._diode_stamps, strict=True):
            branch_voltage = voltage(stamp)
            current, conductance = self._diode_current_and_conductance(diode, branch_voltage)
            add_conductance(stamp, current, conductance)

        for current, stamp in zip(
            inputs.current_source_values,
            self._current_source_stamps,
            strict=True,
        ):
            add_known_current(stamp, current)

        for inductor, stamp in zip(self.inductors, self._inductor_stamps, strict=True):
            current = dynamic_state[self.inductor_state_index[inductor.name]]
            add_known_current(stamp, current)

        for branch, constraint_stamp, target_voltage in zip(
            self.constraint_branches,
            self._constraint_stamps,
            inputs.constraint_targets,
            strict=True,
        ):
            stamp = constraint_stamp.terminal
            branch_unknown_index = constraint_stamp.branch_index
            branch_current = unknowns[branch_unknown_index]
            add_known_current(stamp, branch_current)
            if include_jacobian:
                add_jacobian(stamp, 1.0)

            residual[branch_unknown_index] = voltage(stamp) - target_voltage

        return residual, dense_jacobian

    def _assemble_compiled_algebraic_residual(
        self,
        time: float,
        dynamic_state: Sequence[float],
        unknowns: Sequence[float],
        inputs: _AlgebraicInputs,
    ) -> list[float]:
        kernel = self._compiled_algebraic_residual_kernel
        if kernel is None and type(self) is Circuit and self._uses_reusable_algebraic_inputs():
            kernel = self._build_compiled_algebraic_residual_kernel()
            self._compiled_algebraic_residual_kernel = kernel
        if kernel is not None:
            return kernel(self, time, dynamic_state, unknowns, inputs)
        return self._assemble_compiled_algebraic_residual_fallback(
            time,
            dynamic_state,
            unknowns,
            inputs,
        )

    def _assemble_compiled_algebraic_residual_fallback(
        self,
        time: float,
        dynamic_state: Sequence[float],
        unknowns: Sequence[float],
        inputs: _AlgebraicInputs,
    ) -> list[float]:
        residual = [0.0] * self.algebraic_size
        diode_currents: list[float] = []

        for resistor, stamp in zip(self.resistors, self._resistor_stamps, strict=True):
            positive_voltage = (
                0.0 if stamp.positive_index is None else unknowns[stamp.positive_index]
            )
            negative_voltage = (
                0.0 if stamp.negative_index is None else unknowns[stamp.negative_index]
            )
            conductance = 1.0 / resistor.resistance
            current = conductance * (positive_voltage - negative_voltage)
            if stamp.positive_index is not None:
                residual[stamp.positive_index] += current
            if stamp.negative_index is not None:
                residual[stamp.negative_index] -= current

        for resistance, stamp in zip(
            inputs.switch_resistances,
            self._switch_stamps,
            strict=True,
        ):
            positive_voltage = (
                0.0 if stamp.positive_index is None else unknowns[stamp.positive_index]
            )
            negative_voltage = (
                0.0 if stamp.negative_index is None else unknowns[stamp.negative_index]
            )
            conductance = 1.0 / resistance
            current = conductance * (positive_voltage - negative_voltage)
            if stamp.positive_index is not None:
                residual[stamp.positive_index] += current
            if stamp.negative_index is not None:
                residual[stamp.negative_index] -= current

        inline_diode_kernel = type(self) is Circuit
        for diode, stamp in zip(self.diodes, self._diode_stamps, strict=True):
            positive_voltage = (
                0.0 if stamp.positive_index is None else unknowns[stamp.positive_index]
            )
            negative_voltage = (
                0.0 if stamp.negative_index is None else unknowns[stamp.negative_index]
            )
            voltage = positive_voltage - negative_voltage
            if inline_diode_kernel:
                exponent = voltage / diode.thermal_voltage
                if exponent > 40.0:
                    exponential = math.exp(40.0) * (1.0 + exponent - 40.0)
                elif exponent < -40.0:
                    exponential = math.exp(-40.0)
                else:
                    exponential = math.exp(exponent)
                current = diode.saturation_current * (exponential - 1.0)
            else:
                current, _ = self._diode_current_and_conductance(diode, voltage)
            diode_currents.append(current)
            if stamp.positive_index is not None:
                residual[stamp.positive_index] += current
            if stamp.negative_index is not None:
                residual[stamp.negative_index] -= current

        for current, stamp in zip(
            inputs.current_source_values,
            self._current_source_stamps,
            strict=True,
        ):
            if stamp.positive_index is not None:
                residual[stamp.positive_index] += current
            if stamp.negative_index is not None:
                residual[stamp.negative_index] -= current

        for inductor, stamp in zip(self.inductors, self._inductor_stamps, strict=True):
            current = dynamic_state[self.inductor_state_index[inductor.name]]
            if stamp.positive_index is not None:
                residual[stamp.positive_index] += current
            if stamp.negative_index is not None:
                residual[stamp.negative_index] -= current

        for branch, constraint_stamp, target_voltage in zip(
            self.constraint_branches,
            self._constraint_stamps,
            inputs.constraint_targets,
            strict=True,
        ):
            stamp = constraint_stamp.terminal
            branch_unknown_index = constraint_stamp.branch_index
            branch_current = unknowns[branch_unknown_index]
            if stamp.positive_index is not None:
                residual[stamp.positive_index] += branch_current
            if stamp.negative_index is not None:
                residual[stamp.negative_index] -= branch_current

            positive_voltage = (
                0.0 if stamp.positive_index is None else unknowns[stamp.positive_index]
            )
            negative_voltage = (
                0.0 if stamp.negative_index is None else unknowns[stamp.negative_index]
            )
            residual[branch_unknown_index] = (
                positive_voltage - negative_voltage - target_voltage
            )

        self._last_assembled_unknowns = unknowns
        self._last_assembled_diode_currents = tuple(diode_currents)
        return residual

    def _build_compiled_algebraic_residual_kernel(self) -> Any:
        lines = [
            "def kernel(self, time, dynamic_state, unknowns, inputs):",
            f"    residual = [0.0] * {self.algebraic_size}",
            "    diode_currents = []",
            "    resistors = self.resistors",
            "    diodes = self.diodes",
        ]

        def voltage_expressions(stamp: _TerminalStamp) -> tuple[str, str]:
            positive = (
                "0.0"
                if stamp.positive_index is None
                else f"unknowns[{stamp.positive_index}]"
            )
            negative = (
                "0.0"
                if stamp.negative_index is None
                else f"unknowns[{stamp.negative_index}]"
            )
            return positive, negative

        def append_current_stamp(stamp: _TerminalStamp, value: str) -> None:
            if stamp.positive_index is not None:
                lines.append(f"    residual[{stamp.positive_index}] += {value}")
            if stamp.negative_index is not None:
                lines.append(f"    residual[{stamp.negative_index}] -= {value}")

        for index, stamp in enumerate(self._resistor_stamps):
            positive, negative = voltage_expressions(stamp)
            lines.extend(
                [
                    f"    conductance = 1.0 / resistors[{index}].resistance",
                    f"    current = conductance * ({positive} - {negative})",
                ]
            )
            append_current_stamp(stamp, "current")

        for index, stamp in enumerate(self._switch_stamps):
            positive, negative = voltage_expressions(stamp)
            lines.extend(
                [
                    f"    conductance = 1.0 / inputs.switch_resistances[{index}]",
                    f"    current = conductance * ({positive} - {negative})",
                ]
            )
            append_current_stamp(stamp, "current")

        for index, stamp in enumerate(self._diode_stamps):
            positive, negative = voltage_expressions(stamp)
            lines.extend(
                [
                    f"    diode = diodes[{index}]",
                    f"    exponent = ({positive} - {negative}) / diode.thermal_voltage",
                    "    if exponent > 40.0:",
                    "        exponential = exp40 * (1.0 + exponent - 40.0)",
                    "    elif exponent < -40.0:",
                    "        exponential = exp_neg40",
                    "    else:",
                    "        exponential = exp(exponent)",
                    "    current = diode.saturation_current * (exponential - 1.0)",
                    "    diode_currents.append(current)",
                ]
            )
            append_current_stamp(stamp, "current")

        for index, stamp in enumerate(self._current_source_stamps):
            append_current_stamp(stamp, f"inputs.current_source_values[{index}]")

        for inductor, stamp in zip(
            self.inductors,
            self._inductor_stamps,
            strict=True,
        ):
            append_current_stamp(
                stamp,
                f"dynamic_state[{self.inductor_state_index[inductor.name]}]",
            )

        for index, constraint_stamp in enumerate(self._constraint_stamps):
            stamp = constraint_stamp.terminal
            branch_index = constraint_stamp.branch_index
            positive, negative = voltage_expressions(stamp)
            append_current_stamp(stamp, f"unknowns[{branch_index}]")
            lines.append(
                f"    residual[{branch_index}] = {positive} - {negative} "
                f"- inputs.constraint_targets[{index}]"
            )

        lines.extend(
            [
                "    self._last_assembled_unknowns = unknowns",
                "    self._last_assembled_diode_currents = tuple(diode_currents)",
                "    return residual",
            ]
        )
        namespace = {
            "exp": math.exp,
            "exp40": math.exp(40.0),
            "exp_neg40": math.exp(-40.0),
        }
        source = "\n".join(lines) + "\n"
        exec(compile(source, "<babcs-algebraic-residual>", "exec"), namespace)
        return namespace["kernel"]

    def _build_compiled_sparse_algebraic_kernel(self) -> Any:
        lines = [
            "def kernel(self, time, dynamic_state, unknowns, inputs, raw_data=False):",
            f"    residual = [0.0] * {self.algebraic_size}",
            f"    sparse_data = [0.0] * {len(self._algebraic_sparse_row_indices)}",
            "    diode_currents = []",
            "    resistors = self.resistors",
            "    diodes = self.diodes",
        ]

        def voltage_expressions(stamp: _TerminalStamp) -> tuple[str, str]:
            positive = (
                "0.0"
                if stamp.positive_index is None
                else f"unknowns[{stamp.positive_index}]"
            )
            negative = (
                "0.0"
                if stamp.negative_index is None
                else f"unknowns[{stamp.negative_index}]"
            )
            return positive, negative

        def append_current_stamp(stamp: _TerminalStamp, value: str) -> None:
            if stamp.positive_index is not None:
                lines.append(f"    residual[{stamp.positive_index}] += {value}")
            if stamp.negative_index is not None:
                lines.append(f"    residual[{stamp.negative_index}] -= {value}")

        def append_jacobian_stamp(stamp: _TerminalStamp, value: str) -> None:
            for entry in stamp.jacobian_entries:
                lines.append(
                    f"    sparse_data[{entry.sparse_index}] += "
                    f"{entry.multiplier!r} * {value}"
                )

        for index, stamp in enumerate(self._resistor_stamps):
            positive, negative = voltage_expressions(stamp)
            lines.extend(
                [
                    f"    conductance = 1.0 / resistors[{index}].resistance",
                    f"    current = conductance * ({positive} - {negative})",
                ]
            )
            append_current_stamp(stamp, "current")
            append_jacobian_stamp(stamp, "conductance")

        for index, stamp in enumerate(self._switch_stamps):
            positive, negative = voltage_expressions(stamp)
            lines.extend(
                [
                    f"    conductance = 1.0 / inputs.switch_resistances[{index}]",
                    f"    current = conductance * ({positive} - {negative})",
                ]
            )
            append_current_stamp(stamp, "current")
            append_jacobian_stamp(stamp, "conductance")

        for index, stamp in enumerate(self._diode_stamps):
            positive, negative = voltage_expressions(stamp)
            lines.extend(
                [
                    f"    diode = diodes[{index}]",
                    f"    exponent = ({positive} - {negative}) / diode.thermal_voltage",
                    "    if exponent > 40.0:",
                    "        exponential = exp40 * (1.0 + exponent - 40.0)",
                    "        derivative = exp40",
                    "    elif exponent < -40.0:",
                    "        exponential = exp_neg40",
                    "        derivative = exp_neg40",
                    "    else:",
                    "        exponential = exp(exponent)",
                    "        derivative = exponential",
                    "    current = diode.saturation_current * (exponential - 1.0)",
                    "    conductance = (",
                    "        diode.saturation_current * derivative / diode.thermal_voltage",
                    "    )",
                    "    diode_currents.append(current)",
                ]
            )
            append_current_stamp(stamp, "current")
            append_jacobian_stamp(stamp, "conductance")

        for index, stamp in enumerate(self._current_source_stamps):
            append_current_stamp(stamp, f"inputs.current_source_values[{index}]")

        for inductor, stamp in zip(
            self.inductors,
            self._inductor_stamps,
            strict=True,
        ):
            append_current_stamp(
                stamp,
                f"dynamic_state[{self.inductor_state_index[inductor.name]}]",
            )

        for index, constraint_stamp in enumerate(self._constraint_stamps):
            stamp = constraint_stamp.terminal
            branch_index = constraint_stamp.branch_index
            positive, negative = voltage_expressions(stamp)
            append_current_stamp(stamp, f"unknowns[{branch_index}]")
            for entry in stamp.jacobian_entries:
                lines.append(
                    f"    sparse_data[{entry.sparse_index}] += {entry.multiplier!r}"
                )
            lines.append(
                f"    residual[{branch_index}] = {positive} - {negative} "
                f"- inputs.constraint_targets[{index}]"
            )

        lines.extend(
            [
                "    self._last_assembled_unknowns = unknowns",
                "    self._last_assembled_diode_currents = tuple(diode_currents)",
                "    if raw_data:",
                "        return residual, sparse_data",
                "    return residual, self._algebraic_sparse_template.with_data(sparse_data)",
            ]
        )
        source = "\n".join(lines) + "\n"
        return _compile_sparse_algebraic_kernel(source)

    def _build_compiled_sparse_algebraic_jacobian_kernel(self) -> Any:
        lines = [
            "def kernel(self, unknowns, inputs):",
            f"    sparse_data = [0.0] * {len(self._algebraic_sparse_row_indices)}",
            "    resistors = self.resistors",
            "    diodes = self.diodes",
        ]

        def voltage_expressions(stamp: _TerminalStamp) -> tuple[str, str]:
            positive = (
                "0.0"
                if stamp.positive_index is None
                else f"unknowns[{stamp.positive_index}]"
            )
            negative = (
                "0.0"
                if stamp.negative_index is None
                else f"unknowns[{stamp.negative_index}]"
            )
            return positive, negative

        def append_jacobian_stamp(stamp: _TerminalStamp, value: str) -> None:
            for entry in stamp.jacobian_entries:
                lines.append(
                    f"    sparse_data[{entry.sparse_index}] += "
                    f"{entry.multiplier!r} * {value}"
                )

        for index, stamp in enumerate(self._resistor_stamps):
            lines.append(f"    conductance = 1.0 / resistors[{index}].resistance")
            append_jacobian_stamp(stamp, "conductance")

        for index, stamp in enumerate(self._switch_stamps):
            lines.append(
                f"    conductance = 1.0 / inputs.switch_resistances[{index}]"
            )
            append_jacobian_stamp(stamp, "conductance")

        for index, stamp in enumerate(self._diode_stamps):
            positive, negative = voltage_expressions(stamp)
            lines.extend(
                [
                    f"    diode = diodes[{index}]",
                    f"    exponent = ({positive} - {negative}) / diode.thermal_voltage",
                    "    if exponent > 40.0:",
                    "        derivative = exp40",
                    "    elif exponent < -40.0:",
                    "        derivative = exp_neg40",
                    "    else:",
                    "        derivative = exp(exponent)",
                    "    conductance = (",
                    "        diode.saturation_current * derivative / diode.thermal_voltage",
                    "    )",
                ]
            )
            append_jacobian_stamp(stamp, "conductance")

        for constraint_stamp in self._constraint_stamps:
            for entry in constraint_stamp.terminal.jacobian_entries:
                lines.append(
                    f"    sparse_data[{entry.sparse_index}] += {entry.multiplier!r}"
                )

        lines.append("    return sparse_data")
        source = "\n".join(lines) + "\n"
        return _compile_sparse_algebraic_jacobian_kernel(source)

    def _sparse_algebraic_topology(self) -> tuple[object, ...]:
        return (
            self.algebraic_size,
            self._algebraic_sparse_row_indices,
            self._algebraic_sparse_column_pointers,
            self._resistor_stamps,
            self._switch_stamps,
            self._diode_stamps,
            self._current_source_stamps,
            self._inductor_stamps,
            tuple(
                self.inductor_state_index[inductor.name]
                for inductor in self.inductors
            ),
            self._constraint_stamps,
        )

    def _assemble_sparse_algebraic(
        self,
        time: float,
        dynamic_state: Sequence[float],
        unknowns: Sequence[float],
        inputs: _AlgebraicInputs,
    ) -> tuple[list[float], SparseMatrix]:
        kernel = self._compiled_sparse_algebraic_kernel
        if kernel is not None:
            return kernel(self, time, dynamic_state, unknowns, inputs)
        if type(self) is Circuit and self._uses_reusable_algebraic_inputs():
            if self._compiled_sparse_algebraic_calls == 0:
                topology = self._sparse_algebraic_topology()
                self._compiled_sparse_algebraic_topology = topology
                kernel = _lookup_compiled_sparse_algebraic_topology(topology)
                if kernel is not None:
                    self._compiled_sparse_algebraic_kernel = kernel
                    return kernel(self, time, dynamic_state, unknowns, inputs)
            self._compiled_sparse_algebraic_calls += 1
            if (
                self._compiled_sparse_algebraic_calls
                >= COMPILED_SPARSE_ALGEBRAIC_MINIMUM_CALLS
            ):
                kernel = self._build_compiled_sparse_algebraic_kernel()
                self._compiled_sparse_algebraic_kernel = kernel
                topology = self._compiled_sparse_algebraic_topology
                if topology is None:
                    topology = self._sparse_algebraic_topology()
                    self._compiled_sparse_algebraic_topology = topology
                _store_compiled_sparse_algebraic_topology(topology, kernel)
                return kernel(self, time, dynamic_state, unknowns, inputs)
        return self._assemble_sparse_algebraic_fallback(
            time,
            dynamic_state,
            unknowns,
            inputs,
        )

    def _assemble_sparse_algebraic_fallback(
        self,
        time: float,
        dynamic_state: Sequence[float],
        unknowns: Sequence[float],
        inputs: _AlgebraicInputs,
    ) -> tuple[list[float], SparseMatrix]:
        residual = [0.0] * self.algebraic_size
        sparse_data = [0.0] * len(self._algebraic_sparse_row_indices)
        diode_currents: list[float] = []

        for resistor, stamp in zip(self.resistors, self._resistor_stamps, strict=True):
            positive_voltage = (
                0.0 if stamp.positive_index is None else unknowns[stamp.positive_index]
            )
            negative_voltage = (
                0.0 if stamp.negative_index is None else unknowns[stamp.negative_index]
            )
            conductance = 1.0 / resistor.resistance
            current = conductance * (positive_voltage - negative_voltage)
            if stamp.positive_index is not None:
                residual[stamp.positive_index] += current
            if stamp.negative_index is not None:
                residual[stamp.negative_index] -= current
            for entry in stamp.jacobian_entries:
                sparse_data[entry.sparse_index] += entry.multiplier * conductance

        for resistance, stamp in zip(
            inputs.switch_resistances,
            self._switch_stamps,
            strict=True,
        ):
            positive_voltage = (
                0.0 if stamp.positive_index is None else unknowns[stamp.positive_index]
            )
            negative_voltage = (
                0.0 if stamp.negative_index is None else unknowns[stamp.negative_index]
            )
            conductance = 1.0 / resistance
            current = conductance * (positive_voltage - negative_voltage)
            if stamp.positive_index is not None:
                residual[stamp.positive_index] += current
            if stamp.negative_index is not None:
                residual[stamp.negative_index] -= current
            for entry in stamp.jacobian_entries:
                sparse_data[entry.sparse_index] += entry.multiplier * conductance

        inline_diode_kernel = type(self) is Circuit
        for diode, stamp in zip(self.diodes, self._diode_stamps, strict=True):
            positive_voltage = (
                0.0 if stamp.positive_index is None else unknowns[stamp.positive_index]
            )
            negative_voltage = (
                0.0 if stamp.negative_index is None else unknowns[stamp.negative_index]
            )
            voltage = positive_voltage - negative_voltage
            if inline_diode_kernel:
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
                conductance = (
                    diode.saturation_current * derivative / diode.thermal_voltage
                )
            else:
                current, conductance = self._diode_current_and_conductance(diode, voltage)
            diode_currents.append(current)
            if stamp.positive_index is not None:
                residual[stamp.positive_index] += current
            if stamp.negative_index is not None:
                residual[stamp.negative_index] -= current
            for entry in stamp.jacobian_entries:
                sparse_data[entry.sparse_index] += entry.multiplier * conductance

        for current, stamp in zip(
            inputs.current_source_values,
            self._current_source_stamps,
            strict=True,
        ):
            if stamp.positive_index is not None:
                residual[stamp.positive_index] += current
            if stamp.negative_index is not None:
                residual[stamp.negative_index] -= current

        for inductor, stamp in zip(self.inductors, self._inductor_stamps, strict=True):
            current = dynamic_state[self.inductor_state_index[inductor.name]]
            if stamp.positive_index is not None:
                residual[stamp.positive_index] += current
            if stamp.negative_index is not None:
                residual[stamp.negative_index] -= current

        for branch, constraint_stamp, target_voltage in zip(
            self.constraint_branches,
            self._constraint_stamps,
            inputs.constraint_targets,
            strict=True,
        ):
            stamp = constraint_stamp.terminal
            branch_unknown_index = constraint_stamp.branch_index
            branch_current = unknowns[branch_unknown_index]
            if stamp.positive_index is not None:
                residual[stamp.positive_index] += branch_current
            if stamp.negative_index is not None:
                residual[stamp.negative_index] -= branch_current
            for entry in stamp.jacobian_entries:
                sparse_data[entry.sparse_index] += entry.multiplier

            positive_voltage = (
                0.0 if stamp.positive_index is None else unknowns[stamp.positive_index]
            )
            negative_voltage = (
                0.0 if stamp.negative_index is None else unknowns[stamp.negative_index]
            )
            residual[branch_unknown_index] = (
                positive_voltage - negative_voltage - target_voltage
            )

        self._last_assembled_unknowns = unknowns
        self._last_assembled_diode_currents = tuple(diode_currents)
        return residual, self._algebraic_sparse_template.with_data(sparse_data)

    def _build_algebraic_sparse_pattern(
        self,
    ) -> tuple[tuple[int, ...], tuple[int, ...], dict[tuple[int, int], int]]:
        positions: set[tuple[int, int]] = set()

        def add_conductance_pattern(positive: str, negative: str) -> None:
            positive_index = self.node_index.get(positive)
            negative_index = self.node_index.get(negative)
            if positive_index is not None:
                positions.add((positive_index, positive_index))
                if negative_index is not None:
                    positions.add((positive_index, negative_index))
            if negative_index is not None:
                if positive_index is not None:
                    positions.add((negative_index, positive_index))
                positions.add((negative_index, negative_index))

        for element in (*self.resistors, *self.switches, *self.diodes):
            add_conductance_pattern(element.positive, element.negative)
        for branch in self.constraint_branches:
            branch_index = self.branch_index[branch.name]
            if branch.positive != GROUND:
                node_index = self.node_index[branch.positive]
                positions.add((node_index, branch_index))
                positions.add((branch_index, node_index))
            if branch.negative != GROUND:
                node_index = self.node_index[branch.negative]
                positions.add((node_index, branch_index))
                positions.add((branch_index, node_index))

        row_indices: list[int] = []
        column_pointers = [0]
        position_index: dict[tuple[int, int], int] = {}
        for column in range(self.algebraic_size):
            column_rows = sorted(row for row, candidate_column in positions if candidate_column == column)
            for row in column_rows:
                position_index[(row, column)] = len(row_indices)
                row_indices.append(row)
            column_pointers.append(len(row_indices))
        return tuple(row_indices), tuple(column_pointers), position_index

    def _make_terminal_stamp(self, element: Element) -> _TerminalStamp:
        return _TerminalStamp(
            self.node_index.get(element.positive),
            self.node_index.get(element.negative),
        )

    def _make_conductance_stamp(self, element: Element) -> _TerminalStamp:
        terminal = self._make_terminal_stamp(element)
        positions: list[tuple[int, int, float]] = []
        if terminal.positive_index is not None:
            positions.append((terminal.positive_index, terminal.positive_index, 1.0))
            if terminal.negative_index is not None:
                positions.append((terminal.positive_index, terminal.negative_index, -1.0))
        if terminal.negative_index is not None:
            if terminal.positive_index is not None:
                positions.append((terminal.negative_index, terminal.positive_index, -1.0))
            positions.append((terminal.negative_index, terminal.negative_index, 1.0))
        return _TerminalStamp(
            terminal.positive_index,
            terminal.negative_index,
            tuple(
                _JacobianStamp(
                    row,
                    column,
                    self._algebraic_sparse_position_index[(row, column)],
                    multiplier,
                )
                for row, column, multiplier in positions
            ),
        )

    def _make_constraint_stamp(self, element: Element) -> _ConstraintStamp:
        terminal = self._make_terminal_stamp(element)
        branch_index = self.branch_index[element.name]
        positions: list[tuple[int, int, float]] = []
        if terminal.positive_index is not None:
            positions.extend(
                [
                    (terminal.positive_index, branch_index, 1.0),
                    (branch_index, terminal.positive_index, 1.0),
                ]
            )
        if terminal.negative_index is not None:
            positions.extend(
                [
                    (terminal.negative_index, branch_index, -1.0),
                    (branch_index, terminal.negative_index, -1.0),
                ]
            )
        return _ConstraintStamp(
            _TerminalStamp(
                terminal.positive_index,
                terminal.negative_index,
                tuple(
                    _JacobianStamp(
                        row,
                        column,
                        self._algebraic_sparse_position_index[(row, column)],
                        multiplier,
                    )
                    for row, column, multiplier in positions
                ),
            ),
            branch_index,
        )

    def _build_differential_sensitivity_right_hand_sides(
        self,
    ) -> tuple[tuple[float, ...], ...]:
        right_hand_sides: list[tuple[float, ...]] = []
        for state_index in range(self.dynamic_size):
            right_hand_side = [0.0] * self.algebraic_size
            if state_index < len(self.capacitors):
                capacitor = self.capacitors[state_index]
                right_hand_side[self.branch_index[capacitor.name]] = 1.0
            else:
                inductor = self.inductors[state_index - len(self.capacitors)]
                if inductor.positive != GROUND:
                    right_hand_side[self.node_index[inductor.positive]] = -1.0
                if inductor.negative != GROUND:
                    right_hand_side[self.node_index[inductor.negative]] = 1.0
            right_hand_sides.append(tuple(right_hand_side))
        return tuple(right_hand_sides)

    def _build_implicit_block_sparse_structure(
        self,
    ) -> tuple[
        SparseMatrix,
        tuple[int, ...],
        tuple[_ImplicitBlockStamp, ...],
        tuple[int, ...],
    ]:
        algebraic_size = self.algebraic_size
        block_size = algebraic_size + self.dynamic_size
        positions: set[tuple[int, int]] = set()
        for column in range(algebraic_size):
            for sparse_index in range(
                self._algebraic_sparse_column_pointers[column],
                self._algebraic_sparse_column_pointers[column + 1],
            ):
                positions.add((self._algebraic_sparse_row_indices[sparse_index], column))

        derivative_entries: list[tuple[int, int, float]] = []
        for state_index, capacitor in enumerate(self.capacitors):
            row = algebraic_size + state_index
            column = self.branch_index[capacitor.name]
            multiplier = 1.0 / capacitor.capacitance
            positions.add((row, column))
            derivative_entries.append((row, column, multiplier))
        for inductor_index, inductor in enumerate(self.inductors):
            row = algebraic_size + len(self.capacitors) + inductor_index
            if inductor.positive != GROUND:
                column = self.node_index[inductor.positive]
                multiplier = 1.0 / inductor.inductance
                positions.add((row, column))
                derivative_entries.append((row, column, multiplier))
            if inductor.negative != GROUND:
                column = self.node_index[inductor.negative]
                multiplier = -1.0 / inductor.inductance
                positions.add((row, column))
                derivative_entries.append((row, column, multiplier))

        for state_index, right_hand_side in enumerate(
            self._differential_sensitivity_right_hand_sides
        ):
            column = algebraic_size + state_index
            for row, value in enumerate(right_hand_side):
                if value != 0.0:
                    positions.add((row, column))
            positions.add((column, column))

        row_indices: list[int] = []
        column_pointers = [0]
        position_index: dict[tuple[int, int], int] = {}
        for column in range(block_size):
            column_rows = sorted(
                row for row, candidate_column in positions if candidate_column == column
            )
            for row in column_rows:
                position_index[(row, column)] = len(row_indices)
                row_indices.append(row)
            column_pointers.append(len(row_indices))

        data = [0.0] * len(row_indices)
        for state_index, right_hand_side in enumerate(
            self._differential_sensitivity_right_hand_sides
        ):
            column = algebraic_size + state_index
            for row, value in enumerate(right_hand_side):
                if value != 0.0:
                    data[position_index[(row, column)]] = -value

        algebraic_positions: list[int] = []
        for column in range(algebraic_size):
            for sparse_index in range(
                self._algebraic_sparse_column_pointers[column],
                self._algebraic_sparse_column_pointers[column + 1],
            ):
                row = self._algebraic_sparse_row_indices[sparse_index]
                algebraic_positions.append(position_index[(row, column)])

        return (
            SparseMatrix(
                block_size,
                tuple(data),
                tuple(row_indices),
                tuple(column_pointers),
            ),
            tuple(algebraic_positions),
            tuple(
                _ImplicitBlockStamp(position_index[(row, column)], multiplier)
                for row, column, multiplier in derivative_entries
            ),
            tuple(
                position_index[(algebraic_size + state_index, algebraic_size + state_index)]
                for state_index in range(self.dynamic_size)
            ),
        )

    def _uses_sparse_algebraic_jacobian(self) -> bool:
        backend = self.linear_backend
        if (
            backend == self._sparse_algebraic_backend
            and self._sparse_algebraic_enabled is not None
        ):
            return self._sparse_algebraic_enabled
        if backend == "dense" or self.algebraic_size == 0:
            enabled = False
        elif backend in {"klu", "scipy"}:
            enabled = True
        elif not sparse_linear_available():
            return False
        else:
            minimum_size = (
                SCIPY_SPARSE_SINGLE_SOLVE_MINIMUM_SIZE
                if self.diodes
                else SCIPY_SPARSE_REUSABLE_MINIMUM_SIZE
            )
            density = len(self._algebraic_sparse_row_indices) / self.algebraic_size**2
            enabled = (
                self.algebraic_size >= minimum_size
                and density <= SCIPY_SPARSE_MAXIMUM_DENSITY
            )
        self._sparse_algebraic_backend = backend
        self._sparse_algebraic_enabled = enabled
        return enabled

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

    def differential_jacobian_at_evaluation(
        self,
        evaluation: CircuitEvaluation,
    ) -> list[list[float]]:
        if type(self).differential_jacobian is Circuit.differential_jacobian:
            return self.differential_jacobian(
                evaluation.time,
                evaluation.dynamic_state,
                evaluation.algebraic.unknowns,
                base_evaluation=evaluation,
            )
        return self.differential_jacobian(
            evaluation.time,
            evaluation.dynamic_state,
            evaluation.algebraic.unknowns,
        )

    def differential_jacobian_norm_at_evaluation(
        self,
        evaluation: CircuitEvaluation,
    ) -> float:
        native = self._native_differential_sensitivity(evaluation)
        if native is not None:
            return native.differential_jacobian_norm
        return matrix_inf_norm(self.differential_jacobian_at_evaluation(evaluation))

    def _predict_sparse_algebraic_projection(
        self,
        evaluation: CircuitEvaluation,
        target_time: float,
        target_state: Sequence[float],
    ) -> _AlgebraicProjection | None:
        if len(target_state) != self.dynamic_size:
            raise ValueError("algebraic projection state has the wrong size")
        native = self._native_differential_sensitivity(evaluation)
        if native is None:
            return None

        numpy = native.numpy
        state_delta = numpy.asarray(target_state, dtype=float) - numpy.asarray(
            evaluation.dynamic_state,
            dtype=float,
        )
        predicted_unknowns = numpy.asarray(
            evaluation.algebraic.unknowns,
            dtype=float,
        ) + state_delta @ native.sensitivities
        inputs = self._sample_algebraic_inputs(target_time, target_state)
        residual = self._algebraic_residual(
            target_time,
            target_state,
            predicted_unknowns,
            inputs,
        )
        try:
            correction = solve_factored(
                native.factorization,
                [-value for value in residual],
            )
        except SingularMatrixError as error:
            raise CircuitSolveError(f"algebraic projection failed: {error}") from error
        unknowns = tuple(
            float(value + update)
            for value, update in zip(
                predicted_unknowns,
                correction,
                strict=True,
            )
        )
        return _AlgebraicProjection(
            unknowns=unknowns,
            inputs=inputs,
            differential_jacobian_norm=native.differential_jacobian_norm,
        )

    def _native_differential_scales(self, numpy: Any) -> tuple[Any, Any]:
        scale_values = (
            tuple(capacitor.capacitance for capacitor in self.capacitors),
            tuple(inductor.inductance for inductor in self.inductors),
        )
        if self._native_differential_scale_values != scale_values:
            capacitances = numpy.asarray(scale_values[0], dtype=float)
            inductances = numpy.asarray(scale_values[1], dtype=float)
            capacitances.setflags(write=False)
            inductances.setflags(write=False)
            self._native_differential_scale_values = scale_values
            self._native_capacitances = capacitances
            self._native_inductances = inductances
        return self._native_capacitances, self._native_inductances

    def _native_differential_sensitivity(
        self,
        evaluation: CircuitEvaluation,
    ) -> _NativeDifferentialSensitivity | None:
        if (
            type(self) is not Circuit
            or self.dynamic_size == 0
            or not self.diodes
            or self.algebraic_size < REUSABLE_ALGEBRAIC_INPUT_MINIMUM_SIZE
            or not self._uses_sparse_algebraic_jacobian()
        ):
            return None

        inputs = (
            evaluation._algebraic_inputs
            if evaluation._input_owner is self
            else None
        )
        numpy = _numpy_component()
        if numpy is None:
            return None
        native_right_hand_sides = (
            self._native_differential_sensitivity_right_hand_sides
        )
        if native_right_hand_sides is None:
            native_right_hand_sides = numpy.asarray(
                self._differential_sensitivity_right_hand_sides,
                dtype=float,
            )
            native_right_hand_sides.setflags(write=False)
            self._native_differential_sensitivity_right_hand_sides = (
                native_right_hand_sides
            )
        factor_backend = self.linear_backend
        automatic_klu = (
            factor_backend == "auto"
            and self.algebraic_size
            >= KLU_NATIVE_SENSITIVITY_MINIMUM_ALGEBRAIC_SIZE
            and self.dynamic_size
            >= KLU_NATIVE_SENSITIVITY_MINIMUM_RIGHT_HAND_SIDES
            and klu_sparse_available()
        )
        if automatic_klu:
            factor_backend = "klu"
        algebraic_jacobian: SparseMatrix | None = None
        sparse_data: Sequence[float]
        kernel = self._compiled_sparse_algebraic_kernel
        compiled_jacobian_eligible = factor_backend == "klu" and (
            kernel is not None
            or (
                self.algebraic_size
                >= KLU_NATIVE_SENSITIVITY_MINIMUM_ALGEBRAIC_SIZE
                and self.dynamic_size
                >= KLU_NATIVE_SENSITIVITY_MINIMUM_RIGHT_HAND_SIDES
            )
        )
        if compiled_jacobian_eligible:
            if inputs is None:
                inputs = self._sample_algebraic_inputs(
                    evaluation.time,
                    evaluation.dynamic_state,
                )
            jacobian_kernel = self._compiled_sparse_algebraic_jacobian_kernel
            if jacobian_kernel is None:
                jacobian_kernel = (
                    self._build_compiled_sparse_algebraic_jacobian_kernel()
                )
                self._compiled_sparse_algebraic_jacobian_kernel = jacobian_kernel
            sparse_data = jacobian_kernel(
                self,
                evaluation.algebraic.unknowns,
                inputs,
            )
        else:
            _, assembled_jacobian = self._algebraic_residual_and_jacobian(
                evaluation.time,
                evaluation.dynamic_state,
                evaluation.algebraic.unknowns,
                inputs,
            )
            if not isinstance(assembled_jacobian, SparseMatrix):
                return None
            algebraic_jacobian = assembled_jacobian
            sparse_data = algebraic_jacobian.data
        try:
            if factor_backend == "klu":
                factorization, sensitivities = (
                    _factor_and_solve_klu_sparse_values_multiple_array(
                        self.algebraic_size,
                        sparse_data,
                        self._algebraic_sparse_row_indices,
                        self._algebraic_sparse_column_pointers,
                        native_right_hand_sides,
                    )
                )
            else:
                assert algebraic_jacobian is not None
                factorization = factor_linear(
                    algebraic_jacobian,
                    backend=factor_backend,
                )
                sensitivities = solve_factored_multiple_array(
                    factorization,
                    native_right_hand_sides,
                )
        except (LinearBackendUnavailableError, SingularMatrixError) as error:
            if automatic_klu:
                try:
                    if algebraic_jacobian is None:
                        algebraic_jacobian = self._algebraic_sparse_template.with_data(
                            sparse_data
                        )
                    factorization = factor_linear(
                        algebraic_jacobian,
                        backend="scipy",
                    )
                    sensitivities = solve_factored_multiple_array(
                        factorization,
                        native_right_hand_sides,
                    )
                except (LinearBackendUnavailableError, SingularMatrixError) as fallback_error:
                    raise CircuitSolveError(
                        f"differential sensitivity solve failed: {fallback_error}"
                    ) from fallback_error
            else:
                raise CircuitSolveError(
                    f"differential sensitivity solve failed: {error}"
                ) from error
        if sensitivities is None:
            return None

        differential_jacobian = numpy.empty(
            (self.dynamic_size, self.dynamic_size),
            dtype=float,
        )
        capacitances, inductances = self._native_differential_scales(numpy)
        maximum = 0.0
        if self.capacitors:
            capacitor_sensitivities = sensitivities[:, self._capacitor_branch_indices]
            differential_jacobian[: len(self.capacitors), :] = (
                capacitor_sensitivities.transpose() / capacitances[:, None]
            )
            row_sums = numpy.sum(
                numpy.abs(capacitor_sensitivities),
                axis=0,
            )
            scaled_maximum = float(
                numpy.max(row_sums / capacitances, initial=0.0)
            )
            if math.isnan(scaled_maximum):
                return scaled_maximum
            if scaled_maximum > maximum:
                maximum = scaled_maximum
        if self.inductors:
            positive_columns = self._inductor_positive_sensitivity_columns
            positive_nodes = self._inductor_positive_sensitivity_nodes
            if len(positive_columns) == len(self.inductors):
                voltage_sensitivities = sensitivities[:, positive_nodes]
            else:
                voltage_sensitivities = numpy.zeros(
                    (self.dynamic_size, len(self.inductors)),
                    dtype=float,
                )
                voltage_sensitivities[:, positive_columns] = sensitivities[
                    :, positive_nodes
                ]
            negative_columns = self._inductor_negative_sensitivity_columns
            if negative_columns:
                negative_nodes = self._inductor_negative_sensitivity_nodes
                if len(negative_columns) == len(self.inductors):
                    voltage_sensitivities -= sensitivities[:, negative_nodes]
                else:
                    voltage_sensitivities[:, negative_columns] -= sensitivities[
                        :, negative_nodes
                    ]
            row_sums = numpy.sum(numpy.abs(voltage_sensitivities), axis=0)
            differential_jacobian[len(self.capacitors) :, :] = (
                voltage_sensitivities.transpose() / inductances[:, None]
            )
            scaled_maximum = float(
                numpy.max(row_sums / inductances, initial=0.0)
            )
            if math.isnan(scaled_maximum):
                return scaled_maximum
            if scaled_maximum > maximum:
                maximum = scaled_maximum

        rounding = self.dynamic_size * 2.220446049250313e-16
        if maximum == 0.0 or not math.isfinite(maximum) or rounding >= 1.0:
            differential_jacobian_norm = maximum
        else:
            differential_jacobian_norm = math.nextafter(
                maximum / (1.0 - rounding),
                math.inf,
            )
        native = _NativeDifferentialSensitivity(
            factorization=factorization,
            sensitivities=sensitivities,
            differential_jacobian=differential_jacobian,
            differential_jacobian_norm=differential_jacobian_norm,
            numpy=numpy,
        )
        self._latest_native_differential_sensitivity_evaluation = evaluation
        self._latest_native_differential_sensitivity = native
        return native

    def differential_jacobian(
        self,
        time: float,
        dynamic_state: Sequence[float],
        algebraic_guess: Sequence[float] | None = None,
        *,
        base_evaluation: CircuitEvaluation | None = None,
    ) -> list[list[float]]:
        state_values = tuple(dynamic_state)
        if base_evaluation is None:
            base = self.evaluate(time, state_values, algebraic_guess)
        else:
            if base_evaluation.time != time or base_evaluation.dynamic_state != state_values:
                raise ValueError("differential Jacobian base evaluation does not match its state")
            base = base_evaluation

        if type(self) is Circuit:
            cache_key = self._linear_differential_jacobian_cache_key(time)
            if cache_key is not None:
                cached = self._linear_differential_jacobian_cache.get(cache_key)
                if cached is not None:
                    return [list(row) for row in cached]
            jacobian = self._analytic_differential_jacobian(base)
            if cache_key is not None:
                self._store_linear_cache_entry(
                    self._linear_differential_jacobian_cache,
                    cache_key,
                    tuple(tuple(row) for row in jacobian),
                )
            return jacobian

        def derivative(candidate: list[float]) -> list[float]:
            return list(self.evaluate(time, candidate, base.algebraic.unknowns).derivative)

        return finite_difference_jacobian(derivative, state_values, base.derivative)

    def _linear_differential_jacobian_cache_key(
        self,
        time: float,
    ) -> tuple[tuple[float, ...], ...] | None:
        if self.diodes:
            return None
        return (
            tuple(resistor.resistance for resistor in self.resistors),
            tuple(capacitor.capacitance for capacitor in self.capacitors),
            tuple(inductor.inductance for inductor in self.inductors),
            tuple(
                switch.on_resistance
                if switch.control.value(time) >= switch.threshold
                else switch.off_resistance
                for switch in self.switches
            ),
        )

    def _linear_algebraic_factorization_cache_key(
        self,
        time: float,
        switch_resistances: Sequence[float] | None = None,
    ) -> tuple[tuple[float, ...], ...] | None:
        if type(self) is not Circuit or self.diodes:
            return None
        if switch_resistances is None:
            switch_resistances = tuple(
                switch.on_resistance
                if switch.control.value(time) >= switch.threshold
                else switch.off_resistance
                for switch in self.switches
            )
        return (
            tuple(resistor.resistance for resistor in self.resistors),
            tuple(switch_resistances),
        )

    def linear_implicit_factorization(
        self,
        evaluation: CircuitEvaluation,
        state_coefficient: float,
        derivative_coefficient: float,
    ) -> ReusableLinearFactorization | None:
        if type(self) is not Circuit:
            return None
        topology_key = self._linear_differential_jacobian_cache_key(evaluation.time)
        if topology_key is None:
            return None
        cache_key = (topology_key, state_coefficient, derivative_coefficient)
        cached = self._linear_implicit_factorization_cache.get(cache_key)
        if cached is not None:
            return cached
        differential_jacobian = self.differential_jacobian_at_evaluation(evaluation)
        residual_jacobian = [
            [
                (state_coefficient if row == column else 0.0)
                - derivative_coefficient * differential_jacobian[row][column]
                for column in range(self.dynamic_size)
            ]
            for row in range(self.dynamic_size)
        ]
        factorization = factor_linear(
            residual_jacobian,
            backend=self.linear_backend,
        )
        self._store_linear_cache_entry(
            self._linear_implicit_factorization_cache,
            cache_key,
            factorization,
        )
        return factorization

    def sparse_implicit_update(
        self,
        evaluation: CircuitEvaluation,
        state_coefficient: float,
        derivative_coefficient: float,
        residual: Sequence[float],
        *,
        allow_chord: bool = True,
    ) -> SparseImplicitUpdate | None:
        if (
            type(self) is not Circuit
            or not self.diodes
            or not self._uses_sparse_algebraic_jacobian()
        ):
            return None
        if len(residual) != self.dynamic_size:
            raise ValueError("implicit residual has the wrong size")
        if allow_chord:
            chord_update = self._sparse_chord_implicit_update(
                evaluation,
                state_coefficient,
                derivative_coefficient,
                residual,
            )
            if chord_update is not None:
                return chord_update
        inputs = (
            evaluation._algebraic_inputs
            if evaluation._input_owner is self
            else None
        )
        _, algebraic_jacobian = self._algebraic_residual_and_jacobian(
            evaluation.time,
            evaluation.dynamic_state,
            evaluation.algebraic.unknowns,
            inputs,
        )
        if not isinstance(algebraic_jacobian, SparseMatrix):
            return None

        block_data = list(self._implicit_block_sparse_template.data)
        for value, block_index in zip(
            algebraic_jacobian.data,
            self._implicit_block_algebraic_positions,
            strict=True,
        ):
            block_data[block_index] = value
        for stamp in self._implicit_block_derivative_stamps:
            block_data[stamp.sparse_index] = -derivative_coefficient * stamp.multiplier
        for sparse_index in self._implicit_block_diagonal_positions:
            block_data[sparse_index] = state_coefficient

        block_matrix = self._implicit_block_sparse_template.with_data(block_data)
        right_hand_side = [0.0] * self.algebraic_size
        right_hand_side.extend(-float(value) for value in residual)
        solution = solve_linear(
            block_matrix,
            right_hand_side,
            backend=self.linear_backend,
        )
        return SparseImplicitUpdate(
            algebraic_update=tuple(solution[: self.algebraic_size]),
            dynamic_update=tuple(solution[self.algebraic_size :]),
        )

    def _sparse_chord_implicit_update(
        self,
        evaluation: CircuitEvaluation,
        state_coefficient: float,
        derivative_coefficient: float,
        residual: Sequence[float],
    ) -> SparseImplicitUpdate | None:
        source_evaluation = self._latest_native_differential_sensitivity_evaluation
        native = self._latest_native_differential_sensitivity
        if source_evaluation is None or native is None:
            return None
        if not _within_ulp_time_window(
            source_evaluation.time,
            evaluation.time,
            2.0 * abs(derivative_coefficient),
        ):
            return None
        source_inputs = (
            source_evaluation._algebraic_inputs
            if source_evaluation._input_owner is self
            else None
        )
        target_inputs = (
            evaluation._algebraic_inputs
            if evaluation._input_owner is self
            else None
        )
        if (
            source_inputs is not None
            and target_inputs is not None
            and source_inputs.switch_resistances != target_inputs.switch_resistances
        ):
            return None

        numpy = native.numpy
        implicit_jacobian = -derivative_coefficient * native.differential_jacobian
        diagonal = numpy.diag_indices(self.dynamic_size)
        implicit_jacobian[diagonal] += state_coefficient
        try:
            dynamic_update = numpy.linalg.solve(
                implicit_jacobian,
                -numpy.asarray(residual, dtype=float),
            )
        except numpy.linalg.LinAlgError:
            return None
        algebraic_update = native.sensitivities.transpose() @ dynamic_update
        if not numpy.all(numpy.isfinite(dynamic_update)) or not numpy.all(
            numpy.isfinite(algebraic_update)
        ):
            return None
        return SparseImplicitUpdate(
            algebraic_update=tuple(map(float, algebraic_update)),
            dynamic_update=tuple(map(float, dynamic_update)),
            requires_contraction=True,
        )

    @staticmethod
    def _store_linear_cache_entry(cache: dict, key: object, value: object) -> None:
        if key not in cache and len(cache) >= MAXIMUM_LINEAR_CACHE_ENTRIES:
            cache.pop(next(iter(cache)))
        cache[key] = value

    def _analytic_differential_jacobian(
        self,
        evaluation: CircuitEvaluation,
    ) -> list[list[float]]:
        if self.dynamic_size == 0:
            return []
        inputs = (
            evaluation._algebraic_inputs
            if evaluation._input_owner is self
            else None
        )
        _, algebraic_jacobian = self._algebraic_residual_and_jacobian(
            evaluation.time,
            evaluation.dynamic_state,
            evaluation.algebraic.unknowns,
            inputs,
        )
        jacobian = [[0.0] * self.dynamic_size for _ in range(self.dynamic_size)]
        right_hand_sides = self._differential_sensitivity_right_hand_sides

        try:
            algebraic_sensitivities = (
                [
                    solve_linear(
                        algebraic_jacobian,
                        right_hand_sides[0],
                        backend=self.linear_backend,
                    )
                ]
                if self.dynamic_size == 1
                else solve_linear_multiple(
                    algebraic_jacobian,
                    right_hand_sides,
                    backend=self.linear_backend,
                )
            )
        except SingularMatrixError as error:
            raise CircuitSolveError(f"differential sensitivity solve failed: {error}") from error

        for state_index, algebraic_sensitivity in enumerate(algebraic_sensitivities):
            for capacitor_index, capacitor in enumerate(self.capacitors):
                jacobian[capacitor_index][state_index] = (
                    algebraic_sensitivity[self.branch_index[capacitor.name]]
                    / capacitor.capacitance
                )
            for inductor_index, inductor in enumerate(self.inductors):
                positive_voltage = (
                    0.0
                    if inductor.positive == GROUND
                    else algebraic_sensitivity[self.node_index[inductor.positive]]
                )
                negative_voltage = (
                    0.0
                    if inductor.negative == GROUND
                    else algebraic_sensitivity[self.node_index[inductor.negative]]
                )
                jacobian[len(self.capacitors) + inductor_index][state_index] = (
                    positive_voltage - negative_voltage
                ) / inductor.inductance
        return jacobian


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
