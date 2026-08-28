"""Fixture evaluation, replay, and transparent VS-V1 reporting."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any, Mapping, Sequence

from .artifacts import CandidateArtifact
from .contracts import (
    CheckletVerdict,
    CounterfactualClass,
    HardVerifierOutcome,
    HardVerifierResult,
    TaskContract,
    jsonable,
    utc_now,
)
from .hard_verify import HardVerifier
from .runner import VerificationRun, VerificationRunner
from .telemetry import InMemoryEventSink


DATASET_SCHEMA_VERSION = "verification-v1-evaluation/1.0.0"
FORBIDDEN_ARTIFACT_METADATA = {
    "hard_verifier_outcome",
    "expected_defect_class",
    "expected_affected_checklets",
}


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def _metric_summary(values: Sequence[float]) -> dict[str, float | None]:
    return {
        "mean": mean(values) if values else None,
        "p50": _percentile(values, 0.5),
        "p95": _percentile(values, 0.95),
        "total": sum(values),
    }


def _counterfactual_interval(false_waives: int, waiver_count: int) -> dict[str, Any]:
    # The normal approximation is intentionally withheld for a small experimental fixture set.
    if waiver_count < 30:
        return {"method": "not_reported_small_sample", "lower": None, "upper": None}
    rate = false_waives / waiver_count
    margin = 1.96 * ((rate * (1 - rate) / waiver_count) ** 0.5)
    return {"method": "normal_approximation_95", "lower": max(0.0, rate - margin), "upper": min(1.0, rate + margin)}


def run_to_record(run: VerificationRun) -> dict[str, Any]:
    return {
        "schema_version": DATASET_SCHEMA_VERSION,
        "recorded_at": utc_now(),
        "run_id": run.run_id,
        "task": run.task.to_dict(),
        "artifact": run.artifact.ref.to_dict(),
        "artifact_content_b64": base64.b64encode(run.artifact.content).decode("ascii"),
        "gates": [gate.to_dict() for gate in run.gates],
        "observations": [observation.to_dict() for observation in run.observations],
        "shadow_assessment": run.shadow_assessment.to_dict(),
        "hard_verifier_result": run.hard_verifier_result.to_dict(),
        "comparison": run.comparison.to_dict(),
        "final_outcome": run.final_outcome.value,
        "telemetry_failures": [failure.to_dict() for failure in run.telemetry_failures],
        "component_versions": {
            "runner": {"version": VerificationRunner.version},
            "domain_pack": {"id": run.domain_pack_id, "version": run.domain_pack_version},
            "policy": {
                "id": run.shadow_assessment.policy_id,
                "version": run.shadow_assessment.policy_version,
            },
            "gates": {gate.gate_id: gate.gate_version for gate in run.gates},
            "hard_verifier": f"{run.hard_verifier_result.verifier_id}/{run.hard_verifier_result.verifier_version}",
            "checklets": {
                observation.checklet_id: observation.checklet_version for observation in run.observations
            },
        },
    }


class RecordedHardVerifier:
    """Replays a known hard outcome without pretending it is a newly executed oracle."""

    def __init__(self, recorded: Mapping[str, Any]) -> None:
        self.verifier_id = str(recorded["verifier_id"])
        self.version = str(recorded["verifier_version"])
        self._artifact_digest = str(recorded["artifact_digest"])
        self._recorded = recorded

    def verify(self, task: TaskContract, artifact) -> HardVerifierResult:
        if artifact.artifact_digest != self._artifact_digest:
            raise ValueError("recorded hard-verifier result binds a different artifact digest")
        started = utc_now()
        return HardVerifierResult(
            verifier_id=self.verifier_id,
            verifier_version=self.version,
            artifact_digest=artifact.artifact_digest,
            outcome=HardVerifierOutcome(self._recorded["outcome"]),
            defect_refs=tuple(self._recorded.get("defect_refs", [])),
            evidence_refs=tuple(self._recorded.get("evidence_refs", [])),
            oracle_class=str(self._recorded["oracle_class"]),
            oracle_applicability=str(self._recorded["oracle_applicability"]),
            started_at=started,
            completed_at=utc_now(),
            latency_ms=0.0,
            cost={"kind": "replayed_recorded_cost", "recorded": self._recorded.get("cost", {})},
            metadata={"replayed_from_run_id": self._recorded.get("run_id")},
        )


def replay_run_record(record: Mapping[str, Any]) -> VerificationRun:
    """Re-run deterministic pre-oracle stages against frozen bytes and a recorded hard outcome."""
    if record.get("schema_version") != DATASET_SCHEMA_VERSION:
        raise ValueError("unsupported VS-V1 replay record schema")
    artifact_data = record["artifact"]
    task_data = record["task"]
    task = TaskContract(
        task_id=str(task_data["task_id"]),
        requirements=tuple(task_data.get("requirements", [])),
        description=str(task_data.get("description", "")),
        version=str(task_data.get("version", "1.0.0")),
        metadata=dict(task_data.get("metadata", {})),
    )
    candidate = CandidateArtifact(
        artifact_id=str(artifact_data["artifact_id"]),
        artifact_type=str(artifact_data["artifact_type"]),
        content=base64.b64decode(record["artifact_content_b64"]),
        metadata=dict(artifact_data.get("metadata", {})),
    )
    expected_digest = str(artifact_data["artifact_digest"])
    actual_frozen_digest = sha256(candidate.content).hexdigest()
    if actual_frozen_digest != expected_digest:
        raise ValueError("replay digest mismatch: frozen content no longer identifies the recorded artifact")
    recorded_hard_result = record["hard_verifier_result"]
    if str(recorded_hard_result.get("artifact_digest")) != expected_digest:
        raise ValueError("replay hard-verifier result does not bind the recorded artifact digest")
    expected_components = record.get("component_versions")
    if not isinstance(expected_components, Mapping):
        raise ValueError("replay record lacks semantic component provenance")
    sink = InMemoryEventSink()
    runner = VerificationRunner.default(event_sink=sink)
    replay = runner.run(task, candidate, RecordedHardVerifier(recorded_hard_result))
    if replay.artifact.artifact_digest != expected_digest:
        raise ValueError("replay digest mismatch: frozen content no longer identifies the recorded artifact")
    actual_components = {
        "runner": {"version": VerificationRunner.version},
        "domain_pack": {"id": replay.domain_pack_id, "version": replay.domain_pack_version},
        "policy": {"id": replay.shadow_assessment.policy_id, "version": replay.shadow_assessment.policy_version},
        "gates": {gate.gate_id: gate.gate_version for gate in replay.gates},
        "hard_verifier": f"{replay.hard_verifier_result.verifier_id}/{replay.hard_verifier_result.verifier_version}",
        "checklets": {observation.checklet_id: observation.checklet_version for observation in replay.observations},
    }
    if actual_components != expected_components:
        raise ValueError("replay component provenance changed; this is not scientifically equivalent replay")
    return replay


@dataclass(frozen=True)
class EvaluationReport:
    dataset_id: str
    dataset_version: str
    generated_at: str
    task_count: int
    hard_verifier_coverage: int
    indeterminate_count: int
    run_records: tuple[dict[str, Any], ...]
    per_checklet: Mapping[str, Mapping[str, Any]]
    cross_checklet_overlap: Mapping[str, Any]
    shadow_metrics: Mapping[str, Any]
    cost_and_latency: Mapping[str, Any]
    hard_verifier_outcomes: Mapping[str, int]
    fixture_composition: Mapping[str, int]
    known_limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


def _build_task(data: Mapping[str, Any]) -> TaskContract:
    return TaskContract(
        task_id=str(data["task_id"]),
        requirements=tuple(str(item) for item in data.get("requirements", [])),
        description=str(data.get("description", "")),
        version=str(data.get("version", "1.0.0")),
        metadata=dict(data.get("metadata", {})),
    )


def _build_candidate(fixture: Mapping[str, Any]) -> CandidateArtifact:
    artifact = fixture["artifact"]
    metadata = {key: value for key, value in dict(artifact.get("metadata", {})).items() if key not in FORBIDDEN_ARTIFACT_METADATA}
    metadata["fixture_id"] = fixture["fixture_id"]
    return CandidateArtifact.from_text(
        artifact_id=str(artifact["artifact_id"]),
        artifact_type=str(artifact["artifact_type"]),
        content=str(artifact["content"]),
        metadata=metadata,
    )


class _DatasetHardVerifier:
    verifier_id = "fixture-reference-oracle"
    version = "1.0.0"

    def __init__(self, outcomes: Mapping[str, HardVerifierOutcome]) -> None:
        self._outcomes = dict(outcomes)

    def verify(self, task: TaskContract, artifact) -> HardVerifierResult:
        timer = perf_counter()
        fixture_id = str(artifact.ref.metadata.get("fixture_id"))
        outcome = self._outcomes.get(artifact.artifact_digest, HardVerifierOutcome.OUTCOME_UNKNOWN)
        now = utc_now()
        return HardVerifierResult(
            verifier_id=self.verifier_id,
            verifier_version=self.version,
            artifact_digest=artifact.artifact_digest,
            outcome=outcome,
            defect_refs=(),
            evidence_refs=(f"fixture-reference:{fixture_id}:{artifact.artifact_digest}",),
            oracle_class="executable_reference_fixture",
            oracle_applicability="fixture_acceptance",
            started_at=now,
            completed_at=utc_now(),
            latency_ms=(perf_counter() - timer) * 1000,
            cost={"kind": "actual_cost", "amount": 0.0, "currency": "USD"},
            metadata={},
        )


def _per_checklet_metrics(runs: Sequence[tuple[Mapping[str, Any], VerificationRun]]) -> dict[str, dict[str, Any]]:
    identifiers = sorted({observation.checklet_id for _, run in runs for observation in run.observations})
    result: dict[str, dict[str, Any]] = {}
    for identifier in identifiers:
        observations = [(fixture, next(obs for obs in run.observations if obs.checklet_id == identifier)) for fixture, run in runs]
        positive = [
            fixture for fixture, run in runs
            if run.final_outcome == HardVerifierOutcome.REJECTED and identifier in fixture.get("expected_affected_checklets", [])
        ]
        findings = [(fixture, observation) for fixture, observation in observations if observation.verdict == CheckletVerdict.FINDING]
        true_positive = sum(1 for fixture, _ in findings if fixture in positive)
        false_positive = len(findings) - true_positive
        false_negative = sum(
            1 for fixture, observation in observations if fixture in positive and observation.verdict != CheckletVerdict.FINDING
        )
        true_negative = sum(
            1
            for fixture, observation in observations
            if fixture not in positive and observation.verdict != CheckletVerdict.FINDING
        )
        unique = 0
        for fixture, observation in findings:
            if fixture not in positive:
                continue
            finding_count = sum(item.verdict == CheckletVerdict.FINDING for item in next(run for candidate, run in runs if candidate is fixture).observations)
            unique += finding_count == 1
        latency = [observation.latency_ms for _, observation in observations]
        cost = [
            float(observation.estimated_or_actual_cost.get("amount", 0.0))
            for _, observation in observations
            if observation.estimated_or_actual_cost.get("kind") in {"actual_cost", "estimated_cost"}
        ]
        clean = [(fixture, observation) for fixture, observation in observations if observation.verdict == CheckletVerdict.CLEAN]
        clean_rejections = sum(
            1
            for fixture, _ in clean
            if next(run for candidate, run in runs if candidate is fixture).final_outcome == HardVerifierOutcome.REJECTED
        )
        result[identifier] = {
            "observation_count": len(observations),
            "applicability_count": len(observations),
            "finding_count": len(findings),
            "clean_count": len(clean),
            "abstention_count": sum(observation.verdict == CheckletVerdict.ABSTAIN for _, observation in observations),
            "error_count": sum(observation.verdict == CheckletVerdict.ERROR for _, observation in observations),
            "precision": _ratio(true_positive, true_positive + false_positive),
            "recall": _ratio(true_positive, true_positive + false_negative),
            "specificity": _ratio(true_negative, true_negative + false_positive),
            "false_positive_rate": _ratio(false_positive, false_positive + true_negative),
            "false_negative_rate": _ratio(false_negative, false_negative + true_positive),
            "unique_catch_count": unique,
            "unique_catch_rate": _ratio(unique, len(positive)),
            "clean_predictive_value_for_fixture_label": _ratio(len(clean) - clean_rejections, len(clean)),
            "latency_ms": _metric_summary(latency),
            "cost": _metric_summary(cost),
        }
    return result


def _overlap_metrics(runs: Sequence[tuple[Mapping[str, Any], VerificationRun]]) -> dict[str, Any]:
    identifiers = sorted({observation.checklet_id for _, run in runs for observation in run.observations})
    matrix: dict[str, float | None] = {}
    for left in identifiers:
        for right in identifiers:
            if left >= right:
                continue
            left_flags = {fixture["fixture_id"] for fixture, run in runs if next(obs for obs in run.observations if obs.checklet_id == left).verdict == CheckletVerdict.FINDING}
            right_flags = {fixture["fixture_id"] for fixture, run in runs if next(obs for obs in run.observations if obs.checklet_id == right).verdict == CheckletVerdict.FINDING}
            matrix[f"{left}|{right}"] = _ratio(len(left_flags & right_flags), len(left_flags | right_flags))
    return {"jaccard_finding_overlap": matrix}


def evaluate_fixture_set(path: Path) -> EvaluationReport:
    payload = json.loads(path.read_text(encoding="utf-8"))
    fixtures = tuple(payload.get("fixtures", []))
    outcomes: dict[str, HardVerifierOutcome] = {}
    for fixture in fixtures:
        digest = sha256(_build_candidate(fixture).content).hexdigest()
        outcome = HardVerifierOutcome(fixture["hard_verifier_outcome"])
        if digest in outcomes and outcomes[digest] != outcome:
            raise ValueError("fixture oracle assigns conflicting hard outcomes to identical artifact content")
        outcomes[digest] = outcome
    verifier: HardVerifier = _DatasetHardVerifier(outcomes)
    evaluated: list[tuple[Mapping[str, Any], VerificationRun]] = []
    records: list[dict[str, Any]] = []
    for fixture in fixtures:
        # Checklets get only the task and candidate artifact; oracle labels stay in the verifier mapping.
        run = VerificationRunner.default(event_sink=InMemoryEventSink()).run(_build_task(fixture["task"]), _build_candidate(fixture), verifier)
        evaluated.append((fixture, run))
        record = run_to_record(run)
        record["fixture_id"] = fixture["fixture_id"]
        record["fixture_split"] = fixture.get("split", "development")
        record["expected_defect_class"] = fixture.get("expected_defect_class")
        record["expected_affected_checklets"] = fixture.get("expected_affected_checklets", [])
        records.append(record)
    per_checklet = _per_checklet_metrics(evaluated)
    waiver_runs = [run for _, run in evaluated if run.shadow_assessment.shadow_action.value == "would_waive"]
    determinate_waiver_runs = [
        run for run in waiver_runs if run.comparison.counterfactual_class != CounterfactualClass.INDETERMINATE
    ]
    false_waives = sum(run.comparison.counterfactual_class == CounterfactualClass.FALSE_SHADOW_WAIVE for run in determinate_waiver_runs)
    correct_waives = sum(run.comparison.counterfactual_class == CounterfactualClass.CORRECT_SHADOW_WAIVE for run in determinate_waiver_runs)
    outcomes_count = {outcome.value: sum(run.final_outcome == outcome for _, run in evaluated) for outcome in HardVerifierOutcome}
    checklet_latencies = [observation.latency_ms for _, run in evaluated for observation in run.observations]
    hard_latencies = [run.hard_verifier_result.latency_ms for _, run in evaluated]
    fixture_composition = {
        "seeded_defect": sum(bool(fixture.get("expected_defect_class")) for fixture in fixtures),
        "known_clean_control": sum(not bool(fixture.get("expected_defect_class")) for fixture in fixtures),
    }
    indeterminate = sum(
        run.comparison.counterfactual_class == CounterfactualClass.INDETERMINATE for _, run in evaluated
    )
    return EvaluationReport(
        dataset_id=str(payload.get("dataset_id", "engineering_fixture_set")),
        dataset_version=str(payload.get("dataset_version", "1.0.0")),
        generated_at=utc_now(),
        task_count=len(evaluated),
        hard_verifier_coverage=sum(run.final_outcome in {HardVerifierOutcome.ACCEPTED, HardVerifierOutcome.REJECTED} for _, run in evaluated),
        indeterminate_count=indeterminate,
        run_records=tuple(records),
        per_checklet=per_checklet,
        cross_checklet_overlap=_overlap_metrics(evaluated),
        shadow_metrics={
            "shadow_waiver_count": len(waiver_runs),
            "determinate_shadow_waiver_count": len(determinate_waiver_runs),
            "shadow_verification_count": len(evaluated) - len(waiver_runs),
            "shadow_indeterminate_count": sum(run.shadow_assessment.risk_band.value == "indeterminate" for _, run in evaluated),
            "shadow_waiver_coverage": _ratio(len(waiver_runs), len(evaluated)),
            "false_shadow_waiver_count": false_waives,
            "correct_shadow_waiver_count": correct_waives,
            "observed_counterfactual_shadow_miss_rate": _ratio(false_waives, len(determinate_waiver_runs)),
            "unnecessary_shadow_verification_rate": _ratio(
                sum(run.comparison.counterfactual_class == CounterfactualClass.UNNECESSARY_SHADOW_VERIFY for _, run in evaluated),
                len(evaluated) - len(waiver_runs),
            ),
            "observed_miss_interval": _counterfactual_interval(false_waives, len(determinate_waiver_runs)),
        },
        cost_and_latency={
            "checklets_latency_ms": _metric_summary(checklet_latencies),
            "hard_verifier_latency_ms": _metric_summary(hard_latencies),
            "total_verification_overhead_ms": sum(checklet_latencies) + sum(hard_latencies),
            "counterfactual_savings_note": "Experimental estimate only; VS-V1 always invokes the hard verifier.",
        },
        hard_verifier_outcomes=outcomes_count,
        fixture_composition=fixture_composition,
        known_limitations=(
            "engineering_fixture_set is not a statistically representative production dataset",
            "checklet metrics use seeded fixture expectations and should not be generalized beyond this sample",
            "would_waive is an experimental counterfactual and never authorizes acceptance",
        ),
    )


def _markdown_report(report: EvaluationReport) -> str:
    shadow = report.shadow_metrics
    lines = [
        "# Verification Slice V1 Evaluation Report",
        "",
        f"- Dataset: `{report.dataset_id}` v`{report.dataset_version}`",
        f"- Generated: {report.generated_at}",
        f"- Tasks: {report.task_count}; hard-verifier coverage: {report.hard_verifier_coverage}; indeterminate: {report.indeterminate_count}",
        f"- Shadow waiver coverage: {shadow['shadow_waiver_coverage']}; observed counterfactual shadow miss rate: {shadow['observed_counterfactual_shadow_miss_rate']}",
        "",
        "## Per-checklet results",
        "",
        "| Checklet | Findings | Precision | Recall | Unique catches |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for checklet_id, metrics in report.per_checklet.items():
        lines.append(
            f"| {checklet_id} | {metrics['finding_count']} | {metrics['precision']} | {metrics['recall']} | {metrics['unique_catch_count']} |"
        )
    lines.extend(["", "## Known limitations", ""])
    lines.extend(f"- {limitation}" for limitation in report.known_limitations)
    return "\n".join(lines) + "\n"


def write_report(report: EvaluationReport, report_dir: Path) -> dict[str, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "latest.json"
    markdown_path = report_dir / "latest.md"
    json_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_markdown_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}
