"""Hard-verifier hardening.

INTEG-007 materialisation failure was swallowed and the oracle then ran against a
          partial workspace, so a REJECTED verdict was indistinguishable from a
          real defect.
INTEG-027 timeout_seconds bounded one process, and capture_output pipes are
          inherited by descendants -- so a grandchild that outlives its parent
          kept the verifier blocked well past its own bound.
INTEG-029 the chmod/rehash integrity guard protected candidate.artifact, a file
          the oracle command never reads. The executed surface is the workspace.
INTEG-031 the empty-test-run branch required the literal string 'NO TESTS RAN'
          in interpreter output, so a wording change silently reclassified an
          infrastructure failure as a genuine rejection.
"""

import time
import unittest

from verification_v1.artifacts import ArtifactStore, CandidateArtifact
from verification_v1.bundle import encode_coding_bundle
from verification_v1.contracts import HardVerifierOutcome, TaskContract
from verification_v1.hard_verify import CommandHardVerifier


def _registered(overlay):
    artifact = CandidateArtifact.from_text(
        artifact_id="candidate",
        artifact_type="coding_patch",
        content=encode_coding_bundle(base_files={}, overlay=overlay),
        metadata={},
    )
    return ArtifactStore().register(artifact, run_id="run")


def _verify(overlay, command, *, timeout=60.0, extra_files=None):
    return CommandHardVerifier(
        command=command, timeout_seconds=timeout, extra_files=extra_files or {}
    ).verify(TaskContract(task_id="t", requirements=("r",)), _registered(overlay))


OK = ("{python}", "-c", "import sys; sys.exit(0)")


class MaterialisationFailsClosedTest(unittest.TestCase):
    def test_partial_workspace_is_infrastructure_error_not_rejection(self) -> None:
        """'x' is written as a file, then 'x/y.py' needs 'x' to be a directory.
        The oracle must not run against the half-built workspace."""
        result = _verify({"x": "data\n", "x/y.py": "value = 1\n"}, OK)
        self.assertEqual(result.outcome, HardVerifierOutcome.INFRASTRUCTURE_ERROR)
        self.assertIn("workspace_materialization_failed", result.evidence_refs)

    def test_healthy_bundle_still_runs(self) -> None:
        result = _verify({"calc.py": "x = 1\n"}, OK)
        self.assertEqual(result.outcome, HardVerifierOutcome.ACCEPTED)


class EmptyTestRunIsStructuralTest(unittest.TestCase):
    def test_exit_five_without_the_magic_string_is_infrastructure_error(self) -> None:
        result = _verify({"calc.py": "x = 1\n"}, ("{python}", "-c", "import sys; sys.exit(5)"))
        self.assertEqual(result.outcome, HardVerifierOutcome.INFRASTRUCTURE_ERROR)

    def test_ordinary_failure_is_still_a_rejection(self) -> None:
        result = _verify({"calc.py": "x = 1\n"}, ("{python}", "-c", "import sys; sys.exit(1)"))
        self.assertEqual(result.outcome, HardVerifierOutcome.REJECTED)


class WorkspaceIntegrityTest(unittest.TestCase):
    def test_candidate_file_rewritten_by_the_command_is_detected(self) -> None:
        """The executed surface is the workspace, so that is what must be
        attested -- not the serialized artifact the command never opens."""
        tamper = (
            "{python}",
            "-c",
            "open('calc.py','w').write('rewritten by the candidate\\n')",
        )
        result = _verify({"calc.py": "x = 1\n"}, tamper)
        self.assertIn("workspace_digest_mismatch", result.evidence_refs)
        self.assertEqual(result.outcome, HardVerifierOutcome.INFRASTRUCTURE_ERROR)

    def test_bytecode_cache_is_not_treated_as_tampering(self) -> None:
        """Importing a module writes __pycache__; that must not trip the guard."""
        overlay = {"calc.py": "VALUE = 1\n"}
        importer = ("{python}", "-c", "import calc; assert calc.VALUE == 1")
        result = _verify(overlay, importer)
        self.assertEqual(result.outcome, HardVerifierOutcome.ACCEPTED)
        self.assertNotIn("workspace_digest_mismatch", result.evidence_refs)


class WallClockBoundTest(unittest.TestCase):
    def test_timeout_is_enforced(self) -> None:
        started = time.monotonic()
        result = _verify(
            {"calc.py": "x = 1\n"},
            ("{python}", "-c", "import time; time.sleep(30)"),
            timeout=3.0,
        )
        elapsed = time.monotonic() - started
        self.assertEqual(result.outcome, HardVerifierOutcome.OUTCOME_UNKNOWN)
        self.assertIn("command_timeout", result.evidence_refs)
        self.assertLess(elapsed, 20.0, f"timeout was not a wall-clock bound ({elapsed:.1f}s)")

    def test_detached_grandchild_does_not_hold_the_verifier_open(self) -> None:
        """A grandchild inherits captured pipes. The parent exits immediately;
        the verifier must not wait on the grandchild's lifetime."""
        spawn = (
            "{python}",
            "-c",
            "import subprocess,sys;"
            "subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']);"
            "sys.exit(0)",
        )
        started = time.monotonic()
        result = _verify({"calc.py": "x = 1\n"}, spawn, timeout=60.0)
        elapsed = time.monotonic() - started
        self.assertEqual(result.outcome, HardVerifierOutcome.ACCEPTED)
        self.assertLess(elapsed, 20.0, f"verifier blocked on a grandchild ({elapsed:.1f}s)")


if __name__ == "__main__":
    unittest.main()
