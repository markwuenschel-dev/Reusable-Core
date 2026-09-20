"""Parse and materialize coding artifacts as independently inspectable repositories."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


CODING_BUNDLE_FORMAT = "coding_bundle/1.0.0"

# The hard verifier runs the oracle with the candidate's materialized workspace as
# cwd, so every top-level file in a bundle is importable by the judging interpreter.
# CPython imports sitecustomize/usercustomize during startup -- before the oracle's
# own modules are collected -- and cwd precedes the standard library on sys.path, so
# a candidate shipping any of these names executes ahead of, or in place of, the
# verifier that is supposed to judge it.
RESERVED_TOP_LEVEL_MODULES = frozenset(
    {
        "sitecustomize",
        "usercustomize",
        "unittest",
        "pytest",
    }
)

_DIFF_PLUS_PATH = re.compile(r"^\+\+\+\s+(?:b/)?(.+?)(?:\t.*)?$")
_DIFF_GIT_PATH = re.compile(r"^diff --git a/(.+?) b/(.+)$")
_EMPTY_INPUT_MARKERS = (
    "empty",
    "if not ",
    "== []",
    "== ()",
    '== ""',
    "== ''",
    "len(",
    "indexerror",
)
_NONE_INPUT_MARKERS = ("is none", "is not none", "none")
_TOKEN_SYNONYMS = {
    "zero": ("zero", "return 0"),
    "empty": ("empty", "if not ", "== []", "== ()", "len("),
    "none": ("none", "is none"),
}


class BundleParseError(ValueError):
    """The artifact bytes cannot be interpreted as an inspectable coding bundle."""


@dataclass(frozen=True)
class FunctionSignature:
    name: str
    required: int
    max_positional: int
    has_varargs: bool


@dataclass(frozen=True)
class CodingBundle:
    base_files: Mapping[str, str]
    patched_files: Mapping[str, str]

    def changed_paths(self) -> tuple[str, ...]:
        paths = set(self.base_files) | set(self.patched_files)
        return tuple(
            path
            for path in sorted(paths)
            if self.base_files.get(path) != self.patched_files.get(path)
        )


def _reserved_top_level_module(normalized: str) -> str | None:
    """Return the reserved module name a repository path would become importable as."""
    head = normalized.split("/", 1)[0]
    name = head[:-3] if head.endswith(".py") else head
    return name if name in RESERVED_TOP_LEVEL_MODULES else None


def normalize_repo_path(path: str) -> str:
    normalized = str(path).replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")
    if not normalized or normalized in {".", ".."} or ".." in normalized.split("/"):
        raise BundleParseError(f"unsafe repository path: {path}")
    reserved = _reserved_top_level_module(normalized)
    if reserved is not None:
        raise BundleParseError(
            f"candidate may not supply the reserved top-level module {reserved!r}: {path}"
        )
    return normalized


def encode_coding_bundle(
    base_files: Mapping[str, str] | None = None,
    overlay: Mapping[str, str | None] | None = None,
) -> str:
    payload = {
        "format": CODING_BUNDLE_FORMAT,
        "base_files": {normalize_repo_path(path): str(content) for path, content in dict(base_files or {}).items()},
        "overlay": {
            normalize_repo_path(path): (None if content is None else str(content))
            for path, content in dict(overlay or {}).items()
        },
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def parse_coding_bundle(content: bytes, metadata: Mapping[str, Any] | None = None) -> CodingBundle:
    text = content.decode("utf-8")
    metadata = dict(metadata or {})
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict) and payload.get("format") == CODING_BUNDLE_FORMAT:
        return _bundle_from_payload(payload)
    diff_bundle = _bundle_from_unified_diff(text)
    if diff_bundle is not None:
        return diff_bundle
    return _bundle_from_snippet(text, metadata)


def materialize_coding_bundle(bundle: CodingBundle, root: Path) -> None:
    resolved_root = root.resolve()
    resolved_root.mkdir(parents=True, exist_ok=True)
    for path, content in bundle.patched_files.items():
        destination = resolved_root.joinpath(*normalize_repo_path(path).split("/"))
        try:
            destination.resolve().relative_to(resolved_root)
        except ValueError as exc:
            raise BundleParseError(f"path escapes workspace: {path}") from exc
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


def is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1]
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if name.endswith("_test.py"):
        return True
    parents = normalized.split("/")[:-1]
    return name.endswith(".py") and any(part in {"test", "tests"} for part in parents)


def public_functions(source: str) -> dict[str, FunctionSignature]:
    tree = ast.parse(source)
    signatures: dict[str, FunctionSignature] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            signatures[node.name] = _function_signature(node, drop_self=False)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                    signatures[f"{node.name}.{item.name}"] = _function_signature(item, drop_self=True)
    return signatures


def call_argument_counts(source: str, func_name: str) -> tuple[int, ...]:
    tree = ast.parse(source)
    short_name = func_name.rsplit(".", 1)[-1]
    counts: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        called = node.func
        matched = False
        if isinstance(called, ast.Name) and called.id == short_name:
            matched = True
        elif isinstance(called, ast.Attribute) and called.attr == short_name:
            matched = True
        if matched:
            counts.append(len(node.args))
    return tuple(counts)


def test_function_names(source: str) -> tuple[str, ...]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ()
    return tuple(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    )


def requirement_tokens(requirement: str) -> tuple[str, ...]:
    return tuple(token for token in requirement.lower().replace("_", "-").split("-") if len(token) > 2)


def requirement_evidence_present(
    requirement: str, text: str, extra_patterns: Sequence[str] | None = None
) -> bool:
    blob = text.lower()
    if extra_patterns:
        return any(str(pattern).lower() in blob for pattern in extra_patterns if str(pattern))
    if requirement.lower() in blob:
        return True
    tokens = requirement_tokens(requirement)
    if not tokens:
        return bool(requirement) and requirement.lower() in blob
    for token in tokens:
        options = _TOKEN_SYNONYMS.get(token, (token,))
        if not any(option in blob for option in options):
            return False
    return True


def tests_covering_requirement(requirement: str, test_files: Mapping[str, str]) -> tuple[str, ...]:
    matches: list[str] = []
    for path, source in test_files.items():
        names = test_function_names(source)
        if not names:
            continue
        haystack = f"{path}\n{source}".lower()
        if requirement_evidence_present(requirement, haystack):
            matches.append(path)
            continue
        for name in names:
            if requirement_evidence_present(requirement, name):
                matches.append(f"{path}:{name}")
    return tuple(matches)


def boundary_handled(case: str, source: str) -> bool:
    blob = source.lower()
    key = str(case).strip().lower().replace("_", "-")
    if key in {"empty-input", "empty", "empty-list"}:
        return any(marker in blob for marker in _EMPTY_INPUT_MARKERS)
    if key in {"none-input", "none", "null-input"}:
        return any(marker in blob for marker in _NONE_INPUT_MARKERS)
    return key.replace("-", " ") in blob or key in blob


def _bundle_from_payload(payload: Mapping[str, Any]) -> CodingBundle:
    base_files = _string_file_map(payload.get("base_files", {}))
    patched = dict(base_files)
    if "patched_files" in payload:
        patched = _string_file_map(payload.get("patched_files", {}))
    overlay = payload.get("overlay", {})
    if not isinstance(overlay, Mapping):
        raise BundleParseError("coding bundle overlay must be an object")
    for raw_path, content in overlay.items():
        path = normalize_repo_path(str(raw_path))
        if content is None:
            patched.pop(path, None)
        else:
            patched[path] = str(content)
    return CodingBundle(base_files, patched)


def _string_file_map(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise BundleParseError("coding bundle file map must be an object")
    files: dict[str, str] = {}
    for raw_path, content in value.items():
        if content is None:
            continue
        files[normalize_repo_path(str(raw_path))] = str(content)
    return files


def _bundle_from_unified_diff(text: str) -> CodingBundle | None:
    lines = text.splitlines()
    if not any(line.startswith(("diff --git ", "--- ", "+++ ")) for line in lines[:20]):
        return None
    paths: list[str] = []
    for line in lines:
        git_match = _DIFF_GIT_PATH.match(line)
        if git_match:
            paths.append(normalize_repo_path(git_match.group(2)))
            continue
        plus_match = _DIFF_PLUS_PATH.match(line)
        if plus_match and plus_match.group(1) != "/dev/null":
            paths.append(normalize_repo_path(plus_match.group(1)))
    unique = tuple(dict.fromkeys(paths))
    if not unique:
        return None
    return CodingBundle({}, {path: text for path in unique})


def _bundle_from_snippet(text: str, metadata: Mapping[str, Any]) -> CodingBundle:
    claimed = metadata.get("changed_paths")
    if isinstance(claimed, (list, tuple)) and len(claimed) == 1:
        path = normalize_repo_path(str(claimed[0]))
    else:
        path = "snippet.py"
    return CodingBundle({}, {path: text})


def _function_signature(node: ast.FunctionDef, *, drop_self: bool) -> FunctionSignature:
    positional = list(node.args.posonlyargs) + list(node.args.args)
    if drop_self and positional and positional[0].arg in {"self", "cls"}:
        positional = positional[1:]
    default_count = len(node.args.defaults)
    required = max(0, len(positional) - default_count)
    return FunctionSignature(
        name=node.name,
        required=required,
        max_positional=len(positional),
        has_varargs=node.args.vararg is not None,
    )
