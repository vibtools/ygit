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
from backend.providers.cloudflare_provider.schemas import (
    CloudflarePagesUploadToken,
)


HASH_A = "a" * 32
HASH_B = "b" * 32
UPLOAD_VALUE = "pages-upload-jwt-for-test"


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int,
        payload: object,
        json_error: Exception | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error

    def json(self) -> object:
        if self._json_error is not None:
            raise self._json_error
        return self._payload


def upload_session() -> CloudflarePagesUploadToken:
    session_fields = {
        "upload_token": UPLOAD_VALUE,
    }
    return CloudflarePagesUploadToken(
        **session_fields
    )


@pytest.mark.asyncio
async def test_hash_upsert_uses_upload_jwt_and_deduplicates(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class UpsertClient:
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
                    "result": None,
                },
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        UpsertClient,
    )

    result = await CloudflareProviderClient(
        timeout_seconds=4.5,
    ).upsert_pages_asset_hashes(
        upload_session=upload_session(),
        content_hashes=[
            HASH_B,
            HASH_A,
            HASH_A,
        ],
    )

    assert captured["timeout"] == 4.5
    assert captured["headers"] == {
        "Authorization": (
            f"Bearer {UPLOAD_VALUE}"
        ),
        "Content-Type": "application/json",
    }
    assert captured["url"] == (
        "https://api.cloudflare.com/client/v4/"
        "pages/assets/upsert-hashes"
    )
    assert captured["json"] == {
        "hashes": [
            HASH_A,
            HASH_B,
        ],
    }
    assert result.registered_hashes == [
        HASH_A,
        HASH_B,
    ]
    assert result.registered_hash_count == 2
    assert (
        UPLOAD_VALUE
        not in result.model_dump_json()
    )


@pytest.mark.asyncio
async def test_empty_hash_set_is_rejected_before_http(
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

    with pytest.raises(
        CloudflarePagesAssetUploadError,
        match="hashes are missing",
    ):
        await CloudflareProviderClient().upsert_pages_asset_hashes(
            upload_session=upload_session(),
            content_hashes=[],
        )


@pytest.mark.asyncio
async def test_invalid_hash_is_rejected_before_http(
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

    with pytest.raises(
        CloudflarePagesAssetUploadError,
        match="hash is invalid",
    ):
        await CloudflareProviderClient().upsert_pages_asset_hashes(
            upload_session=upload_session(),
            content_hashes=["not-a-hash"],
        )


@pytest.mark.asyncio
async def test_hash_count_limit_is_rejected_before_http(
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

    hashes = [
        f"{index:032x}"
        for index in range(20_001)
    ]

    with pytest.raises(
        CloudflarePagesAssetUploadError,
        match="hash limit exceeded",
    ):
        await CloudflareProviderClient().upsert_pages_asset_hashes(
            upload_session=upload_session(),
            content_hashes=hashes,
        )


@pytest.mark.asyncio
async def test_invalid_success_envelope_is_rejected(
    monkeypatch,
) -> None:
    class InvalidClient:
        def __init__(self, **kwargs) -> None:
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
                    "success": False,
                    "result": None,
                },
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        InvalidClient,
    )

    with pytest.raises(
        CloudflarePagesAssetUploadError,
        match="invalid hash registration response",
    ):
        await CloudflareProviderClient().upsert_pages_asset_hashes(
            upload_session=upload_session(),
            content_hashes=[HASH_A],
        )


@pytest.mark.asyncio
async def test_invalid_json_response_is_rejected(
    monkeypatch,
) -> None:
    class InvalidJsonClient:
        def __init__(self, **kwargs) -> None:
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
                payload=None,
                json_error=ValueError(
                    "provider parse detail"
                ),
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        InvalidJsonClient,
    )

    with pytest.raises(
        CloudflarePagesAssetUploadError
    ) as captured:
        await CloudflareProviderClient().upsert_pages_asset_hashes(
            upload_session=upload_session(),
            content_hashes=[HASH_A],
        )

    message = str(captured.value)
    assert UPLOAD_VALUE not in message
    assert "provider parse detail" not in message


@pytest.mark.asyncio
async def test_hash_upsert_transport_failure_is_sanitized(
    monkeypatch,
) -> None:
    class FailingClient:
        def __init__(self, **kwargs) -> None:
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
            request = httpx.Request(
                "POST",
                url,
            )
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
        await CloudflareProviderClient().upsert_pages_asset_hashes(
            upload_session=upload_session(),
            content_hashes=[HASH_A],
        )

    message = str(captured.value)
    assert UPLOAD_VALUE not in message
    assert "provider transport detail" not in message


@pytest.mark.asyncio
async def test_hash_upsert_rejection_is_sanitized(
    monkeypatch,
) -> None:
    class RejectedClient:
        def __init__(self, **kwargs) -> None:
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
        await CloudflareProviderClient().upsert_pages_asset_hashes(
            upload_session=upload_session(),
            content_hashes=[HASH_A],
        )

    message = str(captured.value)
    assert UPLOAD_VALUE not in message
    assert "provider-secret-detail" not in message
