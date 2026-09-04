"""V1.2 ingestion: freeze identities, run unchanged V1.1 evaluation, adjudicate independently."""

from __future__ import annotations

import base64
from difflib import SequenceMatcher
from typing import Any, Mapping

from .adjudication import adjudicate_artifact_bytes
from .artifacts import CandidateArtifact
from .bundle import BundleParseError, CodingBundle, is_test_path, parse_coding_bundle, public_functions
from .contracts import HardVerifierOutcome, TaskContract, utc_now
from .evaluation import FORBIDDEN_ARTIFACT_METADATA, run_to_record
from .evidence import (
    CHECKLET_IDS,
    COHORT_ID,
    EVIDENCE_SCHEMA_VERSION,
    EXPERIMENT_BASELINE_ID,
    EXPERIMENT_ID,
    FORBIDDEN_CHECKLET_CONTEXT_KEYS,
    CandidateSource,
    FailureCode,
    ProducerProvenance,
    RealTaskEvidenceRecord,
    SamplingProvenance,
    SelectionReason,
    TaskOrigin,
    canonical_digest,
    identity_record_id,
    utf8_digest,
    workspace_manifest_digest,
)
from .hard_verify import CommandHardVerifier, HardVerifier, UnavailableHardVerifier
from .integrity import checklet_context_is_clean
from .runner import VerificationRunner
from .splits import SPLIT_ALGORITHM_VERSION, SPLIT_SEED, assign_partition
from .telemetry import InMemoryEventSink

INGESTION_VERSION = "v1.2-ingest/1.0.0"
STRIPPED_METADATA_KEYS = FORBIDDEN_ARTIFACT_METADATA | FORBIDDEN_CHECKLET_CONTEXT_KEYS


def _task_from_mapping(payload: Mapping[str, Any]) -> TaskContract:
    return TaskContract(
        task_id=str(payload["task_id"]),
        requirements=tuple(str(item) for item in payload.get("requirements", [])),
        description=str(payload.get("description", "")),
        version=str(payload.get("version", "1.0.0")),
        metadata=dict(payload.get("metadata", {})),
    )


def _strip_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in dict(metadata).items() if key not in STRIPPED_METADATA_KEYS}


def _line_edits(before: str, after: str) -> tuple[int, int]:
    matcher = SequenceMatcher(a=before.splitlines(), b=after.splitlines())
    added = deleted = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert":
            added += j2 - j1
        elif tag == "delete":
            deleted += i2 - i1
        elif tag == "replace":
            deleted += i2 - i1
            added += j2 - j1
    return added, deleted


def patch_stats(bundle: CodingBundle) -> dict[str, Any]:
    added = deleted = 0
    changed = bundle.changed_paths()
    directories = {path.rsplit("/", 1)[0] if "/" in path else "." for path in changed}
    signature_changed = False
    integration = False
    for path in changed:
        before = bundle.base_files.get(path, "")
        after = bundle.patched_files.get(path, "")
        file_added, file_deleted = _line_edits(before, after)
        added += file_added
        deleted += file_deleted
        if path.endswith(".py") and not is_test_path(path):
            try:
                old_sigs = public_functions(before) if before else {}
                new_sigs = public_functions(after) if after else {}
            except (SyntaxError, UnicodeDecodeError):
                old_sigs, new_sigs = {}, {}
            if old_sigs != new_sigs:
                signature_changed = True
                if any(other != path and not is_test_path(other) for other in bundle.patched_files):
                    integration = True
    total = added + deleted
    if total < 20:
        bucket = "small"
    elif total < 100:
        bucket = "medium"
    else:
        bucket = "large"
    if not changed:
        surface = "none"
    elif integration:
        surface = "integration_boundary"
    elif signature_changed:
        surface = "public_interface"
    elif len(directories) > 1:
        surface = "cross_module"
    elif len(changed) > 1:
        surface = "multi_file_local"
    else:
        surface = "single_file_local"
    return {
        "changed_file_count": len(changed),
        "lines_added": added,
        "lines_deleted": deleted,
        "patch_size_bucket": bucket,
        "change_surface_class": surface,
    }


def _oracle_verifier(manifest: Mapping[str, Any]) -> tuple[HardVerifier, dict[str, str], str, str]:
    if manifest.get("oracle_unavailable"):
        return (
            UnavailableHardVerifier(),
            {},
            str(manifest.get("oracle_scope", "unavailable")),
            str(manifest.get("oracle_limitations", "independent oracle was not available")),
        )
    extra_files = {str(path): str(content) for path, content in dict(manifest.get("reference_files") or {}).items()}
    command = manifest.get("hard_command")
    if not command:
        raise ValueError(f"{FailureCode.ORACLE_UNAVAILABLE.value}: hard_command missing")
    verifier = CommandHardVerifier(
        tuple(str(part) for part in command),
        timeout_seconds=float(manifest.get("hard_timeout_seconds", 30.0)),
        extra_files=extra_files,
    )
    return (
        verifier,
        extra_files,
        str(manifest.get("oracle_scope", "unit_reference_tests")),
        str(manifest.get("oracle_limitations", "reference tests measure configured acceptance, not universal correctness")),
    )


def ingest_task_manifest(manifest: Mapping[str, Any]) -> RealTaskEvidenceRecord:
    task = _task_from_mapping(manifest["task"])
    artifact_payload = dict(manifest["artifact"])
    metadata = _strip_metadata(dict(artifact_payload.get("metadata", {})))
    leaks = checklet_context_is_clean(metadata)
    if leaks:
        raise ValueError(f"{FailureCode.LABEL_CONTAMINATION.value}: {sorted(STRIPPED_METADATA_KEYS & set(artifact_payload.get('metadata', {})))}")
    candidate = CandidateArtifact.from_text(
        artifact_id=str(artifact_payload["artifact_id"]),
        artifact_type=str(artifact_payload.get("artifact_type", "coding_patch")),
        content=str(artifact_payload["content"]),
        metadata=metadata,
    )
    verifier, oracle_files, oracle_scope, oracle_limitations = _oracle_verifier(manifest)
    missing_links: list[str] = []
    flags: list[str] = []
    try:
        bundle = parse_coding_bundle(candidate.content, metadata)
    except (BundleParseError, UnicodeDecodeError):
        bundle = None
        missing_links.append("candidate_workspace")
        flags.append(FailureCode.PATCH_INVALID.value)
    overlap = []
    if bundle is not None:
        overlap = sorted(path for path in oracle_files if path in bundle.patched_files)
        if overlap:
            raise ValueError(f"{FailureCode.ORACLE_INJECTION_FAILED.value}: {overlap}")
    if bundle is None:
        candidate_workspace_digest = utf8_digest("")
        verifier_workspace_digest = workspace_manifest_digest(oracle_files) if oracle_files else utf8_digest("")
        stats = {
            "changed_file_count": 0,
            "lines_added": 0,
            "lines_deleted": 0,
            "patch_size_bucket": "small",
            "change_surface_class": "none",
        }
        base_tree_digest = utf8_digest("")
    else:
        candidate_workspace_digest = workspace_manifest_digest(bundle.patched_files)
        verifier_files = dict(bundle.patched_files)
        verifier_files.update(oracle_files)
        verifier_workspace_digest = workspace_manifest_digest(verifier_files)
        stats = patch_stats(bundle)
        base_tree_digest = workspace_manifest_digest(bundle.base_files)
    oracle_bundle_digest = workspace_manifest_digest(oracle_files) if oracle_files else utf8_digest("")
    if not oracle_files:
        flags.append(FailureCode.ORACLE_UNAVAILABLE.value)

    runner = VerificationRunner.default(event_sink=InMemoryEventSink())
    run = runner.run(task, candidate, verifier)
    if run.artifact.ref.metadata.keys() & STRIPPED_METADATA_KEYS:
        raise ValueError(f"{FailureCode.LABEL_CONTAMINATION.value}: checklet-visible metadata contained labels")
    if run.hard_verifier_result.artifact_digest != run.artifact.artifact_digest:
        raise ValueError(FailureCode.DIGEST_MISMATCH.value)
    for observation in run.observations:
        if observation.artifact_digest != run.artifact.artifact_digest:
            raise ValueError(FailureCode.DIGEST_MISMATCH.value)
        if observation.checklet_id in CHECKLET_IDS and observation.verdict.value == "error":
            flags.append(FailureCode.CHECKLET_RUN_FAILED.value)
            if "timeout" in observation.summary.lower():
                flags.append(FailureCode.CHECKLET_TIMEOUT.value)

    # Criterion truth is formed without checklet verdicts.
    # Secondary inspector shares domain primitives; evaluation-grade AST inspector does not.
    from .independent_adjudication import independent_adjudicate_artifact_bytes

    adjudications = adjudicate_artifact_bytes(task, run.artifact.content, run.artifact.artifact_digest, metadata) + independent_adjudicate_artifact_bytes(
        task, run.artifact.content, run.artifact.artifact_digest, metadata
    )

    origin = TaskOrigin(manifest.get("task_origin", TaskOrigin.ENGINEERING_FIXTURE.value))
    repository_id = str(manifest.get("repository_id", "engineering://verification_v1"))
    task_family_id = str(manifest.get("task_family_id", task.task_id))
    partition = assign_partition(f"{repository_id}::{task_family_id}")
    producer_payload = dict(manifest.get("producer") or {})
    producer = ProducerProvenance(
        producer_executor_id=str(producer_payload.get("producer_executor_id", "engineering-fixture-generator")),
        producer_model_id=str(producer_payload.get("producer_model_id", "none")),
        producer_scaffold_version=str(producer_payload.get("producer_scaffold_version", "v1.1-fixtures")),
        producer_tool_profile=str(producer_payload.get("producer_tool_profile", "deterministic-fixture")),
        producer_attempt_number=int(producer_payload.get("producer_attempt_number", 1)),
        candidate_source=CandidateSource(producer_payload.get("candidate_source", CandidateSource.ENGINEERING_FIXTURE.value)),
    )
    sampling_payload = dict(manifest.get("sampling") or {})
    sampling = SamplingProvenance(
        sampling_source=str(sampling_payload.get("sampling_source", "engineering_fixture_set")),
        sampling_rule=str(sampling_payload.get("sampling_rule", "checked-in engineering fixtures")),
        selection_timestamp=str(sampling_payload.get("selection_timestamp", utc_now())),
        selection_reason=SelectionReason(sampling_payload.get("selection_reason", SelectionReason.ENGINEERING_CONTROL.value)),
        dataset_kind=str(sampling_payload.get("dataset_kind", "challenge_set" if origin != TaskOrigin.REAL_HISTORICAL else "real_task_core")),
    )
    if origin in {TaskOrigin.CONTROLLED_MUTATION, TaskOrigin.ENGINEERING_FIXTURE} and sampling.dataset_kind == "real_task_core":
        sampling = SamplingProvenance(
            sampling_source=sampling.sampling_source,
            sampling_rule=sampling.sampling_rule,
            selection_timestamp=sampling.selection_timestamp,
            selection_reason=sampling.selection_reason,
            dataset_kind="challenge_set",
        )
    task_contract = task.to_dict()
    record_id = identity_record_id(EXPERIMENT_ID, task.task_id, run.artifact.artifact_digest, oracle_bundle_digest)
    v1_record = run_to_record(run)
    cost_summary = {
        "objective_gate_cost": {"kind": "actual_cost", "amount": 0.0, "currency": "USD"},
        "checklet_costs": [
            dict(observation.estimated_or_actual_cost) for observation in run.observations
        ],
        "hard_verifier_cost": dict(run.hard_verifier_result.cost),
        "counterfactual_expected_cost": {
            "label": "NOT REALIZED / NOT AUTHORIZED",
            "note": "selective verification is off; this is a hypothetical accounting field only",
        },
    }
    latency_summary = {
        "objective_gate_latency_ms": [gate.latency_ms for gate in run.gates],
        "per_checklet_latency_ms": {
            observation.checklet_id: observation.latency_ms for observation in run.observations
        },
        "total_checklet_bundle_latency_ms": sum(observation.latency_ms for observation in run.observations),
        "hard_verifier_latency_ms": run.hard_verifier_result.latency_ms,
        "total_verification_latency_ms": sum(gate.latency_ms for gate in run.gates)
        + sum(observation.latency_ms for observation in run.observations)
        + run.hard_verifier_result.latency_ms,
    }
    if run.final_outcome == HardVerifierOutcome.OUTCOME_UNKNOWN:
        flags.append(FailureCode.HARD_VERIFY_UNKNOWN.value)
    if run.final_outcome == HardVerifierOutcome.INFRASTRUCTURE_ERROR:
        flags.append(FailureCode.HARD_VERIFY_INFRA_ERROR.value)
    return RealTaskEvidenceRecord(
        record_id=record_id,
        schema_version=EVIDENCE_SCHEMA_VERSION,
        experiment_id=EXPERIMENT_ID,
        cohort_id=str(manifest.get("cohort_id", COHORT_ID)),
        experiment_baseline_id=EXPERIMENT_BASELINE_ID,
        partition=partition,
        split_algorithm_version=SPLIT_ALGORITHM_VERSION,
        split_seed=SPLIT_SEED,
        task_id=task.task_id,
        task_family_id=task_family_id,
        task_contract_digest=canonical_digest(task_contract),
        task_type=str(manifest.get("task_type", "engineering_fixture")),
        task_complexity=str(manifest.get("task_complexity", stats["patch_size_bucket"])),
        task_origin=origin,
        repository_id=repository_id,
        repository_group=str(manifest.get("repository_group", "engineering")),
        language=str(manifest.get("language", "python")),
        framework=str(manifest.get("framework", "unittest")),
        base_revision=str(manifest.get("base_revision", "bundle-base")),
        base_tree_digest=base_tree_digest,
        candidate_id=str(artifact_payload["artifact_id"]),
        candidate_lineage_id=str(manifest.get("candidate_lineage_id", task_family_id)),
        candidate_patch_digest=run.artifact.artifact_digest,
        candidate_workspace_digest=candidate_workspace_digest,
        verifier_workspace_digest=verifier_workspace_digest,
        materialized_workspace_digest=candidate_workspace_digest,
        oracle_bundle_digest=oracle_bundle_digest,
        oracle_scope=oracle_scope,
        oracle_limitations=oracle_limitations,
        producer=producer,
        sampling=sampling,
        changed_file_count=int(stats["changed_file_count"]),
        lines_added=int(stats["lines_added"]),
        lines_deleted=int(stats["lines_deleted"]),
        patch_size_bucket=str(stats["patch_size_bucket"]),
        change_surface_class=str(stats["change_surface_class"]),
        gate_results=tuple(gate.to_dict() for gate in run.gates),
        checklet_observations=tuple(observation.to_dict() for observation in run.observations),
        shadow_policy_id=run.shadow_assessment.policy_id,
        shadow_policy_version=run.shadow_assessment.policy_version,
        shadow_assessment=run.shadow_assessment.to_dict(),
        hard_verifier_id=run.hard_verifier_result.verifier_id,
        hard_verifier_version=run.hard_verifier_result.verifier_version,
        hard_verifier_result=run.hard_verifier_result.to_dict(),
        hard_outcome=run.final_outcome,
        criterion_adjudications=adjudications,
        cost_summary=cost_summary,
        latency_summary=latency_summary,
        data_quality_flags=tuple(dict.fromkeys(flags)),
        provenance_refs=(f"run:{run.run_id}", f"ingest:{INGESTION_VERSION}"),
        created_at=utc_now(),
        component_versions=v1_record["component_versions"],
        candidate_bytes_b64=base64.b64encode(run.artifact.content).decode("ascii"),
        oracle_files=oracle_files,
        task_contract=task_contract,
        run_id=run.run_id,
        missing_evidence_links=tuple(missing_links),
        metadata={
            "fixture_id": manifest.get("fixture_id"),
            "ingestion_version": INGESTION_VERSION,
            "v1_run_schema": v1_record.get("schema_version"),
        },
    )


def fixture_to_manifest(fixture: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "fixture_id": fixture.get("fixture_id"),
        "task_origin": TaskOrigin.ENGINEERING_FIXTURE.value,
        "task_family_id": str(fixture.get("task", {}).get("task_id", fixture.get("fixture_id"))),
        "candidate_lineage_id": str(fixture.get("fixture_id")),
        "repository_id": "engineering://verification_v1",
        "repository_group": "engineering",
        "task_type": "engineering_fixture",
        "language": "python",
        "framework": "unittest",
        "base_revision": "bundle-base",
        "oracle_unavailable": bool(fixture.get("oracle_unavailable")),
        "hard_command": fixture.get("hard_command"),
        "reference_files": dict(fixture.get("reference_files") or {}),
        "hard_timeout_seconds": fixture.get("hard_timeout_seconds", 30.0),
        "oracle_scope": "unit_reference_tests",
        "oracle_limitations": "engineering-fixture reference tests; not a universal correctness proof",
        "task": fixture["task"],
        "artifact": fixture["artifact"],
        "producer": {
            "producer_executor_id": "engineering-fixture-generator",
            "producer_model_id": "none",
            "producer_scaffold_version": "v1.1-fixtures",
            "producer_tool_profile": "deterministic-fixture",
            "producer_attempt_number": 1,
            "candidate_source": CandidateSource.ENGINEERING_FIXTURE.value,
        },
        "sampling": {
            "sampling_source": "evals/verification_v1/engineering_fixture_set.json",
            "sampling_rule": "checked-in VS-V1.1 engineering fixtures",
            "selection_timestamp": utc_now(),
            "selection_reason": SelectionReason.ENGINEERING_CONTROL.value,
            "dataset_kind": "challenge_set",
        },
    }
