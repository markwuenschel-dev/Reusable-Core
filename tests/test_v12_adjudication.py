import unittest

from verification_v1.adjudication import (
    FROZEN_CRITERION_DEFINITIONS,
    adjudicate_artifact_bytes,
    criterion_registry,
)
from verification_v1.artifacts import canonical_artifact_bytes
from verification_v1.bundle import encode_coding_bundle
from verification_v1.checklets import default_coding_checklets
from verification_v1.contracts import TaskContract
from verification_v1.evidence import CHECKLET_IDS, CriterionLabel

from hashlib import sha256


class AdjudicationTests(unittest.TestCase):
    def test_registry_matches_live_checklets_and_frozen_definitions(self) -> None:
        registry = criterion_registry()
        live = default_coding_checklets()
        self.assertEqual(5, len(registry))
        self.assertEqual(tuple(item.checklet_id for item in registry), tuple(item.spec.checklet_id for item in live))
        for item in registry:
            self.assertEqual(FROZEN_CRITERION_DEFINITIONS[item.checklet_id], item.frozen_definition)
            self.assertEqual(
                item.criterion_id,
                next(checklet.spec.criterion_id for checklet in live if checklet.spec.checklet_id == item.checklet_id),
            )

    def test_adjudication_is_blind_and_covers_all_five_criteria(self) -> None:
        content = encode_coding_bundle(
            {},
            {"stats.py": "def total(items):\n    return items[0]\n"},
        ).encode("utf-8")
        digest = sha256(canonical_artifact_bytes(content)).hexdigest()
        task = TaskContract("zero-for-empty", ("return-zero-for-empty",), metadata={"allowed_paths": ["stats.py"]})
        adjudications = adjudicate_artifact_bytes(task, content, digest)
        self.assertEqual(tuple(item.checklet_id for item in adjudications), CHECKLET_IDS)
        self.assertTrue(all(item.adjudication_mode.value == "blind" for item in adjudications))
        requirement = next(item for item in adjudications if item.checklet_id == "requirement_coverage")
        self.assertEqual(CriterionLabel.TRUE, requirement.label)

    def test_missing_scope_is_indeterminate_not_a_forced_finding(self) -> None:
        content = encode_coding_bundle({}, {"extra.py": "x = 1\n"}).encode("utf-8")
        digest = sha256(canonical_artifact_bytes(content)).hexdigest()
        task = TaskContract("no-scope", ())
        adjudications = adjudicate_artifact_bytes(task, content, digest)
        scope = next(item for item in adjudications if item.checklet_id == "change_scope")
        self.assertEqual(CriterionLabel.INDETERMINATE, scope.label)
        coverage = next(item for item in adjudications if item.checklet_id == "requirement_coverage")
        self.assertEqual(CriterionLabel.NOT_APPLICABLE, coverage.label)

    def test_evaluation_grade_inspector_does_not_share_checklet_primitives(self) -> None:
        import ast
        import inspect

        import verification_v1.independent_adjudication as independent

        tree = ast.parse(inspect.getsource(independent))
        imported_modules = []
        imported_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module)
                imported_names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
        self.assertNotIn("bundle", imported_modules)
        self.assertNotIn("checklets", imported_modules)
        for forbidden in (
            "requirement_evidence_present",
            "tests_covering_requirement",
            "public_functions",
            "call_argument_counts",
            "boundary_handled",
        ):
            self.assertNotIn(forbidden, imported_names)
        content = encode_coding_bundle(
            {},
            {"stats.py": "def total(items):\n    return items[0]\n"},
        ).encode("utf-8")
        digest = sha256(canonical_artifact_bytes(content)).hexdigest()
        task = TaskContract("zero-for-empty", ("return-zero-for-empty",), metadata={"allowed_paths": ["stats.py"]})
        from verification_v1.independent_adjudication import (
            EVALUATION_GRADE_ADJUDICATOR_ID,
            expert_adjudication_form,
            independent_adjudicate_artifact_bytes,
        )

        labels = independent_adjudicate_artifact_bytes(task, content, digest)
        self.assertEqual(5, len(labels))
        self.assertTrue(all(item.adjudicator_id == EVALUATION_GRADE_ADJUDICATOR_ID for item in labels))
        self.assertTrue(all(item.adjudication_mode.value == "blind" for item in labels))
        form = expert_adjudication_form(task, digest)
        self.assertFalse(form["checklet_verdicts_included"])
        self.assertIn("Do not judge whether a checklet was correct", form["instruction"])
