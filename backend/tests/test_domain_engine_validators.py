import pytest

from backend.engines.domain_engine.errors import DomainSlugInvalidError
from backend.engines.domain_engine.internal.validators import build_full_url, validate_base_domain, validate_domain_slug


def test_domain_slug_validator_accepts_clean_slug() -> None:
    assert validate_domain_slug(" my-portfolio ") == "my-portfolio"


@pytest.mark.parametrize("slug", ["admin", "api", "www", "Bad_Name", "-bad", "bad-", "aa", "bad--slug"])
def test_domain_slug_validator_rejects_invalid_or_reserved_slugs(slug: str) -> None:
    with pytest.raises(DomainSlugInvalidError):
        validate_domain_slug(slug)


def test_base_domain_limited_to_ygit_net_for_mvp() -> None:
    assert validate_base_domain("https://ygit.net/") == "ygit.net"
    with pytest.raises(DomainSlugInvalidError):
        validate_base_domain("example.com")


def test_build_full_url_uses_generated_ygit_domain() -> None:
    assert build_full_url("portfolio", "ygit.net") == "https://portfolio.ygit.net"
