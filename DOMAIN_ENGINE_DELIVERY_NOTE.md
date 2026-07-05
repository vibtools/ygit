# YGIT Domain Engine v0.1.0 — Delivery Note

## Scope

Domain Engine v0.1.0 implements the MVP domain boundary:

```text
Project slug
YGIT-generated URL
Subdomain availability
Reserved slug
Domain preview
```

The generated URL model is:

```text
https://{slug}.ygit.net
```

## Out of Scope

```text
Custom domain automation
Cloudflare DNS automation
Cloudflare custom hostname APIs
User DNS setup
Provider mutation
```

## Routes

```text
POST /api/v1/domains/check
POST /api/v1/projects/{project_id}/domain
GET  /api/v1/projects/{project_id}/domain
DELETE /api/v1/projects/{project_id}/domain
```

## Owned Table

```text
domains
```

## Boundary

Domain Engine may validate project access through Project Engine public API. It must not import Cloudflare Provider, GitHub Provider, Deploy Pipeline, or Admin Surface internals.
