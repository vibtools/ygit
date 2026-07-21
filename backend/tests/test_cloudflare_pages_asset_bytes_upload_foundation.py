from __future__ import annotations

import base64
from pathlib import Path

import httpx
import pytest

from backend.providers.cloudflare_provider import (
    client as cloudflare_client_module,
)
from backend.providers.cloudflare_provider.artifacts import (
    CloudflarePagesArtifactBuilder,
    CloudflarePagesAssetUploadBatch,
    CloudflarePagesAssetUploadItem,
)
from backend.providers.cloudflare_provider.client import (
    CloudflareProviderClient,
)
from backend.providers.cloudflare_provider.errors import (
    CloudflarePagesArtifactError,
    CloudflarePagesAssetUploadError,
    CloudflareProviderUnavailableError,
)
from backend.providers.cloudflare_provider.schemas import (
    CloudflarePagesUploadToken,
)


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


def upload_session() -> CloudflarePagesUploadToken:
    session_fields = {
        "upload_token": UPLOAD_VALUE,
    }
    return CloudflarePagesUploadToken(
        **session_fields
    )


def build_manifest(
    tmp_path: Path,
    files: dict[str, bytes],
):
    output = tmp_path / "dist"

    for relative_path, value in files.items():
        path = output.joinpath(
            *relative_path.split("/")
        )
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_bytes(value)

    manifest = (
        CloudflarePagesArtifactBuilder()
        .build(output)
    )
    return output, manifest


def test_upload_batch_payload_is_base64_and_typed(
    tmp_path: Path,
) -> None:
    html = b"<h1>YGIT</h1>"
    binary = b"\x00\x01\x02"
    output, manifest = build_manifest(
        tmp_path,
        {
            "index.html": html,
            "asset.bin": binary,
        },
    )

    batches = list(
        CloudflarePagesArtifactBuilder()
        .iter_upload_batches(
            output_directory=output,
            manifest=manifest,
            missing_hashes=sorted(
                set(manifest.manifest.values())
            ),
        )
    )

    assert len(batches) == 1
    payload = [
        item.api_payload()
        for item in batches[0].items
    ]
    payload_by_hash = {
        item["key"]: item
        for item in payload
    }

    html_hash = manifest.manifest[
        "index.html"
    ]
    binary_hash = manifest.manifest[
        "asset.bin"
    ]

    assert payload_by_hash[html_hash] == {
        "key": html_hash,
        "value": (
            base64.b64encode(html)
            .decode("ascii")
        ),
        "metadata": {
            "contentType": "text/html",
        },
        "base64": True,
    }
    assert payload_by_hash[binary_hash] == {
        "key": binary_hash,
        "value": (
            base64.b64encode(binary)
            .decode("ascii")
        ),
        "metadata": {
            "contentType": (
                "application/octet-stream"
            ),
        },
        "base64": True,
    }


def test_upload_batches_are_deterministic_and_bounded(
    tmp_path: Path,
) -> None:
    output, manifest = build_manifest(
        tmp_path,
        {
            "a.txt": b"aaaa",
            "b.txt": b"bbb",
            "c.txt": b"cc",
        },
    )

    batches = list(
        CloudflarePagesArtifactBuilder()
        .iter_upload_batches(
            output_directory=output,
            manifest=manifest,
            missing_hashes=list(
                manifest.manifest.values()
            ),
            batch_max_bytes=5,
            batch_max_files=2,
        )
    )

    assert [
        batch.total_bytes
        for batch in batches
    ] == [4, 5]
    assert all(
        len(batch.items) <= 2
        for batch in batches
    )


def test_duplicate_content_hash_uploads_once(
    tmp_path: Path,
) -> None:
    value = b"same-content"
    output, manifest = build_manifest(
        tmp_path,
        {
            "a.txt": value,
            "b.txt": value,
        },
    )
    shared_hash = manifest.manifest[
        "a.txt"
    ]

    batches = list(
        CloudflarePagesArtifactBuilder()
        .iter_upload_batches(
            output_directory=output,
            manifest=manifest,
            missing_hashes=[shared_hash],
        )
    )

    assert len(batches) == 1
    assert len(batches[0].items) == 1
    assert (
        batches[0].items[0].content_hash
        == shared_hash
    )


def test_foreign_missing_hash_is_rejected(
    tmp_path: Path,
) -> None:
    output, manifest = build_manifest(
        tmp_path,
        {
            "index.html": b"content",
        },
    )

    with pytest.raises(
        CloudflarePagesArtifactError,
        match="not present",
    ):
        list(
            CloudflarePagesArtifactBuilder()
            .iter_upload_batches(
                output_directory=output,
                manifest=manifest,
                missing_hashes=["f" * 32],
            )
        )


def test_changed_file_is_rejected_before_encoding(
    tmp_path: Path,
) -> None:
    output, manifest = build_manifest(
        tmp_path,
        {
            "index.html": b"before",
        },
    )
    (
        output
        / "index.html"
    ).write_bytes(b"after")

    with pytest.raises(
        CloudflarePagesArtifactError,
        match=(
            "changed after manifest creation"
            "|no longer matches"
        ),
    ):
        list(
            CloudflarePagesArtifactBuilder()
            .iter_upload_batches(
                output_directory=output,
                manifest=manifest,
                missing_hashes=[
                    manifest.manifest[
                        "index.html"
                    ]
                ],
            )
        )


@pytest.mark.asyncio
async def test_upload_batch_uses_upload_jwt_and_endpoint(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    item = CloudflarePagesAssetUploadItem(
        content_hash="a" * 32,
        content_type="text/plain",
        encoded_value="eWdpdA==",
        size_bytes=4,
    )
    batch = CloudflarePagesAssetUploadBatch(
        items=(item,),
        total_bytes=4,
    )

    class UploadClient:
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
            json: list[dict[str, object]],
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
        UploadClient,
    )

    result = (
        await CloudflareProviderClient(
            timeout_seconds=6.5,
        ).upload_pages_asset_batch(
            upload_session=upload_session(),
            batch=batch,
        )
    )

    assert captured["timeout"] == 6.5
    assert captured["headers"] == {
        "Authorization": (
            f"Bearer {UPLOAD_VALUE}"
        ),
        "Content-Type": "application/json",
    }
    assert captured["url"] == (
        "https://api.cloudflare.com/client/v4/"
        "pages/assets/upload"
    )
    assert captured["json"] == [
        item.api_payload()
    ]
    assert result.uploaded_hashes == [
        "a" * 32
    ]
    assert result.uploaded_file_count == 1
    assert result.uploaded_bytes == 4


@pytest.mark.asyncio
async def test_upload_result_excludes_asset_bytes(
    monkeypatch,
) -> None:
    encoded_value = "cHJpdmF0ZS1wYWdlLWJvZHk="
    item = CloudflarePagesAssetUploadItem(
        content_hash="b" * 32,
        content_type="text/html",
        encoded_value=encoded_value,
        size_bytes=17,
    )
    batch = CloudflarePagesAssetUploadBatch(
        items=(item,),
        total_bytes=17,
    )

    class SuccessClient:
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
            json: list[dict[str, object]],
        ) -> FakeResponse:
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
        SuccessClient,
    )

    result = (
        await CloudflareProviderClient()
        .upload_pages_asset_batch(
            upload_session=upload_session(),
            batch=batch,
        )
    )
    serialized = result.model_dump_json()

    assert encoded_value not in serialized
    assert UPLOAD_VALUE not in serialized


@pytest.mark.asyncio
async def test_empty_upload_batch_is_rejected_before_http(
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
        match="batch is empty",
    ):
        await CloudflareProviderClient().upload_pages_asset_batch(
            upload_session=upload_session(),
            batch=CloudflarePagesAssetUploadBatch(
                items=(),
                total_bytes=0,
            ),
        )


@pytest.mark.asyncio
async def test_asset_upload_transport_failure_is_sanitized(
    monkeypatch,
) -> None:
    item = CloudflarePagesAssetUploadItem(
        content_hash="c" * 32,
        content_type="text/plain",
        encoded_value="eA==",
        size_bytes=1,
    )
    batch = CloudflarePagesAssetUploadBatch(
        items=(item,),
        total_bytes=1,
    )

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
            json: list[dict[str, object]],
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
        await CloudflareProviderClient().upload_pages_asset_batch(
            upload_session=upload_session(),
            batch=batch,
        )

    message = str(captured.value)

    assert UPLOAD_VALUE not in message
    assert "provider transport detail" not in message


@pytest.mark.asyncio
async def test_asset_upload_rejection_is_sanitized(
    monkeypatch,
) -> None:
    item = CloudflarePagesAssetUploadItem(
        content_hash="d" * 32,
        content_type="text/plain",
        encoded_value="eA==",
        size_bytes=1,
    )
    batch = CloudflarePagesAssetUploadBatch(
        items=(item,),
        total_bytes=1,
    )

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
            json: list[dict[str, object]],
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
        await CloudflareProviderClient().upload_pages_asset_batch(
            upload_session=upload_session(),
            batch=batch,
        )

    message = str(captured.value)

    assert UPLOAD_VALUE not in message
    assert "provider-secret-detail" not in message
