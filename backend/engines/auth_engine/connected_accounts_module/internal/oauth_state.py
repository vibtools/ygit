from __future__ import annotations

import hmac
from secrets import token_urlsafe

from backend.core.config import get_settings
from backend.engines.auth_engine.connected_accounts_module.schemas import ProviderName


class ConnectedAccountOAuthState:
    """Minimal OAuth state helper for Connected Accounts v0.1.0.

    The state value is intentionally simple for this MVP module. Full provider OAuth
    session persistence can be expanded in a later approved revision.
    """

    @staticmethod
    def new_state(*, user_id: str, provider: ProviderName) -> str:
        nonce = token_urlsafe(18)
        return f"ca.{provider}.{user_id}.{nonce}"

    @staticmethod
    def validate_state(*, state: str, user_id: str, provider: ProviderName) -> bool:
        expected_prefix = f"ca.{provider}.{user_id}."
        return hmac.compare_digest(state[: len(expected_prefix)], expected_prefix)


class TokenReferenceFactory:
    """Creates safe token references without exposing token values."""

    @staticmethod
    def new_token_ref(*, provider: ProviderName) -> str:
        return f"{provider}_token_ref_{token_urlsafe(24)}"

    @staticmethod
    def key_version() -> str:
        return get_settings().token_encryption_key_version



class ConnectedAccountInstallState(ConnectedAccountOAuthState):
    """GitHub App installation state helper.

    Kept separate from the legacy OAuth naming so new GitHub App code can use
    installation terminology without breaking older Connected Accounts tests.
    """
