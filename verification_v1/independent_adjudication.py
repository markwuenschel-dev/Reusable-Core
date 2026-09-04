"""Evaluation-grade criterion inspection that does not import checklet primitives.

The shared-primitive inspector in ``adjudication.py`` remains a cheap secondary
label. V2 decision-grade criterion truth must come from this AST inspector,
bounded expert review, or another adjudicator that does not share
``requirement_evidence_present``, ``tests_covering_requirement``,
``public_functions``, ``call_argument_counts``, or ``boundary_handled``.
"""

from __future__ import annotations

import ast
import json
from typing import Any, Mapping

from .contracts import TaskContract, utc_now
from .evidence import (
    CHECKLET_IDS,
    CRITERION_IDS,
    AdjudicationMode,
    AdjudicatorType,
    CriterionAdjudication,
    CriterionLabel,
)
from .adjudication import FROZEN_CRITERION_DEFINITIONS

EVALUATION_GRADE_ADJUDICATOR_ID = "independent-ast-inspector"
EXPERT_ADJUDICATOR_ID = "bounded-expert-review"
SECONDARY_ADJUDICATOR_ID = "deterministic-shared"
EVALUATION_GRADE_ADJUDICATOR_IDS = frozenset(
    {EVALUATION_GRADE_ADJUDICATOR_ID, EXPERT_ADJUDICATOR_ID}
)
INDEPENDENT_AST_VERSION = "independent-ast/1.0.0"


def _is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1]
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if name.endswith("_test.py"):
        return True
    parents = normalized.split("/")[:-1]
    return name.endswith(".py") and any(part in {"test", "tests"} for part in parents)


def _bundle_maps(content: bytes) -> tuple[dict[str, str], dict[str, str]]:
    text = content.decode("utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}, {"snippet.py": text}
    if not isinstance(payload, dict) or payload.get("format") != "coding_bundle/1.0.0":
        return {}, {"snippet.py": text}
    base = {
        str(path).replace("\\", "/"): str(body)
        for path, body in dict(payload.get("base_files") or {}).items()
        if body is not None
    }
    patched = dict(base)
    if "patched_files" in payload:
        patched = {
            str(path).replace("\\", "/"): str(body)
            for path, body in dict(payload.get("patched_files") or {}).items()
            if body is not None
        }
    for raw_path, body in dict(payload.get("overlay") or {}).items():
        path = str(raw_path).replace("\\", "/")
        if body is None:
            patched.pop(path, None)
        else:
            patched[path] = str(body)
    return base, patched


def _changed_paths(base: Mapping[str, str], patched: Mapping[str, str]) -> tuple[str, ...]:
    paths = set(base) | set(patched)
    return tuple(path for path in sorted(paths) if base.get(path) != patched.get(path))


def _snake(requirement: str) -> str:
    return requirement.lower().replace("-", "_")


def _tokens(requirement: str) -> tuple[str, ...]:
    return tuple(token for token in requirement.lower().replace("_", "-").split("-") if len(token) > 2)


def _parse(source: str) -> ast.AST | None:
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def _identifiers_and_strings(source: str) -> set[str]:
    tree = _parse(source)
    found: set[str] = set()
    if tree is None:
        return found
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id.lower())
        elif isinstance(node, ast.FunctionDef):
            found.add(node.name.lower())
        elif isinstance(node, ast.ClassDef):
            found.add(node.name.lower())
        elif isinstance(node, ast.Attribute):
            found.add(node.attr.lower())
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            found.add(node.value.lower())
    return found


def _function_names(source: str) -> set[str]:
    tree = _parse(source)
    if tree is None:
        return set()
    return {node.name.lower() for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def _public_required_arity(source: str) -> dict[str, int]:
    tree = _parse(source)
    if tree is None:
        return {}
    arities: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            positional = list(node.args.posonlyargs) + list(node.args.args)
            arities[node.name] = max(0, len(positional) - len(node.args.defaults))
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                    positional = list(item.args.posonlyargs) + list(item.args.args)
                    if positional and positional[0].arg in {"self", "cls"}:
                        positional = positional[1:]
                    arities[f"{node.name}.{item.name}"] = max(0, len(positional) - len(item.args.defaults))
    return arities


def _call_arities(source: str, func_name: str) -> tuple[int, ...]:
    tree = _parse(source)
    if tree is None:
        return ()
    short = func_name.rsplit(".", 1)[-1]
    counts: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        called = node.func
        matched = isinstance(called, ast.Name) and called.id == short
        matched = matched or (isinstance(called, ast.Attribute) and called.attr == short)
        if matched:
            counts.append(len(node.args))
    return tuple(counts)


def _ast_handles_empty(source: str) -> bool:
    tree = _parse(source)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            name = getattr(node.type, "id", None)
            if name in {"IndexError", "TypeError", "ValueError"}:
                return True
        if isinstance(node, ast.If) and _test_looks_empty(node.test):
            return True
    return False


def _ast_handles_none(source: str) -> bool:
    tree = _parse(source)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            comparators = list(node.comparators)
            if any(isinstance(item, ast.Constant) and item.value is None for item in comparators):
                return True
            if isinstance(node.left, ast.Constant) and node.left.value is None:
                return True
        if isinstance(node, ast.ExceptHandler) and getattr(node.type, "id", None) == "TypeError":
            return True
    return False


def _test_looks_empty(test: ast.AST) -> bool:
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return True
    if isinstance(test, ast.Call) and isinstance(test.func, ast.Name) and test.func.id == "len":
        return True
    if isinstance(test, ast.Compare):
        if isinstance(test.left, ast.Call) and isinstance(test.left.func, ast.Name) and test.left.func.id == "len":
            return True
        for item in test.comparators:
            if isinstance(item, ast.Constant) and item.value in {0, "", None}:
                return True
            if isinstance(item, (ast.List, ast.Tuple, ast.Set)) and not item.elts:
                return True
    return False


def _requirement_covered_by_ast(requirement: str, production_sources: Mapping[str, str]) -> bool:
    snake = _snake(requirement)
    tokens = _tokens(requirement)
    names: set[str] = set()
    identifiers: set[str] = set()
    for source in production_sources.values():
        names.update(_function_names(source))
        identifiers.update(_identifiers_and_strings(source))
    if snake in names:
        return True
    if tokens and all(token in identifiers for token in tokens):
        return True
    return False


def _inspect_requirement(task: TaskContract, patched: Mapping[str, str]) -> tuple[CriterionLabel, str]:
    if not task.requirements:
        return CriterionLabel.NOT_APPLICABLE, "no explicit required behaviors in the task contract"
    production = {path: source for path, source in patched.items() if not _is_test_path(path)}
    missing = [item for item in task.requirements if not _requirement_covered_by_ast(item, production)]
    if missing:
        return CriterionLabel.TRUE, "AST identifiers/function names lack required behaviors: " + ", ".join(missing)
    return CriterionLabel.FALSE, "AST identifiers or function names evidence every declared requirement"


def _inspect_tests(task: TaskContract, patched: Mapping[str, str]) -> tuple[CriterionLabel, str]:
    if not task.requirements:
        return CriterionLabel.NOT_APPLICABLE, "no required behaviors for tests to exercise"
    test_names: set[str] = set()
    for path, source in patched.items():
        if _is_test_path(path):
            test_names.update(_function_names(source))
    test_names = {name for name in test_names if name.startswith("test_")}
    if not test_names:
        return CriterionLabel.TRUE, "no candidate-visible test_* functions"
    missing = []
    for requirement in task.requirements:
        snake = _snake(requirement)
        tokens = _tokens(requirement)
        covered = any(snake in name for name in test_names) or any(
            tokens and all(token in name for token in tokens) for name in test_names
        )
        if not covered:
            missing.append(requirement)
    if missing:
        return CriterionLabel.TRUE, "test_* names do not mention declared required behaviors"
    return CriterionLabel.FALSE, "test_* names mention the declared required behaviors"


def _inspect_scope(task: TaskContract, base: Mapping[str, str], patched: Mapping[str, str]) -> tuple[CriterionLabel, str]:
    derived = _changed_paths(base, patched)
    raw = task.metadata.get("allowed_paths")
    if not isinstance(raw, (list, tuple)):
        if derived:
            return CriterionLabel.INDETERMINATE, "changed paths exist but the task contract declares no allowed scope"
        return CriterionLabel.NOT_APPLICABLE, "no derived changes and no declared scope"
    allowed = {str(item).replace("\\", "/") for item in raw}
    unrelated = tuple(path for path in derived if path not in allowed)
    if unrelated:
        return CriterionLabel.TRUE, "derived diff leaves justified task scope: " + ", ".join(unrelated)
    return CriterionLabel.FALSE, "derived diff stays within the declared task scope"


def _inspect_dependency(base: Mapping[str, str], patched: Mapping[str, str]) -> tuple[CriterionLabel, str]:
    changed = set(_changed_paths(base, patched))
    risky: list[str] = []
    inspected = False
    for path in sorted(set(base) | set(patched)):
        if _is_test_path(path) or not path.endswith(".py"):
            continue
        before = base.get(path, "")
        after = patched.get(path)
        if after is None or before == after:
            continue
        old = _public_required_arity(before) if before else {}
        new = _public_required_arity(after)
        for symbol, old_arity in old.items():
            new_arity = new.get(symbol)
            if new_arity == old_arity:
                continue
            inspected = True
            for other_path, source in patched.items():
                if other_path == path or _is_test_path(other_path) or not other_path.endswith(".py"):
                    continue
                counts = _call_arities(source, symbol)
                if not counts:
                    continue
                if other_path not in changed:
                    risky.append(f"{symbol}@{other_path}")
                elif new_arity is not None and any(count < new_arity for count in counts):
                    risky.append(f"{symbol}@{other_path}")
    if risky:
        return CriterionLabel.TRUE, "changed public arities have unaccounted call sites: " + ", ".join(sorted(set(risky)))
    if not inspected:
        return CriterionLabel.NOT_APPLICABLE, "no public arity changes were present"
    return CriterionLabel.FALSE, "changed public arities account for affected call sites"


def _inspect_boundary(task: TaskContract, patched: Mapping[str, str]) -> tuple[CriterionLabel, str]:
    raw = task.metadata.get("boundary_cases")
    if not isinstance(raw, (list, tuple)) or not raw:
        return CriterionLabel.NOT_APPLICABLE, "no task-relevant failure/boundary cases were declared"
    production = "\n".join(source for path, source in patched.items() if not _is_test_path(path))
    missing: list[str] = []
    for case in raw:
        key = str(case).strip().lower().replace("_", "-")
        if key in {"empty-input", "empty", "empty-list"}:
            if not _ast_handles_empty(production):
                missing.append(str(case))
        elif key in {"none-input", "none", "null-input"}:
            if not _ast_handles_none(production):
                missing.append(str(case))
        else:
            missing.append(str(case))
    if missing:
        return CriterionLabel.TRUE, "AST control-flow lacks handling for declared boundary cases: " + ", ".join(missing)
    return CriterionLabel.FALSE, "AST control-flow evidence handles declared boundary cases"


def independent_adjudicate_artifact_bytes(
    task: TaskContract,
    content: bytes,
    artifact_digest: str,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[CriterionAdjudication, ...]:
    del metadata
    base, patched = _bundle_maps(content)
    created = utc_now()
    inspectors = {
        "requirement_coverage": lambda: _inspect_requirement(task, patched),
        "test_adequacy": lambda: _inspect_tests(task, patched),
        "change_scope": lambda: _inspect_scope(task, base, patched),
        "dependency_integration_risk": lambda: _inspect_dependency(base, patched),
        "error_boundary": lambda: _inspect_boundary(task, patched),
    }
    results: list[CriterionAdjudication] = []
    for checklet_id in CHECKLET_IDS:
        label, reason = inspectors[checklet_id]()
        results.append(
            CriterionAdjudication(
                task_id=task.task_id,
                artifact_digest=artifact_digest,
                checklet_id=checklet_id,
                criterion_id=CRITERION_IDS[checklet_id],
                label=label,
                adjudicator_type=AdjudicatorType.INDEPENDENT_STATIC_ANALYSIS,
                adjudicator_id=EVALUATION_GRADE_ADJUDICATOR_ID,
                adjudication_version=INDEPENDENT_AST_VERSION,
                evidence_refs=(f"independent-ast:{checklet_id}",),
                reason=reason,
                created_at=created,
                adjudication_mode=AdjudicationMode.BLIND,
            )
        )
    return tuple(results)


def expert_adjudication_form(
    task: TaskContract,
    artifact_digest: str,
) -> dict[str, Any]:
    """Blind review packet. Checklet verdicts are intentionally omitted."""
    return {
        "adjudicator_type": AdjudicatorType.BOUNDED_EXPERT_REVIEW.value,
        "adjudicator_id": EXPERT_ADJUDICATOR_ID,
        "adjudication_mode": AdjudicationMode.BLIND.value,
        "checklet_verdicts_included": False,
        "instruction": (
            "Is criterion X actually satisfied or violated in this exact artifact? "
            "Do not judge whether a checklet was correct."
        ),
        "task_id": task.task_id,
        "artifact_digest": artifact_digest,
        "task_contract": task.to_dict(),
        "criteria": [
            {
                "checklet_id": checklet_id,
                "criterion_id": CRITERION_IDS[checklet_id],
                "definition": FROZEN_CRITERION_DEFINITIONS[checklet_id],
                "label_options": [item.value for item in CriterionLabel],
            }
            for checklet_id in CHECKLET_IDS
        ],
    }
