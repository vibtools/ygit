# YGIT Dashboard Project Readiness API Specification

Version: 1.0
Status: Approved for Implementation
Owner: Deploy Engine / API Layer

## Purpose

Expose the existing Deploy Engine readiness decision through a read-only authenticated Project API.

## Route

```text
GET /api/v1/projects/{project_id}/readiness
```

## Authority

The route delegates to `DeployEngineService.validate_deploy_ready`.

## Safety

This route is read-only. It must not create a deployment, enqueue a worker job, call a provider, modify Repository Analysis, or change provider execution policy.

## Follow-up Boundary

Dashboard Open and Deploy controls will be implemented in later independent patches after this API contract is committed and verified.
