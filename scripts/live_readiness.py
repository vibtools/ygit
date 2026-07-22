from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import ssl
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse


CORE_REQUIRED_ENVIRONMENT = (
    "DATABASE_URL",
    "REDIS_URL",
    "SESSION_SECRET",
    "CLOUDFLARE_OAUTH_CLIENT_ID",
    "CLOUDFLARE_OAUTH_CLIENT_SECRET",
    "WORKER_PROVIDER_EXECUTION_MODE",
)

GITHUB_APP_REQUIRED_ENVIRONMENT = (
    "GITHUB_APP_SLUG",
    "GITHUB_APP_ID",
    "GITHUB_APP_PRIVATE_KEY",
    "GITHUB_APP_WEBHOOK_SECRET",
)

REQUIRED_ENVIRONMENT = (
    CORE_REQUIRED_ENVIRONMENT
    + GITHUB_APP_REQUIRED_ENVIRONMENT
)

FORBIDDEN_GITHUB_OAUTH_ENVIRONMENT = (
    "GITHUB_OAUTH_CLIENT_ID",
    "GITHUB_OAUTH_CLIENT_SECRET",
)

SECRET_ENVIRONMENT = {
    "SESSION_SECRET",
    "GITHUB_APP_PRIVATE_KEY",
    "GITHUB_APP_WEBHOOK_SECRET",
    "CLOUDFLARE_OAUTH_CLIENT_SECRET",
}

SUPPORTED_PROVIDER_MODES = {
    "disabled",
    "cloudflare",
}


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    details: str


@dataclass(frozen=True)
class ReadinessReport:
    mode: str
    overall_status: str
    checks: tuple[CheckResult, ...]
    live_provider_execution: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "overall_status": self.overall_status,
            "checks": [
                asdict(check)
                for check in self.checks
            ],
            "live_provider_execution": (
                self.live_provider_execution
            ),
        }


def _present(value: str | None) -> bool:
    return bool(
        str(value or "").strip()
    )


def _safe_url_label(value: str) -> str:
    parsed = urlparse(value)
    scheme = parsed.scheme or "unknown"
    host = parsed.hostname or "unknown"
    port = (
        f":{parsed.port}"
        if parsed.port is not None
        else ""
    )
    return f"{scheme}://{host}{port}"


def validate_environment(
    environment: Mapping[str, str],
    *,
    expected_provider_mode: str,
) -> list[CheckResult]:
    checks: list[CheckResult] = []

    for name in REQUIRED_ENVIRONMENT:
        value = environment.get(name)

        if not _present(value):
            checks.append(
                CheckResult(
                    name=f"env:{name}",
                    status="FAIL",
                    details="required value is missing",
                )
            )
            continue

        if (
            name in SECRET_ENVIRONMENT
            and len(str(value)) < 16
        ):
            checks.append(
                CheckResult(
                    name=f"env:{name}",
                    status="FAIL",
                    details=(
                        "secret is present but shorter "
                        "than the minimum readiness threshold"
                    ),
                )
            )
            continue

        checks.append(
            CheckResult(
                name=f"env:{name}",
                status="PASS",
                details="configured",
            )
        )

    for name in FORBIDDEN_GITHUB_OAUTH_ENVIRONMENT:
        configured = _present(environment.get(name))
        checks.append(
            CheckResult(
                name=f"forbidden:{name}",
                status=("FAIL" if configured else "PASS"),
                details=(
                    "legacy GitHub OAuth variable must not be configured; YGIT uses GitHub App integration"
                    if configured
                    else "not configured; GitHub App architecture preserved"
                ),
            )
        )

    github_app_slug = str(environment.get("GITHUB_APP_SLUG", "")).strip()
    slug_valid = bool(
        re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", github_app_slug)
    )
    checks.append(
        CheckResult(
            name="github_app:slug",
            status=("PASS" if slug_valid else "FAIL"),
            details=("valid GitHub App slug" if slug_valid else "GitHub App slug is invalid"),
        )
    )

    github_app_id = str(environment.get("GITHUB_APP_ID", "")).strip()
    app_id_valid = github_app_id.isdigit() and int(github_app_id) > 0
    checks.append(
        CheckResult(
            name="github_app:id",
            status=("PASS" if app_id_valid else "FAIL"),
            details=(
                "valid GitHub App identifier"
                if app_id_valid
                else "GitHub App identifier is invalid"
            ),
        )
    )

    private_key = str(environment.get("GITHUB_APP_PRIVATE_KEY", ""))
    private_key_valid = len(private_key.strip()) >= 64
    checks.append(
        CheckResult(
            name="github_app:private_key",
            status=("PASS" if private_key_valid else "FAIL"),
            details=(
                "GitHub App private key is configured"
                if private_key_valid
                else "GitHub App private key is invalid"
            ),
        )
    )

    configured_mode = str(
        environment.get(
            "WORKER_PROVIDER_EXECUTION_MODE",
            "",
        )
    ).strip().lower()

    if configured_mode not in (
        SUPPORTED_PROVIDER_MODES
    ):
        checks.append(
            CheckResult(
                name="provider_execution_mode",
                status="FAIL",
                details="unsupported provider mode",
            )
        )
    elif configured_mode != (
        expected_provider_mode
    ):
        checks.append(
            CheckResult(
                name="provider_execution_mode",
                status="FAIL",
                details=(
                    "configured mode does not match "
                    "the explicitly expected mode"
                ),
            )
        )
    else:
        checks.append(
            CheckResult(
                name="provider_execution_mode",
                status="PASS",
                details=(
                    "mode matches explicit expectation"
                ),
            )
        )

    return checks


def normalize_async_database_url(
    value: str,
) -> str:
    normalized = str(value).strip()

    if normalized.startswith(
        "postgresql://"
    ):
        return (
            "postgresql+asyncpg://"
            + normalized[
                len("postgresql://"):
            ]
        )

    if normalized.startswith(
        "postgres://"
    ):
        return (
            "postgresql+asyncpg://"
            + normalized[
                len("postgres://"):
            ]
        )

    return normalized


async def check_database(
    database_url: str,
    *,
    timeout_seconds: float,
) -> CheckResult:
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import (
            create_async_engine,
        )
    except Exception:
        return CheckResult(
            name="postgresql",
            status="FAIL",
            details=(
                "SQLAlchemy async runtime is unavailable"
            ),
        )

    safe_label = _safe_url_label(
        database_url
    )
    engine = create_async_engine(
        normalize_async_database_url(
            database_url
        ),
        pool_pre_ping=True,
    )

    try:
        async with asyncio.timeout(
            timeout_seconds
        ):
            async with engine.connect() as connection:
                value = await connection.scalar(
                    text("SELECT 1")
                )

        if int(value or 0) != 1:
            return CheckResult(
                name="postgresql",
                status="FAIL",
                details=(
                    f"{safe_label} returned an "
                    "unexpected probe result"
                ),
            )

        return CheckResult(
            name="postgresql",
            status="PASS",
            details=(
                f"{safe_label} accepted SELECT 1"
            ),
        )
    except Exception as exc:
        return CheckResult(
            name="postgresql",
            status="FAIL",
            details=(
                f"{safe_label} probe failed "
                f"({type(exc).__name__})"
            ),
        )
    finally:
        await engine.dispose()


async def check_redis(
    redis_url: str,
    *,
    timeout_seconds: float,
) -> CheckResult:
    try:
        from redis.asyncio import (
            Redis,
        )
    except Exception:
        return CheckResult(
            name="redis",
            status="FAIL",
            details=(
                "redis asyncio runtime is unavailable"
            ),
        )

    safe_label = _safe_url_label(redis_url)
    client = Redis.from_url(
        redis_url,
        decode_responses=True,
    )

    try:
        async with asyncio.timeout(
            timeout_seconds
        ):
            pong = await client.ping()

        if pong is not True:
            return CheckResult(
                name="redis",
                status="FAIL",
                details=(
                    f"{safe_label} returned an "
                    "unexpected ping result"
                ),
            )

        return CheckResult(
            name="redis",
            status="PASS",
            details=(
                f"{safe_label} accepted PING"
            ),
        )
    except Exception as exc:
        return CheckResult(
            name="redis",
            status="FAIL",
            details=(
                f"{safe_label} probe failed "
                f"({type(exc).__name__})"
            ),
        )
    finally:
        close = getattr(
            client,
            "aclose",
            None,
        )

        if close is None:
            close = getattr(
                client,
                "close",
                None,
            )

        if close is not None:
            result = close()

            if asyncio.iscoroutine(result):
                await result


def _request_status(
    url: str,
    *,
    timeout_seconds: float,
) -> int:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": (
                "YGIT-Live-Readiness/1.0"
            ),
        },
    )
    context = ssl.create_default_context()

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout_seconds,
            context=context,
        ) as response:
            return int(response.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)


def evaluate_http_status(
    *,
    route: str,
    status_code: int,
) -> CheckResult:
    if route in {
        "/api/v1/platform/version",
        "/api/v1/platform/health",
    }:
        expected = {200}
    else:
        expected = {
            401,
            403,
        }

    if status_code in expected:
        return CheckResult(
            name=f"http:{route}",
            status="PASS",
            details=(
                f"returned expected HTTP "
                f"{status_code}"
            ),
        )

    return CheckResult(
        name=f"http:{route}",
        status="FAIL",
        details=(
            f"returned unexpected HTTP "
            f"{status_code}"
        ),
    )


async def check_http_runtime(
    base_url: str,
    *,
    timeout_seconds: float,
) -> list[CheckResult]:
    normalized = base_url.rstrip("/")
    routes = (
        "/api/v1/platform/version",
        "/api/v1/platform/health",
        "/dashboard",
        "/admin",
    )
    checks: list[CheckResult] = []

    for route in routes:
        try:
            status = await asyncio.to_thread(
                _request_status,
                normalized + route,
                timeout_seconds=timeout_seconds,
            )
            checks.append(
                evaluate_http_status(
                    route=route,
                    status_code=status,
                )
            )
        except Exception as exc:
            checks.append(
                CheckResult(
                    name=f"http:{route}",
                    status="FAIL",
                    details=(
                        "request failed "
                        f"({type(exc).__name__})"
                    ),
                )
            )

    return checks


def build_report(
    *,
    mode: str,
    checks: list[CheckResult],
) -> ReadinessReport:
    overall = (
        "PASS"
        if checks
        and all(
            check.status == "PASS"
            for check in checks
        )
        else "FAIL"
    )
    return ReadinessReport(
        mode=mode,
        overall_status=overall,
        checks=tuple(checks),
        live_provider_execution=False,
    )


async def run_readiness(
    *,
    mode: str,
    environment: Mapping[str, str],
    expected_provider_mode: str,
    base_url: str | None,
    check_db: bool,
    check_redis_runtime: bool,
    timeout_seconds: float,
) -> ReadinessReport:
    checks = validate_environment(
        environment,
        expected_provider_mode=(
            expected_provider_mode
        ),
    )

    database_url = str(
        environment.get(
            "DATABASE_URL",
            "",
        )
    )
    redis_url = str(
        environment.get(
            "REDIS_URL",
            "",
        )
    )

    if check_db and _present(database_url):
        checks.append(
            await check_database(
                database_url,
                timeout_seconds=timeout_seconds,
            )
        )

    if (
        check_redis_runtime
        and _present(redis_url)
    ):
        checks.append(
            await check_redis(
                redis_url,
                timeout_seconds=timeout_seconds,
            )
        )

    if mode == "post-redeploy":
        if not _present(base_url):
            checks.append(
                CheckResult(
                    name="http:base_url",
                    status="FAIL",
                    details=(
                        "base URL is required "
                        "for post-redeploy mode"
                    ),
                )
            )
        else:
            checks.extend(
                await check_http_runtime(
                    str(base_url),
                    timeout_seconds=(
                        timeout_seconds
                    ),
                )
            )

    return build_report(
        mode=mode,
        checks=checks,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate YGIT production "
            "configuration and runtime readiness "
            "without executing a provider."
        )
    )
    parser.add_argument(
        "--mode",
        choices=(
            "pre-redeploy",
            "post-redeploy",
        ),
        required=True,
    )
    parser.add_argument(
        "--expected-provider-mode",
        choices=tuple(
            sorted(
                SUPPORTED_PROVIDER_MODES
            )
        ),
        default="disabled",
    )
    parser.add_argument(
        "--base-url",
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
    )
    parser.add_argument(
        "--skip-redis",
        action="store_true",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
    )
    parser.add_argument(
        "--json-output",
        type=Path,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = asyncio.run(
        run_readiness(
            mode=args.mode,
            environment=os.environ,
            expected_provider_mode=(
                args.expected_provider_mode
            ),
            base_url=args.base_url,
            check_db=not args.skip_db,
            check_redis_runtime=(
                not args.skip_redis
            ),
            timeout_seconds=max(
                1.0,
                args.timeout_seconds,
            ),
        )
    )
    rendered = json.dumps(
        report.to_dict(),
        indent=2,
        ensure_ascii=False,
    )
    print(rendered)

    if args.json_output is not None:
        args.json_output.write_text(
            rendered + "\n",
            encoding="utf-8",
        )

    return (
        0
        if report.overall_status
        == "PASS"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
