import pytest

from backend.engines.repository_engine.errors import RepositoryProviderUnsupportedError, RepositoryUrlInvalidError
from backend.engines.repository_engine.internal.validators import parse_github_repository_url


def test_parse_https_github_repository_url() -> None:
    parsed = parse_github_repository_url("https://github.com/vibtools/ygit.git")
    assert parsed.provider == "github"
    assert parsed.owner == "vibtools"
    assert parsed.repo == "ygit"
    assert parsed.normalized_url == "https://github.com/vibtools/ygit"


def test_parse_ssh_github_repository_url() -> None:
    parsed = parse_github_repository_url("git@github.com:vibtools/ygit.git")
    assert parsed.owner == "vibtools"
    assert parsed.repo == "ygit"
    assert parsed.normalized_url == "https://github.com/vibtools/ygit"


def test_rejects_non_github_provider() -> None:
    with pytest.raises(RepositoryProviderUnsupportedError):
        parse_github_repository_url("https://gitlab.com/vibtools/ygit")


def test_rejects_invalid_github_url() -> None:
    with pytest.raises(RepositoryUrlInvalidError):
        parse_github_repository_url("https://github.com/vibtools")
