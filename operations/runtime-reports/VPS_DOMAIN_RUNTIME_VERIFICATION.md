# YGIT VPS Domain Runtime Verification

**Status:** PASS
**Environment:** VPS test deployment
**Domain:** https://relayo.shop
**Repository:** https://github.com/vibtools/ygit
**Commit:** 8511519 - Update runtime report for continuous worker verification

## Verification Summary

```text
Local Docker runtime: PASS
GitHub push: PASS
Fresh GitHub clone: PASS
VPS Docker build: PASS
VPS PostgreSQL migration: PASS
VPS API runtime: PASS
VPS worker runtime: PASS
Nginx HTTPS reverse proxy: PASS
Public domain smoke: PASS
```

## VPS Runtime

```text
ygit-api-vps-test: Up
ygit-worker-vps-test: Up
ygit-postgres-vps-test: Up
ygit-redis-vps-test: Up
```

## Public Bindings

```text
80/443: nginx public HTTPS reverse proxy
127.0.0.1:8000: YGIT API only
PostgreSQL: internal Docker network only
Redis: internal Docker network only
```

## Public Route Checks

```text
https://relayo.shop/api/v1/platform/health   200
https://relayo.shop/api/v1/platform/version  200
https://relayo.shop/dashboard                200
https://relayo.shop/admin                    200
https://www.relayo.shop/api/v1/platform/health 200
http://relayo.shop/dashboard -> 301
```

## Database Migration

```text
Alembic current: 0012_notification_engine (head)
```

## Notes

```text
401 responses from protected dashboard API calls are expected without a login session.
404 responses for /, /robots.txt, /favicon.ico, and /meta.json are non-blocking for this runtime gate.
Provider live GitHub OAuth, Cloudflare OAuth, and real Cloudflare Pages deployment are not yet validated in this gate.
```

## Result

```text
FINAL_VPS_DOMAIN_RUNTIME_PASS
```
