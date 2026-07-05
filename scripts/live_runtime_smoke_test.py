#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "LIVE_RUNTIME_SMOKE_TEST_REPORT.json"

PUBLIC_ENDPOINTS = [
    ("GET", "/api/v1/platform/health", "json_success"),
    ("GET", "/api/v1/platform/version", "json_success"),
    ("GET", "/dashboard", "contains:YGIT Dashboard"),
    ("GET", "/admin", "contains:Platform Operations Console"),
]

AUTHENTICATED_ENDPOINTS = [
    ("GET", "/api/v1/me", "json_any"),
    ("GET", "/api/v1/platform/status", "json_any"),
    ("GET", "/api/v1/platform/feature-flags", "json_any"),
    ("GET", "/api/v1/projects", "json_any"),
    ("GET", "/api/v1/notifications/unread-count", "json_any"),
]

ADMIN_ENDPOINTS = [
    ("GET", "/api/v1/admin/overview", "json_any"),
    ("GET", "/api/v1/admin/platform/health", "json_any"),
    ("GET", "/api/v1/admin/queue/status", "json_any"),
    ("GET", "/api/v1/admin/system-monitoring", "json_any"),
    ("GET", "/api/v1/admin/deployments", "json_any"),
    ("GET", "/api/v1/admin/users", "json_any"),
    ("GET", "/api/v1/admin/audit-logs", "json_any"),
    ("GET", "/api/v1/admin/settings", "json_any"),
    ("GET", "/api/v1/admin/manifest", "json_any"),
]

FORBIDDEN_RESPONSE_MARKERS = [
    "github_pat_",
    "ghp_",
    "glpat-",
    "cf_api_token",
    "cloudflare_api_token",
    "client_secret=",
    "session_secret=",
    "database_url=postgres://",
    "BEGIN PRIVATE KEY",
]


@dataclass(frozen=True)
class RuntimeCheck:
    phase: str
    name: str
    status: str
    details: str
    http_status: int | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "name": self.name,
            "status": self.status,
            "details": self.details,
            "http_status": self.http_status,
        }


def build_url(base_url: str, path: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def request(method: str, url: str, cookie: str | None = None, timeout: float = 10.0) -> tuple[int, str, str]:
    headers = {"User-Agent": "ygit-live-runtime-smoke/0.1.0"}
    if cookie:
        headers["Cookie"] = cookie
    req = Request(url=url, method=method, headers=headers)
    try:
        with urlopen(req, timeout=timeout) as response:  # noqa: S310 - explicit runtime smoke target
            body = response.read(512_000).decode("utf-8", errors="replace")
            content_type = response.headers.get("content-type", "")
            return response.status, body, content_type
    except HTTPError as exc:
        body = exc.read(128_000).decode("utf-8", errors="replace")
        return exc.code, body, exc.headers.get("content-type", "")
    except URLError as exc:
        return 0, str(exc.reason), ""
    except TimeoutError as exc:
        return 0, str(exc), ""


def contains_forbidden_marker(body: str) -> str | None:
    body_lower = body.lower()
    for marker in FORBIDDEN_RESPONSE_MARKERS:
        if marker.lower() in body_lower:
            return marker
    return None


def validate_body(expectation: str, body: str, content_type: str) -> tuple[bool, str]:
    if expectation == "json_success":
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            return False, f"invalid JSON: {exc}"
        if data.get("success") is not True:
            return False, "JSON response did not contain success=true"
        return True, "success envelope present"
    if expectation == "json_any":
        try:
            json.loads(body)
        except json.JSONDecodeError as exc:
            return False, f"invalid JSON: {exc}"
        return True, "JSON response parsed"
    if expectation.startswith("contains:"):
        marker = expectation.split(":", 1)[1]
        if marker not in body:
            return False, f"missing body marker: {marker}"
        return True, f"body marker present: {marker}"
    return True, "no body validator"


def run_endpoint_group(
    *,
    phase: str,
    base_url: str,
    endpoints: Iterable[tuple[str, str, str]],
    cookie: str | None,
    allow_auth_rejection: bool = False,
) -> list[RuntimeCheck]:
    checks: list[RuntimeCheck] = []
    for method, path, expectation in endpoints:
        url = build_url(base_url, path)
        status, body, content_type = request(method, url, cookie=cookie)
        name = f"{method} {path}"
        if status == 0:
            checks.append(RuntimeCheck(phase, name, "BLOCKED", body, status))
            continue
        forbidden = contains_forbidden_marker(body)
        if forbidden:
            checks.append(RuntimeCheck(phase, name, "BLOCKED", f"forbidden response marker detected: {forbidden}", status))
            continue
        if allow_auth_rejection and status in {401, 403}:
            checks.append(RuntimeCheck(phase, name, "PASS", "safe auth rejection", status))
            continue
        if not (200 <= status < 300):
            checks.append(RuntimeCheck(phase, name, "BLOCKED", f"unexpected HTTP status {status}", status))
            continue
        valid, detail = validate_body(expectation, body, content_type)
        checks.append(RuntimeCheck(phase, name, "PASS" if valid else "BLOCKED", detail, status))
    return checks


def make_plan_report() -> dict[str, object]:
    return {
        "product": "YGIT",
        "package": "YGIT_Live_Runtime_Smoke_Test_Plan_v0.1.0",
        "plan_version": "0.1.0",
        "overall_status": "PLAN_READY",
        "public_endpoints": [path for _, path, _ in PUBLIC_ENDPOINTS],
        "authenticated_endpoints": [path for _, path, _ in AUTHENTICATED_ENDPOINTS],
        "admin_endpoints": [path for _, path, _ in ADMIN_ENDPOINTS],
        "not_executed": "No live HTTP request is sent in plan-only mode",
    }


def make_report(args: argparse.Namespace) -> dict[str, object]:
    checks: list[RuntimeCheck] = []
    checks.append(RuntimeCheck("phase_0_preflight", "base_url_configured", "PASS", args.base_url))
    checks.extend(run_endpoint_group(phase="phase_1_public_http", base_url=args.base_url, endpoints=PUBLIC_ENDPOINTS, cookie=None))

    session_cookie = args.session_cookie or os.environ.get("YGIT_SMOKE_SESSION_COOKIE")
    admin_cookie = args.admin_cookie or os.environ.get("YGIT_SMOKE_ADMIN_COOKIE")

    if args.include_authenticated:
        if session_cookie:
            checks.extend(
                run_endpoint_group(
                    phase="phase_2_authenticated_http",
                    base_url=args.base_url,
                    endpoints=AUTHENTICATED_ENDPOINTS,
                    cookie=session_cookie,
                    allow_auth_rejection=False,
                )
            )
        else:
            checks.append(RuntimeCheck("phase_2_authenticated_http", "session_cookie_present", "SKIPPED", "No test user session cookie provided"))
    else:
        checks.append(RuntimeCheck("phase_2_authenticated_http", "authenticated_phase", "SKIPPED", "Not requested"))

    if args.include_admin:
        if admin_cookie:
            checks.extend(
                run_endpoint_group(
                    phase="phase_5_admin_http",
                    base_url=args.base_url,
                    endpoints=ADMIN_ENDPOINTS,
                    cookie=admin_cookie,
                    allow_auth_rejection=False,
                )
            )
        else:
            checks.append(RuntimeCheck("phase_5_admin_http", "admin_cookie_present", "SKIPPED", "No admin test session cookie provided"))
    else:
        checks.append(RuntimeCheck("phase_5_admin_http", "admin_phase", "SKIPPED", "Not requested"))

    failures = [check for check in checks if check.status == "BLOCKED"]
    report = {
        "product": "YGIT",
        "package": "YGIT_Live_Runtime_Smoke_Test_Plan_v0.1.0",
        "plan_version": "0.1.0",
        "generated_at_unix": int(time.time()),
        "base_url": args.base_url,
        "overall_status": "BLOCKED" if failures else "PASS",
        "checks": [check.as_dict() for check in checks],
        "failures": [check.as_dict() for check in failures],
        "not_executed_by_this_script": [
            "Alembic current check inside API container",
            "Redis direct connection check",
            "worker job lease check",
            "controlled project/repository/deploy manual flow",
            "real Cloudflare Pages deployment",
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="YGIT live runtime smoke test helper")
    parser.add_argument("--base-url", help="Deployed YGIT base URL, for example https://ygit.net")
    parser.add_argument("--plan-only", action="store_true", help="Print the smoke test matrix without sending live HTTP requests")
    parser.add_argument("--include-authenticated", action="store_true", help="Run authenticated user endpoints with test session cookie")
    parser.add_argument("--include-admin", action="store_true", help="Run admin endpoints with admin test session cookie")
    parser.add_argument("--session-cookie", help="Test user session cookie. Prefer YGIT_SMOKE_SESSION_COOKIE env var.")
    parser.add_argument("--admin-cookie", help="Admin test session cookie. Prefer YGIT_SMOKE_ADMIN_COOKIE env var.")
    parser.add_argument("--write-report", action="store_true", help="Write LIVE_RUNTIME_SMOKE_TEST_REPORT.json")
    args = parser.parse_args()

    if args.plan_only:
        report = make_plan_report()
        print(json.dumps(report, indent=2))
        return 0
    if not args.base_url:
        parser.error("--base-url is required unless --plan-only is used")
    report = make_report(args)
    if args.write_report:
        REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
