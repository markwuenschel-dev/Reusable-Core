"""Authoritative hard-verifier adapters; no adapter treats uncertainty as acceptance."""

from __future__ import annotations

import os
import subprocess
import tempfile
from hashlib import sha256
from time import perf_counter
from typing import Mapping, Protocol, Sequence

from .artifacts import RegisteredArtifact
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


class CommandHardVerifier:
    """Runs an independently configured command against a materialized immutable artifact."""

    verifier_id = "command-hard-verifier"
    version = "1.0.0"

    def __init__(self, command: Sequence[str], timeout_seconds: float = 30.0) -> None:
        if not command:
            raise ValueError("hard verifier command is required")
        self.command = tuple(command)
        self.timeout_seconds = timeout_seconds

    def verify(self, task: TaskContract, artifact: RegisteredArtifact) -> HardVerifierResult:
        started = utc_now()
        timer = perf_counter()
        with tempfile.TemporaryDirectory(prefix="verification-v1-") as directory:
            artifact_path = os.path.join(directory, "candidate.artifact")
            with open(artifact_path, "wb") as stream:
                stream.write(artifact.content)
            materialized_digest = _file_digest(artifact_path)
            if materialized_digest != artifact.artifact_digest:
                raise RuntimeError("materialized artifact digest does not match registered artifact")
            # The command receives a read-only snapshot. Rehashing after it completes
            # detects replacement even if the command changes permissions on its own copy.
            os.chmod(artifact_path, 0o444)
            command = [part.replace("{artifact_path}", artifact_path) for part in self.command]
            try:
                completed = subprocess.run(command, capture_output=True, text=True, timeout=self.timeout_seconds, check=False)
                outcome = HardVerifierOutcome.ACCEPTED if completed.returncode == 0 else HardVerifierOutcome.REJECTED
                evidence = (f"command_exit:{completed.returncode}",)
                metadata = {
                    "returncode": completed.returncode,
                    "stdout": completed.stdout[-2000:],
                    "stderr": completed.stderr[-2000:],
                    "materialized_artifact_digest": materialized_digest,
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
