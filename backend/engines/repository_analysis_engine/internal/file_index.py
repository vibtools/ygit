from __future__ import annotations

from typing import Any


def _collect(value: Any, files: set[str]) -> None:
    if isinstance(value, str):
        files.add(value.strip().lstrip("/"))
    elif isinstance(value, list):
        for item in value:
            _collect(item, files)
    elif isinstance(value, dict):
        for key in ("path", "name", "file", "filename"):
            item = value.get(key)
            if isinstance(item, str):
                files.add(item.strip().lstrip("/"))
        for key in ("files", "tree", "items", "children", "paths"):
            _collect(value.get(key), files)


def extract_file_paths(file_tree_snapshot: dict[str, Any] | None) -> set[str]:
    files: set[str] = set()
    if file_tree_snapshot:
        _collect(file_tree_snapshot, files)
    return {path for path in files if path}


def has_file(files: set[str], *names: str) -> bool:
    lowered = {path.lower() for path in files}
    return any(name.lower().strip("/") in lowered for name in names)


def has_suffix(files: set[str], *suffixes: str) -> bool:
    lowered = {path.lower() for path in files}
    return any(path.endswith(suffix.lower()) for path in lowered for suffix in suffixes)


def has_prefix(files: set[str], *prefixes: str) -> bool:
    lowered = {path.lower() for path in files}
    return any(path.startswith(prefix.lower().strip("/")) for path in lowered for prefix in prefixes)
