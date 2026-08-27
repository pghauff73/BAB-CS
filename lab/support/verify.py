from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
SOURCE_ROOT = REPOSITORY_ROOT / "src"
FIXTURE_PATH = REPOSITORY_ROOT / "lab/fixtures/verification-baseline.json"

import build_backend
from babcs import BABCSConfig, BoundedIntegrator, Simulator
from babcs.io import load_case, summary_data
from babcs.linalg import weighted_rms
from tools.compare_external import generate_ngspice_netlist
from tools.run_external_suite import load_external_manifest


EXERCISES = (
    "01-mna",
    "02-convergence",
    "03-phase-versus-energy",
    "04-shadow-authority",
    "05-deterministic-packaging",
    "06-source-wheel-equivalence",
    "07-event-alignment",
    "08-bound-coverage",
    "09-fallback-forensics",
    "10-ngspice-mapping",
)


class LabVerificationError(RuntimeError):
    pass


class LabVerifier:
    def __init__(self, *, development: bool = False) -> None:
        self.development = development
        self._temporary = tempfile.TemporaryDirectory(prefix="babcs-lab-")
        self.root = Path(self._temporary.name)
        self._wheel_path: Path | None = None
        self._wheel_pair: tuple[Path, Path] | None = None

    def close(self) -> None:
        self._temporary.cleanup()

    def run(self, exercise_ids: list[str]) -> dict[str, Any]:
        results = []
        for exercise_id in exercise_ids:
            method = getattr(self, f"exercise_{exercise_id.replace('-', '_')}")
            evidence = method()
            results.append({"id": exercise_id, "status": "passed", "evidence": evidence})
        return {
            "schema_version": 1,
            "development_mode": self.development,
            "all_passed": True,
            "exercises": results,
        }

    def exercise_01_mna(self) -> dict[str, Any]:
        circuit, simulation, _ = load_case(REPOSITORY_ROOT / "lab/01-mna/case.json")
        state = circuit.initial_dynamic_state()
        evaluation = circuit.evaluate(simulation["start_time"], state)
        if circuit.dynamic_names != ("v(C1)",):
            raise LabVerificationError("MNA exercise dynamic-state ownership changed")
        if evaluation.algebraic.residual_norm > 1.0e-10:
            raise LabVerificationError("MNA exercise algebraic projection residual is too large")
        return {
            "dynamic_names": list(circuit.dynamic_names),
            "nodes": list(circuit.nodes),
            "dynamic_size": circuit.dynamic_size,
            "algebraic_size": circuit.algebraic_size,
            "initial_derivative": list(evaluation.derivative),
            "algebraic_residual": evaluation.algebraic.residual_norm,
            "state_is_not_node_voltage_vector": circuit.dynamic_size != len(circuit.nodes),
        }

    def exercise_02_convergence(self) -> dict[str, Any]:
        path = REPOSITORY_ROOT / "lab/02-convergence/case.json"
        circuit, simulation, config = load_case(path)
        steps = (1.0e-4, 5.0e-5, 2.5e-5)
        errors = []
        for step in steps:
            result = Simulator(BoundedIntegrator(config)).run(
                circuit,
                simulation["stop_time"],
                step,
                start_time=simulation["start_time"],
            )
            maximum_error = max(
                abs(
                    point.state.evaluation.dynamic_state[0]
                    - _rc_voltage(point.time, 1000.0, 1.0e-6, 1.0, 0.0)
                )
                for point in result.points
            )
            errors.append(maximum_error)
        if not all(fine < coarse for coarse, fine in zip(errors, errors[1:])):
            raise LabVerificationError("RC refinement errors are not monotonically decreasing")
        orders = [
            math.log(coarse / fine) / math.log(2.0)
            for coarse, fine in zip(errors, errors[1:])
        ]
        if min(orders) < 1.8:
            raise LabVerificationError("trapezoidal RC refinement did not show second-order behavior")
        return {"steps": list(steps), "maximum_errors": errors, "observed_orders": orders}

    def exercise_03_phase_versus_energy(self) -> dict[str, Any]:
        path = REPOSITORY_ROOT / "lab/03-phase-versus-energy/case.json"
        circuit, simulation, base = load_case(path)
        capacitance = 1.0e-6
        inductance = 1.0e-3
        phase_scale = math.sqrt(inductance / capacitance)
        methods = {}
        for method in ("backward_euler", "trapezoidal"):
            config = replace(base, reference_method=method)
            result = Simulator(BoundedIntegrator(config)).run(circuit, **simulation)
            energies = [point.state.evaluation.stored_energy for point in result.points]
            final = result.points[-1]
            voltage, current = final.state.evaluation.dynamic_state
            measured_phase = math.atan2(current * phase_scale, voltage)
            angular_frequency = 1.0 / math.sqrt(inductance * capacitance)
            authority_phase = math.atan2(
                math.sin(angular_frequency * final.time),
                math.cos(angular_frequency * final.time),
            )
            phase_error = abs(
                math.atan2(
                    math.sin(measured_phase - authority_phase),
                    math.cos(measured_phase - authority_phase),
                )
            )
            methods[method] = {
                "final_phase_error_radians": phase_error,
                "relative_energy_span": (max(energies) - min(energies)) / energies[0],
                "final_relative_energy_error": abs(energies[-1] - energies[0]) / energies[0],
            }
        if methods["trapezoidal"]["relative_energy_span"] >= methods["backward_euler"]["relative_energy_span"]:
            raise LabVerificationError("LC exercise no longer distinguishes energy behavior")
        if methods["trapezoidal"]["final_phase_error_radians"] <= 0.0:
            raise LabVerificationError("LC exercise requires nonzero measured phase error")
        return {"periods": 10, "methods": methods, "phase_and_energy_are_separate": True}

    def exercise_04_shadow_authority(self) -> dict[str, Any]:
        path = REPOSITORY_ROOT / "lab/04-shadow-authority/case.json"
        circuit, simulation, base = load_case(path)
        disabled = Simulator(BoundedIntegrator(replace(base, rollout_mode="disabled"))).run(
            circuit,
            **simulation,
        )
        shadow = Simulator(BoundedIntegrator(replace(base, rollout_mode="shadow"))).run(
            circuit,
            **simulation,
        )
        active = Simulator(BoundedIntegrator(replace(base, rollout_mode="active"))).run(
            circuit,
            **simulation,
        )
        disabled_times = [point.time for point in disabled.points]
        shadow_times = [point.time for point in shadow.points]
        if shadow_times != disabled_times:
            raise LabVerificationError("shadow accepted time grid diverged from implicit authority")
        maximum_delta = 0.0
        maximum_tolerance = 0.0
        for disabled_point, shadow_point in zip(disabled.points, shadow.points):
            disabled_state = disabled_point.state.evaluation.dynamic_state
            shadow_state = shadow_point.state.evaluation.dynamic_state
            if len(shadow_state) != len(disabled_state):
                raise LabVerificationError("shadow accepted state dimension changed")
            for disabled_value, shadow_value in zip(disabled_state, shadow_state):
                delta = abs(shadow_value - disabled_value)
                tolerance = 16.0 * max(
                    math.ulp(disabled_value),
                    math.ulp(shadow_value),
                    math.ulp(1.0),
                )
                maximum_delta = max(maximum_delta, delta)
                maximum_tolerance = max(maximum_tolerance, tolerance)
                if delta > tolerance:
                    raise LabVerificationError(
                        "shadow accepted state diverged beyond solver roundoff from implicit authority"
                    )
        shadow_summary = summary_data(shadow)
        active_summary = summary_data(active)
        if shadow_summary["candidate_steps"] <= 0:
            raise LabVerificationError("shadow mode did not emit candidate diagnostics")
        return {
            "shadow_matches_disabled_within_solver_roundoff": True,
            "maximum_shadow_authority_delta": maximum_delta,
            "maximum_roundoff_tolerance": maximum_tolerance,
            "shadow_candidate_steps": shadow_summary["candidate_steps"],
            "shadow_reference_solves": shadow_summary["reference_solves"],
            "active_candidate_steps": active_summary["candidate_steps"],
            "accepted_authority": {"disabled": "implicit", "shadow": "implicit", "active": "bounded"},
        }

    def exercise_05_deterministic_packaging(self) -> dict[str, Any]:
        self._require_clean_or_development()
        first_dir = self.root / "wheel-a"
        second_dir = self.root / "wheel-b"
        first_dir.mkdir(exist_ok=True)
        second_dir.mkdir(exist_ok=True)
        first = first_dir / build_backend.build_wheel(str(first_dir))
        second = second_dir / build_backend.build_wheel(str(second_dir))
        first_hash = _sha256_file(first)
        second_hash = _sha256_file(second)
        if first.read_bytes() != second.read_bytes() or first_hash != second_hash:
            raise LabVerificationError("wheel builds are not byte deterministic")
        with zipfile.ZipFile(first) as archive:
            members = archive.infolist()
            if any(member.date_time != (1980, 1, 1, 0, 0, 0) for member in members):
                raise LabVerificationError("wheel member timestamps are not deterministic")
            if any(member.external_attr >> 16 != 0o100644 for member in members):
                raise LabVerificationError("wheel member permissions are not deterministic")
            names = [member.filename for member in members]
        with zipfile.ZipFile(second) as archive:
            second_names = archive.namelist()
        project = build_backend._project()
        dist_info = project.dist_info_directory()
        expected_names = [
            *(f"babcs/{path.name}" for path in sorted((SOURCE_ROOT / "babcs").glob("*.py"))),
            f"{dist_info}/METADATA",
            f"{dist_info}/WHEEL",
            f"{dist_info}/entry_points.txt",
            f"{dist_info}/licenses/{project.LICENSE_FILE}",
            f"{dist_info}/RECORD",
        ]
        if names != expected_names or second_names != expected_names:
            raise LabVerificationError("wheel members do not follow the deterministic backend order")
        self._wheel_path = first
        self._wheel_pair = (first, second)
        return {
            "development_mode": self.development,
            "release_evidence": not self.development,
            "wheel_filename": first.name,
            "first_wheel_sha256": first_hash,
            "second_wheel_sha256": second_hash,
            "wheel_hashes_match": True,
            "member_count": len(members),
            "member_order_matches_backend_contract": True,
            "fixed_timestamps": True,
            "fixed_permissions": True,
        }

    def exercise_06_source_wheel_equivalence(self) -> dict[str, Any]:
        self._require_clean_or_development()
        if self._wheel_path is None:
            self.exercise_05_deterministic_packaging()
        assert self._wheel_path is not None
        venv = self.root / "installed-venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, capture_output=True)
        python = venv / "bin/python"
        console = venv / "bin/babcs"
        subprocess.run(
            [str(python), "-m", "pip", "install", "--no-deps", str(self._wheel_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment["PYTHONNOUSERSITE"] = "1"
        imported_path = subprocess.run(
            [str(python), "-c", "import babcs; print(babcs.__file__)"],
            cwd=self.root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if str(REPOSITORY_ROOT) in imported_path or str(venv) not in imported_path:
            raise LabVerificationError("installed equivalence run imported the source tree")
        normalized_imported_path = (
            Path("<isolated-venv>")
            / Path(imported_path).resolve().relative_to(venv.resolve())
        ).as_posix()

        cases = {
            "rc_step": REPOSITORY_ROOT / "examples/rc_step.json",
            "switched_rc": REPOSITORY_ROOT / "benchmarks/cases/switched_rc.json",
            "buck_like_reduced_order": (
                REPOSITORY_ROOT / "examples/power_stage/buck_like_reduced_order.json"
            ),
            "h_bridge_rl_reduced_order": (
                REPOSITORY_ROOT / "examples/power_stage/h_bridge_rl_reduced_order.json"
            ),
            "dc_link_rlc_reduced_order": (
                REPOSITORY_ROOT / "examples/power_stage/dc_link_rlc_reduced_order.json"
            ),
        }
        evidence = {}
        for case_id, case_path in cases.items():
            source_dir = self.root / f"source-{case_id}"
            module_dir = self.root / f"module-{case_id}"
            console_dir = self.root / f"console-{case_id}"
            for directory in (source_dir, module_dir, console_dir):
                directory.mkdir()
            source_env = os.environ.copy()
            source_env["PYTHONPATH"] = str(SOURCE_ROOT)
            _run_simulation_command(
                [sys.executable, "-m", "babcs"],
                case_path,
                source_dir,
                cwd=REPOSITORY_ROOT,
                environment=source_env,
            )
            _run_simulation_command(
                [str(python), "-m", "babcs"],
                case_path,
                module_dir,
                cwd=self.root,
                environment=environment,
            )
            _run_simulation_command(
                [str(console)],
                case_path,
                console_dir,
                cwd=self.root,
                environment=environment,
            )
            hashes = {}
            for filename in ("trace.csv", "summary.json"):
                source_bytes = (source_dir / filename).read_bytes()
                module_bytes = (module_dir / filename).read_bytes()
                console_bytes = (console_dir / filename).read_bytes()
                if not (source_bytes == module_bytes == console_bytes):
                    raise LabVerificationError(
                        f"source/module/console artifacts differ for {case_id} {filename}"
                    )
                hashes[filename] = hashlib.sha256(source_bytes).hexdigest()
            evidence[case_id] = {"artifacts_match": True, "artifact_sha256": hashes}
        source_observatory = self.root / "source-observatory"
        installed_observatory = self.root / "installed-observatory"
        source_observatory.mkdir()
        installed_observatory.mkdir()
        source_observatory_report = source_observatory / "observatory.json"
        installed_observatory_report = installed_observatory / "observatory.json"
        observatory_command = [
            str(REPOSITORY_ROOT / "tools/method_observatory.py"),
            "--case",
            "rc_step",
            "--quick",
            "--output",
        ]
        source_environment = os.environ.copy()
        source_environment["PYTHONPATH"] = str(SOURCE_ROOT)
        subprocess.run(
            [sys.executable, *observatory_command, str(source_observatory_report)],
            cwd=REPOSITORY_ROOT,
            env=source_environment,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [str(python), *observatory_command, str(installed_observatory_report)],
            cwd=REPOSITORY_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        if source_observatory_report.read_bytes() != installed_observatory_report.read_bytes():
            raise LabVerificationError("source and installed-wheel observatory smoke differ")
        return {
            "development_mode": self.development,
            "release_evidence": not self.development,
            "installed_module_path": normalized_imported_path,
            "source_tree_excluded": True,
            "cases": evidence,
            "observatory_smoke": {
                "artifacts_match": True,
                "artifact_sha256": _sha256_file(source_observatory_report),
            },
        }

    def exercise_07_event_alignment(self) -> dict[str, Any]:
        circuit, simulation, config = load_case(
            REPOSITORY_ROOT / "lab/07-event-alignment/case.json"
        )
        scheduled = circuit.breakpoints(simulation["start_time"], simulation["stop_time"])
        result = Simulator(BoundedIntegrator(config)).run(circuit, **simulation)
        accepted = [point.time for point in result.points if point.event_boundary]
        if len(accepted) != len(scheduled):
            raise LabVerificationError("event-alignment exercise changed the event count")
        for actual, expected in zip(accepted, scheduled, strict=True):
            if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1.0e-15):
                raise LabVerificationError("event-alignment exercise missed a scheduled time")
        event_points = [point for point in result.points if point.event_boundary]
        if any(point.history_reset_reason != "event" for point in event_points):
            raise LabVerificationError("event-alignment exercise did not reset history at an event")
        startup_after_event = 0
        for index, point in enumerate(result.points[:-1]):
            if not point.event_boundary:
                continue
            next_metrics = result.points[index + 1].metrics
            if next_metrics is not None and next_metrics.method.endswith("_startup"):
                startup_after_event += 1
        if startup_after_event != len(event_points) - int(event_points[-1].time == result.points[-1].time):
            raise LabVerificationError("event-alignment exercise did not restart multistep history")
        return {
            "scheduled_event_times": scheduled,
            "accepted_event_times": accepted,
            "event_count": len(accepted),
            "history_resets": summary_data(result)["history_resets"],
            "startup_steps_after_events": startup_after_event,
            "events_are_exactly_aligned": True,
        }

    def exercise_08_bound_coverage(self) -> dict[str, Any]:
        circuit, simulation, config = load_case(
            REPOSITORY_ROOT / "lab/08-bound-coverage/case.json"
        )
        result = Simulator(BoundedIntegrator(config)).run(circuit, **simulation)
        initial_candidate = result.points[0].state.evaluation.dynamic_state
        initial_authority = (
            _rc_voltage(result.points[0].time, 1000.0, 1.0e-6, 1.0, 0.0),
        )
        anchor_candidate = initial_candidate
        anchor_authority = initial_authority
        eligible = 0
        covered = 0
        maximum_error = 0.0
        maximum_bound = 0.0
        for point in result.points[1:]:
            metrics = point.metrics
            assert metrics is not None
            candidate = point.state.evaluation.dynamic_state
            authority = (_rc_voltage(point.time, 1000.0, 1.0e-6, 1.0, 0.0),)
            candidate_delta = tuple(
                value - anchor
                for value, anchor in zip(candidate, anchor_candidate, strict=True)
            )
            authority_delta = tuple(
                value - anchor
                for value, anchor in zip(authority, anchor_authority, strict=True)
            )
            epoch_error = weighted_rms(
                tuple(
                    value - authority_value
                    for value, authority_value in zip(
                        candidate_delta, authority_delta, strict=True
                    )
                ),
                candidate_delta,
                authority_delta,
                config.absolute_tolerance,
                config.relative_tolerance,
            )
            coverage_eligible = (
                math.isfinite(metrics.estimated_bound)
                and metrics.estimated_bound > 0.0
                and not metrics.periodic_reanchor
                and not point.event_boundary
            )
            if coverage_eligible:
                eligible += 1
                covered += int(epoch_error <= metrics.estimated_bound)
                maximum_error = max(maximum_error, epoch_error)
                maximum_bound = max(maximum_bound, metrics.estimated_bound)
            if metrics.periodic_reanchor:
                anchor_candidate = candidate
                anchor_authority = authority
        if eligible <= 0:
            raise LabVerificationError("bound-coverage exercise produced no eligible samples")
        coverage_ratio = covered / eligible
        if not 0.0 <= coverage_ratio <= 1.0:
            raise LabVerificationError("bound-coverage ratio is outside the probability interval")
        return {
            "eligible_samples": eligible,
            "covered_samples": covered,
            "empirical_coverage_ratio": coverage_ratio,
            "maximum_authority_epoch_drift_error": maximum_error,
            "maximum_recursive_internal_bound": maximum_bound,
            "formal_enclosure_claim": False,
        }

    def exercise_09_fallback_forensics(self) -> dict[str, Any]:
        circuit, simulation, config = load_case(
            REPOSITORY_ROOT / "examples/power_stage/h_bridge_rl_reduced_order.json"
        )
        result = Simulator(BoundedIntegrator(config)).run(circuit, **simulation)
        summary = summary_data(result)
        reasons = Counter(
            rejection.reason.split(":", 1)[0]
            for point in result.points
            for rejection in point.rejections
        )
        if summary["rejected_steps"] <= 0:
            raise LabVerificationError("fallback-forensics exercise emitted no rejection evidence")
        if summary["implicit_fallbacks"] <= 0:
            raise LabVerificationError("fallback-forensics exercise emitted no implicit fallback")
        if not reasons:
            raise LabVerificationError("fallback-forensics exercise emitted no classified causes")
        return {
            "reduced_order_numerical_experiment": True,
            "rejected_steps": summary["rejected_steps"],
            "implicit_fallbacks": summary["implicit_fallbacks"],
            "rejection_causes": dict(sorted(reasons.items())),
            "history_resets": summary["history_resets"],
            "accepted_stop_time": result.points[-1].time,
            "production_device_claim": False,
        }

    def exercise_10_ngspice_mapping(self) -> dict[str, Any]:
        manifest_path = REPOSITORY_ROOT / "benchmarks/external/manifest.json"
        manifest = load_external_manifest(manifest_path)
        category_counts: Counter[str] = Counter()
        feature_counts: Counter[str] = Counter()
        case_hashes: dict[str, str] = {}
        total_states = 0
        for case in manifest["cases"]:
            case_id = str(case["id"])
            input_path = (manifest_path.parent / str(case["input"])).resolve()
            circuit, _, _ = load_case(input_path)
            data = json.loads(input_path.read_text(encoding="utf-8"))
            netlist, state_names = generate_ngspice_netlist(data)
            if tuple(circuit.dynamic_names) != state_names:
                raise LabVerificationError(f"{case_id}: external state order differs from BAB-CS")
            if "wrdata external.dat" not in netlist:
                raise LabVerificationError(f"{case_id}: mapped netlist lacks deterministic output")
            category_counts[str(case["category"])] += 1
            feature_counts.update(str(feature) for feature in case["mapped_features"])
            case_hashes[case_id] = hashlib.sha256(input_path.read_bytes()).hexdigest()
            total_states += len(state_names)
        if len(case_hashes) != 20:
            raise LabVerificationError("ngspice-mapping exercise requires exactly 20 cases")
        return {
            "mapped_case_count": len(case_hashes),
            "category_counts": dict(sorted(category_counts.items())),
            "mapped_feature_count": len(feature_counts),
            "total_dynamic_states": total_states,
            "case_sha256": dict(sorted(case_hashes.items())),
            "external_tool_is_oracle": False,
        }

    def _require_clean_or_development(self) -> None:
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=REPOSITORY_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        if dirty and not self.development:
            raise LabVerificationError(
                "packaging exercises require a clean source tree; use --development for non-release evidence"
            )


def _run_simulation_command(command, case_path, output_dir, *, cwd, environment) -> None:
    subprocess.run(
        command
        + [
            "simulate",
            str(case_path),
            "--csv",
            str(output_dir / "trace.csv"),
            "--summary",
            str(output_dir / "summary.json"),
        ],
        cwd=cwd,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


def _rc_voltage(time, resistance, capacitance, source_voltage, initial_voltage) -> float:
    return source_voltage + (initial_voltage - source_voltage) * math.exp(
        -time / (resistance * capacitance)
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture_projection(report: dict[str, Any]) -> dict[str, Any]:
    removed = {
        "first_wheel_sha256",
        "second_wheel_sha256",
        "installed_module_path",
        "artifact_sha256",
        "development_mode",
        "release_evidence",
    }

    def project(value):
        if isinstance(value, dict):
            return {
                key: project(item)
                for key, item in sorted(value.items())
                if key not in removed
            }
        if isinstance(value, list):
            return [project(item) for item in value]
        return value

    return project(report)


def _verify_fixture(report: dict[str, Any], exercise_ids: list[str]) -> None:
    if not FIXTURE_PATH.is_file():
        raise LabVerificationError("lab verification fixture is missing")
    expected = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    actual = _fixture_projection(report)
    expected_by_id = {item["id"]: item for item in expected["exercises"]}
    actual_by_id = {item["id"]: item for item in actual["exercises"]}
    for exercise_id in exercise_ids:
        if expected_by_id.get(exercise_id) != actual_by_id.get(exercise_id):
            raise LabVerificationError(
                f"lab fixture differs for {exercise_id}; review and use --update-fixtures explicitly"
            )


def _update_fixture(report: dict[str, Any]) -> tuple[str, str]:
    old_hash = _sha256_file(FIXTURE_PATH) if FIXTURE_PATH.is_file() else "missing"
    payload = json.dumps(
        _fixture_projection(report),
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(payload, encoding="utf-8")
    return old_hash, _sha256_file(FIXTURE_PATH)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify BAB-CS teaching lab exercises")
    parser.add_argument("--exercise", action="append", choices=("all", *EXERCISES), required=True)
    parser.add_argument("--output")
    parser.add_argument("--development", action="store_true")
    parser.add_argument("--update-fixtures", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    exercise_ids = list(EXERCISES) if "all" in arguments.exercise else list(dict.fromkeys(arguments.exercise))
    verifier = LabVerifier(development=arguments.development)
    try:
        report = verifier.run(exercise_ids)
    finally:
        verifier.close()
    if arguments.update_fixtures:
        if set(exercise_ids) != set(EXERCISES):
            raise LabVerificationError("fixture updates require --exercise all")
        old_hash, new_hash = _update_fixture(report)
        print(
            f"WARNING: updated review-controlled lab fixture: {old_hash} -> {new_hash}",
            file=sys.stderr,
        )
    else:
        _verify_fixture(report, exercise_ids)
    payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if arguments.output:
        output = Path(arguments.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
