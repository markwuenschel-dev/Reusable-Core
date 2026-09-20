"""VS-V1.2 evidence-record contracts. Sidecar to V1.1; does not alter runtime authority."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Mapping

from .contracts import (
    CheckletObservation,
    CheckletVerdict,
    GateResult,
    HardVerifierOutcome,
    HardVerifierResult,
    ShadowRiskAssessment,
    freeze_value,
    jsonable,
    utc_now,
)

EVIDENCE_SCHEMA_VERSION = "verification-v1.2-evidence/1.0.0"
EXPERIMENT_ID = "vs-v1.2-exp-001"
COHORT_ID = "v1.2-c01-v11-frozen"
EXPERIMENT_BASELINE_ID = "vs-v1.1-baseline-001"
DATASET_KIND_CORE = "real_task_core"
DATASET_KIND_CHALLENGE = "challenge_set"

CHECKLET_IDS = (
    "requirement_coverage",
    "test_adequacy",
    "change_scope",
    "dependency_integration_risk",
    "error_boundary",
)
CRITERION_IDS = {
    "requirement_coverage": "requirements-covered",
    "test_adequacy": "producer-test-adequacy",
    "change_scope": "declared-change-scope",
    "dependency_integration_risk": "interface-dependency-risk",
    "error_boundary": "failure-boundaries",
}
EVIDENCE_FAMILY_IDS = {
    checklet_id: f"deterministic:vs-v1:{checklet_id}" for checklet_id in CHECKLET_IDS
}
KNOWN_CHECKLET_VERSION = "1.1.0"
KNOWN_SHADOW_POLICY_ID = "shadow-rule-v1.1"
KNOWN_SHADOW_POLICY_VERSION = "1.1.0"
KNOWN_HARD_VERIFIER_IDS = {
    "command-hard-verifier": "1.1.0",
    "unavailable-reference-oracle": "1.1.0",
    "fixture-reference-oracle": "1.0.0",
    "static-test-oracle": "1.0.0",
    "recorded-hard-verifier": "replay",
}


class TaskOrigin(str, Enum):
    REAL_HISTORICAL = "real_historical"
    REAL_LIVE = "real_live"
    CONTROLLED_MUTATION = "controlled_mutation"
    ENGINEERING_FIXTURE = "engineering_fixture"


class Partition(str, Enum):
    DEVELOPMENT = "development"
    POLICY_SELECTION = "policy_selection"
    CALIBRATION_RESERVED = "calibration_reserved"
    HOLDOUT = "holdout"


class CriterionLabel(str, Enum):
    TRUE = "criterion_true"
    FALSE = "criterion_false"
    INDETERMINATE = "criterion_indeterminate"
    NOT_APPLICABLE = "criterion_not_applicable"


class AdjudicatorType(str, Enum):
    DETERMINISTIC_ORACLE = "deterministic_oracle"
    INDEPENDENT_STATIC_ANALYSIS = "independent_static_analysis"
    INDEPENDENT_TEST = "independent_test"
    INDEPENDENT_RULE = "independent_rule"
    BOUNDED_EXPERT_REVIEW = "bounded_expert_review"


class AdjudicationMode(str, Enum):
    BLIND = "blind"
    ASSISTED = "assisted"


class CandidateSource(str, Enum):
    HISTORICAL_COMMITTED_SOLUTION = "historical_committed_solution"
    HISTORICAL_REJECTED_SOLUTION = "historical_rejected_solution"
    RECORDED_AGENT_OUTPUT = "recorded_agent_output"
    CONTROLLED_REAL_TASK_REPLAY = "controlled_real_task_replay"
    LIVE_BOUNDED_PRODUCER_RUN = "live_bounded_producer_run"
    ENGINEERING_FIXTURE = "engineering_fixture"


class ReplayMode(str, Enum):
    FULL = "full"
    FROZEN_OBSERVATION = "frozen-observation"
    ANALYSIS_ONLY = "analysis-only"


class SelectionReason(str, Enum):
    NATURAL = "natural"
    FAILURE_ENRICHMENT = "failure_enrichment"
    CRITERION_COVERAGE = "criterion_coverage"
    ENGINEERING_CONTROL = "engineering_control"


class FailureCode(str, Enum):
    TASK_CONTRACT_INVALID = "TASK_CONTRACT_INVALID"
    BASE_REVISION_UNAVAILABLE = "BASE_REVISION_UNAVAILABLE"
    PATCH_INVALID = "PATCH_INVALID"
    PATCH_APPLY_FAILED = "PATCH_APPLY_FAILED"
    WORKSPACE_DIGEST_FAILED = "WORKSPACE_DIGEST_FAILED"
    CHECKLET_RUN_FAILED = "CHECKLET_RUN_FAILED"
    CHECKLET_TIMEOUT = "CHECKLET_TIMEOUT"
    ORACLE_UNAVAILABLE = "ORACLE_UNAVAILABLE"
    ORACLE_INJECTION_FAILED = "ORACLE_INJECTION_FAILED"
    HARD_VERIFY_UNKNOWN = "HARD_VERIFY_UNKNOWN"
    HARD_VERIFY_INFRA_ERROR = "HARD_VERIFY_INFRA_ERROR"
    CRITERION_ADJUDICATION_MISSING = "CRITERION_ADJUDICATION_MISSING"
    CRITERION_ADJUDICATION_CONFLICT = "CRITERION_ADJUDICATION_CONFLICT"
    DATASET_DUPLICATE = "DATASET_DUPLICATE"
    DIGEST_MISMATCH = "DIGEST_MISMATCH"
    PARTITION_LEAKAGE = "PARTITION_LEAKAGE"
    BASELINE_VERSION_UNKNOWN = "BASELINE_VERSION_UNKNOWN"
    REPORT_INTEGRITY_FAILURE = "REPORT_INTEGRITY_FAILURE"
    ORACLE_LEAK = "ORACLE_LEAK"
    LABEL_CONTAMINATION = "LABEL_CONTAMINATION"
    HOLDOUT_ACCESS = "HOLDOUT_ACCESS"
    RECORD_INVALIDATED = "RECORD_INVALIDATED"
    MISSING_IDENTITY = "MISSING_IDENTITY"
    UNKNOWN_TASK_ORIGIN = "UNKNOWN_TASK_ORIGIN"
    UNKNOWN_PARTITION = "UNKNOWN_PARTITION"
    TIMESTAMP_INVALID = "TIMESTAMP_INVALID"
    PRODUCER_PROVENANCE_MISSING = "PRODUCER_PROVENANCE_MISSING"
    CRITERION_LABEL_INCONSISTENT = "CRITERION_LABEL_INCONSISTENT"


FORBIDDEN_CHECKLET_CONTEXT_KEYS = frozenset(
    {
        "hard_verifier_outcome",
        "expected_defect_class",
        "expected_affected_checklets",
        "criterion_adjudications",
        "criterion_labels",
        "criterion_truth",
        "partition",
        "dataset_partition",
        "holdout",
        "final_outcome",
        "shadow_action",
        "reference_files",
        "oracle_bundle",
        "oracle_files",
        "hard_verifier_result",
    }
)

DETERMINATE_HARD_OUTCOMES = frozenset(
    {HardVerifierOutcome.ACCEPTED, HardVerifierOutcome.REJECTED}
)


def canonical_digest(value: Any) -> str:
    payload = json.dumps(jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(payload.encode("utf-8")).hexdigest()


def utf8_digest(text: str) -> str:
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return sha256(canonical).hexdigest()


def workspace_manifest_digest(files: Mapping[str, str]) -> str:
    return workspace_manifest_digest_from_hashes(
        {path: utf8_digest(str(content)) for path, content in files.items()}
    )


def workspace_manifest_digest_from_hashes(file_hashes: Mapping[str, str]) -> str:
    """The same manifest digest, for a surface that is already hashed.

    Lets the hard verifier report what it actually materialised without shipping
    file contents back, so the recorded materialised digest is real evidence
    rather than a copy of the declared one.
    """
    entries = [
        {"path": str(path).replace("\\", "/"), "sha256": str(digest)}
        for path, digest in sorted(file_hashes.items(), key=lambda item: str(item[0]).replace("\\", "/"))
    ]
    return canonical_digest(entries)


def identity_record_id(
    experiment_id: str,
    task_id: str,
    artifact_digest: str,
    oracle_bundle_digest: str,
) -> str:
    digest = canonical_digest(
        {
            "experiment_id": experiment_id,
            "task_id": task_id,
            "artifact_digest": artifact_digest,
            "oracle_bundle_digest": oracle_bundle_digest,
        }
    )
    return f"v12_{digest[:32]}"


@dataclass(frozen=True)
class ProducerProvenance:
    producer_executor_id: str
    producer_model_id: str
    producer_scaffold_version: str
    producer_tool_profile: str
    producer_attempt_number: int
    candidate_source: CandidateSource

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ProducerProvenance":
        return cls(
            producer_executor_id=str(payload["producer_executor_id"]),
            producer_model_id=str(payload["producer_model_id"]),
            producer_scaffold_version=str(payload["producer_scaffold_version"]),
            producer_tool_profile=str(payload["producer_tool_profile"]),
            producer_attempt_number=int(payload["producer_attempt_number"]),
            candidate_source=CandidateSource(payload["candidate_source"]),
        )


@dataclass(frozen=True)
class SamplingProvenance:
    sampling_source: str
    sampling_rule: str
    selection_timestamp: str
    selection_reason: SelectionReason
    dataset_kind: str = DATASET_KIND_CORE

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SamplingProvenance":
        return cls(
            sampling_source=str(payload["sampling_source"]),
            sampling_rule=str(payload["sampling_rule"]),
            selection_timestamp=str(payload["selection_timestamp"]),
            selection_reason=SelectionReason(payload["selection_reason"]),
            dataset_kind=str(payload.get("dataset_kind", DATASET_KIND_CORE)),
        )


@dataclass(frozen=True)
class CriterionAdjudication:
    task_id: str
    artifact_digest: str
    checklet_id: str
    criterion_id: str
    label: CriterionLabel
    adjudicator_type: AdjudicatorType
    adjudicator_id: str
    adjudication_version: str
    evidence_refs: tuple[str, ...]
    reason: str
    created_at: str
    adjudication_mode: AdjudicationMode = AdjudicationMode.BLIND

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_refs", tuple(str(item) for item in self.evidence_refs))
        if self.checklet_id not in CHECKLET_IDS:
            raise ValueError(f"unknown checklet_id: {self.checklet_id}")
        if self.criterion_id != CRITERION_IDS[self.checklet_id]:
            raise ValueError("criterion_id does not match checklet_id")

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CriterionAdjudication":
        return cls(
            task_id=str(payload["task_id"]),
            artifact_digest=str(payload["artifact_digest"]),
            checklet_id=str(payload["checklet_id"]),
            criterion_id=str(payload["criterion_id"]),
            label=CriterionLabel(payload["label"]),
            adjudicator_type=AdjudicatorType(payload["adjudicator_type"]),
            adjudicator_id=str(payload["adjudicator_id"]),
            adjudication_version=str(payload["adjudication_version"]),
            evidence_refs=tuple(str(item) for item in payload.get("evidence_refs", [])),
            reason=str(payload["reason"]),
            created_at=str(payload["created_at"]),
            adjudication_mode=AdjudicationMode(payload.get("adjudication_mode", AdjudicationMode.BLIND.value)),
        )


@dataclass(frozen=True)
class RealTaskEvidenceRecord:
    record_id: str
    schema_version: str
    experiment_id: str
    cohort_id: str
    experiment_baseline_id: str
    partition: Partition
    split_algorithm_version: str
    split_seed: str
    task_id: str
    task_family_id: str
    task_contract_digest: str
    task_type: str
    task_complexity: str
    task_origin: TaskOrigin
    repository_id: str
    repository_group: str
    language: str
    framework: str
    base_revision: str
    base_tree_digest: str
    candidate_id: str
    candidate_lineage_id: str
    candidate_patch_digest: str
    candidate_workspace_digest: str
    verifier_workspace_digest: str
    materialized_workspace_digest: str
    oracle_bundle_digest: str
    oracle_scope: str
    oracle_limitations: str
    producer: ProducerProvenance
    sampling: SamplingProvenance
    changed_file_count: int
    lines_added: int
    lines_deleted: int
    patch_size_bucket: str
    change_surface_class: str
    gate_results: tuple[dict[str, Any], ...]
    checklet_observations: tuple[dict[str, Any], ...]
    shadow_policy_id: str
    shadow_policy_version: str
    shadow_assessment: Mapping[str, Any]
    hard_verifier_id: str
    hard_verifier_version: str
    hard_verifier_result: Mapping[str, Any]
    hard_outcome: HardVerifierOutcome
    criterion_adjudications: tuple[CriterionAdjudication, ...]
    cost_summary: Mapping[str, Any]
    latency_summary: Mapping[str, Any]
    data_quality_flags: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    created_at: str
    component_versions: Mapping[str, Any]
    candidate_bytes_b64: str
    oracle_files: Mapping[str, str]
    task_contract: Mapping[str, Any]
    run_id: str
    invalidated: bool = False
    invalidation_reason: str = ""
    successor_record_id: str = ""
    missing_evidence_links: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_results", tuple(dict(item) for item in self.gate_results))
        object.__setattr__(self, "checklet_observations", tuple(dict(item) for item in self.checklet_observations))
        object.__setattr__(self, "criterion_adjudications", tuple(self.criterion_adjudications))
        object.__setattr__(self, "data_quality_flags", tuple(str(item) for item in self.data_quality_flags))
        object.__setattr__(self, "provenance_refs", tuple(str(item) for item in self.provenance_refs))
        object.__setattr__(self, "missing_evidence_links", tuple(str(item) for item in self.missing_evidence_links))
        object.__setattr__(self, "shadow_assessment", freeze_value(self.shadow_assessment))
        object.__setattr__(self, "hard_verifier_result", freeze_value(self.hard_verifier_result))
        object.__setattr__(self, "cost_summary", freeze_value(self.cost_summary))
        object.__setattr__(self, "latency_summary", freeze_value(self.latency_summary))
        object.__setattr__(self, "component_versions", freeze_value(self.component_versions))
        object.__setattr__(self, "oracle_files", freeze_value(dict(self.oracle_files)))
        object.__setattr__(self, "task_contract", freeze_value(dict(self.task_contract)))
        object.__setattr__(self, "metadata", freeze_value(self.metadata))

    @property
    def artifact_digest(self) -> str:
        return self.candidate_patch_digest

    @property
    def group_id(self) -> str:
        return f"{self.repository_id}::{self.task_family_id}"

    @property
    def determinate(self) -> bool:
        return self.hard_outcome in DETERMINATE_HARD_OUTCOMES

    def primary_criterion_label(
        self,
        checklet_id: str,
        *,
        adjudicator_ids: frozenset[str] | set[str] | None = None,
    ) -> CriterionLabel | None:
        labels = [
            item.label
            for item in self.criterion_adjudications
            if item.checklet_id == checklet_id
            and (adjudicator_ids is None or item.adjudicator_id in adjudicator_ids)
        ]
        if not labels:
            return None
        unique = set(labels)
        if len(unique) == 1:
            return labels[0]
        return CriterionLabel.INDETERMINATE

    def observation_for(self, checklet_id: str) -> Mapping[str, Any] | None:
        for item in self.checklet_observations:
            if item.get("checklet_id") == checklet_id:
                return item
        return None

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RealTaskEvidenceRecord":
        adjudications = tuple(CriterionAdjudication.from_dict(item) for item in payload.get("criterion_adjudications", []))
        return cls(
            record_id=str(payload["record_id"]),
            schema_version=str(payload["schema_version"]),
            experiment_id=str(payload["experiment_id"]),
            cohort_id=str(payload["cohort_id"]),
            experiment_baseline_id=str(payload["experiment_baseline_id"]),
            partition=Partition(payload["partition"]),
            split_algorithm_version=str(payload["split_algorithm_version"]),
            split_seed=str(payload["split_seed"]),
            task_id=str(payload["task_id"]),
            task_family_id=str(payload["task_family_id"]),
            task_contract_digest=str(payload["task_contract_digest"]),
            task_type=str(payload["task_type"]),
            task_complexity=str(payload["task_complexity"]),
            task_origin=TaskOrigin(payload["task_origin"]),
            repository_id=str(payload["repository_id"]),
            repository_group=str(payload["repository_group"]),
            language=str(payload["language"]),
            framework=str(payload["framework"]),
            base_revision=str(payload["base_revision"]),
            base_tree_digest=str(payload["base_tree_digest"]),
            candidate_id=str(payload["candidate_id"]),
            candidate_lineage_id=str(payload["candidate_lineage_id"]),
            candidate_patch_digest=str(payload["candidate_patch_digest"]),
            candidate_workspace_digest=str(payload["candidate_workspace_digest"]),
            verifier_workspace_digest=str(payload["verifier_workspace_digest"]),
            materialized_workspace_digest=str(payload["materialized_workspace_digest"]),
            oracle_bundle_digest=str(payload["oracle_bundle_digest"]),
            oracle_scope=str(payload["oracle_scope"]),
            oracle_limitations=str(payload["oracle_limitations"]),
            producer=ProducerProvenance.from_dict(payload["producer"]),
            sampling=SamplingProvenance.from_dict(payload["sampling"]),
            changed_file_count=int(payload["changed_file_count"]),
            lines_added=int(payload["lines_added"]),
            lines_deleted=int(payload["lines_deleted"]),
            patch_size_bucket=str(payload["patch_size_bucket"]),
            change_surface_class=str(payload["change_surface_class"]),
            gate_results=tuple(payload.get("gate_results", [])),
            checklet_observations=tuple(payload.get("checklet_observations", [])),
            shadow_policy_id=str(payload["shadow_policy_id"]),
            shadow_policy_version=str(payload["shadow_policy_version"]),
            shadow_assessment=dict(payload["shadow_assessment"]),
            hard_verifier_id=str(payload["hard_verifier_id"]),
            hard_verifier_version=str(payload["hard_verifier_version"]),
            hard_verifier_result=dict(payload["hard_verifier_result"]),
            hard_outcome=HardVerifierOutcome(payload["hard_outcome"]),
            criterion_adjudications=adjudications,
            cost_summary=dict(payload.get("cost_summary", {})),
            latency_summary=dict(payload.get("latency_summary", {})),
            data_quality_flags=tuple(payload.get("data_quality_flags", [])),
            provenance_refs=tuple(payload.get("provenance_refs", [])),
            created_at=str(payload["created_at"]),
            component_versions=dict(payload.get("component_versions", {})),
            candidate_bytes_b64=str(payload.get("candidate_bytes_b64", "")),
            oracle_files=dict(payload.get("oracle_files", {})),
            task_contract=dict(payload.get("task_contract", {})),
            run_id=str(payload.get("run_id", "")),
            invalidated=bool(payload.get("invalidated", False)),
            invalidation_reason=str(payload.get("invalidation_reason", "")),
            successor_record_id=str(payload.get("successor_record_id", "")),
            missing_evidence_links=tuple(payload.get("missing_evidence_links", [])),
            metadata=dict(payload.get("metadata", {})),
        )


def observation_dicts(observations: tuple[CheckletObservation, ...]) -> tuple[dict[str, Any], ...]:
    return tuple(observation.to_dict() for observation in observations)


def gate_dicts(gates: tuple[GateResult, ...]) -> tuple[dict[str, Any], ...]:
    return tuple(gate.to_dict() for gate in gates)


def shadow_dict(assessment: ShadowRiskAssessment) -> dict[str, Any]:
    return assessment.to_dict()


def hard_result_dict(result: HardVerifierResult) -> dict[str, Any]:
    return result.to_dict()


def parse_iso8601(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def verdict_of(observation: Mapping[str, Any]) -> CheckletVerdict:
    return CheckletVerdict(observation["verdict"])
