import unittest

from verification_v1.dataset import append_records, empty_dataset
from verification_v1.evidence import FailureCode, RealTaskEvidenceRecord
from verification_v1.integrity import duplicate_failures, exact_artifact_key, validate_dataset_records, validate_record

try:
    from v12_helpers import make_record, metric_integrity_records
except ImportError:
    from tests.v12_helpers import make_record, metric_integrity_records


class DatasetIntegrityTests(unittest.TestCase):
    def test_record_binds_exact_artifact(self) -> None:
        record = make_record(name="bind")
        self.assertEqual(record.candidate_patch_digest, record.shadow_assessment["artifact_digest"])
        self.assertEqual(record.candidate_patch_digest, record.hard_verifier_result["artifact_digest"])
        self.assertTrue(all(item["artifact_digest"] == record.candidate_patch_digest for item in record.checklet_observations))
        self.assertTrue(all(item.artifact_digest == record.candidate_patch_digest for item in record.criterion_adjudications))
        self.assertFalse(validate_record(record))

    def test_duplicate_detection(self) -> None:
        first = make_record(name="dup-a")
        payload = first.to_dict()
        payload["record_id"] = first.record_id + "-copy"
        second = RealTaskEvidenceRecord.from_dict(payload)
        failures = duplicate_failures((first, second))
        self.assertTrue(any(item["code"] == FailureCode.DATASET_DUPLICATE.value for item in failures))

    def test_roundtrip_serialization(self) -> None:
        record = make_record(name="roundtrip")
        restored = RealTaskEvidenceRecord.from_dict(record.to_dict())
        self.assertEqual(record.record_id, restored.record_id)
        self.assertEqual(record.candidate_patch_digest, restored.candidate_patch_digest)
        self.assertEqual(record.primary_criterion_label("requirement_coverage"), restored.primary_criterion_label("requirement_coverage"))

    def test_invalid_record_cannot_enter_report(self) -> None:
        record = make_record(name="invalid-missing")
        payload = record.to_dict()
        payload["criterion_adjudications"] = []
        broken = RealTaskEvidenceRecord.from_dict(payload)
        self.assertIn(FailureCode.CRITERION_ADJUDICATION_MISSING, validate_record(broken))
        with self.assertRaises(ValueError):
            append_records(empty_dataset(), (broken,), note="should fail")

    def test_digest_mismatch_is_blocking(self) -> None:
        record = make_record(name="mismatch")
        payload = record.to_dict()
        payload["hard_verifier_result"]["artifact_digest"] = "0" * 64
        broken = RealTaskEvidenceRecord.from_dict(payload)
        self.assertIn(FailureCode.DIGEST_MISMATCH, validate_record(broken))

    def test_cross_adjudicator_disagreement_is_not_blocking(self) -> None:
        from verification_v1.evidence import (
            CRITERION_IDS,
            AdjudicationMode,
            AdjudicatorType,
            CriterionAdjudication,
            CriterionLabel,
        )

        record = make_record(name="dual-disagree")
        payload = record.to_dict()
        extra = CriterionAdjudication(
            task_id=record.task_id,
            artifact_digest=record.candidate_patch_digest,
            checklet_id="requirement_coverage",
            criterion_id=CRITERION_IDS["requirement_coverage"],
            label=CriterionLabel.TRUE,
            adjudicator_type=AdjudicatorType.INDEPENDENT_STATIC_ANALYSIS,
            adjudicator_id="independent-ast-inspector",
            adjudication_version="independent-ast/1.0.0",
            evidence_refs=("test",),
            reason="disagreement fixture",
            created_at="2026-01-01T00:00:00+00:00",
            adjudication_mode=AdjudicationMode.BLIND,
        )
        payload["criterion_adjudications"] = [item.to_dict() for item in record.criterion_adjudications] + [extra.to_dict()]
        dual = RealTaskEvidenceRecord.from_dict(payload)
        self.assertFalse(validate_record(dual))

    def test_metric_integrity_records_validate(self) -> None:
        records = metric_integrity_records()
        result = validate_dataset_records(records)
        self.assertTrue(result["ok"], result["blocking"])
        keys = {exact_artifact_key(record) for record in records}
        self.assertEqual(len(keys), len(records))
