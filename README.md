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

## GitHub Integration Architecture Lock

```text
User authentication: Vib ID / Keycloak OIDC
GitHub repository integration: GitHub App
Cloudflare account connection: Cloudflare OAuth
```

GitHub OAuth client credentials are not part of YGIT. The GitHub App webhook capability is separately controlled and remains default-disabled until an approved receiver exists. The authoritative contract is [GITHUB_APP_INTEGRATION.md](GITHUB_APP_INTEGRATION.md).

## Technology

```text
Backend: Python, FastAPI
Authentication: Keycloak / OIDC
Database: PostgreSQL
Queue/runtime coordination: Redis + Worker Runtime
Source control integration: GitHub App
Deployment provider: Cloudflare Pages
Object storage target: Cloudflare R2
```

## Core Engine Status

| Engine or component | Current state |
|---|---|
| Auth Engine | Implemented with OIDC/session boundaries |
| Connected Accounts Module | Implemented with GitHub/Cloudflare connection state, credential references, credential acquisition boundary, metadata UI, scopes, last-sync data, and disconnect/reconnect flows |
| Project Engine | Implemented |
| Repository Engine | Metadata persistence implemented; AG-002 standalone provider gate foundation added but not runtime-wired; real installation-token tree acquisition remains incomplete |
| Repository Analysis Engine | Quick-analysis contract implemented; real repository tree input, deep execution, and Project reattachment remain incomplete |
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

### AG-001 — Deploy Provider Gate

AG-001 remains a standalone Deploy Engine extension contract.

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

AG-001 is not runtime-wired. Current Cloudflare deployment behavior remains unchanged.

### AG-002 — Repository Provider Gate

AG-002 is a standalone Repository Engine decision contract.

```text
repository provider missing
        ↓
github

repository provider present
        ↓
selected provider
```

GitHub remains the current default. AG-002 does not call providers, access the database, change repository parsing or metadata acquisition, add routes or migrations, or wire future providers into runtime. GitLab, Bitbucket, Azure DevOps, and other providers remain future work requiring separate architecture approval.

See [AG-002 Repository Provider Gate](docs/architecture/AG_002_REPOSITORY_PROVIDER_GATE.md).

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
- Runtime image packaging for the live-readiness script and controlled deployment runbook in both API and worker containers.

The default runtime remains provider-disabled.

Still disabled or incomplete:

- Default production configuration remains provider-disabled until controlled live validation.
- AG-001 runtime integration and future YGIT App resolver integration.
- AG-002 runtime integration and future non-GitHub repository provider adapters.
- Controlled live verification of provider-result/history persistence against PostgreSQL.
- Live Cloudflare API execution from the production worker.
- Controlled end-to-end PostgreSQL, Redis worker, and Cloudflare Pages validation.

## Verification Snapshot

Latest verified local run for the current foundation:

```text
Running baseline lock: PASS at b9019b79d1af3fe73d1a74769792ebb6958c4f4c
Provider execution policy unit tests: 18 passed
Provider policy runtime integration tests: 9 passed
Handler binding regression: 5 passed
Dispatcher DB regression: 5 passed
Worker Runtime architecture tests: 4 passed
Deploy/redeploy architecture tests: 2 passed
AG-001 regression: 15 passed
AG-002 regression: 9 passed
Deployment History runtime tests: 8 passed
Deployment History idempotency tests: 4 passed
Live-readiness tooling tests: 18 passed
Runtime image packaging tests: 4 passed
Full suite: 579 passed, 1 warning
Smoke test with database skipped: PASS
Release gate with database skipped: PASS
Backend CI workflow: IMPLEMENTED at .github/workflows/backend-ci.yml
Backend CI final-head pull-request validation: SUCCESS — run 30096212556 / job 89490793519
Backend CI post-merge main validation: SUCCESS — run 30106115262 / job 89523839117
Phase 0 merge commit: 6e44866de9ec3a3a745777afc12276f903259709
Phase 0 completion record: COMPLETE
Branch-protection required-check enablement: NOT AUTHORIZED
Live PostgreSQL: NOT EXECUTED
Live Redis worker loop: NOT EXECUTED
GitHub API integration: NOT EXECUTED
Cloudflare API integration: NOT EXECUTED
Real Cloudflare Pages deployment: NOT EXECUTED
```

The recurring `StarletteDeprecationWarning` is non-blocking and relates to the existing test-client dependency combination.

## Backend CI State

Backend CI is implemented, PR-verified, merged through PR #1, and push-verified on the resulting `main` merge commit.

```text
Workflow file: .github/workflows/backend-ci.yml
Workflow: Backend CI
Job: Validate
Stable status: Backend CI / Validate
Pull-request validation: SUCCESS
Workflow commit: 7f383ba6b0c17b92de9a27e0abe4cbeb8adbbac2
Final-head PR run ID: 30096212556
Final-head PR job ID: 89490793519
Merge commit: 6e44866de9ec3a3a745777afc12276f903259709
Post-merge push run ID: 30106115262
Post-merge push job ID: 89523839117
Permissions: contents read
Python: 3.12
MyPy required gate: DEFERRED
Provider execution: DISABLED
Production secrets: NOT USED
Post-merge push validation: SUCCESS
Branch protection: NOT ENABLED
```

Backend CI is a verification mechanism only. It does not execute providers, contact production infrastructure, modify repository state, deploy YGIT, or replace controlled live validation.

## Local Verification

```bash
python -m pytest -q
python scripts/smoke_test.py --skip-db
python scripts/release_gate.py --skip-db
```

Live checks must use the controlled runtime runbook and dedicated test accounts.

## Immediate Critical Path

1. Redeploy the verified current `main` branch and validate the Dashboard compact provider cards, Project Open flow, and backend-readiness-gated Deploy flow.
2. Reduce the GitHub App to the approved minimum permissions, reconnect the controlled installation, and verify captured permission scopes.
3. Implement GitHub App installation-token repository acquisition with a pinned commit SHA and normalized real file-tree snapshot.
4. Implement the approved deep-analysis execution and Project reattachment boundaries.
5. Confirm `deploy_ready=true` from real repository evidence and execute one controlled Cloudflare Pages deployment.
6. Resolve only defects demonstrated by live evidence.
7. Keep AG-001 and AG-002 runtime integration deferred until separate post-MVP architecture approval.

## Documentation Scope

The following files are current project references:

- `README.md`
- `PROJECT_STATUS.md`
- `VERSION.json`
- `CONTRACT_MANIFEST.json`
- `CHANGELOG.md`
- `AUDIT_REPORT.md`
- `REPOSITORY_ANALYSIS_CURRENT_STATE_AUDIT.md`
- `docs/architecture/AG_002_REPOSITORY_PROVIDER_GATE.md`
- `docs/phase0/PHASE0_COMPLETION_RECORD.md`
- `docs/ci/BACKEND_CI_SPECIFICATION.md`
- `docs/ci/BACKEND_CI_IMPLEMENTATION_PLAN.md`
- `docs/ci/BACKEND_CI_TESTING_AND_ROLLBACK_SPECIFICATION.md`
- `.github/workflows/backend-ci.yml`

The MVP release-gate and live-runtime-smoke-plan documents remain historical versioned artifacts. They should not be interpreted as the complete current implementation snapshot.

---

<!-- YGIT-UI-V2-DOCS:START -->
## YGIT UI V2

YGIT UI V2 is currently in the documentation-freeze phase. It will be developed as an isolated React frontend and migrated page by page while the existing dashboard remains available.

- [UI V2 documentation index](./docs/ui-v2/README.md)
- [Master Architecture](./docs/ui-v2/UI_V2_MASTER_ARCHITECTURE.md)
- [API Architecture](./docs/ui-v2/UI_V2_API_ARCHITECTURE.md)
- [Design System Freeze](./docs/ui-v2/UI_V2_DESIGN_SYSTEM_FREEZE.md)
- [Migration Plan](./docs/ui-v2/UI_V2_MIGRATION_PLAN.md)
- [Testing and Release Gate](./docs/ui-v2/UI_V2_TESTING_AND_RELEASE_GATE.md)
- [Decision Log](./docs/ui-v2/UI_V2_DECISION_LOG.md)

> UI V2 implementation has not started. The existing YGIT backend, engines, providers, workers, authentication, and production dashboard remain unchanged.
<!-- YGIT-UI-V2-DOCS:END -->
