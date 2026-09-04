import json
import unittest
from pathlib import Path

from verification_v1.artifacts import ArtifactStore
from verification_v1.bundle import encode_coding_bundle, parse_coding_bundle
from verification_v1.checklets import CheckletContext, RequirementCoverageChecklet
from verification_v1.contracts import TaskContract
from verification_v1.evidence import FORBIDDEN_CHECKLET_CONTEXT_KEYS, FailureCode, Partition
from verification_v1.hard_verify import CommandHardVerifier
from verification_v1.ingestion import fixture_to_manifest, ingest_task_manifest
from verification_v1.integrity import checklet_context_is_clean
from verification_v1.runner import CandidateArtifact, VerificationRunner
from verification_v1.telemetry import InMemoryEventSink

try:
    from v12_helpers import make_record
except ImportError:
    from tests.v12_helpers import make_record


FIXTURE_SET = Path(__file__).resolve().parents[1] / "evals" / "verification_v1" / "engineering_fixture_set.json"


class LeakageTests(unittest.TestCase):
    def test_oracle_bundle_not_visible_to_checklets(self) -> None:
        payload = json.loads(FIXTURE_SET.read_text(encoding="utf-8"))
        fixture = next(item for item in payload["fixtures"] if item["fixture_id"] == "clean-minimal-patch")
        content = fixture["artifact"]["content"]
        bundle = parse_coding_bundle(content.encode("utf-8"), fixture["artifact"]["metadata"])
        self.assertNotIn("test_oracle.py", bundle.patched_files)
        self.assertIn("test_oracle.py", fixture["reference_files"])

    def test_checklet_workspace_excludes_reference_oracle(self) -> None:
        artifact = ArtifactStore().register(
            CandidateArtifact.from_text(
                "oracle-visible",
                "coding_patch",
                encode_coding_bundle({}, {"math_lib.py": "def add(a, b):\n    return a + b\n"}),
                {"allowed_paths": ["math_lib.py"]},
            ),
            "run-oracle-visible",
        )
        context = CheckletContext(TaskContract("t", (), metadata={"allowed_paths": ["math_lib.py"]}), artifact)
        observation = RequirementCoverageChecklet().evaluate(context)
        derived = observation.metadata.get("derived_changed_paths", [])
        self.assertNotIn("test_oracle.py", derived)
        verifier = CommandHardVerifier(
            ("{python}", "-m", "unittest", "discover", "-s", ".", "-p", "test_oracle.py"),
            extra_files={"test_oracle.py": "import unittest\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n"},
        )
        result = VerificationRunner.default(event_sink=InMemoryEventSink()).run(
            TaskContract("t", (), metadata={"allowed_paths": ["math_lib.py"]}),
            CandidateArtifact.from_text(
                "oracle-visible",
                "coding_patch",
                encode_coding_bundle({}, {"math_lib.py": "def add(a, b):\n    return a + b\n"}),
                {"allowed_paths": ["math_lib.py"]},
            ),
            verifier,
        )
        for observation in result.observations:
            blob = json.dumps(observation.to_dict())
            self.assertNotIn("test_oracle.py", blob)

    def test_hard_outcome_not_visible_to_checklets(self) -> None:
        self.assertIn("hard_verifier_outcome", FORBIDDEN_CHECKLET_CONTEXT_KEYS)
        self.assertEqual(
            [FailureCode.LABEL_CONTAMINATION],
            checklet_context_is_clean({"hard_verifier_outcome": "accepted"}),
        )

    def test_criterion_labels_not_visible_to_checklets(self) -> None:
        self.assertIn("criterion_labels", FORBIDDEN_CHECKLET_CONTEXT_KEYS)
        self.assertIn("criterion_adjudications", FORBIDDEN_CHECKLET_CONTEXT_KEYS)
        payload = json.loads(FIXTURE_SET.read_text(encoding="utf-8"))
        fixture = payload["fixtures"][0]
        manifest = fixture_to_manifest(fixture)
        record = ingest_task_manifest(manifest)
        for observation in record.checklet_observations:
            metadata = observation.get("metadata") or {}
            self.assertFalse(set(metadata) & FORBIDDEN_CHECKLET_CONTEXT_KEYS)

    def test_ingestion_strips_fixture_labels(self) -> None:
        payload = json.loads(FIXTURE_SET.read_text(encoding="utf-8"))
        fixture = payload["fixtures"][1]
        fixture["artifact"]["metadata"] = dict(fixture["artifact"]["metadata"])
        fixture["artifact"]["metadata"]["hard_verifier_outcome"] = "rejected"
        fixture["artifact"]["metadata"]["expected_affected_checklets"] = ["requirement_coverage"]
        record = ingest_task_manifest(fixture_to_manifest(fixture))
        self.assertNotIn("hard_verifier_outcome", record.task_contract.get("metadata", {}))
        self.assertTrue(all("hard_verifier_outcome" not in (item.get("metadata") or {}) for item in record.checklet_observations))

    def test_partition_contamination_fails_closed(self) -> None:
        from verification_v1.integrity import validate_dataset_records

        family = "same-lineage"
        records = (
            make_record(name="dev-copy", task_family_id=family, partition=Partition.DEVELOPMENT, repository_id="repo-x"),
            make_record(name="hold-copy", task_family_id=family, partition=Partition.HOLDOUT, repository_id="repo-x"),
        )
        result = validate_dataset_records(records)
        self.assertFalse(result["ok"])
        self.assertTrue(any("PARTITION_LEAKAGE" in item["codes"] for item in result["blocking"]))

    def test_oracle_overlap_is_injection_failure(self) -> None:
        manifest = {
            "task": {"task_id": "overlap", "requirements": [], "metadata": {"allowed_paths": ["test_oracle.py"]}},
            "artifact": {
                "artifact_id": "overlap-art",
                "artifact_type": "coding_patch",
                "content": encode_coding_bundle({}, {"test_oracle.py": "def x():\n    return 1\n"}),
                "metadata": {"allowed_paths": ["test_oracle.py"]},
            },
            "hard_command": ["{python}", "-c", "raise SystemExit(0)"],
            "reference_files": {"test_oracle.py": "import unittest\n"},
            "task_origin": "engineering_fixture",
            "task_family_id": "overlap",
            "repository_id": "engineering://overlap",
        }
        with self.assertRaises(ValueError) as raised:
            ingest_task_manifest(manifest)
        self.assertIn("ORACLE_INJECTION_FAILED", str(raised.exception))
