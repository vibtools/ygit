# Deployment History Engine

Version: `0.1.0`

## Responsibility

Deployment History Engine owns:

- `deployment_history`
- `deployment_logs`
- deployment timeline views
- append-only deployment logs
- provider result summaries
- sanitized failure summaries
- Deployment History API read endpoints

It does **not** decide deploy readiness and does **not** call GitHub or Cloudflare providers.

## Public API

External consumers may import only:

```python
from backend.engines.deployment_history_engine.public import deployment_history_service
```

## Pipeline Integration

This engine consumes the frozen Deploy Pipeline `HistoryWriteIntent` contract:

```text
Deploy Pipeline
        ↓
HistoryWriteIntent
        ↓
Deployment History Engine public API
        ↓
deployment_history / deployment_logs
```

## Forbidden

```text
Deployment History Engine → GitHub Provider
Deployment History Engine → Cloudflare Provider
Deployment History Engine → Deploy Pipeline
Deploy Engine → deployment_logs table direct
Worker → deployment_logs table direct
```

## Security

Deployment logs and metadata are secret-safe. Metadata keys containing token, secret,
password, authorization, client_secret, refresh_token, or access_token are rejected.
