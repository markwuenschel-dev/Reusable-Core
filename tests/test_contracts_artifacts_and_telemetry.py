import json
import sys
import tempfile
import unittest
from pathlib import Path

from verification_v1.aggregation import ShadowAggregator
from verification_v1.artifacts import ArtifactStore
from verification_v1.checklets import BaseCodingChecklet, CheckletContext, CheckletRegistry
from verification_v1.contracts import (
    CheckletVerdict,
    GateResult,
    GateStatus,
    HardVerifierOutcome,
    Severity,
    ShadowAction,
    TaskContract,
)
from verification_v1.gates import GateRunner, MetadataShapeGate
from verification_v1.hard_verify import CommandHardVerifier, StaticHardVerifier
from verification_v1.runner import CandidateArtifact, VerificationRunner
from verification_v1.telemetry import InMemoryEventSink, JsonlEventSink, make_event


class FixedObservationChecklet(BaseCodingChecklet):
    def __init__(self, verdict: CheckletVerdict, severity: Severity = Severity.INFO, structured: bool = False) -> None:
        super().__init__("fixed_contract", "contract-fixture", "A controlled observation for contract tests.")
        self.verdict = verdict
        self.severity = severity
        self.structured = structured

    def evaluate(self, context: CheckletContext):
        observation = self.observation(context, self.verdict, self.severity)
        if not self.structured:
            return observation
        payload = observation.to_dict()
        payload.update({"model_provider": "fixture-provider", "resolved_model_id": "fixture-model-1", "prompt_template_hash": "sha256:fixture"})
        return payload


class MalformedChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("malformed", "structured-contract", "Returns an incomplete structured observation.")

    def evaluate(self, context: CheckletContext):
        return {"verdict": "clean"}


def artifact() -> CandidateArtifact:
    return CandidateArtifact.from_text(
        "contract-artifact",
        "coding_patch",
        "def value():\n    return 1\n",
        {
            "changed_paths": ["src/value.py"], "allowed_paths": ["src/value.py"],
            "producer_test_cases": [], "test_cases_by_requirement": {}, "covered_requirements": [],
            "boundary_cases": [], "handled_boundary_cases": [], "signature_changes": [],
        },
    )


def runner(checklet, event_sink):
    return VerificationRunner(
        ArtifactStore(), GateRunner((MetadataShapeGate(),)), CheckletRegistry((checklet,)), ShadowAggregator(), event_sink
    )


class ContractsArtifactsAndTelemetryTests(unittest.TestCase):
    def test_digest_is_stable_for_canonical_bytes_and_changes_when_artifact_changes(self) -> None:
        store = ArtifactStore()
        first = store.register(CandidateArtifact.from_text("same", "coding_patch", "line-one\r\nline-two\r\n", {"changed_paths": []}), "run-a")
        same = store.register(CandidateArtifact.from_text("same", "coding_patch", "line-one\nline-two\n", {"changed_paths": []}), "run-b")
        mutated = store.register(CandidateArtifact.from_text("same", "coding_patch", "line-one\nchanged\n", {"changed_paths": []}), "run-c")

        self.assertEqual(first.artifact_digest, same.artifact_digest)
        self.assertNotEqual(first.artifact_digest, mutated.artifact_digest)
        self.assertNotEqual(first.ref.artifact_version, mutated.ref.artifact_version)

    def test_all_decision_results_bind_one_artifact_digest_and_model_identity_survives_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sink = JsonlEventSink(Path(directory) / "events.jsonl")
            result = runner(FixedObservationChecklet(CheckletVerdict.CLEAN, structured=True), sink).run(
                TaskContract("identity-task", ()), artifact(), StaticHardVerifier(HardVerifierOutcome.ACCEPTED)
            )
            events = [json.loads(line) for line in (Path(directory) / "events.jsonl").read_text(encoding="utf-8").splitlines()]

        digest = result.artifact.artifact_digest
        self.assertEqual({digest}, {gate.artifact_digest for gate in result.gates})
        self.assertEqual({digest}, {observation.artifact_digest for observation in result.observations})
        self.assertEqual(digest, result.shadow_assessment.artifact_digest)
        self.assertEqual(digest, result.hard_verifier_result.artifact_digest)
        self.assertEqual(digest, result.comparison.artifact_digest)
        self.assertEqual("fixture-model-1", result.observations[0].resolved_model_id)
        self.assertEqual("sha256:fixture", result.observations[0].prompt_template_hash)
        required_envelope = {"schema_version", "event_id", "timestamp", "run_id", "task_id", "artifact_id", "artifact_digest", "artifact_version", "event_type", "component_id", "component_version"}
        self.assertTrue(all(required_envelope <= set(event) and event["artifact_digest"] == digest for event in events))

    def test_malformed_and_abstaining_required_checklets_fail_closed_in_shadow_policy(self) -> None:
        malformed = runner(MalformedChecklet(), event_sink=InMemoryEventSink()).run(
            TaskContract("malformed-task", ()), artifact(), StaticHardVerifier(HardVerifierOutcome.ACCEPTED)
        )
        abstaining = runner(FixedObservationChecklet(CheckletVerdict.ABSTAIN), event_sink=InMemoryEventSink()).run(
            TaskContract("abstain-task", ()), artifact(), StaticHardVerifier(HardVerifierOutcome.ACCEPTED)
        )

        self.assertEqual(CheckletVerdict.ERROR, malformed.observations[0].verdict)
        self.assertEqual(ShadowAction.WOULD_HARD_VERIFY, malformed.shadow_assessment.shadow_action)
        self.assertEqual(ShadowAction.WOULD_HARD_VERIFY, abstaining.shadow_assessment.shadow_action)

    def test_shadow_policy_is_deterministic_for_same_inputs(self) -> None:
        controlled_runner = runner(FixedObservationChecklet(CheckletVerdict.FINDING, Severity.HIGH), event_sink=InMemoryEventSink())
        result = controlled_runner.run(TaskContract("deterministic-task", ()), artifact(), StaticHardVerifier(HardVerifierOutcome.ACCEPTED))

        first = controlled_runner.aggregator.assess(result.artifact.artifact_digest, result.gates, result.observations)
        second = controlled_runner.aggregator.assess(result.artifact.artifact_digest, result.gates, result.observations)

        self.assertEqual(first.risk_band, second.risk_band)
        self.assertEqual(first.shadow_action, second.shadow_action)
        self.assertEqual(first.reason_codes, second.reason_codes)
        self.assertEqual(ShadowAction.WOULD_HARD_VERIFY, first.shadow_action)

    def test_command_hard_verifier_uses_materialized_exact_artifact_bytes(self) -> None:
        check = "from pathlib import Path; import sys; sys.exit(0 if Path(sys.argv[1]).read_bytes() == b'def value():\\n    return 1\\n' else 1)"
        result = runner(FixedObservationChecklet(CheckletVerdict.CLEAN), event_sink=InMemoryEventSink()).run(
            TaskContract("command-task", ()), artifact(), CommandHardVerifier((sys.executable, "-c", check, "{artifact_path}"))
        )

        self.assertEqual(HardVerifierOutcome.ACCEPTED, result.final_outcome)
        self.assertEqual("external_executable_command", result.hard_verifier_result.oracle_class)

    def test_command_hard_verifier_detects_materialized_artifact_tampering(self) -> None:
        tamper = (
            "from pathlib import Path; import os, sys; "
            "path = Path(sys.argv[1]); os.chmod(path, 0o666); path.write_bytes(b'tampered'); sys.exit(0)"
        )
        result = runner(FixedObservationChecklet(CheckletVerdict.CLEAN), event_sink=InMemoryEventSink()).run(
            TaskContract("tamper-command-task", ()), artifact(), CommandHardVerifier((sys.executable, "-c", tamper, "{artifact_path}"))
        )

        self.assertEqual(HardVerifierOutcome.INFRASTRUCTURE_ERROR, result.final_outcome)
        self.assertIn("materialized_artifact_digest_mismatch", result.hard_verifier_result.evidence_refs)

    def test_telemetry_payload_cannot_override_identity_envelope(self) -> None:
        registered = ArtifactStore().register(artifact(), "event-run")

        with self.assertRaises(ValueError):
            make_event(
                "test_event",
                TaskContract("event-task", ()),
                registered,
                "test-component",
                "1.0.0",
                artifact_digest="not-the-registered-digest",
            )

    def test_contract_collections_are_deeply_frozen_at_construction(self) -> None:
        requirements = ["declared-requirement"]
        details = {"nested": ["evidence"]}
        task = TaskContract("frozen-task", requirements)
        gate = GateResult(
            "frozen-gate", "1.0.0", "digest", GateStatus.PASS, Severity.INFO,
            "started", "completed", 0.0, details=details,
        )
        requirements.append("late-mutation")
        details["nested"].append("late-mutation")

        self.assertEqual(("declared-requirement",), task.requirements)
        self.assertEqual(("evidence",), gate.details["nested"])
        with self.assertRaises(TypeError):
            gate.details["new"] = "not-allowed"

    def test_frozen_set_metadata_remains_json_serializable(self) -> None:
        task = TaskContract("set-metadata-task", (), metadata={"tags": {"stable", "diagnostic"}})

        payload = task.to_dict()

        self.assertEqual({"stable", "diagnostic"}, set(payload["metadata"]["tags"]))


if __name__ == "__main__":
    unittest.main()
