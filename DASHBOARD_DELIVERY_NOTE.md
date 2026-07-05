# YGIT Dashboard v0.1.0 Delivery Note

Product: YGIT
Company: Vib Tools
Component: User Dashboard
Version: 0.1.0
Architecture Version: 1.1
API Contract: 1.0
Engine Contract: 1.0
Database Contract: 1.0

## Purpose

This release adds the MVP user dashboard shell for `ygit.net`.

The dashboard is intentionally a browser client only. It does not contain business logic, does not import backend engines, does not import providers, does not access the database, and does not bypass `/api/v1`.

## Implemented

```text
Dashboard route
Static dashboard assets
Dark-first YGIT UI
Project creation UI
Deployment action UI
Connected accounts UI
Deployment history list placeholder/client hook
Templates Beta preview
Settings MVP placeholder
Future feature preview pages
Dashboard route tests
Dashboard boundary tests
Smoke test update
Release manifest update
Version registry update
Changelog update
```

## Routes

```text
GET /dashboard
GET /dashboard/assets/{asset_path:path}
```

## Dashboard API Calls

```text
GET  /api/v1/platform/status
GET  /api/v1/projects
POST /api/v1/projects
GET  /api/v1/connected-accounts
POST /api/v1/projects/{project_id}/deploy
GET  /api/v1/projects/{project_id}/deployments
```

## Boundary Confirmation

```text
No Dashboard → Database access
No Dashboard → Provider access
No Dashboard → Engine direct import
No Dashboard → Worker direct import
No business logic inside frontend assets
Dashboard uses API contract only
```

## Live Runtime Notes

Live PostgreSQL, Redis, GitHub API, Cloudflare API, and real Cloudflare Pages deployment were not executed in the sandbox. The dashboard is ready for runtime testing against the existing API container.
