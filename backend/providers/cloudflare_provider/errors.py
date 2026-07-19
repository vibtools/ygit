from __future__ import annotations


class CloudflareProviderError(RuntimeError):
    """Base Cloudflare provider error."""


class CloudflareOAuthConfigurationError(CloudflareProviderError):
    """Cloudflare OAuth configuration is invalid."""


class CloudflareOAuthExchangeError(CloudflareProviderError):
    """Cloudflare OAuth exchange failed."""


class CloudflareAccountValidationError(CloudflareProviderError):
    """Cloudflare account validation failed."""


class CloudflareProviderUnavailableError(CloudflareProviderError):
    """Cloudflare provider API is unavailable."""
