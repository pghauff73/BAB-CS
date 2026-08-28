from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def run_worker(
    case_path: str | Path,
    *,
    forbidden_root: str | Path | None = None,
    linear_backend: str | None = None,
    nominal_step: float | None = None,
) -> dict[str, Any]:
    import_started = time.perf_counter_ns()
    import babcs
    from babcs import BoundedIntegrator, Circuit, Simulator
    from babcs.io import load_case, summary_data

    import_finished = time.perf_counter_ns()
    module_path = Path(babcs.__file__).resolve()
    source_tree_excluded = True
    if forbidden_root is not None:
        source_tree_excluded = not _inside(module_path, Path(forbidden_root))
    if not source_tree_excluded:
        raise RuntimeError(f"BAB-CS worker imported from forbidden source tree: {module_path}")

    input_path = Path(case_path).resolve()
    load_started = time.perf_counter_ns()
    circuit, simulation, config = load_case(input_path)
    if linear_backend is not None:
        circuit = Circuit(circuit.elements, linear_backend=linear_backend)
    if nominal_step is not None:
        if nominal_step <= 0.0:
            raise ValueError("nominal_step override must be positive")
        simulation = {**simulation, "nominal_step": nominal_step}
    load_finished = time.perf_counter_ns()
    initialize_started = time.perf_counter_ns()
    simulator = Simulator(BoundedIntegrator(config))
    initialize_finished = time.perf_counter_ns()
    analysis_started = time.perf_counter_ns()
    result = simulator.run(circuit, **simulation)
    analysis_finished = time.perf_counter_ns()
    trace_rows = [
        [point.time, *point.state.evaluation.dynamic_state]
        for point in result.points
    ]
    summary = summary_data(result)
    return {
        "schema_version": 1,
        "tool": "babcs",
        "case_sha256": _sha256(input_path.read_bytes()),
        "module_path": str(module_path),
        "source_tree_excluded": source_tree_excluded,
        "python_executable": sys.executable,
        "requested_linear_backend": linear_backend,
        "linear_backend": result.linear_backend,
        "timing": {
            "import_seconds": (import_finished - import_started) / 1.0e9,
            "load_seconds": (load_finished - load_started) / 1.0e9,
            "initialization_seconds": (initialize_finished - initialize_started) / 1.0e9,
            "analysis_seconds": (analysis_finished - analysis_started) / 1.0e9,
        },
        "simulation": simulation,
        "babcs_configuration": asdict(config),
        "circuit_size": {
            "element_count": len(circuit.elements),
            "non_ground_node_count": len(circuit.nodes),
            "dynamic_state_count": circuit.dynamic_size,
            "algebraic_unknown_count": circuit.algebraic_size,
            "declared_mna_unknowns": circuit.dynamic_size + circuit.algebraic_size,
        },
        "state_names": list(circuit.dynamic_names),
        "output_points": len(trace_rows),
        "trace_rows": trace_rows,
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one isolated installed-wheel BAB-CS benchmark sample")
    parser.add_argument("case")
    parser.add_argument("--output", required=True)
    parser.add_argument("--forbidden-root")
    parser.add_argument("--linear-backend", choices=("dense", "scipy"))
    parser.add_argument("--nominal-step", type=float)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    result = run_worker(
        arguments.case,
        forbidden_root=arguments.forbidden_root,
        linear_backend=arguments.linear_backend,
        nominal_step=arguments.nominal_step,
    )
    Path(arguments.output).write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"analysis_seconds": result["timing"]["analysis_seconds"], "output": arguments.output}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
