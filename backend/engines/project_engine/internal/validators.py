from __future__ import annotations

import re

from backend.engines.project_engine.errors import ProjectNameInvalidError, ProjectSlugInvalidError

_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,62}[a-z0-9])?$")
_RESERVED_SLUGS = {
    "admin",
    "api",
    "app",
    "auth",
    "dashboard",
    "docs",
    "health",
    "login",
    "logout",
    "new",
    "settings",
    "static",
    "support",
    "www",
}


def validate_project_name(name: str) -> str:
    cleaned = " ".join(name.strip().split())
    if not cleaned or len(cleaned) > 120:
        raise ProjectNameInvalidError()
    return cleaned


def validate_project_slug(slug: str) -> str:
    cleaned = slug.strip().lower()
    if len(cleaned) < 3 or cleaned in _RESERVED_SLUGS or not _SLUG_RE.fullmatch(cleaned):
        raise ProjectSlugInvalidError()
    return cleaned
