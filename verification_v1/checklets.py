"""Narrow, deterministic, diagnostic-only coding checklets."""

from __future__ import annotations

from dataclasses import dataclass, replace
from importlib import import_module
from multiprocessing import get_context
from queue import Empty
from time import perf_counter
from typing import Any, Mapping, Protocol
from types import MappingProxyType

from .artifacts import RegisteredArtifact
from .bundle import (
    boundary_handled,
    call_argument_counts,
    is_test_path,
    parse_coding_bundle,
    public_functions,
    requirement_evidence_present,
    tests_covering_requirement,
)
from .contracts import (
    CheckletObservation,
    CheckletSpec,
    CheckletVerdict,
    Severity,
    TaskContract,
    mutable_copy,
    new_id,
    parse_checklet_observation,
    jsonable,
    utc_now,
)


@dataclass(frozen=True)
class CheckletContext:
    task: TaskContract
    artifact: RegisteredArtifact

    @property
    def metadata(self) -> Mapping[str, Any]:
        # Checklets receive a disposable copy. They can never alter the registered
        # bytes or metadata that bind the hard-verifier result to this artifact.
        return mutable_copy(self.artifact.ref.metadata)


class Checklet(Protocol):
    spec: CheckletSpec

    def evaluate(self, context: CheckletContext) -> CheckletObservation | Mapping[str, Any]: ...


MAX_CHECKLET_ARTIFACT_BYTES = 512_000
_MAX_TRANSPORT_ITEMS = 4_096
_MAX_TRANSPORT_TEXT_CHARS = 65_536
_MAX_TRANSPORT_BYTES = 1_000_000


class _TransportLimitError(ValueError):
    pass


def _charge_transport_budget(budget: list[int], byte_count: int) -> None:
    budget[0] += 1
    budget[1] += byte_count
    if budget[0] > _MAX_TRANSPORT_ITEMS:
        raise _TransportLimitError("checklet transport item count exceeds the limit")
    if budget[1] > _MAX_TRANSPORT_BYTES:
        raise _TransportLimitError("checklet transport byte count exceeds the limit")


def _transport_value(
    value: Any,
    *,
    budget: list[int] | None = None,
    depth: int = 0,
    allow_mapping_proxy: bool = False,
) -> Any:
    """Copy only bounded, inert values before spawning a checklet process."""
    if depth > 16:
        raise _TransportLimitError("checklet transport nesting exceeds the limit")
    budget = budget if budget is not None else [0, 0]
    if value is None:
        _charge_transport_budget(budget, 16)
        return value
    if type(value) is bool:
        _charge_transport_budget(budget, 1)
        return value
    if type(value) is int:
        _charge_transport_budget(budget, max(1, (value.bit_length() + 7) // 8))
        return value
    if type(value) is float:
        _charge_transport_budget(budget, 8)
        return value
    if type(value) is str:
        if len(value) > _MAX_TRANSPORT_TEXT_CHARS:
            raise _TransportLimitError("checklet transport text exceeds the limit")
        _charge_transport_budget(budget, len(value))
        return value
    if type(value) is bytes:
        if len(value) > MAX_CHECKLET_ARTIFACT_BYTES:
            raise _TransportLimitError("checklet transport bytes exceed the limit")
        _charge_transport_budget(budget, len(value))
        return {"kind": "bytes", "value": value}
    if type(value) in {CheckletVerdict, Severity}:
        _charge_transport_budget(budget, len(type(value).__module__) + len(type(value).__qualname__))
        return {
            "kind": "enum",
            "module": type(value).__module__,
            "qualname": type(value).__qualname__,
            "value": _transport_value(value.value, budget=budget, depth=depth + 1, allow_mapping_proxy=allow_mapping_proxy),
        }
    if type(value) is CheckletSpec:
        _charge_transport_budget(budget, 16)
        return {
            "kind": "checklet_spec",
            "value": _transport_value(value.to_dict(), budget=budget, depth=depth + 1, allow_mapping_proxy=allow_mapping_proxy),
        }
    if type(value) is dict or (allow_mapping_proxy and type(value) is MappingProxyType):
        _charge_transport_budget(budget, 16)
        items: list[tuple[str, Any]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise _TransportLimitError("checklet transport mapping keys must be strings")
            if len(key) > _MAX_TRANSPORT_TEXT_CHARS:
                raise _TransportLimitError("checklet transport mapping key exceeds the limit")
            _charge_transport_budget(budget, len(key))
            items.append((key, _transport_value(item, budget=budget, depth=depth + 1, allow_mapping_proxy=allow_mapping_proxy)))
        return {"kind": "mapping", "items": items}
    if type(value) is tuple:
        _charge_transport_budget(budget, 16)
        return {"kind": "tuple", "items": [_transport_value(item, budget=budget, depth=depth + 1, allow_mapping_proxy=allow_mapping_proxy) for item in value]}
    if type(value) is list:
        _charge_transport_budget(budget, 16)
        return {"kind": "list", "items": [_transport_value(item, budget=budget, depth=depth + 1, allow_mapping_proxy=allow_mapping_proxy) for item in value]}
    if type(value) in {set, frozenset}:
        _charge_transport_budget(budget, 16)
        return {"kind": "frozenset", "items": [_transport_value(item, budget=budget, depth=depth + 1, allow_mapping_proxy=allow_mapping_proxy) for item in value]}
    raise _TransportLimitError(f"unsupported checklet transport value: {type(value).__name__}")


def _resolve_qualified(module_name: str, qualname: str) -> type[Any]:
    if "<locals>" in qualname:
        raise ValueError("locally defined checklets cannot run in isolated processes")
    value: Any = import_module(module_name)
    for part in qualname.split("."):
        value = getattr(value, part)
    if not isinstance(value, type):
        raise TypeError("transport value does not resolve to a type")
    return value


def _restore_transport(value: Any) -> Any:
    if not isinstance(value, Mapping) or "kind" not in value:
        return value
    kind = value["kind"]
    if kind == "bytes":
        return value["value"]
    if kind == "mapping":
        return {key: _restore_transport(item) for key, item in value["items"]}
    if kind == "tuple":
        return tuple(_restore_transport(item) for item in value["items"])
    if kind == "list":
        return [_restore_transport(item) for item in value["items"]]
    if kind == "frozenset":
        return frozenset(_restore_transport(item) for item in value["items"])
    if kind == "enum":
        return _resolve_qualified(str(value["module"]), str(value["qualname"]))(_restore_transport(value["value"]))
    if kind == "checklet_spec":
        return CheckletSpec(**_restore_transport(value["value"]))
    raise ValueError("unsupported checklet transport kind")


def _checklet_descriptor(checklet: Checklet) -> Any:
    checklet_type = type(checklet)
    state = object.__getattribute__(checklet, "__dict__")
    if not isinstance(state, dict):
        raise _TransportLimitError("isolated checklets must have a plain instance state dictionary")
    return _transport_value(
        {
            "module": checklet_type.__module__,
            "qualname": checklet_type.__qualname__,
            "state": state,
        }
    )


def _evaluate_in_isolated_process(
    result_queue: Any,
    descriptor: Any,
    task_payload: Any,
    artifact_payload: Any,
) -> None:
    """Evaluate untrusted checklet code in a process that can be terminated at its deadline."""
    try:
        import sys
        from os import getcwd

        from .contracts import ArtifactRef

        cwd = getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
        descriptor = _restore_transport(descriptor)
        checklet_type = _resolve_qualified(str(descriptor["module"]), str(descriptor["qualname"]))
        checklet = checklet_type.__new__(checklet_type)
        object.__getattribute__(checklet, "__dict__").update(descriptor["state"])
        task_payload = _restore_transport(task_payload)
        artifact_payload = _restore_transport(artifact_payload)
        task = TaskContract(
            task_id=str(task_payload["task_id"]),
            requirements=tuple(str(item) for item in task_payload.get("requirements", [])),
            description=str(task_payload.get("description", "")),
            version=str(task_payload.get("version", "1.0.0")),
            metadata=dict(task_payload.get("metadata", {})),
        )
        reference = ArtifactRef(
            artifact_id=str(artifact_payload["artifact_id"]),
            artifact_digest=str(artifact_payload["artifact_digest"]),
            artifact_type=str(artifact_payload["artifact_type"]),
            artifact_version=str(artifact_payload["artifact_version"]),
            run_id=str(artifact_payload["run_id"]),
            created_at=str(artifact_payload["created_at"]),
            metadata=dict(artifact_payload.get("metadata", {})),
        )
        context = CheckletContext(task=task, artifact=RegisteredArtifact(reference, artifact_payload["content"]))
        raw = checklet.evaluate(context)
        if isinstance(raw, CheckletObservation):
            result_queue.put(("structured", raw.to_dict()))
        elif isinstance(raw, Mapping):
            result_queue.put(("structured", jsonable(raw)))
        else:
            result_queue.put(("unsupported", type(raw).__name__))
    except Exception as exc:
        result_queue.put(("error", type(exc).__name__))


class BaseCodingChecklet:
    def __init__(self, checklet_id: str, criterion_id: str, description: str) -> None:
        self.spec = CheckletSpec(
            checklet_id=checklet_id,
            version="1.1.0",
            domain_pack="coding-v1",
            criterion_id=criterion_id,
            description=description,
            required_artifact_types=("coding_patch",),
            required_context=(),
            implementation_type="deterministic",
            authority_ceiling="diagnostic",
            estimated_cost_class="negligible",
            timeout_seconds=10.0,
            required_or_optional="required",
            evidence_family_template=f"deterministic:vs-v1:{checklet_id}",
        )

    def observation(
        self,
        context: CheckletContext,
        verdict: CheckletVerdict,
        severity: Severity = Severity.INFO,
        finding_type: str | None = None,
        locus: str | None = None,
        summary: str = "No defect found for this criterion.",
        trigger_refs: tuple[str, ...] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> CheckletObservation:
        now = utc_now()
        return CheckletObservation(
            observation_id=new_id("observation"),
            checklet_id=self.spec.checklet_id,
            checklet_version=self.spec.version,
            criterion_id=self.spec.criterion_id,
            artifact_digest=context.artifact.artifact_digest,
            verdict=verdict,
            severity=severity,
            finding_type=finding_type,
            locus=locus,
            summary=summary,
            confidence=1.0 if verdict != CheckletVerdict.ABSTAIN else None,
            confidence_semantics="heuristic confidence",
            evidence_refs=(),
            trigger_refs=trigger_refs,
            model_provider=None,
            resolved_model_id=None,
            prompt_template_hash=None,
            evidence_family_id=self.spec.evidence_family_template,
            started_at=now,
            completed_at=now,
            latency_ms=0.0,
            estimated_or_actual_cost={"kind": "actual_cost", "amount": 0.0, "currency": "USD"},
            metadata=metadata or {},
        )


def _inspect_bundle(context: CheckletContext):
    return parse_coding_bundle(context.artifact.content, context.metadata)


def _sequence_claim(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return ()


def _allowed_paths(context: CheckletContext) -> set[str] | None:
    for source in (context.task.metadata, context.metadata):
        raw = source.get("allowed_paths")
        if isinstance(raw, (list, tuple)):
            return {str(item).replace("\\", "/") for item in raw}
    return None


def _expected_boundary_cases(context: CheckletContext) -> tuple[str, ...]:
    for source in (context.task.metadata, context.metadata):
        raw = source.get("boundary_cases")
        if isinstance(raw, (list, tuple)):
            return tuple(str(item) for item in raw)
    return ()


def _test_files(bundle) -> dict[str, str]:
    files: dict[str, str] = {}
    for path, content in bundle.patched_files.items():
        if is_test_path(path):
            files[path] = content
    return files


def _production_text(bundle) -> str:
    return "\n".join(
        content
        for path, content in bundle.patched_files.items()
        if not is_test_path(path)
    )


def _stale_call_site_files(symbol: str, bundle, defining_path: str, changed: set[str]) -> tuple[str, ...]:
    stale: list[str] = []
    for path, content in bundle.patched_files.items():
        if path == defining_path or is_test_path(path) or not path.endswith(".py"):
            continue
        try:
            counts = call_argument_counts(content, symbol)
        except SyntaxError:
            continue
        if counts and path not in changed:
            stale.append(path)
    return tuple(stale)


class RequirementCoverageChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("requirement_coverage", "requirements-covered", "Checks declared task requirements against the actual patched production files.")

    def evaluate(self, context: CheckletContext) -> CheckletObservation:
        if not context.task.requirements:
            return self.observation(context, CheckletVerdict.CLEAN)
        bundle = _inspect_bundle(context)
        production = "\n".join(
            bundle.patched_files[path]
            for path in bundle.changed_paths()
            if path in bundle.patched_files and not is_test_path(path)
        )
        patterns = context.task.metadata.get("requirement_evidence_patterns", {})
        missing = []
        for requirement in context.task.requirements:
            extra = patterns.get(requirement) if isinstance(patterns, Mapping) else None
            extra_patterns = extra if isinstance(extra, (list, tuple)) else None
            if not requirement_evidence_present(requirement, production, extra_patterns):
                missing.append(requirement)
        evidence = {
            "derived_changed_paths": list(bundle.changed_paths()),
            "producer_claimed_covered_requirements": list(_sequence_claim(context.metadata.get("covered_requirements"))),
        }
        if missing:
            return self.observation(
                context, CheckletVerdict.FINDING, Severity.MEDIUM, "requirement_omitted", "task.requirements",
                f"Declared requirements lack coverage in the patched production files: {', '.join(missing)}.",
                tuple(missing),
                metadata=evidence,
            )
        return self.observation(context, CheckletVerdict.CLEAN, metadata=evidence)


class TestAdequacyChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("test_adequacy", "producer-test-adequacy", "Checks whether tests present in the patched repository cover declared requirements.")

    def evaluate(self, context: CheckletContext) -> CheckletObservation:
        if not context.task.requirements:
            return self.observation(context, CheckletVerdict.CLEAN)
        bundle = _inspect_bundle(context)
        test_files = _test_files(bundle)
        missing = [
            requirement
            for requirement in context.task.requirements
            if not tests_covering_requirement(requirement, test_files)
        ]
        evidence = {
            "derived_test_paths": sorted(test_files),
            "producer_claimed_test_cases": list(_sequence_claim(context.metadata.get("producer_test_cases"))),
        }
        if not test_files or missing:
            return self.observation(
                context, CheckletVerdict.FINDING, Severity.MEDIUM, "test_inadequate", "tests",
                "Patched repository tests do not cover every declared requirement.",
                tuple(missing or context.task.requirements),
                metadata=evidence,
            )
        return self.observation(context, CheckletVerdict.CLEAN, metadata=evidence)


class ChangeScopeChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("change_scope", "declared-change-scope", "Checks derived diff paths against the task-contract scope.")

    def evaluate(self, context: CheckletContext) -> CheckletObservation:
        bundle = _inspect_bundle(context)
        derived = bundle.changed_paths()
        allowed = _allowed_paths(context)
        evidence = {
            "derived_changed_paths": list(derived),
            "producer_claimed_changed_paths": list(_sequence_claim(context.metadata.get("changed_paths"))),
        }
        if allowed is None:
            if derived:
                return self.observation(
                    context, CheckletVerdict.ABSTAIN, Severity.MEDIUM, "scope_unspecified", None,
                    "Changed paths were derived but the task contract does not declare an allowed scope.",
                    derived,
                    metadata=evidence,
                )
            return self.observation(context, CheckletVerdict.CLEAN, metadata=evidence)
        unrelated = tuple(path for path in derived if path not in allowed)
        if unrelated:
            return self.observation(
                context, CheckletVerdict.FINDING, Severity.MEDIUM, "unrelated_change", ", ".join(unrelated),
                "Changed paths fall outside the declared task scope.", unrelated,
                metadata=evidence,
            )
        return self.observation(context, CheckletVerdict.CLEAN, metadata=evidence)


class DependencyRiskChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("dependency_integration_risk", "interface-dependency-risk", "Checks changed public interfaces against real call sites in the patched repository.")

    def evaluate(self, context: CheckletContext) -> CheckletObservation:
        bundle = _inspect_bundle(context)
        changed = set(bundle.changed_paths())
        risky: list[str] = []
        stale_files: list[str] = []
        inspected_paths = sorted(set(bundle.base_files) | set(bundle.patched_files))
        for path in inspected_paths:
            if is_test_path(path) or not path.endswith(".py"):
                continue
            before = bundle.base_files.get(path, "")
            after = bundle.patched_files.get(path)
            if after is None or before == after:
                if after is None and before:
                    try:
                        for symbol in public_functions(before):
                            stale = _stale_call_site_files(symbol, bundle, path, changed)
                            if stale:
                                risky.append(symbol)
                                stale_files.extend(stale)
                    except SyntaxError:
                        continue
                continue
            try:
                old_sigs = public_functions(before) if before else {}
                new_sigs = public_functions(after)
            except SyntaxError:
                continue
            for symbol, old in old_sigs.items():
                new = new_sigs.get(symbol)
                if new is None or new.required != old.required:
                    stale = _stale_call_site_files(symbol, bundle, path, changed)
                    if stale:
                        risky.append(symbol)
                        stale_files.extend(stale)
                        continue
                    if new is not None and not new.has_varargs:
                        for other_path, content in bundle.patched_files.items():
                            if other_path == path or is_test_path(other_path) or not other_path.endswith(".py"):
                                continue
                            try:
                                counts = call_argument_counts(content, symbol)
                            except SyntaxError:
                                continue
                            if any(count < new.required or count > new.max_positional for count in counts):
                                risky.append(symbol)
                                stale_files.append(other_path)
        evidence = {
            "derived_changed_paths": sorted(changed),
            "producer_claimed_signature_changes": list(context.metadata.get("signature_changes", []) or []),
        }
        if risky:
            loci = tuple(dict.fromkeys(risky))
            return self.observation(
                context, CheckletVerdict.FINDING, Severity.HIGH, "integration_risk", ", ".join(loci),
                "A changed public interface has un-updated or incompatible call sites.",
                tuple(dict.fromkeys(stale_files)) or loci,
                metadata=evidence,
            )
        return self.observation(context, CheckletVerdict.CLEAN, metadata=evidence)


class ErrorBoundaryChecklet(BaseCodingChecklet):
    def __init__(self) -> None:
        super().__init__("error_boundary", "failure-boundaries", "Checks declared boundary cases against handling evidence in patched production files.")

    def evaluate(self, context: CheckletContext) -> CheckletObservation:
        expected = _expected_boundary_cases(context)
        if not expected:
            return self.observation(context, CheckletVerdict.CLEAN)
        bundle = _inspect_bundle(context)
        production = _production_text(bundle)
        missing = tuple(case for case in expected if not boundary_handled(case, production))
        evidence = {
            "derived_changed_paths": list(bundle.changed_paths()),
            "producer_claimed_handled_boundary_cases": list(_sequence_claim(context.metadata.get("handled_boundary_cases"))),
        }
        if missing:
            return self.observation(
                context, CheckletVerdict.FINDING, Severity.MEDIUM, "boundary_not_handled", ", ".join(missing),
                "Declared boundary cases lack handling evidence in the patched production files.",
                missing,
                metadata=evidence,
            )
        return self.observation(context, CheckletVerdict.CLEAN, metadata=evidence)


def error_observation(
    spec: CheckletSpec,
    context: CheckletContext,
    reason: str,
    started_at: str | None = None,
    latency_ms: float = 0.0,
) -> CheckletObservation:
    return CheckletObservation(
        observation_id=new_id("observation"),
        checklet_id=spec.checklet_id,
        checklet_version=spec.version,
        criterion_id=spec.criterion_id,
        artifact_digest=context.artifact.artifact_digest,
        verdict=CheckletVerdict.ERROR,
        severity=Severity.HIGH,
        finding_type="checklet_execution_error",
        locus=None,
        summary=reason,
        confidence=None,
        confidence_semantics="not available after checklet error",
        evidence_refs=(),
        trigger_refs=(),
        model_provider=None,
        resolved_model_id=None,
        prompt_template_hash=None,
        evidence_family_id=spec.evidence_family_template,
        started_at=started_at or utc_now(),
        completed_at=utc_now(),
        latency_ms=latency_ms,
        estimated_or_actual_cost={"kind": "unknown_cost"},
        metadata={},
    )


class CheckletRegistry:
    def __init__(self, checklets: tuple[Checklet, ...]) -> None:
        self._checklets = checklets

    @property
    def specs(self) -> tuple[CheckletSpec, ...]:
        return tuple(checklet.spec for checklet in self._checklets)

    def run_all(self, context: CheckletContext) -> tuple[CheckletObservation, ...]:
        observations: list[CheckletObservation] = []
        for checklet in self._checklets:
            started_at = utc_now()
            timer = perf_counter()
            if context.artifact.ref.artifact_type not in checklet.spec.required_artifact_types:
                continue
            if any(key not in context.metadata for key in checklet.spec.required_context):
                observations.append(
                    error_observation(
                        checklet.spec,
                        context,
                        "required checklet context unavailable",
                        started_at,
                        (perf_counter() - timer) * 1000,
                    )
                )
                continue
            process = None
            result_queue = None
            try:
                if len(context.artifact.content) > MAX_CHECKLET_ARTIFACT_BYTES:
                    raise _TransportLimitError("artifact content exceeds the isolated-checklet byte limit")
                descriptor = _checklet_descriptor(checklet)
                task_payload = _transport_value(
                    {
                        "task_id": context.task.task_id,
                        "requirements": context.task.requirements,
                        "description": context.task.description,
                        "version": context.task.version,
                        "metadata": context.task.metadata,
                    },
                    allow_mapping_proxy=True,
                )
                artifact_payload = _transport_value(
                    {
                        "artifact_id": context.artifact.ref.artifact_id,
                        "artifact_digest": context.artifact.ref.artifact_digest,
                        "artifact_type": context.artifact.ref.artifact_type,
                        "artifact_version": context.artifact.ref.artifact_version,
                        "run_id": context.artifact.ref.run_id,
                        "created_at": context.artifact.ref.created_at,
                        "metadata": context.artifact.ref.metadata,
                        "content": context.artifact.content,
                    },
                    allow_mapping_proxy=True,
                )
                remaining = checklet.spec.timeout_seconds - (perf_counter() - timer)
                if remaining <= 0:
                    raise TimeoutError("checklet preparation exceeded its deadline")
                process_context = get_context("spawn")
                result_queue = process_context.Queue(maxsize=1)
                process = process_context.Process(
                    target=_evaluate_in_isolated_process,
                    args=(result_queue, descriptor, task_payload, artifact_payload),
                )
                process.start()
                remaining = checklet.spec.timeout_seconds - (perf_counter() - timer)
                process.join(max(0.0, remaining))
                if process.is_alive():
                    process.terminate()
                    process.join()
                    observations.append(
                        error_observation(
                            checklet.spec,
                            context,
                            f"checklet timeout after {checklet.spec.timeout_seconds:.3f} seconds",
                            started_at,
                            (perf_counter() - timer) * 1000,
                        )
                    )
                    continue
                try:
                    result_kind, raw = result_queue.get(timeout=max(0.0, checklet.spec.timeout_seconds - (perf_counter() - timer)))
                except Empty:
                    observations.append(
                        error_observation(
                            checklet.spec,
                            context,
                            "checklet process exited without a structured result",
                            started_at,
                            (perf_counter() - timer) * 1000,
                        )
                    )
                    continue
                if result_kind == "error":
                    observations.append(
                        error_observation(
                            checklet.spec,
                            context,
                            f"checklet exception: {raw}",
                            started_at,
                            (perf_counter() - timer) * 1000,
                        )
                    )
                    continue
                if result_kind != "structured" or not isinstance(raw, Mapping):
                    observations.append(
                        error_observation(
                            checklet.spec,
                            context,
                            "malformed structured checklet output",
                            started_at,
                            (perf_counter() - timer) * 1000,
                        )
                    )
                    continue
                observation = parse_checklet_observation(raw, checklet.spec, context.artifact.artifact_digest)
                observations.append(
                    replace(
                        observation,
                        started_at=started_at,
                        completed_at=utc_now(),
                        latency_ms=(perf_counter() - timer) * 1000,
                    )
                )
            except TimeoutError:
                observations.append(
                    error_observation(
                        checklet.spec,
                        context,
                        f"checklet timeout after {checklet.spec.timeout_seconds:.3f} seconds",
                        started_at,
                        (perf_counter() - timer) * 1000,
                    )
                )
            except _TransportLimitError as exc:
                observations.append(
                    error_observation(
                        checklet.spec,
                        context,
                        f"checklet transport unavailable: {exc}",
                        started_at,
                        (perf_counter() - timer) * 1000,
                    )
                )
            except Exception as exc:
                observations.append(
                    error_observation(
                        checklet.spec,
                        context,
                        f"checklet exception: {type(exc).__name__}",
                        started_at,
                        (perf_counter() - timer) * 1000,
                    )
                )
            finally:
                if process is not None:
                    try:
                        if process.is_alive():
                            process.terminate()
                            process.join(1.0)
                        if process.is_alive():
                            process.kill()
                            process.join(1.0)
                    except Exception:
                        pass
                    try:
                        process.close()
                    except Exception:
                        pass
                if result_queue is not None:
                    try:
                        while True:
                            result_queue.get_nowait()
                    except Exception:
                        pass
                    try:
                        result_queue.close()
                    except Exception:
                        pass
                    try:
                        result_queue.join_thread()
                    except Exception:
                        pass
        return tuple(observations)


def default_coding_checklets() -> tuple[Checklet, ...]:
    return (
        RequirementCoverageChecklet(),
        TestAdequacyChecklet(),
        ChangeScopeChecklet(),
        DependencyRiskChecklet(),
        ErrorBoundaryChecklet(),
    )
