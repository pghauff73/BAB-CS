from __future__ import annotations

import argparse
import json
from dataclasses import replace

from .bounded import BoundedAdamsBashforthIntegrator
from .io import load_case, summary_data, write_csv, write_summary
from .simulator import Simulator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="babcs", description="BAB-CSv1 circuit simulator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    simulate = subparsers.add_parser("simulate", help="simulate a JSON circuit case")
    simulate.add_argument("input", help="input JSON circuit")
    simulate.add_argument("--csv", help="write waveform and metric data to CSV")
    simulate.add_argument("--summary", help="write summary diagnostics to JSON")
    simulate.add_argument(
        "--mode",
        choices=("disabled", "shadow", "active"),
        help="override the configured rollout mode",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command != "simulate":
        raise AssertionError("unreachable command")
    circuit, simulation, config = load_case(arguments.input)
    if arguments.mode is not None:
        config = replace(config, rollout_mode=arguments.mode)
    simulator = Simulator(BoundedAdamsBashforthIntegrator(config))
    result = simulator.run(circuit, **simulation)
    if arguments.csv:
        write_csv(arguments.csv, circuit, result)
    if arguments.summary:
        write_summary(arguments.summary, result)
    print(json.dumps(summary_data(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

