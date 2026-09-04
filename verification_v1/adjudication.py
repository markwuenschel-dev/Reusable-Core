"""Independent criterion adjudication. Never asks whether a checklet was correct."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .bundle import (
    CodingBundle,
    boundary_handled,
    call_argument_counts,
    is_test_path,
    parse_coding_bundle,
    public_functions,
    requirement_evidence_present,
    tests_covering_requirement,
)
from .contracts import TaskContract, utc_now
from .evidence import (
    CHECKLET_IDS,
    CRITERION_IDS,
    AdjudicationMode,
    AdjudicatorType,
    CriterionAdjudication,
    CriterionLabel,
)

CRITERION_REGISTRY_VERSION = "criterion-registry/1.0.0"
ADJUDICATION_VERSION = "deterministic-shared/1.0.0"
SHARED_ADJUDICATOR_ID = "deterministic-shared"

FROZEN_CRITERION_DEFINITIONS: dict[str, str] = {
    "requirement_coverage": (
        "Does the candidate artifact materially implement every explicit required "
        "behavior within the adjudicable task contract?"
    ),
    "test_adequacy": (
        "Do the candidate-visible tests meaningfully exercise the changed required behavior?"
    ),
    "change_scope": (
        "Does the actual candidate diff stay within a justified task-related scope?"
    ),
    "dependency_integration_risk": (
        "Does the candidate account for materially affected callsites/interfaces caused "
        "by changed public dependencies/signatures?"
    ),
    "error_boundary": (
        "Does the candidate contain evidence of handling task-relevant failure/boundary cases?"
    ),
}


@dataclass(frozen=True)
class CriterionDefinition:
    checklet_id: str
    criterion_id: str
    frozen_definition: str
    live_description: str
    evidence_family_id: str
    version: str

    def to_dict(self) -> dict[str, str]:
        return {
            "checklet_id": self.checklet_id,
            "criterion_id": self.criterion_id,
            "frozen_definition": self.frozen_definition,
            "live_description": self.live_description,
            "evidence_family_id": self.evidence_family_id,
            "version": self.version,
        }


def criterion_registry() -> tuple[CriterionDefinition, ...]:
    from .checklets import default_coding_checklets

    definitions: list[CriterionDefinition] = []
    for checklet in default_coding_checklets():
        checklet_id = checklet.spec.checklet_id
        definitions.append(
            CriterionDefinition(
                checklet_id=checklet_id,
                criterion_id=checklet.spec.criterion_id,
                frozen_definition=FROZEN_CRITERION_DEFINITIONS[checklet_id],
                live_description=checklet.spec.description,
                evidence_family_id=checklet.spec.evidence_family_template,
                version=checklet.spec.version,
            )
        )
    return tuple(definitions)


def _allowed_paths(task: TaskContract) -> set[str] | None:
    raw = task.metadata.get("allowed_paths")
    if isinstance(raw, (list, tuple)):
        return {str(item).replace("\\", "/") for item in raw}
    return None


def _boundary_cases(task: TaskContract) -> tuple[str, ...]:
    raw = task.metadata.get("boundary_cases")
    if isinstance(raw, (list, tuple)):
        return tuple(str(item) for item in raw)
    return ()


def _production_text(bundle: CodingBundle, changed_only: bool = False) -> str:
    paths = bundle.changed_paths() if changed_only else tuple(bundle.patched_files)
    return "\n".join(
        bundle.patched_files[path]
        for path in paths
        if path in bundle.patched_files and not is_test_path(path)
    )


def _test_files(bundle: CodingBundle) -> dict[str, str]:
    return {path: content for path, content in bundle.patched_files.items() if is_test_path(path)}


def _inspect_requirement_coverage(task: TaskContract, bundle: CodingBundle) -> tuple[CriterionLabel, str]:
    if not task.requirements:
        return CriterionLabel.NOT_APPLICABLE, "no explicit required behaviors in the task contract"
    production = _production_text(bundle, changed_only=False)
    missing = [
        requirement
        for requirement in task.requirements
        if not requirement_evidence_present(requirement, production)
    ]
    if missing:
        return CriterionLabel.TRUE, "required behaviors lack evidence in patched production files: " + ", ".join(missing)
    return CriterionLabel.FALSE, "patched production files contain evidence for every declared requirement"


def _inspect_test_adequacy(task: TaskContract, bundle: CodingBundle) -> tuple[CriterionLabel, str]:
    if not task.requirements:
        return CriterionLabel.NOT_APPLICABLE, "no required behaviors for tests to exercise"
    test_files = _test_files(bundle)
    missing = [
        requirement
        for requirement in task.requirements
        if not tests_covering_requirement(requirement, test_files)
    ]
    if not test_files or missing:
        return CriterionLabel.TRUE, "candidate-visible tests do not exercise every declared required behavior"
    return CriterionLabel.FALSE, "candidate-visible tests exercise the declared required behaviors"


def _inspect_change_scope(task: TaskContract, bundle: CodingBundle) -> tuple[CriterionLabel, str]:
    derived = bundle.changed_paths()
    allowed = _allowed_paths(task)
    if allowed is None:
        if derived:
            return CriterionLabel.INDETERMINATE, "changed paths exist but the task contract declares no allowed scope"
        return CriterionLabel.NOT_APPLICABLE, "no derived changes and no declared scope"
    unrelated = tuple(path for path in derived if path not in allowed)
    if unrelated:
        return CriterionLabel.TRUE, "derived diff leaves justified task scope: " + ", ".join(unrelated)
    return CriterionLabel.FALSE, "derived diff stays within the declared task scope"


def _inspect_dependency_risk(task: TaskContract, bundle: CodingBundle) -> tuple[CriterionLabel, str]:
    changed = set(bundle.changed_paths())
    risky: list[str] = []
    inspected = False
    for path in sorted(set(bundle.base_files) | set(bundle.patched_files)):
        if is_test_path(path) or not path.endswith(".py"):
            continue
        before = bundle.base_files.get(path, "")
        after = bundle.patched_files.get(path)
        if after is None or before == after:
            continue
        try:
            old_sigs = public_functions(before) if before else {}
            new_sigs = public_functions(after)
        except SyntaxError:
            continue
        for symbol, old in old_sigs.items():
            new = new_sigs.get(symbol)
            if new is not None and new.required == old.required:
                continue
            inspected = True
            for other_path, content in bundle.patched_files.items():
                if other_path == path or is_test_path(other_path) or not other_path.endswith(".py"):
                    continue
                try:
                    counts = call_argument_counts(content, symbol)
                except SyntaxError:
                    continue
                if counts and other_path not in changed:
                    risky.append(f"{symbol}@{other_path}")
                    continue
                if new is not None and any(
                    count < new.required or count > new.max_positional for count in counts
                ):
                    risky.append(f"{symbol}@{other_path}")
    if risky:
        return CriterionLabel.TRUE, "changed public interfaces have unaccounted call sites: " + ", ".join(sorted(set(risky)))
    if not inspected:
        return CriterionLabel.NOT_APPLICABLE, "no public signature changes were present"
    return CriterionLabel.FALSE, "changed public interfaces account for affected call sites"


def _inspect_error_boundary(task: TaskContract, bundle: CodingBundle) -> tuple[CriterionLabel, str]:
    expected = _boundary_cases(task)
    if not expected:
        return CriterionLabel.NOT_APPLICABLE, "no task-relevant failure/boundary cases were declared"
    production = _production_text(bundle, changed_only=False)
    missing = tuple(case for case in expected if not boundary_handled(case, production))
    if missing:
        return CriterionLabel.TRUE, "declared boundary cases lack handling evidence: " + ", ".join(missing)
    return CriterionLabel.FALSE, "declared boundary cases have handling evidence in patched production files"


_INSPECTORS = {
    "requirement_coverage": _inspect_requirement_coverage,
    "test_adequacy": _inspect_test_adequacy,
    "change_scope": _inspect_change_scope,
    "dependency_integration_risk": _inspect_dependency_risk,
    "error_boundary": _inspect_error_boundary,
}


def adjudicate_bundle(
    task: TaskContract,
    bundle: CodingBundle,
    artifact_digest: str,
    *,
    adjudicator_id: str = SHARED_ADJUDICATOR_ID,
) -> tuple[CriterionAdjudication, ...]:
    """Blind criterion inspection. Does not receive checklet verdicts."""
    created = utc_now()
    results: list[CriterionAdjudication] = []
    for checklet_id in CHECKLET_IDS:
        label, reason = _INSPECTORS[checklet_id](task, bundle)
        results.append(
            CriterionAdjudication(
                task_id=task.task_id,
                artifact_digest=artifact_digest,
                checklet_id=checklet_id,
                criterion_id=CRITERION_IDS[checklet_id],
                label=label,
                adjudicator_type=AdjudicatorType.INDEPENDENT_RULE,
                adjudicator_id=adjudicator_id,
                adjudication_version=ADJUDICATION_VERSION,
                evidence_refs=(f"criterion:{checklet_id}",),
                reason=reason,
                created_at=created,
                adjudication_mode=AdjudicationMode.BLIND,
            )
        )
    return tuple(results)


def adjudicate_artifact_bytes(
    task: TaskContract,
    content: bytes,
    artifact_digest: str,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[CriterionAdjudication, ...]:
    bundle = parse_coding_bundle(content, metadata or {})
    return adjudicate_bundle(task, bundle, artifact_digest)


def resolve_primary_labels(
    adjudications: tuple[CriterionAdjudication, ...],
) -> dict[str, CriterionLabel]:
    grouped: dict[str, list[CriterionLabel]] = {checklet_id: [] for checklet_id in CHECKLET_IDS}
    for item in adjudications:
        grouped[item.checklet_id].append(item.label)
    resolved: dict[str, CriterionLabel] = {}
    for checklet_id, labels in grouped.items():
        unique = set(labels)
        if not labels:
            continue
        if len(unique) == 1:
            resolved[checklet_id] = labels[0]
        else:
            resolved[checklet_id] = CriterionLabel.INDETERMINATE
    return resolved
