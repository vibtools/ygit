from __future__ import annotations


class GitHubProviderError(Exception):
    """Base GitHub provider error. Provider errors must be sanitized by engines."""


class GitHubRepositoryNotFoundError(GitHubProviderError):
    pass


class GitHubProviderUnavailableError(GitHubProviderError):
    pass
