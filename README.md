# YGIT Audit Engine v0.1.0

YGIT is a deployment automation platform by Vib Tools. This package contains the YGIT backend through **Audit Engine v0.1.0**.

## Current Release

```text
Component: Audit Engine
Version: 0.1.0
Architecture: YGIT Architecture Freeze v1.1
Engine Contract: v1.0
API Contract: v1.0
Database Contract: v1.0
```

## Implemented Engines / Components

```text
Auth Engine
Project Engine
Repository Engine
Repository Analysis Engine
Connected Accounts Module
Deploy Engine
Deploy Pipeline Contract + Skeleton
Deployment History Engine
Worker Runtime Integration
Dashboard
Admin Panel
Domain Engine
Audit Engine
```

## Audit Engine Scope

```text
Immutable audit log persistence
Event envelope recording
Safe admin audit log read surface
Secret-safe metadata redaction
Append-only repository contract
PostgreSQL immutability trigger migration
```

## Runtime

```text
ygit-api
ygit-worker
postgres
redis
```

## Verify

```bash
python -m compileall -q backend
pytest -q
python scripts/smoke_test.py --skip-db
```

Live PostgreSQL/Redis and real provider calls are not required for sandbox verification.


## Platform Engine v0.1.0

Implemented MVP Platform Engine with health, version, system status, feature flags, platform settings summary, and owned tables `platform_settings` and `feature_flags`.


## YGIT Notification Engine v0.1.0

Implemented Notification Engine with in-app notifications, unread count, mark-read flow, `notifications` table ownership, migration `0012_notification_engine_notifications`, API routes, public/internal boundary, secret-safe metadata validation, and architecture boundary tests.


## MVP Integration Review and Release Gate v0.1.0

This package includes the MVP integration review release gate.

Run:

```bash
python scripts/release_gate.py --skip-db --write-report
pytest -q
python scripts/smoke_test.py --skip-db
```

The release gate validates the implemented MVP engine registry, API routes, migration chain, manifests, and architecture boundaries. It does not add a new engine, database table, migration, or external dependency.


## Live Runtime Smoke Test Plan v0.1.0

This package adds the controlled live/runtime smoke test plan after the MVP Integration Review and Release Gate.

Artifacts:

```text
LIVE_RUNTIME_SMOKE_TEST_PLAN_v0.1.0.md
LIVE_RUNTIME_SMOKE_TEST_CHECKLIST.md
LIVE_RUNTIME_SMOKE_TEST_RUNBOOK.md
LIVE_RUNTIME_SMOKE_TEST_MATRIX.json
scripts/live_runtime_smoke_test.py
```

Public live smoke helper:

```bash
python scripts/live_runtime_smoke_test.py --base-url https://ygit.net --write-report
```

Authenticated and admin phases require dedicated test sessions and should use environment variables for session cookies.
