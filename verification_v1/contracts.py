"""Explicit, serializable contracts for Verification Slice V1."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4


SCHEMA_VERSION = "verification-v1-contracts/1.0.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {item.name: jsonable(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [jsonable(item) for item in value]
    return value


def freeze_value(value: Any) -> Any:
    """Create immutable value semantics for contracts crossing execution boundaries."""
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): freeze_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_value(item) for item in value)
    if isinstance(value, set):
        return frozenset(freeze_value(item) for item in value)
    return value


def mutable_copy(value: Any) -> Any:
    """Return a disposable mutable copy for diagnostic checklet context."""
    if isinstance(value, Mapping):
        return {str(key): mutable_copy(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, frozenset, set)):
        return [mutable_copy(item) for item in value]
    return value


class GateStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    NOT_APPLICABLE = "not_applicable"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CheckletVerdict(str, Enum):
    CLEAN = "clean"
    FINDING = "finding"
    ABSTAIN = "abstain"
    ERROR = "error"


class RiskBand(str, Enum):
    LOW = "low"
    ELEVATED = "elevated"
    HIGH = "high"
    INDETERMINATE = "indeterminate"


class ShadowAction(str, Enum):
    WOULD_WAIVE = "would_waive"
    WOULD_HARD_VERIFY = "would_hard_verify"
    WOULD_ESCALATE = "would_escalate"


class HardVerifierOutcome(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    OUTCOME_UNKNOWN = "outcome_unknown"
    INFRASTRUCTURE_ERROR = "infrastructure_error"


class CounterfactualClass(str, Enum):
    CORRECT_SHADOW_WAIVE = "correct_shadow_waive"
    FALSE_SHADOW_WAIVE = "false_shadow_waive"
    CORRECT_SHADOW_VERIFY = "correct_shadow_verify"
    UNNECESSARY_SHADOW_VERIFY = "unnecessary_shadow_verify"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class TaskContract:
    task_id: str
    requirements: tuple[str, ...]
    description: str = ""
    version: str = "1.0.0"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "requirements", tuple(str(item) for item in self.requirements))
        object.__setattr__(self, "metadata", freeze_value(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


@dataclass(frozen=True)
class ArtifactRef:
    artifact_id: str
    artifact_digest: str
    artifact_type: str
    artifact_version: str
    run_id: str
    created_at: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", freeze_value(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


@dataclass(frozen=True)
class GateResult:
    gate_id: str
    gate_version: str
    artifact_digest: str
    status: GateStatus
    severity: Severity
    started_at: str
    completed_at: str
    latency_ms: float
    evidence_refs: tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)
    result_id: str = field(default_factory=lambda: new_id("gate"))

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_refs", tuple(str(item) for item in self.evidence_refs))
        object.__setattr__(self, "details", freeze_value(self.details))

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


@dataclass(frozen=True)
class CheckletSpec:
    checklet_id: str
    version: str
    domain_pack: str
    criterion_id: str
    description: str
    required_artifact_types: tuple[str, ...]
    required_context: tuple[str, ...]
    implementation_type: str
    authority_ceiling: str
    estimated_cost_class: str
    timeout_seconds: float
    required_or_optional: str
    evidence_family_template: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "required_artifact_types", tuple(str(item) for item in self.required_artifact_types))
        object.__setattr__(self, "required_context", tuple(str(item) for item in self.required_context))
        if self.authority_ceiling != "diagnostic":
            raise ValueError("VS-V1 checklets must have diagnostic authority only")

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


@dataclass(frozen=True)
class CheckletObservation:
    observation_id: str
    checklet_id: str
    checklet_version: str
    criterion_id: str
    artifact_digest: str
    verdict: CheckletVerdict
    severity: Severity
    finding_type: str | None
    locus: str | None
    summary: str
    confidence: float | None
    confidence_semantics: str
    evidence_refs: tuple[str, ...]
    trigger_refs: tuple[str, ...]
    model_provider: str | None
    resolved_model_id: str | None
    prompt_template_hash: str | None
    evidence_family_id: str
    started_at: str
    completed_at: str
    latency_ms: float
    estimated_or_actual_cost: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_refs", tuple(str(item) for item in self.evidence_refs))
        object.__setattr__(self, "trigger_refs", tuple(str(item) for item in self.trigger_refs))
        object.__setattr__(self, "estimated_or_actual_cost", freeze_value(self.estimated_or_actual_cost))
        object.__setattr__(self, "metadata", freeze_value(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


def parse_checklet_observation(
    value: Mapping[str, Any], spec: CheckletSpec, artifact_digest: str
) -> CheckletObservation:
    """Validate a model/backend structured payload before it enters the decision path."""
    required = set(CheckletObservation.__dataclass_fields__)
    actual = set(value)
    if actual != required:
        missing = sorted(required - actual)
        extra = sorted(actual - required)
        raise ValueError(f"structured observation keys mismatch; missing={missing}, extra={extra}")
    if value["checklet_id"] != spec.checklet_id or value["checklet_version"] != spec.version:
        raise ValueError("structured observation does not identify its issuing checklet version")
    if value["criterion_id"] != spec.criterion_id:
        raise ValueError("structured observation criterion does not match its checklet")
    if value["artifact_digest"] != artifact_digest:
        raise ValueError("structured observation binds a different artifact")
    if not isinstance(value["estimated_or_actual_cost"], Mapping):
        raise ValueError("structured observation cost must be an object")
    confidence = value["confidence"]
    if confidence is not None and not isinstance(confidence, (int, float)):
        raise ValueError("structured observation confidence must be numeric or null")
    return CheckletObservation(
        observation_id=str(value["observation_id"]),
        checklet_id=str(value["checklet_id"]),
        checklet_version=str(value["checklet_version"]),
        criterion_id=str(value["criterion_id"]),
        artifact_digest=str(value["artifact_digest"]),
        verdict=CheckletVerdict(value["verdict"]),
        severity=Severity(value["severity"]),
        finding_type=value["finding_type"],
        locus=value["locus"],
        summary=str(value["summary"]),
        confidence=float(confidence) if confidence is not None else None,
        confidence_semantics=str(value["confidence_semantics"]),
        evidence_refs=tuple(str(item) for item in value["evidence_refs"]),
        trigger_refs=tuple(str(item) for item in value["trigger_refs"]),
        model_provider=value["model_provider"],
        resolved_model_id=value["resolved_model_id"],
        prompt_template_hash=value["prompt_template_hash"],
        evidence_family_id=str(value["evidence_family_id"]),
        started_at=str(value["started_at"]),
        completed_at=str(value["completed_at"]),
        latency_ms=float(value["latency_ms"]),
        estimated_or_actual_cost=dict(value["estimated_or_actual_cost"]),
        metadata=dict(value["metadata"]),
    )


@dataclass(frozen=True)
class ShadowRiskAssessment:
    assessment_id: str
    artifact_digest: str
    policy_id: str
    policy_version: str
    risk_band: RiskBand
    shadow_action: ShadowAction
    reason_codes: tuple[str, ...]
    observation_ids: tuple[str, ...]
    gate_result_ids: tuple[str, ...]
    is_authoritative: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason_codes", tuple(str(item) for item in self.reason_codes))
        object.__setattr__(self, "observation_ids", tuple(str(item) for item in self.observation_ids))
        object.__setattr__(self, "gate_result_ids", tuple(str(item) for item in self.gate_result_ids))
        if self.is_authoritative:
            raise ValueError("shadow assessments are never authoritative")

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


@dataclass(frozen=True)
class HardVerifierResult:
    verifier_id: str
    verifier_version: str
    artifact_digest: str
    outcome: HardVerifierOutcome
    defect_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    oracle_class: str
    oracle_applicability: str
    started_at: str
    completed_at: str
    latency_ms: float
    cost: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "defect_refs", tuple(str(item) for item in self.defect_refs))
        object.__setattr__(self, "evidence_refs", tuple(str(item) for item in self.evidence_refs))
        object.__setattr__(self, "cost", freeze_value(self.cost))
        object.__setattr__(self, "metadata", freeze_value(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


@dataclass(frozen=True)
class ShadowComparison:
    artifact_digest: str
    shadow_action: ShadowAction
    hard_verifier_outcome: HardVerifierOutcome
    counterfactual_class: CounterfactualClass
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason_codes", tuple(str(item) for item in self.reason_codes))

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


def compare_shadow_to_hard_verifier(
    shadow: ShadowRiskAssessment, hard_result: HardVerifierResult
) -> ShadowComparison:
    if hard_result.outcome in {
        HardVerifierOutcome.OUTCOME_UNKNOWN,
        HardVerifierOutcome.INFRASTRUCTURE_ERROR,
    }:
        classification = CounterfactualClass.INDETERMINATE
    elif shadow.shadow_action == ShadowAction.WOULD_WAIVE:
        classification = (
            CounterfactualClass.CORRECT_SHADOW_WAIVE
            if hard_result.outcome == HardVerifierOutcome.ACCEPTED
            else CounterfactualClass.FALSE_SHADOW_WAIVE
        )
    else:
        classification = (
            CounterfactualClass.CORRECT_SHADOW_VERIFY
            if hard_result.outcome == HardVerifierOutcome.REJECTED
            else CounterfactualClass.UNNECESSARY_SHADOW_VERIFY
        )
    return ShadowComparison(
        artifact_digest=shadow.artifact_digest,
        shadow_action=shadow.shadow_action,
        hard_verifier_outcome=hard_result.outcome,
        counterfactual_class=classification,
        reason_codes=shadow.reason_codes,
    )
