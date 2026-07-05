# YGIT Worker Runtime Integration v0.1.0

**Product:** YGIT
**Company:** Vib Tools
**Version:** 0.1.0
**Architecture Baseline:** Architecture Freeze v1.1
**Contract Baseline:** Engine Contract v1.0 / API Contract v1.0 / Database Architecture v1.0

---

## Purpose

This release integrates the single shared worker runtime with the Worker / Job System boundary.

It implements durable job-state structures and the worker dispatch lifecycle required before Dashboard and Admin Panel implementation.

---

## Implemented

```text
Worker Runtime public lifecycle
Durable jobs table model
Job Repository
Job System public service
QueueClient durable-job integration
Worker run_once lifecycle
Job leasing
Job completion
Job failure
Retry scheduling
Job status route
Deploy job runtime handoff
Redeploy job runtime handoff
Deep analysis job boundary
Webhook job boundary
Alembic migration 0008_worker_runtime_jobs
Worker architecture tests
Runtime tests
Smoke script update
Release manifest update
Version registry update
Changelog update
```

---

## Runtime Boundary

```text
Worker
↓
Queue / Job Repository
↓
Job Runner
↓
Engine Public API / Deploy Pipeline
↓
Provider Layer
```

Worker Runtime does not contain deployment business logic and does not call providers directly.

---

## Enabled Job Types

```text
deploy_project
redeploy_project
repository_analysis_deep
webhook_event
```

---

## API Route Added

```text
GET /api/v1/jobs/{job_id}
```

---

## Owned Table

```text
jobs
```

---

## Security Boundary

```text
No provider token exposure
No Worker → GitHub Provider direct call
No Worker → Cloudflare Provider direct call
No API route → Worker internal runtime import
No Worker job → engine repository direct import
No business logic inside Worker Runtime
```

---

## Verification

```text
python -m compileall -q backend
pytest -q
python scripts/smoke_test.py --skip-db
python -m zipfile -t YGIT_Worker_Runtime_Integration_v0.1.0.zip
basic secret scan
```

Live PostgreSQL, Redis, GitHub API, Cloudflare API, and real Cloudflare Pages deployment were not executed in the sandbox.
