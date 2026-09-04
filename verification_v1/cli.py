"""Minimal developer entry point for Verification Slice V1."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any, Sequence

from .artifacts import ArtifactStore, CandidateArtifact
from .baseline import validate_baseline, write_baseline
from .contracts import HardVerifierOutcome, TaskContract, jsonable
from .dataset import append_records, empty_dataset, freeze_dataset, load_dataset, write_dataset
from .domain import CodingDomainPack
from .evaluation import evaluate_fixture_set, replay_run_record, run_to_record, write_report
from .evidence import RealTaskEvidenceRecord, ReplayMode
from .hard_verify import CommandHardVerifier
from .ingestion import fixture_to_manifest, ingest_task_manifest
from .integrity import validate_dataset_records
from .runner import VerificationRunner
from .telemetry import InMemoryEventSink, JsonlEventSink
from .v12_report import report_from_dataset_path, replay_record


def _emit_json(payload: Any) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _load_json(path: str) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def _task_from_json(payload: dict[str, Any]) -> TaskContract:
    return TaskContract(
        task_id=str(payload["task_id"]),
        requirements=tuple(str(item) for item in payload.get("requirements", [])),
        description=str(payload.get("description", "")),
        version=str(payload.get("version", "1.0.0")),
        metadata=dict(payload.get("metadata", {})),
    )


def _artifact_from_json(payload: dict[str, Any]) -> CandidateArtifact:
    return CandidateArtifact.from_text(
        artifact_id=str(payload["artifact_id"]),
        artifact_type=str(payload["artifact_type"]),
        content=str(payload["content"]),
        metadata=dict(payload.get("metadata", {})),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="verification-v1", description="Run the VS-V1 experimental verification slice.")
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="run gates/checklets and an explicitly configured hard verifier")
    run.add_argument("task", help="task-contract JSON object")
    run.add_argument("artifact", help="artifact JSON object")
    run.add_argument("--hard-command", required=True, help="quoted executable command; use {artifact_path}, {workspace}, or {python}")
    run.add_argument("--event-log", help="optional append-only JSONL output path")
    run.add_argument("--artifact-store", help="optional content-addressed artifact directory")

    evaluate = commands.add_parser("evaluate", help="evaluate the engineering fixture set")
    evaluate.add_argument("fixture_set", help="fixture-set JSON")
    evaluate.add_argument("--report-dir", default="reports/verification_v1", help="directory for latest.json and latest.md")

    replay = commands.add_parser("replay", help="replay a run record with a recorded hard outcome")
    replay.add_argument("record", help="run-record JSON object")

    commands.add_parser("list-checklets", help="list the registered coding-domain checklets")

    validate_baseline_cmd = commands.add_parser("validate-baseline", help="validate the frozen VS-V1.1 baseline manifest")
    validate_baseline_cmd.add_argument("--write", action="store_true", help="write the live baseline manifest if missing")

    ingest = commands.add_parser("ingest-fixture-set", help="ingest fixtures into a V1.2 evidence dataset")
    ingest.add_argument("fixture_set", help="fixture-set JSON")
    ingest.add_argument("--dataset-out", required=True, help="output dataset JSON")
    ingest.add_argument("--freeze", action="store_true", help="freeze the dataset after ingestion")

    adjudicate = commands.add_parser("adjudicate", help="independently adjudicate criteria for a task/artifact pair")
    adjudicate.add_argument("task", help="task-contract JSON object")
    adjudicate.add_argument("artifact", help="artifact JSON object")

    validate_dataset_cmd = commands.add_parser("validate-dataset", help="fail-closed V1.2 dataset validation")
    validate_dataset_cmd.add_argument("dataset", help="dataset JSON")

    analyze = commands.add_parser("analyze-v12", help="analyze a validated V1.2 dataset and write v12 reports")
    analyze.add_argument("dataset", help="dataset JSON")
    analyze.add_argument("--report-dir", default="reports/verification_v1", help="directory for v12_latest.json and v12_latest.md")
    analyze.add_argument("--scope", default="operational", choices=["operational", "policy-selection", "calibration", "final-holdout"])
    analyze.add_argument("--unseal-receipt", help="persisted unseal receipt JSON; required only if the dataset is not already unsealed")

    report = commands.add_parser("report-v12", help="regenerate V1.2 reports from a frozen dataset")
    report.add_argument("dataset", help="dataset JSON")
    report.add_argument("--report-dir", default="reports/verification_v1")
    report.add_argument("--scope", default="operational", choices=["operational", "policy-selection", "calibration", "final-holdout"])
    report.add_argument("--unseal-receipt", help="persisted unseal receipt JSON")

    finalize = commands.add_parser("finalize-holdout", help="persist one-way holdout unseal on a dataset after freezing analysis rules")
    finalize.add_argument("--receipt-out", required=True, help="output unseal receipt JSON")
    finalize.add_argument("--dataset", help="dataset JSON to mark holdout_state=final_unsealed")

    unseal_cal = commands.add_parser("unseal-calibration", help="persist calibration_reserved unseal; not for ordinary V1.2 analysis")
    unseal_cal.add_argument("--receipt-out", required=True)
    unseal_cal.add_argument("--dataset", help="dataset JSON to mark calibration_state=unsealed")

    stress = commands.add_parser("stress-isolation", help="repeat fixture evaluation in one interpreter and assert no leftover children")
    stress.add_argument("--iterations", type=int, default=3)
    stress.add_argument("--fixture-set", default="evals/verification_v1/engineering_fixture_set.json")

    replay_v12 = commands.add_parser("replay-v12", help="replay a V1.2 evidence record")
    replay_v12.add_argument("record", help="evidence-record JSON object")
    replay_v12.add_argument("--mode", default="analysis-only", choices=[item.value for item in ReplayMode])
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "list-checklets":
            pack = CodingDomainPack.default()
            payload = {
                "domain_pack": pack.pack_id,
                "version": pack.version,
                "checklets": [spec.to_dict() for spec in pack.build_checklet_registry().specs],
            }
            _emit_json(payload)
            return 0
        if args.command == "run":
            task = _task_from_json(_load_json(args.task))
            artifact = _artifact_from_json(_load_json(args.artifact))
            event_sink = JsonlEventSink(Path(args.event_log)) if args.event_log else InMemoryEventSink()
            store = ArtifactStore(Path(args.artifact_store)) if args.artifact_store else ArtifactStore()
            hard_command = tuple(shlex.split(args.hard_command, posix=True))
            if not hard_command:
                raise ValueError("--hard-command cannot be empty")
            result = VerificationRunner.default(event_sink=event_sink, artifact_store=store).run(
                task, artifact, CommandHardVerifier(hard_command)
            )
            _emit_json(run_to_record(result))
            return 0 if result.final_outcome == HardVerifierOutcome.ACCEPTED else 1
        if args.command == "evaluate":
            report = evaluate_fixture_set(Path(args.fixture_set))
            locations = write_report(report, Path(args.report_dir))
            _emit_json({"report": report.to_dict(), "artifacts": {key: str(value) for key, value in locations.items()}})
            return 0
        if args.command == "replay":
            replay = replay_run_record(_load_json(args.record))
            _emit_json(run_to_record(replay))
            return 0 if replay.final_outcome == HardVerifierOutcome.ACCEPTED else 1
        if args.command == "validate-baseline":
            from .baseline import baseline_manifest_path

            manifest = baseline_manifest_path()
            if args.write or not manifest.exists():
                write_baseline(manifest)
            result = validate_baseline()
            _emit_json(
                {
                    "ok": result["ok"],
                    "errors": result["errors"],
                    "baseline_id": result.get("baseline_id"),
                    "content_address": result["content_address"],
                    "frozen_id": result["frozen_id"],
                    "content_match": result.get("content_match"),
                    "source_reconstructable": result.get("source_reconstructable"),
                    "snapshot_reconstructable": result.get("snapshot_reconstructable"),
                    "snapshot_tracked": result.get("snapshot_tracked"),
                    "git_commit_match": result.get("git_commit_match"),
                    "tree_match": result.get("tree_match"),
                    "git_reconstructable": result.get("git_reconstructable"),
                    "collection_ready": result.get("collection_ready"),
                    "git_note": result.get("git_note"),
                }
            )
            return 0 if result["ok"] else 1
        if args.command == "ingest-fixture-set":
            payload = json.loads(Path(args.fixture_set).read_text(encoding="utf-8"))
            dataset = empty_dataset()
            records = [ingest_task_manifest(fixture_to_manifest(fixture)) for fixture in payload.get("fixtures", [])]
            dataset = append_records(dataset, records, note=f"ingest {args.fixture_set}")
            if args.freeze:
                dataset = freeze_dataset(dataset)
            write_dataset(dataset, Path(args.dataset_out))
            _emit_json({"dataset": args.dataset_out, "n_records": len(dataset.records), "frozen": dataset.frozen})
            return 0
        if args.command == "adjudicate":
            from hashlib import sha256

            from .adjudication import adjudicate_artifact_bytes
            from .artifacts import canonical_artifact_bytes
            from .independent_adjudication import expert_adjudication_form, independent_adjudicate_artifact_bytes

            task = _task_from_json(_load_json(args.task))
            artifact_payload = _load_json(args.artifact)
            content = canonical_artifact_bytes(str(artifact_payload["content"]).encode("utf-8"))
            digest = sha256(content).hexdigest()
            metadata = dict(artifact_payload.get("metadata", {}))
            secondary = adjudicate_artifact_bytes(task, content, digest, metadata)
            evaluation_grade = independent_adjudicate_artifact_bytes(task, content, digest, metadata)
            _emit_json(
                {
                    "artifact_digest": digest,
                    "secondary_adjudications": [item.to_dict() for item in secondary],
                    "evaluation_grade_adjudications": [item.to_dict() for item in evaluation_grade],
                    "expert_form": expert_adjudication_form(task, digest),
                }
            )
            return 0
        if args.command == "validate-dataset":
            dataset = load_dataset(Path(args.dataset))
            result = validate_dataset_records(dataset.records)
            _emit_json(result)
            return 0 if result["ok"] else 1
        if args.command in {"analyze-v12", "report-v12"}:
            receipt = _load_json(args.unseal_receipt) if getattr(args, "unseal_receipt", None) else None
            payload = report_from_dataset_path(
                Path(args.dataset),
                Path(args.report_dir),
                scope=args.scope,
                unseal_receipt=receipt,
            )
            _emit_json(
                {
                    "decision": payload["report"]["analysis"]["v2_decision"]["decision"],
                    "n_records": payload["report"]["analysis"]["n_records_analyzed"],
                    "analysis_scope": payload["report"]["analysis"].get("analysis_scope"),
                    "artifacts": payload["artifacts"],
                }
            )
            return 0
        if args.command in {"finalize-holdout", "unseal-calibration"}:
            from .baseline import collect_baseline
            from .dataset import persist_partition_unseal, write_dataset
            from .splits import build_unseal_receipt
            from .v12_report import analysis_code_version

            live = collect_baseline()
            receipt = build_unseal_receipt(
                baseline_content_address=str(live["content_address"]),
                analysis_code_version=analysis_code_version(),
                checklet_implementation_hash=str(live["implementation_hashes"]["verification_v1/checklets.py"]),
                shadow_policy=f"{live['shadow_policy']['id']}/{live['shadow_policy']['version']}",
                git_commit=str(live.get("repository_commit_sha") or ""),
            )
            destination = Path(args.receipt_out)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            target = "holdout" if args.command == "finalize-holdout" else "calibration"
            dataset_path = getattr(args, "dataset", None)
            if dataset_path:
                dataset = persist_partition_unseal(load_dataset(Path(dataset_path)), receipt, target=target)
                write_dataset(dataset, Path(dataset_path))
            _emit_json(
                {
                    "receipt": str(destination),
                    "unsealed_at": receipt["unsealed_at"],
                    "target": target,
                    "dataset": dataset_path,
                    "holdout_state": None if not dataset_path else dataset.holdout_state,
                    "calibration_state": None if not dataset_path else dataset.calibration_state,
                }
            )
            return 0
        if args.command == "stress-isolation":
            from .isolation_stress import stress_fixture_evaluation

            payload = stress_fixture_evaluation(Path(args.fixture_set), int(args.iterations))
            _emit_json(payload)
            return 0 if payload.get("ok") else 1
        if args.command == "replay-v12":
            record = RealTaskEvidenceRecord.from_dict(_load_json(args.record))
            _emit_json(replay_record(record, args.mode))
            return 0
    except (KeyError, OSError, ValueError, json.JSONDecodeError, PermissionError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
