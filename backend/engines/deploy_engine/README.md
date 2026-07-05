# Deploy Engine v0.1.0

## Contract

Implements:

- Architecture Freeze v1.1
- Engine Contract Specification v1.0
- API Contract Specification v1.0
- Database Architecture Specification v1.0

## Responsibility

Deploy Engine owns deployment request validation, deployment state, queued deployment creation, redeploy request creation, cancellation, and job enqueueing.

## Boundary

Deploy Engine does **not** call GitHub Provider or Cloudflare Provider directly.

Approved path:

```text
Deploy Engine
↓
Job System / Worker
↓
Deploy Pipeline
↓
GitHub Provider / Cloudflare Provider
```

Forbidden:

```text
Deploy Engine → GitHub Provider
Deploy Engine → Cloudflare Provider
Deploy Engine → build/deploy provider logic
```

## Owned Table

```text
deployments
```

## API Routes

```text
POST /api/v1/projects/{project_id}/deploy
GET  /api/v1/deployments/{deployment_id}
POST /api/v1/deployments/{deployment_id}/redeploy
POST /api/v1/deployments/{deployment_id}/cancel
```

`GET /api/v1/deployments/{deployment_id}/logs` remains owned by Deployment History Engine and is intentionally not implemented in this release.
