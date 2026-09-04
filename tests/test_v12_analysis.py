import unittest

from verification_v1.analysis import (
    V2_MORE_DATA,
    V2_PROCEED,
    analyze_records,
    criterion_metrics,
    decide_v2,
    predictive_metrics,
    shadow_metrics,
    wilson_interval,
)
from verification_v1.dataset import EvidenceDataset, empty_dataset
from verification_v1.evidence import CHECKLET_IDS, CriterionLabel, FailureCode, Partition
from verification_v1.v12_report import build_report, markdown_report

try:
    from v12_helpers import make_record, metric_integrity_records
except ImportError:
    from tests.v12_helpers import make_record, metric_integrity_records


class AnalysisTests(unittest.TestCase):
    def test_metric_fixture_precision_recall(self) -> None:
        records = metric_integrity_records()
        metrics = criterion_metrics(records, "requirement_coverage")
        self.assertEqual(2, metrics["true_positive"])
        self.assertEqual(2, metrics["false_positive"])
        self.assertEqual(1, metrics["false_negative"])
        self.assertEqual(3, metrics["true_negative"])
        self.assertAlmostEqual(0.5, metrics["criterion_precision"])
        self.assertAlmostEqual(2 / 3, metrics["criterion_recall"])

    def test_metric_fixture_shadow_miss_rate(self) -> None:
        records = metric_integrity_records()
        shadow = shadow_metrics(records)
        self.assertEqual("1 / 2", shadow["false_shadow_waive_display"])
        self.assertAlmostEqual(0.5, shadow["observed_miss_rate"])
        self.assertEqual(1, shadow["n_unknown"])
        self.assertEqual(7, shadow["n_determinate"])
        self.assertEqual(8, shadow["n_total"])

    def test_unknown_hard_outcome_excluded_from_miss_denominator(self) -> None:
        records = metric_integrity_records()
        shadow = shadow_metrics(records)
        self.assertEqual(2, shadow["n_determinate_would_waive"])
        self.assertEqual(3, shadow["n_would_waive"])

    def test_criterion_truth_separate_from_hard_outcome(self) -> None:
        records = metric_integrity_records()
        criterion = criterion_metrics(records, "requirement_coverage")
        predictive = predictive_metrics(records, "requirement_coverage")
        self.assertEqual(2, criterion["true_positive"])
        finding = predictive["p_hard_reject_given_finding"]
        self.assertEqual(2, finding["rejects"])
        self.assertEqual(4, finding["n"])
        accepted_true_finding = next(item for item in records if item.task_id.endswith("tp-accept"))
        self.assertEqual("accepted", accepted_true_finding.hard_outcome.value)
        self.assertEqual("finding", accepted_true_finding.observation_for("requirement_coverage")["verdict"])
        self.assertNotIn("criterion_precision", predictive)
        self.assertNotIn("p_hard_reject_given_finding", criterion)

    def test_accepted_artifact_can_have_true_criterion_finding(self) -> None:
        record = next(item for item in metric_integrity_records() if item.task_id.endswith("tp-accept"))
        self.assertEqual("accepted", record.hard_outcome.value)
        self.assertEqual(CriterionLabel.TRUE, record.primary_criterion_label("requirement_coverage"))
        self.assertEqual("finding", record.observation_for("requirement_coverage")["verdict"])

    def test_rejected_artifact_can_have_false_checklet_finding(self) -> None:
        record = next(item for item in metric_integrity_records() if item.task_id.endswith("fp-reject"))
        self.assertEqual("rejected", record.hard_outcome.value)
        self.assertEqual(CriterionLabel.FALSE, record.primary_criterion_label("requirement_coverage"))
        self.assertEqual("finding", record.observation_for("requirement_coverage")["verdict"])

    def test_report_reconciles_to_dataset(self) -> None:
        records = metric_integrity_records()
        dataset = EvidenceDataset(
            dataset_id=empty_dataset().dataset_id,
            dataset_version="1.2.0",
            schema_version=empty_dataset().schema_version,
            experiment_id=empty_dataset().experiment_id,
            cohort_id=empty_dataset().cohort_id,
            experiment_baseline_id=empty_dataset().experiment_baseline_id,
            split_algorithm_version=empty_dataset().split_algorithm_version,
            split_seed=empty_dataset().split_seed,
            created_at="2026-01-01T00:00:00+00:00",
            changelog=(),
            records=records,
        )
        report = build_report(dataset)
        analysis = report["analysis"]
        self.assertEqual(len(records), analysis["dataset_composition"]["n_total"])
        self.assertEqual(len(records), analysis["n_records_analyzed"])
        self.assertEqual(1, analysis["shadow_metrics"]["n_false_shadow_waives"])
        self.assertEqual(V2_MORE_DATA, analysis["v2_decision"]["decision"])
        markdown = markdown_report(report)
        self.assertIn("Executive conclusion", markdown)
        self.assertIn("Criterion-level checklet quality", markdown)
        self.assertIn("V2 decision gate", markdown)
        self.assertIn("1 / 2", markdown)

    def test_invalid_record_cannot_enter_report(self) -> None:
        record = make_record(name="report-invalid")
        payload = record.to_dict()
        payload["shadow_assessment"]["artifact_digest"] = "1" * 64
        broken = __import__("verification_v1.evidence", fromlist=["RealTaskEvidenceRecord"]).RealTaskEvidenceRecord.from_dict(payload)
        with self.assertRaises(ValueError) as raised:
            analyze_records((broken,))
        self.assertIn(FailureCode.REPORT_INTEGRITY_FAILURE.value, str(raised.exception))

    def test_wilson_zero_over_n_is_not_zero_risk(self) -> None:
        interval = wilson_interval(0, 2)
        self.assertEqual("0 / 2", interval["display"])
        self.assertEqual(0.0, interval["rate"])
        self.assertGreater(interval["upper"], 0.0)
        self.assertEqual("wilson_95", interval["method"])

    def test_zero_low_risk_reject_rate_can_satisfy_go_condition(self) -> None:
        result = decide_v2(_go_ready_analysis(reject_rate=0.0, gate_rate=0.2))
        self.assertEqual(V2_PROCEED, result["decision"], result)

    def test_nonzero_low_risk_reject_rate_below_baseline_also_goes(self) -> None:
        result = decide_v2(_go_ready_analysis(reject_rate=0.01, gate_rate=0.2))
        self.assertEqual(V2_PROCEED, result["decision"], result)

    def test_real_determinate_count_is_anded_not_separate_totals(self) -> None:
        analysis = _go_ready_analysis()
        analysis["dataset_composition"]["n_real"] = 50
        analysis["dataset_composition"]["n_determinate"] = 50
        analysis["dataset_composition"]["n_real_determinate"] = 10
        result = decide_v2(analysis)
        self.assertEqual(V2_MORE_DATA, result["decision"])
        self.assertTrue(any("10 / 50" in reason for reason in result["reasons"]))
        self.assertIn("real_determinate_sample", result["gates"])
        self.assertFalse(result["gates"]["real_determinate_sample"]["passed"])

    def test_insufficient_real_diversity_blocks_go_separately(self) -> None:
        analysis = _go_ready_analysis()
        analysis["dataset_composition"]["real_determinate_diversity"] = {
            "n_repositories": 1,
            "n_task_families": 1,
            "n_patch_sizes": 1,
            "n_producers": 1,
            "sufficient": False,
        }
        result = decide_v2(analysis)
        self.assertEqual(V2_MORE_DATA, result["decision"])
        self.assertTrue(any("too narrow" in reason for reason in result["reasons"]))

    def test_default_analysis_excludes_holdout_and_calibration(self) -> None:
        records = (
            make_record(name="scope-dev", partition=Partition.DEVELOPMENT),
            make_record(name="scope-hold", partition=Partition.HOLDOUT, task_family_id="fam-hold"),
            make_record(name="scope-cal", partition=Partition.CALIBRATION_RESERVED, task_family_id="fam-cal"),
        )
        analysis = analyze_records(records)
        self.assertEqual(1, analysis["n_records_analyzed"])
        self.assertEqual(3, analysis["n_records_in_dataset"])
        self.assertEqual("operational", analysis["analysis_scope"])
        self.assertEqual(1, analysis["sealed_partition_counts"]["holdout"])
        self.assertEqual(1, analysis["sealed_partition_counts"]["calibration_reserved"])


def _go_ready_analysis(*, reject_rate: float | None = 0.0, gate_rate: float | None = 0.2) -> dict:
    checklets = {
        checklet_id: {"criterion_precision": 0.8, "criterion_recall": 0.7} for checklet_id in CHECKLET_IDS
    }
    predictive = {
        checklet_id: {
            "absolute_rejection_rate_difference": 0.15,
            "p_hard_reject_given_finding": {"descriptive_only": False},
        }
        for checklet_id in CHECKLET_IDS
    }
    return {
        "dataset_composition": {
            "n_real": 80,
            "n_determinate": 80,
            "n_real_determinate": 80,
            "real_determinate_diversity": {
                "n_repositories": 3,
                "n_task_families": 6,
                "n_patch_sizes": 3,
                "n_producers": 2,
                "sufficient": True,
            },
        },
        "data_quality": {"ok": True},
        "low_risk_region": {
            "reject_rate": reject_rate,
            "descriptive_only": False,
            "generalizes": True,
            "generalization_note": "low-risk region observed across multiple repositories, families, and patch sizes",
        },
        "objective_gate_baseline": {"after_objective_gates_pass": {"rate": gate_rate}},
        "criterion_quality": checklets,
        "predictive_utility": predictive,
    }
