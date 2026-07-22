from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, Protocol


DEFAULT_PROVIDER_EXECUTION_MODE: Final[str] = (
    "disabled"
)
CURRENT_PROVIDER_EXECUTION_MODE: Final[str] = (
    "cloudflare"
)

ProviderExecutionMode = Literal[
    "disabled",
    "cloudflare",
]
ProviderExecutionPolicySource = Literal[
    "server_settings",
]


class ProviderExecutionSettings(
    Protocol
):
    worker_provider_execution_mode: str


class WorkerProviderExecutionPolicyError(
    ValueError
):
    """Raised when trusted worker policy cannot be resolved safely."""

    def __init__(
        self,
        *,
        mode: str,
    ) -> None:
        self.mode = mode
        super().__init__(
            "Worker provider execution policy "
            "could not be resolved."
        )


@dataclass(frozen=True, slots=True)
class WorkerProviderExecutionPolicy:
    mode: ProviderExecutionMode
    enabled: bool
    provider: str | None
    source: ProviderExecutionPolicySource


def _normalize_mode(
    value: object,
) -> str:
    normalized = str(value).strip().casefold()
    return normalized or DEFAULT_PROVIDER_EXECUTION_MODE


def resolve_worker_provider_execution_policy(
    settings: ProviderExecutionSettings,
) -> WorkerProviderExecutionPolicy:
    """Resolve provider execution from trusted server settings only."""

    mode = _normalize_mode(
        settings.worker_provider_execution_mode
    )

    if mode == DEFAULT_PROVIDER_EXECUTION_MODE:
        return WorkerProviderExecutionPolicy(
            mode="disabled",
            enabled=False,
            provider=None,
            source="server_settings",
        )

    if mode == CURRENT_PROVIDER_EXECUTION_MODE:
        return WorkerProviderExecutionPolicy(
            mode="cloudflare",
            enabled=True,
            provider="cloudflare",
            source="server_settings",
        )

    raise WorkerProviderExecutionPolicyError(
        mode=mode
    )
