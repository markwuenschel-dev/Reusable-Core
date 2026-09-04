"""Dual-layer V1.2 analysis: criterion truth and hard-outcome prediction stay separate."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from statistics import mean
from typing import Any, Mapping, Sequence

from .contracts import CheckletVerdict, CounterfactualClass, HardVerifierOutcome, Severity, ShadowAction
from .evidence import (
    CHECKLET_IDS,
    CriterionLabel,
    FailureCode,
    Partition,
    RealTaskEvidenceRecord,
    TaskOrigin,
)
from .independent_adjudication import EVALUATION_GRADE_ADJUDICATOR_IDS, SECONDARY_ADJUDICATOR_ID
from .integrity import validate_dataset_records
from .splits import (
    HOLDOUT_TUNING_PURPOSES,
    OPERATIONAL_PARTITIONS,
    AnalysisScope,
    HoldoutAccessError,
    assert_partition_allowed,
    filter_records_for_scope,
    sealed_partition_counts,
)

ANALYSIS_SCHEMA_VERSION = "verification-v1.2-analysis/1.1.0"
MINIMUM_DESCRIPTIVE_N = 10
WILSON_Z = 1.96


@dataclass(frozen=True)
class DecisionGateConfig:
    """Research-heuristic V1.2 decision thresholds. Not a production safety certificate."""

    decision_gate_id: str = "v12-decision-gate-1.1"
    minimum_real_determinate_n: int = 50
    minimum_repository_count: int = 2
    minimum_task_family_count: int = 2
    minimum_patch_size_count: int = 2
    criterion_precision_floor: float = 0.6
    criterion_recall_floor: float = 0.5
    kind: str = "research heuristic"


DEFAULT_DECISION_GATE = DecisionGateConfig()
MINIMUM_REAL_DETERMINATE_FOR_V2 = DEFAULT_DECISION_GATE.minimum_real_determinate_n
MATERIAL_FINDING_SEVERITIES = {Severity.MEDIUM.value, Severity.HIGH.value, Severity.CRITICAL.value}

V2_PROCEED = "PROCEED_TO_V2_RESEARCH"
V2_REWORK = "REWORK_CHECKLET_SET"
V2_MORE_DATA = "COLLECT_MORE_V1_2_DATA"
V2_DIAGNOSTIC = "DIAGNOSTIC_VALUE_ONLY"
V2_STOP = "STOP_SELECTIVE_VERIFICATION_PATH"


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def wilson_interval(successes: int, n: int, z: float = WILSON_Z) -> dict[str, Any]:
    if n <= 0:
        return {"method": "wilson_95", "lower": None, "upper": None, "n": 0, "successes": successes, "rate": None}
    p = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    margin = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n) / denom
    return {
        "method": "wilson_95",
        "lower": max(0.0, center - margin),
        "upper": min(1.0, center + margin),
        "n": n,
        "successes": successes,
        "rate": p,
        "display": f"{successes} / {n}",
    }


def cohens_kappa(left: Sequence[str], right: Sequence[str]) -> float | None:
    if len(left) != len(right) or not left:
        return None
    n = len(left)
    agreement = sum(a == b for a, b in zip(left, right)) / n
    categories = sorted(set(left) | set(right))
    pe = 0.0
    for category in categories:
        pe += (sum(item == category for item in left) / n) * (sum(item == category for item in right) / n)
    if pe == 1.0:
        return 1.0 if agreement == 1.0 else 0.0
    return (agreement - pe) / (1.0 - pe)


def phi_coefficient(n11: int, n10: int, n01: int, n00: int) -> float | None:
    denom = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    if denom == 0:
        return None
    return ((n11 * n00) - (n10 * n01)) / denom


def _descriptive(n: int) -> bool:
    return n < MINIMUM_DESCRIPTIVE_N


def analysis_records(records: Sequence[RealTaskEvidenceRecord]) -> tuple[RealTaskEvidenceRecord, ...]:
    integrity = validate_dataset_records(records)
    if not integrity["ok"]:
        raise ValueError(f"{FailureCode.REPORT_INTEGRITY_FAILURE.value}: {integrity['blocking']}")
    return tuple(record for record in records if not record.invalidated)


def _is_finding(observation: Mapping[str, Any] | None) -> bool:
    return bool(observation) and observation.get("verdict") == CheckletVerdict.FINDING.value


def _material_finding(observation: Mapping[str, Any] | None) -> bool:
    if not _is_finding(observation):
        return False
    return str(observation.get("severity")) in MATERIAL_FINDING_SEVERITIES


def _gates_pass(record: RealTaskEvidenceRecord) -> bool:
    if not record.gate_results:
        return False
    return all(item.get("status") == "pass" for item in record.gate_results)


def _low_risk(record: RealTaskEvidenceRecord) -> bool:
    if not _gates_pass(record):
        return False
    for observation in record.checklet_observations:
        verdict = observation.get("verdict")
        if verdict in {CheckletVerdict.ABSTAIN.value, CheckletVerdict.ERROR.value}:
            return False
        if _material_finding(observation):
            return False
    return True


def criterion_metrics(
    records: Sequence[RealTaskEvidenceRecord],
    checklet_id: str,
    *,
    adjudicator_ids: frozenset[str] | set[str] | None = None,
) -> dict[str, Any]:
    applicable: list[RealTaskEvidenceRecord] = []
    adjudicated: list[RealTaskEvidenceRecord] = []
    tp = fp = tn = fn = 0
    abstain = error = indeterminate = not_applicable = 0
    unique_catches = 0
    severity_rows: dict[str, dict[str, int]] = {}
    for record in records:
        label = record.primary_criterion_label(checklet_id, adjudicator_ids=adjudicator_ids)
        observation = record.observation_for(checklet_id)
        if label == CriterionLabel.NOT_APPLICABLE:
            not_applicable += 1
            continue
        applicable.append(record)
        if label is None or label == CriterionLabel.INDETERMINATE:
            indeterminate += 1
            continue
        adjudicated.append(record)
        predicted_finding = _is_finding(observation)
        verdict = observation.get("verdict") if observation else None
        if verdict == CheckletVerdict.ABSTAIN.value:
            abstain += 1
        if verdict == CheckletVerdict.ERROR.value:
            error += 1
        truth = label == CriterionLabel.TRUE
        if predicted_finding and truth:
            tp += 1
            others = [
                other_id
                for other_id in CHECKLET_IDS
                if other_id != checklet_id
                and record.primary_criterion_label(other_id, adjudicator_ids=adjudicator_ids) == CriterionLabel.TRUE
                and _is_finding(record.observation_for(other_id))
            ]
            if not others:
                unique_catches += 1
        elif predicted_finding and not truth:
            fp += 1
        elif (not predicted_finding) and truth:
            fn += 1
        else:
            tn += 1
        if predicted_finding and observation is not None:
            severity = str(observation.get("severity", "info"))
            bucket = severity_rows.setdefault(severity, {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
            if truth:
                bucket["tp"] += 1
            else:
                bucket["fp"] += 1
    n_adj = tp + fp + tn + fn
    return {
        "checklet_id": checklet_id,
        "n_applicable": len(applicable),
        "n_adjudicated": n_adj,
        "n_indeterminate": indeterminate,
        "n_not_applicable": not_applicable,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "criterion_precision": _ratio(tp, tp + fp),
        "criterion_recall": _ratio(tp, tp + fn),
        "criterion_specificity": _ratio(tn, tn + fp),
        "criterion_false_positive_rate": _ratio(fp, fp + tn),
        "criterion_false_negative_rate": _ratio(fn, fn + tp),
        "criterion_abstention_rate": _ratio(abstain, len(applicable)),
        "criterion_indeterminate_rate": _ratio(indeterminate, len(applicable) + not_applicable + indeterminate),
        "unique_criterion_catches": unique_catches,
        "precision_by_severity": {
            severity: _ratio(counts["tp"], counts["tp"] + counts["fp"]) for severity, counts in severity_rows.items()
        },
        "recall_by_severity": {
            severity: _ratio(counts["tp"], counts["tp"] + counts["fn"]) for severity, counts in severity_rows.items()
        },
        "descriptive_only": _descriptive(n_adj),
        "counts": {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "abstain": abstain, "error": error},
        "adjudicator_ids": sorted(adjudicator_ids) if adjudicator_ids is not None else None,
    }


def predictive_metrics(records: Sequence[RealTaskEvidenceRecord], checklet_id: str) -> dict[str, Any]:
    determinate = [record for record in records if record.determinate]
    by_verdict: dict[str, list[RealTaskEvidenceRecord]] = {
        CheckletVerdict.CLEAN.value: [],
        CheckletVerdict.FINDING.value: [],
        CheckletVerdict.ABSTAIN.value: [],
        CheckletVerdict.ERROR.value: [],
    }
    unique_hard_signals = 0
    for record in determinate:
        observation = record.observation_for(checklet_id)
        if observation is None:
            continue
        by_verdict[str(observation.get("verdict"))].append(record)
        if (
            record.hard_outcome == HardVerifierOutcome.REJECTED
            and _material_finding(observation)
            and not any(
                _material_finding(record.observation_for(other))
                for other in CHECKLET_IDS
                if other != checklet_id
            )
        ):
            unique_hard_signals += 1

    def _reject_stats(subset: Sequence[RealTaskEvidenceRecord]) -> dict[str, Any]:
        rejects = sum(record.hard_outcome == HardVerifierOutcome.REJECTED for record in subset)
        n = len(subset)
        return {
            "n": n,
            "rejects": rejects,
            "display": f"{rejects} / {n}",
            "rate": _ratio(rejects, n),
            "interval": wilson_interval(rejects, n),
            "descriptive_only": _descriptive(n),
        }

    clean = _reject_stats(by_verdict[CheckletVerdict.CLEAN.value])
    finding = _reject_stats(by_verdict[CheckletVerdict.FINDING.value])
    lift_abs = None
    lift_rel = None
    if clean["rate"] is not None and finding["rate"] is not None:
        lift_abs = finding["rate"] - clean["rate"]
        if clean["rate"] > 0:
            lift_rel = finding["rate"] / clean["rate"]
    return {
        "checklet_id": checklet_id,
        "p_hard_reject_given_clean": clean,
        "p_hard_reject_given_finding": finding,
        "p_hard_reject_given_abstain": _reject_stats(by_verdict[CheckletVerdict.ABSTAIN.value]),
        "p_hard_reject_given_error": _reject_stats(by_verdict[CheckletVerdict.ERROR.value]),
        "absolute_rejection_rate_difference": lift_abs,
        "relative_lift": lift_rel,
        "association_not_causality": True,
        "hard_reject_unique_signal": unique_hard_signals,
        "n_determinate": len(determinate),
    }


def shadow_metrics(records: Sequence[RealTaskEvidenceRecord]) -> dict[str, Any]:
    n_total = len(records)
    n_unknown = sum(record.hard_outcome == HardVerifierOutcome.OUTCOME_UNKNOWN for record in records)
    n_infra = sum(record.hard_outcome == HardVerifierOutcome.INFRASTRUCTURE_ERROR for record in records)
    determinate = [record for record in records if record.determinate]
    n_determinate = len(determinate)
    would_waive = [record for record in records if record.shadow_assessment.get("shadow_action") == ShadowAction.WOULD_WAIVE.value]
    determinate_waive = [record for record in would_waive if record.determinate]
    false_waives = sum(
        record.hard_outcome == HardVerifierOutcome.REJECTED for record in determinate_waive
    )
    correct_waives = sum(
        record.hard_outcome == HardVerifierOutcome.ACCEPTED for record in determinate_waive
    )
    would_verify = [record for record in records if record.shadow_assessment.get("shadow_action") != ShadowAction.WOULD_WAIVE.value]
    unnecessary = sum(
        record.determinate and record.hard_outcome == HardVerifierOutcome.ACCEPTED for record in would_verify
    )
    miss_n = len(determinate_waive)
    return {
        "n_total": n_total,
        "n_determinate": n_determinate,
        "n_unknown": n_unknown,
        "n_infrastructure_error": n_infra,
        "n_would_waive": len(would_waive),
        "n_determinate_would_waive": len(determinate_waive),
        "n_false_shadow_waives": false_waives,
        "false_shadow_waive_display": f"{false_waives} / {miss_n}",
        "n_correct_shadow_waives": correct_waives,
        "shadow_waiver_coverage": _ratio(len(would_waive), n_total),
        "observed_miss_rate": _ratio(false_waives, miss_n),
        "observed_miss_interval": wilson_interval(false_waives, miss_n),
        "n_would_hard_verify": len(would_verify),
        "n_unnecessary_shadow_verifies": unnecessary,
        "unnecessary_verify_rate": _ratio(unnecessary, len(would_verify)),
        "unnecessary_verify_display": f"{unnecessary} / {len(would_verify)}",
        "unknown_outcome_rate": _ratio(n_unknown, n_total),
        "infrastructure_error_rate": _ratio(n_infra, n_total),
        "descriptive_only": _descriptive(n_determinate),
    }


def objective_gate_baseline(records: Sequence[RealTaskEvidenceRecord]) -> dict[str, Any]:
    determinate = [record for record in records if record.determinate]
    gates_pass = [record for record in determinate if _gates_pass(record)]
    gates_pass_all_clean = [
        record
        for record in gates_pass
        if all(item.get("verdict") == CheckletVerdict.CLEAN.value for item in record.checklet_observations)
    ]
    low_risk = [record for record in determinate if _low_risk(record)]

    def _rate(subset: Sequence[RealTaskEvidenceRecord], label: str) -> dict[str, Any]:
        rejects = sum(record.hard_outcome == HardVerifierOutcome.REJECTED for record in subset)
        return {
            "label": label,
            "n": len(subset),
            "rejects": rejects,
            "display": f"{rejects} / {len(subset)}",
            "rate": _ratio(rejects, len(subset)),
            "interval": wilson_interval(rejects, len(subset)),
            "descriptive_only": _descriptive(len(subset)),
        }

    return {
        "after_objective_gates_pass": _rate(gates_pass, "hard rejection after objective gates pass"),
        "after_gates_pass_and_all_checklets_clean": _rate(
            gates_pass_all_clean, "hard rejection after gates pass + all checklets clean"
        ),
        "low_risk_region": _rate(low_risk, "V1.1 low-risk region"),
    }


def low_risk_region(records: Sequence[RealTaskEvidenceRecord]) -> dict[str, Any]:
    determinate = [record for record in records if record.determinate]
    region = [record for record in determinate if _low_risk(record)]
    rejects = sum(record.hard_outcome == HardVerifierOutcome.REJECTED for record in region)
    repos = sorted({record.repository_id for record in region})
    families = sorted({record.task_family_id for record in region})
    producers = sorted({record.producer.producer_executor_id for record in region})
    sizes = sorted({record.patch_size_bucket for record in region})
    types = sorted({record.task_type for record in region})
    generalizes = len(repos) > 1 and len(families) > 1 and len(sizes) > 1
    return {
        "definition": "objective gates pass + no required checklet abstain/error + no medium/high/critical findings",
        "n": len(region),
        "coverage": _ratio(len(region), len(determinate)),
        "reject_count": rejects,
        "reject_rate": _ratio(rejects, len(region)),
        "reject_display": f"{rejects} / {len(region)}",
        "interval": wilson_interval(rejects, len(region)),
        "repository_distribution": dict(Counter(record.repository_id for record in region)),
        "task_type_distribution": dict(Counter(record.task_type for record in region)),
        "producer_distribution": dict(Counter(record.producer.producer_executor_id for record in region)),
        "patch_size_distribution": dict(Counter(record.patch_size_bucket for record in region)),
        "generalizes": generalizes,
        "generalization_note": (
            "low-risk region observed across multiple repositories, families, and patch sizes"
            if generalizes
            else "low-risk region not demonstrated to generalize"
        ),
        "descriptive_only": _descriptive(len(region)),
    }


def dependence_metrics(records: Sequence[RealTaskEvidenceRecord]) -> dict[str, Any]:
    finding_sets: dict[str, set[str]] = {checklet_id: set() for checklet_id in CHECKLET_IDS}
    families: dict[str, str] = {}
    for record in records:
        for checklet_id in CHECKLET_IDS:
            observation = record.observation_for(checklet_id)
            if observation is not None:
                families[checklet_id] = str(observation.get("evidence_family_id", ""))
            if _is_finding(observation):
                finding_sets[checklet_id].add(record.record_id)
    jaccard: dict[str, float | None] = {}
    phi: dict[str, float | None] = {}
    conditional: dict[str, float | None] = {}
    ids = [record.record_id for record in records]
    for i, left in enumerate(CHECKLET_IDS):
        for right in CHECKLET_IDS[i + 1 :]:
            a = finding_sets[left]
            b = finding_sets[right]
            union = a | b
            key = f"{left}|{right}"
            jaccard[key] = _ratio(len(a & b), len(union))
            n11 = len(a & b)
            n10 = len(a - b)
            n01 = len(b - a)
            n00 = len(set(ids) - union)
            phi[key] = phi_coefficient(n11, n10, n01, n00)
            conditional[f"{right}|{left}"] = _ratio(n11, len(a))
            conditional[f"{left}|{right}"] = _ratio(n11, len(b))
    return {
        "evidence_family_ids": families,
        "co_finding_matrix": jaccard,
        "jaccard_overlap": jaccard,
        "phi_correlation": phi,
        "conditional_finding_rates": conditional,
        "note": "checklets are not assumed independent",
    }


def combination_analysis(records: Sequence[RealTaskEvidenceRecord]) -> list[dict[str, Any]]:
    determinate = [record for record in records if record.determinate]
    combos: dict[str, list[RealTaskEvidenceRecord]] = {
        "all_applicable_clean": [],
        "one_low_finding": [],
        "one_medium_finding": [],
        "two_plus_independent_findings": [],
        "required_abstain": [],
        "required_error": [],
        "objective_warning_plus_checklet_finding": [],
        "gates_pass_all_clean": [],
    }
    for record in determinate:
        findings = [item for item in record.checklet_observations if item.get("verdict") == CheckletVerdict.FINDING.value]
        medium = [item for item in findings if item.get("severity") == Severity.MEDIUM.value]
        low = [item for item in findings if item.get("severity") == Severity.LOW.value]
        abstain = any(item.get("verdict") == CheckletVerdict.ABSTAIN.value for item in record.checklet_observations)
        error = any(item.get("verdict") == CheckletVerdict.ERROR.value for item in record.checklet_observations)
        gates_pass = _gates_pass(record)
        gate_warning = any(item.get("status") != "pass" for item in record.gate_results)
        if findings and all(item.get("verdict") == CheckletVerdict.CLEAN.value for item in record.checklet_observations if item not in findings):
            pass
        if not findings and not abstain and not error:
            combos["all_applicable_clean"].append(record)
        if len(low) == 1 and len(findings) == 1:
            combos["one_low_finding"].append(record)
        if len(medium) == 1 and len(findings) == 1:
            combos["one_medium_finding"].append(record)
        if len(findings) >= 2:
            combos["two_plus_independent_findings"].append(record)
        if abstain:
            combos["required_abstain"].append(record)
        if error:
            combos["required_error"].append(record)
        if gate_warning and findings:
            combos["objective_warning_plus_checklet_finding"].append(record)
        if gates_pass and not findings and not abstain and not error:
            combos["gates_pass_all_clean"].append(record)
    results = []
    for label, subset in combos.items():
        if not subset:
            continue
        rejects = sum(record.hard_outcome == HardVerifierOutcome.REJECTED for record in subset)
        results.append(
            {
                "combination": label,
                "n": len(subset),
                "rejects": rejects,
                "display": f"{rejects} / {len(subset)}",
                "rate": _ratio(rejects, len(subset)),
                "interval": wilson_interval(rejects, len(subset)),
                "descriptive_only": _descriptive(len(subset)),
            }
        )
    return results


def stratified_results(records: Sequence[RealTaskEvidenceRecord]) -> dict[str, Any]:
    determinate = [record for record in records if record.determinate]

    def _break(key_fn, name: str) -> list[dict[str, Any]]:
        groups: dict[str, list[RealTaskEvidenceRecord]] = {}
        for record in determinate:
            groups.setdefault(str(key_fn(record)), []).append(record)
        rows = []
        for key, subset in sorted(groups.items()):
            rejects = sum(record.hard_outcome == HardVerifierOutcome.REJECTED for record in subset)
            rows.append(
                {
                    "stratum": name,
                    "value": key,
                    "n": len(subset),
                    "rejects": rejects,
                    "display": f"{rejects} / {len(subset)}",
                    "rate": _ratio(rejects, len(subset)) if not _descriptive(len(subset)) else None,
                    "note": "descriptive only" if _descriptive(len(subset)) else "rate comparison eligible",
                }
            )
        return rows

    return {
        "repository": _break(lambda record: record.repository_id, "repository"),
        "task_type": _break(lambda record: record.task_type, "task_type"),
        "patch_size_bucket": _break(lambda record: record.patch_size_bucket, "patch_size_bucket"),
        "producer": _break(lambda record: record.producer.producer_executor_id, "producer"),
        "oracle_type": _break(lambda record: record.oracle_scope, "oracle_type"),
    }


def cost_latency(records: Sequence[RealTaskEvidenceRecord]) -> dict[str, Any]:
    checklet_latencies = [
        float(item.get("latency_ms", 0.0))
        for record in records
        for item in record.checklet_observations
    ]
    hard_latencies = [float(record.hard_verifier_result.get("latency_ms", 0.0)) for record in records]
    gate_latencies = [float(item.get("latency_ms", 0.0)) for record in records for item in record.gate_results]
    per_checklet: dict[str, list[float]] = {checklet_id: [] for checklet_id in CHECKLET_IDS}
    per_checklet_cost: dict[str, list[float]] = {checklet_id: [] for checklet_id in CHECKLET_IDS}
    for record in records:
        for item in record.checklet_observations:
            checklet_id = str(item.get("checklet_id"))
            if checklet_id in per_checklet:
                per_checklet[checklet_id].append(float(item.get("latency_ms", 0.0)))
                cost = item.get("estimated_or_actual_cost") or {}
                per_checklet_cost[checklet_id].append(float(cost.get("amount", 0.0) or 0.0))

    def _summary(values: Sequence[float]) -> dict[str, float | None]:
        return {
            "mean": mean(values) if values else None,
            "p50": _percentile(values, 0.5),
            "p95": _percentile(values, 0.95),
            "total": sum(values) if values else 0.0,
        }

    return {
        "objective_gate_latency_ms": _summary(gate_latencies),
        "per_checklet_latency_ms": {key: _summary(values) for key, values in per_checklet.items()},
        "per_checklet_cost": {key: _summary(values) for key, values in per_checklet_cost.items()},
        "total_checklet_bundle_latency_ms": _summary(checklet_latencies),
        "hard_verifier_latency_ms": _summary(hard_latencies),
        "total_verification_latency_ms": _summary(
            [sum(per_checklet[checklet_id][index] for checklet_id in CHECKLET_IDS if index < len(per_checklet[checklet_id])) for index in range(len(records))]
            if records
            else []
        ),
        "counterfactual_expected_cost": {
            "status": "NOT REALIZED",
            "authorization": "NOT AUTHORIZED",
            "note": "All five applicable checklets still run; selective verification remains off.",
        },
    }


def dataset_composition(records: Sequence[RealTaskEvidenceRecord]) -> dict[str, Any]:
    origins = Counter(record.task_origin.value for record in records)
    n_real = origins.get(TaskOrigin.REAL_HISTORICAL.value, 0) + origins.get(TaskOrigin.REAL_LIVE.value, 0)
    n_controlled = origins.get(TaskOrigin.CONTROLLED_MUTATION.value, 0) + origins.get(TaskOrigin.ENGINEERING_FIXTURE.value, 0)
    real_unknown = sum(
        record.task_origin in {TaskOrigin.REAL_HISTORICAL, TaskOrigin.REAL_LIVE}
        and record.hard_outcome == HardVerifierOutcome.OUTCOME_UNKNOWN
        for record in records
    )
    real_infra = sum(
        record.task_origin in {TaskOrigin.REAL_HISTORICAL, TaskOrigin.REAL_LIVE}
        and record.hard_outcome == HardVerifierOutcome.INFRASTRUCTURE_ERROR
        for record in records
    )
    synthetic_records = [
        record
        for record in records
        if record.task_origin in {TaskOrigin.ENGINEERING_FIXTURE, TaskOrigin.CONTROLLED_MUTATION}
    ]
    partitions = Counter(record.partition.value for record in records)
    real_origins = {TaskOrigin.REAL_HISTORICAL, TaskOrigin.REAL_LIVE}
    real_determinate = [
        record
        for record in records
        if record.task_origin in real_origins and record.determinate
    ]
    diversity = {
        "n_repositories": len({record.repository_id for record in real_determinate}),
        "n_task_families": len({record.task_family_id for record in real_determinate}),
        "n_patch_sizes": len({record.patch_size_bucket for record in real_determinate}),
        "n_producers": len({record.producer.producer_executor_id for record in real_determinate}),
    }
    diversity["sufficient"] = (
        diversity["n_repositories"] >= 2
        and diversity["n_task_families"] >= 2
        and diversity["n_patch_sizes"] >= 2
    )
    return {
        "n_total": len(records),
        "n_real": n_real,
        "n_controlled_or_synthetic": n_controlled,
        "n_determinate": sum(record.determinate for record in records),
        "n_real_determinate": len(real_determinate),
        "n_real_unknown": real_unknown,
        "n_real_infrastructure_error": real_infra,
        "n_synthetic": n_controlled,
        "n_synthetic_determinate": sum(record.determinate for record in synthetic_records),
        "n_accepted": sum(record.hard_outcome == HardVerifierOutcome.ACCEPTED for record in records),
        "n_rejected": sum(record.hard_outcome == HardVerifierOutcome.REJECTED for record in records),
        "n_unknown": sum(record.hard_outcome == HardVerifierOutcome.OUTCOME_UNKNOWN for record in records),
        "n_infrastructure_error": sum(record.hard_outcome == HardVerifierOutcome.INFRASTRUCTURE_ERROR for record in records),
        "origins": dict(origins),
        "repositories": sorted({record.repository_id for record in records}),
        "task_families": sorted({record.task_family_id for record in records}),
        "producer_families": sorted({record.producer.producer_executor_id for record in records}),
        "patch_size_distribution": dict(Counter(record.patch_size_bucket for record in records)),
        "oracle_types": sorted({record.oracle_scope for record in records}),
        "partition_sizes": dict(partitions),
        "languages": sorted({record.language for record in records}),
        "real_determinate_diversity": diversity,
    }


def _numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _gate(name: str, passed: bool, **payload: Any) -> dict[str, Any]:
    result = {"name": name, "passed": passed}
    result.update(payload)
    return result


def decide_v2(analysis: Mapping[str, Any], config: DecisionGateConfig | None = None) -> dict[str, Any]:
    gate_config = config or DEFAULT_DECISION_GATE
    composition = analysis["dataset_composition"]
    integrity = analysis["data_quality"]
    low_risk = analysis["low_risk_region"]
    n_real_determinate = int(composition.get("n_real_determinate", 0))
    diversity = dict(composition.get("real_determinate_diversity") or {})
    reject_rate = _numeric(low_risk.get("reject_rate"))
    gate_rate = _numeric(analysis["objective_gate_baseline"]["after_objective_gates_pass"].get("rate"))
    diversity_ok = (
        int(diversity.get("n_repositories") or 0) >= gate_config.minimum_repository_count
        and int(diversity.get("n_task_families") or 0) >= gate_config.minimum_task_family_count
        and int(diversity.get("n_patch_sizes") or 0) >= gate_config.minimum_patch_size_count
    )
    criterion_signal = [
        item
        for item in analysis["criterion_quality"].values()
        if _numeric(item.get("criterion_precision")) is not None
        and _numeric(item.get("criterion_recall")) is not None
        and _numeric(item.get("criterion_precision")) >= gate_config.criterion_precision_floor
        and _numeric(item.get("criterion_recall")) >= gate_config.criterion_recall_floor
    ]
    predictive_signal = [
        item
        for item in analysis["predictive_utility"].values()
        if _numeric(item.get("absolute_rejection_rate_difference")) is not None
        and _numeric(item.get("absolute_rejection_rate_difference")) > 0
        and not item.get("p_hard_reject_given_finding", {}).get("descriptive_only", True)
    ]
    low_risk_ok = (
        not low_risk.get("descriptive_only")
        and bool(low_risk.get("generalizes"))
        and reject_rate is not None
        and gate_rate is not None
        and reject_rate < gate_rate
    )
    gates = {
        "integrity": _gate("integrity", bool(integrity.get("ok", False))),
        "real_determinate_sample": _gate(
            "real_determinate_sample",
            n_real_determinate >= gate_config.minimum_real_determinate_n,
            observed=n_real_determinate,
            required=gate_config.minimum_real_determinate_n,
        ),
        "diversity": _gate(
            "diversity",
            diversity_ok,
            observed={
                "n_repositories": diversity.get("n_repositories", 0),
                "n_task_families": diversity.get("n_task_families", 0),
                "n_patch_sizes": diversity.get("n_patch_sizes", 0),
            },
            required={
                "n_repositories": gate_config.minimum_repository_count,
                "n_task_families": gate_config.minimum_task_family_count,
                "n_patch_sizes": gate_config.minimum_patch_size_count,
            },
        ),
        "low_risk_signal": _gate(
            "low_risk_signal",
            low_risk_ok,
            observed=reject_rate,
            baseline_gate_rate=gate_rate,
        ),
        "criterion_validity": _gate("criterion_validity", bool(criterion_signal), n_useful=len(criterion_signal)),
        "predictive_utility": _gate("predictive_utility", bool(predictive_signal), n_useful=len(predictive_signal)),
    }
    blocking = [name for name, item in gates.items() if not item["passed"] and name in {"integrity", "real_determinate_sample", "diversity"}]
    passing = [name for name, item in gates.items() if item["passed"]]
    reasons: list[str] = []
    if not gates["integrity"]["passed"]:
        decision = V2_MORE_DATA
        reasons.append("blocking integrity failures are present")
    elif not gates["real_determinate_sample"]["passed"]:
        decision = V2_MORE_DATA
        reasons.append(
            f"real determinate tasks: {n_real_determinate} / {gate_config.minimum_real_determinate_n} minimum"
        )
    elif not gates["diversity"]["passed"]:
        decision = V2_MORE_DATA
        reasons.append("real determinate sample is too narrow to support a V2 decision")
    elif criterion_signal and not predictive_signal:
        decision = V2_DIAGNOSTIC
        reasons.append("some checklets have criterion validity but weak hard-reject prediction")
    elif len(predictive_signal) == 1 and len(CHECKLET_IDS) > 1:
        decision = V2_REWORK
        reasons.append("one checklet dominates useful hard-reject signal")
    elif low_risk_ok:
        decision = V2_PROCEED
        reasons.append("reproducible low-risk region with lower rejection than the gate baseline")
    elif not predictive_signal and not criterion_signal:
        decision = V2_STOP
        reasons.append("current five-checklet bundle does not justify further selective-verification investment")
    else:
        decision = V2_REWORK
        reasons.append("signals are mixed; rework the checklet set before a V2 risk model")
    if not low_risk_ok and decision != V2_MORE_DATA:
        reasons.append(str(low_risk.get("generalization_note") or "low-risk region not demonstrated"))
    return {
        "decision": decision,
        "decision_gate_id": gate_config.decision_gate_id,
        "decision_gate_kind": gate_config.kind,
        "reasons": reasons,
        "gates": gates,
        "blocking_gates": blocking if decision == V2_MORE_DATA else [name for name, item in gates.items() if not item["passed"]],
        "passing_gates": passing,
    }


def _redact_protected_quality(
    quality: Sequence[Mapping[str, Any]],
    records: Sequence[RealTaskEvidenceRecord],
    allowed: frozenset[Partition],
) -> list[dict[str, Any]]:
    sealed_ids = {record.record_id for record in records if record.partition not in allowed}
    redacted: list[dict[str, Any]] = []
    for item in quality:
        entry = dict(item)
        if entry.get("record_id") in sealed_ids:
            entry["codes"] = ["protected_partition"]
        redacted.append(entry)
    return redacted


def _holdout_missing_evaluation_grade(records: Sequence[RealTaskEvidenceRecord]) -> list[str]:
    missing: list[str] = []
    for record in records:
        if record.partition != Partition.HOLDOUT:
            continue
        ids = {item.adjudicator_id for item in record.criterion_adjudications}
        if not (ids & set(EVALUATION_GRADE_ADJUDICATOR_IDS)):
            missing.append(record.record_id)
    return missing


def analyze_records(
    records: Sequence[RealTaskEvidenceRecord],
    *,
    purpose: str = "v12_analysis",
    config: Mapping[str, Any] | None = None,
    scope: AnalysisScope | str = AnalysisScope.OPERATIONAL,
    unseal_receipt: Mapping[str, Any] | None = None,
    holdout_state: str = "sealed",
    calibration_state: str = "sealed",
) -> dict[str, Any]:
    if purpose in HOLDOUT_TUNING_PURPOSES:
        assert_partition_allowed(records, purpose)
    resolved_scope = AnalysisScope(scope)
    if resolved_scope is AnalysisScope.FINAL_HOLDOUT and holdout_state != "final_unsealed":
        raise HoldoutAccessError(f"{FailureCode.HOLDOUT_ACCESS.value}: holdout_state is {holdout_state}")
    if resolved_scope is AnalysisScope.CALIBRATION and calibration_state != "unsealed":
        raise HoldoutAccessError(f"{FailureCode.HOLDOUT_ACCESS.value}: calibration_state is {calibration_state}")
    integrity = validate_dataset_records(records)
    if not integrity["ok"]:
        raise ValueError(f"{FailureCode.REPORT_INTEGRITY_FAILURE.value}: invalid records cannot enter the report")
    usable = filter_records_for_scope(analysis_records(records), resolved_scope, unseal_receipt)
    missing_eval = _holdout_missing_evaluation_grade(usable) if resolved_scope is AnalysisScope.FINAL_HOLDOUT else []
    if missing_eval:
        raise ValueError(
            f"{FailureCode.CRITERION_ADJUDICATION_MISSING.value}: holdout requires evaluation-grade labels: {missing_eval}"
        )
    allowed = frozenset(record.partition for record in usable) or OPERATIONAL_PARTITIONS
    integrity = dict(integrity)
    integrity["quality"] = _redact_protected_quality(integrity.get("quality") or [], records, allowed)
    criterion = {
        checklet_id: criterion_metrics(usable, checklet_id, adjudicator_ids=EVALUATION_GRADE_ADJUDICATOR_IDS)
        for checklet_id in CHECKLET_IDS
    }
    criterion_secondary = {
        checklet_id: criterion_metrics(usable, checklet_id, adjudicator_ids={SECONDARY_ADJUDICATOR_ID})
        for checklet_id in CHECKLET_IDS
    }
    predictive = {checklet_id: predictive_metrics(usable, checklet_id) for checklet_id in CHECKLET_IDS}
    payload = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "analysis_config": dict(
            config
            or {
                "interval": "wilson_95",
                "minimum_descriptive_n": MINIMUM_DESCRIPTIVE_N,
                "analysis_scope": AnalysisScope(scope).value,
            }
        ),
        "analysis_scope": resolved_scope.value,
        "holdout_state": holdout_state,
        "calibration_state": calibration_state,
        "sealed_partition_counts": sealed_partition_counts(records),
        "protected_partition_status": {
            "development": "visible",
            "policy_selection": "visible" if resolved_scope in {AnalysisScope.OPERATIONAL, AnalysisScope.POLICY_SELECTION, AnalysisScope.FINAL_HOLDOUT} else "hidden",
            "calibration_reserved": "unsealed" if calibration_state == "unsealed" and resolved_scope is AnalysisScope.CALIBRATION else "sealed",
            "holdout": "final_unsealed" if holdout_state == "final_unsealed" and resolved_scope is AnalysisScope.FINAL_HOLDOUT else "sealed",
        },
        "adjudication_modes": {
            "shared_deterministic": SECONDARY_ADJUDICATOR_ID,
            "independent_deterministic": "independent-ast-inspector",
            "expert_blind": "bounded-expert-review",
            "expert_assisted": "bounded-expert-review/assisted",
        },
        "adjudication_disagreement_count": sum(
            len({item.label for item in record.criterion_adjudications if item.checklet_id == checklet_id}) > 1
            for record in usable
            for checklet_id in CHECKLET_IDS
        ),
        "n_records_in_dataset": len(records),
        "dataset_composition": dataset_composition(usable),
        "data_quality": integrity,
        "hard_verifier_outcomes": {
            outcome.value: sum(record.hard_outcome == outcome for record in usable) for outcome in HardVerifierOutcome
        },
        "criterion_quality": criterion,
        "criterion_quality_secondary": criterion_secondary,
        "predictive_utility": predictive,
        "objective_gate_baseline": objective_gate_baseline(usable),
        "cross_checklet_dependence": dependence_metrics(usable),
        "combinations": combination_analysis(usable),
        "low_risk_region": low_risk_region(usable),
        "shadow_metrics": shadow_metrics(usable),
        "stratified_results": stratified_results(usable),
        "cost_and_latency": cost_latency(usable),
        "limitations": [
            "V1.2 is observational/selective-prediction evidence; predictive lift is not causality",
            "engineering fixtures and controlled mutations are not a substitute for 50-200 real tasks",
            "unknown and infrastructure-error outcomes are excluded from miss-rate denominators",
            "would_waive never authorizes acceptance; selective verification remains off",
            "small-N strata are descriptive only",
            "V2 criterion metrics use evaluation-grade labels only; shared-primitive inspection is secondary",
            "default analysis excludes calibration_reserved and holdout until finalize-holdout",
        ],
    }
    payload["v2_decision"] = decide_v2(payload)
    payload["n_records_analyzed"] = len(usable)
    return payload
