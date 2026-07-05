# YGIT Dashboard v0.1.0

This is the MVP user dashboard shell for `ygit.net`.

## Scope

The dashboard is a browser client only. It does not contain business logic, does not import engine modules, does not call providers, and does not access the database.

## Navigation

```text
Dashboard
Projects
Deployments
Connected Accounts
Templates Beta
Settings
AI Builder Coming Soon
Marketplace Coming Soon
Plugins Coming Soon
Teams Coming Soon
Analytics Coming Soon
Developer Portal Link
```

## API Boundary

The dashboard uses `/api/v1` endpoints only:

```text
GET  /api/v1/platform/status
GET  /api/v1/projects
POST /api/v1/projects
GET  /api/v1/connected-accounts
POST /api/v1/projects/{project_id}/deploy
GET  /api/v1/projects/{project_id}/deployments
```

Authentication remains owned by Auth Engine / Vib ID / Keycloak.
