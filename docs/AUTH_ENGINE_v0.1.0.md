# YGIT Auth Engine v0.1.0

**Status:** Implementation baseline
**Engine Contract:** v1.0
**API Contract:** v1.0
**Database Contract:** v1.0

## Scope

Implemented:

- `GET /api/v1/auth/login`
- `GET /api/v1/auth/callback`
- `POST /api/v1/auth/logout`
- `GET /api/v1/me`
- Auth Engine public/internal boundary
- OIDC Authorization Code Flow with PKCE
- Server-side session manager
- Secure HttpOnly cookie handling
- Local user identity sync
- User/identity SQLAlchemy models
- Initial Alembic migration for `users` and `user_identities`
- Role guard dependencies

## Explicitly Not Included

Connected Accounts implementation is not included in this phase. It remains under Auth Engine but is scheduled for its own implementation phase.

## Contract Boundaries

External layers may import only:

```python
from backend.engines.auth_engine.public import auth_service
```

No route, worker, or other engine may import:

```python
backend.engines.auth_engine.internal.*
backend.engines.auth_engine.repository
backend.engines.auth_engine.models
```

except Auth Engine tests and migrations.

## Security Notes

- Access tokens are stored server-side only.
- Frontend receives only a Secure/HttpOnly session cookie.
- `/me` returns safe user identity only.
- No password is handled by YGIT.
- Production requires HTTPS, secure cookies, and non-default secrets.
