from __future__ import annotations


class CloudflareProviderClient:
    """Cloudflare API wrapper only. This class must not contain YGIT business logic."""

    provider = "cloudflare"

    async def validate_account(self, token_ref: str) -> dict[str, str]:
        if not token_ref:
            return {"provider": self.provider, "status": "invalid"}
        return {"provider": self.provider, "status": "validated", "account_name": "cloudflare-account"}
