import unittest

from verification_v1.domain import CodingDomainPack, DomainPackRegistry
from verification_v1.runner import VerificationRunner


class DomainPackTests(unittest.TestCase):
    def test_coding_checklets_are_registered_by_a_domain_pack_not_runner_logic(self) -> None:
        registry = DomainPackRegistry()
        pack = CodingDomainPack.default()
        registry.register(pack)

        resolved = registry.resolve("coding-v1")
        runner = VerificationRunner.from_domain_pack(resolved)

        self.assertEqual("coding-v1", resolved.pack_id)
        self.assertEqual(("coding_patch",), resolved.artifact_types)
        self.assertGreaterEqual(len(resolved.checklet_ids), 4)
        self.assertEqual("coding-v1", runner.domain_pack_id)
        self.assertEqual(set(resolved.checklet_ids), {spec.checklet_id for spec in runner.checklets.specs})


if __name__ == "__main__":
    unittest.main()
