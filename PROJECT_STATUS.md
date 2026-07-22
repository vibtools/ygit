# YGIT Project Status

Version: 0.1.0
Status: Active Engineering Snapshot
Updated: 2026-07-22
Product: YGIT
Company: Vib Tools

## Purpose

This document records the current engineering state of the YGIT MVP. It separates implemented foundations from runtime behavior that has actually been exercised.

## Product Definition

YGIT is an open-source deployment automation platform.

It automates deployment of supported Git repositories to infrastructure owned by the user. It is not a website builder, hosting company, CMS, or general-purpose control panel.

## Progress Estimate

| Area | Estimate | Meaning |
|---|---:|---|
| Core MVP implementation | Approximately 97% | Core engines, providers, dashboard, admin surface, queue/runtime foundations, deployment orchestration, and trusted policy handoff are substantially implemented |
| First controlled live deployment path | Approximately 98% | Pre-live code and validation tooling are complete; controlled production evidence remains |
| Production readiness | Not complete | Live reliability, operational hardening, and end-to-end production evidence remain |

These values are engineering planning estimates and are not automated test results.

## Current Architecture State

```text
Dashboard / Admin
        ↓
FastAPI API
        ↓
Independent Engines
        ↓
Deploy Pipeline / Provider Boundaries
        ↓
Worker Runtime
        ↓
GitHub / Cloudflare / PostgreSQL / Redis
```

Business logic remains outside the Dashboard. Providers are not imported directly by API routes, Deploy Engine, Deployment History Engine, or worker job handlers.

## Engine Matrix

| Engine/component | Status | Important remaining work |
|---|---|---|
| Auth Engine | Implemented | Controlled production identity/session validation |
| Connected Accounts Module | Implemented | Live account/credential lifecycle validation under production configuration |
| Project Engine | Implemented | No critical foundation gap identified |
| Repository Engine | Metadata persistence implemented; live tree acquisition incomplete | GitHub App installation-token metadata/tree fetch, commit pinning, and private repository validation |
| Repository Analysis Engine | Quick-analysis contract implemented; current live input is incomplete | Actual repository tree acquisition, deep-analysis execution, Project reattachment after recalculation, and broader framework validation |
| Deploy Engine | Implemented; AG-001 provider gate foundation added but not runtime-wired | Provider result reconciliation and reviewed future gate integration |
| Deploy Pipeline | Concrete Cloudflare orchestration and trusted policy-to-binding handoff implemented; default runtime disabled | Controlled live provider validation and operational hardening |
| Deployment History Engine | Pipeline intent, provider-result, terminal-failure, and retry-safe replay persistence integrated | Controlled PostgreSQL validation and operational monitoring |
| Worker Runtime | DB dispatch, checkout, build, retry, credential boundary, provider binding, trusted server-owned policy resolution, dispatcher handoff, and default-disabled deploy/redeploy integration implemented | Live Redis worker execution and operational hardening |
| Domain Engine | MVP generated-domain flow implemented | Custom-domain and Cloudflare DNS automation |
| Audit Engine | Implemented | Production retention/operations validation |
| Platform Engine | Implemented | Production settings and feature-flag operations validation |
| Notification Engine | Implemented for in-app scope | Live deployment-event integration |
| Dashboard | Implemented | Production visual/runtime validation |
| Admin Panel | Implemented | Production operations validation |
| GitHub Provider | Foundation implemented | Controlled live API execution |
| Cloudflare Provider | OAuth/account and Pages deployment primitives implemented | Controlled live API execution and operational hardening |

## Recently Completed Foundations

- Worker database-aware dispatch contract.
- Cloudflare credential acquisition boundary.
- Connected Accounts avatar, status, connection date, scopes, last sync, and imported-repository reuse UI.
- Cloudflare Pages project creation/reuse foundation.
- Artifact manifest and byte-upload foundations.
- Missing-asset upload planning.
- Asset hash registration.
- Cloudflare Pages deployment creation.
- Concrete provider gateway orchestration and typed completion result.
- Runtime-only provider pipeline binding foundation.
- DB-aware deploy/redeploy handler binding that omits provider enablement.
- Trusted server-owned provider execution policy with default `disabled`, explicit `cloudflare`, and fail-closed unknown or inconsistent modes.
- Worker Runtime policy ownership, dispatcher handoff, and deploy/redeploy binding integration.
- Untrusted job-payload provider-enablement protection.
- Deployment History runtime persistence and deterministic retry-safe history-write idempotency.
- Production configuration, PostgreSQL, Redis, public-route, and provider-mode live-readiness tooling.
- AG-001 Deploy Provider Gate foundation with Cloudflare default and fail-closed future resolver contract.

## Current Safety Boundary

The default runtime remains provider-disabled.

A concrete provider pipeline can be assembled only through the Worker Runtime-owned policy decision. Worker Runtime resolves the server setting, Job Dispatcher transports the immutable policy, and deploy/redeploy handlers validate it before handing a boolean to the neutral binding. The default mode is `disabled`; job payload fields cannot control the policy or enable execution. AG-001 remains standalone and is not used by runtime execution.

Provider results and failures are now routed through the Deployment History Engine public boundary. Deterministic intent keys prevent duplicate history logs during sequential job retries, and an existing completed history record blocks duplicate provider execution. Live PostgreSQL, Redis, GitHub, and Cloudflare evidence is still required.

GitHub integration is architecture-locked to a GitHub App. Vib ID / Keycloak remains the YGIT user-authentication system, and Cloudflare remains a separate OAuth-connected provider. `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` are forbidden legacy variables. GitHub webhook capability is explicitly default-disabled; its secret becomes required only after an approved receiver is enabled.

## Latest Verification Evidence

```text
Provider execution policy unit tests: 18 passed
Provider policy runtime integration: 9 passed
Deploy/redeploy handler binding regression: 5 passed
Dispatcher DB regression: 5 passed
Worker Runtime architecture: 4 passed
Deploy/redeploy architecture: 2 passed
AG-001 regression: 15 passed
Deployment History runtime: 8 passed
Deployment History idempotency: 4 passed
Live-readiness tooling: 18 passed
Runtime image packaging: 4 passed
GitHub App permission capture: 7 passed
Dashboard compact provider cards: 10 passed
Project Open UI: 9 passed
Project Deploy UI: 9 passed
Full suite: 554 passed, 1 warning
Smoke --skip-db: PASS
Release gate --skip-db: PASS
```

Database checks were skipped. External providers were not executed.

## Remaining Critical Path

1. Redeploy the current main branch and validate the Dashboard compact provider cards, Project Open flow, and backend-readiness-gated Deploy flow.
2. Reduce the GitHub App to the approved minimum permissions, reconnect the controlled installation, and verify captured permission scopes.
3. Implement GitHub App installation-token repository acquisition with a pinned commit SHA and normalized real file-tree snapshot.
4. Implement the approved deep-analysis execution and Project reattachment boundaries.
5. Confirm `deploy_ready=true` from real repository evidence and execute one controlled Cloudflare Pages deployment.
6. Resolve only defects demonstrated by live evidence.
7. Review AG-001 runtime integration only as part of future YGIT App Engine work.

## Documentation Authority

Current-state documents:

- `README.md`
- `PROJECT_STATUS.md`
- `VERSION.json`
- `CONTRACT_MANIFEST.json`
- `CHANGELOG.md`
- `AUDIT_REPORT.md`
- `REPOSITORY_ANALYSIS_CURRENT_STATE_AUDIT.md`

Historical release artifacts retain their original versioned purpose. Where a historical artifact conflicts with this current snapshot, this document and the current source code take precedence for development status.

## Revision History

| Date | Revision | Summary |
|---|---|---|
| 2026-07-22 | 1.9 | Documented the current Repository Analysis input, readiness, deep-queue, recalculation, and Project attachment gaps |
| 2026-07-22 | 1.8 | Made GitHub App webhook readiness conditional and locked the current webhook capability off |
| 2026-07-21 | 1.7 | Locked GitHub integration to the GitHub App contract and corrected live-readiness validation |
| 2026-07-21 | 1.6 | Packaged live-readiness artifacts in the shared API/worker runtime image |
| 2026-07-21 | 1.5 | Added controlled live-readiness tooling and production validation runbook |
| 2026-07-21 | 1.4 | Added Deployment History result persistence and retry-safe intent idempotency |
| 2026-07-21 | 1.3 | Added trusted provider-policy runtime handoff while preserving the default-disabled path |
| 2026-07-21 | 1.2 | Added trusted server-owned provider execution policy foundation |
| 2026-07-21 | 1.1 | Added default-disabled handler binding and AG-001 Deploy Provider Gate foundation |
| 2026-07-21 | 1.0 | Added authoritative project snapshot through the worker provider pipeline binding foundation |
