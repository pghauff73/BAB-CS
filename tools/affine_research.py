"""Rational certificates for the four affine replay research directions.

Research-only, fixed affine models. No dependency on babcs.intervals.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from math import isqrt

from tools.replay_error_budget import (
    GRID, Matrix, Vector, add, affine_value, ceil_grid, growth_factors,
    matvec, point_step, rounded_state, scale,
)


def sqrt_upper(x: F) -> F:
    if x < 0:
        raise ValueError("negative squared norm")
    root = isqrt(x.numerator * GRID * GRID // x.denominator)
    return F(root if F(root * root, GRID * GRID) >= x else root + 1, GRID)


def transpose(a: Matrix) -> Matrix:
    return tuple(zip(*a))


def matrix_product(a: Matrix, b: Matrix) -> Matrix:
    return tuple(tuple(sum((x * y for x, y in zip(row, column, strict=True)), F(0))
                       for column in transpose(b)) for row in a)


def matrix_sum(a: Matrix, b: Matrix) -> Matrix:
    return tuple(add(x, y) for x, y in zip(a, b, strict=True))


def psd(a: Matrix) -> bool:
    if len(a) not in (1, 2) or any(len(row) != len(a) for row in a) or a != transpose(a):
        raise ValueError("PSD checker requires a symmetric 1x1 or 2x2 matrix")
    return all(a[i][i] >= 0 for i in range(len(a))) and (
        len(a) == 1 or a[0][0] * a[1][1] - a[0][1] ** 2 >= 0
    )


def identity(n: int) -> Matrix:
    return tuple(tuple(F(i == j) for j in range(n)) for i in range(n))


@dataclass(frozen=True)
class Metric:
    name: str
    mu: F
    matrix: Matrix | None = None
    lower: F = F(1)
    upper: F = F(1)

    @classmethod
    def infinity(cls, a: Matrix) -> Metric:
        if not a or any(len(row) != len(a) for row in a):
            raise ValueError("matrix must be nonempty and square")
        mu = max(row[i] + sum((abs(v) for j, v in enumerate(row) if i != j), F(0))
                 for i, row in enumerate(a))
        return cls("infinity", mu)

    @classmethod
    def weighted(cls, a: Matrix, p: Matrix, mu: F, lower: F, upper: F,
                 name: str = "weighted") -> Metric:
        n = len(a)
        if n not in (1, 2) or len(p) != n or any(len(row) != n for row in (*a, *p)):
            raise ValueError("weighted certificate supports dimensions one and two")
        if lower <= 0 or upper < lower or p != transpose(p):
            raise ValueError("invalid metric eigenvalue bounds or symmetry")
        eye = identity(n)
        low_gap = matrix_sum(p, tuple(scale(-lower, row) for row in eye))
        high_gap = matrix_sum(tuple(scale(upper, row) for row in eye), tuple(scale(F(-1), row) for row in p))
        dissipation = matrix_sum(matrix_product(transpose(a), p), matrix_product(p, a))
        lmi = matrix_sum(tuple(scale(2 * mu, row) for row in p),
                         tuple(scale(F(-1), row) for row in dissipation))
        if not all(psd(m) for m in (low_gap, high_gap, lmi)):
            raise ValueError("unproved metric bounds or logarithmic-norm inequality")
        return cls(name, mu, p, lower, upper)

    def norm(self, v: Vector) -> F:
        if self.matrix is None:
            return max(map(abs, v))
        product = matvec(self.matrix, v)
        return sqrt_upper(sum((x*y for x, y in zip(v, product, strict=True)), F(0)))

    @property
    def coordinate_factor(self) -> F:
        return F(1) if self.matrix is None else sqrt_upper(1 / self.lower)

    def physical_radius(self, radius: F) -> F:
        return ceil_grid(self.coordinate_factor * radius)

    def data(self) -> dict:
        return {"name": self.name, "mu": str(self.mu), "lower_eigenvalue_bound": str(self.lower),
                "upper_eigenvalue_bound": str(self.upper),
                "coordinate_conversion_upper": str(self.coordinate_factor),
                "matrix": [[str(v) for v in row] for row in self.matrix] if self.matrix else None}


def hermite_power(a: Matrix, b: Vector, x: Vector, y: Vector, h: F) -> tuple[Vector, ...]:
    if h <= 0:
        raise ValueError("step must be positive")
    f0, f1 = affine_value(a, b, x), affine_value(a, b, y)
    delta = add(y, scale(F(-1), x))
    return (x, scale(h, f0),
            add(scale(F(3), delta), scale(-h, add(scale(F(2), f0), f1))),
            add(scale(F(-2), delta), scale(h, add(f0, f1))))


def power_to_bernstein(c: tuple[Vector, ...]) -> tuple[Vector, ...]:
    return (c[0], add(c[0], scale(F(1, 3), c[1])),
            add(add(c[0], scale(F(2, 3), c[1])), scale(F(1, 3), c[2])),
            add(add(c[0], c[1]), add(c[2], c[3])))


def split_bernstein(c: tuple[Vector, ...]) -> tuple[tuple[Vector, ...], tuple[Vector, ...]]:
    levels = [c]
    while len(levels[-1]) > 1:
        levels.append(tuple(scale(F(1, 2), add(x, y)) for x, y in zip(levels[-1], levels[-1][1:])))
    return tuple(row[0] for row in levels), tuple(row[-1] for row in reversed(levels))


@dataclass(frozen=True)
class Segment:
    matrix: Matrix
    offset: Vector
    start: Vector
    end: Vector
    step: F
    initial_radius: F
    metric: Metric
    defect: F
    bernstein: tuple[Vector, ...]

    def radius_at(self, time: F) -> F:
        if time < 0 or time > self.step:
            raise ValueError("time outside segment")
        if time == 0:
            return self.initial_radius
        g, phi = growth_factors(self.metric.mu, time)
        return ceil_grid(g * self.initial_radius + phi * self.defect)

    @property
    def endpoint_radius(self) -> F:
        return self.radius_at(self.step)

    @property
    def full_radius(self) -> F:
        return max(self.initial_radius, self.endpoint_radius)

    @property
    def fresh_radius(self) -> F:
        return ceil_grid(growth_factors(self.metric.mu, self.step)[1] * self.defect)

    def data(self) -> dict:
        g = growth_factors(self.metric.mu, self.step)[0]
        return {"step": str(self.step), "initial_radius": str(self.initial_radius),
                "defect_upper": str(self.defect), "endpoint_radius": str(self.endpoint_radius),
                "full_radius": str(self.full_radius),
                "inherited_radius_upper": str(ceil_grid(g * self.initial_radius)),
                "fresh_radius_upper": str(self.fresh_radius),
                "physical_endpoint_radius": str(self.metric.physical_radius(self.endpoint_radius)),
                "physical_full_radius": str(self.metric.physical_radius(self.full_radius)),
                "bernstein": [[str(v) for v in row] for row in self.bernstein]}


def certify_segment(a: Matrix, b: Vector, x: Vector, y: Vector, h: F,
                    radius: F, metric: Metric) -> Segment:
    n = len(a)
    if radius < 0 or n == 0 or any(len(v) != n for v in (*a, b, x, y)):
        raise ValueError("invalid dimensions or negative radius")
    # Revalidate the claimed norm against this segment's actual matrix.
    if metric.matrix is None:
        if metric.mu < Metric.infinity(a).mu:
            raise ValueError("unproved infinity logarithmic norm")
    else:
        Metric.weighted(a, metric.matrix, metric.mu, metric.lower, metric.upper)
    c = hermite_power(a, b, x, y, h)
    residual = (
        add(scale(1/h, c[1]), scale(F(-1), affine_value(a, b, c[0]))),
        add(scale(2/h, c[2]), scale(F(-1), matvec(a, c[1]))),
        add(scale(3/h, c[3]), scale(F(-1), matvec(a, c[2]))),
        scale(F(-1), matvec(a, c[3])),
    )
    defect = max(metric.norm(v) for v in power_to_bernstein(residual))
    return Segment(a, b, x, y, h, radius, metric, defect, power_to_bernstein(c))


def heun(a: Matrix, b: Vector, x: Vector, h: F) -> Vector:
    k1 = affine_value(a, b, x)
    predictor = add(x, scale(h, k1))
    k2 = affine_value(a, b, predictor)
    return rounded_state(add(x, scale(h/2, add(k1, k2))))


def classify_events(segment: Segment, coordinate: int, threshold: tuple[F, F],
                    tolerance: F, *, maximum_cells: int = 4096) -> dict:
    """Enclose every possible crossing; prove existence/uniqueness only with signs and monotonicity."""
    if not 0 <= coordinate < len(segment.start) or threshold[0] > threshold[1] or tolerance <= 0:
        raise ValueError("invalid event coordinate, threshold, or tolerance")
    if isinstance(maximum_cells, bool) or not isinstance(maximum_cells, int) or maximum_cells < 1:
        raise ValueError("maximum_cells must be positive")
    metric = segment.metric

    def radius(t):
        return metric.physical_radius(segment.radius_at(t))

    def guard(point, time):
        error = radius(time)
        return point[coordinate] - error - threshold[1], point[coordinate] + error - threshold[0]

    def range_and_derivative(controls, lo, hi):
        error = max(radius(lo), radius(hi))
        lower = tuple(min(v[j] for v in controls) - error for j in range(len(segment.start)))
        upper = tuple(max(v[j] for v in controls) + error for j in range(len(segment.start)))
        derivative_low = derivative_high = segment.offset[coordinate]
        for a, l, u in zip(segment.matrix[coordinate], lower, upper, strict=True):
            derivative_low += a * (l if a >= 0 else u)
            derivative_high += a * (u if a >= 0 else l)
        return (lower[coordinate] - threshold[1], upper[coordinate] - threshold[0]), (derivative_low, derivative_high)

    stack = [(F(0), segment.step, segment.bernstein)]
    possible, excluded = [], 0
    inspected = 0
    exhausted = False
    while stack:
        lo, hi, controls = stack.pop()
        if inspected >= maximum_cells:
            exhausted = True
            possible.append((lo, hi, controls))
            possible.extend(stack)
            break
        inspected += 1
        enclosure, _ = range_and_derivative(controls, lo, hi)
        if enclosure[0] > 0 or enclosure[1] < 0:
            excluded += 1
            continue
        if hi - lo <= tolerance:
            possible.append((lo, hi, controls))
            continue
        left, right = split_bernstein(controls)
        mid = (lo + hi)/2
        stack.extend(((mid, hi, right), (lo, mid, left)))
    possible.sort(key=lambda row: row[0])
    groups = []
    for cell in possible:
        if groups and groups[-1][-1][1] == cell[0]:
            groups[-1].append(cell)
        else:
            groups.append([cell])
    events = []
    for cells in groups:
        lo, hi = cells[0][0], cells[-1][1]
        gl, gr = guard(cells[0][2][0], lo), guard(cells[-1][2][-1], hi)
        derivative_ranges = [range_and_derivative(c, l, u)[1] for l, u, c in cells]
        derivative = (min(v[0] for v in derivative_ranges), max(v[1] for v in derivative_ranges))
        rising = gl[1] < 0 and gr[0] > 0 and derivative[0] > 0
        falling = gl[0] > 0 and gr[1] < 0 and derivative[1] < 0
        proven = (rising or falling) and not exhausted
        events.append({"time_lower": str(lo), "time_upper": str(hi),
                       "status": "CROSSING" if proven else "UNKNOWN",
                       "direction": "rising" if rising else "falling" if falling else "unresolved",
                       "derivative_lower": str(derivative[0]), "derivative_upper": str(derivative[1]),
                       "reason": "opposite endpoint signs and strict monotonicity" if proven else
                       "cell budget exhausted" if exhausted else "existence or uniqueness unproved"})
    status = "NO_CROSSING" if not events else "CROSSINGS" if all(e["status"] == "CROSSING" for e in events) else "UNKNOWN"
    return {"status": status, "threshold": list(map(str, threshold)), "events": events,
            "requested_cell_tolerance": str(tolerance), "inspected_cells": inspected,
            "excluded_cells": excluded, "budget_exhausted": exhausted,
            "meaning": "all possible roots enclosed; CROSSING proves one root per trajectory and fixed threshold in this cell"}


def transition_times(event: dict, delay: tuple[F, F], jitter: tuple[F, F]) -> dict:
    if delay[0] < 0 or delay[0] > delay[1] or jitter[0] > jitter[1] or delay[0]+jitter[0] < 0:
        raise ValueError("requires ordered timing ranges and nonnegative total delay")
    return {"time_lower": str(F(event["time_lower"]) + delay[0] + jitter[0]),
            "time_upper": str(F(event["time_upper"]) + delay[1] + jitter[1]),
            "status": event["status"], "delay": list(map(str, delay)), "jitter": list(map(str, jitter)),
            "meaning": "time enclosure only; post-transition flow is not certified here"}


def order_events(events: list[dict]) -> str:
    ordered = sorted(events, key=lambda e: F(e["time_lower"]))
    if any(e["status"] != "CROSSING" for e in ordered):
        return "UNKNOWN"
    if any(F(a["time_upper"]) >= F(b["time_lower"]) for a, b in zip(ordered, ordered[1:])):
        return "SIMULTANEOUS_OR_ORDER_UNRESOLVED"
    return "STRICT_ORDER"


def adaptive_run(case, metric: Metric, tolerance: F, policy: str,
                 maximum_step: F = F(1, 5), stop: F = F(2),
                 maximum_attempts: int = 10000, minimum_step: F = F(1, 10**8)) -> dict:
    """Certify entire accepted Hermite segments; failed trials never mutate state."""
    if policy not in {"adaptive_heun", "adaptive_reference", "adaptive_mixed"}:
        raise ValueError("unknown adaptive policy")
    if tolerance <= 0 or maximum_step <= 0 or stop <= 0 or minimum_step <= 0:
        raise ValueError("positive budget, horizon and steps required")
    if metric.mu > 0:
        raise ValueError("this allocation experiment requires a nonexpansive metric")
    if isinstance(maximum_attempts, bool) or not isinstance(maximum_attempts, int) or maximum_attempts < 1:
        raise ValueError("maximum_attempts must be a positive integer")
    x, radius, time, h = case.initial, F(0), F(0), maximum_step
    work = {"candidate_attempts": 0, "reference_attempts": 0, "certificate_evaluations": 0,
            "accepted_candidate_steps": 0, "accepted_reference_steps": 0,
            "rejected_trials": 0, "rhs_evaluations": 0, "linear_solves": 0}
    records = []
    target_metric = tolerance / metric.coordinate_factor
    failure = None
    for attempt in range(maximum_attempts):
        if time == stop:
            break
        h = min(h, maximum_step, stop-time)
        if case.event is not None and time < case.event < time+h:
            h = case.event-time
        if h < minimum_step:
            failure = "minimum_step"
            break
        modes = ("trapezoidal",) if policy == "adaptive_reference" else ("heun", "trapezoidal") if policy == "adaptive_mixed" else ("heun",)
        accepted = None
        for method in modes:
            # A mixed fallback spends two implicit substeps. Its accepted output
            # includes the midpoint, so the complete reconstruction is certified.
            subdivisions = 2 if method == "trapezoidal" and policy == "adaptive_mixed" else 1
            trial_x, trial_r, trial_time, trial_records = x, radius, time, []
            for _ in range(subdivisions):
                dt = h / subdivisions
                b = case.offset(trial_time)
                if method == "heun":
                    work["candidate_attempts"] += 1
                    work["rhs_evaluations"] += 2
                    y = heun(case.matrix, b, trial_x, dt)
                else:
                    work["reference_attempts"] += 1
                    work["linear_solves"] += 1
                    y = point_step(case.matrix, b, trial_x, dt, "trapezoidal")
                cert = certify_segment(case.matrix, b, trial_x, y, dt, trial_r, metric)
                work["certificate_evaluations"] += 1
                allowance = target_metric * dt / stop
                if (cert.fresh_radius > allowance or cert.full_radius > target_metric
                        or metric.physical_radius(cert.full_radius) > tolerance):
                    break
                trial_time += dt
                trial_records.append({"time": str(trial_time), "state": list(map(str, y)),
                                      "method": method, "certificate": cert.data(),
                                      "allocation": str(allowance)})
                trial_x, trial_r = y, cert.endpoint_radius
            else:
                accepted = (trial_x, trial_r, trial_time, trial_records, method)
                break
            work["rejected_trials"] += 1
        if accepted is None:
            h /= 2
            continue
        x, radius, time, new_records, method = accepted
        records.extend(new_records)
        work["accepted_candidate_steps" if method == "heun" else "accepted_reference_steps"] += len(new_records)
        used = max(F(r["certificate"]["fresh_radius_upper"]) / F(r["allocation"]) for r in new_records)
        if used < F(1, 4):
            h *= 2
    if time < stop and failure is None:
        failure = "attempt_budget"
    full = max((F(row["certificate"]["physical_full_radius"]) for row in records), default=F(0))
    return {"case": case.name, "policy": policy, "status": "CERTIFIED" if time == stop else "UNKNOWN",
            "failure_reason": failure, "tolerance_physical": str(tolerance), "maximum_step": str(maximum_step),
            "stop": str(stop), "reached_time": str(time), "metric": metric.data(),
            "maximum_physical_tube_radius": str(full), "final_state": list(map(str, x)),
            "final_radius": str(radius), "work": work, "segments": records,
            "claim": "complete accepted Hermite reconstruction under the declared affine model; no wall-time speed claim"}
