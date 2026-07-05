# YGIT Admin Panel v0.1.0

This is the YGIT Platform Operations Console, not a user project-management dashboard.

## Scope

- Platform Health
- Queue Status
- System Monitoring
- Deployments
- Users
- Audit Logs
- Settings summary

## Boundary

Admin Panel is a presentation/admin surface only.

Allowed:

```text
Admin Panel → /api/v1/admin/* → Admin Surface → approved public services
```

Forbidden:

```text
Admin Panel → Database
Admin Panel → GitHub Provider
Admin Panel → Cloudflare Provider
Admin Panel → Deploy Pipeline
Admin Panel → Engine internal service
```

No `backend/engines/admin_engine` package is created in this release.
