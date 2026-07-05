from __future__ import annotations

from backend.engines.auth_engine.errors import AuthRedirectInvalidError


def validate_local_next_path(value: str | None, default: str) -> str:
    target = value or default
    if not target.startswith("/") or target.startswith("//"):
        raise AuthRedirectInvalidError()
    if "\r" in target or "\n" in target:
        raise AuthRedirectInvalidError()
    return target
