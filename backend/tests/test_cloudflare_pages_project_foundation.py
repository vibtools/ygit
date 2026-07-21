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
    CloudflarePagesProjectError,
    CloudflareProviderUnavailableError,
)


class FakeResponse:
    def __init__(self, *, status_code: int, payload: object) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> object:
        return self._payload


def project_payload(*, name: str = "ygit-demo") -> dict[str, object]:
    return {
        "success": True,
        "errors": [],
        "messages": [],
        "result": {
            "id": "project-id-1",
            "name": name,
            "production_branch": "main",
            "subdomain": f"{name}.pages.dev",
        },
    }


@pytest.mark.asyncio
async def test_get_pages_project_uses_bearer_header(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class SuccessClient:
        def __init__(self, *, timeout: float, headers: dict[str, str]) -> None:
            captured["timeout"] = timeout
            captured["headers"] = dict(headers)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def get(self, url: str) -> FakeResponse:
            captured["url"] = url
            return FakeResponse(status_code=200, payload=project_payload())

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        SuccessClient,
    )

    provider = CloudflareProviderClient(timeout_seconds=8.5)
    project = await provider.get_pages_project(
        account_id="account/id",
        project_name="ygit demo",
        bearer_value="pages-access-value-for-test",
    )

    assert project is not None
    assert project.project_id == "project-id-1"
    assert captured["timeout"] == 8.5
    assert captured["headers"] == {
        "Authorization": "Bearer pages-access-value-for-test",
    }
    assert captured["url"] == (
        "https://api.cloudflare.com/client/v4/"
        "accounts/account%2Fid/pages/projects/ygit%20demo"
    )


@pytest.mark.asyncio
async def test_ensure_pages_project_returns_existing_project(monkeypatch) -> None:
    calls: list[str] = []

    class ExistingClient:
        def __init__(self, *, timeout: float, headers: dict[str, str]) -> None:
            self.timeout = timeout
            self.headers = headers

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def get(self, url: str) -> FakeResponse:
            calls.append("get")
            return FakeResponse(status_code=200, payload=project_payload())

        async def post(self, url: str, *, json: dict[str, str]) -> FakeResponse:
            calls.append("post")
            raise AssertionError("existing project must not be recreated")

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        ExistingClient,
    )

    provider = CloudflareProviderClient()
    project = await provider.ensure_pages_project(
        account_id="account-1",
        project_name="ygit-demo",
        production_branch="main",
        bearer_value="pages-access-value-for-test",
    )

    assert project.project_name == "ygit-demo"
    assert calls == ["get"]


@pytest.mark.asyncio
async def test_ensure_pages_project_creates_missing_project(monkeypatch) -> None:
    captured: dict[str, object] = {}
    calls: list[str] = []

    class MissingThenCreateClient:
        def __init__(self, *, timeout: float, headers: dict[str, str]) -> None:
            captured["headers"] = dict(headers)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def get(self, url: str) -> FakeResponse:
            calls.append("get")
            return FakeResponse(
                status_code=404,
                payload={"success": False, "result": None},
            )

        async def post(self, url: str, *, json: dict[str, str]) -> FakeResponse:
            calls.append("post")
            captured["url"] = url
            captured["json"] = dict(json)
            return FakeResponse(status_code=200, payload=project_payload())

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        MissingThenCreateClient,
    )

    provider = CloudflareProviderClient()
    project = await provider.ensure_pages_project(
        account_id="account-1",
        project_name="ygit-demo",
        production_branch="main",
        bearer_value="pages-access-value-for-test",
    )

    assert project.project_id == "project-id-1"
    assert calls == ["get", "post"]
    assert captured["url"] == (
        "https://api.cloudflare.com/client/v4/"
        "accounts/account-1/pages/projects"
    )
    assert captured["json"] == {
        "name": "ygit-demo",
        "production_branch": "main",
    }


@pytest.mark.asyncio
async def test_pages_project_maps_transport_failure(monkeypatch) -> None:
    class FailingClient:
        def __init__(self, *, timeout: float, headers: dict[str, str]) -> None:
            self.timeout = timeout
            self.headers = headers

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def get(self, url: str) -> FakeResponse:
            request = httpx.Request("GET", url)
            raise httpx.ConnectError("provider unavailable", request=request)

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        FailingClient,
    )

    provider = CloudflareProviderClient()

    with pytest.raises(CloudflareProviderUnavailableError):
        await provider.get_pages_project(
            account_id="account-1",
            project_name="ygit-demo",
            bearer_value="pages-access-value-for-test",
        )


@pytest.mark.asyncio
async def test_pages_project_rejection_is_sanitized(monkeypatch) -> None:
    class RejectedClient:
        def __init__(self, *, timeout: float, headers: dict[str, str]) -> None:
            self.timeout = timeout
            self.headers = headers

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def post(self, url: str, *, json: dict[str, str]) -> FakeResponse:
            return FakeResponse(
                status_code=403,
                payload={
                    "errors": [{"message": "provider-secret-detail"}],
                },
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        RejectedClient,
    )

    provider = CloudflareProviderClient()

    with pytest.raises(CloudflarePagesProjectError) as captured:
        await provider.create_pages_project(
            account_id="account-1",
            project_name="ygit-demo",
            production_branch="main",
            bearer_value="pages-access-value-for-test",
        )

    message = str(captured.value)
    assert "provider-secret-detail" not in message
    assert "pages-access-value-for-test" not in message


@pytest.mark.asyncio
async def test_pages_project_rejects_incomplete_response(monkeypatch) -> None:
    class InvalidResponseClient:
        def __init__(self, *, timeout: float, headers: dict[str, str]) -> None:
            self.timeout = timeout
            self.headers = headers

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def get(self, url: str) -> FakeResponse:
            return FakeResponse(
                status_code=200,
                payload={
                    "success": True,
                    "result": {"id": "", "name": "ygit-demo"},
                },
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        InvalidResponseClient,
    )

    provider = CloudflareProviderClient()

    with pytest.raises(CloudflarePagesProjectError):
        await provider.get_pages_project(
            account_id="account-1",
            project_name="ygit-demo",
            bearer_value="pages-access-value-for-test",
        )
