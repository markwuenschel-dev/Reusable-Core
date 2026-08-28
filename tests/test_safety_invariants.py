import unittest
from dataclasses import replace
from time import sleep

from verification_v1.aggregation import ShadowAggregator
from verification_v1.artifacts import ArtifactStore
from verification_v1.checklets import MAX_CHECKLET_ARTIFACT_BYTES, BaseCodingChecklet, CheckletContext, CheckletRegistry
from verification_v1.contracts import (
    CheckletVerdict,
    CounterfactualClass,
    GateStatus,
    HardVerifierOutcome,
    Severity,
    ShadowAction,
    TaskContract,
)
from verification_v1.gates import GateRunner, MetadataShapeGate
from verification_v1.hard_verify import FixtureHardVerifier, StaticHardVerifier
from verification_v1.runner import CandidateArtifact, VerificationRunner
from verification_v1.telemetry import InMemoryEventSink


class FixedChecklet(BaseCodingChecklet):
    def __init__(self, verdict: CheckletVerdict, severity: Severity = Severity.INFO) -> None:
        super().__init__(f"fixed_{verdict.value}_{severity.value}", "fixed-fixture", "Returns controlled fixture evidence.")
        self.verdict = verdict
        self.severity = severity

    def evaluate(self, context: CheckletContext):
        return self.observation(
            context,
            self.verdict,
            self.severity,
            "fixture_finding" if self.verdict == CheckletVerdict.FINDING else None,
            "fixture.py" if self.verdict == CheckletVerdict.FINDING else None,
            "Controlled checklet observation.",
        )


class ExplodingChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("exploding", "error-fixture", "Raises a fixture exception.")

    def evaluate(self, context: CheckletContext):
        raise RuntimeError("fixture checklet crash")


class ExplodingGate:
    gate_id = "exploding_gate"
    version = "1.0.0"

    def evaluate(self, task, artifact):
        raise RuntimeError("fixture gate crash")


class ExplodingEventSink:
    def emit(self, *args, **kwargs):
        raise OSError("fixture telemetry write failure")


class HardVerifierFinishedFailingSink(InMemoryEventSink):
    def emit(self, event_type, *args, **kwargs):
        if event_type == "hard_verifier_finished":
            raise OSError("fixture hard-verifier telemetry write failure")
        super().emit(event_type, *args, **kwargs)


class PersistThenRaiseSink(InMemoryEventSink):
    def emit(self, event_type, *args, **kwargs):
        super().emit(event_type, *args, **kwargs)
        if event_type == "hard_verifier_finished":
            raise OSError("fixture post-persist telemetry failure")


class BlockingChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("blocking", "timeout-fixture", "Blocks until the process deadline.")
        self.spec = replace(self.spec, timeout_seconds=0.05)

    def evaluate(self, context: CheckletContext):
        sleep(5)
        return self.observation(context, CheckletVerdict.CLEAN)


class CountingVerifier(StaticHardVerifier):
    def __init__(self, outcome: HardVerifierOutcome) -> None:
        super().__init__(outcome)
        self.calls = 0

    def verify(self, task, artifact):
        self.calls += 1
        return super().verify(task, artifact)


def candidate(fixture_id: str | None = None) -> CandidateArtifact:
    metadata = {
        "changed_paths": ["src/candidate.py"],
        "allowed_paths": ["src/candidate.py"],
        "producer_test_cases": ["test_candidate"],
        "test_cases_by_requirement": {},
        "covered_requirements": [],
        "boundary_cases": [],
        "handled_boundary_cases": [],
        "signature_changes": [],
    }
    if fixture_id:
        metadata["fixture_id"] = fixture_id
    return CandidateArtifact.from_text("candidate", "coding_patch", "def candidate():\n    return 1\n", metadata)


def runner_with(checklets, gates=None):
    return VerificationRunner(
        artifact_store=ArtifactStore(),
        gate_runner=GateRunner(tuple(gates or (MetadataShapeGate(),))),
        checklets=CheckletRegistry(tuple(checklets)),
        aggregator=ShadowAggregator(),
        event_sink=InMemoryEventSink(),
    )


class SafetyInvariantTests(unittest.TestCase):
    def test_shadow_waive_does_not_skip_hard_verifier_or_override_rejection(self) -> None:
        verifier = CountingVerifier(HardVerifierOutcome.REJECTED)
        result = runner_with((FixedChecklet(CheckletVerdict.CLEAN),)).run(
            TaskContract("rejecting-task", ()), candidate(), verifier
        )

        self.assertEqual(1, verifier.calls)
        self.assertEqual(ShadowAction.WOULD_WAIVE, result.shadow_assessment.shadow_action)
        self.assertEqual(HardVerifierOutcome.REJECTED, result.final_outcome)
        self.assertEqual(CounterfactualClass.FALSE_SHADOW_WAIVE, result.comparison.counterfactual_class)

    def test_required_checklet_error_forces_shadow_hard_verify_but_hard_acceptance_wins(self) -> None:
        result = runner_with((ExplodingChecklet(),)).run(
            TaskContract("checklet-error", ()), candidate(), StaticHardVerifier(HardVerifierOutcome.ACCEPTED)
        )

        self.assertEqual(CheckletVerdict.ERROR, result.observations[0].verdict)
        self.assertEqual(ShadowAction.WOULD_HARD_VERIFY, result.shadow_assessment.shadow_action)
        self.assertEqual(HardVerifierOutcome.ACCEPTED, result.final_outcome)

    def test_unknown_and_infrastructure_hard_outcomes_are_not_acceptance(self) -> None:
        for outcome in (HardVerifierOutcome.OUTCOME_UNKNOWN, HardVerifierOutcome.INFRASTRUCTURE_ERROR):
            result = runner_with((FixedChecklet(CheckletVerdict.CLEAN),)).run(
                TaskContract(f"{outcome.value}-task", ()), candidate(), StaticHardVerifier(outcome)
            )
            self.assertNotEqual(HardVerifierOutcome.ACCEPTED, result.final_outcome)
            self.assertEqual(CounterfactualClass.INDETERMINATE, result.comparison.counterfactual_class)

    def test_gate_error_is_not_pass_and_forces_shadow_hard_verify(self) -> None:
        result = runner_with((FixedChecklet(CheckletVerdict.CLEAN),), gates=(ExplodingGate(),)).run(
            TaskContract("gate-error", ()), candidate(), StaticHardVerifier(HardVerifierOutcome.ACCEPTED)
        )

        self.assertEqual(GateStatus.ERROR, result.gates[0].status)
        self.assertEqual(ShadowAction.WOULD_HARD_VERIFY, result.shadow_assessment.shadow_action)

    def test_fixture_oracle_rejects_despite_passing_producer_test_evidence(self) -> None:
        artifact_candidate = candidate("producer-tests-pass-but-reference-rejects")
        expected_digest = ArtifactStore().register(artifact_candidate, "fixture-reference").artifact_digest
        result = runner_with((FixedChecklet(CheckletVerdict.CLEAN),)).run(
            TaskContract("adversarial-independent-oracle", ()),
            artifact_candidate,
            FixtureHardVerifier({expected_digest: HardVerifierOutcome.REJECTED}),
        )

        self.assertEqual(HardVerifierOutcome.REJECTED, result.final_outcome)
        self.assertEqual("executable_reference_fixture", result.hard_verifier_result.oracle_class)

    def test_telemetry_failure_is_run_level_infrastructure_evidence_but_cannot_skip_hard_verification(self) -> None:
        verifier = CountingVerifier(HardVerifierOutcome.ACCEPTED)
        unsafe_runner = VerificationRunner(
            artifact_store=ArtifactStore(),
            gate_runner=GateRunner((MetadataShapeGate(),)),
            checklets=CheckletRegistry((FixedChecklet(CheckletVerdict.CLEAN),)),
            aggregator=ShadowAggregator(),
            event_sink=ExplodingEventSink(),
        )

        result = unsafe_runner.run(TaskContract("telemetry-failure", ()), candidate(), verifier)

        self.assertEqual(1, verifier.calls)
        self.assertEqual(HardVerifierOutcome.ACCEPTED, result.final_outcome)
        self.assertGreaterEqual(len(result.telemetry_failures), 1)
        self.assertEqual("OSError", result.telemetry_failures[0].exception_type)

    def test_timed_out_checklet_is_terminated_before_hard_verification(self) -> None:
        verifier = CountingVerifier(HardVerifierOutcome.ACCEPTED)
        result = runner_with((BlockingChecklet(),)).run(TaskContract("timeout-task", ()), candidate(), verifier)

        self.assertEqual(1, verifier.calls)
        self.assertEqual(CheckletVerdict.ERROR, result.observations[0].verdict)
        self.assertIn("timeout", result.observations[0].summary)

    def test_late_telemetry_failure_never_overrides_the_hard_decision(self) -> None:
        sink = HardVerifierFinishedFailingSink()
        controlled_runner = VerificationRunner(
            artifact_store=ArtifactStore(),
            gate_runner=GateRunner((MetadataShapeGate(),)),
            checklets=CheckletRegistry((FixedChecklet(CheckletVerdict.CLEAN),)),
            aggregator=ShadowAggregator(),
            event_sink=sink,
        )

        result = controlled_runner.run(TaskContract("late-telemetry-failure", ()), candidate(), StaticHardVerifier(HardVerifierOutcome.ACCEPTED))
        comparisons = [event["comparison"] for event in sink.events if event["event_type"] == "shadow_comparison_created"]
        completions = [event for event in sink.events if event["event_type"] == "run_completed"]

        self.assertEqual(HardVerifierOutcome.ACCEPTED, result.final_outcome)
        self.assertEqual(HardVerifierOutcome.ACCEPTED.value, comparisons[-1]["hard_verifier_outcome"])
        self.assertEqual(HardVerifierOutcome.ACCEPTED.value, completions[-1]["final_outcome"])
        self.assertEqual("hard_verifier_finished", result.telemetry_failures[0].event_type)

    def test_post_persist_telemetry_failure_keeps_append_only_evidence_consistent_with_result(self) -> None:
        sink = PersistThenRaiseSink()
        controlled_runner = VerificationRunner(
            artifact_store=ArtifactStore(),
            gate_runner=GateRunner((MetadataShapeGate(),)),
            checklets=CheckletRegistry((FixedChecklet(CheckletVerdict.CLEAN),)),
            aggregator=ShadowAggregator(),
            event_sink=sink,
        )

        result = controlled_runner.run(TaskContract("post-persist-telemetry-failure", ()), candidate(), StaticHardVerifier(HardVerifierOutcome.ACCEPTED))
        persisted_hard = [event["hard_verifier_result"] for event in sink.events if event["event_type"] == "hard_verifier_finished"]

        self.assertEqual(HardVerifierOutcome.ACCEPTED, result.final_outcome)
        self.assertEqual(HardVerifierOutcome.ACCEPTED.value, persisted_hard[-1]["outcome"])
        self.assertEqual("hard_verifier_finished", result.telemetry_failures[0].event_type)

    def test_oversized_checklet_payload_becomes_typed_error_without_skipping_hard_verification(self) -> None:
        verifier = CountingVerifier(HardVerifierOutcome.ACCEPTED)
        oversized = CandidateArtifact(
            "oversized", "coding_patch", b"x" * (MAX_CHECKLET_ARTIFACT_BYTES + 1),
            {"changed_paths": ["src/oversized.py"], "allowed_paths": ["src/oversized.py"]},
        )

        result = runner_with((FixedChecklet(CheckletVerdict.CLEAN),)).run(
            TaskContract("oversized-payload", ()), oversized, verifier
        )

        self.assertEqual(1, verifier.calls)
        self.assertEqual(CheckletVerdict.ERROR, result.observations[0].verdict)
        self.assertIn("byte limit", result.observations[0].summary)


if __name__ == "__main__":
    unittest.main()
