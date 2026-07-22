# YGIT

YGIT is an open-source deployment automation platform by Vib Tools.

YGIT helps users deploy supported Git repositories to their own Cloudflare Pages accounts while keeping ownership of the repository, Cloudflare account, domain, code, and infrastructure.

YGIT is not a website builder, hosting company, CMS, or general-purpose control panel.

## Core Flow

```text
Paste Repository
        ↓
Analyze Repository
        ↓
Connect Accounts
        ↓
Deploy
        ↓
Website Live
```

## Current Development Status

Status: **Pre-live provider integration**

The MVP architecture and core engines are substantially implemented. Concrete Cloudflare Pages orchestration, the runtime-only provider pipeline binding foundation, and DB-aware deploy/redeploy handler binding are present. The handlers deliberately omit provider enablement, so production execution remains on the default disabled/skeleton path.

Engineering estimate:

```text
MVP implementation: approximately 92–94%
First controlled live deployment path: approximately 90–92%
Production readiness: not yet reached
```

These percentages are planning estimates, not release-gate results.

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for the authoritative engineering snapshot.

## Architecture

```text
Presentation Layer
        ↓
API Layer
        ↓
Engine Layer
        ↓
Provider Layer
        ↓
Infrastructure
```

The Dashboard and Admin Panel are clients/surfaces. Business logic remains inside engines and pipelines.

## Technology

```text
Backend: Python, FastAPI
Authentication: Keycloak / OIDC
Database: PostgreSQL
Queue/runtime coordination: Redis + Worker Runtime
Source control: GitHub
Deployment provider: Cloudflare Pages
Object storage target: Cloudflare R2
```

## Core Engine Status

| Engine or component | Current state |
|---|---|
| Auth Engine | Implemented with OIDC/session boundaries |
| Connected Accounts Module | Implemented with GitHub/Cloudflare connection state, credential references, credential acquisition boundary, metadata UI, scopes, last-sync data, and disconnect/reconnect flows |
| Project Engine | Implemented |
| Repository Engine | Implemented |
| Repository Analysis Engine | Implemented for MVP quick/deep analysis contracts |
| Deploy Engine | Implemented for validation, queued deployment lifecycle, redeploy, cancel, and reads |
| Deploy Pipeline | Contracts, build stage, Cloudflare operation plan, concrete Cloudflare Pages gateway, completion result branch, and isolated provider pipeline factory implemented |
| Deployment History Engine | Storage/API contracts implemented; final live provider-result persistence integration remains |
| Worker Runtime | Durable jobs, leasing, retry, DB-aware dispatch, checkout/build handoff, credential boundary, provider pipeline binding, and default-disabled deploy/redeploy handler binding implemented |
| Domain Engine | Generated YGIT URL and slug lifecycle implemented; custom domain and Cloudflare DNS automation remain outside current MVP execution path |
| Audit Engine | Implemented |
| Platform Engine | Implemented |
| Notification Engine | Implemented for in-app MVP scope |
| Dashboard | Implemented, including Connected Accounts metadata and imported-repository reuse UI |
| Admin Panel | Implemented as a protected operations console |
| GitHub Provider | Repository metadata and account integration foundations implemented |
| Cloudflare Provider | OAuth/account foundations and Cloudflare Pages project, artifact, asset upload, hash registration, and deployment primitives implemented |

## App Gate Foundations

AG-001 Deploy Provider Gate is implemented as a standalone Deploy Engine extension contract.

```text
build_target missing
        ↓
cloudflare

build_target present
        ↓
injected future resolver
        ↓
selected provider
```

AG-001 is not runtime-wired. It does not call providers, access the database, mutate deployment state, or create a YGIT App Engine. Current Cloudflare behavior remains unchanged.

## Provider Execution Safety State

Implemented:

- Cloudflare provider operation planning.
- Runtime credential acquisition through the Connected Accounts public boundary.
- Secret-wrapped credential handoff.
- Concrete Cloudflare Pages orchestration.
- Provider-error sanitization.
- Runtime-only isolated provider pipeline assembly.
- Protection against job-payload-controlled provider enablement.

The default runtime remains provider-disabled.

Still disabled or incomplete:

- Trusted server-side provider enablement.
- AG-001 runtime integration and future YGIT App resolver integration.
- Final provider-result/history persistence.
- Live Cloudflare API execution from the production worker.
- Controlled end-to-end PostgreSQL, Redis worker, and Cloudflare Pages validation.

## Verification Snapshot

Latest verified local run for the current foundation:

```text
Step 48A targeted tests: 129 passed
AG-001 gate tests: 15 passed
Full suite: 453 passed
Smoke test with database skipped: PASS
Release gate with database skipped: PASS
Live PostgreSQL: NOT EXECUTED
Live Redis worker loop: NOT EXECUTED
GitHub API integration: NOT EXECUTED
Cloudflare API integration: NOT EXECUTED
Real Cloudflare Pages deployment: NOT EXECUTED
```

The recurring `StarletteDeprecationWarning` is non-blocking and relates to the existing test-client dependency combination.

## Local Verification

```bash
python -m pytest -q
python scripts/smoke_test.py --skip-db
python scripts/release_gate.py --skip-db
```

Live checks must use the controlled runtime runbook and dedicated test accounts.

## Immediate Critical Path

1. Commit the verified DB-aware default-disabled handler binding, AG-001 gate foundation, and aligned documentation.
2. Add trusted server-side provider execution configuration while keeping the default disabled.
3. Integrate AG-001 only when a reviewed runtime provider-selection contract is approved.
4. Persist provider results through Deployment History Engine.
5. Run controlled PostgreSQL, Redis worker, GitHub, and Cloudflare Pages integration tests.
6. Harden retry, timeout, idempotency, and failure recovery.

## Documentation Scope

The following files are current project references:

- `README.md`
- `PROJECT_STATUS.md`
- `VERSION.json`
- `CONTRACT_MANIFEST.json`
- `CHANGELOG.md`
- `AUDIT_REPORT.md`

The MVP release-gate and live-runtime-smoke-plan documents remain historical versioned artifacts. They should not be interpreted as the complete current implementation snapshot.
