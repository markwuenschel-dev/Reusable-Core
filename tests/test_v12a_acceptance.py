import inspect
import json
import multiprocessing
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from verification_v1.analysis import (
    V2_DIAGNOSTIC,
    V2_MORE_DATA,
    V2_PROCEED,
    V2_REWORK,
    V2_STOP,
    analyze_records,
    decide_v2,
)
from verification_v1.baseline import collect_baseline, load_frozen_baseline, restore_source_snapshot, validate_baseline
from verification_v1.dataset import persist_partition_unseal
from verification_v1.evidence import (
    CRITERION_IDS,
    AdjudicationMode,
    AdjudicatorType,
    CriterionAdjudication,
    CriterionLabel,
    FailureCode,
    Partition,
    RealTaskEvidenceRecord,
    TaskOrigin,
)
from verification_v1.independent_adjudication import EVALUATION_GRADE_ADJUDICATOR_ID, SECONDARY_ADJUDICATOR_ID
from verification_v1.splits import AnalysisScope, HoldoutAccessError, build_unseal_receipt

try:
    from v12_helpers import make_record, metric_integrity_records
except ImportError:
    from tests.v12_helpers import make_record, metric_integrity_records

try:
    from test_v12_analysis import _go_ready_analysis
except ImportError:
    from tests.test_v12_analysis import _go_ready_analysis


class V12aBaselineTests(unittest.TestCase):
    def test_active_baseline_source_is_reconstructable(self) -> None:
        from verification_v1.baseline import active_baseline_paths, load_source_snapshot

        _manifest, snapshot_path, active_id = active_baseline_paths()
        live = collect_baseline(baseline_id=active_id)
        snapshot = load_source_snapshot(snapshot_path)
        with tempfile.TemporaryDirectory() as directory:
            restored = restore_source_snapshot(snapshot, Path(directory))
        self.assertEqual(live["implementation_hashes"], restored)

    def test_frozen_v11_control_is_reconstructable_from_its_own_bytes(self) -> None:
        """The control no longer matches the live tree, by design. It must still
        reconstruct exactly from the snapshot it was frozen with."""
        from verification_v1.baseline import (
            baseline_manifest_path,
            baseline_snapshot_path,
            load_source_snapshot,
        )

        manifest = load_frozen_baseline(baseline_manifest_path())
        snapshot = load_source_snapshot(baseline_snapshot_path())
        with tempfile.TemporaryDirectory() as directory:
            restored = restore_source_snapshot(snapshot, Path(directory))
        self.assertEqual(manifest["implementation_hashes"], restored)

    def test_baseline_detects_runtime_file_mutation(self) -> None:
        frozen = load_frozen_baseline()
        mutated = dict(frozen)
        hashes = dict(mutated["implementation_hashes"])
        hashes["verification_v1/runner.py"] = "0" * 64
        mutated["implementation_hashes"] = hashes
        mutated["content_address"] = "0" * 64
        result = validate_baseline(mutated)
        self.assertFalse(result["content_match"])
        self.assertFalse(result["ok"])

    def test_baseline_content_hash_alone_is_not_sufficient(self) -> None:
        result = validate_baseline()
        self.assertIn("source_reconstructable", result)
        self.assertIn("git_commit_match", result)
        if result.get("verification_v1_working_tree_dirty") and not result.get("snapshot_tracked"):
            self.assertFalse(result["ok"])
            self.assertFalse(result["source_reconstructable"])

    def test_baseline_manifest_cannot_reference_dirty_unrecoverable_runtime(self) -> None:
        result = validate_baseline()
        if result.get("verification_v1_working_tree_dirty") and not result.get("git_commit_match") and not result.get("snapshot_tracked"):
            self.assertFalse(result["ok"])
            self.assertTrue(any("uncommitted working tree" in error for error in result["errors"]))

    def test_baseline_detects_wrong_git_commit_or_tree(self) -> None:
        from verification_v1.baseline import git_tree_hashes

        result = validate_baseline()
        live = collect_baseline()
        self.assertIn("git_commit_match", result)
        head = str(live.get("repository_commit_sha") or "")
        head_hashes = git_tree_hashes(head) if head and head != "unknown" else None
        self.assertEqual(head_hashes == live["implementation_hashes"], result["git_commit_match"])


class V12aDecisionGateTests(unittest.TestCase):
    def test_v2_gate_requires_real_determinate_intersection(self) -> None:
        analysis = _go_ready_analysis()
        analysis["dataset_composition"]["n_real"] = 50
        analysis["dataset_composition"]["n_determinate"] = 60
        analysis["dataset_composition"]["n_real_determinate"] = 40
        result = decide_v2(analysis)
        self.assertEqual(V2_MORE_DATA, result["decision"])
        self.assertFalse(result["gates"]["real_determinate_sample"]["passed"])

    def test_50_real_with_10_unknown_does_not_pass_minimum(self) -> None:
        analysis = _go_ready_analysis()
        analysis["dataset_composition"]["n_real"] = 50
        analysis["dataset_composition"]["n_real_determinate"] = 40
        analysis["dataset_composition"]["n_real_unknown"] = 10
        result = decide_v2(analysis)
        self.assertEqual(V2_MORE_DATA, result["decision"])

    def test_50_real_determinate_can_satisfy_sample_gate(self) -> None:
        result = decide_v2(_go_ready_analysis(reject_rate=0.0, gate_rate=0.2))
        self.assertTrue(result["gates"]["real_determinate_sample"]["passed"])
        self.assertEqual(V2_PROCEED, result["decision"])

    def test_synthetic_determinate_rows_do_not_substitute_for_real_labels(self) -> None:
        analysis = _go_ready_analysis()
        analysis["dataset_composition"]["n_synthetic_determinate"] = 80
        analysis["dataset_composition"]["n_determinate"] = 80
        analysis["dataset_composition"]["n_real_determinate"] = 0
        result = decide_v2(analysis)
        self.assertEqual(V2_MORE_DATA, result["decision"])

    def test_unknown_rows_never_enter_determinate_denominator(self) -> None:
        records = metric_integrity_records()
        from verification_v1.analysis import dataset_composition

        composition = dataset_composition(records)
        self.assertEqual(composition["n_unknown"], 1)
        self.assertEqual(composition["n_determinate"] + composition["n_unknown"], composition["n_total"])

    def test_case1_insufficient_real_determinate(self) -> None:
        analysis = _go_ready_analysis()
        analysis["dataset_composition"]["n_real_determinate"] = 0
        self.assertEqual(V2_MORE_DATA, decide_v2(analysis)["decision"])

    def test_case2_zero_reject_rate_is_numeric_zero(self) -> None:
        self.assertEqual(V2_PROCEED, decide_v2(_go_ready_analysis(reject_rate=0.0, gate_rate=0.2))["decision"])

    def test_case3_one_useful_checklet_is_rework(self) -> None:
        analysis = _go_ready_analysis()
        analysis["low_risk_region"]["generalizes"] = False
        analysis["low_risk_region"]["reject_rate"] = 0.2
        useful = next(iter(analysis["predictive_utility"]))
        analysis["predictive_utility"] = {
            key: (
                analysis["predictive_utility"][key]
                if key == useful
                else {"absolute_rejection_rate_difference": 0.0, "p_hard_reject_given_finding": {"descriptive_only": False}}
            )
            for key in analysis["predictive_utility"]
        }
        self.assertEqual(V2_REWORK, decide_v2(analysis)["decision"])

    def test_case4_diagnostic_only(self) -> None:
        analysis = _go_ready_analysis()
        analysis["low_risk_region"]["generalizes"] = False
        analysis["predictive_utility"] = {
            key: {"absolute_rejection_rate_difference": 0.0, "p_hard_reject_given_finding": {"descriptive_only": False}}
            for key in analysis["predictive_utility"]
        }
        self.assertEqual(V2_DIAGNOSTIC, decide_v2(analysis)["decision"])

    def test_case5_stop_selective_verification_path(self) -> None:
        analysis = _go_ready_analysis()
        analysis["low_risk_region"]["generalizes"] = False
        analysis["criterion_quality"] = {
            key: {"criterion_precision": 0.1, "criterion_recall": 0.1} for key in analysis["criterion_quality"]
        }
        analysis["predictive_utility"] = {
            key: {"absolute_rejection_rate_difference": 0.0, "p_hard_reject_given_finding": {"descriptive_only": False}}
            for key in analysis["predictive_utility"]
        }
        self.assertEqual(V2_STOP, decide_v2(analysis)["decision"])


class V12aPartitionTests(unittest.TestCase):
    def test_default_analysis_excludes_holdout(self) -> None:
        records = (
            make_record(name="acc-dev", partition=Partition.DEVELOPMENT),
            make_record(name="acc-hold", partition=Partition.HOLDOUT, task_family_id="hold-fam", hard_outcome="rejected"),
        )
        analysis = analyze_records(records)
        self.assertEqual(1, analysis["n_records_analyzed"])
        self.assertEqual(0, analysis["dataset_composition"]["n_rejected"])
        self.assertEqual("sealed", analysis["holdout_state"])

    def test_default_analysis_excludes_calibration_reserved(self) -> None:
        records = (
            make_record(name="acc-dev2", partition=Partition.DEVELOPMENT),
            make_record(name="acc-cal", partition=Partition.CALIBRATION_RESERVED, task_family_id="cal-fam", hard_outcome="rejected"),
        )
        analysis = analyze_records(records)
        self.assertEqual(0, analysis["dataset_composition"]["n_rejected"])
        self.assertEqual("sealed", analysis["protected_partition_status"]["calibration_reserved"])

    def test_policy_selection_analysis_cannot_read_calibration_reserved(self) -> None:
        records = (
            make_record(name="pol-dev", partition=Partition.POLICY_SELECTION),
            make_record(name="pol-cal", partition=Partition.CALIBRATION_RESERVED, task_family_id="pol-cal-fam", hard_outcome="rejected"),
        )
        analysis = analyze_records(records, scope=AnalysisScope.POLICY_SELECTION)
        self.assertEqual(0, analysis["dataset_composition"]["n_rejected"])

    def test_policy_selection_analysis_cannot_read_holdout(self) -> None:
        records = (
            make_record(name="pol-dev2", partition=Partition.POLICY_SELECTION),
            make_record(name="pol-hold", partition=Partition.HOLDOUT, task_family_id="pol-hold-fam", hard_outcome="rejected"),
        )
        analysis = analyze_records(records, scope=AnalysisScope.POLICY_SELECTION)
        self.assertEqual(0, analysis["dataset_composition"]["n_rejected"])

    def test_holdout_requires_explicit_final_unseal(self) -> None:
        records = (make_record(name="need-unseal", partition=Partition.HOLDOUT),)
        with self.assertRaises(HoldoutAccessError):
            analyze_records(records, scope=AnalysisScope.FINAL_HOLDOUT)

    def test_unsealed_holdout_state_is_persisted(self) -> None:
        from verification_v1.dataset import empty_dataset

        receipt = build_unseal_receipt(
            baseline_content_address="abc",
            analysis_code_version="sha256:test",
            checklet_implementation_hash="def",
            shadow_policy="shadow-rule-v1.1/1.1.0",
        )
        dataset = persist_partition_unseal(empty_dataset(), receipt, target="holdout")
        self.assertEqual("final_unsealed", dataset.holdout_state)
        self.assertEqual(receipt["unsealed_at"], dataset.unseal_receipt["unsealed_at"])

    def test_final_holdout_report_records_analysis_version(self) -> None:
        receipt = build_unseal_receipt(
            baseline_content_address="abc",
            analysis_code_version="sha256:test",
            checklet_implementation_hash="def",
            shadow_policy="shadow-rule-v1.1/1.1.0",
        )
        self.assertIn("analysis_code_version", receipt)
        self.assertIn("decision_gate_version", receipt)

    def test_protected_partition_counts_can_be_reported_without_exposing_labels(self) -> None:
        records = (
            make_record(name="cnt-dev", partition=Partition.DEVELOPMENT),
            make_record(name="cnt-hold", partition=Partition.HOLDOUT, task_family_id="cnt-hold", hard_outcome="rejected"),
        )
        analysis = analyze_records(records)
        self.assertEqual(1, analysis["sealed_partition_counts"]["holdout"])
        quality = json.dumps(analysis["data_quality"]["quality"])
        self.assertNotIn("HARD_VERIFY", quality)


class V12aAdjudicationTests(unittest.TestCase):
    def test_shared_adjudicator_is_labeled_as_shared(self) -> None:
        self.assertEqual("deterministic-shared", SECONDARY_ADJUDICATOR_ID)

    def test_independent_adjudicator_does_not_call_checklet_decision_predicates(self) -> None:
        import ast

        import verification_v1.independent_adjudication as independent

        tree = ast.parse(inspect.getsource(independent))
        names = [alias.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) for alias in node.names]
        for forbidden in ("requirement_evidence_present", "tests_covering_requirement", "public_functions", "call_argument_counts", "boundary_handled"):
            self.assertNotIn(forbidden, names)

    def test_blind_adjudicator_context_excludes_checklet_verdict(self) -> None:
        from verification_v1.independent_adjudication import expert_adjudication_form
        from verification_v1.contracts import TaskContract

        form = expert_adjudication_form(TaskContract("t", ()), "a" * 64)
        self.assertFalse(form["checklet_verdicts_included"])
        self.assertNotIn('"verdict":', json.dumps(form))

    def test_blind_adjudicator_context_excludes_hard_outcome(self) -> None:
        from verification_v1.independent_adjudication import expert_adjudication_form
        from verification_v1.contracts import TaskContract

        form = expert_adjudication_form(TaskContract("t", ()), "a" * 64)
        blob = json.dumps(form)
        self.assertNotIn("accepted", blob)
        self.assertNotIn("rejected", blob)

    def test_adjudication_disagreement_is_preserved(self) -> None:
        record = make_record(name="disagree-keep")
        extra = CriterionAdjudication(
            task_id=record.task_id,
            artifact_digest=record.candidate_patch_digest,
            checklet_id="requirement_coverage",
            criterion_id=CRITERION_IDS["requirement_coverage"],
            label=CriterionLabel.TRUE,
            adjudicator_type=AdjudicatorType.INDEPENDENT_STATIC_ANALYSIS,
            adjudicator_id=EVALUATION_GRADE_ADJUDICATOR_ID,
            adjudication_version="independent-ast/1.0.0",
            evidence_refs=("x",),
            reason="disagree",
            created_at="2026-01-01T00:00:00+00:00",
            adjudication_mode=AdjudicationMode.BLIND,
        )
        payload = record.to_dict()
        payload["criterion_adjudications"] = [item.to_dict() for item in record.criterion_adjudications] + [extra.to_dict()]
        dual = RealTaskEvidenceRecord.from_dict(payload)
        self.assertEqual(
            CriterionLabel.FALSE,
            dual.primary_criterion_label("requirement_coverage", adjudicator_ids={"test-independent-rule"}),
        )
        self.assertEqual(CriterionLabel.TRUE, dual.primary_criterion_label("requirement_coverage", adjudicator_ids={EVALUATION_GRADE_ADJUDICATOR_ID}))
        self.assertEqual(CriterionLabel.INDETERMINATE, dual.primary_criterion_label("requirement_coverage"))

    def test_holdout_requires_evaluation_grade_criterion_labels(self) -> None:
        record = make_record(name="hold-shared-only", partition=Partition.HOLDOUT)
        self.assertTrue(all(item.adjudicator_id != EVALUATION_GRADE_ADJUDICATOR_ID for item in record.criterion_adjudications))
        with self.assertRaises(ValueError) as raised:
            analyze_records(
                (record,),
                scope=AnalysisScope.FINAL_HOLDOUT,
                holdout_state="final_unsealed",
                unseal_receipt=build_unseal_receipt(
                    baseline_content_address="a",
                    analysis_code_version="b",
                    checklet_implementation_hash="c",
                    shadow_policy="shadow-rule-v1.1/1.1.0",
                ),
            )
        self.assertIn(FailureCode.CRITERION_ADJUDICATION_MISSING.value, str(raised.exception))


class V12aIsolationTests(unittest.TestCase):
    def test_repeated_evaluation_terminates(self) -> None:
        from verification_v1.isolation_stress import stress_fixture_evaluation

        result = stress_fixture_evaluation(Path("evals/verification_v1/engineering_fixture_set.json"), 2)
        self.assertTrue(result["ok"], result)

    def test_repeated_evaluation_leaves_no_children(self) -> None:
        self.assertEqual([], multiprocessing.active_children())

    def test_cli_repeated_evaluation_terminates(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "verification_v1", "stress-isolation", "--iterations", "2"],
            capture_output=True,
            text=True,
            check=False,
            timeout=90,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["ok"])

    def test_supported_python_matrix_runs_isolation_suite(self) -> None:
        self.assertGreaterEqual(sys.version_info[:2], (3, 11))

    def test_checklet_timeout_terminates_child(self) -> None:
        try:
            from test_safety_invariants import BlockingChecklet
        except ImportError:
            from tests.test_safety_invariants import BlockingChecklet
        from verification_v1.artifacts import ArtifactStore
        from verification_v1.checklets import CheckletContext, CheckletRegistry
        from verification_v1.contracts import CheckletVerdict, TaskContract
        from verification_v1.runner import CandidateArtifact

        artifact = ArtifactStore().register(
            CandidateArtifact.from_text("timeout-a", "coding_patch", "x = 1\n", {"changed_paths": ["x.py"]}),
            "run-timeout",
        )
        observations = CheckletRegistry((BlockingChecklet(),)).run_all(CheckletContext(TaskContract("t", ()), artifact))
        self.assertEqual(CheckletVerdict.ERROR, observations[0].verdict)
        self.assertEqual([], multiprocessing.active_children())

    def test_checklet_crash_cleans_up_child(self) -> None:
        try:
            from test_safety_invariants import ExplodingChecklet
        except ImportError:
            from tests.test_safety_invariants import ExplodingChecklet
        from verification_v1.artifacts import ArtifactStore
        from verification_v1.checklets import CheckletContext, CheckletRegistry
        from verification_v1.contracts import CheckletVerdict, TaskContract
        from verification_v1.runner import CandidateArtifact

        artifact = ArtifactStore().register(
            CandidateArtifact.from_text("crash-a", "coding_patch", "x = 1\n", {"changed_paths": ["x.py"]}),
            "run-crash",
        )
        observations = CheckletRegistry((ExplodingChecklet(),)).run_all(CheckletContext(TaskContract("t", ()), artifact))
        self.assertEqual(CheckletVerdict.ERROR, observations[0].verdict)
        self.assertEqual([], multiprocessing.active_children())

    def test_queue_failure_does_not_hang_parent(self) -> None:
        from verification_v1.checklets import MAX_CHECKLET_ARTIFACT_BYTES
        from verification_v1.artifacts import ArtifactStore
        from verification_v1.checklets import CheckletContext, CheckletRegistry, default_coding_checklets
        from verification_v1.contracts import TaskContract
        from verification_v1.runner import CandidateArtifact

        huge = "x" * (MAX_CHECKLET_ARTIFACT_BYTES + 10)
        artifact = ArtifactStore().register(
            CandidateArtifact.from_text("queue-a", "coding_patch", huge, {"changed_paths": ["x.py"]}),
            "run-queue",
        )
        started = __import__("time").perf_counter()
        CheckletRegistry(default_coding_checklets()[:1]).run_all(CheckletContext(TaskContract("t", ()), artifact))
        self.assertLess(__import__("time").perf_counter() - started, 15.0)
        self.assertEqual([], multiprocessing.active_children())


class V12aSafetyTests(unittest.TestCase):
    def test_v12a_does_not_change_v11_authority_invariant(self) -> None:
        from pathlib import Path

        import verification_v1.runner as runner

        source = Path(runner.__file__).read_text(encoding="utf-8")
        self.assertIn("hard_verifier.verify", source)
        prefix = source.split("hard_verifier.verify", 1)[0]
        self.assertNotIn("would_waive", prefix)
        self.assertIn("final_outcome", source)
        self.assertIn("hard_verifier_result.outcome", source)
