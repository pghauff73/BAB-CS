import copy
import importlib.util
import json
import math
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from babcs.io import load_case
from tools.benchmark_ngspice_runtime import (
    CaseSpec,
    build_isolated_wheel_environment,
    execute_runtime_benchmark,
    resolve_case_babcs_backend,
    select_fixed_accuracy_attempt,
)
from tools.compare_external import generate_ngspice_netlist
from tools.generate_runtime_cases import (
    DEFAULT_MANIFEST,
    DEFAULT_OUTPUT_ROOT,
    generate_runtime_case,
    generate_runtime_cases,
    load_runtime_manifest,
)
from tools.runtime_benchmark import (
    RuntimeBenchmarkError,
    analytic_authority,
    canonical_row_id,
    common_grid,
    interpolate_rows,
    native_rows_at_times,
    external_analytic_authority,
    parse_ngspice_rusage,
    refined_authority,
    summarize_samples,
    trajectory_error,
    validate_runtime_report,
    oscillator_metrics,
    write_speed_accuracy_svg,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class RuntimeBenchmarkTests(unittest.TestCase):
    def test_runtime_manifest_generates_complete_stable_scaling_inventory(self) -> None:
        manifest = load_runtime_manifest(DEFAULT_MANIFEST)
        self.assertEqual([family["id"] for family in manifest["families"]], [
            "rc_bank",
            "coupled_rc_ring",
            "coupled_rlc_ring",
            "rl_bank",
            "diode_rc_bank",
            "switched_rc_bank",
        ])
        result = generate_runtime_cases(DEFAULT_MANIFEST, DEFAULT_OUTPUT_ROOT, check=True)
        self.assertEqual(result["cases"], 42)
        self.assertEqual(result["families"], 6)
        self.assertEqual(
            {row["dynamic_state_count"] for row in result["metadata"]},
            {1, 2, 4, 8, 16, 32, 64, 128},
        )
        authorities = {
            family["id"]: family["authority"]["type"]
            for family in manifest["families"]
        }
        self.assertEqual(authorities["coupled_rc_ring"], "refined_trapezoidal")
        self.assertEqual(authorities["coupled_rlc_ring"], "refined_trapezoidal")
        self.assertEqual(
            next(
                family["dynamic_states_per_size"]
                for family in manifest["families"]
                if family["id"] == "coupled_rlc_ring"
            ),
            2,
        )
        self.assertEqual(authorities["diode_rc_bank"], "refined_trapezoidal")
        self.assertEqual(authorities["switched_rc_bank"], "analytic_switched_rc")
        profile_assignments = {
            family["id"]: family["babcs_profile"]
            for family in manifest["families"]
        }
        self.assertEqual(
            profile_assignments["rc_bank"],
            "active_heun_deferred4_smooth",
        )
        self.assertEqual(
            profile_assignments["coupled_rc_ring"],
            "active_heun_deferred4_smooth",
        )
        self.assertEqual(
            profile_assignments["coupled_rlc_ring"],
            "active_heun_deferred4_smooth",
        )
        self.assertEqual(
            profile_assignments["rl_bank"],
            "active_heun_deferred4_smooth",
        )
        self.assertEqual(
            profile_assignments["diode_rc_bank"],
            "active_ab2_reference1_nonlinear",
        )
        self.assertEqual(
            profile_assignments["switched_rc_bank"],
            "active_ab2_deferred4_events",
        )

    def test_repeated_channel_cases_preserve_simulation_and_channel_values(self) -> None:
        manifest = load_runtime_manifest(DEFAULT_MANIFEST)
        for family in manifest["families"]:
            small = generate_runtime_case(family, 1, manifest["babcs_profiles"])
            large = generate_runtime_case(family, 16, manifest["babcs_profiles"])
            with self.subTest(family=family["id"]):
                self.assertEqual(small["simulation"], large["simulation"])
                self.assertEqual(small["runtime_benchmark"]["authority"], large["runtime_benchmark"]["authority"])
                self.assertEqual(
                    small["runtime_benchmark"]["babcs_profile_id"],
                    family["babcs_profile"],
                )
                self.assertEqual(small["babcs"], large["babcs"])
                self.assertEqual(small["babcs"]["rollout_mode"], "active")
                self.assertEqual(
                    sum(element["type"] in {"capacitor", "inductor"} for element in large["elements"]),
                    32 if family["id"] == "coupled_rlc_ring" else 16,
                )

    def test_coupled_rc_family_adds_real_neighbor_coupling(self) -> None:
        manifest = load_runtime_manifest(DEFAULT_MANIFEST)
        family = next(
            family for family in manifest["families"]
            if family["id"] == "coupled_rc_ring"
        )
        case = generate_runtime_case(family, 8, manifest["babcs_profiles"])
        coupling = [
            element for element in case["elements"]
            if element["type"] == "resistor"
            and element["positive"].startswith("out")
            and element["negative"].startswith("out")
        ]
        self.assertEqual(len(coupling), 8)
        self.assertEqual(
            sum(element["name"].startswith("RIN") for element in case["elements"]),
            1,
        )

    def test_coupled_rlc_family_adds_mixed_energy_and_bounded_size_law(self) -> None:
        manifest = load_runtime_manifest(DEFAULT_MANIFEST)
        family = next(
            family for family in manifest["families"]
            if family["id"] == "coupled_rlc_ring"
        )
        for size in family["sizes"]:
            with self.subTest(size=size), tempfile.TemporaryDirectory() as directory:
                case = generate_runtime_case(family, size, manifest["babcs_profiles"])
                self.assertEqual(case["simulation"], family["simulation"])
                self.assertEqual(
                    case["runtime_benchmark"]["babcs_profile_id"],
                    family["babcs_profile"],
                )
                self.assertEqual(
                    sum(element["type"] == "capacitor" for element in case["elements"]),
                    size,
                )
                self.assertEqual(
                    sum(element["type"] == "inductor" for element in case["elements"]),
                    size,
                )
                coupling = [
                    element for element in case["elements"]
                    if element["type"] == "resistor"
                    and element["positive"].startswith("out")
                    and element["negative"].startswith("out")
                ]
                self.assertEqual(len(coupling), size if size > 2 else size - 1)
                path = Path(directory) / "case.json"
                path.write_text(json.dumps(case), encoding="utf-8")
                circuit, _, _ = load_case(path)
                self.assertEqual(circuit.dynamic_size, 2 * size)
                self.assertEqual(circuit.algebraic_size, 2 * size + 2)
                self.assertEqual(
                    circuit.dynamic_size + circuit.algebraic_size,
                    4 * size + 2,
                )
                _, state_names = generate_ngspice_netlist(
                    case,
                    output_filename="trajectory.dat",
                )
                self.assertEqual(len(state_names), 2 * size)

    def test_switched_rc_analytic_authority_tracks_off_and_on_segments(self) -> None:
        manifest = load_runtime_manifest(DEFAULT_MANIFEST)
        family = next(
            family for family in manifest["families"]
            if family["id"] == "switched_rc_bank"
        )
        parameters = family["parameters"]
        delay = float(parameters["delay"])
        width = float(parameters["width"])
        times = (0.0, delay, delay + width)
        authority = analytic_authority(family, 2, times)
        source = float(parameters["source_voltage"])
        initial = float(parameters["initial_voltage"])
        off_tau = (
            float(parameters["resistance"])
            + float(parameters["off_resistance"])
        ) * float(parameters["capacitance"])
        on_tau = (
            float(parameters["resistance"])
            + float(parameters["on_resistance"])
        ) * float(parameters["capacitance"])
        at_delay = source + (initial - source) * math.exp(-delay / off_tau)
        at_turn_off = source + (at_delay - source) * math.exp(-width / on_tau)
        self.assertEqual(authority[0], (initial, initial))
        self.assertEqual(authority[1], (at_delay, at_delay))
        self.assertEqual(authority[2], (at_turn_off, at_turn_off))

    def test_hybrid_backend_uses_reviewed_declared_mna_crossover(self) -> None:
        generate_runtime_cases(DEFAULT_MANIFEST, DEFAULT_OUTPUT_ROOT, check=True)

        def spec(case_id: str) -> CaseSpec:
            return CaseSpec(
                row_id="runtime-000000000000000000000000",
                inventory="size_scaling",
                case_id=case_id,
                title=case_id,
                path=DEFAULT_OUTPUT_ROOT / f"{case_id}.json",
                family_id=case_id.rsplit("-n", 1)[0],
                size=int(case_id.rsplit("-n", 1)[1]),
                family=None,
            )

        self.assertEqual(resolve_case_babcs_backend(spec("rc_bank-n004"), "hybrid"), "dense")
        self.assertEqual(resolve_case_babcs_backend(spec("rc_bank-n008"), "hybrid"), "scipy")
        self.assertEqual(resolve_case_babcs_backend(spec("coupled_rc_ring-n004"), "hybrid"), "dense")
        self.assertEqual(resolve_case_babcs_backend(spec("coupled_rc_ring-n008"), "hybrid"), "scipy")
        self.assertEqual(resolve_case_babcs_backend(spec("rc_bank-n064"), "dense"), "dense")

    def test_fixed_accuracy_selector_uses_native_work_before_error(self) -> None:
        attempts = [
            {
                "qualifies": False,
                "native_work": 5,
                "maximum_scaled_trajectory_error": 2.0,
                "nominal_step": 1.0,
                "step_divisor": 1,
            },
            {
                "qualifies": True,
                "native_work": 20,
                "maximum_scaled_trajectory_error": 0.1,
                "nominal_step": 0.25,
                "step_divisor": 4,
            },
            {
                "qualifies": True,
                "native_work": 10,
                "maximum_scaled_trajectory_error": 0.9,
                "nominal_step": 0.5,
                "step_divisor": 2,
            },
        ]
        selected = select_fixed_accuracy_attempt(attempts)
        self.assertIsNotNone(selected)
        self.assertEqual(selected["step_divisor"], 2)
        self.assertIsNone(select_fixed_accuracy_attempt(attempts[:1]))

    def test_fixed_accuracy_report_requires_bounded_sweeps_and_authority(self) -> None:
        report = self._synthetic_fixed_accuracy_report()
        validate_runtime_report(report)

        malformed_family_sweep = copy.deepcopy(report)
        malformed_family_sweep["configuration"]["fixed_accuracy"][
            "family_step_divisors"
        ]["switched_rc_bank"] = [4, 2]
        with self.assertRaisesRegex(RuntimeBenchmarkError, "invalid timestep"):
            validate_runtime_report(malformed_family_sweep)

        malformed_stop_policy = copy.deepcopy(report)
        malformed_stop_policy["configuration"]["fixed_accuracy"][
            "stop_at_first_qualifying"
        ] = "yes"
        with self.assertRaisesRegex(RuntimeBenchmarkError, "invalid timestep"):
            validate_runtime_report(malformed_stop_policy)

        unqualified_authority = copy.deepcopy(report)
        unqualified_authority["rows"][0]["accuracy"]["authority"][
            "qualified"
        ] = False
        with self.assertRaisesRegex(RuntimeBenchmarkError, "does not meet the target"):
            validate_runtime_report(unqualified_authority)

    @unittest.skipUnless(
        importlib.util.find_spec("scipy") is not None,
        "optional scipy backend unavailable",
    )
    def test_isolated_wheel_sparse_profile_records_dependencies_and_backend(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            python_path, wheel = build_isolated_wheel_environment(
                root,
                linear_backend="scipy",
            )
            output = root / "worker.json"
            completed = subprocess.run(
                [
                    str(python_path),
                    str(REPOSITORY_ROOT / "tools" / "runtime_babcs_worker.py"),
                    str(DEFAULT_OUTPUT_ROOT / "rc_bank-n004.json"),
                    "--output",
                    str(output),
                    "--forbidden-root",
                    str(REPOSITORY_ROOT),
                    "--linear-backend",
                    "scipy",
                ],
                cwd=root,
                env={**os.environ, "PYTHONPATH": ""},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["linear_backend"], "scipy")
            self.assertEqual(payload["babcs_configuration"]["rollout_mode"], "active")
            self.assertEqual(payload["babcs_configuration"]["candidate_method"], "heun")
            self.assertEqual(payload["babcs_configuration"]["reference_interval_steps"], 4)
            self.assertTrue(payload["source_tree_excluded"])
            self.assertEqual(wheel["linear_backend"], "scipy")
            self.assertIn("scipy", wheel["dependencies"])
            self.assertIn("numpy", wheel["dependencies"])

    def test_ngspice_rusage_parser_requires_reviewed_core_counters(self) -> None:
        fixture = (REPOSITORY_ROOT / "tests" / "fixtures" / "ngspice-rusage-46.txt").read_text(encoding="utf-8")
        parsed = parse_ngspice_rusage(fixture)
        self.assertEqual(parsed["linear_solver"], "SPARSE 1.3")
        self.assertEqual(parsed["counters"]["accepted_timepoints"], 25)
        self.assertAlmostEqual(parsed["counters"]["total_analysis_seconds"], 0.000233883)
        with self.assertRaisesRegex(RuntimeBenchmarkError, "missing required counters"):
            parse_ngspice_rusage(fixture.replace("Total iterations = 48\n", ""))
        with self.assertRaisesRegex(RuntimeBenchmarkError, "duplicate"):
            parse_ngspice_rusage(fixture + "\nTotal iterations = 48\n")
        with self.assertRaisesRegex(RuntimeBenchmarkError, "nonfinite"):
            parse_ngspice_rusage(fixture.replace("Matrix solve time = 2.00793E-06", "Matrix solve time = nan"))

    def test_statistics_and_bootstrap_are_deterministic(self) -> None:
        samples = [float(index) for index in range(1, 12)]
        first = summarize_samples(samples)
        second = summarize_samples(samples)
        self.assertEqual(first, second)
        self.assertEqual(first["median"], 6.0)
        self.assertEqual(first["p25"], 3.5)
        self.assertEqual(first["p75"], 8.5)
        self.assertIsNotNone(first["bootstrap_median_95"])

    def test_common_grid_interpolation_and_scaled_error(self) -> None:
        grid = common_grid(0.0, 1.0, 5)
        rows = ((0.0, 0.0), (0.5, 1.0), (1.0, 0.0))
        sampled = interpolate_rows(rows, 1, grid)
        self.assertEqual(sampled, ((0.0,), (0.5,), (1.0,), (0.5,), (0.0,)))
        error = trajectory_error(
            sampled,
            ((0.0,), (0.4,), (1.0,), (0.4,), (0.0,)),
            ("v(C1)",),
            absolute_tolerance=0.01,
            relative_tolerance=0.0,
        )
        self.assertAlmostEqual(error["maximum_scaled_trajectory_error"], 10.0)

    def test_native_row_sampling_requires_integrated_output_points(self) -> None:
        rows = ((0.0, 0.0), (0.5, 1.0), (1.0, 0.0))
        self.assertEqual(
            native_rows_at_times(rows, 1, (0.0, 0.5, 1.0)),
            ((0.0,), (1.0,), (0.0,)),
        )
        with self.assertRaisesRegex(RuntimeBenchmarkError, "missing"):
            native_rows_at_times(rows, 1, (0.25,))

    def test_refined_authority_can_integrate_to_requested_output_times(self) -> None:
        times = (0.0, 3.7e-5, 9.1e-5, 0.003)
        sampled, metadata = refined_authority(
            REPOSITORY_ROOT / "benchmarks/runtime/cases/rc_bank-n001.json",
            times,
            refinement_factor=4,
            sampling_mode="integrated_output_times",
        )
        self.assertEqual(len(sampled), len(times))
        self.assertEqual(metadata["sampling_mode"], "integrated_output_times")
        self.assertEqual(metadata["requested_output_times"], len(times))
        self.assertGreater(metadata["effective_minimum_step"], 0.0)
        self.assertLessEqual(
            metadata["effective_minimum_step"],
            metadata["configured_minimum_step"],
        )
        self.assertGreater(
            metadata["effective_anchor_interval_steps"],
            metadata["configured_anchor_interval_steps"],
        )
        self.assertEqual(metadata["work"]["replay_steps"], 0)
        self.assertEqual(metadata["output_interval_substeps"], 4)

    def test_refined_authority_reduces_only_offline_diagnostic_minimum_step(self) -> None:
        close_time = 0.001 + 5.0e-16
        times = (0.0, 0.001, close_time, 0.003)
        sampled, metadata = refined_authority(
            REPOSITORY_ROOT / "benchmarks/runtime/cases/rc_bank-n001.json",
            times,
            refinement_factor=4,
            sampling_mode="integrated_output_times",
        )
        self.assertEqual(len(sampled), len(times))
        self.assertEqual(metadata["configured_minimum_step"], 1.0e-15)
        self.assertLess(metadata["effective_minimum_step"], 1.0e-15)
        self.assertLessEqual(
            metadata["effective_minimum_step"],
            close_time - times[1],
        )
        self.assertLessEqual(
            metadata["effective_minimum_step"],
            4.0 * math.ulp(times[1]),
        )

    def test_oscillator_metrics_keep_phase_and_energy_separate(self) -> None:
        times = common_grid(0.0, 2.0 * math.pi, 201)
        authority = tuple((math.cos(time), -math.sin(time)) for time in times)
        actual = tuple((math.cos(time + 0.01), -math.sin(time + 0.01)) for time in times)
        metrics = oscillator_metrics(
            actual,
            authority,
            times,
            {
                "elements": [
                    {"type": "capacitor", "capacitance": 1.0},
                    {"type": "inductor", "inductance": 1.0},
                ]
            },
        )
        self.assertIsNotNone(metrics)
        self.assertIn("final_phase_error_radians", metrics)
        self.assertIn("relative_energy_span", metrics)
        self.assertLess(metrics["relative_energy_span"], 1.0e-12)

    def test_row_identity_is_semantic_and_order_independent(self) -> None:
        first = canonical_row_id({"case_id": "rc", "profile": "quick", "size": 4})
        second = canonical_row_id({"size": 4, "profile": "quick", "case_id": "rc"})
        changed = canonical_row_id({"case_id": "rc", "profile": "quick", "size": 8})
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)

    def test_supported_external_linear_cases_use_analytic_authority(self) -> None:
        for case_id, relative_path in (
            ("rc_step", "benchmarks/cases/rc_step.json"),
            ("rl_step", "benchmarks/cases/rl_step.json"),
            ("lc_long", "benchmarks/cases/lc_long.json"),
            ("rlc_damped", "benchmarks/cases/rlc_damped.json"),
        ):
            data = json.loads((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8"))
            times = common_grid(
                float(data["simulation"]["start_time"]),
                float(data["simulation"]["stop_time"]),
                21,
            )
            authority = external_analytic_authority(case_id, data, times)
            with self.subTest(case=case_id):
                self.assertIsNotNone(authority)
                rows, metadata = authority
                self.assertEqual(len(rows), len(times))
                self.assertTrue(metadata["type"].startswith("analytic_"))

    def test_headline_svg_is_deterministic_and_keeps_failure_markers(self) -> None:
        report = self._synthetic_report()
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.svg"
            second = Path(directory) / "second.svg"
            write_speed_accuracy_svg(first, report)
            write_speed_accuracy_svg(second, report)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            rendered = first.read_text(encoding="utf-8")
            self.assertIn("HOW FAST?", rendered)
            self.assertIn("HOW ACCURATE?", rendered)
            self.assertIn("1×", rendered)
            self.assertIn("ACCURACY TARGET", rendered)
            self.assertIn("#b42318", rendered)
            self.assertIn("RC bank", rendered)

    @unittest.skipUnless(Path("/usr/bin/time").is_file(), "GNU Time is required")
    def test_isolated_wheel_supervisor_smoke_with_ngspice_stub(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "fake-ngspice"
            executable.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = \"--version\" ]; then\n"
                "  echo 'ngspice-46-stub : runtime test'\n"
                "  exit 0\n"
                "fi\n"
                "cat > ngspice.log <<'EOF'\n"
                "Using SPARSE 1.3 as Direct Linear Solver\n"
                "Total iterations = 8\nTransient iterations = 8\nCircuit Equations = 4\n"
                "Transient timepoints = 4\nAccepted timepoints = 4\nRejected timepoints = 0\n"
                "Total analysis time (seconds) = 0.001\nMatrix load time = 0.0001\n"
                "Matrix reorder time = 0.00001\nMatrix factor time = 0.00002\nMatrix solve time = 0.00003\n"
                "Transient analysis time = 0.0009\nTransient load time = 0.0001\n"
                "Transient factor time = 0.00002\nTransient solve time = 0.00003\n"
                "Maximum ngspice program size = 10 MB.\nEOF\n"
                "cat > external.dat <<'EOF'\n"
                "time bab_state_0\n"
                "0.001 0.6321205588\n"
                "0.002 0.8646647168\n"
                "0.003 0.9502129316\n"
                "EOF\n",
                encoding="utf-8",
            )
            executable.chmod(0o755)
            output = root / "artifacts"
            report = execute_runtime_benchmark(
                manifest_path=DEFAULT_MANIFEST,
                external_manifest_path=REPOSITORY_ROOT / "benchmarks" / "external" / "manifest.json",
                output_root=output,
                profile_name="quick",
                warmups=0,
                repeats=1,
                rounds=1,
                selected_case="rc_bank-n001",
                ngspice_executable=str(executable),
                cpu=None,
                timeout=30.0,
                overwrite=False,
                publish_docs=False,
            )
            self.assertEqual(report["rows"][0]["status"], "success")
            self.assertTrue(report["rows"][0]["source_wheel_equivalent"])
            self.assertTrue(report["rows"][0]["accuracy"]["ngspice_evaluation_initial_point_injected"])
            self.assertTrue((output / "speedup-accuracy-by-size.svg").is_file())
            self.assertTrue((output / "raw-samples.json").is_file())

    @unittest.skipUnless(Path("/usr/bin/time").is_file(), "GNU Time is required")
    def test_failed_ngspice_child_remains_visible_in_report_and_chart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "failing-ngspice"
            executable.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = \"--version\" ]; then\n"
                "  echo 'ngspice-46-failing-stub'\n"
                "  exit 0\n"
                "fi\n"
                "exit 7\n",
                encoding="utf-8",
            )
            executable.chmod(0o755)
            output = root / "artifacts"
            report = execute_runtime_benchmark(
                manifest_path=DEFAULT_MANIFEST,
                external_manifest_path=REPOSITORY_ROOT / "benchmarks" / "external" / "manifest.json",
                output_root=output,
                profile_name="quick",
                warmups=0,
                repeats=1,
                rounds=1,
                selected_case="rc_bank-n001",
                ngspice_executable=str(executable),
                cpu=None,
                timeout=30.0,
                overwrite=False,
                publish_docs=False,
            )
            row = report["rows"][0]
            self.assertEqual(row["status"], "failed")
            self.assertIn("ngspice", row["failure_reason"])
            self.assertIn(
                "#b42318",
                (output / "speedup-accuracy-by-size.svg").read_text(encoding="utf-8"),
            )

    @staticmethod
    def _synthetic_report() -> dict[str, object]:
        def row(case_id: str, size: int, mna: int, *, status: str = "success") -> dict[str, object]:
            success = status == "success"
            return {
                "row_id": canonical_row_id({"case_id": case_id, "size": size}),
                "inventory": "size_scaling",
                "case_id": case_id,
                "family_id": "rc_bank",
                "size": size,
                "status": status,
                "circuit_size": {"declared_mna_unknowns": mna},
                "speedup_x": 2.0 if success else None,
                "runtime": {"speedup_bootstrap_95": None},
                "accuracy": {
                    "babcs": {"maximum_scaled_trajectory_error": 0.5} if success else None,
                    "ngspice": {"maximum_scaled_trajectory_error": 0.25} if success else None,
                },
            }
        return {
            "environment": {
                "machine": {"processor_model": "Test CPU"},
                "ngspice": {"version": "ngspice-46-test"},
            },
            "configuration": {
                "profile": "quick",
                "warmups": 1,
                "repeats": 3,
                "rounds": 1,
                "accuracy": {"target_scaled_error": 1.0},
            },
            "rows": [row("rc-bank-1", 1, 5), row("rc-bank-4", 4, 14), row("rc-bank-16", 16, 50, status="failed")],
        }

    @staticmethod
    def _synthetic_fixed_accuracy_report() -> dict[str, object]:
        return {
            "schema_version": 1,
            "environment": {"babcs_wheel": {"linear_backend": "dense"}},
            "configuration": {
                "babcs_linear_backend": "dense",
                "babcs_backend_policy": {
                    "requested": "dense",
                    "sparse_minimum_declared_mna_unknowns": None,
                },
                "accuracy_mode": "fixed_accuracy",
                "accuracy": {"target_scaled_error": 1.0},
                "babcs_profiles": {
                    "active_heun_deferred4_smooth": {
                        "description": "Synthetic active profile.",
                        "config": {
                            "rollout_mode": "active",
                            "candidate_method": "heun",
                            "reference_method": "trapezoidal",
                            "reference_interval_steps": 4,
                        },
                    }
                },
                "fixed_accuracy": {
                    "step_divisors": [1, 2],
                    "family_step_divisors": {"switched_rc_bank": [1, 2, 4]},
                    "stop_at_first_qualifying": True,
                    "maximum_estimated_calibration_points": 100,
                    "maximum_estimated_calibration_trace_values": 200,
                    "maximum_estimated_authority_trace_values": 400,
                    "authority_refinement_factor": 8,
                    "authority_convergence_scaled_error_cap": 0.25,
                },
            },
            "rows": [
                {
                    "row_id": canonical_row_id(
                        {"case_id": "rc_bank-n001", "size": 1}
                    ),
                    "status": "success",
                    "accuracy_mode": "fixed_accuracy",
                    "accuracy_sweep": {"qualified": True},
                    "babcs_linear_backend": "dense",
                    "babcs_profile": {
                        "id": "active_heun_deferred4_smooth",
                        "source": "runtime_manifest",
                        "description": "Synthetic active profile.",
                        "declared_overrides": {
                            "rollout_mode": "active",
                            "candidate_method": "heun",
                            "reference_method": "trapezoidal",
                            "reference_interval_steps": 4,
                        },
                        "effective_configuration": {
                            "rollout_mode": "active",
                            "candidate_method": "heun",
                            "reference_method": "trapezoidal",
                            "reference_interval_steps": 4,
                        },
                    },
                    "semantic_equality": {
                        "babcs_configuration_matches": True,
                    },
                    "circuit_size": {"declared_mna_unknowns": 5},
                    "speedup_x": 0.5,
                    "source_wheel_equivalent": True,
                    "runtime": {
                        "babcs": {"analysis_seconds": {"median": 0.2}},
                        "ngspice": {"analysis_seconds": {"median": 0.1}},
                    },
                    "memory": {
                        "babcs": {"maximum_rss_kib": {"median": 1024}},
                        "ngspice": {"maximum_rss_kib": {"median": 1024}},
                    },
                    "accuracy": {
                        "authority": {"qualified": True},
                        "babcs": {"maximum_scaled_trajectory_error": 0.5},
                        "ngspice": {"maximum_scaled_trajectory_error": 0.25},
                    },
                }
            ],
            "claim_boundary": "Synthetic validator fixture.",
        }


if __name__ == "__main__":
    unittest.main()
