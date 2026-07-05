from __future__ import annotations


class PlatformEngineError(Exception):
    """Base error for Platform Engine failures."""


class PlatformSettingNotFoundError(PlatformEngineError):
    """Raised when a platform setting cannot be found."""


class PlatformSettingInvalidError(PlatformEngineError):
    """Raised when a platform setting payload is invalid."""


class FeatureFlagNotFoundError(PlatformEngineError):
    """Raised when a feature flag cannot be found."""


class FeatureFlagInvalidError(PlatformEngineError):
    """Raised when a feature flag payload is invalid."""
