# Auth Engine

**Version:** 0.1.0
**Contract:** YGIT Engine Contract Specification v1.0
**Status:** Implementation baseline

## Responsibility

Auth Engine owns:

- Vib ID / Keycloak OIDC login flow
- Authorization Code Flow with PKCE
- Server-side session handling
- Secure HttpOnly cookie handling
- Current user resolution
- Role guards
- Local user and identity synchronization

## Public API

Other layers may import only:

```python
from backend.engines.auth_engine.public import auth_service
```

Internal modules under `backend.engines.auth_engine.internal` are private to this engine.

## Owned Tables

- `users`
- `user_identities`

## Security Rules

- No password handling inside YGIT
- No access token returned to frontend
- No localStorage token model
- No plaintext provider token storage
- Server-side session only
- Secure HttpOnly cookie in production
