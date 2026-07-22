from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias


AG_001_GATE_ID: Final[str] = "AG-001"
AG_001_PHASE: Final[str] = (
    "before_deploy_completion"
)
DEFAULT_DEPLOY_PROVIDER: Final[str] = (
    "cloudflare"
)

DeployProviderResolver: TypeAlias = Callable[
    [str],
    str | None,
]
DeployProviderResolutionSource: TypeAlias = Literal[
    "default",
    "core",
    "extension",
]


class DeployProviderGateResolutionError(
    ValueError
):
    """Raised when AG-001 cannot resolve a provider safely."""

    def __init__(
        self,
        *,
        build_target: str,
    ) -> None:
        self.build_target = build_target
        super().__init__(
            "Deploy provider could not be resolved "
            "for the requested build target."
        )


@dataclass(frozen=True, slots=True)
class DeployProviderGateDecision:
    gate_id: str
    phase: str
    provider: str
    build_target: str | None
    resolution_source: (
        DeployProviderResolutionSource
    )


def _normalize_key(
    value: object,
) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip().casefold()
    return normalized or None


def resolve_deploy_provider(
    build_target: str | None = None,
    *,
    resolver: (
        DeployProviderResolver | None
    ) = None,
) -> DeployProviderGateDecision:
    """Resolve AG-001 without executing a provider.

    No build target keeps the current Cloudflare default.
    An explicit Cloudflare target remains a core decision.
    Other targets require an injected future extension resolver.
    """

    normalized_target = _normalize_key(
        build_target
    )

    if normalized_target is None:
        return DeployProviderGateDecision(
            gate_id=AG_001_GATE_ID,
            phase=AG_001_PHASE,
            provider=DEFAULT_DEPLOY_PROVIDER,
            build_target=None,
            resolution_source="default",
        )

    if (
        normalized_target
        == DEFAULT_DEPLOY_PROVIDER
    ):
        return DeployProviderGateDecision(
            gate_id=AG_001_GATE_ID,
            phase=AG_001_PHASE,
            provider=DEFAULT_DEPLOY_PROVIDER,
            build_target=normalized_target,
            resolution_source="core",
        )

    if resolver is None:
        raise DeployProviderGateResolutionError(
            build_target=normalized_target
        )

    try:
        resolved_provider = _normalize_key(
            resolver(normalized_target)
        )
    except Exception:
        raise DeployProviderGateResolutionError(
            build_target=normalized_target
        ) from None

    if resolved_provider is None:
        raise DeployProviderGateResolutionError(
            build_target=normalized_target
        )

    return DeployProviderGateDecision(
        gate_id=AG_001_GATE_ID,
        phase=AG_001_PHASE,
        provider=resolved_provider,
        build_target=normalized_target,
        resolution_source="extension",
    )
