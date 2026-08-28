from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from babcs import BABCSConfig, BoundedIntegrator
from babcs.io import load_case
from tools.bound_coverage_atlas import (
    _global_common_policy_frontier,
    _modal_basis_metadata,
    _modal_epoch_group_diagnostic,
    _order_aware_sample_diagnostic,
    _statewise_epoch_state_diagnostic,
    _statewise_four_level_sample_diagnostic,
    _statewise_four_level_state_diagnostic,
    _symmetric_eigenbasis,
    _temporally_align_scalar_sequences,
    _two_term_design_metadata,
    _two_term_modal_group_diagnostic,
    execute_bound_atlas,
    execute_runtime_bound_atlas,
    write_atlas_plots,
    write_sample_csv,
)
from tools.method_observatory import DEFAULT_MANIFEST, execute_observatory


DUAL_REFERENCE_MANIFEST = Path("benchmarks/atlas/runtime-dual-reference.json")
GLOBAL_DUAL_TRAJECTORY_MANIFEST = Path(
    "benchmarks/atlas/runtime-global-dual-trajectory.json"
)
GLOBAL_REFINEMENT_PAIR_SWEEP_MANIFEST = Path(
    "benchmarks/atlas/runtime-global-refinement-pair-sweep.json"
)
GLOBAL_ORDER_AWARE_MANIFEST = Path(
    "benchmarks/atlas/runtime-global-order-aware.json"
)
GLOBAL_STATEWISE_FOUR_LEVEL_MANIFEST = Path(
    "benchmarks/atlas/runtime-global-statewise-four-level.json"
)
GLOBAL_STATEWISE_EPOCH_MANIFEST = Path(
    "benchmarks/atlas/runtime-global-statewise-epoch.json"
)
GLOBAL_MODAL_EPOCH_MANIFEST = Path(
    "benchmarks/atlas/runtime-global-modal-epoch.json"
)
GLOBAL_TEMPORAL_MODAL_EPOCH_MANIFEST = Path(
    "benchmarks/atlas/runtime-global-temporal-modal-epoch.json"
)
GLOBAL_TWO_TERM_MODAL_MANIFEST = Path(
    "benchmarks/atlas/runtime-global-two-term-modal.json"
)


class BoundCoverageAtlasTests(unittest.TestCase):
    def test_quick_rc_atlas_reconciles_and_is_deterministic(self) -> None:
        observatory, _ = execute_observatory(
            DEFAULT_MANIFEST,
            selected_cases={"rc_step"},
            quick=True,
        )
        first = execute_bound_atlas(
            observatory,
            observatory_manifest_path=DEFAULT_MANIFEST,
        )
        second = execute_bound_atlas(
            observatory,
            observatory_manifest_path=DEFAULT_MANIFEST,
        )
        self.assertEqual(
            json.dumps(first, sort_keys=True, allow_nan=False),
            json.dumps(second, sort_keys=True, allow_nan=False),
        )
        self.assertEqual(len(first["aggregates"]), 14)
        self.assertEqual(
            first["sample_count"],
            sum(row["diagnostics"]["accepted_steps"] for row in observatory["results"]),
        )
        self.assertTrue(first["anchors"])
        self.assertTrue(
            all("actual_authority_error" in sample for sample in first["samples"])
        )
        self.assertTrue(
            all("recursive_internal_bound" in sample for sample in first["samples"])
        )
        self.assertTrue(
            all(
                aggregate["empirical_coverage_fraction"] is None
                or 0.0 <= aggregate["empirical_coverage_fraction"] <= 1.0
                for aggregate in first["aggregates"]
            )
        )

    def test_atlas_csv_and_plots_are_written(self) -> None:
        observatory, _ = execute_observatory(
            DEFAULT_MANIFEST,
            selected_cases={"rc_step"},
            quick=True,
        )
        atlas = execute_bound_atlas(
            observatory,
            observatory_manifest_path=DEFAULT_MANIFEST,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "samples.csv"
            plots = root / "plots"
            write_sample_csv(csv_path, atlas)
            write_atlas_plots(plots, atlas)
            self.assertIn("actual_authority_error", csv_path.read_text(encoding="utf-8"))
            self.assertEqual(len(list(plots.glob("*.svg"))), 5)

    def test_runtime_profile_atlas_is_deterministic_and_decomposes_the_bound(self) -> None:
        first = execute_runtime_bound_atlas(selected_cases={"rc_bank-n001"})
        second = execute_runtime_bound_atlas(selected_cases={"rc_bank-n001"})
        self.assertEqual(
            json.dumps(first, sort_keys=True, allow_nan=False),
            json.dumps(second, sort_keys=True, allow_nan=False),
        )
        self.assertEqual(first["requested_case_count"], 1)
        self.assertEqual(first["qualified_case_count"], 1)
        self.assertEqual(first["unqualified_case_count"], 0)
        self.assertEqual(
            first["authority_qualifications"][0]["status"],
            "qualified",
        )
        aggregate = first["aggregates"][0]
        self.assertEqual(aggregate["babcs_profile_id"], "active_heun_deferred4_smooth")
        self.assertEqual(aggregate["step_divisor"], 1)
        self.assertGreater(aggregate["maximum_embedded_defect"], 0.0)
        self.assertGreater(aggregate["maximum_propagated_prior_bound"], 0.0)
        self.assertIn("embedded_fast", aggregate["coverage_by_authority_transfer"])
        sample = first["samples"][0]
        for field in (
            "propagated_prior_bound",
            "pre_reset_local_defect",
            "embedded_defect",
            "corrected_reference_defect",
            "residual_defect",
            "authority_transfer_kind",
            "uncovered_authority_gap",
        ):
            self.assertIn(field, sample)

    def test_dual_reference_atlas_reports_coverage_and_refinement_work(self) -> None:
        atlas = execute_runtime_bound_atlas(
            DUAL_REFERENCE_MANIFEST,
            selected_cases={"rc_bank-n001"},
        )
        aggregate = atlas["aggregates"][0]
        self.assertEqual(aggregate["variant_id"], "dual_reference")
        self.assertGreater(aggregate["reference_refinement_solve_count"], 0)
        self.assertGreater(aggregate["maximum_reference_discretization_defect"], 0.0)
        self.assertGreater(aggregate["maximum_reference_uncertainty"], 0.0)
        self.assertGreater(aggregate["work"]["reference_solves"], 0)
        self.assertGreater(aggregate["work"]["deterministic_work_units"], 0)
        self.assertGreaterEqual(
            aggregate["empirical_total_uncertainty_coverage_fraction"],
            aggregate["empirical_coverage_fraction"],
        )

    def test_global_dual_trajectory_reports_qualification_curve(self) -> None:
        atlas = execute_runtime_bound_atlas(
            GLOBAL_DUAL_TRAJECTORY_MANIFEST,
            selected_cases={"rc_bank-n001"},
        )
        aggregate = atlas["aggregates"][0]
        self.assertEqual(aggregate["variant_id"], "global_dual_trajectory")
        self.assertGreater(aggregate["maximum_global_reference_epoch_discrepancy"], 0.0)
        self.assertGreater(aggregate["maximum_global_refined_epoch_authority_error"], 0.0)
        self.assertGreaterEqual(
            aggregate["global_total_uncertainty_coverage_fraction"],
            aggregate["empirical_coverage_fraction"],
        )
        curve = aggregate["global_trajectory_coverage_by_safety_factor"]
        self.assertEqual(tuple(curve), ("1", "2", "4", "8", "16"))
        self.assertTrue(
            all(
                0.0 <= row["reference_estimator_coverage_fraction"] <= 1.0
                and 0.0 <= row["babcs_total_coverage_fraction"] <= 1.0
                for row in curve.values()
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            write_atlas_plots(directory, atlas)
            self.assertEqual(len(list(Path(directory).glob("*.svg"))), 6)

    def test_global_refinement_pair_sweep_reports_pareto_frontier(self) -> None:
        atlas = execute_runtime_bound_atlas(
            GLOBAL_REFINEMENT_PAIR_SWEEP_MANIFEST,
            selected_cases={"rc_bank-n001"},
        )
        aggregate = atlas["aggregates"][0]
        sweep = aggregate["global_refinement_pair_sweep"]
        self.assertEqual(tuple(sweep), ("2x4", "4x8", "8x16", "16x32"))
        self.assertEqual(
            tuple(aggregate["global_dual_trajectory"]["factor_trajectories"]),
            ("2", "4", "8", "16", "32"),
        )
        self.assertTrue(aggregate["global_refinement_pair_pareto_frontier"])
        self.assertTrue(atlas["global_refinement_common_policy_frontier"])
        self.assertEqual(
            atlas["global_refinement_work_accounting"]["unit"],
            "unweighted solver events and iterations",
        )
        self.assertEqual(
            aggregate["circuit_size"]["declared_mna_unknowns"],
            aggregate["circuit_size"]["dynamic_state_count"]
            + aggregate["circuit_size"]["algebraic_unknown_count"],
        )
        self.assertTrue(
            all(
                row["pair_id"] in sweep
                and row["safety_factor"] in {1.0, 2.0, 4.0, 8.0, 16.0}
                for row in aggregate["global_refinement_pair_pareto_frontier"]
            )
        )
        self.assertEqual(
            aggregate["global_dual_trajectory"]["sweep_deterministic_work_units"],
            sum(
                row["work"]["deterministic_work_units"]
                for row in aggregate["global_dual_trajectory"][
                    "factor_trajectories"
                ].values()
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_sample_csv(root / "samples.csv", atlas)
            write_atlas_plots(root / "plots", atlas)
            self.assertIn(
                '"2x4"',
                (root / "samples.csv").read_text(encoding="utf-8"),
            )
            self.assertEqual(len(list((root / "plots").glob("*.svg"))), 8)

    def test_common_policy_frontier_rejects_case_specific_cherry_picking(self) -> None:
        def aggregate(
            *,
            first_coverage: float,
            first_inflation: float,
            second_coverage: float,
            second_inflation: float,
        ) -> dict[str, object]:
            def pair(coverage: float, inflation: float, work: int) -> dict[str, object]:
                return {
                    "coarse_refinement_factor": 2 if work == 10 else 4,
                    "fine_refinement_factor": 4 if work == 10 else 8,
                    "coverage_by_safety_factor": {
                        "1": {
                            "safety_factor": 1.0,
                            "babcs_total_coverage_fraction": coverage,
                            "reference_estimator_coverage_fraction": coverage - 0.01,
                            "median_uncertainty_to_authority_error_ratio": inflation,
                            "p95_uncertainty_to_authority_error_ratio": inflation * 10.0,
                            "independent_pair_work_units": work,
                        }
                    },
                }

            return {
                "global_refinement_pair_sweep": {
                    "2x4": pair(first_coverage, first_inflation, 10),
                    "4x8": pair(second_coverage, second_inflation, 20),
                }
            }

        frontier = _global_common_policy_frontier(
            [
                aggregate(
                    first_coverage=1.0,
                    first_inflation=100.0,
                    second_coverage=0.95,
                    second_inflation=10.0,
                ),
                aggregate(
                    first_coverage=0.8,
                    first_inflation=50.0,
                    second_coverage=0.95,
                    second_inflation=10.0,
                ),
            ]
        )
        self.assertEqual(
            {(row["pair_id"], row["safety_factor"]) for row in frontier},
            {("2x4", 1.0), ("4x8", 1.0)},
        )
        by_pair = {row["pair_id"]: row for row in frontier}
        self.assertEqual(
            by_pair["2x4"]["minimum_babcs_total_coverage_fraction"],
            0.8,
        )
        self.assertEqual(by_pair["4x8"]["case_count"], 2)

    def test_order_aware_sample_diagnostic_is_gated_and_fail_closed(self) -> None:
        triplet = {
            "triplet_id": "2x4x8",
            "coarse_refinement_factor": 2,
            "middle_refinement_factor": 4,
            "fine_refinement_factor": 8,
            "coarse_pair_id": "2x4",
            "fine_pair_id": "4x8",
            "refinement_ratio": 2.0,
        }
        settings = {
            "expected_order": 2.0,
            "minimum_observed_order": 1.0,
            "maximum_observed_order": 3.0,
            "discrepancy_floor": 1.0e-12,
        }

        def pair(discrepancy: float, authority_error: float) -> dict[str, float]:
            return {
                "epoch_discrepancy": discrepancy,
                "refined_epoch_authority_error": authority_error,
            }

        qualified = _order_aware_sample_diagnostic(
            triplet,
            settings,
            pair(4.0, 1.0),
            pair(1.0, 0.25),
            recursive_internal_bound=0.1,
            authority_epoch_drift_error=0.4,
            coverage_eligible=True,
        )
        self.assertTrue(qualified["qualified"])
        self.assertAlmostEqual(qualified["observed_order"], 2.0)
        self.assertAlmostEqual(qualified["estimated_fine_error"], 1.0 / 3.0)
        self.assertTrue(qualified["reference_estimator_covered"])
        self.assertTrue(qualified["total_uncertainty_covered"])

        rejected = _order_aware_sample_diagnostic(
            triplet,
            settings,
            pair(1.5, 1.0),
            pair(1.0, 0.25),
            recursive_internal_bound=100.0,
            authority_epoch_drift_error=0.1,
            coverage_eligible=True,
        )
        self.assertFalse(rejected["qualified"])
        self.assertEqual(rejected["rejection_cause"], "observed_order_below_minimum")
        self.assertIsNone(rejected["estimated_fine_error"])
        self.assertIsNone(rejected["total_uncertainty_covered"])

    def test_global_order_aware_atlas_reports_triplets_and_rejections(self) -> None:
        atlas = execute_runtime_bound_atlas(
            GLOBAL_ORDER_AWARE_MANIFEST,
            selected_cases={"rc_bank-n001"},
        )
        aggregate = atlas["aggregates"][0]
        sweep = aggregate["global_order_aware_triplet_sweep"]
        self.assertEqual(tuple(sweep), ("2x4x8", "4x8x16", "8x16x32"))
        self.assertTrue(aggregate["global_order_aware_triplet_pareto_frontier"])
        self.assertTrue(atlas["global_order_aware_common_policy_frontier"])
        self.assertTrue(atlas["global_order_aware_epoch_common_policy_frontier"])
        self.assertTrue(
            atlas["global_order_aware_epoch_envelope_common_policy_frontier"]
        )
        for triplet in sweep.values():
            self.assertEqual(
                triplet["eligible"],
                triplet["qualified"] + triplet["rejected"],
            )
            self.assertEqual(
                triplet["rejected"],
                sum(triplet["rejection_causes"].values()),
            )
            self.assertLessEqual(
                triplet["effective_babcs_total_coverage_fraction"],
                triplet["qualified_babcs_total_coverage_fraction"],
            )
            epoch = triplet["epoch_qualified"]
            self.assertEqual(
                epoch["epoch_count"],
                epoch["qualified_epochs"] + epoch["rejected_epochs"],
            )
            self.assertEqual(
                epoch["eligible_samples"],
                epoch["qualified_samples"] + epoch["rejected_samples"],
            )
            self.assertGreater(
                epoch["sample_qualification_fraction"],
                triplet["qualification_fraction"],
            )
            envelope = epoch["envelope"]
            self.assertGreaterEqual(
                envelope["effective_reference_estimator_coverage_fraction"],
                epoch["effective_reference_estimator_coverage_fraction"],
            )
            self.assertGreaterEqual(
                envelope["effective_babcs_total_coverage_fraction"],
                epoch["effective_babcs_total_coverage_fraction"],
            )
        self.assertTrue(
            all(
                "global_order_aware_diagnostics" in sample
                for sample in atlas["samples"]
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            write_atlas_plots(directory, atlas)
            self.assertEqual(len(list(Path(directory).glob("*.svg"))), 17)

    def test_statewise_four_level_exact_second_order_sequence_qualifies(self) -> None:
        diagnostic = _statewise_four_level_sample_diagnostic(
            self._statewise_quadruplet(),
            self._statewise_settings(),
            (
                (2.75,),
                (1.25,),
                (0.875,),
                (0.78125,),
            ),
            state_names=("x",),
            candidate_delta=(0.76,),
            authority_delta=(0.75,),
            recursive_internal_bound=0.1,
            authority_epoch_drift_error=0.1,
            config=BABCSConfig(),
            coverage_eligible=True,
        )
        self.assertTrue(diagnostic["qualified"])
        self.assertEqual(diagnostic["qualified_state_count"], 1)
        state = diagnostic["states"][0]
        self.assertAlmostEqual(state["left_observed_order"], 2.0)
        self.assertAlmostEqual(state["right_observed_order"], 2.0)
        self.assertAlmostEqual(state["common_observed_order"], 2.0)
        self.assertAlmostEqual(state["estimated_finest_absolute_error"], 0.03125)
        self.assertAlmostEqual(state["extrapolant_residual"], 0.0)
        self.assertTrue(state["component_reference_covered"])
        self.assertTrue(diagnostic["reference_estimator_covered"])
        self.assertTrue(diagnostic["total_uncertainty_covered"])

    def test_statewise_four_level_rejects_unstable_sequences(self) -> None:
        cases = (
            (
                (3.0, 2.0, 2.5, 2.0),
                {},
                "signed_difference_inconsistent",
            ),
            (
                (5.435275281648062, 1.435275281648062, 0.435275281648062, 0.0),
                {},
                "adjacent_order_difference_exceeded",
            ),
            (
                (5.435275281648062, 1.435275281648062, 0.435275281648062, 0.0),
                {
                    "maximum_adjacent_order_difference": 1.0,
                    "maximum_coefficient_relative_difference": 0.01,
                },
                "coefficient_relative_difference_exceeded",
            ),
            (
                (5.435275281648062, 1.435275281648062, 0.435275281648062, 0.0),
                {
                    "maximum_adjacent_order_difference": 1.0,
                    "maximum_coefficient_relative_difference": 10.0,
                    "maximum_extrapolant_residual_ratio": 0.01,
                },
                "extrapolant_residual_ratio_exceeded",
            ),
        )
        for values, overrides, expected_cause in cases:
            with self.subTest(expected_cause=expected_cause):
                settings = {**self._statewise_settings(), **overrides}
                diagnostic = _statewise_four_level_sample_diagnostic(
                    self._statewise_quadruplet(),
                    settings,
                    tuple((value,) for value in values),
                    state_names=("x",),
                    candidate_delta=(0.0,),
                    authority_delta=(0.0,),
                    recursive_internal_bound=1.0,
                    authority_epoch_drift_error=1.0,
                    config=BABCSConfig(),
                    coverage_eligible=True,
                )
                self.assertFalse(diagnostic["qualified"])
                self.assertEqual(
                    diagnostic["states"][0]["rejection_cause"],
                    expected_cause,
                )

        floor_diagnostic = _statewise_four_level_sample_diagnostic(
            self._statewise_quadruplet(),
            self._statewise_settings(),
            ((1.0,), (1.0,), (0.5,), (0.25,)),
            state_names=("x",),
            candidate_delta=(0.0,),
            authority_delta=(0.0,),
            recursive_internal_bound=1.0,
            authority_epoch_drift_error=1.0,
            config=BABCSConfig(),
            coverage_eligible=True,
            sampling_context={
                "interpolated_refinement_factors": [2, 4, 8, 16],
                "anchor_reset_context": True,
                "algebraic_solve_floor_context": False,
            },
        )
        self.assertEqual(
            floor_diagnostic["states"][0]["rejection_cause"],
            "first_difference_at_or_below_floor",
        )
        self.assertEqual(
            floor_diagnostic["states"][0]["floor_contexts"],
            ["interpolation", "anchor_reset"],
        )

    def test_global_statewise_four_level_atlas_reconciles_diagnostics(self) -> None:
        atlas = execute_runtime_bound_atlas(
            GLOBAL_STATEWISE_FOUR_LEVEL_MANIFEST,
            selected_cases={"rc_bank-n001"},
        )
        aggregate = atlas["aggregates"][0]
        sweep = aggregate["global_statewise_four_level_sweep"]
        self.assertEqual(tuple(sweep), ("2x4x8x16", "4x8x16x32"))
        self.assertIn("global_statewise_four_level_common_policy_frontier", atlas)
        for quadruplet in sweep.values():
            self.assertEqual(
                quadruplet["eligible_samples"],
                quadruplet["qualified_samples"] + quadruplet["rejected_samples"],
            )
            self.assertEqual(
                quadruplet["total_states"],
                quadruplet["qualified_states"] + quadruplet["rejected_states"],
            )
            self.assertEqual(
                quadruplet["rejected_samples"],
                sum(quadruplet["sample_rejection_causes"].values()),
            )
            self.assertEqual(
                quadruplet["rejected_states"],
                sum(quadruplet["state_rejection_causes"].values()),
            )
            self.assertEqual(
                quadruplet["eligible_samples"],
                quadruplet["interpolated_sample_count"]
                + quadruplet["all_native_sample_count"],
            )
            self.assertGreaterEqual(
                sum(quadruplet["floor_context_state_mentions"].values()),
                quadruplet["floor_rejected_state_count"],
            )
            self.assertLessEqual(
                quadruplet["effective_babcs_total_coverage_fraction"],
                quadruplet["qualified_babcs_total_coverage_fraction"] or 0.0,
            )
        self.assertTrue(
            all(
                "global_statewise_four_level_diagnostics" in sample
                for sample in atlas["samples"]
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_sample_csv(root / "samples.csv", atlas)
            write_atlas_plots(root / "plots", atlas)
            self.assertIn(
                "global_statewise_four_level_diagnostics",
                (root / "samples.csv").read_text(encoding="utf-8"),
            )
            self.assertEqual(len(list((root / "plots").glob("*.svg"))), 20)

    def test_statewise_epoch_fit_accepts_coherent_zero_crossing(self) -> None:
        config = BABCSConfig()
        rows = []
        for amplitude in (-1.0, -0.5, 0.5, 1.0):
            exact = 0.75
            values = tuple(exact + amplitude / factor**2 for factor in (2, 4, 8, 16))
            rows.append(
                _statewise_four_level_state_diagnostic(
                    self._statewise_quadruplet(),
                    self._statewise_settings(),
                    values,
                    state_index=0,
                    state_name="x",
                    authority_delta=exact,
                    config=config,
                )
            )
        diagnostic = _statewise_epoch_state_diagnostic(
            self._statewise_quadruplet(),
            self._statewise_settings(),
            self._epoch_fit_settings(),
            rows,
        )
        self.assertTrue(diagnostic["qualified"])
        self.assertEqual(diagnostic["coherent_zero_crossing_interval_count"], 1)
        self.assertEqual(diagnostic["unmatched_sign_change_interval_count"], 0)
        self.assertAlmostEqual(diagnostic["left_observed_order"], 2.0)
        self.assertAlmostEqual(diagnostic["right_observed_order"], 2.0)

        unstable = [dict(row) for row in rows]
        unstable[-1]["signed_differences"] = list(
            unstable[-1]["signed_differences"]
        )
        unstable[-1]["normalized_signed_differences"] = list(
            unstable[-1]["normalized_signed_differences"]
        )
        unstable[-1]["signed_differences"][2] *= -1.0
        unstable[-1]["normalized_signed_differences"][2] *= -1.0
        rejected = _statewise_epoch_state_diagnostic(
            self._statewise_quadruplet(),
            self._statewise_settings(),
            self._epoch_fit_settings(),
            unstable,
        )
        self.assertFalse(rejected["qualified"])
        self.assertEqual(
            rejected["rejection_cause"],
            "unmatched_sign_change_intervals_exceeded",
        )

    def test_global_statewise_epoch_atlas_uses_direct_sampling(self) -> None:
        atlas = execute_runtime_bound_atlas(
            GLOBAL_STATEWISE_EPOCH_MANIFEST,
            selected_cases={"rc_bank-n001"},
        )
        aggregate = atlas["aggregates"][0]
        pointwise = aggregate["global_statewise_four_level_sweep"]
        epoch_sweep = aggregate["global_statewise_epoch_sweep"]
        self.assertEqual(tuple(epoch_sweep), ("2x4x8x16", "4x8x16x32"))
        self.assertIn("global_statewise_epoch_common_policy_frontier", atlas)
        for factor, metadata in aggregate["global_dual_trajectory"][
            "factor_trajectories"
        ].items():
            self.assertEqual(metadata["sampling_mode"], "integrated_output_times")
            self.assertEqual(metadata["output_interval_substeps"], int(factor))
            self.assertEqual(metadata["work"]["replay_steps"], 0)
            self.assertGreater(
                metadata["effective_anchor_interval_steps"],
                metadata["configured_anchor_interval_steps"],
            )
        for quadruplet_id, epoch in epoch_sweep.items():
            self.assertEqual(epoch["sampling_mode"], "integrated_output_times")
            self.assertEqual(
                epoch["epoch_count"],
                epoch["qualified_epochs"] + epoch["rejected_epochs"],
            )
            self.assertEqual(
                epoch["eligible_samples"],
                epoch["qualified_samples"] + epoch["rejected_samples"],
            )
            self.assertEqual(
                epoch["state_epoch_count"],
                epoch["qualified_state_epochs"] + epoch["rejected_state_epochs"],
            )
            self.assertEqual(
                pointwise[quadruplet_id]["interpolated_sample_count"],
                0,
            )
            self.assertEqual(
                pointwise[quadruplet_id]["all_native_sample_count"],
                pointwise[quadruplet_id]["eligible_samples"],
            )
        with tempfile.TemporaryDirectory() as directory:
            write_atlas_plots(directory, atlas)
            self.assertEqual(len(list(Path(directory).glob("*.svg"))), 24)

    def test_symmetric_eigenbasis_is_deterministic_and_orthogonal(self) -> None:
        first = _symmetric_eigenbasis(
            [[2.0, 1.0], [1.0, 2.0]],
            maximum_sweeps=32,
            relative_tolerance=1.0e-14,
        )
        second = _symmetric_eigenbasis(
            [[2.0, 1.0], [1.0, 2.0]],
            maximum_sweeps=32,
            relative_tolerance=1.0e-14,
        )
        self.assertEqual(first, second)
        eigenvalues, basis, _, converged = first
        self.assertTrue(converged)
        self.assertAlmostEqual(eigenvalues[0], 1.0)
        self.assertAlmostEqual(eigenvalues[1], 3.0)
        self.assertAlmostEqual(
            sum(basis[row][0] * basis[row][1] for row in range(2)),
            0.0,
        )

    def test_modal_epoch_group_accepts_exact_second_order_sequence(self) -> None:
        rows = []
        for amplitude in (-1.0, -0.5, 0.5, 1.0):
            levels = [[amplitude / factor**2] for factor in (2, 4, 8, 16)]
            rows.append(
                {
                    "refinement_modes": levels,
                    "mode_scales": [1.0],
                }
            )
        diagnostic = _modal_epoch_group_diagnostic(
            self._statewise_quadruplet(),
            self._statewise_settings(),
            self._epoch_fit_settings(),
            {
                "group_id": "mode-group-000",
                "mode_indices": [0],
                "dimension": 1,
                "eigenvalues": [-1.0],
            },
            rows,
        )
        self.assertTrue(diagnostic["qualified"])
        self.assertAlmostEqual(diagnostic["left_observed_order"], 2.0)
        self.assertAlmostEqual(diagnostic["right_observed_order"], 2.0)
        self.assertEqual(diagnostic["coherent_zero_crossing_interval_count"], 1)
        self.assertEqual(diagnostic["unmatched_sign_change_interval_count"], 0)

    def test_temporal_alignment_uses_unique_crossing_lags(self) -> None:
        diagnostic = _temporally_align_scalar_sequences(
            [
                [-1.0, -1.0, -1.0, 1.0, 1.0, 1.0],
                [-1.0, -1.0, -1.0, -1.0, 1.0, 1.0],
                [-1.0, -1.0, -1.0, -1.0, -1.0, 1.0],
            ],
            floor=1.0e-12,
            maximum_sample_lag=1,
            minimum_retained_samples=4,
        )
        self.assertTrue(diagnostic["qualified"])
        self.assertEqual(
            diagnostic["selected_sequence_sample_lags"],
            [-1, 0, 1],
        )
        self.assertEqual(diagnostic["retained_sample_count"], 4)
        self.assertEqual(diagnostic["discarded_endpoint_count"], 6)
        self.assertEqual(diagnostic["matched_zero_crossing_interval_count"], 1)
        self.assertAlmostEqual(diagnostic["left_direction_cosine"], 1.0)
        self.assertAlmostEqual(diagnostic["right_direction_cosine"], 1.0)

    def test_temporal_alignment_rejects_sign_chatter(self) -> None:
        diagnostic = _temporally_align_scalar_sequences(
            [
                [-1.0, 1.0, -1.0, 1.0, -1.0],
                [-1.0, 1.0, -1.0, 1.0, -1.0],
                [-1.0, 1.0, -1.0, 1.0, -1.0],
            ],
            floor=1.0e-12,
            maximum_sample_lag=1,
            minimum_retained_samples=4,
        )
        self.assertFalse(diagnostic["qualified"])
        self.assertEqual(
            diagnostic["rejection_cause"],
            "temporal_alignment_sign_chatter_detected",
        )

    def test_two_term_modal_fit_uses_finest_level_as_holdout(self) -> None:
        policy = self._two_term_policy(secondary_order=4.0)
        design = _two_term_design_metadata(policy)
        rows = []
        exact_errors = []
        for sample_index in range(4):
            limit = 1.0 + 0.1 * sample_index
            primary = 2.0 - 0.2 * sample_index
            secondary = -3.0 + 0.1 * sample_index
            refinement_modes = {
                factor: [
                    limit
                    + primary * factor**-2.0
                    + secondary * factor**-4.0
                ]
                for factor in (2, 4, 8, 16, 32)
            }
            rows.append(
                {
                    "refinement_modes_by_factor": refinement_modes,
                    "mode_scales": [1.0],
                }
            )
            exact_errors.append(abs(refinement_modes[32][0] - limit))
        diagnostic = _two_term_modal_group_diagnostic(
            policy,
            self._two_term_settings(),
            self._epoch_fit_settings(),
            {
                "group_id": "mode-group-000",
                "mode_indices": [0],
                "dimension": 1,
                "eigenvalues": [-1.0],
            },
            rows,
            design,
            {
                "qualified": False,
                "rejection_cause": "left_direction_cosine_below_minimum",
            },
        )
        self.assertTrue(diagnostic["qualified"])
        self.assertTrue(diagnostic["fit_attempted"])
        self.assertEqual(
            diagnostic["qualification_source"],
            "five_level_two_term",
        )
        self.assertLess(diagnostic["training_residual_ratio"], 1.0e-10)
        self.assertLess(diagnostic["holdout_residual_ratio"], 1.0e-10)
        estimates = [row[0] for row in diagnostic["estimated_holdout_absolute_errors"]]
        for estimate, exact_error in zip(estimates, exact_errors, strict=True):
            self.assertGreaterEqual(estimate, exact_error)

    def test_two_term_modal_fit_rejects_inconsistent_holdout(self) -> None:
        policy = self._two_term_policy(secondary_order=4.0)
        design = _two_term_design_metadata(policy)
        rows = []
        for sample_index in range(4):
            refinement_modes = {
                factor: [1.0 + 2.0 * factor**-2.0 - factor**-4.0]
                for factor in (2, 4, 8, 16, 32)
            }
            refinement_modes[32][0] += 0.1 * (sample_index + 1)
            rows.append(
                {
                    "refinement_modes_by_factor": refinement_modes,
                    "mode_scales": [1.0],
                }
            )
        diagnostic = _two_term_modal_group_diagnostic(
            policy,
            self._two_term_settings(),
            self._epoch_fit_settings(),
            {
                "group_id": "mode-group-000",
                "mode_indices": [0],
                "dimension": 1,
                "eigenvalues": [-1.0],
            },
            rows,
            design,
            {
                "qualified": False,
                "rejection_cause": "unmatched_sign_change_intervals_exceeded",
            },
        )
        self.assertFalse(diagnostic["qualified"])
        self.assertEqual(
            diagnostic["rejection_cause"],
            "two_term_holdout_residual_ratio_exceeded",
        )

    def test_two_term_modal_fit_rejects_ill_conditioned_policy(self) -> None:
        policy = self._two_term_policy(secondary_order=4.0)
        settings = self._two_term_settings()
        settings["maximum_design_condition_number"] = 1.0
        diagnostic = _two_term_modal_group_diagnostic(
            policy,
            settings,
            self._epoch_fit_settings(),
            {
                "group_id": "mode-group-000",
                "mode_indices": [0],
                "dimension": 1,
                "eigenvalues": [-1.0],
            },
            [
                {
                    "refinement_modes_by_factor": {
                        factor: [1.0 + factor**-2.0 + factor**-4.0]
                        for factor in (2, 4, 8, 16, 32)
                    },
                    "mode_scales": [1.0],
                }
                for _ in range(4)
            ],
            _two_term_design_metadata(policy),
            {
                "qualified": False,
                "rejection_cause": "left_direction_cosine_below_minimum",
            },
        )
        self.assertFalse(diagnostic["qualified"])
        self.assertEqual(
            diagnostic["rejection_cause"],
            "two_term_design_condition_exceeded",
        )

    def test_two_term_modal_fit_preserves_loop_5g_fallback(self) -> None:
        policy = self._two_term_policy(secondary_order=3.0)
        fallback_estimates = [[0.1], [0.2], [0.3], [0.4]]
        diagnostic = _two_term_modal_group_diagnostic(
            policy,
            self._two_term_settings(),
            self._epoch_fit_settings(),
            {
                "group_id": "mode-group-000",
                "mode_indices": [0],
                "dimension": 1,
                "eigenvalues": [-1.0],
            },
            [],
            _two_term_design_metadata(policy),
            {
                "qualified": True,
                "rejection_cause": None,
                "estimated_finest_absolute_errors": fallback_estimates,
            },
        )
        self.assertTrue(diagnostic["qualified"])
        self.assertFalse(diagnostic["fit_attempted"])
        self.assertEqual(
            diagnostic["qualification_source"],
            "loop_5g_fallback",
        )
        self.assertEqual(
            diagnostic["estimated_holdout_absolute_errors"],
            fallback_estimates,
        )

    def test_global_modal_epoch_atlas_records_reviewed_basis(self) -> None:
        atlas = execute_runtime_bound_atlas(
            GLOBAL_MODAL_EPOCH_MANIFEST,
            selected_cases={"coupled_rc_ring-n004"},
        )
        aggregate = atlas["aggregates"][0]
        basis = aggregate["global_dual_trajectory"]["modal_basis"]
        self.assertTrue(basis["qualified"])
        self.assertEqual(basis["state_unit"], "voltage")
        self.assertEqual(len(basis["mode_groups"]), 4)
        self.assertEqual(
            tuple(aggregate["global_modal_epoch_sweep"]),
            ("2x4x8x16", "4x8x16x32"),
        )
        self.assertIn("global_modal_epoch_common_policy_frontier", atlas)
        with tempfile.TemporaryDirectory() as directory:
            write_atlas_plots(directory, atlas)
            self.assertEqual(len(list(Path(directory).glob("*.svg"))), 28)

    def test_temporal_modal_atlas_preserves_unshifted_fallback(self) -> None:
        atlas = execute_runtime_bound_atlas(
            GLOBAL_TEMPORAL_MODAL_EPOCH_MANIFEST,
            selected_cases={"coupled_rc_ring-n004"},
        )
        aggregate = atlas["aggregates"][0]
        baseline = aggregate["global_modal_epoch_sweep"]
        temporal = aggregate["global_temporally_aligned_modal_epoch_sweep"]
        self.assertEqual(tuple(baseline), ("2x4x8x16", "4x8x16x32"))
        self.assertEqual(tuple(temporal), ("2x4x8x16", "4x8x16x32"))
        self.assertTrue(
            all(row["temporal_alignment_enabled"] for row in temporal.values())
        )
        self.assertIn(
            "global_temporally_aligned_modal_epoch_common_policy_frontier",
            atlas,
        )
        for quadruplet_id, baseline_row in baseline.items():
            temporal_row = temporal[quadruplet_id]
            self.assertGreaterEqual(
                temporal_row["qualified_mode_group_epochs"],
                baseline_row["qualified_mode_group_epochs"],
            )
        with tempfile.TemporaryDirectory() as directory:
            write_atlas_plots(directory, atlas)
            self.assertEqual(len(list(Path(directory).glob("*.svg"))), 34)

    def test_two_term_modal_atlas_records_holdout_policies(self) -> None:
        atlas = execute_runtime_bound_atlas(
            GLOBAL_TWO_TERM_MODAL_MANIFEST,
            selected_cases={"coupled_rc_ring-n004"},
        )
        aggregate = atlas["aggregates"][0]
        sweep = aggregate["global_two_term_modal_sweep"]
        self.assertEqual(tuple(sweep), ("p2q3", "p2q4"))
        self.assertTrue(
            all(row["holdout_refinement_factor"] == 32 for row in sweep.values())
        )
        self.assertTrue(
            all(
                row["training_refinement_factors"] == [2, 4, 8, 16]
                for row in sweep.values()
            )
        )
        self.assertIn("global_two_term_modal_common_policy_frontier", atlas)
        with tempfile.TemporaryDirectory() as directory:
            write_atlas_plots(directory, atlas)
            self.assertEqual(len(list(Path(directory).glob("*.svg"))), 34)

    def test_modal_basis_rejects_mixed_units_and_nonlinearity(self) -> None:
        for case_path, cause in (
            (Path("benchmarks/cases/rlc_damped.json"), "mixed_dynamic_units"),
            (Path("benchmarks/cases/diode_clip.json"), "nonlinear_circuit"),
        ):
            with self.subTest(case_path=case_path):
                circuit, simulation, config = load_case(case_path)
                state, _ = BoundedIntegrator(config).initialize(
                    circuit,
                    simulation["start_time"],
                )
                basis = _modal_basis_metadata(
                    circuit,
                    state.evaluation,
                    self._modal_fit_settings(),
                )
                self.assertFalse(basis["qualified"])
                self.assertEqual(basis["rejection_cause"], cause)

    @staticmethod
    def _statewise_quadruplet() -> dict[str, object]:
        return {
            "quadruplet_id": "2x4x8x16",
            "refinement_factors": [2, 4, 8, 16],
            "refinement_ratio": 2.0,
        }

    @staticmethod
    def _statewise_settings() -> dict[str, float]:
        return {
            "minimum_observed_order": 1.0,
            "maximum_observed_order": 3.0,
            "scaled_difference_floor": 1.0e-12,
            "maximum_adjacent_order_difference": 0.5,
            "maximum_coefficient_relative_difference": 0.5,
            "maximum_extrapolant_residual_ratio": 1.0,
        }

    @staticmethod
    def _epoch_fit_settings() -> dict[str, float | int]:
        return {
            "minimum_epoch_samples": 4,
            "minimum_pairwise_direction_cosine": 0.9,
            "maximum_unmatched_sign_change_intervals": 0,
        }

    @staticmethod
    def _modal_fit_settings() -> dict[str, float | int]:
        return {
            "maximum_symmetry_relative_error": 1.0e-10,
            "maximum_eigen_residual_relative_error": 1.0e-9,
            "maximum_orthogonality_error": 1.0e-9,
            "repeated_eigenvalue_relative_tolerance": 1.0e-9,
            "repeated_eigenvalue_absolute_tolerance": 1.0e-12,
            "maximum_jacobi_sweeps": 128,
        }

    @staticmethod
    def _two_term_policy(*, secondary_order: float) -> dict[str, object]:
        return {
            "policy_id": f"p2q{secondary_order:g}",
            "primary_order": 2.0,
            "secondary_order": secondary_order,
            "training_refinement_factors": [2, 4, 8, 16],
            "holdout_refinement_factor": 32,
        }

    @staticmethod
    def _two_term_settings() -> dict[str, float]:
        return {
            "maximum_design_condition_number": 1000.0,
            "maximum_training_residual_ratio": 0.25,
            "maximum_holdout_residual_ratio": 1.0,
            "scaled_difference_floor": 1.0e-12,
        }


if __name__ == "__main__":
    unittest.main()
