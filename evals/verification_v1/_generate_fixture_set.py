"""Generate the VS-V1.1 engineering fixture set. Not part of the runtime package."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verification_v1.bundle import encode_coding_bundle


def _ref_cmd() -> list[str]:
    return ["{python}", "-m", "unittest", "discover", "-s", ".", "-p", "test_oracle.py"]


def build_fixtures() -> dict:
    fixtures = [
        {
            "fixture_id": "clean-minimal-patch",
            "split": "development",
            "task": {
                "task_id": "clean-minimal",
                "requirements": [],
                "description": "A deliberately small, valid coding change.",
                "metadata": {"allowed_paths": ["math_lib.py", "test_math_lib.py"]},
            },
            "artifact": {
                "artifact_id": "clean-minimal-artifact",
                "artifact_type": "coding_patch",
                "content": encode_coding_bundle(
                    {},
                    {
                        "math_lib.py": "def add(left, right):\n    return left + right\n",
                        "test_math_lib.py": (
                            "from math_lib import add\n\n"
                            "def test_add():\n    assert add(1, 2) == 3\n"
                        ),
                    },
                ),
                "metadata": {
                    "changed_paths": ["math_lib.py"],
                    "allowed_paths": ["math_lib.py"],
                    "producer_test_cases": ["test_add"],
                    "test_cases_by_requirement": {},
                    "covered_requirements": [],
                    "boundary_cases": [],
                    "handled_boundary_cases": [],
                    "signature_changes": [],
                },
            },
            "hard_command": _ref_cmd(),
            "reference_files": {
                "test_oracle.py": (
                    "import unittest\nfrom math_lib import add\n\n"
                    "class ReferenceTests(unittest.TestCase):\n"
                    "    def test_reference_add(self):\n"
                    "        self.assertEqual(add(2, 3), 5)\n"
                ),
            },
            "hard_verifier_outcome": "accepted",
            "expected_defect_class": None,
            "expected_affected_checklets": [],
        },
        {
            "fixture_id": "requirement-omitted",
            "split": "development",
            "task": {
                "task_id": "zero-for-empty",
                "requirements": ["return-zero-for-empty"],
                "description": "Empty input must return zero.",
                "metadata": {"allowed_paths": ["stats.py", "test_stats.py"]},
            },
            "artifact": {
                "artifact_id": "requirement-omitted-artifact",
                "artifact_type": "coding_patch",
                "content": encode_coding_bundle(
                    {},
                    {
                        "stats.py": "def total(items):\n    return items[0] + sum(items[1:])\n",
                        "test_stats.py": (
                            "from stats import total\n\n"
                            "def test_return_zero_for_empty():\n    assert total([1, 2]) == 3\n"
                        ),
                    },
                ),
                "metadata": {
                    "changed_paths": ["stats.py", "test_stats.py"],
                    "allowed_paths": ["stats.py", "test_stats.py"],
                    "producer_test_cases": ["test_return_zero_for_empty"],
                    "test_cases_by_requirement": {"return-zero-for-empty": ["test_return_zero_for_empty"]},
                    "covered_requirements": ["return-zero-for-empty"],
                    "boundary_cases": [],
                    "handled_boundary_cases": [],
                    "signature_changes": [],
                },
            },
            "hard_command": _ref_cmd(),
            "reference_files": {
                "test_oracle.py": (
                    "import unittest\nfrom stats import total\n\n"
                    "class ReferenceTests(unittest.TestCase):\n"
                    "    def test_empty_returns_zero(self):\n"
                    "        self.assertEqual(total([]), 0)\n"
                ),
            },
            "hard_verifier_outcome": "rejected",
            "expected_defect_class": "requirement_omitted",
            "expected_affected_checklets": ["requirement_coverage"],
        },
        {
            "fixture_id": "missing-producer-test",
            "split": "development",
            "task": {
                "task_id": "sort-unique",
                "requirements": ["sort-unique-values"],
                "description": "Return sorted unique values.",
                "metadata": {"allowed_paths": ["unique.py", "test_unique.py"]},
            },
            "artifact": {
                "artifact_id": "missing-producer-test-artifact",
                "artifact_type": "coding_patch",
                "content": encode_coding_bundle(
                    {},
                    {"unique.py": "def unique(values):\n    return sorted(set(values))\n"},
                ),
                "metadata": {
                    "changed_paths": ["unique.py"],
                    "allowed_paths": ["unique.py"],
                    "producer_test_cases": ["test_unique"],
                    "test_cases_by_requirement": {"sort-unique-values": ["test_unique"]},
                    "covered_requirements": ["sort-unique-values"],
                    "boundary_cases": [],
                    "handled_boundary_cases": [],
                    "signature_changes": [],
                },
            },
            "hard_command": _ref_cmd(),
            "reference_files": {
                "test_oracle.py": (
                    "import unittest\nfrom unique import unique\n\n"
                    "class ReferenceTests(unittest.TestCase):\n"
                    "    def test_reference_unique(self):\n"
                    "        self.assertEqual(unique([2, 1, 2]), [1, 2])\n"
                ),
            },
            "hard_verifier_outcome": "accepted",
            "expected_defect_class": "missing_test",
            "expected_affected_checklets": ["test_adequacy"],
        },
        {
            "fixture_id": "unrelated-scope-change",
            "split": "development",
            "task": {
                "task_id": "change-scope",
                "requirements": [],
                "description": "Touch only the requested module.",
                "metadata": {"allowed_paths": ["wanted.py"]},
            },
            "artifact": {
                "artifact_id": "scope-artifact",
                "artifact_type": "coding_patch",
                "content": encode_coding_bundle(
                    {},
                    {
                        "wanted.py": "def wanted():\n    return True\n",
                        "infra/release.py": "def release():\n    return 'ship it'\n",
                    },
                ),
                "metadata": {
                    "changed_paths": ["wanted.py"],
                    "allowed_paths": ["wanted.py", "infra/release.py"],
                    "producer_test_cases": ["test_wanted"],
                    "test_cases_by_requirement": {},
                    "covered_requirements": [],
                    "boundary_cases": [],
                    "handled_boundary_cases": [],
                    "signature_changes": [],
                },
            },
            "hard_command": _ref_cmd(),
            "reference_files": {
                "test_oracle.py": (
                    "import unittest\nfrom wanted import wanted\n\n"
                    "class ReferenceTests(unittest.TestCase):\n"
                    "    def test_wanted(self):\n"
                    "        self.assertTrue(wanted())\n"
                ),
            },
            "hard_verifier_outcome": "accepted",
            "expected_defect_class": "unrelated_change",
            "expected_affected_checklets": ["change_scope"],
        },
        {
            "fixture_id": "unupdated-interface",
            "split": "development",
            "task": {
                "task_id": "interface-update",
                "requirements": [],
                "description": "A public signature change with a missing consumer update.",
                "metadata": {"allowed_paths": ["sender.py", "client.py"]},
            },
            "artifact": {
                "artifact_id": "dependency-artifact",
                "artifact_type": "coding_patch",
                "content": encode_coding_bundle(
                    {
                        "sender.py": "def send(message):\n    return message\n",
                        "client.py": "from sender import send\n\ndef deliver(message):\n    return send(message)\n",
                    },
                    {"sender.py": "def send(message, retry_count):\n    return message\n"},
                ),
                "metadata": {
                    "changed_paths": ["sender.py"],
                    "allowed_paths": ["sender.py"],
                    "producer_test_cases": ["test_send"],
                    "test_cases_by_requirement": {},
                    "covered_requirements": [],
                    "boundary_cases": [],
                    "handled_boundary_cases": [],
                    "signature_changes": [{"symbol": "send", "callsites_updated": True}],
                },
            },
            "hard_command": _ref_cmd(),
            "reference_files": {
                "test_oracle.py": (
                    "import unittest\nfrom client import deliver\n\n"
                    "class ReferenceTests(unittest.TestCase):\n"
                    "    def test_deliver(self):\n"
                    "        self.assertEqual(deliver('hi'), 'hi')\n"
                ),
            },
            "hard_verifier_outcome": "rejected",
            "expected_defect_class": "interface_not_updated",
            "expected_affected_checklets": ["dependency_integration_risk"],
        },
        {
            "fixture_id": "unhandled-boundary",
            "split": "development",
            "task": {
                "task_id": "empty-boundary",
                "requirements": [],
                "description": "An empty input boundary is expected.",
                "metadata": {"allowed_paths": ["first.py"], "boundary_cases": ["empty-input"]},
            },
            "artifact": {
                "artifact_id": "boundary-artifact",
                "artifact_type": "coding_patch",
                "content": encode_coding_bundle(
                    {},
                    {"first.py": "def first(items):\n    return items[0]\n"},
                ),
                "metadata": {
                    "changed_paths": ["first.py"],
                    "allowed_paths": ["first.py"],
                    "producer_test_cases": ["test_first"],
                    "test_cases_by_requirement": {},
                    "covered_requirements": [],
                    "boundary_cases": ["empty-input"],
                    "handled_boundary_cases": ["empty-input"],
                    "signature_changes": [],
                },
            },
            "hard_command": _ref_cmd(),
            "reference_files": {
                "test_oracle.py": (
                    "import unittest\nfrom first import first\n\n"
                    "class ReferenceTests(unittest.TestCase):\n"
                    "    def test_empty_is_safe(self):\n"
                    "        self.assertIsNone(first([]))\n"
                ),
            },
            "hard_verifier_outcome": "rejected",
            "expected_defect_class": "boundary_not_handled",
            "expected_affected_checklets": ["error_boundary"],
        },
        {
            "fixture_id": "clean-large-interface-change",
            "split": "development",
            "task": {
                "task_id": "updated-interface",
                "requirements": [],
                "description": "A justified public change with all consumers updated.",
                "metadata": {"allowed_paths": ["sender.py", "client.py", "test_sender.py"]},
            },
            "artifact": {
                "artifact_id": "clean-interface-artifact",
                "artifact_type": "coding_patch",
                "content": encode_coding_bundle(
                    {
                        "sender.py": "def send(message):\n    return message\n",
                        "client.py": "from sender import send\n\ndef deliver(message):\n    return send(message)\n",
                        "test_sender.py": "from sender import send\n\ndef test_send():\n    assert send('ok') == 'ok'\n",
                    },
                    {
                        "sender.py": "def send(message, retry_count=0):\n    return message\n",
                        "client.py": (
                            "from sender import send\n\n"
                            "def deliver(message):\n    return send(message, retry_count=1)\n"
                        ),
                        "test_sender.py": (
                            "from sender import send\n\n"
                            "def test_send_retry():\n    assert send('ok', retry_count=1) == 'ok'\n"
                        ),
                    },
                ),
                "metadata": {
                    "changed_paths": ["sender.py", "client.py", "test_sender.py"],
                    "allowed_paths": ["sender.py", "client.py", "test_sender.py"],
                    "producer_test_cases": ["test_send_retry"],
                    "test_cases_by_requirement": {},
                    "covered_requirements": [],
                    "boundary_cases": [],
                    "handled_boundary_cases": [],
                    "signature_changes": [{"symbol": "send", "callsites_updated": False}],
                },
            },
            "hard_command": _ref_cmd(),
            "reference_files": {
                "test_oracle.py": (
                    "import unittest\nfrom client import deliver\nfrom sender import send\n\n"
                    "class ReferenceTests(unittest.TestCase):\n"
                    "    def test_updated_callers(self):\n"
                    "        self.assertEqual(deliver('hi'), 'hi')\n"
                    "        self.assertEqual(send('hi', retry_count=2), 'hi')\n"
                ),
            },
            "hard_verifier_outcome": "accepted",
            "expected_defect_class": None,
            "expected_affected_checklets": [],
        },
        {
            "fixture_id": "unknown-reference-outcome",
            "split": "development",
            "task": {
                "task_id": "unknown-oracle",
                "requirements": [],
                "description": "A fixture used to keep unknown outcomes out of success metrics.",
                "metadata": {"allowed_paths": ["uncertain.py"]},
            },
            "artifact": {
                "artifact_id": "unknown-artifact",
                "artifact_type": "coding_patch",
                "content": encode_coding_bundle(
                    {},
                    {"uncertain.py": "def uncertain():\n    return None\n"},
                ),
                "metadata": {
                    "changed_paths": ["uncertain.py"],
                    "allowed_paths": ["uncertain.py"],
                    "producer_test_cases": ["test_uncertain"],
                    "test_cases_by_requirement": {},
                    "covered_requirements": [],
                    "boundary_cases": [],
                    "handled_boundary_cases": [],
                    "signature_changes": [],
                },
            },
            "oracle_unavailable": True,
            "hard_verifier_outcome": "outcome_unknown",
            "expected_defect_class": None,
            "expected_affected_checklets": [],
        },
    ]
    return {
        "dataset_id": "engineering_fixture_set",
        "dataset_version": "1.1.0",
        "fixtures": fixtures,
    }


def main() -> None:
    path = Path(__file__).with_name("engineering_fixture_set.json")
    path.write_text(json.dumps(build_fixtures(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
