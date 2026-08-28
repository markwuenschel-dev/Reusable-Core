"""Append-only JSONL and in-memory event sinks with a common identity envelope."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from .artifacts import RegisteredArtifact
from .contracts import TaskContract, new_id, utc_now


EVENT_SCHEMA_VERSION = "verification-v1-events/1.0.0"


class EventSink(Protocol):
    def emit(
        self,
        event_type: str,
        task: TaskContract,
        artifact: RegisteredArtifact,
        component_id: str,
        component_version: str,
        **payload: Any,
    ) -> None: ...


def make_event(
    event_type: str,
    task: TaskContract,
    artifact: RegisteredArtifact,
    component_id: str,
    component_version: str,
    **payload: Any,
) -> dict[str, Any]:
    return {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": new_id("event"),
        "timestamp": utc_now(),
        "run_id": artifact.ref.run_id,
        "task_id": task.task_id,
        "artifact_id": artifact.ref.artifact_id,
        "artifact_digest": artifact.ref.artifact_digest,
        "artifact_version": artifact.ref.artifact_version,
        "event_type": event_type,
        "component_id": component_id,
        "component_version": component_version,
        **payload,
    }


class InMemoryEventSink:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, *args: Any, **kwargs: Any) -> None:
        self.events.append(make_event(*args, **kwargs))


class JsonlEventSink:
    def __init__(self, path: Path) -> None:
        self.path = path

    def emit(self, *args: Any, **kwargs: Any) -> None:
        event = make_event(*args, **kwargs)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
