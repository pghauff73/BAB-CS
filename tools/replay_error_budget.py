"""Exact-rational research pilot for affine replay error budgets.

This is a separate reduced-system experiment, not the BAB-CS production loop.
See docs/REPLAY_ERROR_BUDGET_THEOREM.md for the theorem and claim boundary.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction as F
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import platform

Vector = tuple[F, ...]
Matrix = tuple[Vector, ...]
GRID = 10**24
ROOT = Path(__file__).resolve().parents[1]


def add(x: Vector, y: Vector) -> Vector:
    return tuple(a + b for a, b in zip(x, y, strict=True))


def scale(a: F, x: Vector) -> Vector:
    return tuple(a * v for v in x)


def matvec(a: Matrix, x: Vector) -> Vector:
    return tuple(sum((u * v for u, v in zip(row, x, strict=True)), F(0)) for row in a)


def ceil_grid(x: F) -> F:
    return F(-((-x.numerator * GRID) // x.denominator), GRID)


def rounded_state(x: Vector) -> Vector:
    # The returned rational point defines the approximation exactly. Its rounding
    # error is included by reconstructing the defect from these endpoints.
    return tuple(F(round(v * GRID), GRID) for v in x)


def norm_upper(x: Vector, metric: str) -> F:
    if metric == "infinity":
        return max(map(abs, x))
    if metric == "euclidean":
        # l1 is a rational upper bound on l2. This costs tightness, not soundness.
        return sum(map(abs, x), F(0))
    raise ValueError("unsupported metric")


def logarithmic_norm_upper(a: Matrix, metric: str) -> F:
    if not a or any(len(row) != len(a) for row in a):
        raise ValueError("matrix must be square and nonempty")
    if metric == "infinity":
        return max(row[i] + sum((abs(v) for j, v in enumerate(row) if i != j), F(0))
                   for i, row in enumerate(a))
    if metric == "euclidean":
        if len(a) != 2:
            raise ValueError("Euclidean pilot supports only dissipative 2x2 matrices")
        s00, s11, s01 = 2 * a[0][0], 2 * a[1][1], a[0][1] + a[1][0]
        if s00 > 0 or s11 > 0 or s00 * s11 - s01 * s01 < 0:
            raise ValueError("symmetric part is not negative semidefinite")
        return F(0)
    raise ValueError("unsupported metric")


@lru_cache(maxsize=256)
def exp_bounds(x: F) -> tuple[F, F]:
    """Enclose exp(x) by rational Taylor sums and a geometric tail."""
    if abs(x) > 1:
        raise ValueError("pilot requires abs(mu * step) <= 1")
    z = abs(x)
    term = total = F(1)
    for k in range(1, 25):
        term *= z / k
        total += term
    first_omitted = term * z / 25
    upper = total + first_omitted / (1 - z / 26)
    return (total, upper) if x >= 0 else (1 / upper, 1 / total)


@lru_cache(maxsize=256)
def growth_factors(mu: F, h: F) -> tuple[F, F]:
    if h <= 0:
        raise ValueError("step must be positive")
    if mu == 0:
        return F(1), h
    lower, upper = exp_bounds(mu * h)
    integral = (upper - 1) / mu if mu > 0 else (lower - 1) / mu
    return upper, integral


def propagate(radius: F, defect: F, mu: F, h: F) -> F:
    if radius < 0 or defect < 0:
        raise ValueError("radius and defect must be nonnegative")
    growth, integral = growth_factors(mu, h)
    return ceil_grid(growth * radius + integral * defect)


def affine_value(a: Matrix, b: Vector, x: Vector) -> Vector:
    return add(matvec(a, x), b)


def hermite_defect(a: Matrix, b: Vector, x: Vector, y: Vector, h: F,
                   metric: str) -> F:
    """Bound the whole cubic Hermite defect using Bernstein convexity."""
    if h <= 0:
        raise ValueError("step must be positive")
    f0, f1 = affine_value(a, b, x), affine_value(a, b, y)
    difference = add(y, scale(F(-1), x))
    c0, c1 = x, scale(h, f0)
    c2 = add(scale(F(3), difference), scale(-h, add(scale(F(2), f0), f1)))
    c3 = add(scale(F(-2), difference), scale(h, add(f0, f1)))
    power = (
        add(scale(1 / h, c1), scale(F(-1), affine_value(a, b, c0))),
        add(scale(2 / h, c2), scale(F(-1), matvec(a, c1))),
        add(scale(3 / h, c3), scale(F(-1), matvec(a, c2))),
        scale(F(-1), matvec(a, c3)),
    )
    bernstein = (
        power[0],
        add(power[0], scale(F(1, 3), power[1])),
        add(add(power[0], scale(F(2, 3), power[1])), scale(F(1, 3), power[2])),
        add(add(power[0], power[1]), add(power[2], power[3])),
    )
    return max(norm_upper(v, metric) for v in bernstein)


def solve(a: Matrix, rhs: Vector) -> Vector:
    rows = [list(row) + [v] for row, v in zip(a, rhs, strict=True)]
    for j in range(len(rows)):
        pivot = next((i for i in range(j, len(rows)) if rows[i][j]), None)
        if pivot is None:
            raise ValueError("singular point-system matrix")
        rows[j], rows[pivot] = rows[pivot], rows[j]
        divisor = rows[j][j]
        rows[j] = [v / divisor for v in rows[j]]
        for i in range(len(rows)):
            if i != j:
                factor = rows[i][j]
                rows[i] = [v - factor * w for v, w in zip(rows[i], rows[j], strict=True)]
    return tuple(row[-1] for row in rows)


def point_step(a: Matrix, b: Vector, x: Vector, h: F, method: str) -> Vector:
    if method == "euler":
        return rounded_state(add(x, scale(h, affine_value(a, b, x))))
    if method != "trapezoidal":
        raise ValueError("unknown point method")
    lhs = tuple(tuple(F(i == j) - h * v / 2 for j, v in enumerate(row))
                for i, row in enumerate(a))
    rhs = add(x, scale(h / 2, add(matvec(a, x), scale(F(2), b))))
    return rounded_state(solve(lhs, rhs))


@dataclass(frozen=True)
class Case:
    name: str
    matrix: Matrix
    initial: Vector
    offset_before: Vector
    offset_after: Vector
    metric: str
    event: F | None = None

    def offset(self, time: F) -> Vector:
        return self.offset_after if self.event is not None and time >= self.event else self.offset_before


CASES = (
    Case("rc_decay", ((F(-1),),), (F(1),), (F(0),), (F(0),), "infinity"),
    Case("rl_step", ((F(-2),),), (F(0),), (F(1),), (F(1),), "infinity"),
    Case("rlc_damped", ((F(0), F(1)), (F(-1), F(-2))), (F(1), F(0)),
         (F(0), F(0)), (F(0), F(0)), "euclidean"),
    Case("lc_neutral", ((F(0), F(1)), (F(-1), F(0))), (F(1), F(0)),
         (F(0), F(0)), (F(0), F(0)), "euclidean"),
    Case("rc_scheduled_source", ((F(-1),),), (F(0),), (F(1),), (F(0),),
         "infinity", F(1)),
)


def reference_decimal(case: Case, time: F) -> tuple[Decimal, ...]:
    """Independent 80-digit matrix-series diagnostic, not the certificate."""
    with localcontext() as ctx:
        ctx.prec = 80
        def decimal(q: F) -> Decimal:
            return Decimal(q.numerator) / Decimal(q.denominator)
        a = tuple(tuple(decimal(v) for v in row) for row in case.matrix)
        x = tuple(decimal(v) for v in case.initial)
        cuts = [F(0)] + ([case.event] if case.event is not None and case.event < time else []) + [time]
        for left, right in zip(cuts, cuts[1:]):
            dt = decimal(right - left)
            b = tuple(decimal(v) for v in case.offset(left))
            term = tuple(dt * (sum((v * y for v, y in zip(row, x)), Decimal(0)) + source)
                         for row, source in zip(a, b))
            total = tuple(v + w for v, w in zip(x, term))
            for k in range(2, 161):
                term = tuple(dt / k * sum((v * y for v, y in zip(row, term)), Decimal(0)) for row in a)
                total = tuple(v + w for v, w in zip(total, term))
            x = total
        return x


def decimal_error(case: Case, time: F, x: Vector) -> float:
    with localcontext() as ctx:
        ctx.prec = 80
        delta = tuple(abs(Decimal(v.numerator) / Decimal(v.denominator) - y)
                      for v, y in zip(x, reference_decimal(case, time), strict=True))
        error = max(delta) if case.metric == "infinity" else sum((v*v for v in delta), Decimal(0)).sqrt()
        return float(error)


def run_case(case: Case, h: F, interval: int | None, refinement: int = 4,
             initial_radius: F = F(0), stop: F = F(2), reference_only: bool = False) -> dict:
    if h <= 0 or stop <= 0 or stop / h != int(stop / h):
        raise ValueError("positive uniform grid must exactly divide horizon")
    if interval is not None and (isinstance(interval, bool) or not isinstance(interval, int) or interval < 1):
        raise ValueError("interval must be a positive integer or None")
    if isinstance(refinement, bool) or not isinstance(refinement, int) or refinement < 1:
        raise ValueError("refinement must be a positive integer")
    if initial_radius < 0:
        raise ValueError("initial radius must be nonnegative")
    if reference_only and interval != 1:
        raise ValueError("reference-only baseline requires interval one")
    if case.event is not None and case.event / h != int(case.event / h):
        raise ValueError("scheduled event must lie on the pilot grid")
    mu = logarithmic_norm_upper(case.matrix, case.metric)
    x, radius = case.initial, initial_radius
    anchor_x, anchor_radius, anchor_time = x, radius, F(0)
    points, replay_count, candidate_count = [], 0, 0
    for n in range(1, int(stop / h) + 1):
        left, right = (n-1)*h, n*h
        b = case.offset(left)
        if reference_only:
            proposal, proposal_radius = x, radius
        else:
            proposal = point_step(case.matrix, b, x, h, "euler")
            candidate_count += 1
            proposal_radius = propagate(radius, hermite_defect(case.matrix, b, x, proposal, h, case.metric), mu, h)
        due = interval is not None and (n % interval == 0 or right == stop or right == case.event)
        inherited, fresh, jump = F(0), F(0), F(0)
        if due:
            replay_x, inherited, fresh = anchor_x, anchor_radius, F(0)
            small_h = h / refinement
            steps = int((right - anchor_time) / small_h)
            for k in range(steps):
                replay_left = anchor_time + k * small_h
                rb = case.offset(replay_left)
                replay_y = point_step(case.matrix, rb, replay_x, small_h, "trapezoidal")
                defect = hermite_defect(case.matrix, rb, replay_x, replay_y, small_h, case.metric)
                inherited = propagate(inherited, F(0), mu, small_h)
                fresh = propagate(fresh, defect, mu, small_h)
                replay_x = replay_y
            replay_count += steps
            jump = norm_upper(add(proposal, scale(F(-1), replay_x)), case.metric)
            x, radius = replay_x, inherited + fresh
            anchor_x, anchor_radius, anchor_time = x, radius, right
        else:
            x, radius = proposal, proposal_radius
        error = decimal_error(case, right, x)
        points.append({
            "time": str(right), "state": [str(v) for v in x],
            "radius": str(radius), "radius_float": float(radius),
            "central_trajectory_error_diagnostic": error,
            "diagnostic_covered": error <= float(radius),
            "replay": due, "inherited_anchor_radius": str(inherited) if due else None,
            "fresh_replay_defect_radius": str(fresh) if due else None,
            "proposal_radius_before_replay": str(proposal_radius) if not reference_only else None,
            "proposal_replay_distance_upper": str(jump) if due and not reference_only else None,
        })
    return {
        "case": case.name, "step": str(h), "anchor_interval": interval,
        "reference_only": reference_only,
        "refinement": refinement, "initial_radius": str(initial_radius),
        "metric": case.metric, "logarithmic_norm_upper": str(mu),
        "candidate_steps": candidate_count, "replay_steps": replay_count,
        "replay_windows": sum(p["replay"] for p in points),
        "max_accepted_radius": max(p["radius_float"] for p in points),
        "max_central_error_diagnostic": max(p["central_trajectory_error_diagnostic"] for p in points),
        "final_radius": points[-1]["radius"],
        "final_central_error_diagnostic": points[-1]["central_trajectory_error_diagnostic"],
        "all_diagnostics_covered": all(p["diagnostic_covered"] for p in points),
        "points": points,
    }


def study() -> dict:
    rows = [run_case(case, h, interval) for case in CASES
            for h in (F(1, 20), F(1, 40)) for interval in (None, 1, 4, 16)]
    rows += [run_case(CASES[0], F(1, 20), 4, initial_radius=F(1, 1000))]
    rows += [run_case(CASES[0], F(1, 20), 4, refinement=r) for r in (1, 2, 8)]
    rows += [run_case(case, F(1, 20), 1, reference_only=True) for case in CASES]
    sources = (Path(__file__), ROOT / "docs/REPLAY_ERROR_BUDGET_THEOREM.md",
               ROOT / "tests/test_replay_error_budget.py")
    return {
        "report_kind": "babcs.affine-replay-error-budget-pilot.v1",
        "claim": "restricted exact-rational reduced-system experiment; not production certification",
        "python": platform.python_version(),
        "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "arithmetic": "Fraction proof quantities; rational state rounding and upward radius rounding at 1e-24",
        "diagnostic": "80-digit Decimal matrix series, independent of bound; not an interval oracle",
        "cases": [{"name": c.name, "matrix": [[str(v) for v in row] for row in c.matrix],
                   "initial": list(map(str, c.initial)), "offset_before": list(map(str, c.offset_before)),
                   "offset_after": list(map(str, c.offset_after)), "event": str(c.event) if c.event is not None else None,
                   "metric": c.metric} for c in CASES],
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.dumps(study(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(payload)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
