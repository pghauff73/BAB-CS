from __future__ import annotations

import hashlib
import html
import json
import math
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Sequence

from babcs import BoundedAdamsBashforthIntegrator, Simulator
from babcs.io import load_case
from babcs.linalg import weighted_rms

try:
    from tools.method_observatory import execute_observatory
except ModuleNotFoundError:
    from method_observatory import execute_observatory


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

CASE_PATHS = {
    "rc_step": Path("benchmarks/cases/rc_step.json"),
    "rl_step": Path("benchmarks/cases/rl_step.json"),
    "rlc_damped": Path("benchmarks/cases/rlc_damped.json"),
    "lc_long": Path("benchmarks/cases/lc_long.json"),
    "diode_clip": Path("benchmarks/cases/diode_clip.json"),
    "switched_rc": Path("benchmarks/cases/switched_rc.json"),
    "buck_like": Path("examples/power_stage/buck_like_reduced_order.json"),
    "h_bridge_rl": Path("examples/power_stage/h_bridge_rl_reduced_order.json"),
    "dc_link_rlc": Path("examples/power_stage/dc_link_rlc_reduced_order.json"),
}

FIGURE_ASSET_NAMES = (
    "circuit-rc-step.svg",
    "result-rc-step.svg",
    "circuit-rl-step.svg",
    "result-rl-step.svg",
    "circuit-rlc-damped.svg",
    "result-rlc-damped.svg",
    "circuit-lc-long.svg",
    "result-lc-long.svg",
    "circuit-diode-clip.svg",
    "result-diode-clip.svg",
    "circuit-switched-rc.svg",
    "result-switched-rc.svg",
    "circuit-buck-like.svg",
    "result-buck-like.svg",
    "circuit-h-bridge-rl.svg",
    "result-h-bridge-rl.svg",
    "circuit-dc-link-rlc.svg",
    "result-dc-link-rlc.svg",
    "result-observatory-accuracy-work.svg",
    "result-bound-coverage.svg",
    "result-coverage-by-age.svg",
    "result-phase-energy.svg",
    "result-rejection-causes.svg",
)

TRACE_COLORS = (
    "#0d7185",
    "#d9782d",
    "#6856a8",
    "#2f8f68",
    "#b34e63",
    "#4d6e93",
    "#8a6b1f",
)


def _rc_voltage(
    time: float,
    *,
    resistance: float,
    capacitance: float,
    source_voltage: float,
    initial_voltage: float,
) -> float:
    time_constant = resistance * capacitance
    return source_voltage + (initial_voltage - source_voltage) * math.exp(-time / time_constant)


def _parallel_rlc_state(
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
        first_coefficient = (initial_derivative - second_root * initial_voltage) / (first_root - second_root)
        second_coefficient = initial_voltage - first_coefficient
        first_term = first_coefficient * math.exp(first_root * time)
        second_term = second_coefficient * math.exp(second_root * time)
        voltage = first_term + second_term
        derivative = first_root * first_term + second_root * second_term
    current = -capacitance * derivative - conductance * voltage
    return voltage, current


def _classify_reason(reason: str) -> str:
    normalized = reason.lower().replace("_", "-")
    rules = (
        ("minimum step", "minimum_step"),
        ("non-finite", "non_finite_metric"),
        ("predictor/reference", "predictor_reference_cap"),
        ("anchor/reference", "anchor_reference_cap"),
        ("estimated-bound", "recursive_bound_cap"),
        ("bound cap", "recursive_bound_cap"),
        ("algebraic residual", "algebraic_residual_cap"),
        ("full residual", "full_residual_cap"),
        ("energy", "energy_injection_cap"),
        ("stiff", "stiffness_transfer"),
        ("contract", "non_contractive"),
        ("event", "event_restart"),
        ("re-anchor", "replay_failure"),
        ("replay", "replay_failure"),
        ("projection", "projection_failure"),
        ("reference", "reference_nonconvergence"),
        ("candidate", "candidate_nonconvergence"),
        ("linear", "linear_solve_failure"),
        ("config", "configuration_error"),
    )
    for fragment, code in rules:
        if fragment in normalized:
            return code
    return "unknown"


def _svg_document(
    title: str,
    description: str,
    body: str,
    *,
    width: int,
    height: int,
) -> bytes:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title description" viewBox="0 0 {width} {height}">
  <title id="title">{html.escape(title)}</title>
  <desc id="description">{html.escape(description)}</desc>
  <defs>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="7" stdDeviation="9" flood-color="#10243a" flood-opacity="0.11"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0 0 L10 5 L0 10 Z" fill="#0d7185"/>
    </marker>
    <style>
      .sans {{ font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
      .mono {{ font-family: "SFMono-Regular", Consolas, monospace; }}
      .title {{ fill: #10243a; font-size: 30px; font-weight: 820; letter-spacing: -0.025em; }}
      .subtitle {{ fill: #607386; font-size: 15px; }}
      .section {{ fill: #0a5870; font-size: 12px; font-weight: 820; letter-spacing: 0.1em; }}
      .label {{ fill: #10243a; font-size: 15px; font-weight: 760; }}
      .value {{ fill: #607386; font-size: 13px; }}
      .small {{ fill: #607386; font-size: 12px; }}
      .micro {{ fill: #718397; font-size: 10.5px; font-weight: 680; letter-spacing: 0.04em; }}
      .wire {{ fill: none; stroke: #27485a; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }}
      .symbol {{ fill: #ffffff; stroke: #27485a; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }}
      .node {{ fill: #0d7185; }}
      .ground {{ fill: none; stroke: #27485a; stroke-width: 2.5; stroke-linecap: round; }}
      .event {{ stroke: #d9782d; stroke-width: 1.5; stroke-dasharray: 6 6; }}
      .axis {{ stroke: #9aabba; stroke-width: 1.2; }}
      .grid {{ stroke: #dce5ec; stroke-width: 1; }}
      .plot {{ fill: none; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }}
      .card {{ fill: #ffffff; stroke: #d5e0e9; stroke-width: 1.5; }}
      .soft {{ fill: #edf6f8; stroke: #b8d6df; stroke-width: 1.5; }}
      .warm {{ fill: #fff3e7; stroke: #e4bd98; stroke-width: 1.5; }}
    </style>
  </defs>
{body}
</svg>
'''.encode("utf-8")


@lru_cache(maxsize=None)
def _case_payload(case_id: str) -> dict[str, Any]:
    path = REPOSITORY_ROOT / CASE_PATHS[case_id]
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("elements"), list):
        raise ValueError(f"{CASE_PATHS[case_id]}: invalid case payload")
    return data


@lru_cache(maxsize=None)
def _case_sha256(case_id: str) -> str:
    return hashlib.sha256((REPOSITORY_ROOT / CASE_PATHS[case_id]).read_bytes()).hexdigest()


@lru_cache(maxsize=None)
def _case_execution(case_id: str):
    circuit, simulation, config = load_case(REPOSITORY_ROOT / CASE_PATHS[case_id])
    result = Simulator(BoundedAdamsBashforthIntegrator(config)).run(
        circuit,
        simulation["stop_time"],
        simulation["nominal_step"],
        start_time=simulation["start_time"],
    )
    return circuit, simulation, config, result


def _element(case_id: str, name: str) -> dict[str, Any]:
    matches = [element for element in _case_payload(case_id)["elements"] if element.get("name") == name]
    if len(matches) != 1:
        raise ValueError(f"{CASE_PATHS[case_id]}: expected one element named {name}")
    return matches[0]


def _engineering(value: float, unit: str) -> str:
    absolute = abs(value)
    scales = (
        (1.0e9, "G"),
        (1.0e6, "M"),
        (1.0e3, "k"),
        (1.0, ""),
        (1.0e-3, "m"),
        (1.0e-6, "µ"),
        (1.0e-9, "n"),
        (1.0e-12, "p"),
    )
    for scale, prefix in scales:
        if absolute >= scale or scale == 1.0e-12:
            return f"{value / scale:.4g} {prefix}{unit}"
    raise AssertionError("engineering scale is unreachable")


def _component_value(element: dict[str, Any]) -> str:
    kind = str(element["type"]).lower()
    if kind in {"r", "resistor"}:
        return _engineering(float(element["resistance"]), "Ω")
    if kind in {"c", "capacitor"}:
        return _engineering(float(element["capacitance"]), "F")
    if kind in {"l", "inductor"}:
        return _engineering(float(element["inductance"]), "H")
    if kind in {"v", "voltage_source"}:
        waveform = element["waveform"]
        if isinstance(waveform, (int, float)):
            return _engineering(float(waveform), "V")
        if waveform.get("type") == "sine":
            return f'{_engineering(float(waveform["amplitude"]), "V")} sine · {_engineering(float(waveform["frequency"]), "Hz")}'
        return "declared waveform"
    if kind in {"s", "switch"}:
        return f'{_engineering(float(element["on_resistance"]), "Ω")} on'
    if kind in {"d", "diode"}:
        return "Shockley diode"
    return "declared value"


def _text(x: float, y: float, value: str, class_name: str = "label", *, anchor: str = "start") -> str:
    return f'<text class="sans {class_name}" x="{x:g}" y="{y:g}" text-anchor="{anchor}">{html.escape(value)}</text>'


def _rotated_text(
    x: float,
    y: float,
    value: str,
    class_name: str = "small",
    *,
    angle: float = -90.0,
) -> str:
    return (
        f'<text class="sans {class_name}" x="{x:g}" y="{y:g}" text-anchor="middle" '
        f'transform="rotate({angle:g} {x:g} {y:g})">{html.escape(value)}</text>'
    )


def _wire(x1: float, y1: float, x2: float, y2: float) -> str:
    return f'<path class="wire" d="M{x1:g} {y1:g} L{x2:g} {y2:g}"/>'


def _node(x: float, y: float, label: str = "") -> str:
    rendered = f'<circle class="node" cx="{x:g}" cy="{y:g}" r="5"/>'
    if label:
        rendered += _text(x, y - 15, label, "micro", anchor="middle")
    return rendered


def _ground(x: float, y: float) -> str:
    return (
        _wire(x, y - 24, x, y)
        + f'<path class="ground" d="M{x-18:g} {y:g} H{x+18:g} M{x-12:g} {y+8:g} H{x+12:g} M{x-6:g} {y+16:g} H{x+6:g}"/>'
    )


def _resistor_h(x1: float, x2: float, y: float, name: str, value: str) -> str:
    lead = 22.0
    usable = x2 - x1 - 2 * lead
    step = usable / 8.0
    points = [(x1 + lead, y)]
    for index in range(1, 8):
        points.append((x1 + lead + step * index, y + (-13 if index % 2 else 13)))
    points.append((x2 - lead, y))
    path = " ".join(f"L{x:g} {point_y:g}" for x, point_y in points[1:])
    return (
        _wire(x1, y, x1 + lead, y)
        + f'<path class="wire" d="M{points[0][0]:g} {y:g} {path}"/>'
        + _wire(x2 - lead, y, x2, y)
        + _text((x1 + x2) / 2, y - 28, name, anchor="middle")
        + _text((x1 + x2) / 2, y + 38, value, "value", anchor="middle")
    )


def _resistor_v(x: float, y1: float, y2: float, name: str, value: str, *, side: str = "right") -> str:
    lead = 22.0
    usable = y2 - y1 - 2 * lead
    step = usable / 8.0
    points = [(x, y1 + lead)]
    for index in range(1, 8):
        points.append((x + (-13 if index % 2 else 13), y1 + lead + step * index))
    points.append((x, y2 - lead))
    path = " ".join(f"L{point_x:g} {y:g}" for point_x, y in points[1:])
    label_x = x + (35 if side == "right" else -35)
    anchor = "start" if side == "right" else "end"
    return (
        _wire(x, y1, x, y1 + lead)
        + f'<path class="wire" d="M{x:g} {points[0][1]:g} {path}"/>'
        + _wire(x, y2 - lead, x, y2)
        + _text(label_x, (y1 + y2) / 2 - 8, name, anchor=anchor)
        + _text(label_x, (y1 + y2) / 2 + 17, value, "value", anchor=anchor)
    )


def _capacitor_v(x: float, y1: float, y2: float, name: str, value: str, *, side: str = "right") -> str:
    middle = (y1 + y2) / 2
    label_x = x + (34 if side == "right" else -34)
    anchor = "start" if side == "right" else "end"
    return (
        _wire(x, y1, x, middle - 14)
        + f'<path class="symbol" d="M{x-24:g} {middle-14:g} H{x+24:g} M{x-24:g} {middle+14:g} H{x+24:g}"/>'
        + _wire(x, middle + 14, x, y2)
        + _text(label_x, middle - 8, name, anchor=anchor)
        + _text(label_x, middle + 17, value, "value", anchor=anchor)
    )


def _inductor_h(x1: float, x2: float, y: float, name: str, value: str) -> str:
    lead = 22.0
    start = x1 + lead
    end = x2 - lead
    radius = (end - start) / 8.0
    arcs = " ".join(
        f"a{radius:g} {radius:g} 0 0 1 {2*radius:g} 0"
        for _ in range(4)
    )
    return (
        _wire(x1, y, start, y)
        + f'<path class="wire" d="M{start:g} {y:g} {arcs}"/>'
        + _wire(end, y, x2, y)
        + _text((x1 + x2) / 2, y - 30, name, anchor="middle")
        + _text((x1 + x2) / 2, y + 40, value, "value", anchor="middle")
    )


def _inductor_v(x: float, y1: float, y2: float, name: str, value: str, *, side: str = "right") -> str:
    label_x = x + (38 if side == "right" else -38)
    anchor = "start" if side == "right" else "end"
    length = y2 - y1
    rendered = f'<g transform="translate({x:g} {y1:g}) rotate(90)">{_inductor_h(0, length, 0, "", "")}</g>'
    return rendered + _text(label_x, (y1 + y2) / 2 - 8, name, anchor=anchor) + _text(
        label_x, (y1 + y2) / 2 + 17, value, "value", anchor=anchor
    )


def _voltage_source_v(x: float, y1: float, y2: float, name: str, value: str) -> str:
    middle = (y1 + y2) / 2
    radius = 42
    return (
        _wire(x, y1, x, middle - radius)
        + f'<circle class="symbol" cx="{x:g}" cy="{middle:g}" r="{radius}"/>'
        + _text(x, middle - 12, "+", "label", anchor="middle")
        + _text(x, middle + 24, "−", "label", anchor="middle")
        + _wire(x, middle + radius, x, y2)
        + _text(x - 58, middle - 6, name, anchor="end")
        + _text(x - 58, middle + 19, value, "value", anchor="end")
    )


def _switch_h(x1: float, x2: float, y: float, name: str, value: str) -> str:
    return (
        _wire(x1, y, x1 + 24, y)
        + _wire(x2 - 24, y, x2, y)
        + f'<circle class="symbol" cx="{x1+24:g}" cy="{y:g}" r="5"/>'
        + f'<circle class="symbol" cx="{x2-24:g}" cy="{y:g}" r="5"/>'
        + f'<path class="wire" d="M{x1+28:g} {y-3:g} L{x2-30:g} {y-27:g}"/>'
        + _text((x1 + x2) / 2, y - 42, name, anchor="middle")
        + _text((x1 + x2) / 2, y + 32, value, "value", anchor="middle")
    )


def _switch_v(x: float, y1: float, y2: float, name: str, value: str, *, side: str = "right") -> str:
    label_x = x + (35 if side == "right" else -35)
    anchor = "start" if side == "right" else "end"
    length = y2 - y1
    rendered = f'<g transform="translate({x:g} {y1:g}) rotate(90)">{_switch_h(0, length, 0, "", "")}</g>'
    return rendered + _text(label_x, (y1 + y2) / 2 - 8, name, anchor=anchor) + _text(
        label_x, (y1 + y2) / 2 + 17, value, "value", anchor=anchor
    )


def _diode_v(x: float, y1: float, y2: float, name: str, value: str, *, side: str = "right") -> str:
    middle = (y1 + y2) / 2
    label_x = x + (36 if side == "right" else -36)
    anchor = "start" if side == "right" else "end"
    return (
        _wire(x, y1, x, middle - 28)
        + f'<path class="symbol" d="M{x-22:g} {middle-28:g} L{x+22:g} {middle-28:g} L{x:g} {middle+8:g} Z M{x-23:g} {middle+14:g} H{x+23:g}"/>'
        + _wire(x, middle + 14, x, y2)
        + _text(label_x, middle - 8, name, anchor=anchor)
        + _text(label_x, middle + 17, value, "value", anchor=anchor)
    )


def _circuit_shell(case_id: str, title: str, description: str, diagram: str, *, note: str = "") -> bytes:
    relative = CASE_PATHS[case_id].as_posix()
    sha = _case_sha256(case_id)
    note_markup = ""
    if note:
        note_markup = f'''  <rect class="warm" x="70" y="516" width="1060" height="50" rx="13"/>
  {_text(92, 547, note, "small")}'''
    body = f'''  <rect width="1200" height="650" rx="28" fill="#f5f8fb"/>
  {_text(64, 58, title, "title")}
  {_text(64, 96, description, "subtitle")}
  <rect class="card" x="52" y="132" width="1096" height="364" rx="22" filter="url(#shadow)"/>
  <g>{diagram}</g>
{note_markup}
  <text class="mono micro" x="70" y="616">SOURCE {html.escape(relative)} · INPUT SHA-256 {sha[:16]}</text>'''
    return _svg_document(
        title,
        f"{description} Generated from {relative}, SHA-256 {sha}.",
        body,
        width=1200,
        height=650,
    )


def _rc_circuit_svg() -> bytes:
    case_id = "rc_step"
    source = _element(case_id, "V1")
    resistor = _element(case_id, "R1")
    capacitor = _element(case_id, "C1")
    diagram = (
        _voltage_source_v(180, 220, 420, "V1", _component_value(source))
        + _wire(180, 220, 320, 220)
        + _resistor_h(320, 560, 220, "R1", _component_value(resistor))
        + _wire(560, 220, 760, 220)
        + _node(650, 220, "out")
        + _capacitor_v(650, 220, 420, "C1", _component_value(capacitor))
        + _wire(180, 420, 760, 420)
        + _ground(470, 420)
        + _text(856, 248, "Accepted state", "section")
        + _text(856, 280, "v(C1)", "label")
        + _text(856, 311, "Charging toward 1 V", "value")
    )
    return _circuit_shell(case_id, "RC step circuit", "A voltage step charges one capacitor through one resistor.", diagram)


def _rl_circuit_svg() -> bytes:
    case_id = "rl_step"
    source = _element(case_id, "V1")
    resistor = _element(case_id, "R1")
    inductor = _element(case_id, "L1")
    diagram = (
        _voltage_source_v(180, 220, 420, "V1", _component_value(source))
        + _wire(180, 220, 320, 220)
        + _resistor_h(320, 560, 220, "R1", _component_value(resistor))
        + _wire(560, 220, 650, 220)
        + _node(650, 220, "out")
        + _inductor_v(650, 220, 420, "L1", _component_value(inductor))
        + _wire(180, 420, 760, 420)
        + _ground(470, 420)
        + '<path class="wire" marker-end="url(#arrow)" d="M720 275 V350"/>'
        + _text(744, 320, "i(L1)", "label")
        + _text(856, 248, "Accepted state", "section")
        + _text(856, 280, "i(L1)", "label")
        + _text(856, 311, "Current rises toward 0.1 A", "value")
    )
    return _circuit_shell(case_id, "RL step circuit", "A voltage step drives current through a resistor and inductor.", diagram)


def _parallel_tank_svg(case_id: str, *, damped: bool) -> bytes:
    capacitor = _element(case_id, "C1")
    inductor = _element(case_id, "L1")
    resistor = _element(case_id, "R1") if damped else None
    title = "Damped parallel RLC circuit" if damped else "Lossless parallel LC circuit"
    description = (
        "Electrical and magnetic energy exchange while the resistor dissipates energy."
        if damped
        else "Electrical and magnetic energy exchange without a declared resistive loss path."
    )
    branch_x = (360, 600, 840) if damped else (470, 730)
    diagram = _wire(280, 210, 920, 210) + _wire(280, 420, 920, 420) + _node(600, 210, "tank")
    if damped and resistor is not None:
        diagram += _resistor_v(branch_x[0], 210, 420, "R1", _component_value(resistor), side="left")
        capacitor_x = branch_x[1]
        inductor_x = branch_x[2]
    else:
        capacitor_x, inductor_x = branch_x
    diagram += _capacitor_v(capacitor_x, 210, 420, "C1", _component_value(capacitor), side="left")
    diagram += _inductor_v(inductor_x, 210, 420, "L1", _component_value(inductor))
    diagram += _ground(600, 420)
    diagram += _text(86, 244, "Initial condition", "section")
    diagram += _text(86, 278, "v(C1) = 1 V", "label")
    diagram += _text(86, 309, "i(L1) = 0 A", "value")
    note = "Lossless here means no declared resistor; numerical phase and energy must still be reported separately." if not damped else "The resistor is the declared physical damping path; numerical energy loss remains a separate measurement."
    return _circuit_shell(case_id, title, description, diagram, note=note)


def _diode_clip_circuit_svg() -> bytes:
    case_id = "diode_clip"
    source = _element(case_id, "V1")
    resistor = _element(case_id, "R1")
    diode = _element(case_id, "D1")
    capacitor = _element(case_id, "C1")
    diagram = (
        _voltage_source_v(155, 220, 430, "V1", _component_value(source))
        + _wire(155, 220, 275, 220)
        + _resistor_h(275, 515, 220, "R1", _component_value(resistor))
        + _wire(515, 220, 825, 220)
        + _node(650, 220, "out")
        + _diode_v(600, 220, 430, "D1", _component_value(diode), side="left")
        + _capacitor_v(760, 220, 430, "C1", _component_value(capacitor))
        + _wire(155, 430, 825, 430)
        + _ground(650, 430)
        + _text(888, 250, "Nonlinear check", "section")
        + _text(888, 282, "Diode conduction clips", "label")
        + _text(888, 313, "the positive output swing", "value")
    )
    return _circuit_shell(case_id, "Diode-clip circuit", "A sine source drives an RC node with a nonlinear diode clamp.", diagram)


def _switched_rc_circuit_svg() -> bytes:
    case_id = "switched_rc"
    source = _element(case_id, "V1")
    resistor = _element(case_id, "R1")
    capacitor = _element(case_id, "C1")
    switch = _element(case_id, "S1")
    diagram = (
        _voltage_source_v(155, 220, 430, "V1", _component_value(source))
        + _wire(155, 220, 275, 220)
        + _resistor_h(275, 515, 220, "R1", _component_value(resistor))
        + _wire(515, 220, 825, 220)
        + _node(650, 220, "out")
        + _capacitor_v(595, 220, 430, "C1", _component_value(capacitor), side="left")
        + _switch_v(760, 220, 430, "S1", _component_value(switch))
        + _wire(155, 430, 825, 430)
        + _ground(650, 430)
        + _text(880, 250, "Scheduled event", "section")
        + _text(880, 282, "S1 discharges C1", "label")
        + _text(880, 313, "at exact pulse boundaries", "value")
    )
    return _circuit_shell(case_id, "Switched RC circuit", "A scheduled resistive switch repeatedly discharges the capacitor node.", diagram)


def _buck_circuit_svg() -> bytes:
    case_id = "buck_like"
    source = _element(case_id, "VDC")
    switch = _element(case_id, "S_HIGH")
    diode = _element(case_id, "D_FREE")
    bleed = _element(case_id, "R_SW_BLEED")
    inductor = _element(case_id, "L_OUT")
    capacitor = _element(case_id, "C_OUT")
    load = _element(case_id, "R_LOAD")
    diagram = (
        _voltage_source_v(120, 220, 440, "VDC", _component_value(source))
        + _wire(120, 220, 215, 220)
        + _switch_h(215, 390, 220, "S_HIGH", _component_value(switch))
        + _wire(390, 220, 455, 220)
        + _node(455, 220, "sw")
        + _inductor_h(455, 690, 220, "L_OUT", _component_value(inductor))
        + _wire(690, 220, 960, 220)
        + _node(790, 220, "out")
        + _diode_v(390, 220, 440, "D_FREE", _component_value(diode), side="left")
        + _resistor_v(510, 220, 440, "R_SW_BLEED", _component_value(bleed))
        + _capacitor_v(780, 220, 440, "C_OUT", _component_value(capacitor), side="left")
        + _resistor_v(940, 220, 440, "R_LOAD", _component_value(load))
        + _wire(120, 440, 960, 440)
        + _ground(690, 440)
    )
    return _circuit_shell(
        case_id,
        "Simplified buck-like converter",
        "A scheduled switch transfers energy through an inductor while a diode provides a freewheel path.",
        diagram,
        note="Reduced-order numerical experiment, not a production device model.",
    )


def _h_bridge_circuit_svg() -> bytes:
    case_id = "h_bridge_rl"
    source = _element(case_id, "VDC")
    left_high = _element(case_id, "S_LEFT_HIGH")
    left_low = _element(case_id, "S_LEFT_LOW")
    right_high = _element(case_id, "S_RIGHT_HIGH")
    right_low = _element(case_id, "S_RIGHT_LOW")
    resistor = _element(case_id, "R_LOAD")
    inductor = _element(case_id, "L_LOAD")
    diagram = (
        _voltage_source_v(125, 190, 455, "VDC", _component_value(source))
        + _wire(125, 190, 950, 190)
        + _wire(125, 455, 950, 455)
        + _switch_v(350, 190, 300, "S_LEFT_HIGH", _component_value(left_high), side="left")
        + _switch_v(350, 345, 455, "S_LEFT_LOW", _component_value(left_low), side="left")
        + _switch_v(875, 190, 300, "S_RIGHT_HIGH", _component_value(right_high))
        + _switch_v(875, 345, 455, "S_RIGHT_LOW", _component_value(right_low))
        + _wire(350, 300, 350, 345)
        + _wire(875, 300, 875, 345)
        + _node(350, 322, "left")
        + _node(875, 322, "right")
        + _wire(350, 322, 440, 322)
        + _resistor_h(440, 625, 322, "R_LOAD", _component_value(resistor))
        + _inductor_h(625, 810, 322, "L_LOAD", _component_value(inductor))
        + _wire(810, 322, 875, 322)
        + _ground(610, 455)
    )
    return _circuit_shell(
        case_id,
        "Scheduled H-bridge RL load",
        "Four scheduled resistive switches apply positive and negative voltage across a series RL load.",
        diagram,
        note="Reduced-order numerical experiment with explicit dead time; no body-diode or shoot-through model.",
    )


def _dc_link_circuit_svg() -> bytes:
    case_id = "dc_link_rlc"
    source = _element(case_id, "VDC")
    switch = _element(case_id, "S_CONNECT")
    series = _element(case_id, "R_SERIES")
    diode = _element(case_id, "D_FREE")
    bleed = _element(case_id, "R_PRELINK_BLEED")
    inductor = _element(case_id, "L_LINK")
    capacitor = _element(case_id, "C_LINK")
    load = _element(case_id, "R_LOAD")
    diagram = (
        _voltage_source_v(105, 220, 440, "VDC", _component_value(source))
        + _wire(105, 220, 175, 220)
        + _switch_h(175, 330, 220, "S_CONNECT", _component_value(switch))
        + _resistor_h(330, 485, 220, "R_SERIES", _component_value(series))
        + _wire(485, 220, 540, 220)
        + _node(540, 220, "prelink")
        + _inductor_h(540, 735, 220, "L_LINK", _component_value(inductor))
        + _wire(735, 220, 1000, 220)
        + _node(820, 220, "dc_link")
        + _diode_v(465, 220, 440, "D_FREE", _component_value(diode), side="left")
        + _resistor_v(590, 220, 440, "R_PRELINK_BLEED", _component_value(bleed))
        + _capacitor_v(810, 220, 440, "C_LINK", _component_value(capacitor), side="right")
        + _resistor_v(970, 220, 440, "R_LOAD", _component_value(load))
        + _wire(105, 440, 1000, 440)
        + _ground(735, 440)
    )
    return _circuit_shell(
        case_id,
        "DC-link RLC startup and interruption",
        "A scheduled connection drives a series RL path into a capacitor and resistive load with a freewheel path.",
        diagram,
        note="Reduced-order numerical experiment, not a contactor, fault, protection, or production device model.",
    )


def _decimate(points: Sequence[tuple[float, float]], maximum: int = 420) -> tuple[tuple[float, float], ...]:
    if len(points) <= maximum:
        return tuple(points)
    indices = {
        round(index * (len(points) - 1) / (maximum - 1))
        for index in range(maximum)
    }
    return tuple(points[index] for index in sorted(indices))


def _time_axis(start: float, stop: float) -> tuple[float, str]:
    span = abs(stop - start)
    if span < 1.0e-6:
        return 1.0e9, "ns"
    if span < 1.0e-3:
        return 1.0e6, "µs"
    if span < 1.0:
        return 1.0e3, "ms"
    return 1.0, "s"


def _tick(value: float) -> str:
    if value == 0.0:
        return "0"
    if abs(value) >= 1.0e4 or abs(value) < 1.0e-3:
        return f"{value:.2e}"
    return f"{value:.4g}"


def _expanded_range(values: Iterable[float]) -> tuple[float, float]:
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return -1.0, 1.0
    minimum = min(finite)
    maximum = max(finite)
    if minimum == maximum:
        padding = max(abs(minimum) * 0.08, 0.5)
    else:
        padding = 0.08 * (maximum - minimum)
    return minimum - padding, maximum + padding


def _case_plot_svg(
    case_id: str,
    title: str,
    description: str,
    panels: Sequence[tuple[str, str, Sequence[tuple[str, Sequence[tuple[float, float]]]]]],
    *,
    event_times: Sequence[float] = (),
    claim_note: str = "",
) -> bytes:
    _, simulation, config, result = _case_execution(case_id)
    width = 1200
    top = 160
    panel_height = 220
    panel_gap = 64
    last_panel_bottom = top + len(panels) * panel_height + max(0, len(panels) - 1) * panel_gap
    footer_y = last_panel_bottom + 86
    event_footer_y = footer_y + 26 if event_times else None
    claim_footer_y = footer_y + 26 * (bool(event_times) + 1) if claim_note else None
    final_footer_y = claim_footer_y or event_footer_y or footer_y
    height = final_footer_y + 28
    plot_left = 112
    plot_right = 1138
    start = float(simulation["start_time"])
    stop = float(simulation["stop_time"])
    time_factor, time_unit = _time_axis(start, stop)
    body = [f'  <rect width="{width}" height="{height}" rx="28" fill="#f5f8fb"/>']
    body.append(_text(64, 58, title, "title"))
    body.append(_text(64, 96, description, "subtitle"))
    body.append(_text(64, 124, "ACCEPTED BAB-CS SIMULATION POINTS", "section"))

    for panel_index, (panel_label, unit, traces) in enumerate(panels):
        panel_top = top + panel_index * (panel_height + panel_gap)
        panel_bottom = panel_top + panel_height
        values = [value for _, points in traces for _, value in points]
        y_minimum, y_maximum = _expanded_range(values)
        y_span = max(y_maximum - y_minimum, 1.0e-30)
        body.append(f'  <rect class="card" x="52" y="{panel_top-28:g}" width="1096" height="{panel_height+58:g}" rx="18"/>')
        body.append(_text(plot_left, panel_top - 4, panel_label, "label"))
        body.append(_text(plot_right, panel_top - 4, unit, "micro", anchor="end"))

        for tick_index in range(5):
            fraction = tick_index / 4
            y = panel_bottom - fraction * panel_height
            value = y_minimum + fraction * y_span
            body.append(f'  <path class="grid" d="M{plot_left:g} {y:g} H{plot_right:g}"/>')
            body.append(_text(plot_left - 13, y + 4, _tick(value), "micro", anchor="end"))
        for tick_index in range(6):
            fraction = tick_index / 5
            x = plot_left + fraction * (plot_right - plot_left)
            time_value = start + fraction * (stop - start)
            body.append(f'  <path class="grid" d="M{x:g} {panel_top:g} V{panel_bottom:g}"/>')
            body.append(_text(x, panel_bottom + 22, _tick(time_value * time_factor), "micro", anchor="middle"))
        body.append(_text((plot_left + plot_right) / 2, panel_bottom + 43, f"time ({time_unit})", "small", anchor="middle"))

        for event_time in sorted(set(event_times)):
            if start <= event_time <= stop:
                x = plot_left + (event_time - start) / max(stop - start, 1.0e-30) * (plot_right - plot_left)
                body.append(f'  <path class="event" d="M{x:.3f} {panel_top:g} V{panel_bottom:g}"/>')

        for trace_index, (name, points) in enumerate(traces):
            color = TRACE_COLORS[trace_index % len(TRACE_COLORS)]
            coordinates = []
            for time_value, value in _decimate(points):
                x = plot_left + (time_value - start) / max(stop - start, 1.0e-30) * (plot_right - plot_left)
                y = panel_bottom - (value - y_minimum) / y_span * panel_height
                coordinates.append((x, y))
            if coordinates:
                path = " ".join(
                    ("M" if index == 0 else "L") + f"{x:.3f} {y:.3f}"
                    for index, (x, y) in enumerate(coordinates)
                )
                body.append(f'  <path class="plot" stroke="{color}" d="{path}"/>')
            legend_x = plot_left + trace_index * 235
            body.append(f'  <path d="M{legend_x:g} {panel_top+18:g} H{legend_x+28:g}" stroke="{color}" stroke-width="4"/>')
            body.append(_text(legend_x + 36, panel_top + 23, name, "small"))

    relative = CASE_PATHS[case_id].as_posix()
    method = config.candidate_method if config.rollout_mode != "disabled" else config.reference_method
    body.append(
        f'  <text class="mono micro" x="64" y="{footer_y}">SOURCE {html.escape(relative)} · INPUT SHA-256 {_case_sha256(case_id)[:16]} · METHOD {html.escape(method)} · NOMINAL STEP {simulation["nominal_step"]:.8g} s · ACCEPTED POINTS {len(result.points)}</text>'
    )
    if event_footer_y is not None:
        body.append(_text(64, event_footer_y, "orange rules = accepted event boundaries", "micro"))
    if claim_footer_y is not None:
        body.append(_text(64, claim_footer_y, claim_note, "small"))
    return _svg_document(
        title,
        f"{description} Result generated from {relative}, SHA-256 {_case_sha256(case_id)}.",
        "\n".join(body),
        width=width,
        height=height,
    )


def _node_difference(result, positive: str, negative: str) -> tuple[tuple[float, float], ...]:
    return tuple(
        (
            point.time,
            point.state.evaluation.algebraic.node_voltages[positive]
            - point.state.evaluation.algebraic.node_voltages[negative],
        )
        for point in result.points
    )


def _case_result_svg(case_id: str) -> bytes:
    circuit, _, _, result = _case_execution(case_id)
    events = tuple(point.time for point in result.points if point.event_boundary)
    if case_id == "rc_step":
        return _case_plot_svg(
            case_id,
            "RC step simulation result",
            "The accepted capacitor voltage rises toward the declared one-volt source.",
            (("Capacitor voltage v(C1)", "V", (("accepted v(C1)", result.dynamic_trace(0)),)),),
        )
    if case_id == "rl_step":
        return _case_plot_svg(
            case_id,
            "RL step simulation result",
            "The accepted inductor current rises continuously toward the declared steady current.",
            (("Inductor current i(L1)", "A", (("accepted i(L1)", result.dynamic_trace(0)),)),),
        )
    if case_id == "rlc_damped":
        return _case_plot_svg(
            case_id,
            "Damped RLC simulation result",
            "Voltage and current oscillate while the declared resistor dissipates stored energy.",
            (
                ("Capacitor voltage v(C1)", "V", (("accepted v(C1)", result.dynamic_trace(0)),)),
                ("Inductor current i(L1)", "A", (("accepted i(L1)", result.dynamic_trace(1)),)),
            ),
        )
    if case_id == "lc_long":
        return _case_plot_svg(
            case_id,
            "Lossless LC long-horizon result",
            "Voltage and current exchange energy over ten declared oscillation periods.",
            (
                ("Capacitor voltage v(C1)", "V", (("accepted v(C1)", result.dynamic_trace(0)),)),
                ("Inductor current i(L1)", "A", (("accepted i(L1)", result.dynamic_trace(1)),)),
            ),
            claim_note="The graph is a numerical trajectory; phase and stored-energy error are evaluated separately.",
        )
    if case_id == "diode_clip":
        return _case_plot_svg(
            case_id,
            "Diode-clip simulation result",
            "The nonlinear output departs from the sinusoidal input when the diode conducts.",
            (
                (
                    "Input and clipped output",
                    "V",
                    (
                        ("input v(vin)", result.node_trace("vin")),
                        ("accepted v(out)", result.node_trace("out")),
                    ),
                ),
            ),
        )
    if case_id == "switched_rc":
        control = tuple((point.time, circuit.switches[0].control.value(point.time)) for point in result.points)
        return _case_plot_svg(
            case_id,
            "Switched RC simulation result",
            "Exact pulse boundaries align the accepted capacitor voltage with repeated discharge intervals.",
            (
                ("Capacitor voltage v(C1)", "V", (("accepted v(C1)", result.dynamic_trace(0)),)),
                ("Switch command", "command", (("S1 control", control),)),
            ),
            event_times=events,
        )
    if case_id == "buck_like":
        return _case_plot_svg(
            case_id,
            "Simplified buck-like simulation result",
            "The accepted output voltage and inductor current show scheduled energy transfer and ripple.",
            (
                ("Output capacitor voltage v(C_OUT)", "V", (("accepted v(C_OUT)", result.dynamic_trace(0)),)),
                ("Output inductor current i(L_OUT)", "A", (("accepted i(L_OUT)", result.dynamic_trace(1)),)),
            ),
            event_times=events,
            claim_note="Reduced-order numerical experiment, not measured production-device behavior.",
        )
    if case_id == "h_bridge_rl":
        return _case_plot_svg(
            case_id,
            "Scheduled H-bridge RL simulation result",
            "The bridge applies positive and negative load voltage with explicit dead-time intervals while current remains continuous.",
            (
                ("Bridge load voltage v(left)-v(right)", "V", (("accepted load voltage", _node_difference(result, "left", "right")),)),
                ("Load inductor current i(L_LOAD)", "A", (("accepted i(L_LOAD)", result.dynamic_trace(0)),)),
            ),
            event_times=events,
            claim_note="Reduced-order numerical experiment; body-diode, shoot-through, and switching-loss physics are omitted.",
        )
    if case_id == "dc_link_rlc":
        return _case_plot_svg(
            case_id,
            "DC-link startup and interruption result",
            "The accepted link voltage rises after connection and the inductor current decays after scheduled interruption.",
            (
                ("DC-link capacitor voltage v(C_LINK)", "V", (("accepted v(C_LINK)", result.dynamic_trace(0)),)),
                ("Link inductor current i(L_LINK)", "A", (("accepted i(L_LINK)", result.dynamic_trace(1)),)),
            ),
            event_times=events,
            claim_note="Reduced-order numerical experiment, not a contactor, protection, or fault model.",
        )
    raise ValueError(f"unsupported documentation result case: {case_id}")


@lru_cache(maxsize=1)
def _observatory_rows() -> tuple[dict[str, Any], ...]:
    report, _ = execute_observatory(selected_cases={"rc_step"}, quick=True)
    maximum_step = max(float(row["nominal_step"]) for row in report["results"])
    rows = [
        row
        for row in report["results"]
        if row["status"] == "success" and float(row["nominal_step"]) == maximum_step
    ]
    return tuple(sorted(rows, key=lambda row: str(row["method"])))


def _observatory_accuracy_work_svg() -> bytes:
    rows = _observatory_rows()
    width = 1200
    height = 760
    left, right, top, bottom = 125, 1125, 160, 590
    work_values = [math.log10(float(row["work"]["deterministic_work_units"])) for row in rows]
    error_values = [math.log10(max(float(row["accuracy"]["maximum_absolute_error"]), 1.0e-300)) for row in rows]
    x_minimum, x_maximum = _expanded_range(work_values)
    y_minimum, y_maximum = _expanded_range(error_values)
    body = [f'  <rect width="{width}" height="{height}" rx="28" fill="#f5f8fb"/>']
    body.append(_text(64, 58, "Method Observatory: accuracy versus deterministic work", "title"))
    body.append(_text(64, 96, "Seven bounded candidate profiles on the same declared RC fixed-step configuration.", "subtitle"))
    body.append(_text(64, 124, "REPRESENTATIVE FIXED-STEP VIEW · NOT A UNIVERSAL METHOD RANKING", "section"))
    body.append(f'  <rect class="card" x="52" y="140" width="1096" height="570" rx="20"/>')
    for index in range(6):
        fraction = index / 5
        x = left + fraction * (right - left)
        x_value = x_minimum + fraction * (x_maximum - x_minimum)
        y = bottom - fraction * (bottom - top)
        y_value = y_minimum + fraction * (y_maximum - y_minimum)
        body.append(f'  <path class="grid" d="M{x:g} {top:g} V{bottom:g}"/>')
        body.append(f'  <path class="grid" d="M{left:g} {y:g} H{right:g}"/>')
        body.append(_text(x, bottom + 24, f"{x_value:.2f}", "micro", anchor="middle"))
        body.append(_text(left - 14, y + 4, f"{y_value:.2f}", "micro", anchor="end"))
    body.append(_text((left + right) / 2, bottom + 52, "log10 work units", "small", anchor="middle"))
    body.append(_rotated_text(38, (top + bottom) / 2, "log10 maximum authority error"))
    for index, row in enumerate(rows):
        x_value = math.log10(float(row["work"]["deterministic_work_units"]))
        y_value = math.log10(max(float(row["accuracy"]["maximum_absolute_error"]), 1.0e-300))
        x = left + (x_value - x_minimum) / (x_maximum - x_minimum) * (right - left)
        y = bottom - (y_value - y_minimum) / (y_maximum - y_minimum) * (bottom - top)
        color = TRACE_COLORS[index % len(TRACE_COLORS)]
        method = str(row["method"]).removeprefix("candidate_").replace("_", " ")
        body.append(f'  <circle cx="{x:.3f}" cy="{y:.3f}" r="9" fill="{color}" stroke="#fff" stroke-width="3"><title>{html.escape(method)} · work {row["work"]["deterministic_work_units"]} · error {row["accuracy"]["maximum_absolute_error"]:.6g}</title></circle>')
        label_y = 674 + (index // 4) * 24
        label_x = 70 + (index % 4) * 270
        body.append(f'  <circle cx="{label_x:g}" cy="{label_y-4:g}" r="5" fill="{color}"/>')
        body.append(_text(label_x + 13, label_y, method, "small"))
    return _svg_document(
        "Method Observatory accuracy versus deterministic work",
        "A representative fixed-step RC scatter plot for all seven bounded candidate profiles. Each point shows maximum authority error and deterministic work from a measured simulation row.",
        "\n".join(body),
        width=width,
        height=height,
    )


def _scaled_error(left: Sequence[float], right: Sequence[float], config) -> float:
    difference = [left_value - right_value for left_value, right_value in zip(left, right, strict=True)]
    return weighted_rms(
        difference,
        left,
        right,
        config.absolute_tolerance,
        config.relative_tolerance,
    )


def _rc_authority(time: float) -> tuple[float, ...]:
    return (
        _rc_voltage(
            time,
            resistance=1000.0,
            capacitance=1.0e-6,
            source_voltage=1.0,
            initial_voltage=0.0,
        ),
    )


def _lc_authority(time: float) -> tuple[float, ...]:
    return _parallel_rlc_state(
        time,
        resistance=math.inf,
        capacitance=1.0e-6,
        inductance=1.0e-3,
        initial_voltage=1.0,
        initial_current=0.0,
    )


def _bound_coverage_svg() -> bytes:
    _, _, config, result = _case_execution("rc_step")
    actual = []
    bound = []
    for point in result.points[1:]:
        metrics = point.metrics
        assert metrics is not None
        actual.append((point.time, math.log10(max(_scaled_error(point.state.evaluation.dynamic_state, _rc_authority(point.time), config), 1.0e-12))))
        bound.append((point.time, math.log10(max(metrics.estimated_bound, 1.0e-12))))
    return _case_plot_svg(
        "rc_step",
        "Bound Coverage Atlas: authority error and recursive bound",
        "The representative RC view compares weighted authority error with the accepted recursive internal bound.",
        (("Scaled error and bound", "log10 weighted RMS", (("actual authority error", actual), ("recursive internal bound", bound))),),
        claim_note="Coverage on measured samples is characterization evidence, not a formal enclosure theorem.",
    )


def _age_bucket(age: int) -> str:
    if age <= 3:
        return "0-3"
    if age <= 7:
        return "4-7"
    if age <= 15:
        return "8-15"
    return "16+"


def _coverage_by_age_svg() -> bytes:
    _, _, config, result = _case_execution("lc_long")
    initial_candidate = result.points[0].state.evaluation.dynamic_state
    initial_authority = _lc_authority(result.points[0].time)
    epoch_candidate = initial_candidate
    epoch_authority = initial_authority
    age = 0
    totals: Counter[str] = Counter()
    covered: Counter[str] = Counter()
    for point in result.points[1:]:
        metrics = point.metrics
        assert metrics is not None
        authority = _lc_authority(point.time)
        age += 1
        candidate_delta = tuple(value - anchor for value, anchor in zip(point.state.evaluation.dynamic_state, epoch_candidate, strict=True))
        authority_delta = tuple(value - anchor for value, anchor in zip(authority, epoch_authority, strict=True))
        error = _scaled_error(candidate_delta, authority_delta, config)
        eligible = math.isfinite(metrics.estimated_bound) and metrics.estimated_bound > 0.0 and not metrics.periodic_reanchor and not point.event_boundary
        if eligible:
            bucket = _age_bucket(age)
            totals[bucket] += 1
            covered[bucket] += int(error <= metrics.estimated_bound)
        if metrics.periodic_reanchor:
            epoch_candidate = point.state.evaluation.dynamic_state
            epoch_authority = authority
            age = 0
    values = [(bucket, covered[bucket] / totals[bucket] if totals[bucket] else 0.0, totals[bucket]) for bucket in ("0-3", "4-7", "8-15", "16+")]
    return _bar_svg(
        "Bound Coverage Atlas: empirical coverage by authority age",
        "Lossless LC eligible samples grouped by the number of accepted steps since independent replay authority was refreshed.",
        values,
        y_label="empirical coverage fraction",
        maximum=1.0,
        footer="Representative lc_long accepted samples · coverage excludes anchors, events, zero bounds, and non-finite values.",
    )


def _phase_energy_svg() -> bytes:
    circuit, _, config, result = _case_execution("lc_long")
    phase = []
    energy = []
    scale = math.sqrt(1.0e-3 / 1.0e-6)
    for point in result.points:
        candidate = point.state.evaluation.dynamic_state
        authority = _lc_authority(point.time)
        candidate_phase = math.atan2(candidate[1] * scale, candidate[0])
        authority_phase = math.atan2(authority[1] * scale, authority[0])
        phase_error = abs(math.atan2(math.sin(candidate_phase - authority_phase), math.cos(candidate_phase - authority_phase)))
        authority_evaluation = circuit.evaluate(point.time, authority)
        energy_scale = max(abs(authority_evaluation.stored_energy), config.energy_absolute_tolerance)
        relative_energy_error = (point.state.evaluation.stored_energy - authority_evaluation.stored_energy) / energy_scale
        phase.append((point.time, phase_error))
        energy.append((point.time, relative_energy_error))
    return _case_plot_svg(
        "lc_long",
        "Bound Coverage Atlas: phase and energy remain separate",
        "The lossless LC trajectory reports timing displacement and stored-energy drift as different engineering quantities.",
        (
            ("Absolute phase error", "rad", (("phase error", phase),)),
            ("Relative stored-energy error", "ratio", (("relative energy error", energy),)),
        ),
        claim_note="A small energy error does not imply a small phase error, and the reverse is also not guaranteed.",
    )


def _bar_svg(
    title: str,
    description: str,
    values: Sequence[tuple[str, float, int]],
    *,
    y_label: str,
    maximum: float | None = None,
    footer: str,
) -> bytes:
    width = 1200
    height = 680
    left, right, top, bottom = 135, 1120, 158, 545
    maximum_value = maximum if maximum is not None else max((value for _, value, _ in values), default=1.0)
    maximum_value = max(maximum_value, 1.0e-12)
    body = [f'  <rect width="{width}" height="{height}" rx="28" fill="#f5f8fb"/>']
    body.append(_text(64, 58, title, "title"))
    body.append(_text(64, 96, description, "subtitle"))
    body.append(f'  <rect class="card" x="52" y="134" width="1096" height="442" rx="20"/>')
    for index in range(6):
        fraction = index / 5
        y = bottom - fraction * (bottom - top)
        body.append(f'  <path class="grid" d="M{left:g} {y:g} H{right:g}"/>')
        body.append(_text(left - 14, y + 4, _tick(fraction * maximum_value), "micro", anchor="end"))
    slot = (right - left) / max(len(values), 1)
    bar_width = min(120.0, slot * 0.58)
    for index, (label, value, sample_count) in enumerate(values):
        x = left + slot * (index + 0.5)
        height_value = value / maximum_value * (bottom - top)
        body.append(f'  <rect x="{x-bar_width/2:.3f}" y="{bottom-height_value:.3f}" width="{bar_width:.3f}" height="{height_value:.3f}" rx="10" fill="{TRACE_COLORS[index % len(TRACE_COLORS)]}"/>')
        body.append(_text(x, bottom + 28, label.replace("_", " "), "small", anchor="middle"))
        body.append(_text(x, bottom - height_value - 13, f"{value:.3g}", "label", anchor="middle"))
        body.append(_text(x, bottom + 56, f"n={sample_count}", "micro", anchor="middle"))
    body.append(_rotated_text(38, (top + bottom) / 2, y_label))
    body.append(_text(64, 630, footer, "small"))
    return _svg_document(title, description, "\n".join(body), width=width, height=height)


def _rejection_causes_svg() -> bytes:
    _, _, _, result = _case_execution("h_bridge_rl")
    causes: Counter[str] = Counter()
    for point in result.points:
        for rejection in point.rejections:
            causes[_classify_reason(rejection.reason)] += 1
        if point.metrics is not None and "fallback" in point.metrics.method:
            causes["implicit_fallback"] += 1
    values = [(reason, float(count), count) for reason, count in sorted(causes.items())]
    if not values:
        values = [("none_observed", 0.0, 0)]
    return _bar_svg(
        "Bound Coverage Atlas: rejection and fallback causes",
        "Classified causes observed in the scheduled H-bridge reduced-order numerical experiment.",
        values,
        y_label="observed cause count",
        footer="Exact raw rejection messages remain in numerical evidence; this view groups them by the canonical reason taxonomy.",
    )


def render_figure_assets() -> dict[str, bytes]:
    assets = {
        "circuit-rc-step.svg": _rc_circuit_svg(),
        "result-rc-step.svg": _case_result_svg("rc_step"),
        "circuit-rl-step.svg": _rl_circuit_svg(),
        "result-rl-step.svg": _case_result_svg("rl_step"),
        "circuit-rlc-damped.svg": _parallel_tank_svg("rlc_damped", damped=True),
        "result-rlc-damped.svg": _case_result_svg("rlc_damped"),
        "circuit-lc-long.svg": _parallel_tank_svg("lc_long", damped=False),
        "result-lc-long.svg": _case_result_svg("lc_long"),
        "circuit-diode-clip.svg": _diode_clip_circuit_svg(),
        "result-diode-clip.svg": _case_result_svg("diode_clip"),
        "circuit-switched-rc.svg": _switched_rc_circuit_svg(),
        "result-switched-rc.svg": _case_result_svg("switched_rc"),
        "circuit-buck-like.svg": _buck_circuit_svg(),
        "result-buck-like.svg": _case_result_svg("buck_like"),
        "circuit-h-bridge-rl.svg": _h_bridge_circuit_svg(),
        "result-h-bridge-rl.svg": _case_result_svg("h_bridge_rl"),
        "circuit-dc-link-rlc.svg": _dc_link_circuit_svg(),
        "result-dc-link-rlc.svg": _case_result_svg("dc_link_rlc"),
        "result-observatory-accuracy-work.svg": _observatory_accuracy_work_svg(),
        "result-bound-coverage.svg": _bound_coverage_svg(),
        "result-coverage-by-age.svg": _coverage_by_age_svg(),
        "result-phase-energy.svg": _phase_energy_svg(),
        "result-rejection-causes.svg": _rejection_causes_svg(),
    }
    if tuple(assets) != FIGURE_ASSET_NAMES:
        raise AssertionError("documentation figure inventory order drifted")
    return assets
