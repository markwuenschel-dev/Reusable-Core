"""INTEG-002: criterion_metrics published three arithmetically wrong rates.

`applicable` is appended to before the indeterminate `continue`, so it already
contains the indeterminate records. The published rates then either add
`indeterminate` to the denominator a second time, or divide an adjudicated-only
numerator by the wider applicable denominator. The severity buckets only ever
increment tp/fp, so per-severity recall was pinned to 1.0 whenever tp > 0.

The committed reports/verification_v1/v12_latest.json shows the consequence:
every checklet has n_applicable=8, n_indeterminate=8, n_not_applicable=0 and
reports criterion_indeterminate_rate=0.5 where the true rate is 1.0.
"""

import unittest

from verification_v1.analysis import criterion_metrics
from verification_v1.evidence import CriterionLabel

try:  # pragma: no cover - import shim matching the other v12 test modules
    from v12_helpers import make_record
except ImportError:
    from tests.v12_helpers import make_record


CHECKLET = "requirement_coverage"


def _records(labels_and_findings):
    return [
        make_record(name=name, labels={CHECKLET: label}, findings=findings)
        for name, label, findings in labels_and_findings
    ]


class CriterionRateArithmeticTest(unittest.TestCase):
    def test_indeterminate_rate_is_one_when_nothing_was_adjudicated(self) -> None:
        records = _records(
            [(f"r{i}", CriterionLabel.INDETERMINATE, None) for i in range(8)]
        )
        m = criterion_metrics(records, CHECKLET)
        self.assertEqual(m["n_applicable"], 8)
        self.assertEqual(m["n_indeterminate"], 8)
        self.assertEqual(m["n_not_applicable"], 0)
        self.assertEqual(m["criterion_indeterminate_rate"], 1.0)

    def test_indeterminate_rate_uses_the_applicable_denominator(self) -> None:
        records = _records(
            [
                ("a", CriterionLabel.INDETERMINATE, None),
                ("b", CriterionLabel.INDETERMINATE, None),
                ("c", CriterionLabel.TRUE, {CHECKLET: "medium"}),
                ("d", CriterionLabel.FALSE, None),
            ]
        )
        m = criterion_metrics(records, CHECKLET)
        self.assertEqual(m["n_applicable"], 4)
        self.assertEqual(m["n_indeterminate"], 2)
        self.assertEqual(m["criterion_indeterminate_rate"], 0.5)

    def test_not_applicable_is_outside_the_applicable_denominator(self) -> None:
        records = _records(
            [
                ("a", CriterionLabel.INDETERMINATE, None),
                ("b", CriterionLabel.TRUE, {CHECKLET: "medium"}),
                ("c", CriterionLabel.NOT_APPLICABLE, None),
            ]
        )
        m = criterion_metrics(records, CHECKLET)
        self.assertEqual(m["n_applicable"], 2)
        self.assertEqual(m["n_not_applicable"], 1)
        self.assertEqual(m["criterion_indeterminate_rate"], 0.5)

    def test_abstention_rate_is_undefined_when_nothing_was_adjudicated(self) -> None:
        """abstain is only counted among adjudicated records, so the denominator
        must be the adjudicated count -- not a wider one that reports a
        confident 0.0 for a population that was never adjudicated."""
        records = _records(
            [(f"r{i}", CriterionLabel.INDETERMINATE, None) for i in range(8)]
        )
        m = criterion_metrics(records, CHECKLET)
        self.assertEqual(m["n_adjudicated"], 0)
        self.assertIsNone(m["criterion_abstention_rate"])

    def test_recall_by_severity_is_not_pinned_to_one(self) -> None:
        """A false negative carries no reported finding, so it has no severity to
        be bucketed under; per-severity recall is undefined by construction and
        must not be published as a perfect score."""
        records = _records(
            [
                ("a", CriterionLabel.TRUE, {CHECKLET: "medium"}),
                ("b", CriterionLabel.TRUE, None),  # missed -> false negative
            ]
        )
        m = criterion_metrics(records, CHECKLET)
        self.assertEqual(m["false_negative"], 1)
        self.assertTrue(m["recall_by_severity"], "severity buckets should exist")
        for severity, value in m["recall_by_severity"].items():
            self.assertIsNone(value, f"{severity} recall must not claim 1.0")

    def test_precision_by_severity_still_computes(self) -> None:
        records = _records(
            [
                ("a", CriterionLabel.TRUE, {CHECKLET: "medium"}),
                ("b", CriterionLabel.FALSE, {CHECKLET: "medium"}),
            ]
        )
        m = criterion_metrics(records, CHECKLET)
        self.assertEqual(m["precision_by_severity"]["medium"], 0.5)


if __name__ == "__main__":
    unittest.main()
