# Auth Engine Smoke Test

1. Configure `.env` from `.env.example`.
2. Ensure Keycloak client redirects include:
   - `http://localhost:8000/api/v1/auth/callback`
3. Start the local stack:

```bash
docker compose up --build
```

4. Open:

```text
http://localhost:8000/api/v1/auth/login
```

5. Expected flow:

```text
YGIT → auth.vib.tools → callback → session cookie → /dashboard
```

6. Verify current user:

```bash
curl -i --cookie "ygit_session=<value>" http://localhost:8000/api/v1/me
```

7. Verify logout:

```bash
curl -i -X POST --cookie "ygit_session=<value>" http://localhost:8000/api/v1/auth/logout
```
