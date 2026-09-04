"""Immutable V1.2 dataset container. Invalid records never enter analysis."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import jsonable, utc_now
from .evidence import (
    COHORT_ID,
    EXPERIMENT_BASELINE_ID,
    EXPERIMENT_ID,
    FailureCode,
    RealTaskEvidenceRecord,
)
from .integrity import DATASET_SCHEMA_VERSION, validate_dataset_records, validate_record
from .splits import SPLIT_ALGORITHM_VERSION, SPLIT_SEED

DATASET_ID = "vs-v1.2-real-task-evidence"
DATASET_VERSION = "1.2.0"


@dataclass(frozen=True)
class EvidenceDataset:
    dataset_id: str
    dataset_version: str
    schema_version: str
    experiment_id: str
    cohort_id: str
    experiment_baseline_id: str
    split_algorithm_version: str
    split_seed: str
    created_at: str
    changelog: tuple[dict[str, Any], ...]
    records: tuple[RealTaskEvidenceRecord, ...]
    frozen: bool = False
    holdout_state: str = "sealed"
    calibration_state: str = "sealed"
    unseal_receipt: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EvidenceDataset":
        records = tuple(RealTaskEvidenceRecord.from_dict(item) for item in payload.get("records", []))
        return cls(
            dataset_id=str(payload.get("dataset_id", DATASET_ID)),
            dataset_version=str(payload.get("dataset_version", DATASET_VERSION)),
            schema_version=str(payload.get("schema_version", DATASET_SCHEMA_VERSION)),
            experiment_id=str(payload.get("experiment_id", EXPERIMENT_ID)),
            cohort_id=str(payload.get("cohort_id", COHORT_ID)),
            experiment_baseline_id=str(payload.get("experiment_baseline_id", EXPERIMENT_BASELINE_ID)),
            split_algorithm_version=str(payload.get("split_algorithm_version", SPLIT_ALGORITHM_VERSION)),
            split_seed=str(payload.get("split_seed", SPLIT_SEED)),
            created_at=str(payload.get("created_at", utc_now())),
            changelog=tuple(dict(item) for item in payload.get("changelog", [])),
            records=records,
            frozen=bool(payload.get("frozen", False)),
            holdout_state=str(payload.get("holdout_state", "sealed")),
            calibration_state=str(payload.get("calibration_state", "sealed")),
            unseal_receipt=dict(payload["unseal_receipt"]) if payload.get("unseal_receipt") else None,
        )

    def valid_records(self) -> tuple[RealTaskEvidenceRecord, ...]:
        return tuple(record for record in self.records if not record.invalidated and not validate_record(record))


def empty_dataset() -> EvidenceDataset:
    return EvidenceDataset(
        dataset_id=DATASET_ID,
        dataset_version=DATASET_VERSION,
        schema_version=DATASET_SCHEMA_VERSION,
        experiment_id=EXPERIMENT_ID,
        cohort_id=COHORT_ID,
        experiment_baseline_id=EXPERIMENT_BASELINE_ID,
        split_algorithm_version=SPLIT_ALGORITHM_VERSION,
        split_seed=SPLIT_SEED,
        created_at=utc_now(),
        changelog=(),
        records=(),
        frozen=False,
        holdout_state="sealed",
        calibration_state="sealed",
        unseal_receipt=None,
    )


def load_dataset(path: Path) -> EvidenceDataset:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("dataset must be a JSON object")
    return EvidenceDataset.from_dict(payload)


def write_dataset(dataset: EvidenceDataset, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dataset.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def append_records(
    dataset: EvidenceDataset,
    records: Sequence[RealTaskEvidenceRecord],
    *,
    note: str,
) -> EvidenceDataset:
    if dataset.frozen:
        next_version = _bump_version(dataset.dataset_version)
        changelog = dataset.changelog + (
            {
                "at": utc_now(),
                "action": "successor_dataset",
                "note": "frozen dataset is immutable; creating a successor version",
                "from_version": dataset.dataset_version,
                "to_version": next_version,
            },
        )
        return append_records(
            EvidenceDataset(
                dataset_id=dataset.dataset_id,
                dataset_version=next_version,
                schema_version=dataset.schema_version,
                experiment_id=dataset.experiment_id,
                cohort_id=dataset.cohort_id,
                experiment_baseline_id=dataset.experiment_baseline_id,
                split_algorithm_version=dataset.split_algorithm_version,
                split_seed=dataset.split_seed,
                created_at=utc_now(),
                changelog=changelog,
                records=dataset.records,
                frozen=False,
                holdout_state=dataset.holdout_state,
                calibration_state=dataset.calibration_state,
                unseal_receipt=dataset.unseal_receipt,
            ),
            records,
            note=note,
        )
    merged = list(dataset.records)
    added: list[str] = []
    for record in records:
        blocking = validate_record(record)
        if blocking:
            raise ValueError(
                f"{FailureCode.REPORT_INTEGRITY_FAILURE.value}: record {record.record_id} blocked: "
                + ",".join(code.value for code in blocking)
            )
        merged.append(record)
        added.append(record.record_id)
    integrity = validate_dataset_records(merged)
    if not integrity["ok"]:
        raise ValueError(f"{FailureCode.DATASET_DUPLICATE.value}: {integrity['blocking']}")
    return EvidenceDataset(
        dataset_id=dataset.dataset_id,
        dataset_version=dataset.dataset_version,
        schema_version=dataset.schema_version,
        experiment_id=dataset.experiment_id,
        cohort_id=dataset.cohort_id,
        experiment_baseline_id=dataset.experiment_baseline_id,
        split_algorithm_version=dataset.split_algorithm_version,
        split_seed=dataset.split_seed,
        created_at=dataset.created_at,
        changelog=dataset.changelog
        + ({"at": utc_now(), "action": "append", "added": added, "note": note},),
        records=tuple(merged),
        frozen=False,
        holdout_state=dataset.holdout_state,
        calibration_state=dataset.calibration_state,
        unseal_receipt=dataset.unseal_receipt,
    )


def invalidate_record(dataset: EvidenceDataset, record_id: str, reason: str) -> EvidenceDataset:
    found = False
    updated: list[RealTaskEvidenceRecord] = []
    for record in dataset.records:
        if record.record_id != record_id:
            updated.append(record)
            continue
        found = True
        payload = record.to_dict()
        payload["invalidated"] = True
        payload["invalidation_reason"] = reason
        updated.append(RealTaskEvidenceRecord.from_dict(payload))
    if not found:
        raise KeyError(record_id)
    next_version = _bump_version(dataset.dataset_version) if dataset.frozen else dataset.dataset_version
    return EvidenceDataset(
        dataset_id=dataset.dataset_id,
        dataset_version=next_version,
        schema_version=dataset.schema_version,
        experiment_id=dataset.experiment_id,
        cohort_id=dataset.cohort_id,
        experiment_baseline_id=dataset.experiment_baseline_id,
        split_algorithm_version=dataset.split_algorithm_version,
        split_seed=dataset.split_seed,
        created_at=dataset.created_at,
        changelog=dataset.changelog
        + (
            {
                "at": utc_now(),
                "action": "invalidate",
                "record_id": record_id,
                "reason": reason,
                "from_version": dataset.dataset_version,
                "to_version": next_version,
            },
        ),
        records=tuple(updated),
        frozen=False,
        holdout_state=dataset.holdout_state,
        calibration_state=dataset.calibration_state,
        unseal_receipt=dataset.unseal_receipt,
    )


def freeze_dataset(dataset: EvidenceDataset) -> EvidenceDataset:
    return EvidenceDataset(
        dataset_id=dataset.dataset_id,
        dataset_version=dataset.dataset_version,
        schema_version=dataset.schema_version,
        experiment_id=dataset.experiment_id,
        cohort_id=dataset.cohort_id,
        experiment_baseline_id=dataset.experiment_baseline_id,
        split_algorithm_version=dataset.split_algorithm_version,
        split_seed=dataset.split_seed,
        created_at=dataset.created_at,
        changelog=dataset.changelog + ({"at": utc_now(), "action": "freeze"},),
        records=dataset.records,
        frozen=True,
        holdout_state=dataset.holdout_state,
        calibration_state=dataset.calibration_state,
        unseal_receipt=dataset.unseal_receipt,
    )


def persist_partition_unseal(
    dataset: EvidenceDataset,
    receipt: Mapping[str, Any],
    *,
    target: str,
) -> EvidenceDataset:
    if target not in {"holdout", "calibration"}:
        raise ValueError(f"unknown unseal target: {target}")
    holdout_state = "final_unsealed" if target == "holdout" else dataset.holdout_state
    calibration_state = "unsealed" if target == "calibration" else dataset.calibration_state
    return EvidenceDataset(
        dataset_id=dataset.dataset_id,
        dataset_version=dataset.dataset_version,
        schema_version=dataset.schema_version,
        experiment_id=dataset.experiment_id,
        cohort_id=dataset.cohort_id,
        experiment_baseline_id=dataset.experiment_baseline_id,
        split_algorithm_version=dataset.split_algorithm_version,
        split_seed=dataset.split_seed,
        created_at=dataset.created_at,
        changelog=dataset.changelog
        + (
            {
                "at": utc_now(),
                "action": "unseal",
                "target": target,
                "receipt": dict(receipt),
            },
        ),
        records=dataset.records,
        frozen=dataset.frozen,
        holdout_state=holdout_state,
        calibration_state=calibration_state,
        unseal_receipt=dict(receipt),
    )


def _bump_version(version: str) -> str:
    parts = version.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return version + ".1"
    return f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
