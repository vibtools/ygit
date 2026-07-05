# Repository Engine v0.1.0

## Responsibility

Repository Engine owns GitHub repository URL validation, repository metadata normalization, default branch, visibility, and repository metadata snapshots.

## Contract Version

- Engine Contract: `1.0`
- API Contract: `1.0`
- Database Architecture: `1.0`
- Architecture Freeze: `1.1`

## Public API

```python
parse_repository_url(repository_url)
validate_repository_url(input_data)
fetch_repository_metadata(db, user_id, input_data)
get_repository_metadata(db, user_id, repository_id)
prepare_analysis_input(db, user_id, repository_id)
```

## API Routes

```text
POST /api/v1/repositories/validate
POST /api/v1/repositories/metadata
GET  /api/v1/repositories/{repository_id}
```

## Owned Table

```text
repository_metadata
```

## Boundary Rules

Repository Engine may call GitHub Provider. It must not call Cloudflare Provider, Deploy Pipeline, Deploy Engine mutation services, or Repository Analysis internal services.
