# YGIT Project Engine v0.1.0

## Status
Implementation package for Project Engine.

## Contract
Implements Project Engine section of Engine Contract Specification v1.0.

## Responsibilities

- Create project
- List projects
- View project
- Rename project
- Soft delete project
- Validate ownership
- Validate slug
- Own `projects` and `project_settings`

## Boundaries

Project Engine does not call GitHub Provider, Cloudflare Provider, Deploy Pipeline, or Deployment History tables directly.

## Public API

- `create_project`
- `list_projects`
- `get_project`
- `rename_project`
- `delete_project`
- `validate_project_access`

## API Routes

- `POST /api/v1/projects`
- `GET /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `PATCH /api/v1/projects/{project_id}`
- `DELETE /api/v1/projects/{project_id}`

## Owned Tables

- `projects`
- `project_settings`

## Migration

- `0002_project_engine_projects.py`
