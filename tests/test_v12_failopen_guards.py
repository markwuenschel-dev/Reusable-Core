"""Guards that could never fire.

INTEG-003 ingestion stripped the forbidden label keys before checking for them,
          so LABEL_CONTAMINATION was unreachable and a leaking manifest was
          silently laundered into the evidence dataset.
INTEG-004 assert_partition_allowed returned on any unrecognised purpose, so a
          typo'd purpose string silently granted holdout access.
INTEG-006 the second ORACLE_LEAK check built a set from a Mapping, which yields
          its keys, and intersected oracle file paths with metadata key names.
"""

import json
import pathlib
import unittest

from verification_v1.ingestion import fixture_to_manifest, ingest_task_manifest
from verification_v1.splits import HoldoutAccessError, assert_partition_allowed

try:  # pragma: no cover - import shim matching the other v12 test modules
    from v12_helpers import make_record
except ImportError:
    from tests.v12_helpers import make_record


FIXTURES = (
    pathlib.Path(__file__).resolve().parent.parent
    / "evals"
    / "verification_v1"
    / "engineering_fixture_set.json"
)


def _manifest():
    payload = json.loads(FIXTURES.read_text(encoding="utf-8"))
    return fixture_to_manifest(payload["fixtures"][0])


class LabelContaminationReachableTest(unittest.TestCase):
    def test_clean_manifest_still_ingests(self) -> None:
        record = ingest_task_manifest(_manifest())
        self.assertTrue(record.record_id)

    def test_engineering_fixture_labels_are_still_sanitised(self) -> None:
        """Fixtures carry their own oracle labels by construction; stripping is
        the mechanism that keeps those away from the checklets, not an error."""
        manifest = _manifest()
        metadata = dict(manifest["artifact"].get("metadata") or {})
        metadata["hard_verifier_outcome"] = "accepted"
        manifest["artifact"]["metadata"] = metadata
        record = ingest_task_manifest(manifest)
        self.assertNotIn("hard_verifier_outcome", record.task_contract.get("metadata", {}))

    def test_real_task_outcome_label_is_rejected_not_laundered(self) -> None:
        manifest = _manifest()
        manifest["task_origin"] = "real_historical"
        metadata = dict(manifest["artifact"].get("metadata") or {})
        metadata["hard_verifier_outcome"] = "accepted"
        manifest["artifact"]["metadata"] = metadata
        with self.assertRaises(ValueError) as ctx:
            ingest_task_manifest(manifest)
        self.assertIn("LABEL_CONTAMINATION", str(ctx.exception))

    def test_real_task_leaked_partition_is_rejected(self) -> None:
        manifest = _manifest()
        manifest["task_origin"] = "real_live"
        metadata = dict(manifest["artifact"].get("metadata") or {})
        metadata["partition"] = "holdout"
        manifest["artifact"]["metadata"] = metadata
        with self.assertRaises(ValueError) as ctx:
            ingest_task_manifest(manifest)
        self.assertIn("LABEL_CONTAMINATION", str(ctx.exception))


class PartitionPurposeFailsClosedTest(unittest.TestCase):
    def test_unrecognised_purpose_is_refused(self) -> None:
        holdout = make_record(name="h", partition=None)
        with self.assertRaises(HoldoutAccessError):
            # 'threshold_tuning' is not in the vocabulary; the real name is
            # 'threshold_selection'. A typo must not open every partition.
            assert_partition_allowed((holdout,), "threshold_tuning")

    def test_known_purposes_still_work(self) -> None:
        record = make_record(name="d")
        assert_partition_allowed((record,), "v12_analysis")


if __name__ == "__main__":
    unittest.main()
