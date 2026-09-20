import tempfile
import unittest
from pathlib import Path

from verification_v1.aggregation import ShadowAggregator, ShadowPolicy
from verification_v1.baseline import (
    collect_baseline,
    load_frozen_baseline,
    load_source_snapshot,
    restore_source_snapshot,
    validate_baseline,
)
from verification_v1.checklets import default_coding_checklets
from verification_v1.domain import CodingDomainPack
from verification_v1.evidence import EXPERIMENT_BASELINE_ID
from verification_v1.runner import VerificationRunner


class BaselineFreezeTests(unittest.TestCase):
    def test_frozen_v11_control_stays_intact(self) -> None:
        """The V1.1 control is verified from its own stored bytes, so it keeps its
        meaning after the runtime forked away from it."""
        from verification_v1.baseline import validate_frozen_control

        control = validate_frozen_control()
        self.assertTrue(control["ok"], control["errors"])
        self.assertEqual(EXPERIMENT_BASELINE_ID, control["baseline_id"])
        self.assertEqual(
            EXPERIMENT_BASELINE_ID, load_frozen_baseline()["experiment_baseline_id"]
        )

    def test_baseline_manifest_is_frozen(self) -> None:
        from verification_v1.baseline import active_baseline_paths

        manifest_path, _snapshot_path, active_id = active_baseline_paths()
        frozen = load_frozen_baseline(manifest_path)
        live = collect_baseline(baseline_id=active_id)
        result = validate_baseline(frozen)
        self.assertEqual(active_id, frozen["experiment_baseline_id"])
        self.assertTrue(result["content_match"], result["errors"])
        self.assertTrue(result.get("snapshot_reconstructable"), result["errors"])
        if result.get("verification_v1_working_tree_dirty") and not result.get("snapshot_tracked"):
            self.assertFalse(result["ok"])
            self.assertFalse(result["source_reconstructable"])
        else:
            self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(live["implementation_hashes"], frozen["implementation_hashes"])
        self.assertEqual("1.1.0", live["runner"]["version"])
        self.assertEqual("coding-v1", live["domain_pack"]["id"])
        self.assertEqual("1.1.0", live["domain_pack"]["version"])
        self.assertEqual(5, len(live["checklets"]))
        self.assertEqual("shadow-rule-v1.1", live["shadow_policy"]["id"])
        self.assertEqual("1.1.0", live["shadow_policy"]["version"])
        self.assertEqual(("3.11", "3.12", "3.13"), tuple(live["supported_python_versions"]))
        self.assertTrue(result["snapshot_reconstructable"], result["errors"])
        self.assertIn("git_reconstructable", result)
        self.assertEqual(result["ok"], result["collection_ready"])
        snapshot = load_source_snapshot(_snapshot_path)
        with tempfile.TemporaryDirectory() as directory:
            restored = restore_source_snapshot(snapshot, Path(directory))
            self.assertEqual(live["implementation_hashes"], restored)

    def test_v11_component_versions_are_the_experimental_subjects(self) -> None:
        pack = CodingDomainPack.default()
        self.assertEqual(
            (
                "requirement_coverage",
                "test_adequacy",
                "change_scope",
                "dependency_integration_risk",
                "error_boundary",
            ),
            pack.checklet_ids,
        )
        self.assertEqual(5, len(default_coding_checklets()))
        self.assertEqual("1.1.0", VerificationRunner.version)
        policy = ShadowPolicy()
        self.assertEqual("shadow-rule-v1.1", policy.policy_id)
        self.assertIsInstance(ShadowAggregator().policy, ShadowPolicy)
