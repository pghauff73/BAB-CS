from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from babcs import (
    RootFindingError,
    RootResult,
    RootSettings,
    bisection,
    bounded_newton_raphson,
    interval_newton,
    newton_raphson,
    ridders,
    secant,
)
from tools.compare_methods import environment_metadata, source_metadata


SCHEMA_VERSION = 2
METHODS = (
    "newton_raphson",
    "bounded_newton_raphson",
    "interval_newton",
    "secant",
    "bisection",
    "ridders",
)


@dataclass(frozen=True, slots=True)
class RootCase:
    case_id: str
    description: str
    function: Callable[[float], float]
    derivative: Callable[[float], float]
    derivative_interval: Callable[[float, float], tuple[float, float]]
    bracket: tuple[float, float]
    newton_initial: float
    secant_initial: tuple[float, float]
    expected_root: float


def benchmark_cases() -> tuple[RootCase, ...]:
    saturation_current = 1.0e-12
    thermal_voltage = 0.02585
    resistance = 1_000.0
    source_voltage = 5.0

    def diode_residual(voltage: float) -> float:
        diode_current = saturation_current * math.expm1(voltage / thermal_voltage)
        return diode_current + voltage / resistance - source_voltage / resistance

    def diode_derivative(voltage: float) -> float:
        return (
            saturation_current * math.exp(voltage / thermal_voltage) / thermal_voltage
            + 1.0 / resistance
        )

    def cycle_derivative_interval(lower: float, upper: float) -> tuple[float, float]:
        endpoint_values = (
            3.0 * lower * lower - 2.0,
            3.0 * upper * upper - 2.0,
        )
        derivative_lower = -2.0 if lower <= 0.0 <= upper else min(endpoint_values)
        return derivative_lower, max(endpoint_values)

    def multiple_root_derivative_interval(
        lower: float,
        upper: float,
    ) -> tuple[float, float]:
        endpoint_values = (
            3.0 * (lower - 1.0) ** 2,
            3.0 * (upper - 1.0) ** 2,
        )
        derivative_lower = 0.0 if lower <= 1.0 <= upper else min(endpoint_values)
        return derivative_lower, max(endpoint_values)

    return (
        RootCase(
            "square_root_two",
            "Smooth convex simple root",
            lambda value: value * value - 2.0,
            lambda value: 2.0 * value,
            lambda lower, upper: (2.0 * lower, 2.0 * upper),
            (0.0, 2.0),
            2.0,
            (0.0, 2.0),
            math.sqrt(2.0),
        ),
        RootCase(
            "exponential_root",
            "Smooth monotone exponential root",
            lambda value: math.exp(value) - 3.0,
            math.exp,
            lambda lower, upper: (math.exp(lower), math.exp(upper)),
            (0.0, 2.0),
            2.0,
            (0.0, 2.0),
            math.log(3.0),
        ),
        RootCase(
            "newton_cycle",
            "Newton cycles between zero and one from the selected initial value",
            lambda value: value**3 - 2.0 * value + 2.0,
            lambda value: 3.0 * value * value - 2.0,
            cycle_derivative_interval,
            (-2.0, 0.0),
            0.0,
            (-2.0, 0.0),
            -1.7692923542386314,
        ),
        RootCase(
            "multiple_root",
            "Triple root with only linear Newton convergence",
            lambda value: (value - 1.0) ** 3,
            lambda value: 3.0 * (value - 1.0) ** 2,
            multiple_root_derivative_interval,
            (0.0, 1.5),
            1.5,
            (0.0, 1.5),
            1.0,
        ),
        RootCase(
            "diode_operating_point",
            "Shockley diode and resistor operating point",
            diode_residual,
            diode_derivative,
            lambda lower, upper: (
                diode_derivative(lower),
                diode_derivative(upper),
            ),
            (0.0, 1.0),
            0.0,
            (0.0, 1.0),
            0.5741473391899134,
        ),
    )


def execute_comparison(
    *,
    settings: RootSettings = RootSettings(max_iterations=80),
) -> dict[str, Any]:
    cases = benchmark_cases()
    results: list[dict[str, Any]] = []
    for case in cases:
        for method in METHODS:
            try:
                result = _execute_method(case, method, settings)
            except (RootFindingError, ValueError) as error:
                results.append(
                    {
                        "case_id": case.case_id,
                        "method": method,
                        "converged": False,
                        "reason": str(error),
                        "root": None,
                        "residual": None,
                        "absolute_error": None,
                        "iterations": None,
                        "function_evaluations": None,
                        "derivative_evaluations": None,
                        "total_evaluations": None,
                        "bracket": None,
                        "absolute_error_bound": None,
                        "certificate_contains_expected_root": None,
                        "step_counts": {},
                    }
                )
                continue
            results.append(_result_data(case, result))

    return {
        "schema_version": SCHEMA_VERSION,
        "source": source_metadata(REPOSITORY_ROOT),
        "environment": environment_metadata(),
        "settings": asdict(settings),
        "method_order": list(METHODS),
        "cases": [
            {
                "id": case.case_id,
                "description": case.description,
                "bracket": list(case.bracket),
                "newton_initial": case.newton_initial,
                "secant_initial": list(case.secant_initial),
                "expected_root": case.expected_root,
            }
            for case in cases
        ],
        "claim_boundary": (
            "Bracket certificates assume continuity and trustworthy finite signs. "
            "Interval Newton additionally assumes each derivative interval encloses "
            "the full derivative range on the requested bracket. The results are "
            "numerical enclosures, not machine-checked interval-arithmetic proofs."
        ),
        "results": results,
    }


def write_report(path: str | Path, report: dict[str, Any], *, overwrite: bool = False) -> None:
    output = Path(path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing report: {output}")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: str | Path, report: dict[str, Any], *, overwrite: bool = False) -> None:
    output = Path(path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing report: {output}")
    fields = (
        "case_id",
        "method",
        "converged",
        "reason",
        "root",
        "residual",
        "absolute_error",
        "iterations",
        "function_evaluations",
        "derivative_evaluations",
        "total_evaluations",
        "absolute_error_bound",
        "certificate_contains_expected_root",
    )
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for result in report["results"]:
            writer.writerow({field: result[field] for field in fields})


def _execute_method(case: RootCase, method: str, settings: RootSettings) -> RootResult:
    if method == "newton_raphson":
        return newton_raphson(
            case.function,
            case.derivative,
            case.newton_initial,
            settings=settings,
        )
    if method == "bounded_newton_raphson":
        return bounded_newton_raphson(
            case.function,
            case.derivative,
            *case.bracket,
            settings=settings,
        )
    if method == "interval_newton":
        return interval_newton(
            case.function,
            case.derivative_interval,
            *case.bracket,
            settings=settings,
        )
    if method == "secant":
        return secant(case.function, *case.secant_initial, settings=settings)
    if method == "bisection":
        return bisection(case.function, *case.bracket, settings=settings)
    if method == "ridders":
        return ridders(case.function, *case.bracket, settings=settings)
    raise ValueError(f"unknown root-finding method: {method}")


def _result_data(case: RootCase, result: RootResult) -> dict[str, Any]:
    step_counts: dict[str, int] = {}
    for point in result.trace:
        step_counts[point.step_kind] = step_counts.get(point.step_kind, 0) + 1
    certificate_contains_expected_root = None
    bracket = None
    if result.bracket is not None:
        bracket = list(result.bracket)
        certificate_contains_expected_root = (
            result.bracket[0] <= case.expected_root <= result.bracket[1]
        )
    return {
        "case_id": case.case_id,
        "method": result.method,
        "converged": result.converged,
        "reason": result.reason,
        "root": result.root,
        "residual": result.residual,
        "absolute_error": abs(result.root - case.expected_root),
        "iterations": result.iterations,
        "function_evaluations": result.function_evaluations,
        "derivative_evaluations": result.derivative_evaluations,
        "total_evaluations": result.function_evaluations + result.derivative_evaluations,
        "bracket": bracket,
        "absolute_error_bound": result.absolute_error_bound,
        "certificate_contains_expected_root": certificate_contains_expected_root,
        "step_counts": step_counts,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare scalar root-finding methods")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--csv-output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--max-iterations", type=int, default=80)
    parser.add_argument("--absolute-tolerance", type=float, default=1.0e-12)
    parser.add_argument("--relative-tolerance", type=float, default=1.0e-12)
    parser.add_argument("--residual-tolerance", type=float, default=1.0e-12)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    settings = RootSettings(
        absolute_tolerance=arguments.absolute_tolerance,
        relative_tolerance=arguments.relative_tolerance,
        residual_tolerance=arguments.residual_tolerance,
        max_iterations=arguments.max_iterations,
    )
    report = execute_comparison(settings=settings)
    if arguments.output is not None:
        write_report(arguments.output, report, overwrite=arguments.overwrite)
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    if arguments.csv_output is not None:
        write_csv(arguments.csv_output, report, overwrite=arguments.overwrite)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
