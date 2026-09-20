"""INTEG-001 and INTEG-017: evidence that attested nothing.

INTEG-001 `replay-v12 --mode full` defaulted the oracle to a hardcoded
          `sys.exit(0)` stub, and the recovery of the real command was gated on
          an unrelated condition and read a metadata key nothing ever wrote. A
          record whose oracle rejected the candidate replayed as accepted.
INTEG-017 materialized_workspace_digest was assigned candidate_workspace_digest,
          so integrity.validate_record's comparison of the two could never fail.
"""

import json
import pathlib
import unittest

from verification_v1.evidence import FailureCode
from verification_v1.ingestion import fixture_to_manifest, ingest_task_manifest
from verification_v1.v12_report import replay_record

FIXTURES = (
    pathlib.Path(__file__).resolve().parent.parent
    / "evals"
    / "verification_v1"
    / "engineering_fixture_set.json"
)


def _executable_fixture():
    payload = json.loads(FIXTURES.read_text(encoding="utf-8"))
    for fixture in payload["fixtures"]:
        if fixture.get("hard_command") and fixture.get("reference_files"):
            return fixture
    raise unittest.SkipTest("no executable fixture available")


class RecordedCommandTest(unittest.TestCase):
    def test_verifier_records_the_command_it_ran(self) -> None:
        record = ingest_task_manifest(fixture_to_manifest(_executable_fixture()))
        command = (record.hard_verifier_result.get("metadata") or {}).get("command")
        self.assertTrue(command, "the oracle argv must be recorded for replay")
        self.assertIsInstance(command, (list, tuple))
        # The template, not a machine-specific absolute interpreter path.
        self.assertIn("{python}", list(command))

    def test_full_replay_reruns_the_recorded_oracle(self) -> None:
        record = ingest_task_manifest(fixture_to_manifest(_executable_fixture()))
        replayed = replay_record(record, "full")
        self.assertEqual(replayed["hard_outcome"], record.hard_outcome.value)

    def test_full_replay_refuses_a_record_with_no_recorded_command(self) -> None:
        """Previously this substituted `sys.exit(0)` and returned accepted."""
        record = ingest_task_manifest(fixture_to_manifest(_executable_fixture()))
        hard = dict(record.hard_verifier_result)
        metadata = dict(hard.get("metadata") or {})
        metadata.pop("command", None)
        hard["metadata"] = metadata
        import dataclasses

        stripped = dataclasses.replace(record, hard_verifier_result=hard)
        with self.assertRaises(ValueError) as ctx:
            replay_record(stripped, "full")
        self.assertIn(FailureCode.ORACLE_UNAVAILABLE.value, str(ctx.exception))


class MaterialisedDigestTest(unittest.TestCase):
    def test_materialised_digest_comes_from_the_verifier(self) -> None:
        record = ingest_task_manifest(fixture_to_manifest(_executable_fixture()))
        reported = (record.hard_verifier_result.get("metadata") or {}).get(
            "materialized_candidate_files"
        )
        self.assertTrue(reported, "the verifier must report what it materialised")
        self.assertTrue(record.materialized_workspace_digest)

    def test_digest_comparison_is_live(self) -> None:
        """A record whose materialised surface disagrees with the declared one
        must be flagged; previously the two fields were the same value."""
        import dataclasses

        from verification_v1.integrity import validate_record

        record = ingest_task_manifest(fixture_to_manifest(_executable_fixture()))
        self.assertNotIn(FailureCode.DIGEST_MISMATCH, validate_record(record))
        tampered = dataclasses.replace(
            record, materialized_workspace_digest="0" * 64
        )
        self.assertIn(FailureCode.DIGEST_MISMATCH, validate_record(tampered))


if __name__ == "__main__":
    unittest.main()
