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

Status: **Ready for controlled live redeploy**

The MVP architecture and core engines are substantially implemented. Concrete Cloudflare Pages orchestration, provider pipeline binding, DB-aware handlers, and trusted server-owned provider-policy handoff are present. The default server policy remains `disabled`, so provider execution stays off until an operator explicitly selects the supported `cloudflare` mode.

Engineering estimate:

```text
MVP implementation: approximately 97%
First controlled live deployment path: approximately 98%
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
| Deployment History Engine | Pipeline completion/failure persistence, retry-safe intent consumption, logs, and provider-result storage integrated through the public engine boundary |
| Worker Runtime | Durable jobs, leasing, retry, DB-aware dispatch, checkout/build handoff, credential boundary, provider pipeline binding, trusted server-owned policy resolution, dispatcher handoff, and default-disabled deploy/redeploy integration implemented |
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
- Trusted server-owned provider execution policy with default `disabled` and explicit `cloudflare` modes.
- Worker Runtime policy resolution, dispatcher transport, and deploy/redeploy binding handoff.
- Protection against job-payload-controlled provider enablement.
- Deployment History persistence for pipeline intents, provider summaries, terminal failures, and retry-safe replay handling.
- Secret-safe live-readiness validation for production configuration, PostgreSQL, Redis, deployed API routes, and explicit provider mode.

The default runtime remains provider-disabled.

Still disabled or incomplete:

- Default production configuration remains provider-disabled until controlled live validation.
- AG-001 runtime integration and future YGIT App resolver integration.
- Controlled live verification of provider-result/history persistence against PostgreSQL.
- Live Cloudflare API execution from the production worker.
- Controlled end-to-end PostgreSQL, Redis worker, and Cloudflare Pages validation.

## Verification Snapshot

Latest verified local run for the current foundation:

```text
Provider execution policy unit tests: 18 passed
Provider policy runtime integration tests: 9 passed
Handler binding regression: 5 passed
Dispatcher DB regression: 5 passed
Worker Runtime architecture tests: 4 passed
Deploy/redeploy architecture tests: 2 passed
AG-001 regression: 15 passed
Deployment History runtime tests: 8 passed
Deployment History idempotency tests: 4 passed
Live-readiness tooling tests: 8 passed
Full suite: 500 passed
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

1. Redeploy the Batch 3 commit to Coolify with provider mode `disabled`.
2. Run pre/post-redeploy PostgreSQL, Redis, API, authentication-shell, and configuration checks.
3. Connect dedicated GitHub and Cloudflare test accounts, then enable `cloudflare` mode for one controlled deployment.
4. Fix only defects demonstrated by live evidence.
5. Integrate AG-001 only when a reviewed future App Engine contract is approved.

## Documentation Scope

The following files are current project references:

- `README.md`
- `PROJECT_STATUS.md`
- `VERSION.json`
- `CONTRACT_MANIFEST.json`
- `CHANGELOG.md`
- `AUDIT_REPORT.md`

The MVP release-gate and live-runtime-smoke-plan documents remain historical versioned artifacts. They should not be interpreted as the complete current implementation snapshot.
