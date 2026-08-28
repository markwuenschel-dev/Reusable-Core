"""Minimal developer entry point for Verification Slice V1."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any, Sequence

from .artifacts import ArtifactStore, CandidateArtifact
from .contracts import HardVerifierOutcome, TaskContract, jsonable
from .domain import CodingDomainPack
from .evaluation import evaluate_fixture_set, replay_run_record, run_to_record, write_report
from .hard_verify import CommandHardVerifier
from .runner import VerificationRunner
from .telemetry import InMemoryEventSink, JsonlEventSink


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
    run.add_argument("--hard-command", required=True, help="quoted executable command; use {artifact_path} to inject frozen bytes")
    run.add_argument("--event-log", help="optional append-only JSONL output path")
    run.add_argument("--artifact-store", help="optional content-addressed artifact directory")

    evaluate = commands.add_parser("evaluate", help="evaluate the engineering fixture set")
    evaluate.add_argument("fixture_set", help="fixture-set JSON")
    evaluate.add_argument("--report-dir", default="reports/verification_v1", help="directory for latest.json and latest.md")

    replay = commands.add_parser("replay", help="replay a run record with a recorded hard outcome")
    replay.add_argument("record", help="run-record JSON object")

    commands.add_parser("list-checklets", help="list the registered coding-domain checklets")
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
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
