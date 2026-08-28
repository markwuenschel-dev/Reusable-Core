"""Content-bound artifact registration for VS-V1."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from .contracts import ArtifactRef, utc_now


def canonical_artifact_bytes(content: bytes) -> bytes:
    """Canonicalize textual line endings without changing meaningful bytes."""
    return content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


@dataclass(frozen=True)
class CandidateArtifact:
    artifact_id: str
    artifact_type: str
    content: bytes
    metadata: Mapping[str, Any]

    @classmethod
    def from_text(
        cls, artifact_id: str, artifact_type: str, content: str, metadata: Mapping[str, Any] | None = None
    ) -> "CandidateArtifact":
        return cls(artifact_id, artifact_type, canonical_artifact_bytes(content.encode("utf-8")), metadata or {})


@dataclass(frozen=True)
class RegisteredArtifact:
    ref: ArtifactRef
    content: bytes

    @property
    def artifact_digest(self) -> str:
        return self.ref.artifact_digest


class ArtifactStore:
    """A small optional filesystem content-addressed store; registered bytes are never overwritten."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root

    def register(self, artifact: CandidateArtifact, run_id: str) -> RegisteredArtifact:
        content = canonical_artifact_bytes(artifact.content)
        digest = sha256(content).hexdigest()
        reference = ArtifactRef(
            artifact_id=artifact.artifact_id,
            artifact_digest=digest,
            artifact_type=artifact.artifact_type,
            artifact_version=f"sha256:{digest[:16]}",
            run_id=run_id,
            created_at=utc_now(),
            metadata=dict(artifact.metadata),
        )
        if self._root is not None:
            self._root.mkdir(parents=True, exist_ok=True)
            artifact_path = self._root / f"{digest}.artifact"
            if not artifact_path.exists():
                artifact_path.write_bytes(content)
        return RegisteredArtifact(reference, content)
