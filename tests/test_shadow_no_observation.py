"""INTEG-018: zero checklet observations aggregated as LOW risk / would_waive.

CheckletRegistry.run_all emits no observation when required_artifact_types does
not match the artifact, and the aggregator's default branch is the permissive
one -- so "no checklet looked at this" produced the same shadow verdict as
"every checklet looked at this and found nothing".
"""

import unittest

from verification_v1.aggregation import ShadowAggregator
from verification_v1.contracts import (
    GateResult,
    GateStatus,
    RiskBand,
    Severity,
    ShadowAction,
    utc_now,
)


DIGEST = "d" * 64


def _passing_gate():
    return GateResult(
        gate_id="metadata-shape",
        gate_version="1.0.0",
        artifact_digest=DIGEST,
        status=GateStatus.PASS,
        severity=Severity.INFO,
        started_at=utc_now(),
        completed_at=utc_now(),
        latency_ms=0.0,
    )


class NoObservationIsNotAWaiverTest(unittest.TestCase):
    def test_zero_observations_does_not_waive(self) -> None:
        assessment = ShadowAggregator().assess(DIGEST, (_passing_gate(),), ())
        self.assertEqual(ShadowAction.WOULD_HARD_VERIFY, assessment.shadow_action)
        self.assertEqual(RiskBand.INDETERMINATE, assessment.risk_band)
        self.assertIn("no_checklet_observed_artifact", assessment.reason_codes)

    def test_no_gates_and_no_observations_still_does_not_waive(self) -> None:
        assessment = ShadowAggregator().assess(DIGEST, (), ())
        self.assertEqual(ShadowAction.WOULD_HARD_VERIFY, assessment.shadow_action)


if __name__ == "__main__":
    unittest.main()
