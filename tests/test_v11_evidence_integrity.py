import json
import unittest
from time import perf_counter
from pathlib import Path

from verification_v1.aggregation import ShadowAggregator
from verification_v1.artifacts import ArtifactStore
from verification_v1.bundle import encode_coding_bundle
from verification_v1.checklets import (
    ChangeScopeChecklet,
    CheckletContext,
    CheckletRegistry,
    DependencyRiskChecklet,
    ErrorBoundaryChecklet,
    RequirementCoverageChecklet,
    TestAdequacyChecklet,
    default_coding_checklets,
)
from verification_v1.contracts import (
    CheckletVerdict,
    GateResult,
    GateStatus,
    HardVerifierOutcome,
    Severity,
    ShadowAction,
    TaskContract,
)
from verification_v1.evaluation import evaluate_fixture_set
from verification_v1.hard_verify import CommandHardVerifier
from verification_v1.runner import CandidateArtifact, VerificationRunner
from verification_v1.telemetry import InMemoryEventSink


def _artifact(content: str, metadata: dict | None = None):
    return ArtifactStore().register(
        CandidateArtifact.from_text("evidence-artifact", "coding_patch", content, metadata or {}),
        "run-evidence",
    )


class ArtifactDerivedEvidenceTests(unittest.TestCase):
    def test_requirement_coverage_ignores_producer_covered_requirements_claim(self) -> None:
        content = encode_coding_bundle(
            {},
            {"stats.py": "def total(items):\n    return items[0]\n"},
        )
        artifact = _artifact(
            content,
            {
                "changed_paths": ["stats.py"],
                "covered_requirements": ["return-zero-for-empty"],
            },
        )
        observation = RequirementCoverageChecklet().evaluate(
            CheckletContext(
                TaskContract("req-task", ("return-zero-for-empty",), metadata={"allowed_paths": ["stats.py"]}),
                artifact,
            )
        )

        self.assertEqual(CheckletVerdict.FINDING, observation.verdict)
        self.assertEqual("requirement_omitted", observation.finding_type)

    def test_test_adequacy_ignores_producer_test_case_claims(self) -> None:
        content = encode_coding_bundle(
            {},
            {"unique.py": "def unique(values):\n    return sorted(set(values))\n"},
        )
        artifact = _artifact(
            content,
            {
                "changed_paths": ["unique.py"],
                "producer_test_cases": ["test_unique"],
                "test_cases_by_requirement": {"sort-unique-values": ["test_unique"]},
            },
        )
        observation = TestAdequacyChecklet().evaluate(
            CheckletContext(
                TaskContract("test-task", ("sort-unique-values",), metadata={"allowed_paths": ["unique.py"]}),
                artifact,
            )
        )

        self.assertEqual(CheckletVerdict.FINDING, observation.verdict)
        self.assertEqual("test_inadequate", observation.finding_type)

    def test_change_scope_uses_derived_diff_paths_not_producer_changed_paths(self) -> None:
        content = encode_coding_bundle(
            {},
            {
                "wanted.py": "def wanted():\n    return True\n",
                "infra/release.py": "def release():\n    return True\n",
            },
        )
        artifact = _artifact(
            content,
            {
                "changed_paths": ["wanted.py"],
                "allowed_paths": ["wanted.py", "infra/release.py"],
            },
        )
        observation = ChangeScopeChecklet().evaluate(
            CheckletContext(
                TaskContract("scope-task", (), metadata={"allowed_paths": ["wanted.py"]}),
                artifact,
            )
        )

        self.assertEqual(CheckletVerdict.FINDING, observation.verdict)
        self.assertIn("infra/release.py", observation.trigger_refs)

    def test_dependency_risk_ignores_callsites_updated_claim(self) -> None:
        content = encode_coding_bundle(
            {
                "sender.py": "def send(message):\n    return message\n",
                "client.py": "from sender import send\n\ndef deliver(message):\n    return send(message)\n",
            },
            {"sender.py": "def send(message, retry_count):\n    return message\n"},
        )
        artifact = _artifact(
            content,
            {
                "changed_paths": ["sender.py"],
                "signature_changes": [{"symbol": "send", "callsites_updated": True}],
            },
        )
        observation = DependencyRiskChecklet().evaluate(
            CheckletContext(
                TaskContract("dep-task", (), metadata={"allowed_paths": ["sender.py", "client.py"]}),
                artifact,
            )
        )

        self.assertEqual(CheckletVerdict.FINDING, observation.verdict)
        self.assertEqual(Severity.HIGH, observation.severity)

    def test_error_boundary_ignores_handled_boundary_cases_claim(self) -> None:
        content = encode_coding_bundle({}, {"first.py": "def first(items):\n    return items[0]\n"})
        artifact = _artifact(
            content,
            {
                "changed_paths": ["first.py"],
                "boundary_cases": ["empty-input"],
                "handled_boundary_cases": ["empty-input"],
            },
        )
        observation = ErrorBoundaryChecklet().evaluate(
            CheckletContext(
                TaskContract(
                    "boundary-task",
                    (),
                    metadata={"allowed_paths": ["first.py"], "boundary_cases": ["empty-input"]},
                ),
                artifact,
            )
        )

        self.assertEqual(CheckletVerdict.FINDING, observation.verdict)
        self.assertEqual("boundary_not_handled", observation.finding_type)


class ConservativeShadowPolicyTests(unittest.TestCase):
    def test_single_medium_finding_forces_hard_verify(self) -> None:
        observation = RequirementCoverageChecklet().observation(
            CheckletContext(TaskContract("policy-task", ()), _artifact("pass\n", {"changed_paths": ["snippet.py"]})),
            CheckletVerdict.FINDING,
            Severity.MEDIUM,
            "requirement_omitted",
        )

        assessment = ShadowAggregator().assess(
            "digest",
            (
                GateResult(
                    "coding_metadata_shape",
                    "1.1.0",
                    "digest",
                    GateStatus.PASS,
                    Severity.INFO,
                    "started",
                    "completed",
                    0.0,
                ),
            ),
            (observation,),
        )

        self.assertEqual(ShadowAction.WOULD_HARD_VERIFY, assessment.shadow_action)
        self.assertIn("medium_finding", assessment.reason_codes)

    def test_only_clean_observations_would_waive(self) -> None:
        observation = RequirementCoverageChecklet().observation(
            CheckletContext(TaskContract("clean-policy-task", ()), _artifact("pass\n", {"changed_paths": ["snippet.py"]})),
            CheckletVerdict.CLEAN,
        )

        assessment = ShadowAggregator().assess(
            "digest",
            (
                GateResult(
                    "coding_metadata_shape",
                    "1.1.0",
                    "digest",
                    GateStatus.PASS,
                    Severity.INFO,
                    "started",
                    "completed",
                    0.0,
                ),
            ),
            (observation,),
        )

        self.assertEqual(ShadowAction.WOULD_WAIVE, assessment.shadow_action)


class ExecutableOracleTests(unittest.TestCase):
    def test_command_hard_verifier_runs_reference_tests_against_materialized_repo(self) -> None:
        content = encode_coding_bundle(
            {},
            {"math_lib.py": "def add(left, right):\n    return left + right\n"},
        )
        candidate = CandidateArtifact.from_text(
            "oracle-artifact",
            "coding_patch",
            content,
            {"changed_paths": ["math_lib.py"], "allowed_paths": ["math_lib.py"]},
        )
        verifier = CommandHardVerifier(
            ("{python}", "-m", "unittest", "discover", "-s", ".", "-p", "test_oracle.py"),
            extra_files={
                "test_oracle.py": (
                    "import unittest\nfrom math_lib import add\n\n"
                    "class ReferenceTests(unittest.TestCase):\n"
                    "    def test_reference_add(self):\n"
                    "        self.assertEqual(add(2, 3), 5)\n"
                )
            },
        )

        result = VerificationRunner.default(event_sink=InMemoryEventSink()).run(
            TaskContract("oracle-task", (), metadata={"allowed_paths": ["math_lib.py"]}),
            candidate,
            verifier,
        )

        self.assertEqual(HardVerifierOutcome.ACCEPTED, result.final_outcome)
        self.assertEqual("command-hard-verifier", result.hard_verifier_result.verifier_id)

    def test_command_hard_verifier_rejects_when_independent_reference_tests_fail(self) -> None:
        content = encode_coding_bundle(
            {},
            {"stats.py": "def total(items):\n    return items[0]\n"},
        )
        candidate = CandidateArtifact.from_text(
            "reject-oracle-artifact",
            "coding_patch",
            content,
            {"changed_paths": ["stats.py"]},
        )
        verifier = CommandHardVerifier(
            ("{python}", "-m", "unittest", "discover", "-s", ".", "-p", "test_oracle.py"),
            extra_files={
                "test_oracle.py": (
                    "import unittest\nfrom stats import total\n\n"
                    "class ReferenceTests(unittest.TestCase):\n"
                    "    def test_empty_returns_zero(self):\n"
                    "        self.assertEqual(total([]), 0)\n"
                )
            },
        )

        result = VerificationRunner.default(event_sink=InMemoryEventSink()).run(
            TaskContract("reject-oracle-task", (), metadata={"allowed_paths": ["stats.py"]}),
            candidate,
            verifier,
        )

        self.assertEqual(HardVerifierOutcome.REJECTED, result.final_outcome)


class IsolationPortabilityTests(unittest.TestCase):
    def test_default_checklets_terminate_deterministically(self) -> None:
        content = encode_coding_bundle(
            {},
            {
                "math_lib.py": "def add(left, right):\n    return left + right\n",
                "test_math_lib.py": "from math_lib import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
            },
        )
        artifact = _artifact(content, {"changed_paths": ["math_lib.py", "test_math_lib.py"]})
        started = perf_counter()
        observations = CheckletRegistry(default_coding_checklets()).run_all(
            CheckletContext(
                TaskContract("portability-task", (), metadata={"allowed_paths": ["math_lib.py", "test_math_lib.py"]}),
                artifact,
            )
        )

        self.assertLess(perf_counter() - started, 30.0)
        self.assertEqual(5, len(observations))
        self.assertTrue(all(observation.verdict in set(CheckletVerdict) for observation in observations))


class EngineeringFixtureClosureTests(unittest.TestCase):
    def test_executable_fixture_set_uses_command_oracle_and_has_no_false_waivers(self) -> None:
        source = Path("evals/verification_v1/engineering_fixture_set.json")
        payload = json.loads(source.read_text(encoding="utf-8"))

        report = evaluate_fixture_set(source)
        by_id = {record["fixture_id"]: record for record in report.run_records}

        self.assertEqual(8, report.task_count)
        self.assertEqual(7, report.hard_verifier_coverage)
        self.assertEqual(1, report.indeterminate_count)
        self.assertEqual(0, report.shadow_metrics["false_shadow_waiver_count"])
        self.assertEqual(0.0, report.shadow_metrics["observed_counterfactual_shadow_miss_rate"])
        self.assertLess(report.shadow_metrics["shadow_waiver_coverage"], 0.5)
        for fixture in payload["fixtures"]:
            record = by_id[fixture["fixture_id"]]
            self.assertEqual(fixture["hard_verifier_outcome"], record["final_outcome"])
            if fixture.get("oracle_unavailable"):
                self.assertEqual("unavailable-reference-oracle", record["hard_verifier_result"]["verifier_id"])
            else:
                self.assertEqual("command-hard-verifier", record["hard_verifier_result"]["verifier_id"])
        for checklet_id in (
            "requirement_coverage",
            "test_adequacy",
            "change_scope",
            "dependency_integration_risk",
            "error_boundary",
        ):
            self.assertGreaterEqual(report.per_checklet[checklet_id]["finding_count"], 1)


if __name__ == "__main__":
    unittest.main()
