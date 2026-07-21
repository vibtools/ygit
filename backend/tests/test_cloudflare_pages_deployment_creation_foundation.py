from __future__ import annotations

import json

import httpx
import pytest

from backend.providers.cloudflare_provider import (
    client as cloudflare_client_module,
)
from backend.providers.cloudflare_provider.client import (
    CloudflareProviderClient,
)
from backend.providers.cloudflare_provider.errors import (
    CloudflarePagesDeploymentError,
    CloudflareProviderUnavailableError,
)
from backend.providers.cloudflare_provider.schemas import (
    CloudflarePagesArtifactFile,
    CloudflarePagesArtifactManifest,
)


ACCESS_VALUE = "pages-access-value-for-test"
HASH_A = "a" * 32
HASH_B = "b" * 32


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


def artifact_manifest() -> CloudflarePagesArtifactManifest:
    return CloudflarePagesArtifactManifest(
        output_directory_name="dist",
        file_count=2,
        total_bytes=7,
        files=[
            CloudflarePagesArtifactFile(
                relative_path="index.html",
                content_hash=HASH_A,
                size_bytes=4,
            ),
            CloudflarePagesArtifactFile(
                relative_path="assets/app.js",
                content_hash=HASH_B,
                size_bytes=3,
            ),
        ],
        manifest={
            "index.html": HASH_A,
            "assets/app.js": HASH_B,
        },
    )


def deployment_payload(
    *,
    environment: str = "production",
    aliases: list[str] | None = None,
) -> dict[str, object]:
    return {
        "success": True,
        "errors": [],
        "messages": [],
        "result": {
            "id": "deployment-1",
            "project_id": "project-1",
            "project_name": "ygit-demo",
            "environment": environment,
            "url": (
                "https://deployment-1."
                "ygit-demo.pages.dev"
            ),
            "aliases": aliases,
            "created_on": (
                "2026-07-21T08:30:00Z"
            ),
            "latest_stage": {
                "name": "deploy",
                "status": "active",
            },
            "deployment_trigger": {
                "type": "ad_hoc",
                "metadata": {
                    "branch": (
                        "main"
                        if environment
                        == "production"
                        else "feature/test"
                    ),
                    "commit_hash": "a" * 40,
                    "commit_message": (
                        "Deploy with YGIT"
                    ),
                    "commit_dirty": False,
                },
            },
        },
    }


@pytest.mark.asyncio
async def test_create_deployment_uses_multipart_manifest_and_metadata(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class DeploymentClient:
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
            files: dict[
                str,
                tuple[None, str],
            ],
        ) -> FakeResponse:
            captured["url"] = url
            captured["files"] = files
            return FakeResponse(
                status_code=200,
                payload=deployment_payload(
                    aliases=None,
                ),
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        DeploymentClient,
    )

    deployment = (
        await CloudflareProviderClient(
            timeout_seconds=8.5,
        ).create_pages_deployment(
            account_id="account/id",
            project_name="ygit demo",
            bearer_value=ACCESS_VALUE,
            branch="main",
            manifest=artifact_manifest(),
            commit_hash="A" * 40,
            commit_message="Deploy with YGIT",
            commit_dirty=False,
        )
    )

    assert captured["timeout"] == 8.5
    assert captured["headers"] == {
        "Authorization": (
            f"Bearer {ACCESS_VALUE}"
        ),
    }
    assert captured["url"] == (
        "https://api.cloudflare.com/client/v4/"
        "accounts/account%2Fid/pages/projects/"
        "ygit%20demo/deployments"
    )

    files = captured["files"]
    assert isinstance(files, dict)
    assert files["manifest"] == (
        None,
        json.dumps(
            {
                "/assets/app.js": HASH_B,
                "/index.html": HASH_A,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
    assert files["branch"] == (
        None,
        "main",
    )
    assert files["commit_hash"] == (
        None,
        "a" * 40,
    )
    assert files["commit_message"] == (
        None,
        "Deploy with YGIT",
    )
    assert files["commit_dirty"] == (
        None,
        "false",
    )
    assert files[
        "pages_build_output_dir"
    ] == (
        None,
        "dist",
    )
    assert deployment.deployment_id == (
        "deployment-1"
    )
    assert deployment.environment == (
        "production"
    )
    assert deployment.aliases == []
    assert deployment.stage_name == "deploy"
    assert deployment.stage_status == (
        "active"
    )


@pytest.mark.asyncio
async def test_commit_message_is_utf8_truncated(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class DeploymentClient:
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
            files: dict[
                str,
                tuple[None, str],
            ],
        ) -> FakeResponse:
            captured["files"] = files
            return FakeResponse(
                status_code=200,
                payload=deployment_payload(),
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        DeploymentClient,
    )

    await CloudflareProviderClient().create_pages_deployment(
        account_id="account-1",
        project_name="ygit-demo",
        bearer_value=ACCESS_VALUE,
        branch="main",
        manifest=artifact_manifest(),
        commit_message="é" * 300,
    )

    files = captured["files"]
    assert isinstance(files, dict)
    message = files["commit_message"][1]

    assert len(
        message.encode("utf-8")
    ) <= 384
    assert message.encode(
        "utf-8"
    ).decode("utf-8") == message


@pytest.mark.asyncio
async def test_inconsistent_manifest_is_rejected_before_http(
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

    manifest = artifact_manifest()
    manifest.total_bytes = 999

    with pytest.raises(
        CloudflarePagesDeploymentError,
        match="manifest is inconsistent",
    ):
        await CloudflareProviderClient().create_pages_deployment(
            account_id="account-1",
            project_name="ygit-demo",
            bearer_value=ACCESS_VALUE,
            branch="main",
            manifest=manifest,
        )


@pytest.mark.asyncio
async def test_invalid_manifest_path_is_rejected_before_http(
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

    manifest = CloudflarePagesArtifactManifest(
        output_directory_name="dist",
        file_count=1,
        total_bytes=1,
        files=[
            CloudflarePagesArtifactFile(
                relative_path="../escape.txt",
                content_hash=HASH_A,
                size_bytes=1,
            ),
        ],
        manifest={
            "../escape.txt": HASH_A,
        },
    )

    with pytest.raises(
        CloudflarePagesDeploymentError,
        match="manifest is invalid",
    ):
        await CloudflareProviderClient().create_pages_deployment(
            account_id="account-1",
            project_name="ygit-demo",
            bearer_value=ACCESS_VALUE,
            branch="main",
            manifest=manifest,
        )


def test_deployment_response_normalizes_aliases_and_stage() -> None:
    deployment = (
        CloudflareProviderClient
        ._pages_deployment_from_payload(
            deployment_payload(
                aliases=[
                    (
                        "https://ygit-demo."
                        "pages.dev"
                    ),
                    (
                        "https://www."
                        "example.test"
                    ),
                ],
            )
        )
    )

    assert deployment.aliases == [
        "https://www.example.test",
        "https://ygit-demo.pages.dev",
    ]
    assert deployment.created_on == (
        "2026-07-21T08:30:00Z"
    )
    assert deployment.branch == "main"
    assert deployment.commit_dirty is False


def test_preview_metadata_is_returned() -> None:
    deployment = (
        CloudflareProviderClient
        ._pages_deployment_from_payload(
            deployment_payload(
                environment="preview",
                aliases=[],
            )
        )
    )

    assert deployment.environment == "preview"
    assert deployment.branch == (
        "feature/test"
    )
    assert deployment.commit_hash == (
        "a" * 40
    )
    assert deployment.commit_message == (
        "Deploy with YGIT"
    )


@pytest.mark.asyncio
async def test_invalid_json_response_is_sanitized(
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
            files: dict[
                str,
                tuple[None, str],
            ],
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
        CloudflarePagesDeploymentError
    ) as captured:
        await CloudflareProviderClient().create_pages_deployment(
            account_id="account-1",
            project_name="ygit-demo",
            bearer_value=ACCESS_VALUE,
            branch="main",
            manifest=artifact_manifest(),
        )

    message = str(captured.value)

    assert ACCESS_VALUE not in message
    assert "provider parse detail" not in message


@pytest.mark.asyncio
async def test_deployment_transport_failure_is_sanitized(
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
            files: dict[
                str,
                tuple[None, str],
            ],
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
        await CloudflareProviderClient().create_pages_deployment(
            account_id="account-1",
            project_name="ygit-demo",
            bearer_value=ACCESS_VALUE,
            branch="main",
            manifest=artifact_manifest(),
        )

    message = str(captured.value)

    assert ACCESS_VALUE not in message
    assert "provider transport detail" not in message


@pytest.mark.asyncio
async def test_deployment_rejection_is_sanitized(
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
            files: dict[
                str,
                tuple[None, str],
            ],
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
        CloudflarePagesDeploymentError
    ) as captured:
        await CloudflareProviderClient().create_pages_deployment(
            account_id="account-1",
            project_name="ygit-demo",
            bearer_value=ACCESS_VALUE,
            branch="main",
            manifest=artifact_manifest(),
        )

    message = str(captured.value)

    assert ACCESS_VALUE not in message
    assert "provider-secret-detail" not in message


def test_incomplete_deployment_response_is_rejected() -> None:
    payload = deployment_payload()
    result = payload["result"]
    assert isinstance(result, dict)
    result["url"] = ""

    with pytest.raises(
        CloudflarePagesDeploymentError,
        match="incomplete deployment data",
    ):
        (
            CloudflareProviderClient
            ._pages_deployment_from_payload(
                payload
            )
        )
