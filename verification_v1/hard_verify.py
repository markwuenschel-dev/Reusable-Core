"""Authoritative hard-verifier adapters; no adapter treats uncertainty as acceptance."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Protocol, Sequence

from .artifacts import RegisteredArtifact
from .bundle import BundleParseError, materialize_coding_bundle, parse_coding_bundle
from .contracts import HardVerifierOutcome, HardVerifierResult, TaskContract, utc_now

# Conventional "no tests were collected" exit status. Detecting this structurally
# rather than by matching a runner's human-readable output keeps an infrastructure
# failure from being reclassified as a candidate rejection when wording changes.
_NO_TESTS_COLLECTED_EXIT = 5


def _file_digest(path: str) -> str:
    with open(path, "rb") as stream:
        return sha256(stream.read()).hexdigest()


def _surface_digests(root: Path, relative_paths: Sequence[str]) -> dict[str, str | None]:
    """Digest exactly the files this verifier placed in the workspace.

    Hashing the whole tree would flag ordinary by-products such as __pycache__;
    the surface that must not change is the candidate and oracle files.
    """
    digests: dict[str, str | None] = {}
    for relative in sorted(set(relative_paths)):
        target = root.joinpath(*str(relative).replace("\\", "/").split("/"))
        try:
            digests[str(relative)] = _file_digest(str(target))
        except OSError:
            digests[str(relative)] = None
    return digests


def _kill_process_tree(process: "subprocess.Popen[bytes]") -> None:
    """Terminate the command and everything it spawned.

    timeout_seconds is supposed to bound the whole verification, but killing
    only the direct child leaves orphaned grandchildren running inside the
    workspace that is about to be deleted.
    """
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                capture_output=True,
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass
    try:
        process.kill()
    except OSError:
        pass
    try:
        process.wait(timeout=10)
    except subprocess.SubprocessError:
        pass


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

    def _run_bounded(
        self, command: list[str], workspace: str, env: Mapping[str, str], directory: str
    ) -> tuple[int, str, str]:
        """Run the oracle under a real wall-clock bound.

        stdout/stderr go to files rather than pipes: a pipe is inherited by every
        descendant, so a grandchild outliving its parent kept the verifier blocked
        on EOF long past timeout_seconds. The command also gets its own process
        group so a timeout can kill the whole tree rather than just the child.
        """
        out_path = os.path.join(directory, "command.stdout")
        err_path = os.path.join(directory, "command.stderr")
        popen_kwargs: dict[str, Any] = {}
        if os.name == "nt":
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_kwargs["start_new_session"] = True
        with open(out_path, "wb") as out_stream, open(err_path, "wb") as err_stream:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=out_stream,
                stderr=err_stream,
                cwd=workspace,
                env=dict(env),
                **popen_kwargs,
            )
            try:
                returncode = process.wait(timeout=self.timeout_seconds)
            except subprocess.TimeoutExpired:
                _kill_process_tree(process)
                raise
            finally:
                if process.poll() is None:
                    _kill_process_tree(process)

        def _read(path: str) -> str:
            try:
                with open(path, "rb") as stream:
                    return stream.read().decode("utf-8", errors="replace")
            except OSError:
                return ""

        return returncode, _read(out_path), _read(err_path)

    def _result(
        self,
        artifact: RegisteredArtifact,
        outcome: HardVerifierOutcome,
        evidence: tuple[str, ...],
        metadata: Mapping[str, Any],
        started: str,
        timer: float,
    ) -> HardVerifierResult:
        return HardVerifierResult(
            verifier_id=self.verifier_id,
            verifier_version=self.version,
            artifact_digest=artifact.artifact_digest,
            outcome=outcome,
            defect_refs=(),
            evidence_refs=tuple(evidence),
            oracle_class="external_executable_command",
            oracle_applicability="configured_task_acceptance",
            started_at=started,
            completed_at=utc_now(),
            latency_ms=(perf_counter() - timer) * 1000,
            cost={"kind": "unknown_cost"},
            metadata=dict(metadata),
        )

    def verify(self, task: TaskContract, artifact: RegisteredArtifact) -> HardVerifierResult:
        started = utc_now()
        timer = perf_counter()
        # ignore_cleanup_errors: a killed process tree can still hold handles
        # inside the workspace on Windows; a cleanup failure must not mask the
        # verdict we already computed.
        with tempfile.TemporaryDirectory(
            prefix="verification-v1-", ignore_cleanup_errors=True
        ) as directory:
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
            candidate_paths: set[str] = set()
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
                # Anything else meant the workspace was never fully built. Running
                # the oracle anyway produced a REJECTED verdict indistinguishable
                # from a genuine defect, which is exactly the uncertainty this
                # module promises never to treat as an outcome. Fail closed.
                return self._result(
                    artifact,
                    HardVerifierOutcome.INFRASTRUCTURE_ERROR,
                    ("workspace_materialization_failed",),
                    {
                        "exception": type(exc).__name__,
                        "detail": str(exc)[:500],
                        "materialized_artifact_digest": materialized_digest,
                    },
                    started,
                    timer,
                )
            self._write_extra_files(Path(workspace))
            # The executed surface is the workspace, so that is what the integrity
            # guard must attest. candidate.artifact is never opened by the command.
            attested_paths = sorted(candidate_paths | set(self.extra_files))
            before_digests = _surface_digests(Path(workspace), attested_paths)
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
                returncode, stdout, stderr = self._run_bounded(command, workspace, env, directory)
                if returncode == 0:
                    outcome = HardVerifierOutcome.ACCEPTED
                elif returncode == _NO_TESTS_COLLECTED_EXIT:
                    # Structural signal. Requiring the literal string 'NO TESTS RAN'
                    # meant a wording change silently reclassified "the oracle never
                    # ran" as "the candidate was rejected".
                    outcome = HardVerifierOutcome.INFRASTRUCTURE_ERROR
                else:
                    outcome = HardVerifierOutcome.REJECTED
                evidence = (f"command_exit:{returncode}",)
                metadata = {
                    "returncode": returncode,
                    "stdout": stdout[-2000:],
                    "stderr": stderr[-2000:],
                    "materialized_artifact_digest": materialized_digest,
                    "workspace": workspace,
                }
            except subprocess.TimeoutExpired:
                outcome, evidence, metadata = HardVerifierOutcome.OUTCOME_UNKNOWN, ("command_timeout",), {"timeout_seconds": self.timeout_seconds}
            except OSError as exc:
                outcome, evidence, metadata = HardVerifierOutcome.INFRASTRUCTURE_ERROR, ("command_infrastructure_error",), {"exception": type(exc).__name__}
            after_digests = _surface_digests(Path(workspace), attested_paths)
            if after_digests != before_digests:
                changed = sorted(
                    path for path in before_digests if before_digests[path] != after_digests.get(path)
                )
                outcome = HardVerifierOutcome.INFRASTRUCTURE_ERROR
                evidence = tuple(evidence) + ("workspace_digest_mismatch",)
                metadata = dict(metadata)
                metadata["workspace_changed_paths"] = changed
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
