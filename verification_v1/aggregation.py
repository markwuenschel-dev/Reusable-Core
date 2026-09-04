"""The fixed, deterministic, non-authoritative VS-V1 shadow policy."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    CheckletObservation,
    CheckletVerdict,
    GateResult,
    GateStatus,
    RiskBand,
    Severity,
    ShadowAction,
    ShadowRiskAssessment,
    new_id,
)


@dataclass(frozen=True)
class ShadowPolicy:
    policy_id: str = "shadow-rule-v1.1"
    version: str = "1.1.0"


class ShadowAggregator:
    def __init__(self, policy: ShadowPolicy | None = None) -> None:
        self.policy = policy or ShadowPolicy()

    def assess(
        self, artifact_digest: str, gates: tuple[GateResult, ...], observations: tuple[CheckletObservation, ...]
    ) -> ShadowRiskAssessment:
        reason_codes: list[str] = []
        if any(gate.status in {GateStatus.FAIL, GateStatus.ERROR} for gate in gates):
            risk, action = RiskBand.HIGH, ShadowAction.WOULD_HARD_VERIFY
            reason_codes.append("objective_gate_not_pass")
        elif any(observation.verdict == CheckletVerdict.ERROR for observation in observations):
            risk, action = RiskBand.INDETERMINATE, ShadowAction.WOULD_HARD_VERIFY
            reason_codes.append("required_checklet_error")
        elif any(observation.verdict == CheckletVerdict.ABSTAIN for observation in observations):
            risk, action = RiskBand.INDETERMINATE, ShadowAction.WOULD_HARD_VERIFY
            reason_codes.append("required_checklet_abstain")
        elif any(
            observation.verdict == CheckletVerdict.FINDING
            and observation.severity in {Severity.HIGH, Severity.CRITICAL}
            for observation in observations
        ):
            risk, action = RiskBand.HIGH, ShadowAction.WOULD_HARD_VERIFY
            reason_codes.append("high_severity_finding")
        elif any(
            observation.verdict == CheckletVerdict.FINDING and observation.severity == Severity.MEDIUM
            for observation in observations
        ):
            risk, action = RiskBand.ELEVATED, ShadowAction.WOULD_HARD_VERIFY
            reason_codes.append("medium_finding")
        else:
            risk, action = RiskBand.LOW, ShadowAction.WOULD_WAIVE
            reason_codes.append("no_shadow_escalation_rule_triggered")
        return ShadowRiskAssessment(
            assessment_id=new_id("shadow"),
            artifact_digest=artifact_digest,
            policy_id=self.policy.policy_id,
            policy_version=self.policy.version,
            risk_band=risk,
            shadow_action=action,
            reason_codes=tuple(reason_codes),
            observation_ids=tuple(observation.observation_id for observation in observations),
            gate_result_ids=tuple(gate.result_id for gate in gates),
        )
