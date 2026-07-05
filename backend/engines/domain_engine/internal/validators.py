from __future__ import annotations

import re

from backend.engines.domain_engine.errors import DomainSlugInvalidError

RESERVED_SLUGS = {
    "admin",
    "api",
    "app",
    "assets",
    "auth",
    "blog",
    "cdn",
    "dashboard",
    "dev",
    "docs",
    "help",
    "health",
    "login",
    "logout",
    "mail",
    "new",
    "ops",
    "root",
    "settings",
    "static",
    "status",
    "support",
    "system",
    "www",
}

SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,62}[a-z0-9])$")
BASE_DOMAIN_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.-]{1,253}[a-z0-9])$")


def validate_domain_slug(value: str) -> str:
    slug = value.strip().lower()
    if not SLUG_RE.fullmatch(slug):
        raise DomainSlugInvalidError(
            "Slug must be 3-64 characters, lowercase, alphanumeric or hyphen, and may not begin or end with a hyphen."
        )
    if "--" in slug:
        raise DomainSlugInvalidError("Slug must not contain consecutive hyphens.")
    if slug in RESERVED_SLUGS:
        raise DomainSlugInvalidError("Slug is reserved by YGIT platform.")
    return slug


def validate_base_domain(value: str) -> str:
    base_domain = value.strip().lower().removeprefix("https://").removeprefix("http://").strip("/")
    if base_domain != "ygit.net":
        raise DomainSlugInvalidError("MVP Domain Engine only supports ygit.net generated URLs.")
    if not BASE_DOMAIN_RE.fullmatch(base_domain) or ".." in base_domain:
        raise DomainSlugInvalidError("Base domain is invalid.")
    return base_domain


def build_full_url(slug: str, base_domain: str) -> str:
    return f"https://{slug}.{base_domain}"
