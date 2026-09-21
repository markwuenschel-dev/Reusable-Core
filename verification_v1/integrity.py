"""Fail-closed V1.2 dataset integrity: identity, digests, duplicates, leakage."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .baseline import collect_baseline
from .evidence import (
    CHECKLET_IDS,
    CRITERION_IDS,
    EVIDENCE_SCHEMA_VERSION,
    EXPERIMENT_BASELINE_ID,
    FORBIDDEN_CHECKLET_CONTEXT_KEYS,
    KNOWN_CHECKLET_VERSION,
    KNOWN_HARD_VERIFIER_IDS,
    KNOWN_SHADOW_POLICY_ID,
    KNOWN_SHADOW_POLICY_VERSION,
    CriterionLabel,
    FailureCode,
    Partition,
    RealTaskEvidenceRecord,
    TaskOrigin,
    parse_iso8601,
    workspace_manifest_digest,
)
from .splits import SPLIT_ALGORITHM_VERSION, SPLIT_SEED, leakage_failures

DATASET_SCHEMA_VERSION = "verification-v1.2-dataset/1.1.0"
MINIMUM_SHA256_HEX = 64

REQUIRED_IDENTITY_FIELDS = (
    "record_id",
    "experiment_id",
    "cohort_id",
    "experiment_baseline_id",
    "task_id",
    "task_family_id",
    "task_contract_digest",
    "candidate_id",
    "candidate_lineage_id",
    "candidate_patch_digest",
    "candidate_workspace_digest",
    "oracle_bundle_digest",
    "base_revision",
)


def _hex_digest(value: str) -> bool:
    return len(value) == MINIMUM_SHA256_HEX and all(char in "0123456789abcdef" for char in value)


def _timestamp_errors(value: str, now: datetime | None = None) -> list[FailureCode]:
    try:
        parsed = parse_iso8601(value)
    except ValueError:
        return [FailureCode.TIMESTAMP_INVALID]
    clock = now or datetime.now(timezone.utc)
    if parsed.year < 2020:
        return [FailureCode.TIMESTAMP_INVALID]
    if parsed > clock.replace(microsecond=0) and (parsed - clock).total_seconds() > 86400:
        return [FailureCode.TIMESTAMP_INVALID]
    return []


def validate_record(record: RealTaskEvidenceRecord, *, live_baseline: Mapping[str, Any] | None = None) -> list[FailureCode]:
    errors: list[FailureCode] = []
    payload = record.to_dict()
    for field in REQUIRED_IDENTITY_FIELDS:
        if not str(payload.get(field, "")).strip():
            errors.append(FailureCode.MISSING_IDENTITY)
            break
    if record.schema_version != EVIDENCE_SCHEMA_VERSION:
        errors.append(FailureCode.MISSING_IDENTITY)
    if record.experiment_baseline_id != EXPERIMENT_BASELINE_ID:
        errors.append(FailureCode.BASELINE_VERSION_UNKNOWN)
    baseline = live_baseline or collect_baseline()
    if record.experiment_baseline_id != baseline.get("experiment_baseline_id"):
        errors.append(FailureCode.BASELINE_VERSION_UNKNOWN)
    if record.task_origin not in TaskOrigin:
        errors.append(FailureCode.UNKNOWN_TASK_ORIGIN)
    if record.partition not in Partition:
        errors.append(FailureCode.UNKNOWN_PARTITION)
    if record.split_algorithm_version != SPLIT_ALGORITHM_VERSION or record.split_seed != SPLIT_SEED:
        errors.append(FailureCode.PARTITION_LEAKAGE)
    for digest in (
        record.task_contract_digest,
        record.candidate_patch_digest,
        record.candidate_workspace_digest,
        record.oracle_bundle_digest,
        record.base_tree_digest,
        record.verifier_workspace_digest,
        record.materialized_workspace_digest,
    ):
        if digest and not _hex_digest(digest):
            errors.append(FailureCode.DIGEST_MISMATCH)
            break
    if record.candidate_workspace_digest != record.materialized_workspace_digest:
        errors.append(FailureCode.DIGEST_MISMATCH)
    shadow_digest = str(record.shadow_assessment.get("artifact_digest", ""))
    hard_digest = str(record.hard_verifier_result.get("artifact_digest", ""))
    observation_digests = {str(item.get("artifact_digest", "")) for item in record.checklet_observations}
    adjudication_digests = {item.artifact_digest for item in record.criterion_adjudications}
    expected = record.candidate_patch_digest
    if shadow_digest != expected or hard_digest != expected:
        errors.append(FailureCode.DIGEST_MISMATCH)
    if observation_digests and observation_digests != {expected}:
        errors.append(FailureCode.DIGEST_MISMATCH)
    if adjudication_digests and adjudication_digests != {expected}:
        errors.append(FailureCode.DIGEST_MISMATCH)
    if record.oracle_files and workspace_manifest_digest(dict(record.oracle_files)) != record.oracle_bundle_digest:
        errors.append(FailureCode.DIGEST_MISMATCH)
    candidate_paths = set()
    for observation in record.checklet_observations:
        metadata = observation.get("metadata") or {}
        derived = metadata.get("derived_changed_paths") or metadata.get("derived_test_paths") or []
        candidate_paths.update(str(path) for path in derived)
    oracle_paths = {str(path).replace("\\", "/") for path in dict(record.oracle_files)}
    if oracle_paths & {path.replace("\\", "/") for path in candidate_paths}:
        errors.append(FailureCode.ORACLE_LEAK)
    # set() over a Mapping yields its keys, so this compared oracle file paths
    # against metadata key names and could essentially never fire. An oracle path
    # leaks through the task contract as a metadata *value*, so check both.
    task_metadata = record.task_contract.get("metadata")
    if isinstance(task_metadata, Mapping):
        metadata_surface = {str(key).replace("\\", "/") for key in task_metadata}
        metadata_surface.update(
            str(value).replace("\\", "/") for value in task_metadata.values()
        )
        if oracle_paths & metadata_surface:
            errors.append(FailureCode.ORACLE_LEAK)
    checklet_versions = {
        str(item.get("checklet_id")): str(item.get("checklet_version"))
        for item in record.checklet_observations
    }
    if checklet_versions and set(checklet_versions) - set(CHECKLET_IDS):
        errors.append(FailureCode.CHECKLET_RUN_FAILED)
    if any(version != KNOWN_CHECKLET_VERSION for version in checklet_versions.values()):
        errors.append(FailureCode.BASELINE_VERSION_UNKNOWN)
    if record.shadow_policy_id != KNOWN_SHADOW_POLICY_ID or record.shadow_policy_version != KNOWN_SHADOW_POLICY_VERSION:
        errors.append(FailureCode.BASELINE_VERSION_UNKNOWN)
    known_hard_version = KNOWN_HARD_VERIFIER_IDS.get(record.hard_verifier_id)
    if known_hard_version is None:
        errors.append(FailureCode.BASELINE_VERSION_UNKNOWN)
    elif record.hard_verifier_id != "recorded-hard-verifier" and record.hard_verifier_version != known_hard_version:
        errors.append(FailureCode.BASELINE_VERSION_UNKNOWN)
    # A try/except around `record.hard_outcome` stood here. Attribute access on a
    # set dataclass field cannot raise, and the line below dereferences .value
    # outside the try anyway, so the guard could never fire.
    if record.hard_outcome.value == "outcome_unknown":
        errors.append(FailureCode.HARD_VERIFY_UNKNOWN)
    if record.hard_outcome.value == "infrastructure_error":
        errors.append(FailureCode.HARD_VERIFY_INFRA_ERROR)
    if not record.producer.producer_executor_id or not record.producer.producer_model_id:
        errors.append(FailureCode.PRODUCER_PROVENANCE_MISSING)
    errors.extend(_timestamp_errors(record.created_at))
    if record.criterion_adjudications:
        by_adjudicator: dict[tuple[str, str], set[CriterionLabel]] = {}
        for item in record.criterion_adjudications:
            if item.criterion_id != CRITERION_IDS.get(item.checklet_id):
                errors.append(FailureCode.CRITERION_LABEL_INCONSISTENT)
            if item.artifact_digest != expected:
                errors.append(FailureCode.DIGEST_MISMATCH)
            by_adjudicator.setdefault((item.checklet_id, item.adjudicator_id), set()).add(item.label)
        for labels in by_adjudicator.values():
            if len(labels) > 1:
                errors.append(FailureCode.CRITERION_ADJUDICATION_CONFLICT)
    else:
        errors.append(FailureCode.CRITERION_ADJUDICATION_MISSING)
    if record.invalidated:
        errors.append(FailureCode.RECORD_INVALIDATED)
    # HARD_VERIFY_UNKNOWN / INFRA_ERROR are recorded outcomes, not record-invalid unless combined
    # with missing identity. Keep them as quality flags; they must not enter determinate metrics,
    # but they may enter the dataset. Strip them from blocking errors.
    blocking = [
        code
        for code in errors
        if code
        not in {
            FailureCode.HARD_VERIFY_UNKNOWN,
            FailureCode.HARD_VERIFY_INFRA_ERROR,
            FailureCode.RECORD_INVALIDATED,
        }
    ]
    # record_flags was assembled here and discarded by the return below;
    # validate_record_with_quality re-derives the same codes independently.
    return blocking


def validate_record_with_quality(
    record: RealTaskEvidenceRecord, *, live_baseline: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    blocking = validate_record(record, live_baseline=live_baseline)
    quality: list[str] = list(record.data_quality_flags)
    if record.hard_outcome.value == "outcome_unknown" and FailureCode.HARD_VERIFY_UNKNOWN.value not in quality:
        quality.append(FailureCode.HARD_VERIFY_UNKNOWN.value)
    if record.hard_outcome.value == "infrastructure_error" and FailureCode.HARD_VERIFY_INFRA_ERROR.value not in quality:
        quality.append(FailureCode.HARD_VERIFY_INFRA_ERROR.value)
    if record.invalidated and FailureCode.RECORD_INVALIDATED.value not in quality:
        quality.append(FailureCode.RECORD_INVALIDATED.value)
    return {"blocking": [code.value for code in blocking], "quality": quality, "ok": not blocking and not record.invalidated}


def exact_artifact_key(record: RealTaskEvidenceRecord) -> tuple[str, str, str]:
    return (record.task_contract_digest, record.candidate_patch_digest, record.oracle_bundle_digest)


def duplicate_failures(records: Sequence[RealTaskEvidenceRecord]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    seen_ids: dict[str, str] = {}
    seen_artifacts: dict[tuple[str, str, str], str] = {}
    seen_base_patch: dict[tuple[str, str], str] = {}
    for record in records:
        if record.record_id in seen_ids:
            failures.append(
                {
                    "code": FailureCode.DATASET_DUPLICATE.value,
                    "reason": "duplicate record_id",
                    "record_id": record.record_id,
                }
            )
        seen_ids[record.record_id] = record.record_id
        key = exact_artifact_key(record)
        if key in seen_artifacts:
            failures.append(
                {
                    "code": FailureCode.DATASET_DUPLICATE.value,
                    "reason": "duplicate exact artifact entry",
                    "record_id": record.record_id,
                    "other_record_id": seen_artifacts[key],
                }
            )
        seen_artifacts[key] = record.record_id
        base_key = (record.base_revision, record.candidate_patch_digest)
        if base_key in seen_base_patch:
            failures.append(
                {
                    "code": FailureCode.DATASET_DUPLICATE.value,
                    "reason": "duplicate base revision + patch",
                    "record_id": record.record_id,
                    "other_record_id": seen_base_patch[base_key],
                }
            )
        seen_base_patch[base_key] = record.record_id
    return failures


def near_duplicate_groups(records: Sequence[RealTaskEvidenceRecord]) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for record in records:
        normalized = " ".join(str(record.task_contract.get("description", "")).lower().split())
        family = record.candidate_lineage_id
        groups.setdefault(f"lineage:{family}", []).append(record.record_id)
        if normalized:
            groups.setdefault(f"task_text:{normalized}", []).append(record.record_id)
        groups.setdefault(f"patch:{record.candidate_patch_digest}", []).append(record.record_id)
    return [
        {"key": key, "record_ids": ids}
        for key, ids in groups.items()
        if len(set(ids)) > 1
    ]


def checklet_context_is_clean(metadata: Mapping[str, Any]) -> list[FailureCode]:
    leaks = sorted(key for key in metadata if key in FORBIDDEN_CHECKLET_CONTEXT_KEYS)
    if leaks:
        return [FailureCode.LABEL_CONTAMINATION]
    return []


def validate_dataset_records(records: Sequence[RealTaskEvidenceRecord]) -> dict[str, Any]:
    blocking: list[dict[str, Any]] = []
    quality: list[dict[str, Any]] = []
    failing_records: list[RealTaskEvidenceRecord] = []
    # Collected once for the whole dataset. validate_record fell back to
    # collect_baseline() per record, and that shells out to `git show` for every
    # frozen file -- so an N-record dataset paid 11*N subprocesses to compare one
    # constant it could have been handed.
    live_baseline = collect_baseline()
    for record in records:
        result = validate_record_with_quality(record, live_baseline=live_baseline)
        if result["blocking"]:
            blocking.append({"record_id": record.record_id, "codes": result["blocking"]})
            failing_records.append(record)
        if result["quality"]:
            quality.append({"record_id": record.record_id, "codes": result["quality"]})
    duplicates = duplicate_failures(records)
    leakage = leakage_failures(records)
    if duplicates:
        blocking.append({"record_id": "*", "codes": [FailureCode.DATASET_DUPLICATE.value], "details": duplicates})
    if leakage:
        blocking.append({"record_id": "*", "codes": [FailureCode.PARTITION_LEAKAGE.value], "details": leakage})
    return {
        "ok": not blocking,
        "blocking": blocking,
        "quality": quality,
        "near_duplicates": near_duplicate_groups(records),
        "n_records": len(records),
        # Count what passed. Subtracting a set of failing ids de-duplicated two
        # distinct records that shared an id, handing one of them back as valid,
        # and dataset-level rows (record_id "*") were excluded from the
        # subtraction entirely rather than being reported.
        "n_valid": len(records) - len(failing_records),
        "n_dataset_level_failures": sum(1 for item in blocking if item["record_id"] == "*"),
    }
