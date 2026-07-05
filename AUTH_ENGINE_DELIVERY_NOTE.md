# YGIT Auth Engine v0.1.0 Delivery Note

## Status

Auth Engine v0.1.0 has been implemented on top of the approved FastAPI MVP Skeleton.

## Implemented

- Auth Engine public/internal boundary
- OIDC Authorization Code Flow with PKCE
- Vib ID / Keycloak issuer configuration
- Server-side session manager
- Secure HttpOnly cookie handling
- Login callback handler
- Logout endpoint
- Current user endpoint
- Role guard dependencies
- Local user + identity SQLAlchemy models
- Auth repository owned by Auth Engine
- Alembic migration for `users` and `user_identities`
- Auth Engine tests
- Auth Engine docs and smoke-test instructions

## API Routes

```text
GET  /api/v1/auth/login
GET  /api/v1/auth/callback
POST /api/v1/auth/logout
GET  /api/v1/me
```

## Owned Tables

```text
users
user_identities
```

## Not Included

Connected Accounts Module is intentionally not implemented in this package. It remains under Auth Engine but belongs to its own phase.

## Verification

```text
python -m compileall -q backend
pytest -q
```

Result:

```text
13 passed
```
