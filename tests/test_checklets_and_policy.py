import unittest
from collections.abc import Mapping
from dataclasses import replace
from time import perf_counter, sleep
from types import MappingProxyType

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


class HostilePickleChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("hostile_pickle", "transport-safety", "Must never be pickled by the parent process.")

    def __reduce__(self):
        raise AssertionError("checklet instance must not be pickled in the parent process")

    def evaluate(self, context: CheckletContext):
        return self.observation(context, CheckletVerdict.CLEAN)


class BlockingMapping(Mapping):
    def __getitem__(self, key):
        raise KeyError(key)

    def __iter__(self):
        sleep(5)
        return iter(())

    def __len__(self):
        return 0

    def items(self):
        sleep(5)
        return ()


class BlockingContainerChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("blocking_container", "transport-boundary", "Carries a hostile container in state.")
        self.blocking = BlockingMapping()

    def evaluate(self, context: CheckletContext):
        return self.observation(context, CheckletVerdict.CLEAN)


class OversizedKeyChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("oversized_key", "transport-boundary", "Carries an oversized transport key.")
        self.payload = {"x" * 65_537: "value"}

    def evaluate(self, context: CheckletContext):
        return self.observation(context, CheckletVerdict.CLEAN)


class EmptyCompositeChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("empty_composite", "transport-boundary", "Carries too many empty transport nodes.")
        self.payload = [() for _ in range(4_097)]

    def evaluate(self, context: CheckletContext):
        return self.observation(context, CheckletVerdict.CLEAN)


class HugeIntegerChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("huge_integer", "transport-boundary", "Carries an oversized integer transport value.")
        self.payload = 1 << 8_000_000

    def evaluate(self, context: CheckletContext):
        return self.observation(context, CheckletVerdict.CLEAN)


class ProxyWrappedBlockingChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("proxy_blocking", "transport-boundary", "Carries a proxy-wrapped hostile mapping.")
        self.blocking = MappingProxyType(BlockingMapping())

    def evaluate(self, context: CheckletContext):
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

    def test_isolated_checklet_uses_bounded_descriptor_not_instance_pickling(self) -> None:
        artifact = ArtifactStore().register(
            CandidateArtifact.from_text("transport-artifact", "coding_patch", "pass\n", {"changed_paths": []}),
            "run-transport",
        )

        observations = CheckletRegistry((HostilePickleChecklet(),)).run_all(
            CheckletContext(TaskContract("transport-task", ()), artifact)
        )

        self.assertEqual(CheckletVerdict.CLEAN, observations[0].verdict)

    def test_untrusted_checklet_state_is_rejected_without_parent_side_iteration(self) -> None:
        artifact = ArtifactStore().register(
            CandidateArtifact.from_text("bounded-artifact", "coding_patch", "pass\n", {"changed_paths": []}),
            "run-bounded",
        )
        started = perf_counter()
        observations = CheckletRegistry((BlockingContainerChecklet(),)).run_all(
            CheckletContext(TaskContract("bounded-task", ()), artifact)
        )

        self.assertLess(perf_counter() - started, 1.0)
        self.assertEqual(CheckletVerdict.ERROR, observations[0].verdict)
        self.assertIn("unsupported checklet transport value", observations[0].summary)

    def test_oversized_checklet_transport_key_is_rejected_before_process_start(self) -> None:
        artifact = ArtifactStore().register(
            CandidateArtifact.from_text("key-artifact", "coding_patch", "pass\n", {"changed_paths": []}),
            "run-key",
        )

        observations = CheckletRegistry((OversizedKeyChecklet(),)).run_all(
            CheckletContext(TaskContract("key-task", ()), artifact)
        )

        self.assertEqual(CheckletVerdict.ERROR, observations[0].verdict)
        self.assertIn("mapping key exceeds", observations[0].summary)

    def test_empty_composite_nodes_count_toward_transport_limit(self) -> None:
        artifact = ArtifactStore().register(
            CandidateArtifact.from_text("composite-artifact", "coding_patch", "pass\n", {"changed_paths": []}),
            "run-composite",
        )

        observations = CheckletRegistry((EmptyCompositeChecklet(),)).run_all(
            CheckletContext(TaskContract("composite-task", ()), artifact)
        )

        self.assertEqual(CheckletVerdict.ERROR, observations[0].verdict)
        self.assertIn("item count exceeds", observations[0].summary)

    def test_huge_integer_is_rejected_by_transport_byte_limit(self) -> None:
        artifact = ArtifactStore().register(
            CandidateArtifact.from_text("integer-artifact", "coding_patch", "pass\n", {"changed_paths": []}),
            "run-integer",
        )

        observations = CheckletRegistry((HugeIntegerChecklet(),)).run_all(
            CheckletContext(TaskContract("integer-task", ()), artifact)
        )

        self.assertEqual(CheckletVerdict.ERROR, observations[0].verdict)
        self.assertIn("byte count exceeds", observations[0].summary)

    def test_proxy_wrapped_hostile_mapping_is_rejected_without_parent_side_iteration(self) -> None:
        artifact = ArtifactStore().register(
            CandidateArtifact.from_text("proxy-artifact", "coding_patch", "pass\n", {"changed_paths": []}),
            "run-proxy",
        )
        started = perf_counter()
        observations = CheckletRegistry((ProxyWrappedBlockingChecklet(),)).run_all(
            CheckletContext(TaskContract("proxy-task", ()), artifact)
        )

        self.assertLess(perf_counter() - started, 1.0)
        self.assertEqual(CheckletVerdict.ERROR, observations[0].verdict)
        self.assertIn("unsupported checklet transport value", observations[0].summary)


if __name__ == "__main__":
    unittest.main()
