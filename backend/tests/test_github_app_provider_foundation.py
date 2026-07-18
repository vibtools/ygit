from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from backend.providers.github_provider.client import GitHubProviderClient


def _test_private_key_pem() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


def test_github_app_installation_url_contains_state_and_no_secrets() -> None:
    client = GitHubProviderClient()
    url = client.build_app_installation_url(
        install_url="https://github.com/apps/ygit/installations/new",
        state="ca.github.user_1.safe",
    )

    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "github.com"
    assert parsed.path == "/apps/ygit/installations/new"
    assert query["state"] == ["ca.github.user_1.safe"]
    assert "private_key" not in url
    assert "client_secret" not in url
    assert "access_token" not in url
    assert "installation_token" not in url


def test_github_app_jwt_is_rs256_and_uses_app_id_as_issuer() -> None:
    private_pem, public_pem = _test_private_key_pem()
    client = GitHubProviderClient()

    token = client.create_app_jwt(app_id="12345", private_key_pem=private_pem)

    header = jwt.get_unverified_header(token)
    decoded = jwt.decode(token, public_pem, algorithms=["RS256"], issuer="12345")

    assert header["alg"] == "RS256"
    assert decoded["iss"] == "12345"
    assert "iat" in decoded
    assert "exp" in decoded


def test_github_app_installation_payload_mapping() -> None:
    client = GitHubProviderClient()

    installation = client._installation_from_payload(
        {
            "id": 98765,
            "account": {
                "id": 123,
                "login": "vibtools",
                "type": "Organization",
            },
            "target_type": "Organization",
            "repository_selection": "selected",
        }
    )

    assert installation.provider == "github"
    assert installation.installation_id == 98765
    assert installation.account_id == "123"
    assert installation.account_login == "vibtools"
    assert installation.account_type == "Organization"
    assert installation.repository_selection == "selected"
