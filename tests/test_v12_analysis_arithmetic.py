"""Regression tests for the analysis.py arithmetic/aliasing cluster.

INTEG-019 total_verification_latency_ms zipped per-checklet latencies positionally
INTEG-020 unnecessary_verify_rate used a denominator including non-determinate records
INTEG-021 the abstain/error exclusion for finding-bearing bins was computed and dropped
INTEG-022 co_finding_matrix and jaccard_overlap were the same object
"""

import dataclasses
import unittest

from verification_v1.analysis import (
    combination_analysis,
    cost_latency,
    dependence_metrics,
    shadow_metrics,
)

try:  # pragma: no cover - import shim matching the other v12 test modules
    from v12_helpers import make_record
except ImportError:
    from tests.v12_helpers import make_record


CHECKLET = "requirement_coverage"
OTHER = "test_adequacy"


def _with_verdict(record, checklet_id, verdict):
    """Rewrite one observation's verdict; make_record only emits clean/finding."""
    observations = []
    for item in record.checklet_observations:
        item = dict(item)
        if item.get("checklet_id") == checklet_id:
            item["verdict"] = verdict
        observations.append(item)
    return dataclasses.replace(record, checklet_observations=tuple(observations))


class OverlapAliasingTest(unittest.TestCase):
    def test_co_finding_matrix_is_not_the_jaccard_object(self) -> None:
        records = [
            make_record(name="a", findings={CHECKLET: "medium", OTHER: "medium"}),
            make_record(name="b", findings={CHECKLET: "medium"}),
        ]
        result = dependence_metrics(records)
        self.assertIsNot(
            result["co_finding_matrix"],
            result["jaccard_overlap"],
            "two report keys bound the same object",
        )

    def test_co_finding_matrix_reports_co_occurrence_counts(self) -> None:
        records = [
            make_record(name="a", findings={CHECKLET: "medium", OTHER: "medium"}),
            make_record(name="b", findings={CHECKLET: "medium"}),
        ]
        result = dependence_metrics(records)
        key = f"{CHECKLET}|{OTHER}"
        self.assertEqual(result["co_finding_matrix"][key], 1)
        # one of two records has both -> jaccard 1/2, distinct from the count
        self.assertEqual(result["jaccard_overlap"][key], 0.5)


class UnnecessaryVerifyDenominatorTest(unittest.TestCase):
    def test_denominator_counts_only_determinate_would_verify(self) -> None:
        records = [
            # would_hard_verify + determinate + accepted -> unnecessary
            make_record(name="a", findings={CHECKLET: "medium"}, shadow_action="would_hard_verify", hard_outcome="accepted"),
            # would_hard_verify but NOT determinate -> must not enter the denominator
            make_record(name="b", findings={CHECKLET: "medium"}, shadow_action="would_hard_verify", hard_outcome="outcome_unknown"),
        ]
        result = shadow_metrics(records)
        self.assertEqual(result["n_would_hard_verify"], 2)
        self.assertEqual(result["n_unnecessary_shadow_verifies"], 1)
        self.assertEqual(result["unnecessary_verify_rate"], 1.0)


class CombinationBinExclusionTest(unittest.TestCase):
    def test_finding_bin_excludes_records_with_an_abstain(self) -> None:
        clean = make_record(name="a", findings={CHECKLET: "low"})
        noisy = _with_verdict(
            make_record(name="b", findings={CHECKLET: "low"}), OTHER, "abstain"
        )
        combos = {row["combination"]: row for row in combination_analysis([clean, noisy])}
        self.assertEqual(combos["one_low_finding"]["n"], 1)

    def test_finding_bin_excludes_records_with_an_error(self) -> None:
        clean = make_record(name="a", findings={CHECKLET: "medium"})
        noisy = _with_verdict(
            make_record(name="b", findings={CHECKLET: "medium"}), OTHER, "error"
        )
        combos = {row["combination"]: row for row in combination_analysis([clean, noisy])}
        self.assertEqual(combos["one_medium_finding"]["n"], 1)


class LatencyAttributionTest(unittest.TestCase):
    def test_total_latency_is_summed_per_record_not_positionally(self) -> None:
        """A record missing an observation shortens that checklet's list; a
        positional zip then borrows a later record's latency."""
        full = make_record(name="a", findings={CHECKLET: "medium"})
        partial = make_record(name="b")
        partial = dataclasses.replace(
            partial,
            checklet_observations=tuple(
                item
                for item in partial.checklet_observations
                if item.get("checklet_id") != CHECKLET
            ),
        )
        result = cost_latency([partial, full])
        per_record_totals = sum(
            float(item.get("latency_ms", 0.0))
            for record in (partial, full)
            for item in record.checklet_observations
        )
        self.assertEqual(result["total_verification_latency_ms"]["total"], per_record_totals)


if __name__ == "__main__":
    unittest.main()
