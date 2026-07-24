from __future__ import annotations

from typing import Final

DEFAULT_REPOSITORY_PROVIDER: Final[str] = "github"


def resolve_repository_provider(provider: str | None) -> str:
    """Resolve the Repository Engine provider without changing runtime behavior."""
    selected_provider = (provider or "").strip()
    if not selected_provider:
        return DEFAULT_REPOSITORY_PROVIDER
    return selected_provider
