# Domain Engine

**Version:** 0.1.0
**Contract:** YGIT Engine Contract Specification v1.0
**Architecture:** YGIT Architecture Freeze v1.1
**Owner Table:** `domains`

## Responsibility

Domain Engine owns the MVP YGIT-generated URL boundary:

```text
Project slug
YGIT-generated URL
Subdomain availability
Reserved slug
Domain preview
```

Custom domain automation and Cloudflare DNS automation are intentionally out of scope for MVP.

## Public API

External consumers may import only:

```python
from backend.engines.domain_engine.public import domain_service
```

Internal service, repository, and models are private to this engine.

## Boundary Rules

```text
No Cloudflare Provider import
No GitHub Provider import
No custom domain automation
No DNS mutation
No direct writes from Admin Panel or Dashboard
```

Domain Engine may call Project Engine public API only for project ownership/access validation.
