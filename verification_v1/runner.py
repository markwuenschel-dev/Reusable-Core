"""The VS-V1 runner: shadow assessment is recorded, hard verification is mandatory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .aggregation import ShadowAggregator
from .artifacts import ArtifactStore, CandidateArtifact, RegisteredArtifact
from .checklets import CheckletContext, CheckletRegistry, default_coding_checklets
from .contracts import (
    CheckletObservation,
    GateResult,
    HardVerifierOutcome,
    HardVerifierResult,
    ShadowComparison,
    ShadowRiskAssessment,
    TaskContract,
    compare_shadow_to_hard_verifier,
    new_id,
    utc_now,
)
from .gates import GateRunner, MetadataShapeGate
from .hard_verify import HardVerifier
from .telemetry import EventSink, InMemoryEventSink

if TYPE_CHECKING:
    from .domain import DomainPack


@dataclass(frozen=True)
class TelemetryFailure:
    """A non-authoritative record that the append-only audit sink was unavailable."""

    event_type: str
    exception_type: str

    def to_dict(self) -> dict[str, str]:
        return {"event_type": self.event_type, "exception_type": self.exception_type}


@dataclass(frozen=True)
class VerificationRun:
    run_id: str
    task: TaskContract
    artifact: RegisteredArtifact
    gates: tuple[GateResult, ...]
    observations: tuple[CheckletObservation, ...]
    shadow_assessment: ShadowRiskAssessment
    hard_verifier_result: HardVerifierResult
    comparison: ShadowComparison
    domain_pack_id: str
    domain_pack_version: str
    telemetry_failures: tuple["TelemetryFailure", ...]

    @property
    def final_outcome(self) -> HardVerifierOutcome:
        """The only final decision source; shadow state is deliberately excluded."""
        return self.hard_verifier_result.outcome


class VerificationRunner:
    version = "1.1.0"

    def __init__(
        self,
        artifact_store: ArtifactStore,
        gate_runner: GateRunner,
        checklets: CheckletRegistry,
        aggregator: ShadowAggregator,
        event_sink: EventSink,
        domain_pack_id: str = "custom",
        domain_pack_version: str = "custom",
    ) -> None:
        self.artifact_store = artifact_store
        self.gate_runner = gate_runner
        self.checklets = checklets
        self.aggregator = aggregator
        self.event_sink = event_sink
        self.domain_pack_id = domain_pack_id
        self.domain_pack_version = domain_pack_version

    @classmethod
    def default(cls, event_sink: EventSink | None = None, artifact_store: ArtifactStore | None = None) -> "VerificationRunner":
        from .domain import CodingDomainPack

        return cls.from_domain_pack(
            CodingDomainPack.default(), event_sink=event_sink, artifact_store=artifact_store
        )

    @classmethod
    def from_domain_pack(
        cls,
        domain_pack: "DomainPack",
        event_sink: EventSink | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> "VerificationRunner":
        return cls(
            artifact_store=artifact_store or ArtifactStore(),
            gate_runner=domain_pack.build_gate_runner(),
            checklets=domain_pack.build_checklet_registry(),
            aggregator=ShadowAggregator(),
            event_sink=event_sink or InMemoryEventSink(),
            domain_pack_id=domain_pack.pack_id,
            domain_pack_version=domain_pack.version,
        )

    def _emit_safely(
        self,
        failures: list["TelemetryFailure"],
        event_type: str,
        task: TaskContract,
        artifact: RegisteredArtifact,
        component_id: str,
        component_version: str,
        **payload: Any,
    ) -> None:
        """Telemetry never gains authority to interrupt the verification sequence."""
        try:
            self.event_sink.emit(event_type, task, artifact, component_id, component_version, **payload)
        except Exception as exc:  # A failing audit sink is explicit infrastructure evidence, not control flow.
            failures.append(TelemetryFailure(event_type, type(exc).__name__))

    def run(self, task: TaskContract, candidate: CandidateArtifact, hard_verifier: HardVerifier) -> VerificationRun:
        run_id = new_id("run")
        artifact = self.artifact_store.register(candidate, run_id)
        telemetry_failures: list[TelemetryFailure] = []
        self._emit_safely(telemetry_failures, "task_received", task, artifact, "verification_runner", self.version)
        self._emit_safely(telemetry_failures, "artifact_registered", task, artifact, "artifact_store", "1.0.0")

        gates = self.gate_runner.run_all(task, artifact)
        for gate in gates:
            self._emit_safely(telemetry_failures, "objective_gate_started", task, artifact, gate.gate_id, gate.gate_version)
            self._emit_safely(telemetry_failures, "objective_gate_finished", task, artifact, gate.gate_id, gate.gate_version, gate=gate.to_dict())

        context = CheckletContext(task=task, artifact=artifact)
        observations = self.checklets.run_all(context)
        for observation in observations:
            self._emit_safely(
                telemetry_failures,
                "checklet_started", task, artifact, observation.checklet_id, observation.checklet_version,
            )
            self._emit_safely(
                telemetry_failures,
                "checklet_finished", task, artifact, observation.checklet_id, observation.checklet_version,
                observation=observation.to_dict(),
            )

        shadow = self.aggregator.assess(artifact.artifact_digest, gates, observations)
        self._emit_safely(telemetry_failures, "shadow_assessment_created", task, artifact, shadow.policy_id, shadow.policy_version, assessment=shadow.to_dict())

        # This call is structurally unconditional: no shadow action returns from this method before it executes.
        self._emit_safely(telemetry_failures, "hard_verifier_started", task, artifact, hard_verifier.verifier_id, hard_verifier.version)
        try:
            hard_result = hard_verifier.verify(task, artifact)
            if hard_result.artifact_digest != artifact.artifact_digest:
                raise ValueError("hard verifier returned a mismatched artifact digest")
        except Exception as exc:
            now = utc_now()
            hard_result = HardVerifierResult(
                verifier_id=getattr(hard_verifier, "verifier_id", "unknown_hard_verifier"),
                verifier_version=getattr(hard_verifier, "version", "unknown"),
                artifact_digest=artifact.artifact_digest,
                outcome=HardVerifierOutcome.INFRASTRUCTURE_ERROR,
                defect_refs=(),
                evidence_refs=("hard_verifier_exception",),
                oracle_class="hard_verifier_failure",
                oracle_applicability="unavailable",
                started_at=now,
                completed_at=now,
                latency_ms=0.0,
                cost={"kind": "unknown_cost"},
                metadata={"exception": type(exc).__name__},
            )
        self._emit_safely(
            telemetry_failures,
            "hard_verifier_finished", task, artifact, hard_result.verifier_id, hard_result.verifier_version,
            hard_verifier_result=hard_result.to_dict(),
        )
        comparison = compare_shadow_to_hard_verifier(shadow, hard_result)
        self._emit_safely(telemetry_failures, "shadow_comparison_created", task, artifact, "shadow_comparison", "1.0.0", comparison=comparison.to_dict())
        self._emit_safely(telemetry_failures, "run_completed", task, artifact, "verification_runner", self.version, final_outcome=hard_result.outcome.value)
        return VerificationRun(
            run_id, task, artifact, gates, observations, shadow, hard_result, comparison,
            self.domain_pack_id, self.domain_pack_version, tuple(telemetry_failures),
        )


__all__ = ["CandidateArtifact", "VerificationRun", "VerificationRunner"]
