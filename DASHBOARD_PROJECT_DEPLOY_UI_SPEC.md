# YGIT Backend-Readiness-Gated Deploy UI Specification

Version: 1.0
Status: Approved for Implementation
Owner: Dashboard / Deploy Engine API Integration

## Purpose

Replace the Project card's local hard lock with a server-authoritative deployment review flow.

The Dashboard must never decide deployment eligibility from Project status alone.

## User Flow

```text
Deploy or Review & Deploy
    -> GET /api/v1/projects/{project_id}/readiness
    -> deploy_ready=false
         -> show safe blocking reasons
         -> open the read-only Project details panel
         -> do not send a deployment POST
    -> deploy_ready=true
         -> POST /api/v1/projects/{project_id}/deploy
         -> refresh deployment history
```

## Button Contract

The Project card always exposes a deploy review action:

- `Deploy` when the loaded Project status suggests readiness;
- `Review & Deploy` otherwise.

The label is informational only. A fresh Deploy Engine readiness response is the authority.

The selected button is temporarily disabled while readiness is checked or a deployment is queued. This prevents duplicate submissions without permanently locking the action.

## Error Handling

The Dashboard maps known deployment errors to safe messages.

A readiness request failure must not send a deployment POST.

A blocked deployment must not mutate or delete Project data.

A deployment request rejected by the backend must preserve the Project and display the backend-safe error.

## Safety Boundary

This patch does not:

- change Deploy Engine business logic;
- bypass backend authorization or readiness validation;
- modify Repository Analysis;
- modify GitHub or Cloudflare scopes;
- change provider execution policy;
- create a database migration.

The existing Project Open action remains read-only.
