# Connected Accounts Module

**Owner:** Auth Engine / Connected Accounts Module
**Version:** 0.1.0
**Contract:** Engine Contract Specification v1.0
**Architecture:** YGIT Architecture Freeze v1.1

## Responsibility

Connected Accounts Module owns GitHub and Cloudflare connection records, provider account metadata, safe token references, connection status, disconnect flow, and provider health checks.

## Scope Implemented

- GitHub connection state
- Cloudflare connection state
- Provider allow-list validation
- Safe token reference creation
- No raw token returned by APIs
- `connected_accounts` SQLAlchemy model
- `connected_accounts` repository
- Public service boundary
- Internal service boundary
- API routes
- Alembic migration
- Tests

## Public API

```python
connected_accounts_service.get_connected_accounts(...)
connected_accounts_service.connect_provider(...)
connected_accounts_service.handle_provider_callback(...)
connected_accounts_service.disconnect_provider(...)
connected_accounts_service.require_provider_connected(...)
connected_accounts_service.check_provider_health(...)
connected_accounts_service.mark_provider_error(...)
```

## Route Contract

```text
GET    /api/v1/connected-accounts
GET    /api/v1/connected-accounts/{provider}/connect
GET    /api/v1/connected-accounts/{provider}/callback
DELETE /api/v1/connected-accounts/{provider}
```

## Security Rules

- Raw GitHub token values are never returned.
- Raw Cloudflare token values are never returned.
- Admin-visible responses must only expose provider state and safe metadata.
- Token storage uses safe token references in this module baseline.
- Provider modules remain external API wrappers only.
