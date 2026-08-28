import json
import tempfile
import unittest
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from verification_v1.artifacts import ArtifactStore, CandidateArtifact
from verification_v1.contracts import HardVerifierOutcome, TaskContract
from verification_v1.evaluation import _DatasetHardVerifier, evaluate_fixture_set, replay_run_record, write_report


class EvaluationAndReplayTests(unittest.TestCase):
    def test_checked_in_engineering_fixture_set_covers_each_narrow_checklet_without_label_leakage(self) -> None:
        source = Path("evals/verification_v1/engineering_fixture_set.json")

        report = evaluate_fixture_set(source)

        self.assertEqual(8, report.task_count)
        self.assertEqual(7, report.hard_verifier_coverage)
        self.assertEqual(1, report.indeterminate_count)
        for checklet_id in (
            "requirement_coverage", "test_adequacy", "change_scope", "dependency_integration_risk", "error_boundary",
        ):
            self.assertGreaterEqual(report.per_checklet[checklet_id]["finding_count"], 1)
        self.assertGreater(report.cost_and_latency["checklets_latency_ms"]["total"], 0.0)
        self.assertGreater(report.cost_and_latency["hard_verifier_latency_ms"]["total"], 0.0)
        self.assertEqual(4 / 6, report.shadow_metrics["observed_counterfactual_shadow_miss_rate"])
        for record in report.run_records:
            metadata = record["artifact"]["metadata"]
            self.assertNotIn("hard_verifier_outcome", metadata)
            self.assertNotIn("expected_defect_class", metadata)

    def test_evaluation_reports_fixture_metrics_and_replay_preserves_artifact_identity(self) -> None:
        dataset = {
            "dataset_id": "engineering_fixture_set",
            "dataset_version": "1.0.0",
            "fixtures": [
                {
                    "fixture_id": "clean-control",
                    "split": "development",
                    "task": {"task_id": "clean-task", "requirements": []},
                    "artifact": {
                        "artifact_id": "clean-artifact",
                        "artifact_type": "coding_patch",
                        "content": "def add(a, b):\n    return a + b\n",
                        "metadata": {
                            "changed_paths": ["src/add.py"], "allowed_paths": ["src/add.py"],
                            "producer_test_cases": ["test_add"], "test_cases_by_requirement": {},
                            "covered_requirements": [], "boundary_cases": [], "handled_boundary_cases": [],
                            "signature_changes": []
                        },
                    },
                    "hard_verifier_outcome": "accepted",
                    "expected_defect_class": None,
                    "expected_affected_checklets": [],
                },
                {
                    "fixture_id": "missing-requirement",
                    "split": "development",
                    "task": {"task_id": "requirement-task", "requirements": ["return-zero-for-empty"]},
                    "artifact": {
                        "artifact_id": "missing-artifact", "artifact_type": "coding_patch", "content": "def choose(items):\n    return items[0]\n",
                        "metadata": {
                            "changed_paths": ["src/choose.py"], "allowed_paths": ["src/choose.py"],
                            "producer_test_cases": ["test_choose"], "test_cases_by_requirement": {"return-zero-for-empty": ["test_choose"]},
                            "covered_requirements": [], "boundary_cases": [], "handled_boundary_cases": [], "signature_changes": []
                        },
                    },
                    "hard_verifier_outcome": "rejected",
                    "expected_defect_class": "requirement_omitted",
                    "expected_affected_checklets": ["requirement_coverage"],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "fixtures.json"
            source.write_text(json.dumps(dataset), encoding="utf-8")

            report = evaluate_fixture_set(source)
            report_paths = write_report(report, root / "reports")
            replay = replay_run_record(report.run_records[0])

            self.assertEqual(2, report.task_count)
            self.assertEqual(2, report.hard_verifier_coverage)
            self.assertIn("requirement_coverage", report.per_checklet)
            self.assertEqual(report.run_records[0]["artifact"]["artifact_digest"], replay.artifact.artifact_digest)
            self.assertTrue(report_paths["json"].exists())
            self.assertTrue(report_paths["markdown"].exists())
            self.assertIn("indeterminate", report_paths["markdown"].read_text(encoding="utf-8"))

    def test_fixture_oracle_rejects_content_with_an_unrecognized_digest_despite_matching_fixture_id(self) -> None:
        expected = CandidateArtifact.from_text(
            "expected", "coding_patch", "def value():\n    return 1\n", {"fixture_id": "same-fixture"}
        )
        tampered = CandidateArtifact.from_text(
            "tampered", "coding_patch", "def value():\n    return 2\n", {"fixture_id": "same-fixture"}
        )
        store = ArtifactStore()
        expected_registered = store.register(expected, "expected-run")
        tampered_registered = store.register(tampered, "tampered-run")
        verifier = _DatasetHardVerifier({expected_registered.artifact_digest: HardVerifierOutcome.REJECTED})

        result = verifier.verify(TaskContract("fixture-digest-binding", ()), tampered_registered)

        self.assertEqual(HardVerifierOutcome.OUTCOME_UNKNOWN, result.outcome)

    def test_replay_rejects_tampered_hard_digest_and_component_provenance(self) -> None:
        report = evaluate_fixture_set(Path("evals/verification_v1/engineering_fixture_set.json"))
        digest_tampered = deepcopy(report.run_records[0])
        digest_tampered["hard_verifier_result"]["artifact_digest"] = sha256(b"different").hexdigest()

        with self.assertRaisesRegex(ValueError, "hard-verifier result"):
            replay_run_record(digest_tampered)

        provenance_tampered = deepcopy(report.run_records[0])
        provenance_tampered["component_versions"]["policy"]["version"] = "different"

        with self.assertRaisesRegex(ValueError, "component provenance"):
            replay_run_record(provenance_tampered)


if __name__ == "__main__":
    unittest.main()
