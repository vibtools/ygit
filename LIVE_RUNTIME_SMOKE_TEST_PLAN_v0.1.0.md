# YGIT Live Runtime Smoke Test Plan v0.1.0

**Product:** YGIT
**Company:** Vib Tools
**Plan Version:** 0.1.0
**Architecture Baseline:** YGIT Architecture Freeze v1.1
**Contract Baseline:** Engine Contract v1.0, API Contract v1.0, Database Architecture v1.0
**Package:** `YGIT_Live_Runtime_Smoke_Test_Plan_v0.1.0`
**Status:** Created for controlled live/runtime validation

---

## 1. Purpose

This document defines the first controlled **live runtime smoke test plan** for YGIT MVP.

The previous integration release gate validated code, contracts, route registration, migration files, static boundaries, manifests, and sandbox runtime behavior. This live smoke plan validates the same baseline against a real deployed environment where these components can be reached together:

```text
Browser / HTTP client
↓
ygit-api
↓
PostgreSQL
Redis
YGIT Worker
↓
Deploy Pipeline skeleton
↓
Provider boundary stubs / later live provider checks
```

This is a release readiness plan, not a new engine and not a product feature.

---

## 2. Non-Goals

This package does not add:

```text
New engine
New database table
New Alembic migration
New external dependency
New worker type
New provider integration
New dashboard feature
New admin feature
```

It also does not execute real Cloudflare Pages deployment in the sandbox.

---

## 3. Required Runtime Environment

Minimum live runtime target:

```text
ygit-api container running
PostgreSQL reachable by API container
Redis reachable by API and worker containers
ygit-worker container running
Migrations applied through 0012_notification_engine
Vib ID / Keycloak auth configured
Dashboard route available
Admin route available
HTTPS configured at deployment edge
```

Expected environment variables must come from deployment secrets, not Git.

---

## 4. Smoke Test Phases

### Phase 0 — Preflight

Validate deployment shape before HTTP checks:

```text
Container status
ygit-api logs
ygit-worker logs
PostgreSQL connectivity
Redis connectivity
Applied Alembic head
Environment variable presence without printing values
```

Pass criteria:

```text
API starts without import error
Worker starts without import error
PostgreSQL connection succeeds
Redis connection succeeds
No obvious startup secret leakage in logs
```

### Phase 1 — Public HTTP Entry Points

Validate unauthenticated safe endpoints:

```text
GET /api/v1/platform/health
GET /api/v1/platform/version
GET /dashboard
GET /admin
```

Pass criteria:

```text
HTTP 200 for public-safe routes
Standard API envelope for API endpoints
Dashboard HTML loads
Admin operations console HTML loads
No token or secret string appears in response body
```

### Phase 2 — Auth Boundary

Validate Vib ID / Keycloak redirect and session behavior:

```text
GET /api/v1/auth/login
GET /api/v1/me without session
GET /api/v1/me with valid session
POST /api/v1/auth/logout with valid session
```

Pass criteria:

```text
Login redirects to auth.vib.tools realm vib
Unauthenticated /me is rejected safely
Authenticated /me returns safe user context
Logout clears server-side session
No access token is returned to browser JSON
```

### Phase 3 — User Flow Smoke

Validate the MVP user flow with a controlled test account:

```text
Create project
Validate repository URL
Fetch repository metadata
Run quick repository analysis
Reserve project domain / generated YGIT URL
Connect provider status check
Request deployment
Read deployment status
Read deployment logs
Read notifications
```

Pass criteria:

```text
Each endpoint returns the standard API envelope
IDs use expected prefixes
No provider token appears in any response
Deployment request returns queued status quickly
Deployment execution stays behind worker / pipeline boundary
```

### Phase 4 — Worker Runtime Smoke

Validate worker and job system in live environment:

```text
Create job through deploy request or deep-analysis request
Read job status
Confirm worker can lease job
Confirm retry/failure state is safe
Confirm worker does not call providers directly
```

Pass criteria:

```text
jobs table persists job
worker records status transition
job failure is sanitized if provider execution is unavailable
no deployment log is written directly by worker
```

### Phase 5 — Admin Operations Console Smoke

Validate Platform Operations Console behavior:

```text
GET /api/v1/admin/overview
GET /api/v1/admin/platform/health
GET /api/v1/admin/queue/status
GET /api/v1/admin/system-monitoring
GET /api/v1/admin/deployments
GET /api/v1/admin/users
GET /api/v1/admin/audit-logs
GET /api/v1/admin/settings
GET /api/v1/admin/manifest
```

Pass criteria:

```text
Admin routes require admin role
Admin responses do not expose provider tokens, OIDC secrets, database credentials, or session values
Admin surface uses approved public API boundaries
```

### Phase 6 — Negative Security Smoke

Validate responses and logs do not leak sensitive material:

```text
API responses
Dashboard HTML
Admin HTML
Worker logs
API logs
Deployment logs
Audit logs
Notification metadata
```

Reject if any live output exposes:

```text
GitHub token value
Cloudflare token value
OIDC client secret
Session secret
Database password
Raw Authorization header
Private key
```

### Phase 7 — Controlled Provider Boundary Smoke

For this v0.1.0 plan, provider checks are boundary checks only.

```text
GitHub provider direct call from API route: forbidden
Cloudflare provider direct call from API route: forbidden
Worker direct provider call: forbidden
Deploy Engine direct provider call: forbidden
Deploy Pipeline remains the provider boundary
```

Real GitHub and Cloudflare deployment execution belongs to a later live provider integration plan.

---

## 5. Required Test Accounts

Use dedicated non-production resources:

```text
Smoke test Vib ID user
Smoke test ygit_admin user
Smoke test GitHub repository
Smoke test Cloudflare account / Pages target
Smoke test ygit.net slug prefix, for example smoke-<date>-<shortid>
```

Do not use a personal production GitHub repository or production Cloudflare account for first smoke.

---

## 6. Rollback Criteria

Stop the smoke test and roll back or disable access if any of the following occur:

```text
API fails to boot
Migrations fail or apply out of order
User session cannot be validated
Provider tokens appear in any response or logs
Admin route is accessible without admin role
Worker mutates deployment logs directly
Deployment request blocks the HTTP request thread
Repeated 5xx errors occur on baseline health/version routes
```

---

## 7. Output Artifacts

A completed live smoke run must produce:

```text
LIVE_RUNTIME_SMOKE_TEST_REPORT.json
Container status evidence
API health/version evidence
Migration head evidence
Worker status evidence
Auth boundary result
Admin boundary result
Secret exposure scan result
Known issues list
Final PASS / BLOCKED decision
```

---

## 8. Release Decision Rule

```text
PASS
  Live runtime can proceed to controlled provider integration smoke.

BLOCKED
  Fix infrastructure/runtime/auth/worker issue before provider integration.

SKIPPED
  A phase was not executed and must not be counted as passed.
```

For MVP v0.1.0, **real Cloudflare Pages deployment is not required to pass this smoke plan** unless explicitly enabled by a later provider integration gate.
