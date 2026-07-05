# YGIT VPS Public UI Runtime Verification

**Version:** 0.1.0
**Status:** PASS
**Commit:** 9784711 Polish dashboard and admin UI
**Environment:** VPS test deployment
**Public Domain:** https://relayo.shop
**WWW Domain:** https://www.relayo.shop

## Scope

This report records the public HTTPS verification after the dashboard/admin UI polish deployment.

## Verified Runtime

```text
GitHub commit: 9784711
VPS project path: /opt/ygit-test
API container: ygit-api-vps-test
Worker container: ygit-worker-vps-test
PostgreSQL container: ygit-postgres-vps-test
Redis container: ygit-redis-vps-test
Nginx HTTPS reverse proxy: active
```

## Public HTTPS Checks

```text
https://relayo.shop/api/v1/platform/health              200
https://relayo.shop/api/v1/platform/version             200
https://relayo.shop/dashboard                           200
https://relayo.shop/dashboard/assets/styles.css         200
https://relayo.shop/dashboard/assets/app.js             200
https://relayo.shop/dashboard/assets/logo-mark.svg      200
https://relayo.shop/dashboard/assets/logo-full.svg      200
https://relayo.shop/dashboard/assets/favicon.svg        200
https://relayo.shop/admin                               200
https://relayo.shop/admin/assets/styles.css             200
https://relayo.shop/admin/assets/app.js                 200
https://relayo.shop/admin/assets/logo-mark.svg          200
https://relayo.shop/admin/assets/logo-full.svg          200
https://relayo.shop/admin/assets/favicon.svg            200
https://www.relayo.shop/dashboard                       200
https://www.relayo.shop/admin                           200
```

## Result

```text
Public HTTPS UI smoke: PASS
Dashboard runtime: PASS
Admin runtime: PASS
Logo assets: PASS
Favicon assets: PASS
API health/version: PASS
```

## Not Covered

```text
Real Vib ID / Keycloak login callback validation
GitHub OAuth live connection
Cloudflare OAuth live connection
Real Cloudflare Pages deployment execution
Production ygit.net domain cutover
```

