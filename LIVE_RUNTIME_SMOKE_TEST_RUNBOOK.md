# YGIT Live Runtime Smoke Test Runbook v0.1.0

## 1. Prepare Runtime

```bash
# On deployment host
cd /path/to/ygit

docker compose ps
docker compose logs --tail=100 ygit-api
docker compose logs --tail=100 ygit-worker
```

Confirm the API, worker, PostgreSQL, and Redis containers are healthy.

## 2. Confirm Migration Head

```bash
docker compose exec ygit-api alembic current
```

Expected head:

```text
0012_notification_engine
```

## 3. Run Public HTTP Smoke

```bash
python scripts/live_runtime_smoke_test.py \
  --base-url https://ygit.net \
  --write-report
```

This checks public-safe endpoints only.

## 4. Run Authenticated User Smoke

Preferred: set cookies through environment variables instead of shell flags.

```bash
export YGIT_SMOKE_SESSION_COOKIE='<secure-session-cookie-from-test-user>'
python scripts/live_runtime_smoke_test.py \
  --base-url https://ygit.net \
  --include-authenticated \
  --write-report
```

The script does not print cookie values.

## 5. Run Admin Smoke

```bash
export YGIT_SMOKE_ADMIN_COOKIE='<secure-session-cookie-from-admin-test-user>'
python scripts/live_runtime_smoke_test.py \
  --base-url https://ygit.net \
  --include-admin \
  --write-report
```

## 6. Review Report

Open:

```text
LIVE_RUNTIME_SMOKE_TEST_REPORT.json
```

Result meanings:

```text
PASS     baseline live runtime smoke passed
BLOCKED  one or more required live runtime checks failed
SKIPPED  optional live/auth/admin phase not executed
```

## 7. Cleanup

```bash
unset YGIT_SMOKE_SESSION_COOKIE
unset YGIT_SMOKE_ADMIN_COOKIE
```

Remove any test project, test slug, and smoke test repository connection created during manual follow-up testing.
