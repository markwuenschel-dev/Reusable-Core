import unittest

from verification_v1.evidence import Partition
from verification_v1.integrity import validate_dataset_records
from verification_v1.splits import (
    HoldoutAccessError,
    SPLIT_ALGORITHM_VERSION,
    SPLIT_SEED,
    assign_partition,
    leakage_failures,
)

try:
    from v12_helpers import make_record
except ImportError:
    from tests.v12_helpers import make_record


class PartitionTests(unittest.TestCase):
    def test_split_is_deterministic(self) -> None:
        first = assign_partition("repo-a::family-1")
        second = assign_partition("repo-a::family-1")
        self.assertEqual(first, second)
        self.assertEqual(SPLIT_ALGORITHM_VERSION, "grouped-sha256-v1")
        self.assertEqual(SPLIT_SEED, "vs-v1.2-split-seed-001")

    def test_candidate_lineage_grouping(self) -> None:
        left = make_record(name="lin-1", task_family_id="same-family", repository_id="repo-z")
        right = make_record(name="lin-2", task_family_id="same-family", repository_id="repo-z")
        self.assertEqual(left.group_id, right.group_id)
        self.assertEqual(left.candidate_lineage_id, right.candidate_lineage_id)

    def test_grouped_split_prevents_leakage(self) -> None:
        family = "shared-bug"
        repository = "repo-split"
        partition = assign_partition(f"{repository}::{family}")
        records = (
            make_record(name="split-a", task_family_id=family, repository_id=repository, partition=partition),
            make_record(name="split-b", task_family_id=family, repository_id=repository, partition=partition),
        )
        self.assertFalse(leakage_failures(records))
        contaminated = (
            records[0],
            make_record(
                name="split-c",
                task_family_id=family,
                repository_id=repository,
                partition=Partition.HOLDOUT if partition != Partition.HOLDOUT else Partition.DEVELOPMENT,
            ),
        )
        leaks = leakage_failures(contaminated)
        self.assertTrue(leaks)
        result = validate_dataset_records(contaminated)
        self.assertFalse(result["ok"])
        self.assertTrue(any("PARTITION_LEAKAGE" in item["codes"] for item in result["blocking"]))

    def test_holdout_access_guard(self) -> None:
        from verification_v1.splits import AnalysisScope, assert_partition_allowed, valid_unseal_receipt
        from verification_v1.analysis import analyze_records

        holdout = make_record(name="holdout-1", partition=Partition.HOLDOUT)
        calibration = make_record(name="cal-1", partition=Partition.CALIBRATION_RESERVED, task_family_id="cal-fam")
        with self.assertRaises(HoldoutAccessError):
            assert_partition_allowed((holdout,), "checklet_tuning")
        with self.assertRaises(HoldoutAccessError):
            assert_partition_allowed((calibration,), "checklet_tuning")
        with self.assertRaises(HoldoutAccessError):
            assert_partition_allowed((holdout,), "v12_analysis")
        with self.assertRaises(HoldoutAccessError):
            analyze_records((holdout, make_record(name="dev-unseal", partition=Partition.DEVELOPMENT)), scope=AnalysisScope.FINAL_HOLDOUT)
        self.assertFalse(valid_unseal_receipt(None))
        self.assertFalse(valid_unseal_receipt({"one_way": True}))
