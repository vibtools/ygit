# YGIT Frontend

This folder contains presentation-layer code only.

## Dashboard v0.1.0

The MVP dashboard lives at:

```text
frontend/dashboard/
```

It is served by FastAPI at:

```text
GET /dashboard
GET /dashboard/assets/{asset_path:path}
```

## Boundary Rule

```text
Frontend / Dashboard
↓
API Layer only
↓
Engine public APIs
```

The frontend must not import backend engines, providers, database modules, worker modules, or pipeline internals.
