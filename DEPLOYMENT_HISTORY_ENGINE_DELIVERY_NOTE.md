# YGIT Deployment History Engine v0.1.0 Delivery Note

## Status

Created as the next implementation step after Deploy Pipeline Contract and Skeleton v0.1.0.

## Implemented

- Deployment History Engine public/internal boundary
- `deployment_history` model
- `deployment_logs` model
- `deployment_history` repository owned by Deployment History Engine
- `deployment_logs` append-only repository owned by Deployment History Engine
- Deployment History public service
- Pipeline `HistoryWriteIntent` consumer
- Deployment logs API endpoint
- Project deployments API endpoint
- Alembic migration `0007_deployment_history_engine`
- Secret-safe metadata validation
- Boundary tests
- Release manifest, version registry, changelog, smoke script update

## API Routes Added

```text
GET /api/v1/projects/{project_id}/deployments
GET /api/v1/deployments/{deployment_id}/logs
```

## Owned Tables

```text
deployment_history
deployment_logs
```

## Boundary

```text
No GitHub Provider import
No Cloudflare Provider import
No Deploy Pipeline execution import
No Deploy Engine direct write to deployment_logs
No Worker direct write to deployment_logs
```

## Pipeline Contract

This engine consumes the Deploy Pipeline `HistoryWriteIntent` object frozen in the previous package.
