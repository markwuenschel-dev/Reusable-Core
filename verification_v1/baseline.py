"""Frozen VS-V1.1 baseline identity for the V1.2 evidence program."""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from .aggregation import ShadowPolicy
from .checklets import default_coding_checklets
from .contracts import SCHEMA_VERSION as CONTRACT_SCHEMA_VERSION
from .domain import CodingDomainPack
from .evaluation import DATASET_SCHEMA_VERSION
from .evidence import EXPERIMENT_BASELINE_ID, canonical_digest
from .gates import MetadataShapeGate
from .hard_verify import CommandHardVerifier, UnavailableHardVerifier
from .runner import VerificationRunner
from .telemetry import EVENT_SCHEMA_VERSION

BASELINE_SCHEMA_VERSION = "verification-v1.2-baseline/1.1.0"
SNAPSHOT_SCHEMA_VERSION = "verification-v1.2-baseline-snapshot/1.0.0"
SUPPORTED_PYTHON_VERSIONS = ("3.11", "3.12", "3.13")
FROZEN_IMPLEMENTATION_PATHS = (
    "verification_v1/aggregation.py",
    "verification_v1/artifacts.py",
    "verification_v1/bundle.py",
    "verification_v1/checklets.py",
    "verification_v1/contracts.py",
    "verification_v1/domain.py",
    "verification_v1/evaluation.py",
    "verification_v1/gates.py",
    "verification_v1/hard_verify.py",
    "verification_v1/runner.py",
    "verification_v1/telemetry.py",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _canonical_source_bytes(path: Path, root: Path | None = None) -> bytes:
    """Return Git-reconstructable file bytes (LF). CRLF-only working trees must not drift the freeze."""
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    base = root or repo_root()
    try:
        relative = path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return raw
    git_bytes = _git_bytes(("show", f"HEAD:{relative}"), base)
    if git_bytes is None:
        return raw
    git_norm = git_bytes.replace(b"\r\n", b"\n")
    if raw == git_norm:
        return git_norm
    return raw


def _file_sha256(path: Path, root: Path | None = None) -> str:
    return sha256(_canonical_source_bytes(path, root)).hexdigest()


def _git(args: tuple[str, ...], cwd: Path) -> str | None:
    raw = _git_bytes(args, cwd)
    if raw is None:
        return None
    return raw.decode("utf-8", errors="replace").strip()


def _git_bytes(args: tuple[str, ...], cwd: Path) -> bytes | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def implementation_hashes(root: Path | None = None) -> dict[str, str]:
    base = root or repo_root()
    hashes: dict[str, str] = {}
    for relative in FROZEN_IMPLEMENTATION_PATHS:
        path = base / relative
        hashes[relative] = _file_sha256(path, base)
    return hashes


def collect_baseline(root: Path | None = None) -> dict[str, Any]:
    base = root or repo_root()
    pack = CodingDomainPack.default()
    checklets = default_coding_checklets()
    policy = ShadowPolicy()
    gate = MetadataShapeGate()
    hashes = implementation_hashes(base)
    checklet_impl_hash = hashes["verification_v1/checklets.py"]
    git_sha = _git(("rev-parse", "HEAD"), base)
    dirty_paths = []
    for relative in FROZEN_IMPLEMENTATION_PATHS:
        status = _git(("status", "--porcelain", "--untracked-files=no", "--", relative), base)
        if status:
            dirty_paths.append(relative)
    git_dirty = bool(dirty_paths)
    return {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "experiment_baseline_id": EXPERIMENT_BASELINE_ID,
        "verification_schema_versions": {
            "contracts": CONTRACT_SCHEMA_VERSION,
            "evaluation": DATASET_SCHEMA_VERSION,
            "events": EVENT_SCHEMA_VERSION,
            "baseline": BASELINE_SCHEMA_VERSION,
        },
        "domain_pack": {"id": pack.pack_id, "version": pack.version},
        "checklets": [
            {
                "checklet_id": checklet.spec.checklet_id,
                "version": checklet.spec.version,
                "criterion_id": checklet.spec.criterion_id,
                "evidence_family_id": checklet.spec.evidence_family_template,
                "implementation_type": checklet.spec.implementation_type,
                "prompt_template_hash": None,
                "implementation_hash": checklet_impl_hash,
            }
            for checklet in checklets
        ],
        "shadow_policy": {"id": policy.policy_id, "version": policy.version},
        "hard_verifiers": [
            {"id": CommandHardVerifier.verifier_id, "version": CommandHardVerifier.version},
            {"id": UnavailableHardVerifier.verifier_id, "version": UnavailableHardVerifier.version},
        ],
        "gates": [{"id": gate.gate_id, "version": gate.version}],
        "runner": {"version": VerificationRunner.version},
        "evaluation_schema_version": DATASET_SCHEMA_VERSION,
        "supported_python_versions": list(SUPPORTED_PYTHON_VERSIONS),
        "runtime_python": ".".join(str(part) for part in sys.version_info[:3]),
        "repository_commit_sha": git_sha or "unknown",
        "verification_v1_working_tree_dirty": bool(git_dirty),
        "implementation_hashes": hashes,
        "content_address": canonical_digest({"id": EXPERIMENT_BASELINE_ID, "hashes": hashes}),
        "source_snapshot_digest": canonical_digest({path: hashes[path] for path in FROZEN_IMPLEMENTATION_PATHS}),
    }


def baseline_manifest_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / "evals" / "verification_v1" / "v12" / "vs-v1.1-baseline-001.json"


def baseline_snapshot_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / "evals" / "verification_v1" / "v12" / "vs-v1.1-baseline-001.sources.json"


def collect_source_snapshot(root: Path | None = None) -> dict[str, Any]:
    base = root or repo_root()
    files: dict[str, Any] = {}
    for relative in FROZEN_IMPLEMENTATION_PATHS:
        raw = _canonical_source_bytes(base / relative, base)
        files[relative] = {
            "sha256": sha256(raw).hexdigest(),
            "size": len(raw),
            "content_b64": base64.b64encode(raw).decode("ascii"),
        }
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "experiment_baseline_id": EXPERIMENT_BASELINE_ID,
        "files": files,
        "snapshot_digest": canonical_digest({path: files[path]["sha256"] for path in FROZEN_IMPLEMENTATION_PATHS}),
    }


def load_source_snapshot(path: Path | None = None) -> dict[str, Any]:
    snapshot = path or baseline_snapshot_path()
    payload = json.loads(snapshot.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("baseline source snapshot must be a JSON object")
    return payload


def restore_source_snapshot(snapshot: Mapping[str, Any], destination: Path) -> dict[str, str]:
    restored: dict[str, str] = {}
    files = snapshot.get("files")
    if not isinstance(files, Mapping):
        raise ValueError("baseline source snapshot lacks files")
    for relative, payload in files.items():
        raw = base64.b64decode(str(payload["content_b64"]))
        digest = sha256(raw).hexdigest()
        if digest != str(payload["sha256"]):
            raise ValueError(f"snapshot bytes do not match recorded hash: {relative}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        restored[str(relative)] = digest
    return restored


def git_tree_hashes(commit: str, root: Path | None = None) -> dict[str, str] | None:
    base = root or repo_root()
    hashes: dict[str, str] = {}
    for relative in FROZEN_IMPLEMENTATION_PATHS:
        raw = _git_bytes(("show", f"{commit}:{relative}"), base)
        if raw is None:
            return None
        hashes[relative] = sha256(raw).hexdigest()
    return hashes


def load_frozen_baseline(path: Path | None = None) -> dict[str, Any]:
    manifest = path or baseline_manifest_path()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("baseline manifest must be a JSON object")
    return payload


def validate_baseline(frozen: Mapping[str, Any] | None = None, root: Path | None = None) -> dict[str, Any]:
    live = collect_baseline(root)
    reference = dict(frozen) if frozen is not None else load_frozen_baseline(baseline_manifest_path(root))
    errors: list[str] = []
    if reference.get("experiment_baseline_id") != EXPERIMENT_BASELINE_ID:
        errors.append("frozen baseline id is not vs-v1.1-baseline-001")
    if live["implementation_hashes"] != reference.get("implementation_hashes"):
        errors.append("implementation hashes drifted from frozen V1.1 baseline")
    if live["content_address"] != reference.get("content_address"):
        errors.append("baseline content address drifted")
    live_ids = tuple(item["checklet_id"] for item in live["checklets"])
    frozen_ids = tuple(item["checklet_id"] for item in reference.get("checklets", []))
    if live_ids != frozen_ids or len(live_ids) != 5:
        errors.append("frozen checklet set is not the five V1.1 checklets")
    if live["shadow_policy"] != reference.get("shadow_policy"):
        errors.append("shadow policy identity drifted")
    if live["runner"] != reference.get("runner"):
        errors.append("runner version drifted")
    if live["domain_pack"] != reference.get("domain_pack"):
        errors.append("domain pack identity drifted")
    snapshot_ok = False
    snapshot_errors: list[str] = []
    try:
        snapshot = load_source_snapshot(baseline_snapshot_path(root))
        snapshot_hashes = {
            path: str(payload["sha256"])
            for path, payload in dict(snapshot.get("files") or {}).items()
        }
        if snapshot_hashes != live["implementation_hashes"]:
            snapshot_errors.append("source snapshot hashes do not match live V1.1 files")
        if snapshot.get("snapshot_digest") != live.get("source_snapshot_digest"):
            snapshot_errors.append("source snapshot digest drifted")
        with tempfile.TemporaryDirectory(prefix="vs-v11-baseline-restore-") as directory:
            restore_hashes = restore_source_snapshot(snapshot, Path(directory))
            if restore_hashes != live["implementation_hashes"]:
                snapshot_errors.append("source snapshot is not reconstructable from stored bytes")
        snapshot_ok = not snapshot_errors
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        snapshot_errors.append(f"source snapshot unavailable or invalid: {type(exc).__name__}")
        snapshot_ok = False
    git_reconstructable = False
    recorded_sha = str(reference.get("repository_commit_sha") or "")
    live_sha = str(live.get("repository_commit_sha") or "")
    candidates: list[str] = []
    for sha in (recorded_sha, live_sha):
        if sha and sha != "unknown" and sha not in candidates:
            candidates.append(sha)
    for sha in candidates:
        commit_hashes = git_tree_hashes(sha, root)
        if commit_hashes == live["implementation_hashes"]:
            git_reconstructable = True
            break
    snapshot_path = baseline_snapshot_path(root)
    snapshot_tracked = _git(("ls-files", "--error-unmatch", str(snapshot_path.relative_to(root or repo_root())).replace("\\", "/")), root or repo_root()) is not None
    content_match = live["implementation_hashes"] == reference.get("implementation_hashes") and live["content_address"] == reference.get("content_address")
    source_reconstructable = snapshot_ok and (snapshot_tracked or git_reconstructable)
    dirty = bool(live.get("verification_v1_working_tree_dirty"))
    if dirty and not git_reconstructable and not snapshot_tracked:
        errors.append("baseline content depends on an uncommitted working tree and is not reconstructable from tracked source")
    errors.extend(snapshot_errors)
    ok = (not errors) and content_match and source_reconstructable
    return {
        "ok": ok,
        "errors": errors,
        "live": live,
        "frozen_id": reference.get("experiment_baseline_id"),
        "baseline_id": reference.get("experiment_baseline_id"),
        "content_address": live["content_address"],
        "source_snapshot_digest": live.get("source_snapshot_digest"),
        "content_match": content_match,
        "source_reconstructable": source_reconstructable,
        "snapshot_reconstructable": snapshot_ok,
        "snapshot_tracked": snapshot_tracked,
        "git_commit_match": git_reconstructable,
        "tree_match": git_reconstructable,
        "git_reconstructable": git_reconstructable,
        "collection_ready": ok,
        "verification_v1_working_tree_dirty": dirty,
        "git_note": (
            "Git HEAD currently contains the frozen V1.1 files"
            if git_reconstructable
            else "Git HEAD does not contain the frozen V1.1 files; reconstruct from a tracked source snapshot or commit those files"
        ),
    }


def write_baseline(path: Path | None = None, root: Path | None = None) -> Path:
    destination = path or baseline_manifest_path(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = collect_baseline(root)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    snapshot_path = baseline_snapshot_path(root)
    snapshot_path.write_text(json.dumps(collect_source_snapshot(root), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
