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

    def test_unsupported_diode_thermal_voltage_fails_closed(self) -> None:
        data = json.loads(
            (REPOSITORY_ROOT / "benchmarks" / "cases" / "diode_clip.json").read_text(
                encoding="utf-8"
            )
        )
        diode = next(element for element in data["elements"] if element["type"] == "diode")
        diode["thermal_voltage"] = 0.03
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


if __name__ == "__main__":
    unittest.main()
