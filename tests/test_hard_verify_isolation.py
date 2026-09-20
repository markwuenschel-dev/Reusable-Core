"""INTEG-026: the candidate artifact must not be able to influence the interpreter
that judges it.

The hard verifier runs the oracle command with the candidate's own materialized
workspace as cwd and on PYTHONPATH. CPython imports ``sitecustomize`` (and
``usercustomize``) from sys.path during interpreter startup, before any test
module is collected -- so a candidate that bundles one of those files executes
arbitrary code ahead of the oracle and can force the process exit status.
"""

import unittest

from verification_v1.artifacts import ArtifactStore, CandidateArtifact
from verification_v1.bundle import BundleParseError, encode_coding_bundle
from verification_v1.contracts import HardVerifierOutcome, TaskContract
from verification_v1.hard_verify import CommandHardVerifier


ORACLE = {
    "test_oracle.py": (
        "import unittest\n"
        "from calc import add\n"
        "\n"
        "class T(unittest.TestCase):\n"
        "    def test_add(self):\n"
        "        self.assertEqual(add(2, 3), 5)\n"
    )
}
HARD_COMMAND = ("{python}", "-m", "unittest", "discover", "-s", ".", "-p", "test_oracle.py")

# Genuinely defective: subtraction where addition was required.
BROKEN = {"calc.py": "def add(a, b):\n    return a - b\n"}


def _verify(overlay):
    artifact = CandidateArtifact.from_text(
        artifact_id="candidate",
        artifact_type="coding_patch",
        content=encode_coding_bundle(base_files={}, overlay=overlay),
        metadata={},
    )
    registered = ArtifactStore().register(artifact, run_id="run")
    task = TaskContract(task_id="task", requirements=("add returns a + b",))
    verifier = CommandHardVerifier(
        command=HARD_COMMAND, timeout_seconds=60.0, extra_files=ORACLE
    )
    return verifier.verify(task, registered)


class HardVerifierInterpreterIsolationTest(unittest.TestCase):
    def test_broken_candidate_is_rejected(self) -> None:
        """Control: without an escape hatch the defect is caught."""
        result = _verify(BROKEN)
        self.assertEqual(result.outcome, HardVerifierOutcome.REJECTED)

    def test_candidate_cannot_bundle_sitecustomize(self) -> None:
        """A bundled sitecustomize.py must never reach the workspace."""
        overlay = dict(BROKEN)
        overlay["sitecustomize.py"] = "import os\nos._exit(0)\n"
        with self.assertRaises(BundleParseError):
            encode_coding_bundle(base_files={}, overlay=overlay)

    def test_candidate_cannot_bundle_usercustomize(self) -> None:
        overlay = dict(BROKEN)
        overlay["usercustomize.py"] = "import os\nos._exit(0)\n"
        with self.assertRaises(BundleParseError):
            encode_coding_bundle(base_files={}, overlay=overlay)

    def test_candidate_cannot_shadow_the_oracle_runner(self) -> None:
        """cwd precedes stdlib on sys.path, so a bundled unittest.py would win."""
        overlay = dict(BROKEN)
        overlay["unittest.py"] = "raise SystemExit(0)\n"
        with self.assertRaises(BundleParseError):
            encode_coding_bundle(base_files={}, overlay=overlay)

    def test_reserved_name_is_rejected_at_parse_time_too(self) -> None:
        """Bundles are also accepted as raw bytes; the guard must hold there."""
        from verification_v1.bundle import parse_coding_bundle

        import json as _json

        payload = _json.dumps(
            {
                "format": "coding_bundle/1.0.0",
                "base_files": {},
                "overlay": {"sitecustomize.py": "import os\nos._exit(0)\n"},
            }
        ).encode("utf-8")
        with self.assertRaises(BundleParseError):
            parse_coding_bundle(payload, {})

    def test_nested_sitecustomize_is_allowed(self) -> None:
        """Only top-level importable names are dangerous; pkg/sitecustomize.py is not."""
        overlay = dict(BROKEN)
        overlay["pkg/sitecustomize.py"] = "x = 1\n"
        encoded = encode_coding_bundle(base_files={}, overlay=overlay)
        self.assertIn("pkg/sitecustomize.py", encoded)


if __name__ == "__main__":
    unittest.main()
