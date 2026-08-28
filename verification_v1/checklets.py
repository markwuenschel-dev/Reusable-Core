"""Narrow, deterministic, diagnostic-only coding checklets."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, replace
from time import perf_counter
from typing import Any, Mapping, Protocol

from .artifacts import RegisteredArtifact
from .contracts import (
    CheckletObservation,
    CheckletSpec,
    CheckletVerdict,
    Severity,
    TaskContract,
    mutable_copy,
    new_id,
    parse_checklet_observation,
    utc_now,
)


@dataclass(frozen=True)
class CheckletContext:
    task: TaskContract
    artifact: RegisteredArtifact

    @property
    def metadata(self) -> Mapping[str, Any]:
        # Checklets receive a disposable copy. They can never alter the registered
        # bytes or metadata that bind the hard-verifier result to this artifact.
        return mutable_copy(self.artifact.ref.metadata)


class Checklet(Protocol):
    spec: CheckletSpec

    def evaluate(self, context: CheckletContext) -> CheckletObservation | Mapping[str, Any]: ...


class BaseCodingChecklet:
    def __init__(self, checklet_id: str, criterion_id: str, description: str) -> None:
        self.spec = CheckletSpec(
            checklet_id=checklet_id,
            version="1.0.0",
            domain_pack="coding-v1",
            criterion_id=criterion_id,
            description=description,
            required_artifact_types=("coding_patch",),
            required_context=("changed_paths",),
            implementation_type="deterministic",
            authority_ceiling="diagnostic",
            estimated_cost_class="negligible",
            timeout_seconds=1.0,
            required_or_optional="required",
            evidence_family_template=f"deterministic:vs-v1:{checklet_id}",
        )

    def observation(
        self,
        context: CheckletContext,
        verdict: CheckletVerdict,
        severity: Severity = Severity.INFO,
        finding_type: str | None = None,
        locus: str | None = None,
        summary: str = "No defect found for this criterion.",
        trigger_refs: tuple[str, ...] = (),
    ) -> CheckletObservation:
        now = utc_now()
        return CheckletObservation(
            observation_id=new_id("observation"),
            checklet_id=self.spec.checklet_id,
            checklet_version=self.spec.version,
            criterion_id=self.spec.criterion_id,
            artifact_digest=context.artifact.artifact_digest,
            verdict=verdict,
            severity=severity,
            finding_type=finding_type,
            locus=locus,
            summary=summary,
            confidence=1.0 if verdict != CheckletVerdict.ABSTAIN else None,
            confidence_semantics="heuristic confidence",
            evidence_refs=(),
            trigger_refs=trigger_refs,
            model_provider=None,
            resolved_model_id=None,
            prompt_template_hash=None,
            evidence_family_id=self.spec.evidence_family_template,
            started_at=now,
            completed_at=now,
            latency_ms=0.0,
            estimated_or_actual_cost={"kind": "actual_cost", "amount": 0.0, "currency": "USD"},
            metadata={},
        )


class RequirementCoverageChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("requirement_coverage", "requirements-covered", "Checks declared task requirements for explicit coverage.")

    def evaluate(self, context: CheckletContext) -> CheckletObservation:
        covered = set(context.metadata.get("covered_requirements", []))
        missing = [requirement for requirement in context.task.requirements if requirement not in covered]
        if missing:
            return self.observation(
                context, CheckletVerdict.FINDING, Severity.MEDIUM, "requirement_omitted", "task.requirements",
                f"Declared requirements lack coverage: {', '.join(missing)}.", tuple(missing),
            )
        return self.observation(context, CheckletVerdict.CLEAN)


class TestAdequacyChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("test_adequacy", "producer-test-adequacy", "Checks whether producer test evidence covers changed requirements.")

    def evaluate(self, context: CheckletContext) -> CheckletObservation:
        if not context.task.requirements:
            return self.observation(context, CheckletVerdict.CLEAN)
        tests = context.metadata.get("producer_test_cases", [])
        mapping = context.metadata.get("test_cases_by_requirement", {})
        missing = [requirement for requirement in context.task.requirements if not mapping.get(requirement)]
        if not tests or missing:
            return self.observation(
                context, CheckletVerdict.FINDING, Severity.MEDIUM, "test_inadequate", "producer_test_cases",
                "Producer test evidence does not cover every declared requirement.", tuple(missing or context.task.requirements),
            )
        return self.observation(context, CheckletVerdict.CLEAN)


class ChangeScopeChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("change_scope", "declared-change-scope", "Checks changed paths against the declared task scope.")

    def evaluate(self, context: CheckletContext) -> CheckletObservation:
        changed = set(context.metadata.get("changed_paths", []))
        allowed = set(context.metadata.get("allowed_paths", []))
        unrelated = sorted(changed - allowed)
        if unrelated:
            return self.observation(
                context, CheckletVerdict.FINDING, Severity.MEDIUM, "unrelated_change", ", ".join(unrelated),
                "Changed paths fall outside the declared scope.", tuple(unrelated),
            )
        return self.observation(context, CheckletVerdict.CLEAN)


class DependencyRiskChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("dependency_integration_risk", "interface-dependency-risk", "Checks changed interfaces for declared downstream updates.")

    def evaluate(self, context: CheckletContext) -> CheckletObservation:
        risky = [change for change in context.metadata.get("signature_changes", []) if not change.get("callsites_updated", False)]
        if risky:
            loci = tuple(str(change.get("symbol", "unknown_interface")) for change in risky)
            return self.observation(
                context, CheckletVerdict.FINDING, Severity.HIGH, "integration_risk", ", ".join(loci),
                "A changed interface has no corresponding call-site update evidence.", loci,
            )
        return self.observation(context, CheckletVerdict.CLEAN)


class ErrorBoundaryChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("error_boundary", "failure-boundaries", "Checks declared boundary cases for handling evidence.")

    def evaluate(self, context: CheckletContext) -> CheckletObservation:
        expected = set(context.metadata.get("boundary_cases", []))
        handled = set(context.metadata.get("handled_boundary_cases", []))
        missing = sorted(expected - handled)
        if missing:
            return self.observation(
                context, CheckletVerdict.FINDING, Severity.MEDIUM, "boundary_not_handled", ", ".join(missing),
                "Declared boundary cases lack handling evidence.", tuple(missing),
            )
        return self.observation(context, CheckletVerdict.CLEAN)


def error_observation(
    spec: CheckletSpec,
    context: CheckletContext,
    reason: str,
    started_at: str | None = None,
    latency_ms: float = 0.0,
) -> CheckletObservation:
    return CheckletObservation(
        observation_id=new_id("observation"),
        checklet_id=spec.checklet_id,
        checklet_version=spec.version,
        criterion_id=spec.criterion_id,
        artifact_digest=context.artifact.artifact_digest,
        verdict=CheckletVerdict.ERROR,
        severity=Severity.HIGH,
        finding_type="checklet_execution_error",
        locus=None,
        summary=reason,
        confidence=None,
        confidence_semantics="not available after checklet error",
        evidence_refs=(),
        trigger_refs=(),
        model_provider=None,
        resolved_model_id=None,
        prompt_template_hash=None,
        evidence_family_id=spec.evidence_family_template,
        started_at=started_at or utc_now(),
        completed_at=utc_now(),
        latency_ms=latency_ms,
        estimated_or_actual_cost={"kind": "unknown_cost"},
        metadata={},
    )


class CheckletRegistry:
    def __init__(self, checklets: tuple[Checklet, ...]) -> None:
        self._checklets = checklets

    @property
    def specs(self) -> tuple[CheckletSpec, ...]:
        return tuple(checklet.spec for checklet in self._checklets)

    def run_all(self, context: CheckletContext) -> tuple[CheckletObservation, ...]:
        observations: list[CheckletObservation] = []
        for checklet in self._checklets:
            started_at = utc_now()
            timer = perf_counter()
            if context.artifact.ref.artifact_type not in checklet.spec.required_artifact_types:
                continue
            if any(key not in context.metadata for key in checklet.spec.required_context):
                observations.append(
                    error_observation(
                        checklet.spec,
                        context,
                        "required checklet context unavailable",
                        started_at,
                        (perf_counter() - timer) * 1000,
                    )
                )
                continue
            executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"vs-v1-{checklet.spec.checklet_id}")
            try:
                future = executor.submit(checklet.evaluate, context)
                raw = future.result(timeout=checklet.spec.timeout_seconds)
                if isinstance(raw, Mapping):
                    raw = parse_checklet_observation(raw, checklet.spec, context.artifact.artifact_digest)
                if not isinstance(raw, CheckletObservation):
                    observations.append(
                        error_observation(
                            checklet.spec, context, "malformed structured checklet output", started_at, (perf_counter() - timer) * 1000
                        )
                    )
                elif raw.artifact_digest != context.artifact.artifact_digest:
                    observations.append(
                        error_observation(
                            checklet.spec, context, "checklet returned a mismatched artifact digest", started_at, (perf_counter() - timer) * 1000
                        )
                    )
                else:
                    observations.append(
                        replace(
                            raw,
                            started_at=started_at,
                            completed_at=utc_now(),
                            latency_ms=(perf_counter() - timer) * 1000,
                        )
                    )
            except FutureTimeoutError:
                observations.append(
                    error_observation(
                        checklet.spec,
                        context,
                        f"checklet timeout after {checklet.spec.timeout_seconds:.3f} seconds",
                        started_at,
                        (perf_counter() - timer) * 1000,
                    )
                )
            except Exception as exc:
                observations.append(
                    error_observation(
                        checklet.spec,
                        context,
                        f"checklet exception: {type(exc).__name__}",
                        started_at,
                        (perf_counter() - timer) * 1000,
                    )
                )
            finally:
                # A timed-out checklet has no authority and receives only its private copy of context.
                executor.shutdown(wait=False, cancel_futures=True)
        return tuple(observations)


def default_coding_checklets() -> tuple[Checklet, ...]:
    return (
        RequirementCoverageChecklet(),
        TestAdequacyChecklet(),
        ChangeScopeChecklet(),
        DependencyRiskChecklet(),
        ErrorBoundaryChecklet(),
    )
