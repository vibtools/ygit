# YGIT Live Runtime Smoke Test Checklist v0.1.0

## Preflight

| Check | Status |
|---|---|
| API container running | Pending |
| Worker container running | Pending |
| PostgreSQL reachable | Pending |
| Redis reachable | Pending |
| Alembic head is `0012_notification_engine` | Pending |
| No secrets printed in startup logs | Pending |

## Public Runtime

| Endpoint | Expected |
|---|---|
| `GET /api/v1/platform/health` | 200 + success envelope |
| `GET /api/v1/platform/version` | 200 + version metadata |
| `GET /dashboard` | 200 + Dashboard HTML |
| `GET /admin` | 200 + Platform Operations Console HTML |

## Auth Runtime

| Check | Expected |
|---|---|
| `GET /api/v1/auth/login` | Redirect to Vib ID / Keycloak |
| `GET /api/v1/me` without session | Safe auth rejection |
| `GET /api/v1/me` with session | Safe user context |
| Logout | Session cleared |

## User Flow

| Step | Expected |
|---|---|
| Create project | `proj_...` ID |
| Validate repository | Provider `github` |
| Fetch repository metadata | `repo_...` ID |
| Run quick analysis | `analysis_...` ID |
| Reserve project domain | YGIT generated URL |
| Request deployment | `dep_...` queued |
| Read deployment | Safe deployment state |
| Read logs | Safe log envelope |
| Read notifications | No secret metadata |

## Worker Runtime

| Check | Expected |
|---|---|
| Job record persisted | `job_...` ID |
| Worker can lease job | Status transition |
| Worker failure safe | Sanitized failure |
| Worker does not call providers directly | PASS |

## Admin Runtime

| Check | Expected |
|---|---|
| Admin overview requires role | PASS |
| Queue status safe | PASS |
| System monitoring safe | PASS |
| Audit logs immutable view | PASS |
| Settings summary does not expose secrets | PASS |

## Secret Exposure

Reject immediately if any response or log contains:

```text
provider token value
OIDC client secret
session secret
database password
raw Authorization header
private key
```
