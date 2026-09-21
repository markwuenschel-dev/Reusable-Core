"""V1.2 reports. Headline numbers are a pure function of a validated dataset."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from .analysis import ANALYSIS_SCHEMA_VERSION, analyze_records
from .artifacts import canonical_artifact_bytes
from .baseline import collect_baseline, repo_root
from .contracts import utc_now
from .dataset import EvidenceDataset
from .evidence import CHECKLET_IDS, EXPERIMENT_BASELINE_ID, EXPERIMENT_ID, FailureCode, RealTaskEvidenceRecord
from .splits import AnalysisScope

REPORT_SCHEMA_VERSION = "verification-v1.2-report/1.0.0"
ANALYSIS_CODE_PATHS = (
    "verification_v1/analysis.py",
    "verification_v1/v12_report.py",
    "verification_v1/integrity.py",
    "verification_v1/evidence.py",
)


def analysis_code_version(root: Path | None = None) -> str:
    """Provenance hash of the analysis code, independent of checkout line endings.

    This hashed raw bytes while baseline.py normalises to LF, so identical source
    produced two different published provenance values depending on whether the
    checkout used CRLF -- and the committed value was the LF one, which a Windows
    checkout could not reproduce even though CI regenerates this artifact there.
    """
    base = root or repo_root()
    material = b""
    for relative in ANALYSIS_CODE_PATHS:
        material += canonical_artifact_bytes((base / relative).read_bytes())
    return "sha256:" + sha256(material).hexdigest()[:16]


def _fmt_rate(value: float | None, successes: int | None = None, n: int | None = None) -> str:
    if n is not None and successes is not None:
        if value is None:
            return f"{successes} / {n} (undefined)"
        return f"{successes} / {n} ({value:.4f})"
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def _fmt_interval(interval: Mapping[str, Any] | None) -> str:
    if not interval or interval.get("lower") is None:
        return "n/a"
    return f"[{interval['lower']:.4f}, {interval['upper']:.4f}] ({interval.get('method')})"


def build_report(
    dataset: EvidenceDataset,
    *,
    analysis_config: Mapping[str, Any] | None = None,
    scope: AnalysisScope | str = AnalysisScope.OPERATIONAL,
    unseal_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    analysis = analyze_records(
        dataset.records,
        config=analysis_config,
        scope=scope,
        unseal_receipt=unseal_receipt or dataset.unseal_receipt,
        holdout_state=dataset.holdout_state,
        calibration_state=dataset.calibration_state,
    )
    baseline = collect_baseline()
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "experiment_id": dataset.experiment_id or EXPERIMENT_ID,
        "cohort_id": dataset.cohort_id,
        "baseline_id": dataset.experiment_baseline_id or EXPERIMENT_BASELINE_ID,
        "dataset_id": dataset.dataset_id,
        "dataset_version": dataset.dataset_version,
        "split_version": f"{dataset.split_algorithm_version}/{dataset.split_seed}",
        "git_revision": baseline.get("repository_commit_sha"),
        "analysis_code_version": analysis_code_version(),
        "analysis_schema_version": ANALYSIS_SCHEMA_VERSION,
        "baseline_content_address": baseline.get("content_address"),
        "analysis": analysis,
    }


def markdown_report(report: Mapping[str, Any]) -> str:
    analysis = report["analysis"]
    composition = analysis["dataset_composition"]
    shadow = analysis["shadow_metrics"]
    low_risk = analysis["low_risk_region"]
    decision = analysis["v2_decision"]
    gate = analysis["objective_gate_baseline"]
    blocking_lines = [
        f"- `{name}`: {decision.get('gates', {}).get(name, {})}"
        for name in decision.get("blocking_gates", [])
    ] or ["- none"]
    passing_lines = [f"- `{name}`" for name in decision.get("passing_gates", [])] or ["- none"]
    lines = [
        "# VS-V1.2 Real-Task Evidence Report",
        "",
        "## Executive conclusion",
        "",
        f"**Decision:** `{decision['decision']}`",
        "",
        *[f"- {reason}" for reason in decision["reasons"]],
        "",
        "### Blocking gates",
        "",
        *blocking_lines,
        "",
        "### Passing gates",
        "",
        *passing_lines,
        "",
        f"- Decision gate: `{decision.get('decision_gate_id', 'unknown')}` ({decision.get('decision_gate_kind', 'research heuristic')})",
        "",
        f"- Experiment: `{report['experiment_id']}` cohort `{report['cohort_id']}`",
        f"- Baseline: `{report['baseline_id']}` `{report['baseline_content_address']}`",
        f"- Dataset: `{report['dataset_id']}` v`{report['dataset_version']}` split `{report['split_version']}`",
        f"- Analysis scope: `{analysis.get('analysis_scope', 'operational')}`",
        f"- Holdout state: `{analysis.get('holdout_state', 'sealed')}`",
        f"- Calibration state: `{analysis.get('calibration_state', 'sealed')}`",
        f"- Protected partitions: {analysis.get('protected_partition_status', {})}",
        f"- Sealed partition counts (no outcome labels): {analysis.get('sealed_partition_counts', {})}",
        f"- Baseline reconstructability: see validate-baseline (`content_match` / `source_reconstructable` / `git_commit_match`)",
        f"- Adjudication modes: {analysis.get('adjudication_modes', {})}",
        f"- Isolation: sequential fixture evaluation must leave no child workers; hosted Linux semaphore warnings remain environment-specific",
        f"- Git revision: `{report['git_revision']}`",
        f"- Analysis code: `{report['analysis_code_version']}`",
        "",
        "## Dataset composition",
        "",
        f"- N total: {composition['n_total']}",
        f"- N real: {composition['n_real']}",
        f"- N real determinate: {composition.get('n_real_determinate', 0)}",
        f"- N controlled/synthetic: {composition['n_controlled_or_synthetic']}",
        f"- N determinate: {composition['n_determinate']}",
        f"- N accepted: {composition['n_accepted']}",
        f"- N rejected: {composition['n_rejected']}",
        f"- N unknown: {composition['n_unknown']}",
        f"- N infrastructure error: {composition['n_infrastructure_error']}",
        f"- Repositories: {', '.join(composition['repositories']) or 'none'}",
        f"- Task families: {len(composition['task_families'])}",
        f"- Producer families: {', '.join(composition['producer_families']) or 'none'}",
        f"- Patch sizes: {composition['patch_size_distribution']}",
        f"- Oracle types: {', '.join(composition['oracle_types']) or 'none'}",
        f"- Partition sizes: {composition['partition_sizes']}",
        "",
        "## Data-quality status",
        "",
        f"- Validator ok: `{analysis['data_quality']['ok']}`",
        f"- Blocking failures: {analysis['data_quality']['blocking'] or 'none'}",
        f"- Quality flags: {analysis['data_quality']['quality'] or 'none'}",
        "",
        "## Hard-verifier outcomes",
        "",
        *[f"- `{key}`: {value}" for key, value in analysis["hard_verifier_outcomes"].items()],
        "",
        "## Criterion-level checklet quality",
        "",
        "| Checklet | N applicable | N adjudicated | N indeterminate | Precision | Recall | FPR | FNR | Abstention | Unique criterion catches | P(reject\\|clean) | P(reject\\|finding) | Lift | Mean cost | p95 latency |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    latency = analysis["cost_and_latency"]["per_checklet_latency_ms"]
    cost = analysis["cost_and_latency"]["per_checklet_cost"]
    for checklet_id in CHECKLET_IDS:
        criterion = analysis["criterion_quality"][checklet_id]
        predictive = analysis["predictive_utility"][checklet_id]
        clean = predictive["p_hard_reject_given_clean"]
        finding = predictive["p_hard_reject_given_finding"]
        lines.append(
            "| {checklet} | {n_app} | {n_adj} | {n_ind} | {prec} | {rec} | {fpr} | {fnr} | {abs_rate} | {uniq} | {p_clean} | {p_find} | {lift} | {mean_cost} | {p95} |".format(
                checklet=checklet_id,
                n_app=criterion["n_applicable"],
                n_adj=criterion["n_adjudicated"],
                n_ind=criterion["n_indeterminate"],
                prec=_fmt_rate(criterion["criterion_precision"], criterion["true_positive"], criterion["true_positive"] + criterion["false_positive"]),
                rec=_fmt_rate(criterion["criterion_recall"], criterion["true_positive"], criterion["true_positive"] + criterion["false_negative"]),
                fpr=_fmt_rate(criterion["criterion_false_positive_rate"], criterion["false_positive"], criterion["false_positive"] + criterion["true_negative"]),
                fnr=_fmt_rate(criterion["criterion_false_negative_rate"], criterion["false_negative"], criterion["false_negative"] + criterion["true_positive"]),
                abs_rate=_fmt_rate(criterion["criterion_abstention_rate"]),
                uniq=criterion["unique_criterion_catches"],
                p_clean=clean["display"],
                p_find=finding["display"],
                lift="n/a" if predictive["absolute_rejection_rate_difference"] is None else f"{predictive['absolute_rejection_rate_difference']:.4f}",
                mean_cost=cost[checklet_id]["mean"],
                p95=latency[checklet_id]["p95"],
            )
        )
    lines.extend(
        [
            "",
            "Criterion metrics measure whether each checklet detects its declared criterion.",
            "Hard-outcome metrics measure association with independent verifier rejection, not criterion correctness.",
            "",
            "## Hard-outcome predictive utility",
            "",
            "Predictive lift is an observational association, not a causal claim.",
            "",
        ]
    )
    for checklet_id in CHECKLET_IDS:
        predictive = analysis["predictive_utility"][checklet_id]
        lines.append(
            f"- `{checklet_id}` unique hard-reject signals: {predictive['hard_reject_unique_signal']}; "
            f"relative lift: {predictive['relative_lift']}"
        )
    after_gates = gate["after_objective_gates_pass"]
    after_clean = gate["after_gates_pass_and_all_checklets_clean"]
    lines.extend(
        [
            "",
            "## Objective-gate baseline",
            "",
            f"- Hard rejection after objective gates pass: {after_gates['display']} interval {_fmt_interval(after_gates['interval'])}",
            f"- Hard rejection after gates pass + all checklets clean: {after_clean['display']} interval {_fmt_interval(after_clean['interval'])}",
            "",
            "## Cross-checklet dependence",
            "",
            f"- Jaccard overlap: {analysis['cross_checklet_dependence']['jaccard_overlap']}",
            f"- Phi correlation: {analysis['cross_checklet_dependence']['phi_correlation']}",
            "",
            "## Low-risk-region analysis",
            "",
            f"- Definition: {low_risk['definition']}",
            f"- N: {low_risk['n']}; coverage: {low_risk['coverage']}",
            f"- Rejects: {low_risk['reject_display']} interval {_fmt_interval(low_risk['interval'])}",
            f"- Strata: repos={low_risk['repository_distribution']} types={low_risk['task_type_distribution']} "
            f"producers={low_risk['producer_distribution']} sizes={low_risk['patch_size_distribution']}",
            f"- Robustness: {low_risk['generalization_note']}",
            "",
            "## Shadow-policy counterfactual metrics",
            "",
            f"- N total / determinate / unknown / infra: {shadow['n_total']} / {shadow['n_determinate']} / {shadow['n_unknown']} / {shadow['n_infrastructure_error']}",
            f"- Would waive: {shadow['n_would_waive']} (determinate {shadow['n_determinate_would_waive']})",
            f"- False shadow waives: {shadow['false_shadow_waive_display']}",
            f"- Shadow waiver coverage: {shadow['shadow_waiver_coverage']}",
            f"- Observed miss rate: {shadow['observed_miss_rate']} interval {_fmt_interval(shadow['observed_miss_interval'])}",
            f"- Would hard-verify: {shadow['n_would_hard_verify']}",
            f"- Unnecessary shadow verifies: {shadow['unnecessary_verify_display']}",
            "",
            "## Stratified results",
            "",
        ]
    )
    for name, rows in analysis["stratified_results"].items():
        lines.append(f"### {name}")
        lines.append("")
        for row in rows:
            rate = row["display"] if row["note"] == "descriptive only" else f"{row['display']} rate={row['rate']}"
            lines.append(f"- `{row['value']}`: {rate} ({row['note']})")
        lines.append("")
    cost_block = analysis["cost_and_latency"]
    lines.extend(
        [
            "## Cost/latency",
            "",
            f"- Gate latency mean ms: {cost_block['objective_gate_latency_ms']['mean']}",
            f"- Checklet bundle latency mean ms: {cost_block['total_checklet_bundle_latency_ms']['mean']}",
            f"- Hard-verifier latency mean ms: {cost_block['hard_verifier_latency_ms']['mean']}",
            f"- Counterfactual selective-verification economics: {cost_block['counterfactual_expected_cost']['status']} / {cost_block['counterfactual_expected_cost']['authorization']}",
            "",
            "## Unknown/infrastructure outcomes",
            "",
            f"- Unknown: {shadow['n_unknown']} rate={shadow['unknown_outcome_rate']}",
            f"- Infrastructure error: {shadow['n_infrastructure_error']} rate={shadow['infrastructure_error_rate']}",
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in analysis["limitations"]],
            "",
            "## V2 decision gate",
            "",
            f"`{decision['decision']}`",
            "",
            *[f"- {reason}" for reason in decision["reasons"]],
            "",
            "This decision does not authorize production selective verification or V2 model training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_v12_report(report: Mapping[str, Any], report_dir: Path) -> dict[str, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "v12_latest.json"
    markdown_path = report_dir / "v12_latest.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def report_from_dataset_path(
    dataset_path: Path,
    report_dir: Path,
    *,
    scope: AnalysisScope | str = AnalysisScope.OPERATIONAL,
    unseal_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from .dataset import load_dataset

    dataset = load_dataset(dataset_path)
    report = build_report(dataset, scope=scope, unseal_receipt=unseal_receipt)
    locations = write_v12_report(report, report_dir)
    return {"report": report, "artifacts": {key: str(value) for key, value in locations.items()}}


def replay_record(record: RealTaskEvidenceRecord, mode: str) -> dict[str, Any]:
    from .evaluation import replay_run_record
    from .ingestion import ingest_task_manifest

    if mode == "analysis-only":
        return {"replay_mode": mode, "record_id": record.record_id, "hard_outcome": record.hard_outcome.value}
    if mode == "frozen-observation":
        if not record.candidate_bytes_b64:
            raise ValueError(f"{FailureCode.MISSING_IDENTITY.value}: candidate bytes required for frozen replay")
        v1 = {
            "schema_version": record.component_versions.get("evaluation_schema") or "verification-v1-evaluation/1.0.0",
            "run_id": record.run_id,
            "task": record.task_contract,
            "artifact": {
                "artifact_id": record.candidate_id,
                "artifact_digest": record.candidate_patch_digest,
                "artifact_type": "coding_patch",
                "artifact_version": f"sha256:{record.candidate_patch_digest[:16]}",
                "run_id": record.run_id,
                "created_at": record.created_at,
                "metadata": {},
            },
            "artifact_content_b64": record.candidate_bytes_b64,
            "hard_verifier_result": dict(record.hard_verifier_result),
            "component_versions": dict(record.component_versions),
        }
        # Frozen V1.1 replay re-runs gates/checklets/shadow against recorded hard outcome.
        replayed = replay_run_record(v1)
        return {"replay_mode": mode, "run_id": replayed.run_id, "final_outcome": replayed.final_outcome.value}
    if mode == "full":
        manifest = {
            "task": record.task_contract,
            "artifact": {
                "artifact_id": record.candidate_id,
                "artifact_type": "coding_patch",
                "content": __import__("base64").b64decode(record.candidate_bytes_b64).decode("utf-8"),
                "metadata": {},
            },
            "reference_files": dict(record.oracle_files),
            "task_origin": record.task_origin.value,
            "task_family_id": record.task_family_id,
            "repository_id": record.repository_id,
            "candidate_lineage_id": record.candidate_lineage_id,
        }
        # A full replay must re-run the oracle that produced the recorded verdict.
        # The default used to be a hardcoded `sys.exit(0)` stub, and the recovery
        # below was gated on an unrelated condition and read a metadata key nothing
        # wrote -- so a record whose oracle rejected the candidate replayed as
        # accepted, exit 0. There is no safe default here: without the recorded
        # command there is nothing to replay against.
        command = (record.hard_verifier_result.get("metadata") or {}).get("command")
        if not command:
            raise ValueError(
                f"{FailureCode.ORACLE_UNAVAILABLE.value}: record {record.record_id} has no recorded "
                "hard-verifier command; a full replay cannot be performed without one"
            )
        manifest["hard_command"] = list(command)
        ingested = ingest_task_manifest(manifest)
        return {"replay_mode": mode, "record_id": ingested.record_id, "hard_outcome": ingested.hard_outcome.value}
    raise ValueError(f"unknown replay_mode: {mode}")
