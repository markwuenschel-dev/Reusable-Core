"""Grouped deterministic dataset partitions. Lineage never crosses a split."""

from __future__ import annotations

from enum import Enum
from hashlib import sha256
from typing import Any, Iterable, Mapping, Sequence

from .contracts import utc_now
from .evidence import FailureCode, Partition, RealTaskEvidenceRecord

SPLIT_ALGORITHM_VERSION = "grouped-sha256-v1"
SPLIT_SEED = "vs-v1.2-split-seed-001"
HOLDOUT_TUNING_PURPOSES = frozenset(
    {
        "checklet_tuning",
        "prompt_tuning",
        "threshold_selection",
        "feature_selection",
        "policy_change",
        "criterion_redefinition",
    }
)
OPERATIONAL_PARTITIONS = frozenset({Partition.DEVELOPMENT, Partition.POLICY_SELECTION})
SEALED_PARTITIONS = frozenset({Partition.CALIBRATION_RESERVED, Partition.HOLDOUT})
TUNING_PARTITIONS = frozenset({Partition.DEVELOPMENT})
UNSEAL_SCHEMA_VERSION = "verification-v1.2-unseal/1.0.0"
DECISION_GATE_VERSION = "v12a-1.0.0"


class AnalysisScope(str, Enum):
    OPERATIONAL = "operational"
    POLICY_SELECTION = "policy-selection"
    CALIBRATION = "calibration"
    FINAL_HOLDOUT = "final-holdout"

# Inclusive ranges over hash % 100.
_PARTITION_CUTS: tuple[tuple[Partition, int, int], ...] = (
    (Partition.DEVELOPMENT, 0, 39),
    (Partition.POLICY_SELECTION, 40, 59),
    (Partition.CALIBRATION_RESERVED, 60, 79),
    (Partition.HOLDOUT, 80, 99),
)


class HoldoutAccessError(PermissionError):
    """Development/tuning utilities may not read holdout outcomes."""


def group_id(repository_id: str, task_family_id: str) -> str:
    return f"{repository_id}::{task_family_id}"


def assign_partition(
    group: str,
    *,
    seed: str = SPLIT_SEED,
    algorithm_version: str = SPLIT_ALGORITHM_VERSION,
) -> Partition:
    material = f"{algorithm_version}:{seed}:{group}".encode("utf-8")
    bucket = int(sha256(material).hexdigest()[:8], 16) % 100
    for partition, low, high in _PARTITION_CUTS:
        if low <= bucket <= high:
            return partition
    return Partition.HOLDOUT


def assign_record_partition(record: RealTaskEvidenceRecord) -> Partition:
    return assign_partition(
        record.group_id,
        seed=record.split_seed,
        algorithm_version=record.split_algorithm_version,
    )


def partition_by_group(records: Sequence[RealTaskEvidenceRecord]) -> dict[str, set[Partition]]:
    grouped: dict[str, set[Partition]] = {}
    for record in records:
        grouped.setdefault(record.group_id, set()).add(record.partition)
        grouped.setdefault(record.candidate_lineage_id, set()).add(record.partition)
    return grouped


def leakage_failures(records: Sequence[RealTaskEvidenceRecord]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for key, partitions in partition_by_group(records).items():
        if len(partitions) > 1:
            failures.append(
                {
                    "code": FailureCode.PARTITION_LEAKAGE.value,
                    "key": key,
                    "partitions": ",".join(sorted(item.value for item in partitions)),
                }
            )
    return failures


def assert_partition_allowed(
    records: Iterable[RealTaskEvidenceRecord],
    purpose: str,
    allowed: Iterable[Partition] | None = None,
) -> None:
    if purpose in HOLDOUT_TUNING_PURPOSES:
        allowed_set = set(allowed or TUNING_PARTITIONS)
    elif purpose == "v12_analysis":
        allowed_set = set(allowed or OPERATIONAL_PARTITIONS)
    else:
        # Fail closed. Returning here granted every partition, including the
        # sealed holdout, to any purpose string the vocabulary does not know --
        # a typo such as "threshold_tuning" for "threshold_selection" was enough.
        raise HoldoutAccessError(
            f"{FailureCode.HOLDOUT_ACCESS.value}: unrecognised purpose {purpose!r}; "
            f"known purposes are {sorted(HOLDOUT_TUNING_PURPOSES | {'v12_analysis'})}"
        )
    blocked = [record.record_id for record in records if record.partition not in allowed_set]
    if blocked:
        raise HoldoutAccessError(
            f"{FailureCode.HOLDOUT_ACCESS.value}: {purpose} cannot use {blocked}"
        )


def valid_unseal_receipt(receipt: Mapping[str, Any] | None) -> bool:
    if not isinstance(receipt, Mapping):
        return False
    required = (
        "baseline_content_address",
        "analysis_code_version",
        "checklet_implementation_hash",
        "shadow_policy",
        "unsealed_at",
    )
    return (
        receipt.get("schema_version") == UNSEAL_SCHEMA_VERSION
        and receipt.get("one_way") is True
        and all(receipt.get(key) for key in required)
    )


def build_unseal_receipt(
    *,
    baseline_content_address: str,
    analysis_code_version: str,
    checklet_implementation_hash: str,
    shadow_policy: str,
    git_commit: str = "",
    baseline_id: str = "vs-v1.1-baseline-001",
) -> dict[str, object]:
    return {
        "schema_version": UNSEAL_SCHEMA_VERSION,
        "one_way": True,
        "baseline_content_address": baseline_content_address,
        "analysis_code_version": analysis_code_version,
        "checklet_implementation_hash": checklet_implementation_hash,
        "shadow_policy": shadow_policy,
        "decision_gate_version": DECISION_GATE_VERSION,
        "git_commit": git_commit,
        "baseline_id": baseline_id,
        "unsealed_at": utc_now(),
    }


def partitions_for_scope(
    scope: AnalysisScope | str,
    unseal_receipt: Mapping[str, Any] | None = None,
) -> frozenset[Partition]:
    resolved = AnalysisScope(scope)
    if resolved is AnalysisScope.OPERATIONAL:
        return OPERATIONAL_PARTITIONS
    if resolved is AnalysisScope.POLICY_SELECTION:
        return OPERATIONAL_PARTITIONS
    if resolved is AnalysisScope.FINAL_HOLDOUT:
        if not valid_unseal_receipt(unseal_receipt):
            raise HoldoutAccessError(
                f"{FailureCode.HOLDOUT_ACCESS.value}: holdout is sealed until finalize-holdout"
            )
        return OPERATIONAL_PARTITIONS | {Partition.HOLDOUT}
    if resolved is AnalysisScope.CALIBRATION:
        if not valid_unseal_receipt(unseal_receipt):
            raise HoldoutAccessError(
                f"{FailureCode.HOLDOUT_ACCESS.value}: calibration_reserved is sealed until unseal-calibration"
            )
        return frozenset({Partition.CALIBRATION_RESERVED})
    raise ValueError(f"unknown analysis scope: {scope}")


def filter_records_for_scope(
    records: Sequence[RealTaskEvidenceRecord],
    scope: AnalysisScope | str = AnalysisScope.OPERATIONAL,
    unseal_receipt: Mapping[str, Any] | None = None,
) -> tuple[RealTaskEvidenceRecord, ...]:
    allowed = partitions_for_scope(scope, unseal_receipt)
    return tuple(record for record in records if record.partition in allowed)


def sealed_partition_counts(records: Sequence[RealTaskEvidenceRecord]) -> dict[str, int]:
    counts = {partition.value: 0 for partition in SEALED_PARTITIONS}
    for record in records:
        if record.partition in SEALED_PARTITIONS:
            counts[record.partition.value] += 1
    return counts


# freeze_split_metadata removed (INTEG-024): no call site anywhere.
