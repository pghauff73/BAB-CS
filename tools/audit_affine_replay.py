"""Offline certificates for actual BAB-CS scalar RC and switched-RC traces.

Instrumentation uses temporary process-local wrappers and must run in an
isolated, single-threaded process. It does not alter production algorithms.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "src"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from babcs import bounded, integrators
from babcs.bounded import BoundedIntegrator
from babcs.io import load_case
from babcs.model import Capacitor, Resistor, Switch, VoltageSource
from babcs.simulator import Simulator
from babcs.waveforms import Constant, Pulse
from tools.affine_research import Metric, certify_segment
from tools.replay_error_budget import ceil_grid, exp_bounds, growth_factors


def q(value: float) -> F:
    return F.from_float(float(value))


@dataclass(frozen=True)
class ScalarRC:
    resistance: F
    capacitance: F
    voltage: F
    initial: F
    state_name: str
    node_name: str
    on: F = F(0)
    off: F = F(0)
    delay: F | None = None
    width: F = F(0)
    period: F = F(0)

    @classmethod
    def from_circuit(cls, circuit) -> ScalarRC:
        capacitors = [e for e in circuit.elements if type(e) is Capacitor]
        resistors = [e for e in circuit.elements if type(e) is Resistor]
        sources = [e for e in circuit.elements if type(e) is VoltageSource]
        switches = [e for e in circuit.elements if type(e) is Switch]
        if (len(capacitors), len(resistors), len(sources)) != (1, 1, 1) or len(switches) > 1:
            raise ValueError("requires exactly one capacitor, resistor, DC source and at most one switch")
        if len(circuit.elements) != 3 + len(switches):
            raise ValueError("unsupported additional device in affine reduction")
        c, r, v = capacitors[0], resistors[0], sources[0]
        if c.negative != "0" or v.negative != "0" or type(v.waveform) is not Constant:
            raise ValueError("requires grounded positive capacitor and constant voltage source")
        if r.negative != c.positive or len(circuit.dynamic_names) != 1:
            raise ValueError("unsupported state order or RC orientation")
        if min(c.capacitance, r.resistance) <= 0:
            raise ValueError("passive positive R and C required")
        arguments = dict(resistance=q(r.resistance), capacitance=q(c.capacitance),
                         voltage=q(v.waveform.level), initial=q(c.initial_voltage),
                         state_name=circuit.dynamic_names[0], node_name=c.positive)
        if not switches:
            if r.positive != v.positive:
                raise ValueError("resistor must connect source to capacitor")
            return cls(**arguments)
        s = switches[0]
        if s.positive != v.positive or s.negative != r.positive:
            raise ValueError("switch must be in series between source and resistor")
        control = s.control
        if type(control) is not Pulse or control.rise != 0 or control.fall != 0:
            raise ValueError("only instantaneous pulse-controlled switches supported")
        if not control.low < s.threshold < control.high or min(s.on_resistance, s.off_resistance) <= 0:
            raise ValueError("requires positive switch resistance and strict pulse threshold")
        return cls(**arguments, on=q(s.on_resistance), off=q(s.off_resistance),
                   delay=q(control.delay), width=q(control.width), period=q(control.period))

    def coefficients(self, time: F):
        resistance = self.resistance
        if self.delay is not None:
            local = time - self.delay
            if local >= 0 and self.period > 0:
                local %= self.period
            active = local >= 0 and local < self.width
            resistance += self.on if active else self.off
        rate = 1 / (resistance * self.capacitance)
        return ((-rate,),), (rate*self.voltage,)

    def events(self, start: F, stop: F) -> list[F]:
        if self.delay is None:
            return []
        events = []
        cycle = 0
        while True:
            begin = self.delay + cycle*self.period
            if begin > stop:
                break
            for point in (begin, begin+self.width):
                if start < point < stop:
                    events.append(point)
            if self.period == 0:
                break
            cycle += 1
            if cycle > 100000:
                raise ValueError("event schedule budget exceeded")
        return sorted(set(events))

    def data(self) -> dict:
        return {key: str(value) if isinstance(value, F) else value for key, value in asdict(self).items()}


def evaluation_point(evaluation):
    if len(evaluation.dynamic_state) != 1:
        raise ValueError("scalar trace required")
    return q(evaluation.time), q(evaluation.dynamic_state[0])


def append_point(points, evaluation):
    point = evaluation_point(evaluation)
    if points and point == points[-1]:
        return
    if points and point[0] < points[-1][0]:
        if point[1] != points[-1][1]:
            raise ValueError("unsupported replay time reversal with changed state")
        # Exact-target reprojection can retime an identical state by an ulp.
        points[-1] = point
        return
    points.append(point)


@contextmanager
def captured_replays():
    windows = []
    original_window = bounded.integrate_reference_window_with_stats
    original_step = integrators.implicit_step
    active = []

    def step(*args, **kwargs):
        result = original_step(*args, **kwargs)
        if active:
            append_point(active[-1]["points"], args[2])
            append_point(active[-1]["points"], result.evaluation)
        return result

    def window(*args, **kwargs):
        record = {"points": [evaluation_point(args[1])], "status": "running"}
        active.append(record)
        try:
            result = original_window(*args, **kwargs)
            append_point(record["points"], result.evaluations[-1])
            record.update(status="completed", steps=result.steps,
                          circuit_evaluations=result.circuit_evaluations,
                          method=kwargs.get("method", "trapezoidal"))
            return result
        except Exception:
            record["status"] = "failed"
            raise
        finally:
            active.pop()
            windows.append(record)

    with patch.object(bounded, "integrate_reference_window_with_stats", window), patch.object(integrators, "implicit_step", step):
        yield windows


def trace_digest(result) -> str:
    rows = [{"time": p.time.hex(), "state": [v.hex() for v in p.state.evaluation.dynamic_state],
             "metrics": asdict(p.metrics) if p.metrics else None,
             "events": getattr(p, "event_sources", ()), "rejections": p.rejection_reasons}
            for p in result.points]
    return hashlib.sha256(json.dumps(rows, sort_keys=True, allow_nan=False).encode()).hexdigest()


def audit_path(model: ScalarRC, points: list[tuple[F, F]], radius: F,
               *, keep_segments: bool = True) -> dict:
    inherited, fresh, full = radius, F(0), radius
    records = []
    count = jumps = 0
    if not points:
        raise ValueError("empty trace")
    for (t0, x0), (t1, x1) in zip(points, points[1:]):
        if t1 < t0:
            raise ValueError("nonmonotone replay trace")
        if t1 == t0:
            fresh = ceil_grid(fresh + abs(x1-x0))
            radius = inherited+fresh
            full = max(full, radius)
            jumps += 1
            continue
        boundaries = [t0, *model.events(t0, t1), t1]
        for left, right in zip(boundaries, boundaries[1:]):
            a, b = model.coefficients((left+right)/2)
            metric = Metric.infinity(a)
            # Split long spans to meet the proved rational exponential domain.
            z = abs(metric.mu*(right-left))
            subdivisions = max(1, -((-2*z.numerator)//z.denominator))
            for k in range(subdivisions):
                lo = left + (right-left)*k/subdivisions
                hi = left + (right-left)*(k+1)/subdivisions
                y0 = x0 + (x1-x0)*(lo-t0)/(t1-t0)
                y1 = x0 + (x1-x0)*(hi-t0)/(t1-t0)
                cert = certify_segment(a, b, (y0,), (y1,), hi-lo, inherited+fresh, metric)
                growth, integral = growth_factors(metric.mu, hi-lo)
                inherited = ceil_grid(growth*inherited)
                fresh = ceil_grid(growth*fresh + integral*cert.defect)
                radius = inherited+fresh
                full = max(full, cert.full_radius, radius)
                count += 1
                if keep_segments:
                    records.append({"start_time": str(lo), "end_time": str(hi),
                                    "start_state": str(y0), "end_state": str(y1),
                                    "matrix": [[str(a[0][0])]], "offset": [str(b[0])],
                                    "certificate": cert.data()})
    return {"endpoint_radius": str(inherited+fresh), "inherited_anchor_radius": str(inherited),
            "fresh_path_defect_radius": str(fresh), "full_path_radius": str(full),
            "certificate_segments": count, "zero_time_state_jumps": jumps,
            "segments": records}


def exact_scalar_enclosure(model: ScalarRC, time: F, start: F) -> tuple[F, F]:
    lower = upper = model.initial
    boundaries = [start, *model.events(start, time), time]
    for left, right in zip(boundaries, boundaries[1:]):
        a, _ = model.coefficients((left+right)/2)
        z = a[0][0]*(right-left)
        subdivisions = max(1, -((-abs(z).numerator)//abs(z).denominator))
        for _ in range(subdivisions):
            gl, gu = exp_bounds(z/subdivisions)
            delta = (lower-model.voltage, upper-model.voltage)
            products = [g*v for g in (gl, gu) for v in delta]
            lower = -ceil_grid(-(model.voltage+min(products)))
            upper = ceil_grid(model.voltage+max(products))
    return lower, upper


def audit_case(path: Path, *, initial_radius: F = F(0), verify_observation: bool = True) -> dict:
    if initial_radius < 0:
        raise ValueError("negative initial radius")
    circuit, simulation, config = load_case(path)
    if simulation["start_time"] != 0:
        raise ValueError("initial-state mapping currently requires start_time=0")
    model = ScalarRC.from_circuit(circuit)
    with captured_replays() as windows:
        result = Simulator(BoundedIntegrator(config)).run(circuit, **simulation)
    observed_digest = trace_digest(result)
    if verify_observation:
        plain_circuit, plain_simulation, plain_config = load_case(path)
        plain = Simulator(BoundedIntegrator(plain_config)).run(plain_circuit, **plain_simulation)
        if trace_digest(plain) != observed_digest:
            raise RuntimeError("instrumentation changed production numerical evidence")
    radius = initial_radius
    first = evaluation_point(result.points[0].state.evaluation)
    if first[1] != model.initial:
        radius = ceil_grid(radius+abs(first[1]-model.initial))
    radii = {first: radius}
    records = []
    window_cache = {}
    selected_windows = set()
    endpoint_index = {}
    for index, window in enumerate(windows):
        if window["status"] == "completed":
            endpoint_index[window["points"][-1]] = index
    previous = first
    for point in result.points[1:]:
        current = evaluation_point(point.state.evaluation)
        direct = audit_path(model, [previous, current], radius)
        direct_radius = F(direct["endpoint_radius"])
        replay = None
        metrics = point.metrics
        if metrics is not None and (metrics.periodic_reanchor or getattr(metrics, "event_authority_check", False)):
            if current not in endpoint_index:
                raise RuntimeError("accepted replay endpoint has no captured trace")
            index = endpoint_index[current]
            window = windows[index]
            start_point = window["points"][0]
            if start_point not in radii:
                raise RuntimeError("captured replay anchor lacks an established error radius")
            replay = audit_path(model, window["points"], radii[start_point])
            replay["window_index"] = index
            replay["anchor_time"] = str(start_point[0])
            replay["anchor_state"] = str(start_point[1])
            window_cache[index] = replay
            selected_windows.add(index)
            radius = min(direct_radius, F(replay["endpoint_radius"]))
        else:
            radius = direct_radius
        truth_lower, truth_upper = exact_scalar_enclosure(model, current[0], first[0])
        # This independent closed-form enclosure verifies the nominal initial
        # state only. The theorem additionally covers the declared initial ball.
        error_upper = max(abs(current[1]-truth_lower), abs(current[1]-truth_upper))
        internal = metrics.estimated_bound if metrics else None
        records.append({"time": str(current[0]), "state": str(current[1]),
                        "endpoint_radius": str(radius), "endpoint_radius_float": float(radius),
                        "nominal_exact_error_upper": str(error_upper),
                        "closed_form_crosscheck": error_upper <= radius,
                        "accepted_output_segment": direct, "replay": replay,
                        "production_estimated_bound_scaled": internal,
                        "production_method": point.state.method,
                        "production_authority_generation": getattr(metrics, "authority_generation", None) if metrics else None,
                        "production_event_check": getattr(metrics, "event_authority_check", False) if metrics else False,
                        "production_refresh": metrics.periodic_reanchor if metrics else False})
        radii[current] = radius
        previous = current
    return {"case_path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
            "case_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "model": model.data(), "model_interpretation": "exact real values of binary-float component inputs; exact rational pulse times",
            "config": asdict(config), "simulation": simulation,
            "state_order": list(circuit.dynamic_names), "production_trace_sha256": observed_digest,
            "instrumentation_equivalent": True if verify_observation else None,
            "initial_radius": str(initial_radius),
            "accepted_steps": len(records), "captured_windows": len(windows),
            "captured_replay_steps": sum(w.get("steps", 0) for w in windows),
            "selected_replay_windows": len(selected_windows),
            "unselected_windows_retained": len(windows)-len(selected_windows),
            "all_closed_form_crosschecks": all(r["closed_form_crosscheck"] for r in records),
            "maximum_endpoint_radius": max(r["endpoint_radius_float"] for r in records),
            "maximum_output_tube_radius": float(max(F(r["accepted_output_segment"]["full_path_radius"]) for r in records)),
            "maximum_nominal_error_upper": float(max(F(r["nominal_exact_error_upper"]) for r in records)),
            "captured_window_inventory": [{"index": i, "status": w["status"], "steps": w.get("steps", 0),
                                           "selected": i in selected_windows,
                                           "points": [[str(t), str(x)] for t, x in w["points"]]} for i, w in enumerate(windows)],
            "points": records,
            "claim": "offline differential-state and declared Hermite reconstruction bounds; no general MNA or hardware certificate"}
