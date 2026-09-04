"""Stable domain-pack registration; Core orchestration has no coding-specific rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .checklets import CheckletRegistry, default_coding_checklets
from .gates import GateRunner, MetadataShapeGate


class DomainPack(Protocol):
    pack_id: str
    version: str
    artifact_types: tuple[str, ...]
    objective_gate_ids: tuple[str, ...]
    checklet_ids: tuple[str, ...]
    hard_verifier_id: str
    required_context: tuple[str, ...]
    known_defect_classes: tuple[str, ...]

    def build_gate_runner(self) -> GateRunner: ...
    def build_checklet_registry(self) -> CheckletRegistry: ...


@dataclass(frozen=True)
class CodingDomainPack:
    pack_id: str = "coding-v1"
    version: str = "1.1.0"
    artifact_types: tuple[str, ...] = ("coding_patch",)
    objective_gate_ids: tuple[str, ...] = ("coding_metadata_shape",)
    checklet_ids: tuple[str, ...] = (
        "requirement_coverage",
        "test_adequacy",
        "change_scope",
        "dependency_integration_risk",
        "error_boundary",
    )
    hard_verifier_id: str = "configured-hard-verifier"
    required_context: tuple[str, ...] = ()
    known_defect_classes: tuple[str, ...] = (
        "requirement_omitted",
        "missing_test",
        "unrelated_change",
        "interface_not_updated",
        "boundary_not_handled",
    )

    @classmethod
    def default(cls) -> "CodingDomainPack":
        return cls()

    def build_gate_runner(self) -> GateRunner:
        return GateRunner((MetadataShapeGate(),))

    def build_checklet_registry(self) -> CheckletRegistry:
        registry = CheckletRegistry(default_coding_checklets())
        if tuple(spec.checklet_id for spec in registry.specs) != self.checklet_ids:
            raise RuntimeError("coding domain manifest and registered checklets diverged")
        return registry


class DomainPackRegistry:
    def __init__(self) -> None:
        self._packs: dict[str, DomainPack] = {}

    def register(self, pack: DomainPack) -> None:
        if pack.pack_id in self._packs:
            raise ValueError(f"domain pack already registered: {pack.pack_id}")
        self._packs[pack.pack_id] = pack

    def resolve(self, pack_id: str) -> DomainPack:
        try:
            return self._packs[pack_id]
        except KeyError as exc:
            raise KeyError(f"unknown domain pack: {pack_id}") from exc

    def list_packs(self) -> tuple[DomainPack, ...]:
        return tuple(self._packs[key] for key in sorted(self._packs))
