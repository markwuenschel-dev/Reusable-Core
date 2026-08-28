import unittest

from verification_v1.contracts import CheckletVerdict, HardVerifierOutcome, TaskContract
from verification_v1.checklets import BaseCodingChecklet, CheckletContext, CheckletRegistry
from verification_v1.aggregation import ShadowAggregator
from verification_v1.artifacts import ArtifactStore
from verification_v1.gates import GateRunner, MetadataShapeGate
from verification_v1.hard_verify import StaticHardVerifier
from verification_v1.runner import CandidateArtifact, VerificationRunner
from verification_v1.telemetry import InMemoryEventSink


class MutatingChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("mutating_fixture", "read-only-observation", "Attempts to mutate observation context.")

    def evaluate(self, context: CheckletContext):
        context.metadata["changed_paths"].append("should-not-persist.py")
        return self.observation(context, verdict=CheckletVerdict.CLEAN)


class VerificationRunnerTests(unittest.TestCase):
    def test_clean_artifact_is_accepted_only_by_hard_verifier(self) -> None:
        events = InMemoryEventSink()
        runner = VerificationRunner.default(event_sink=events)
        task = TaskContract(task_id="clean-task", requirements=())
        artifact = CandidateArtifact.from_text(
            artifact_id="clean-artifact",
            artifact_type="coding_patch",
            content="def add(left, right):\n    return left + right\n",
            metadata={
                "changed_paths": ["src/maths.py"],
                "allowed_paths": ["src/maths.py"],
                "producer_test_cases": ["test_add"],
                "covered_requirements": [],
                "boundary_cases": [],
                "handled_boundary_cases": [],
                "signature_changes": [],
            },
        )

        result = runner.run(task, artifact, StaticHardVerifier(HardVerifierOutcome.ACCEPTED))

        self.assertEqual(HardVerifierOutcome.ACCEPTED, result.final_outcome)
        self.assertEqual("would_waive", result.shadow_assessment.shadow_action.value)
        self.assertEqual(result.artifact.artifact_digest, result.hard_verifier_result.artifact_digest)
        self.assertEqual(result.artifact.artifact_digest, result.shadow_assessment.artifact_digest)
        self.assertIn("hard_verifier_finished", [event["event_type"] for event in events.events])

    def test_checklet_cannot_mutate_registered_artifact(self) -> None:
        runner = VerificationRunner(
            artifact_store=ArtifactStore(),
            gate_runner=GateRunner((MetadataShapeGate(),)),
            checklets=CheckletRegistry((MutatingChecklet(),)),
            aggregator=ShadowAggregator(),
            event_sink=InMemoryEventSink(),
        )
        task = TaskContract(task_id="read-only-task", requirements=())
        artifact = CandidateArtifact.from_text(
            "read-only-artifact",
            "coding_patch",
            "pass\n",
            {"changed_paths": ["src/only.py"], "allowed_paths": ["src/only.py"]},
        )

        result = runner.run(task, artifact, StaticHardVerifier(HardVerifierOutcome.ACCEPTED))

        self.assertEqual(("src/only.py",), result.artifact.ref.metadata["changed_paths"])

    def test_registered_artifact_metadata_is_deeply_immutable(self) -> None:
        result = VerificationRunner.default().run(
            TaskContract("immutable-metadata-task", ()),
            CandidateArtifact.from_text(
                "immutable-metadata-artifact",
                "coding_patch",
                "pass\n",
                {"changed_paths": ["src/only.py"], "allowed_paths": ["src/only.py"]},
            ),
            StaticHardVerifier(HardVerifierOutcome.ACCEPTED),
        )

        with self.assertRaises(TypeError):
            result.artifact.ref.metadata["new_key"] = "not-allowed"
        with self.assertRaises(AttributeError):
            result.artifact.ref.metadata["changed_paths"].append("not-allowed.py")


if __name__ == "__main__":
    unittest.main()
