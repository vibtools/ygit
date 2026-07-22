# Changelog

All notable YGIT MVP implementation releases and active engineering foundations are tracked here.

## Unreleased — Provider Orchestration and Runtime Binding Foundations — 2026-07-21

### Added

- Worker database-aware dispatch from Worker Runtime through Job Dispatcher.
- Cloudflare deployment credential acquisition through the Connected Accounts public boundary.
- Constant-time credential-reference verification and secret-wrapped runtime credential handling.
- Connected Accounts provider avatars, connection date, scopes, last sync, status badge, and repository reuse UI.
- Cloudflare Pages project ensure/reuse foundation.
- Artifact manifest generation and bounded asset-byte upload batches.
- Missing-asset planning and upload-session handling.
- Asset hash registration.
- Cloudflare Pages deployment creation.
- Concrete Cloudflare provider gateway with ordered orchestration.
- Typed successful pipeline completion result.
- Runtime-only provider gateway and isolated Deploy Pipeline assembly foundation.
- DB-aware deploy/redeploy handler binding that preserves default-disabled execution.
- Protection preventing untrusted job payloads from enabling provider execution.
- AG-001 Deploy Provider Gate standalone foundation with Cloudflare default and fail-closed future resolver support.
- Trusted server-owned provider execution policy foundation with default `disabled`, explicit `cloudflare`, and fail-closed unknown modes.
- Current project-status documentation.

### Changed

- Deploy Pipeline is no longer only a contract skeleton at the implementation level; concrete Cloudflare orchestration exists behind an explicit gateway.
- Deploy/redeploy handlers now use worker-owned database context and the neutral provider binding, while omitting the enablement flag so execution remains provider-disabled.
- AG-001 is a standalone gate contract only; it is not wired into runtime and no YGIT App Engine was created.
- The worker policy foundation is separate from AG-001 and is not yet connected to deploy/redeploy handlers.
- Documentation now distinguishes historical release artifacts from the current engineering snapshot.

### Verified

- Provider execution policy suite: 12 passed.
- Worker Runtime architecture suite: 4 passed.
- Deploy/redeploy handler regression: 5 passed.
- AG-001 regression: 15 passed.
- Full suite: 465 passed.
- Smoke test with database skipped: PASS.
- Release gate with database skipped: PASS.

### Not Yet Enabled

- Trusted policy-to-handler runtime wiring.
- AG-001 runtime wiring or future YGIT App resolver integration.
- Provider result persistence into Deployment History Engine.
- Live PostgreSQL, Redis worker, GitHub API, and Cloudflare Pages execution.

All notable YGIT MVP implementation releases are tracked here.

## YGIT Admin Panel v0.1.0 — 2026-07-04

### Added

- Admin Panel as Platform Operations Console, not user project management dashboard.
- Static admin shell served at `/admin`.
- Admin assets under `/admin/assets/*`.
- Protected admin API contract under `/api/v1/admin/*`.
- Operations sections: Overview, Platform Health, Queue Status, System Monitoring, Deployments, Users, Audit Logs, Settings.
- Admin Surface service under `backend/app/admin_surface`; no `admin_engine` was created.
- Role-gated API endpoints using `ygit_admin`, `ygit_support`, and `ygit_readonly` through existing Auth Engine guard.
- Boundary tests proving no provider direct imports, no database direct mutation, and no Admin Engine directory.

### Boundary

- Admin Panel is an operations console only.
- Admin Panel does not import engines directly from frontend.
- Admin API routes do not call providers.
- Admin Surface does not own database tables.
- User-facing project management remains in Dashboard.


## Connected Accounts Module v0.1.0 — 2026-07-04

### Added

- Connected Accounts Module under Auth Engine.
- GitHub and Cloudflare provider connection state.
- Safe token-reference handling; raw provider tokens are not exposed.
- `connected_accounts` SQLAlchemy model and owned repository.
- Connected Accounts public/internal boundary.
- Connected Accounts API routes:
  - `GET /api/v1/connected-accounts`
  - `GET /api/v1/connected-accounts/{provider}/connect`
  - `GET /api/v1/connected-accounts/{provider}/callback`
  - `DELETE /api/v1/connected-accounts/{provider}`
- Alembic migration `0005_connected_accounts_module`.
- Provider validation stubs for GitHub and Cloudflare.
- Release manifest, version registry, smoke-test updates, and tests.

## Repository Analysis Engine v0.1.0 — 2026-07-04

### Added

- Repository Analysis Engine public/internal boundary.
- Quick Analysis flow.
- Framework Detection module.
- Package Manager Detection module.
- Build Command Detection module.
- Output Directory Detection module.
- Static/Dynamic Detection module.
- Deploy Readiness module.
- Repository Score module.
- Warnings and Recommendations modules.
- Deep Analysis job-reference placeholder.
- Result Store and `analysis_results` owned table.
- Repository Analysis API routes:
  - `POST /api/v1/repository-analysis/quick`
  - `POST /api/v1/repository-analysis/deep`
  - `GET /api/v1/repository-analysis/{analysis_id}`
  - `POST /api/v1/repository-analysis/{analysis_id}/recalculate`
- Repository Analysis tests, migration, docs, release manifest, and smoke-test coverage.

## Repository Engine v0.1.0 — 2026-07-04

### Added

- Repository Engine public/internal boundary.
- GitHub repository URL validation and normalization.
- GitHub SSH URL normalization.
- Repository metadata service and owned repository layer.
- `repository_metadata` SQLAlchemy model and Alembic migration.
- GitHub Provider metadata wrapper.
- Repository API routes:
  - `POST /api/v1/repositories/validate`
  - `POST /api/v1/repositories/metadata`
  - `GET /api/v1/repositories/{repository_id}`
- Release manifest, version registry, changelog, and runtime smoke script.
- Repository Engine boundary and contract tests.

## Project Engine v0.1.0 — 2026-07-04

### Added

- Project Engine public/internal boundary.
- Project models, routes, migration, validators, tests, and docs.

## Auth Engine v0.1.0 — 2026-07-04

### Added

- Vib ID / Keycloak OIDC integration boundary.
- Server-side session, login, callback, logout, current user, and role guard scaffolding.

## FastAPI MVP Skeleton v0.1.0 — 2026-07-04

### Added

- FastAPI modular monolith structure.
- API container, worker container, PostgreSQL, Redis, route groups, response envelope, and contract manifest.

## v0.1.0 - Deploy Engine

### Added

- Deploy Engine public/internal boundary.
- Deployment request validation.
- Deploy readiness checks using approved public engine APIs.
- Queued deployment creation.
- Redeploy and cancel workflows.
- Deployment read endpoint.
- Job enqueue integration.
- `deployments` model and migration.
- Boundary tests proving Deploy Engine does not import GitHub/Cloudflare providers.

### Boundary

- Deploy Engine does not contain GitHub build logic.
- Deploy Engine does not call Cloudflare API.
- Provider execution remains reserved for Deploy Pipeline.

## v0.1.0 - Deploy Pipeline Contract and Skeleton

- Added Deploy Pipeline public API.
- Added frozen pipeline stage contract.
- Added frozen pipeline event contract.
- Added Deployment History write intent contract.
- Added provider summary and safe metadata schemas.
- Added contract-skeleton provider gateway.
- Updated redeploy worker job to use `execute_redeployment`.
- Added Deploy Pipeline contract and boundary tests.

## v0.1.0 - Deployment History Engine

### Added

- Deployment History Engine public/internal boundary.
- `deployment_history` SQLAlchemy model and repository.
- `deployment_logs` SQLAlchemy model and append-only repository.
- Alembic migration `0007_deployment_history_engine`.
- Deployment History public API for history records, status updates, logs, and project deployment list.
- Deploy Pipeline `HistoryWriteIntent` consumer.
- API routes:
  - `GET /api/v1/projects/{project_id}/deployments`
  - `GET /api/v1/deployments/{deployment_id}/logs`
- Secret-safe metadata validation for logs/history/provider summaries.
- Architecture tests proving Deployment History Engine does not import GitHub/Cloudflare providers or pipeline execution services.

### Boundary

- Deployment History Engine does not decide deploy readiness.
- Deployment History Engine does not call GitHub Provider.
- Deployment History Engine does not call Cloudflare Provider.
- Deployment History writes are available only through the engine public API.


## Worker Runtime Integration v0.1.0

Added single shared Worker Runtime integration, durable `jobs` table model, Job Repository, Job System public service, job leasing, dispatch lifecycle, retry scheduling, job status API route, worker boundary tests, and migration `0008_worker_runtime_jobs`.

Boundary confirmations:

- Worker Runtime does not call GitHub Provider directly.
- Worker Runtime does not call Cloudflare Provider directly.
- Worker jobs dispatch through approved Engine Public API / Deploy Pipeline boundaries.
- Worker owns only `jobs`; engine-owned tables remain owned by their engines.

## YGIT Dashboard v0.1.0

### Added

- Dashboard static client shell served at `/dashboard`.
- Dashboard assets under `/dashboard/assets/*`.
- Dark-first YGIT UI using the approved blue/accent/success color system.
- Dashboard navigation: Dashboard, Projects, Deployments, Connected Accounts, Templates Beta, Settings.
- Future/preview navigation: AI Builder, Marketplace, Plugins, Teams, Analytics, Developer Portal.
- API-only client calls to `/api/v1` routes.
- Project creation form wired to `POST /api/v1/projects`.
- Deployment action wired to `POST /api/v1/projects/{project_id}/deploy`.
- Connected accounts summary wired to `GET /api/v1/connected-accounts`.
- Dashboard route tests and boundary tests.

### Boundary

- Dashboard contains no business logic.
- Dashboard does not import engines, providers, database, worker runtime, or pipelines.
- Dashboard calls backend API only.
- No new database table.
- No new external dependency.

## Domain Engine v0.1.0

- Implemented Domain Engine public/internal boundary.
- Added MVP-generated URL support for `*.ygit.net`.
- Added slug validation, reserved slug checks, availability check, project slug reservation, project domain read, and domain release flow.
- Added `domains` SQLAlchemy model and Alembic migration `0009_domain_engine_domains`.
- Kept custom domain automation and Cloudflare DNS automation out of scope for MVP.
- Updated release manifest, version registry, smoke script, tests, delivery note, and audit report.

## YGIT Audit Engine v0.1.0 - 2026-07-04

### Added

- Audit Engine public/internal boundary.
- `audit_logs` SQLAlchemy model and owned repository.
- Immutable append-only audit log storage contract.
- Secret-safe audit metadata redaction.
- Admin audit log route integration through Audit Engine public API.
- Alembic migration `0010_audit_engine_audit_logs`.
- Architecture boundary tests, service tests, route contract tests.
- Release manifest, version registry, smoke script, delivery note, and audit report updates.

### Boundaries

- No provider imports inside Audit Engine.
- No Deploy Pipeline import inside Audit Engine.
- No direct admin mutation of audit logs.
- No audit log delete/update API.


## YGIT Notification Engine v0.1.0

Implemented Notification Engine with in-app notifications, unread count, mark-read flow, `notifications` table ownership, migration `0012_notification_engine_notifications`, API routes, public/internal boundary, secret-safe metadata validation, and architecture boundary tests.


## YGIT MVP Integration Review and Release Gate v0.1.0 — 2026-07-04T22:52:08Z

### Added

- MVP integration review release gate.
- `scripts/release_gate.py` for static and in-process runtime gate checks.
- `MVP_RELEASE_GATE_REPORT.json` release gate report.
- `MVP_RELEASE_GATE_CHECKLIST.md` release checklist.
- `MVP_INTEGRATION_REVIEW_AND_RELEASE_GATE_v0.1.0.md` integration review document.

### Confirmed

- No new engine.
- No new database table.
- No new migration.
- No new external dependency.
- Release gate validates route registry, migration chain, manifests, and architecture boundaries.


## YGIT Live Runtime Smoke Test Plan v0.1.0

### Added

- Live runtime smoke test plan.
- Live runtime smoke checklist.
- Live runtime smoke runbook.
- Live runtime smoke matrix.
- `scripts/live_runtime_smoke_test.py` helper using Python standard library only.
- Tests validating plan artifacts, matrix, and script report behavior.

### Boundaries

- No new engine.
- No new database table.
- No new migration.
- No new external dependency.
- No real provider deployment execution in sandbox.
