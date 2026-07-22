from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = Path(
    "scripts/live_readiness.py"
)
SPEC = importlib.util.spec_from_file_location(
    "ygit_live_readiness",
    SCRIPT_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(
    SPEC
)
sys.modules[SPEC.name] = MODULE
try:
    SPEC.loader.exec_module(MODULE)
except Exception:
    sys.modules.pop(
        SPEC.name,
        None,
    )
    raise


def valid_environment(
    *,
    provider_mode: str = "disabled",
) -> dict[str, str]:
    return {
        "DATABASE_URL": (
            "postgresql+asyncpg://"
            "user:password@db:5432/ygit"
        ),
        "REDIS_URL": (
            "redis://redis:6379/0"
        ),
        "SESSION_SECRET": (
            "session-secret-value-123456"
        ),
        "GITHUB_APP_SLUG": (
            "ygit"
        ),
        "GITHUB_APP_ID": (
            "123456"
        ),
        "GITHUB_APP_PRIVATE_KEY": (
            "private-key-material-"
            "abcdefghijklmnopqrstuvwxyz-"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ-"
            "0123456789"
        ),
        "GITHUB_APP_WEBHOOK_ENABLED": (
            "false"
        ),
        "CLOUDFLARE_OAUTH_CLIENT_ID": (
            "cloudflare-client"
        ),
        "CLOUDFLARE_OAUTH_CLIENT_SECRET": (
            "cloudflare-secret-value-123456"
        ),
        "WORKER_PROVIDER_EXECUTION_MODE": (
            provider_mode
        ),
    }


def test_missing_environment_fails_closed(
) -> None:
    checks = MODULE.validate_environment(
        {},
        expected_provider_mode="disabled",
    )

    assert checks
    assert any(
        check.status == "FAIL"
        for check in checks
    )


def test_valid_disabled_environment_passes(
) -> None:
    checks = MODULE.validate_environment(
        valid_environment(),
        expected_provider_mode="disabled",
    )

    assert all(
        check.status == "PASS"
        for check in checks
    )


def test_provider_mode_mismatch_fails(
) -> None:
    checks = MODULE.validate_environment(
        valid_environment(
            provider_mode="disabled"
        ),
        expected_provider_mode="cloudflare",
    )

    mode_check = [
        check
        for check in checks
        if check.name
        == "provider_execution_mode"
    ][0]
    assert mode_check.status == "FAIL"


def test_secret_values_are_not_rendered(
) -> None:
    environment = valid_environment()
    checks = MODULE.validate_environment(
        environment,
        expected_provider_mode="disabled",
    )
    rendered = " ".join(
        check.details
        for check in checks
    )

    for name in (
        "SESSION_SECRET",
        "GITHUB_APP_PRIVATE_KEY",
        "CLOUDFLARE_OAUTH_CLIENT_SECRET",
    ):
        assert (
            environment[name]
            not in rendered
        )


def test_required_environment_uses_github_app_contract(
) -> None:
    assert set(MODULE.GITHUB_APP_REQUIRED_ENVIRONMENT) == {
        "GITHUB_APP_SLUG",
        "GITHUB_APP_ID",
        "GITHUB_APP_PRIVATE_KEY",
    }
    assert (
        "GITHUB_APP_WEBHOOK_SECRET"
        not in MODULE.REQUIRED_ENVIRONMENT
    )
    assert "GITHUB_OAUTH_CLIENT_ID" not in MODULE.REQUIRED_ENVIRONMENT
    assert "GITHUB_OAUTH_CLIENT_SECRET" not in MODULE.REQUIRED_ENVIRONMENT


def test_missing_github_app_private_key_fails(
) -> None:
    environment = valid_environment()
    environment.pop("GITHUB_APP_PRIVATE_KEY")
    checks = MODULE.validate_environment(environment, expected_provider_mode="disabled")
    assert any(
        check.name == "env:GITHUB_APP_PRIVATE_KEY" and check.status == "FAIL"
        for check in checks
    )


def test_legacy_github_oauth_variables_fail_closed(
) -> None:
    environment = valid_environment()
    environment["GITHUB_OAUTH_CLIENT_ID"] = "legacy-client"
    environment["GITHUB_OAUTH_CLIENT_SECRET"] = "legacy-secret-value-123456"
    checks = MODULE.validate_environment(environment, expected_provider_mode="disabled")
    forbidden = [
        check for check in checks if check.name.startswith("forbidden:GITHUB_OAUTH_")
    ]
    assert len(forbidden) == 2
    assert all(check.status == "FAIL" for check in forbidden)


def test_invalid_github_app_id_fails(
) -> None:
    environment = valid_environment()
    environment["GITHUB_APP_ID"] = "not-numeric"
    checks = MODULE.validate_environment(environment, expected_provider_mode="disabled")
    assert any(
        check.name == "github_app:id" and check.status == "FAIL"
        for check in checks
    )


def test_invalid_github_app_slug_fails(
) -> None:
    environment = valid_environment()
    environment["GITHUB_APP_SLUG"] = "Invalid GitHub App"
    checks = MODULE.validate_environment(environment, expected_provider_mode="disabled")
    assert any(
        check.name == "github_app:slug" and check.status == "FAIL"
        for check in checks
    )


def test_short_github_app_private_key_fails(
) -> None:
    environment = valid_environment()
    environment["GITHUB_APP_PRIVATE_KEY"] = "short"
    checks = MODULE.validate_environment(environment, expected_provider_mode="disabled")
    assert any(
        check.name == "github_app:private_key" and check.status == "FAIL"
        for check in checks
    )


def test_webhook_disabled_allows_missing_secret(
) -> None:
    environment = valid_environment()
    environment.pop(
        "GITHUB_APP_WEBHOOK_SECRET",
        None,
    )

    checks = MODULE.validate_environment(
        environment,
        expected_provider_mode="disabled",
    )

    assert all(
        check.status == "PASS"
        for check in checks
    )
    assert any(
        check.name == "github_app:webhook"
        and check.status == "PASS"
        for check in checks
    )


def test_webhook_enabled_requires_secret(
) -> None:
    environment = valid_environment()
    environment[
        "GITHUB_APP_WEBHOOK_ENABLED"
    ] = "true"

    checks = MODULE.validate_environment(
        environment,
        expected_provider_mode="disabled",
    )

    assert any(
        check.name
        == "env:GITHUB_APP_WEBHOOK_SECRET"
        and check.status == "FAIL"
        for check in checks
    )


def test_webhook_enabled_with_secret_passes_without_rendering_secret(
) -> None:
    environment = valid_environment()
    environment[
        "GITHUB_APP_WEBHOOK_ENABLED"
    ] = "true"
    environment[
        "GITHUB_APP_WEBHOOK_SECRET"
    ] = "github-webhook-secret-123456"

    checks = MODULE.validate_environment(
        environment,
        expected_provider_mode="disabled",
    )
    rendered = " ".join(
        check.details
        for check in checks
    )

    assert all(
        check.status == "PASS"
        for check in checks
    )
    assert (
        environment[
            "GITHUB_APP_WEBHOOK_SECRET"
        ]
        not in rendered
    )


def test_invalid_webhook_enabled_value_fails(
) -> None:
    environment = valid_environment()
    environment[
        "GITHUB_APP_WEBHOOK_ENABLED"
    ] = "sometimes"

    checks = MODULE.validate_environment(
        environment,
        expected_provider_mode="disabled",
    )

    assert any(
        check.name
        == "github_app:webhook_enabled"
        and check.status == "FAIL"
        for check in checks
    )


def test_database_url_normalization(
) -> None:
    assert (
        MODULE.normalize_async_database_url(
            "postgresql://u:p@db/ygit"
        )
        == (
            "postgresql+asyncpg://"
            "u:p@db/ygit"
        )
    )


def test_public_health_status_contract(
) -> None:
    result = MODULE.evaluate_http_status(
        route="/api/v1/platform/health",
        status_code=200,
    )

    assert result.status == "PASS"


def test_protected_shell_status_contract(
) -> None:
    for status_code in (
        401,
        403,
    ):
        result = (
            MODULE.evaluate_http_status(
                route="/dashboard",
                status_code=status_code,
            )
        )
        assert result.status == "PASS"


def test_readiness_report_never_claims_live_provider_execution(
) -> None:
    report = MODULE.build_report(
        mode="pre-redeploy",
        checks=[
            MODULE.CheckResult(
                name="example",
                status="PASS",
                details="ready",
            )
        ],
    )

    assert report.overall_status == "PASS"
    assert (
        report.live_provider_execution
        is False
    )
