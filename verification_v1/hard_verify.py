"""Authoritative hard-verifier adapters; no adapter treats uncertainty as acceptance."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Mapping, Protocol, Sequence

from .artifacts import RegisteredArtifact
from .bundle import BundleParseError, materialize_coding_bundle, parse_coding_bundle
from .contracts import HardVerifierOutcome, HardVerifierResult, TaskContract, utc_now


def _file_digest(path: str) -> str:
    with open(path, "rb") as stream:
        return sha256(stream.read()).hexdigest()


class HardVerifier(Protocol):
    verifier_id: str
    version: str

    def verify(self, task: TaskContract, artifact: RegisteredArtifact) -> HardVerifierResult: ...


class StaticHardVerifier:
    """Test adapter only. Production callers should supply a command/reference verifier."""

    verifier_id = "static-test-oracle"
    version = "1.0.0"

    def __init__(self, outcome: HardVerifierOutcome) -> None:
        self.outcome = outcome

    def verify(self, task: TaskContract, artifact: RegisteredArtifact) -> HardVerifierResult:
        now = utc_now()
        return HardVerifierResult(
            verifier_id=self.verifier_id,
            verifier_version=self.version,
            artifact_digest=artifact.artifact_digest,
            outcome=self.outcome,
            defect_refs=(),
            evidence_refs=("static-test-oracle",),
            oracle_class="test_adapter",
            oracle_applicability="test_only",
            started_at=now,
            completed_at=now,
            latency_ms=0.0,
            cost={"kind": "actual_cost", "amount": 0.0, "currency": "USD"},
        )


class FixtureHardVerifier:
    """Independent fixture oracle: labels remain outside candidate/checklet context."""

    verifier_id = "fixture-reference-oracle"
    version = "1.0.0"

    def __init__(self, outcomes: Mapping[str, HardVerifierOutcome]) -> None:
        self._outcomes = dict(outcomes)

    def verify(self, task: TaskContract, artifact: RegisteredArtifact) -> HardVerifierResult:
        started = utc_now()
        timer = perf_counter()
        fixture_id = artifact.ref.metadata.get("fixture_id")
        outcome = self._outcomes.get(artifact.artifact_digest, HardVerifierOutcome.OUTCOME_UNKNOWN)
        return HardVerifierResult(
            verifier_id=self.verifier_id,
            verifier_version=self.version,
            artifact_digest=artifact.artifact_digest,
            outcome=outcome,
            defect_refs=(),
            evidence_refs=(f"fixture-reference:{fixture_id}:{artifact.artifact_digest}",),
            oracle_class="executable_reference_fixture",
            oracle_applicability="fixture_acceptance",
            started_at=started,
            completed_at=utc_now(),
            latency_ms=(perf_counter() - timer) * 1000,
            cost={"kind": "actual_cost", "amount": 0.0, "currency": "USD"},
        )


class UnavailableHardVerifier:
    """Explicitly unavailable oracle; never treated as acceptance."""

    verifier_id = "unavailable-reference-oracle"
    version = "1.1.0"

    def verify(self, task: TaskContract, artifact: RegisteredArtifact) -> HardVerifierResult:
        now = utc_now()
        return HardVerifierResult(
            verifier_id=self.verifier_id,
            verifier_version=self.version,
            artifact_digest=artifact.artifact_digest,
            outcome=HardVerifierOutcome.OUTCOME_UNKNOWN,
            defect_refs=(),
            evidence_refs=("oracle_unavailable",),
            oracle_class="unavailable_reference",
            oracle_applicability="unavailable",
            started_at=now,
            completed_at=now,
            latency_ms=0.0,
            cost={"kind": "unknown_cost"},
        )


class CommandHardVerifier:
    """Runs an independently configured command against a materialized immutable artifact."""

    verifier_id = "command-hard-verifier"
    version = "1.1.0"

    def __init__(
        self,
        command: Sequence[str],
        timeout_seconds: float = 30.0,
        extra_files: Mapping[str, str] | None = None,
    ) -> None:
        if not command:
            raise ValueError("hard verifier command is required")
        self.command = tuple(command)
        self.timeout_seconds = timeout_seconds
        self.extra_files = {str(path): str(content) for path, content in dict(extra_files or {}).items()}

    def verify(self, task: TaskContract, artifact: RegisteredArtifact) -> HardVerifierResult:
        started = utc_now()
        timer = perf_counter()
        with tempfile.TemporaryDirectory(prefix="verification-v1-") as directory:
            artifact_path = os.path.join(directory, "candidate.artifact")
            workspace = os.path.join(directory, "workspace")
            with open(artifact_path, "wb") as stream:
                stream.write(artifact.content)
            materialized_digest = _file_digest(artifact_path)
            if materialized_digest != artifact.artifact_digest:
                raise RuntimeError("materialized artifact digest does not match registered artifact")
            # The command receives a read-only snapshot. Rehashing after it completes
            # detects replacement even if the command changes permissions on its own copy.
            os.chmod(artifact_path, 0o444)
            os.makedirs(workspace, exist_ok=True)
            try:
                bundle = parse_coding_bundle(artifact.content, artifact.ref.metadata)
                candidate_paths = set(bundle.patched_files)
                overlap = sorted(path for path in self.extra_files if path in candidate_paths)
                if overlap:
                    raise RuntimeError(
                        "reference oracle files cannot replace candidate files: " + ", ".join(overlap)
                    )
                materialize_coding_bundle(bundle, Path(workspace))
            except (BundleParseError, OSError, UnicodeDecodeError, RuntimeError) as exc:
                if isinstance(exc, RuntimeError) and "cannot replace candidate files" in str(exc):
                    raise
            self._write_extra_files(Path(workspace))
            command = [
                part.replace("{artifact_path}", artifact_path)
                .replace("{workspace}", workspace)
                .replace("{python}", sys.executable)
                for part in self.command
            ]
            env = os.environ.copy()
            # The oracle is meant to be independently configured. Inheriting the
            # parent's PYTHONPATH lets the calling process' import surface leak into
            # the judging interpreter, so the workspace is the only entry we add.
            # PYTHONNOUSERSITE blocks a user-site usercustomize from running;
            # bundle.RESERVED_TOP_LEVEL_MODULES blocks the in-workspace variants.
            env["PYTHONPATH"] = workspace
            env["PYTHONNOUSERSITE"] = "1"
            env["VERIFICATION_V1_WORKSPACE"] = workspace
            try:
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                    cwd=workspace,
                    env=env,
                )
                if completed.returncode == 0:
                    outcome = HardVerifierOutcome.ACCEPTED
                elif completed.returncode == 5 and "NO TESTS RAN" in (completed.stderr or "") + (completed.stdout or ""):
                    outcome = HardVerifierOutcome.INFRASTRUCTURE_ERROR
                else:
                    outcome = HardVerifierOutcome.REJECTED
                evidence = (f"command_exit:{completed.returncode}",)
                metadata = {
                    "returncode": completed.returncode,
                    "stdout": completed.stdout[-2000:],
                    "stderr": completed.stderr[-2000:],
                    "materialized_artifact_digest": materialized_digest,
                    "workspace": workspace,
                }
            except subprocess.TimeoutExpired:
                outcome, evidence, metadata = HardVerifierOutcome.OUTCOME_UNKNOWN, ("command_timeout",), {"timeout_seconds": self.timeout_seconds}
            except OSError as exc:
                outcome, evidence, metadata = HardVerifierOutcome.INFRASTRUCTURE_ERROR, ("command_infrastructure_error",), {"exception": type(exc).__name__}
            try:
                final_digest = _file_digest(artifact_path)
                if final_digest != artifact.artifact_digest:
                    outcome = HardVerifierOutcome.INFRASTRUCTURE_ERROR
                    evidence = tuple(evidence) + ("materialized_artifact_digest_mismatch",)
                    metadata = dict(metadata)
                    metadata["materialized_artifact_digest_after_command"] = final_digest
            except OSError as exc:
                outcome = HardVerifierOutcome.INFRASTRUCTURE_ERROR
                evidence = tuple(evidence) + ("materialized_artifact_integrity_unavailable",)
                metadata = dict(metadata)
                metadata["artifact_integrity_exception"] = type(exc).__name__
            finally:
                try:
                    os.chmod(artifact_path, 0o600)
                except OSError:
                    pass
        return HardVerifierResult(
            verifier_id=self.verifier_id,
            verifier_version=self.version,
            artifact_digest=artifact.artifact_digest,
            outcome=outcome,
            defect_refs=(),
            evidence_refs=evidence,
            oracle_class="external_executable_command",
            oracle_applicability="configured_task_acceptance",
            started_at=started,
            completed_at=utc_now(),
            latency_ms=(perf_counter() - timer) * 1000,
            cost={"kind": "unknown_cost"},
            metadata=metadata,
        )

    def _write_extra_files(self, workspace: Path) -> None:
        resolved_root = workspace.resolve()
        for path, content in self.extra_files.items():
            destination = resolved_root.joinpath(*path.replace("\\", "/").split("/"))
            try:
                destination.resolve().relative_to(resolved_root)
            except ValueError as exc:
                raise RuntimeError(f"reference oracle path escapes workspace: {path}") from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
