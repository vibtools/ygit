# Project Engine

Owns project lifecycle, project ownership, project status, project settings, and project slug association.

## Owns

- `projects`
- `project_settings`

## Public API

Use `backend.engines.project_engine.public.project_service`.

## Forbidden

- Direct provider calls
- Direct deployment execution
- Direct writes to deployment history
- Import by other engines from `internal/`, `repository.py`, or `models.py`
