import unittest
from dataclasses import replace
from time import sleep

from verification_v1.artifacts import ArtifactStore
from verification_v1.checklets import BaseCodingChecklet, CheckletContext, CheckletRegistry
from verification_v1.contracts import CheckletVerdict, TaskContract
from verification_v1.runner import CandidateArtifact


class StructuredMappingChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("structured_mapping", "structured-output", "Returns a valid structured observation mapping.")

    def evaluate(self, context: CheckletContext):
        return self.observation(context, CheckletVerdict.CLEAN).to_dict()


class TimedOutChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("timed_out", "timeout-semantics", "Exceeds its declared runtime budget.")
        self.spec = replace(self.spec, timeout_seconds=0.001)

    def evaluate(self, context: CheckletContext):
        sleep(0.02)
        return self.observation(context, CheckletVerdict.CLEAN)


class CheckletContractTests(unittest.TestCase):
    def test_valid_structured_mapping_becomes_clean_observation(self) -> None:
        artifact = ArtifactStore().register(
            CandidateArtifact.from_text(
                "structured-artifact",
                "coding_patch",
                "pass\n",
                {"changed_paths": [], "allowed_paths": []},
            ),
            "run-structured",
        )
        context = CheckletContext(TaskContract("structured-task", ()), artifact)

        observations = CheckletRegistry((StructuredMappingChecklet(),)).run_all(context)

        self.assertEqual(CheckletVerdict.CLEAN, observations[0].verdict)
        self.assertEqual(artifact.artifact_digest, observations[0].artifact_digest)

    def test_required_checklet_timeout_becomes_typed_error(self) -> None:
        artifact = ArtifactStore().register(
            CandidateArtifact.from_text("timeout-artifact", "coding_patch", "pass\n", {"changed_paths": [], "allowed_paths": []}),
            "run-timeout",
        )
        observations = CheckletRegistry((TimedOutChecklet(),)).run_all(CheckletContext(TaskContract("timeout-task", ()), artifact))

        self.assertEqual(CheckletVerdict.ERROR, observations[0].verdict)
        self.assertIn("timeout", observations[0].summary)


if __name__ == "__main__":
    unittest.main()
