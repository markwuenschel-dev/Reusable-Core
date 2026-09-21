"""INTEG-008 and INTEG-012.

INTEG-008 validate-baseline regenerated its own reference from the same live tree
          it was validating when the manifest was absent, and treated "this path
          is known to Git" as "this content matches Git".
INTEG-012 evaluate, analyze-v12 and replay-v12 returned 0 regardless of what they
          computed, so the CI steps invoking them could only fail by crashing.
"""

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = REPO / "evals" / "verification_v1" / "engineering_fixture_set.json"
METRIC_DATASET = REPO / "evals" / "verification_v1" / "v12" / "metric_integrity_dataset.json"


def _cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "verification_v1", *args],
        capture_output=True,
        text=True,
        cwd=str(cwd or REPO),
    )


class EvaluateExitCodeTest(unittest.TestCase):
    def test_clean_fixture_set_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as reports:
            result = _cli("evaluate", str(FIXTURES), "--report-dir", reports)
            self.assertEqual(0, result.returncode, result.stderr[-2000:])
            payload = json.loads(result.stdout)
            self.assertEqual(
                0, payload["report"]["shadow_metrics"]["false_shadow_waiver_count"]
            )


class AnalyzeExitCodeTest(unittest.TestCase):
    def test_valid_dataset_exits_zero_and_reports_validator_state(self) -> None:
        with tempfile.TemporaryDirectory() as reports:
            result = _cli("analyze-v12", str(METRIC_DATASET), "--report-dir", reports)
            self.assertEqual(0, result.returncode, result.stderr[-2000:])
            payload = json.loads(result.stdout)
            self.assertTrue(payload["validator_ok"])
            # the decision itself is informational, not a pass/fail gate
            self.assertEqual("COLLECT_MORE_V1_2_DATA", payload["decision"])


class ValidateBaselineDoesNotMintItselfTest(unittest.TestCase):
    def test_absent_runtime_manifest_fails_instead_of_regenerating(self) -> None:
        """Previously the manifest was written from the live tree and then
        'validated' against it, which can never fail."""
        from verification_v1.baseline import runtime_manifest_path

        manifest = runtime_manifest_path(REPO)
        with tempfile.TemporaryDirectory() as directory:
            stash = pathlib.Path(directory) / manifest.name
            shutil.copy2(manifest, stash)
            manifest.unlink()
            try:
                result = _cli("validate-baseline")
                self.assertEqual(1, result.returncode, result.stdout[-2000:])
                payload = json.loads(result.stdout)
                self.assertFalse(payload["ok"])
                self.assertFalse(manifest.exists(), "must not mint its own reference")
            finally:
                shutil.copy2(stash, manifest)
        # restored
        self.assertEqual(0, _cli("validate-baseline").returncode)

    def test_snapshot_tracking_requires_content_match_not_just_a_known_path(self) -> None:
        from verification_v1.baseline import runtime_snapshot_path, validate_baseline

        before = validate_baseline(root=REPO)
        self.assertTrue(before["snapshot_path_tracked"])
        self.assertTrue(before["snapshot_content_matches_git"])

        snapshot = runtime_snapshot_path(REPO)
        original = snapshot.read_bytes()
        try:
            payload = json.loads(original.decode("utf-8"))
            payload["schema_version"] = "tampered/0"
            snapshot.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            after = validate_baseline(root=REPO)
            # the path is still tracked, but its content no longer matches Git
            self.assertTrue(after["snapshot_path_tracked"])
            self.assertFalse(after["snapshot_content_matches_git"])
            self.assertFalse(after["snapshot_tracked"])
        finally:
            snapshot.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
