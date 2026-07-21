from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from backend.engines.deploy_engine.errors import (
    DeploymentCloudflareNotConnectedError,
    DeploymentProjectNotReadyError,
)
from backend.engines.deploy_engine.internal.service import (
    DeployInternalService,
)


GITHUB_REFERENCE = (
    "github_app_installation:installation-1"
)
CLOUDFLARE_REFERENCE = (
    "cloudflare_oauth_account:account-1"
)


def service() -> DeployInternalService:
    return object.__new__(DeployInternalService)


def github_account() -> SimpleNamespace:
    return SimpleNamespace(
        provider="github",
        token_secret_ref=GITHUB_REFERENCE,
        provider_account_id="installation-1",
        provider_account_name="Vib Tools",
        access_token="must-not-propagate",
    )


def cloudflare_account(
    *,
    account_id: str | None = "cf-account-1",
) -> SimpleNamespace:
    return SimpleNamespace(
        provider="cloudflare",
        token_secret_ref=CLOUDFLARE_REFERENCE,
        provider_account_id=account_id,
        provider_account_name="Primary Account",
        access_token="must-not-propagate",
        refresh_token="must-not-propagate",
    )


def test_provider_configuration_contains_runtime_identifiers(
) -> None:
    configuration = (
        service()._provider_reference_configuration(
            github_account(),
            cloudflare_account(),
            cloudflare_project_name=(
                " Portfolio-Site "
            ),
        )
    )

    assert configuration == {
        "github_token_ref": {
            "provider": "github",
            "token_secret_ref": GITHUB_REFERENCE,
            "account_name": "Vib Tools",
        },
        "cloudflare_token_ref": {
            "provider": "cloudflare",
            "token_secret_ref": CLOUDFLARE_REFERENCE,
            "account_id": "cf-account-1",
            "account_name": "Primary Account",
        },
        "cloudflare_project_name": "portfolio-site",
    }


def test_cloudflare_account_id_is_required(
) -> None:
    with pytest.raises(
        DeploymentCloudflareNotConnectedError
    ):
        service()._provider_reference_configuration(
            github_account(),
            cloudflare_account(account_id=None),
            cloudflare_project_name="portfolio-site",
        )


def test_cloudflare_account_id_control_character_is_rejected(
) -> None:
    with pytest.raises(
        DeploymentCloudflareNotConnectedError
    ):
        service()._provider_reference_configuration(
            github_account(),
            cloudflare_account(
                account_id="account\nunsafe"
            ),
            cloudflare_project_name="portfolio-site",
        )


@pytest.mark.parametrize(
    "project_name",
    [
        "",
        "   ",
        "portfolio\nunsafe",
        "portfolio\runsafe",
        "portfolio\x00unsafe",
    ],
)
def test_invalid_cloudflare_project_name_is_rejected(
    project_name: str,
) -> None:
    with pytest.raises(
        DeploymentProjectNotReadyError,
        match="Project slug is invalid",
    ):
        service()._provider_reference_configuration(
            github_account(),
            cloudflare_account(),
            cloudflare_project_name=project_name,
        )


def test_configuration_excludes_resolved_credentials(
) -> None:
    configuration = (
        service()._provider_reference_configuration(
            github_account(),
            cloudflare_account(),
            cloudflare_project_name="portfolio-site",
        )
    )
    serialized = json.dumps(
        configuration,
        sort_keys=True,
    )

    assert "must-not-propagate" not in serialized
    assert "access_token" not in serialized
    assert "refresh_token" not in serialized
    assert "Bearer " not in serialized


def test_github_reference_does_not_gain_cloudflare_account_id(
) -> None:
    configuration = (
        service()._provider_reference_configuration(
            github_account(),
            cloudflare_account(),
            cloudflare_project_name="portfolio-site",
        )
    )

    assert (
        "account_id"
        not in configuration["github_token_ref"]
    )
