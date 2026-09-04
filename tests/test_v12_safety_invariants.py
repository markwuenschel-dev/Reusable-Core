import unittest

from verification_v1.aggregation import ShadowAggregator
from verification_v1.artifacts import ArtifactStore
from verification_v1.checklets import CheckletRegistry, default_coding_checklets
from verification_v1.contracts import (
    CheckletVerdict,
    GateResult,
    GateStatus,
    HardVerifierOutcome,
    Severity,
    ShadowAction,
    TaskContract,
    utc_now,
)
from verification_v1.domain import CodingDomainPack
from verification_v1.gates import GateRunner, MetadataShapeGate
from verification_v1.hard_verify import StaticHardVerifier
from verification_v1.runner import CandidateArtifact, VerificationRunner
from verification_v1.telemetry import InMemoryEventSink


class _CountingVerifier:
    verifier_id = "static-test-oracle"
    version = "1.0.0"

    def __init__(self, outcome: HardVerifierOutcome) -> None:
        self.outcome = outcome
        self.calls = 0

    def verify(self, task, artifact):
        self.calls += 1
        return StaticHardVerifier(self.outcome).verify(task, artifact)


class V11SafetyStillHoldsTests(unittest.TestCase):
    def test_v11_final_outcome_invariant_still_holds(self) -> None:
        runner = VerificationRunner.default(event_sink=InMemoryEventSink())
        verifier = _CountingVerifier(HardVerifierOutcome.REJECTED)
        result = runner.run(
            TaskContract("safety-final", ()),
            CandidateArtifact.from_text("a", "coding_patch", "print(1)\n", {"changed_paths": ["x.py"]}),
            verifier,
        )
        self.assertEqual(HardVerifierOutcome.REJECTED, result.final_outcome)
        self.assertEqual(result.hard_verifier_result.outcome, result.final_outcome)
        self.assertNotEqual(result.shadow_assessment.shadow_action, result.final_outcome)

    def test_v11_shadow_waive_still_runs_hard_verifier(self) -> None:
        runner = VerificationRunner(
            ArtifactStore(),
            GateRunner((MetadataShapeGate(),)),
            CheckletRegistry(default_coding_checklets()),
            ShadowAggregator(),
            InMemoryEventSink(),
            domain_pack_id="coding-v1",
            domain_pack_version="1.1.0",
        )
        verifier = _CountingVerifier(HardVerifierOutcome.REJECTED)
        result = runner.run(
            TaskContract("safety-waive", (), metadata={"allowed_paths": ["snippet.py"]}),
            CandidateArtifact.from_text(
                "clean",
                "coding_patch",
                "def add(a, b):\n    return a + b\n",
                {"changed_paths": ["snippet.py"], "allowed_paths": ["snippet.py"]},
            ),
            verifier,
        )
        self.assertEqual(1, verifier.calls)
        self.assertEqual(HardVerifierOutcome.REJECTED, result.final_outcome)

    def test_no_sixth_checklet_and_no_learned_aggregator(self) -> None:
        pack = CodingDomainPack.default()
        self.assertEqual(5, len(pack.checklet_ids))
        from pathlib import Path

        import verification_v1.aggregation as aggregation
        import verification_v1.runner as runner

        aggregation_source = Path(aggregation.__file__).read_text(encoding="utf-8")
        runner_source = Path(runner.__file__).read_text(encoding="utf-8")
        self.assertNotIn("sklearn", aggregation_source)
        self.assertNotIn("logistic", aggregation_source.lower())
        self.assertIn("hard_verifier.verify", runner_source)
        self.assertNotIn("would_waive", runner_source.split("hard_verifier.verify", 1)[0])
