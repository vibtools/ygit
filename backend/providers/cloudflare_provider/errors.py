from __future__ import annotations


class CloudflareProviderError(RuntimeError):
    """Base Cloudflare provider error."""


class CloudflareOAuthConfigurationError(CloudflareProviderError):
    """Cloudflare OAuth configuration is invalid."""


class CloudflareOAuthExchangeError(CloudflareProviderError):
    """Cloudflare OAuth exchange failed."""


class CloudflareOAuthRefreshError(CloudflareProviderError):
    """Cloudflare OAuth refresh failed."""


class CloudflareAccountValidationError(CloudflareProviderError):
    """Cloudflare account validation failed."""


class CloudflarePagesProjectError(CloudflareProviderError):
    """Cloudflare Pages project operation failed."""


class CloudflareProviderUnavailableError(CloudflareProviderError):
    """Cloudflare provider API is unavailable."""
