from __future__ import annotations

import httpx
import pytest

from backend.providers.cloudflare_provider import (
    client as cloudflare_client_module,
)
from backend.providers.cloudflare_provider.client import (
    CloudflareProviderClient,
)
from backend.providers.cloudflare_provider.errors import (
    CloudflarePagesAssetUploadError,
    CloudflareProviderUnavailableError,
)


HASH_A = "a" * 32
HASH_B = "b" * 32
HASH_C = "c" * 32
ACCESS_VALUE = "pages-access-value-for-test"
UPLOAD_VALUE = "pages-upload-jwt-for-test"


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int,
        payload: object,
    ) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> object:
        return self._payload


def upload_token_payload() -> dict[str, object]:
    return {
        "success": True,
        "errors": [],
        "messages": [],
        "result": {
            "jwt": UPLOAD_VALUE,
        },
    }


@pytest.mark.asyncio
async def test_get_upload_token_uses_access_bearer(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class TokenClient:
        def __init__(
            self,
            *,
            timeout: float,
            headers: dict[str, str],
        ) -> None:
            captured["timeout"] = timeout
            captured["headers"] = dict(headers)

        async def __aenter__(self):
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ) -> None:
            return None

        async def get(self, url: str) -> FakeResponse:
            captured["url"] = url
            return FakeResponse(
                status_code=200,
                payload=upload_token_payload(),
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        TokenClient,
    )

    provider = CloudflareProviderClient(
        timeout_seconds=7.5,
    )
    token = await provider.get_pages_upload_token(
        account_id="account/id",
        project_name="ygit demo",
        bearer_value=ACCESS_VALUE,
    )

    assert captured["timeout"] == 7.5
    assert captured["headers"] == {
        "Authorization": f"Bearer {ACCESS_VALUE}",
    }
    assert captured["url"] == (
        "https://api.cloudflare.com/client/v4/"
        "accounts/account%2Fid/pages/projects/"
        "ygit%20demo/upload-token"
    )
    assert (
        token.upload_token.get_secret_value()
        == UPLOAD_VALUE
    )


@pytest.mark.asyncio
async def test_upload_token_is_masked_in_serialization(
    monkeypatch,
) -> None:
    class TokenClient:
        def __init__(
            self,
            *,
            timeout: float,
            headers: dict[str, str],
        ) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ) -> None:
            return None

        async def get(self, url: str) -> FakeResponse:
            return FakeResponse(
                status_code=200,
                payload=upload_token_payload(),
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        TokenClient,
    )

    token = (
        await CloudflareProviderClient()
        .get_pages_upload_token(
            account_id="account-1",
            project_name="ygit-demo",
            bearer_value=ACCESS_VALUE,
        )
    )
    serialized = token.model_dump_json()

    assert UPLOAD_VALUE not in serialized
    assert "**********" in serialized


@pytest.mark.asyncio
async def test_missing_asset_check_uses_upload_jwt(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class MissingClient:
        def __init__(
            self,
            *,
            timeout: float,
            headers: dict[str, str],
        ) -> None:
            captured["headers"] = dict(headers)

        async def __aenter__(self):
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ) -> None:
            return None

        async def post(
            self,
            url: str,
            *,
            json: dict[str, list[str]],
        ) -> FakeResponse:
            captured["url"] = url
            captured["json"] = json
            return FakeResponse(
                status_code=200,
                payload={
                    "success": True,
                    "result": [HASH_B],
                },
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        MissingClient,
    )

    token = (
        CloudflareProviderClient
        ._pages_upload_token_from_payload(
            upload_token_payload()
        )
    )
    plan = (
        await CloudflareProviderClient()
        .check_missing_pages_assets(
            upload_token=token,
            content_hashes=[
                HASH_B,
                HASH_A,
                HASH_A,
            ],
        )
    )

    assert captured["headers"] == {
        "Authorization": f"Bearer {UPLOAD_VALUE}",
        "Content-Type": "application/json",
    }
    assert captured["url"] == (
        "https://api.cloudflare.com/client/v4/"
        "pages/assets/check-missing"
    )
    assert captured["json"] == {
        "hashes": [HASH_A, HASH_B],
    }
    assert plan.requested_hash_count == 2
    assert plan.missing_hashes == [HASH_B]
    assert plan.cached_hash_count == 1
    assert UPLOAD_VALUE not in plan.model_dump_json()


@pytest.mark.asyncio
async def test_prepare_upload_runs_token_then_cache_check(
    monkeypatch,
) -> None:
    calls: list[str] = []

    class SequenceClient:
        def __init__(
            self,
            *,
            timeout: float,
            headers: dict[str, str],
        ) -> None:
            self.headers = headers

        async def __aenter__(self):
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ) -> None:
            return None

        async def get(self, url: str) -> FakeResponse:
            calls.append("token")
            return FakeResponse(
                status_code=200,
                payload=upload_token_payload(),
            )

        async def post(
            self,
            url: str,
            *,
            json: dict[str, list[str]],
        ) -> FakeResponse:
            calls.append("missing")
            return FakeResponse(
                status_code=200,
                payload={
                    "success": True,
                    "result": [],
                },
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        SequenceClient,
    )

    plan = (
        await CloudflareProviderClient()
        .prepare_pages_asset_upload(
            account_id="account-1",
            project_name="ygit-demo",
            bearer_value=ACCESS_VALUE,
            content_hashes=[HASH_A],
        )
    )

    assert calls == ["token", "missing"]
    assert plan.requested_hash_count == 1
    assert plan.missing_hashes == []
    assert plan.cached_hash_count == 1


@pytest.mark.asyncio
async def test_foreign_missing_hash_is_rejected(
    monkeypatch,
) -> None:
    class InvalidMissingClient:
        def __init__(
            self,
            *,
            timeout: float,
            headers: dict[str, str],
        ) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ) -> None:
            return None

        async def post(
            self,
            url: str,
            *,
            json: dict[str, list[str]],
        ) -> FakeResponse:
            return FakeResponse(
                status_code=200,
                payload={
                    "success": True,
                    "result": [HASH_C],
                },
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        InvalidMissingClient,
    )

    token = (
        CloudflareProviderClient
        ._pages_upload_token_from_payload(
            upload_token_payload()
        )
    )

    with pytest.raises(
        CloudflarePagesAssetUploadError,
        match="invalid missing asset hashes",
    ):
        await CloudflareProviderClient().check_missing_pages_assets(
            upload_token=token,
            content_hashes=[HASH_A],
        )


@pytest.mark.asyncio
async def test_invalid_requested_hash_is_rejected_before_http(
    monkeypatch,
) -> None:
    class ForbiddenClient:
        def __init__(self, **kwargs) -> None:
            raise AssertionError(
                "HTTP client must not be created"
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        ForbiddenClient,
    )

    token = (
        CloudflareProviderClient
        ._pages_upload_token_from_payload(
            upload_token_payload()
        )
    )

    with pytest.raises(
        CloudflarePagesAssetUploadError,
        match="hash is invalid",
    ):
        await CloudflareProviderClient().check_missing_pages_assets(
            upload_token=token,
            content_hashes=["not-a-content-hash"],
        )


@pytest.mark.asyncio
async def test_upload_session_transport_failure_is_sanitized(
    monkeypatch,
) -> None:
    class FailingClient:
        def __init__(
            self,
            *,
            timeout: float,
            headers: dict[str, str],
        ) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ) -> None:
            return None

        async def get(self, url: str) -> FakeResponse:
            request = httpx.Request("GET", url)
            raise httpx.ConnectError(
                "provider transport detail",
                request=request,
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        FailingClient,
    )

    with pytest.raises(
        CloudflareProviderUnavailableError
    ) as captured:
        await CloudflareProviderClient().get_pages_upload_token(
            account_id="account-1",
            project_name="ygit-demo",
            bearer_value=ACCESS_VALUE,
        )

    message = str(captured.value)
    assert ACCESS_VALUE not in message
    assert "provider transport detail" not in message


@pytest.mark.asyncio
async def test_upload_session_rejection_is_sanitized(
    monkeypatch,
) -> None:
    class RejectedClient:
        def __init__(
            self,
            *,
            timeout: float,
            headers: dict[str, str],
        ) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ) -> None:
            return None

        async def get(self, url: str) -> FakeResponse:
            return FakeResponse(
                status_code=403,
                payload={
                    "errors": [
                        {
                            "message": (
                                "provider-secret-detail"
                            ),
                        },
                    ],
                },
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        RejectedClient,
    )

    with pytest.raises(
        CloudflarePagesAssetUploadError
    ) as captured:
        await CloudflareProviderClient().get_pages_upload_token(
            account_id="account-1",
            project_name="ygit-demo",
            bearer_value=ACCESS_VALUE,
        )

    message = str(captured.value)
    assert ACCESS_VALUE not in message
    assert "provider-secret-detail" not in message
