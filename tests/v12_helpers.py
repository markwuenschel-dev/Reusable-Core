"""Builders for VS-V1.2 unit tests. Not used by runtime checklets."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping

from verification_v1.contracts import HardVerifierOutcome
from verification_v1.evidence import (
    CHECKLET_IDS,
    CRITERION_IDS,
    EVIDENCE_FAMILY_IDS,
    EVIDENCE_SCHEMA_VERSION,
    EXPERIMENT_BASELINE_ID,
    EXPERIMENT_ID,
    AdjudicationMode,
    AdjudicatorType,
    CandidateSource,
    CriterionAdjudication,
    CriterionLabel,
    Partition,
    ProducerProvenance,
    RealTaskEvidenceRecord,
    SamplingProvenance,
    SelectionReason,
    TaskOrigin,
    identity_record_id,
)
from verification_v1.splits import SPLIT_ALGORITHM_VERSION, SPLIT_SEED


def digest_for(label: str) -> str:
    return sha256(label.encode("utf-8")).hexdigest()


def _observation(
    checklet_id: str,
    artifact_digest: str,
    verdict: str = "clean",
    severity: str = "info",
) -> dict[str, Any]:
    finding = verdict == "finding"
    return {
        "observation_id": f"obs-{checklet_id}-{artifact_digest[:8]}",
        "checklet_id": checklet_id,
        "checklet_version": "1.1.0",
        "criterion_id": CRITERION_IDS[checklet_id],
        "artifact_digest": artifact_digest,
        "verdict": verdict,
        "severity": severity if finding else "info",
        "finding_type": "synthetic_finding" if finding else None,
        "locus": None,
        "summary": "synthetic observation",
        "confidence": 1.0,
        "confidence_semantics": "test",
        "evidence_refs": [],
        "trigger_refs": [],
        "model_provider": None,
        "resolved_model_id": None,
        "prompt_template_hash": None,
        "evidence_family_id": EVIDENCE_FAMILY_IDS[checklet_id],
        "started_at": "2026-01-01T00:00:00+00:00",
        "completed_at": "2026-01-01T00:00:00+00:00",
        "latency_ms": 1.0,
        "estimated_or_actual_cost": {"kind": "actual_cost", "amount": 0.0, "currency": "USD"},
        "metadata": {},
    }


def make_record(
    *,
    name: str,
    hard_outcome: str = "accepted",
    shadow_action: str = "would_waive",
    findings: Mapping[str, str] | None = None,
    labels: Mapping[str, CriterionLabel] | None = None,
    partition: Partition | None = None,
    task_family_id: str | None = None,
    repository_id: str = "repo-a",
    task_origin: TaskOrigin = TaskOrigin.ENGINEERING_FIXTURE,
    task_type: str = "bug_fix",
    patch_size_bucket: str = "small",
    producer_executor_id: str = "executor-a",
    oracle_scope: str = "unit_reference_tests",
    gates_status: str = "pass",
    invalidated: bool = False,
) -> RealTaskEvidenceRecord:
    artifact_digest = digest_for(f"artifact:{name}")
    oracle_digest = digest_for(f"oracle:{name}")
    workspace_digest = digest_for(f"workspace:{name}")
    task_id = f"task-{name}"
    family = task_family_id or task_id
    findings = dict(findings or {})
    labels = dict(labels or {})
    observations = []
    adjudications = []
    for checklet_id in CHECKLET_IDS:
        if checklet_id in findings:
            verdict = "finding"
            severity = findings[checklet_id]
        else:
            verdict = "clean"
            severity = "info"
        observations.append(_observation(checklet_id, artifact_digest, verdict, severity))
        adjudications.append(
            CriterionAdjudication(
                task_id=task_id,
                artifact_digest=artifact_digest,
                checklet_id=checklet_id,
                criterion_id=CRITERION_IDS[checklet_id],
                label=labels.get(checklet_id, CriterionLabel.FALSE),
                adjudicator_type=AdjudicatorType.INDEPENDENT_RULE,
                adjudicator_id="test-independent-rule",
                adjudication_version="test/1.0.0",
                evidence_refs=("test",),
                reason="synthetic criterion label",
                created_at="2026-01-01T00:00:00+00:00",
                adjudication_mode=AdjudicationMode.BLIND,
            )
        )
    return RealTaskEvidenceRecord(
        record_id=identity_record_id(EXPERIMENT_ID, task_id, artifact_digest, oracle_digest),
        schema_version=EVIDENCE_SCHEMA_VERSION,
        experiment_id=EXPERIMENT_ID,
        cohort_id="v1.2-c01-v11-frozen",
        experiment_baseline_id=EXPERIMENT_BASELINE_ID,
        partition=partition or Partition.DEVELOPMENT,
        split_algorithm_version=SPLIT_ALGORITHM_VERSION,
        split_seed=SPLIT_SEED,
        task_id=task_id,
        task_family_id=family,
        task_contract_digest=digest_for(f"contract:{name}"),
        task_type=task_type,
        task_complexity=patch_size_bucket,
        task_origin=task_origin,
        repository_id=repository_id,
        repository_group="group-a",
        language="python",
        framework="unittest",
        base_revision=f"rev-{name}",
        base_tree_digest=digest_for(f"base:{name}"),
        candidate_id=f"cand-{name}",
        candidate_lineage_id=family,
        candidate_patch_digest=artifact_digest,
        candidate_workspace_digest=workspace_digest,
        verifier_workspace_digest=digest_for(f"verifier:{name}"),
        materialized_workspace_digest=workspace_digest,
        oracle_bundle_digest=oracle_digest,
        oracle_scope=oracle_scope,
        oracle_limitations="synthetic oracle",
        producer=ProducerProvenance(
            producer_executor_id=producer_executor_id,
            producer_model_id="none",
            producer_scaffold_version="test",
            producer_tool_profile="test",
            producer_attempt_number=1,
            candidate_source=CandidateSource.ENGINEERING_FIXTURE,
        ),
        sampling=SamplingProvenance(
            sampling_source="unit-test",
            sampling_rule="synthetic",
            selection_timestamp="2026-01-01T00:00:00+00:00",
            selection_reason=SelectionReason.ENGINEERING_CONTROL,
            dataset_kind="challenge_set",
        ),
        changed_file_count=1,
        lines_added=4,
        lines_deleted=1,
        patch_size_bucket=patch_size_bucket,
        change_surface_class="single_file_local",
        gate_results=(
            {
                "gate_id": "coding_metadata_shape",
                "gate_version": "1.1.0",
                "artifact_digest": artifact_digest,
                "status": gates_status,
                "severity": "info",
                "started_at": "2026-01-01T00:00:00+00:00",
                "completed_at": "2026-01-01T00:00:00+00:00",
                "latency_ms": 0.5,
                "evidence_refs": [],
                "details": {},
                "result_id": f"gate-{name}",
            },
        ),
        checklet_observations=tuple(observations),
        shadow_policy_id="shadow-rule-v1.1",
        shadow_policy_version="1.1.0",
        shadow_assessment={
            "assessment_id": f"shadow-{name}",
            "artifact_digest": artifact_digest,
            "policy_id": "shadow-rule-v1.1",
            "policy_version": "1.1.0",
            "risk_band": "low" if shadow_action == "would_waive" else "elevated",
            "shadow_action": shadow_action,
            "reason_codes": ["synthetic"],
            "observation_ids": [item["observation_id"] for item in observations],
            "gate_result_ids": [f"gate-{name}"],
            "is_authoritative": False,
        },
        hard_verifier_id="command-hard-verifier",
        hard_verifier_version="1.1.0",
        hard_verifier_result={
            "verifier_id": "command-hard-verifier",
            "verifier_version": "1.1.0",
            "artifact_digest": artifact_digest,
            "outcome": hard_outcome,
            "defect_refs": [],
            "evidence_refs": ["synthetic"],
            "oracle_class": "external_executable_command",
            "oracle_applicability": "configured_task_acceptance",
            "started_at": "2026-01-01T00:00:00+00:00",
            "completed_at": "2026-01-01T00:00:00+00:00",
            "latency_ms": 2.0,
            "cost": {"kind": "actual_cost", "amount": 0.0, "currency": "USD"},
            "metadata": {},
        },
        hard_outcome=HardVerifierOutcome(hard_outcome),
        criterion_adjudications=tuple(adjudications),
        cost_summary={"objective_gate_cost": {"amount": 0.0}},
        latency_summary={"hard_verifier_latency_ms": 2.0},
        data_quality_flags=(),
        provenance_refs=("test",),
        created_at="2026-01-01T00:00:00+00:00",
        component_versions={
            "runner": {"version": "1.1.0"},
            "domain_pack": {"id": "coding-v1", "version": "1.1.0"},
            "policy": {"id": "shadow-rule-v1.1", "version": "1.1.0"},
            "gates": {"coding_metadata_shape": "1.1.0"},
            "hard_verifier": "command-hard-verifier/1.1.0",
            "checklets": {checklet_id: "1.1.0" for checklet_id in CHECKLET_IDS},
        },
        candidate_bytes_b64="",
        oracle_files={},
        task_contract={
            "task_id": task_id,
            "requirements": [],
            "description": f"desc {name}",
            "version": "1.0.0",
            "metadata": {},
        },
        run_id=f"run-{name}",
        invalidated=invalidated,
    )


def metric_integrity_records() -> tuple[RealTaskEvidenceRecord, ...]:
    """Hand-computed metric fixture. See tests/test_v12_analysis.py for expected numbers."""
    return (
        make_record(
            name="tp-reject",
            hard_outcome="rejected",
            shadow_action="would_hard_verify",
            findings={"requirement_coverage": "medium"},
            labels={"requirement_coverage": CriterionLabel.TRUE},
        ),
        make_record(
            name="tp-accept",
            hard_outcome="accepted",
            shadow_action="would_hard_verify",
            findings={"requirement_coverage": "medium"},
            labels={"requirement_coverage": CriterionLabel.TRUE},
        ),
        make_record(
            name="fp-accept",
            hard_outcome="accepted",
            shadow_action="would_hard_verify",
            findings={"requirement_coverage": "medium"},
            labels={"requirement_coverage": CriterionLabel.FALSE},
        ),
        make_record(
            name="fn-reject",
            hard_outcome="rejected",
            shadow_action="would_waive",
            findings={},
            labels={"requirement_coverage": CriterionLabel.TRUE},
        ),
        make_record(
            name="tn-accept",
            hard_outcome="accepted",
            shadow_action="would_waive",
            findings={},
            labels={"requirement_coverage": CriterionLabel.FALSE},
        ),
        make_record(
            name="fp-reject",
            hard_outcome="rejected",
            shadow_action="would_hard_verify",
            findings={"requirement_coverage": "medium"},
            labels={"requirement_coverage": CriterionLabel.FALSE},
        ),
        make_record(
            name="unknown-waive",
            hard_outcome="outcome_unknown",
            shadow_action="would_waive",
            findings={},
            labels={"requirement_coverage": CriterionLabel.FALSE},
        ),
        make_record(
            name="unnecessary-verify",
            hard_outcome="accepted",
            shadow_action="would_hard_verify",
            findings={"test_adequacy": "medium"},
            labels={"test_adequacy": CriterionLabel.TRUE},
        ),
    )
