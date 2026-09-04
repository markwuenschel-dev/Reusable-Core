import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def test_list_checklets_and_run_entry_points(self) -> None:
        listed = subprocess.run(
            [sys.executable, "-m", "verification_v1", "list-checklets"],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        self.assertEqual(0, listed.returncode, listed.stderr)
        self.assertGreaterEqual(len(json.loads(listed.stdout)["checklets"]), 4)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = root / "task.json"
            artifact = root / "artifact.json"
            task.write_text(json.dumps({"task_id": "cli-task", "requirements": []}), encoding="utf-8")
            artifact.write_text(
                json.dumps(
                    {
                        "artifact_id": "cli-artifact", "artifact_type": "coding_patch", "content": "pass\n",
                        "metadata": {"changed_paths": [], "allowed_paths": [], "producer_test_cases": [],
                                     "covered_requirements": [], "boundary_cases": [], "handled_boundary_cases": [], "signature_changes": []},
                    }
                ),
                encoding="utf-8",
            )
            run = subprocess.run(
                [
                    sys.executable, "-m", "verification_v1", "run", str(task), str(artifact),
                    "--hard-command", f'"{sys.executable}" -c "import sys; sys.exit(0)"',
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )

        self.assertEqual(0, run.returncode, run.stderr)
        self.assertEqual("accepted", json.loads(run.stdout)["final_outcome"])

    def test_v12_baseline_and_metric_report_commands(self) -> None:
        baseline = subprocess.run(
            [sys.executable, "-m", "verification_v1", "validate-baseline"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        payload = json.loads(baseline.stdout)
        self.assertTrue(payload.get("content_match"), baseline.stderr)
        if payload.get("ok"):
            self.assertEqual(0, baseline.returncode, baseline.stderr)
        else:
            self.assertEqual(1, baseline.returncode, baseline.stderr)
            self.assertFalse(payload.get("snapshot_tracked"))
        with tempfile.TemporaryDirectory() as directory:
            analyzed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "verification_v1",
                    "analyze-v12",
                    "evals/verification_v1/v12/metric_integrity_dataset.json",
                    "--report-dir",
                    directory,
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        self.assertEqual(0, analyzed.returncode, analyzed.stderr)
        payload = json.loads(analyzed.stdout)
        self.assertEqual("COLLECT_MORE_V1_2_DATA", payload["decision"])
        self.assertTrue(Path(payload["artifacts"]["json"]).name == "v12_latest.json")


if __name__ == "__main__":
    unittest.main()
