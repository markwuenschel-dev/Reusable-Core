"""Cheap, explicit objective gates for coding artifacts."""

from __future__ import annotations

from time import perf_counter
from typing import Protocol

from .artifacts import RegisteredArtifact
from .contracts import GateResult, GateStatus, Severity, TaskContract, utc_now


class ObjectiveGate(Protocol):
    gate_id: str
    version: str

    def evaluate(self, task: TaskContract, artifact: RegisteredArtifact) -> GateResult: ...


class MetadataShapeGate:
    gate_id = "coding_metadata_shape"
    version = "1.0.0"

    def evaluate(self, task: TaskContract, artifact: RegisteredArtifact) -> GateResult:
        started = utc_now()
        timer = perf_counter()
        changed_paths = artifact.ref.metadata.get("changed_paths")
        if not isinstance(changed_paths, (list, tuple)):
            status, severity, details = GateStatus.ERROR, Severity.HIGH, {"reason": "changed_paths must be a sequence"}
        else:
            status, severity, details = GateStatus.PASS, Severity.INFO, {"checked": "changed_paths"}
        return GateResult(
            gate_id=self.gate_id,
            gate_version=self.version,
            artifact_digest=artifact.artifact_digest,
            status=status,
            severity=severity,
            started_at=started,
            completed_at=utc_now(),
            latency_ms=(perf_counter() - timer) * 1000,
            details=details,
        )


class GateRunner:
    def __init__(self, gates: tuple[ObjectiveGate, ...]) -> None:
        self.gates = gates

    def run_all(self, task: TaskContract, artifact: RegisteredArtifact) -> tuple[GateResult, ...]:
        results: list[GateResult] = []
        for gate in self.gates:
            try:
                results.append(gate.evaluate(task, artifact))
            except Exception as exc:  # Gates must record unexpected failure explicitly.
                now = utc_now()
                results.append(
                    GateResult(
                        gate_id=getattr(gate, "gate_id", "unknown_gate"),
                        gate_version=getattr(gate, "version", "unknown"),
                        artifact_digest=artifact.artifact_digest,
                        status=GateStatus.ERROR,
                        severity=Severity.HIGH,
                        started_at=now,
                        completed_at=now,
                        latency_ms=0,
                        details={"exception": type(exc).__name__},
                    )
                )
        return tuple(results)
