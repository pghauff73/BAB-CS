from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.compare_external import (
    ExternalComparisonError,
    generate_ngspice_netlist,
    parse_ngspice_wrdata,
    run_external_comparison,
)
from tools.run_external_suite import load_external_manifest, reference_projection


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ExternalComparisonTests(unittest.TestCase):
    def test_rc_netlist_preserves_values_and_state_vector(self) -> None:
        data = json.loads(
            (REPOSITORY_ROOT / "benchmarks" / "cases" / "rc_step.json").read_text(
                encoding="utf-8"
            )
        )
        netlist, state_names = generate_ngspice_netlist(data)
        self.assertIn("RR1 vin out 1000", netlist)
        self.assertIn("CC1 out 0", netlist)
        self.assertIn("let bab_state_0 = v(out)", netlist)
        self.assertIn("wrdata external.dat bab_state_0", netlist)
        self.assertEqual(state_names, ("v(C1)",))

    def test_external_netlist_preserves_dynamic_initial_conditions(self) -> None:
        data = json.loads(
            (REPOSITORY_ROOT / "benchmarks" / "cases" / "rl_step.json").read_text(
                encoding="utf-8"
            )
        )
        inductor = next(element for element in data["elements"] if element["type"] == "inductor")
        inductor["initial_current"] = 0.125
        netlist, state_names = generate_ngspice_netlist(data)
        self.assertIn("IC=0.125", netlist)
        self.assertIn("let bab_state_0 = i(LL1)", netlist)
        self.assertEqual(state_names, ("i(L1)",))

    def test_switch_mapping_uses_explicit_control_source(self) -> None:
        data = json.loads(
            (REPOSITORY_ROOT / "benchmarks" / "cases" / "switched_rc.json").read_text(
                encoding="utf-8"
            )
        )
        netlist, _ = generate_ngspice_netlist(data)
        self.assertIn("VCTRL_S1 bab_ctrl_s1 0 PULSE", netlist)
        self.assertIn("SS1 out 0 bab_ctrl_s1 0 BABSW_S1", netlist)
        self.assertIn(".model BABSW_S1 SW(", netlist)

    def test_external_state_order_matches_babcs_capacitors_then_inductors(self) -> None:
        data = json.loads(
            (
                REPOSITORY_ROOT
                / "benchmarks"
                / "external"
                / "cases"
                / "rlc_driven.json"
            ).read_text(encoding="utf-8")
        )
        netlist, state_names = generate_ngspice_netlist(data)
        self.assertEqual(state_names, ("v(C1)", "i(L1)"))
        self.assertLess(
            netlist.index("let bab_state_0 = v(out)"),
            netlist.index("let bab_state_1 = i(LL1)"),
        )

    def test_diode_mapping_preserves_thermal_voltage_with_ideality_factor(self) -> None:
        data = json.loads(
            (
                REPOSITORY_ROOT
                / "examples"
                / "power_stage"
                / "buck_like_reduced_order.json"
            ).read_text(
                encoding="utf-8"
            )
        )
        netlist, _ = generate_ngspice_netlist(data)
        self.assertIn("DD_FREE 0 sw BABD_D_FREE", netlist)
        self.assertIn(
            f".model BABD_D_FREE D(Is=1.0000000000000001e-09 N={format(0.05 / 0.02585, '.17g')})",
            netlist,
        )

    def test_invalid_diode_parameters_fail_closed(self) -> None:
        data = json.loads(
            (REPOSITORY_ROOT / "benchmarks" / "cases" / "diode_clip.json").read_text(
                encoding="utf-8"
            )
        )
        diode = next(element for element in data["elements"] if element["type"] == "diode")
        diode["thermal_voltage"] = 0.0
        with self.assertRaisesRegex(ExternalComparisonError, "thermal_voltage"):
            generate_ngspice_netlist(data)

    def test_wrdata_parser_validates_shape_and_time(self) -> None:
        rows = parse_ngspice_wrdata("time v(out)\n0 0\n1e-3 0.5\n", 1)
        self.assertEqual(rows[-1], (1.0e-3, 0.5))
        with self.assertRaises(ExternalComparisonError):
            parse_ngspice_wrdata("time v(out)\n0 0\n0 1\n", 1)

    def test_external_comparison_runs_through_deterministic_stub(self) -> None:
        case_path = REPOSITORY_ROOT / "benchmarks" / "cases" / "rc_step.json"
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "fake-ngspice"
            executable.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = \"--version\" ]; then\n"
                "  echo 'fake-ngspice 1.0'\n"
                "  exit 0\n"
                "fi\n"
                "cat > external.dat <<'EOF'\n"
                "time v(out,0)\n"
                "0 0\n"
                "0.001 0.6321205588285577\n"
                "EOF\n"
                "echo ok > ngspice.log\n",
                encoding="utf-8",
            )
            executable.chmod(0o755)
            report, netlist, raw, log = run_external_comparison(
                case_path,
                executable=str(executable),
                mode="active",
            )
        self.assertEqual(report["external_tool"]["version"], "fake-ngspice 1.0")
        self.assertEqual(report["sample_count"], 2)
        self.assertEqual(len(report["source"]["source_tree_sha256"]), 64)
        self.assertEqual(report["configuration"]["mode"], "active")
        self.assertIn("python", report["environment"])
        self.assertIn("v(C1)", report["accuracy"])
        self.assertIn("wrdata external.dat", netlist)
        self.assertIn("0.6321205588285577", raw)
        self.assertIn("ok", log)

    def test_missing_external_executable_fails_explicitly(self) -> None:
        with self.assertRaisesRegex(ExternalComparisonError, "executable not found"):
            run_external_comparison(
                REPOSITORY_ROOT / "benchmarks" / "cases" / "rc_step.json",
                executable="babcs-definitely-missing-ngspice",
            )

    def test_external_manifest_maps_exactly_twenty_unique_cases(self) -> None:
        manifest = load_external_manifest(
            REPOSITORY_ROOT / "benchmarks" / "external" / "manifest.json"
        )
        case_ids = [str(case["id"]) for case in manifest["cases"]]
        self.assertEqual(len(case_ids), 20)
        self.assertEqual(len(set(case_ids)), 20)
        self.assertEqual(
            sum(bool(case.get("reduced_order", False)) for case in manifest["cases"]),
            3,
        )
        self.assertTrue(
            all(case["engineering_question"].endswith("?") for case in manifest["cases"])
        )

    def test_reference_projection_omits_environment_dependent_artifact_hashes(self) -> None:
        case = {
            "id": "case",
            "title": "Case",
            "category": "linear",
            "input": "case.json",
            "engineering_question": "Question?",
            "mapped_features": ["resistor"],
            "reduced_order": False,
            "case_sha256": "a" * 64,
            "netlist_sha256": "b" * 64,
            "raw_output_sha256": "c" * 64,
            "external_log_sha256": "d" * 64,
            "state_names": ["v(C1)"],
            "sample_count": 2,
            "maximum_absolute_error": 1.0,
            "maximum_scaled_error": 2.0,
            "maximum_rms_absolute_error": 0.5,
            "artifact_sha256": {"report": "e" * 64},
        }
        projection = reference_projection(
            {
                "manifest": "benchmarks/external/manifest.json",
                "manifest_sha256": "f" * 64,
                "external_tool": {"name": "ngspice", "version": "ngspice-46"},
                "mode": "active",
                "case_count": 1,
                "cases": [case],
                "claim_boundary": "Scoped evidence.",
            }
        )
        self.assertNotIn("artifact_sha256", projection["cases"][0])
        self.assertNotIn("raw_output_sha256", projection["cases"][0])
        self.assertEqual(projection["case_count"], 1)


if __name__ == "__main__":
    unittest.main()
