# Deploy Pipeline Contract and Skeleton v0.1.0

## Status

Contract frozen for Deployment History Engine implementation.

## Responsibility

Deploy Pipeline owns the provider-facing deployment execution sequence:

```text
Deploy Engine
↓
Worker Job Runner
↓
Deploy Pipeline
↓
GitHub Provider / Cloudflare Provider
```

Deploy Pipeline is not an engine. It does not own database tables.

## v0.1.0 Scope

This release freezes:

```text
Pipeline stages
Pipeline event names
Pipeline metadata envelope
Provider summary envelope
Deployment History write intent contract
Public pipeline API
Worker handoff boundary
Secret-safe metadata validation
```

It intentionally does not execute live GitHub or Cloudflare deployment.

## Frozen Stages

```text
pending
preparing
provider_deploying
verifying
completed
failed
```

## Frozen Events

```text
deployment.started
deployment.preparing
deployment.provider_deploying
deployment.verifying
deployment.completed
deployment.failed
deployment.log_appended
```

## Deployment History Contract

Deployment History Engine should consume `HistoryWriteIntent` objects with:

```text
deployment_id
stage
history_status
event_name
log_entries
provider_summary
metadata
```

## Boundary Rules

Allowed:

```text
Deploy Engine → Deploy Pipeline public API
Worker Job Runner → Deploy Pipeline public API
Deploy Pipeline → Provider Layer
Deploy Pipeline → Deployment History Engine public API
```

Forbidden:

```text
API Route → Deploy Pipeline
Dashboard → Deploy Pipeline
Admin Route → Deploy Pipeline
Deploy Engine → GitHub Provider
Deploy Engine → Cloudflare Provider
Worker → Provider direct
```

## Public API

```python
await deploy_pipeline.execute_deployment(deployment_id)
await deploy_pipeline.execute_redeployment(deployment_id, source_deployment_id=None)
```

## Current Execution Mode

`contract_skeleton`

Provider execution is deliberately disabled in this release. The returned result contains
stage events, safe logs, provider handoff summary, and Deployment History write intents.
