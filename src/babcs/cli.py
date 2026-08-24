from __future__ import annotations

import argparse
import json
from dataclasses import replace

from .bounded import BoundedIntegrator
from .candidates import CANDIDATE_METHODS
from .io import load_case, summary_data, write_csv, write_summary
from .linalg import LINEAR_BACKENDS
from .model import Circuit
from .simulator import Simulator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="babcs", description="BAB-CSv1 circuit simulator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    simulate = subparsers.add_parser("simulate", help="simulate a JSON circuit case")
    simulate.add_argument("input", help="input JSON circuit")
    simulate.add_argument("--csv", help="write waveform and metric data to CSV")
    simulate.add_argument("--summary", help="write summary diagnostics to JSON")
    simulate.add_argument(
        "--linear-backend",
        choices=LINEAR_BACKENDS,
        help="override the circuit linear solver backend",
    )
    simulate.add_argument(
        "--mode",
        choices=("disabled", "shadow", "active"),
        help="override the configured rollout mode",
    )
    simulate.add_argument(
        "--candidate",
        choices=tuple(sorted(CANDIDATE_METHODS)),
        help="override the bounded candidate integrator",
    )
    simulate.add_argument(
        "--reference-method",
        choices=("backward_euler", "trapezoidal", "bdf2"),
        help="override the independent implicit reference method",
    )
    simulate.add_argument(
        "--reference-interval",
        type=int,
        help="run the per-step reference every N accepted steps for embedded candidates",
    )
    simulate.add_argument(
        "--bound-cap",
        type=float,
        help="promote reference authority when the deferred recursive bound reaches this cap",
    )
    simulate.add_argument(
        "--contraction-rate",
        type=float,
        help="use exp(-rate*h) instead of a fixed per-step contraction target",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command != "simulate":
        raise AssertionError("unreachable command")
    circuit, simulation, config = load_case(arguments.input)
    if arguments.linear_backend is not None:
        circuit = Circuit(circuit.elements, linear_backend=arguments.linear_backend)
    overrides = {
        key: value
        for key, value in {
            "rollout_mode": arguments.mode,
            "candidate_method": arguments.candidate,
            "reference_method": arguments.reference_method,
            "reference_interval_steps": arguments.reference_interval,
            "deferred_reference_bound_cap": arguments.bound_cap,
            "contraction_rate": arguments.contraction_rate,
        }.items()
        if value is not None
    }
    if overrides:
        config = replace(config, **overrides)
    simulator = Simulator(BoundedIntegrator(config))
    result = simulator.run(circuit, **simulation)
    if arguments.csv:
        write_csv(arguments.csv, circuit, result)
    if arguments.summary:
        write_summary(arguments.summary, result)
    print(json.dumps(summary_data(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
