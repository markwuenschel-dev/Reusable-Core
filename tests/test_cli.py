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
            )

        self.assertEqual(0, run.returncode, run.stderr)
        self.assertEqual("accepted", json.loads(run.stdout)["final_outcome"])


if __name__ == "__main__":
    unittest.main()
