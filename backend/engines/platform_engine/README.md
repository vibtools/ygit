# YGIT Platform Engine v0.1.0

**Contract Version:** Engine Contract Specification v1.0
**Architecture Baseline:** YGIT Architecture Freeze v1.1
**Owner:** Vib Tools
**Status:** Implemented MVP engine

## Responsibility

Platform Engine owns platform runtime visibility and safe platform configuration state.

It provides:

```text
Health
Version
System Status
Maintenance State
Feature Flags
Platform Settings Summary
```

## Owned Tables

```text
platform_settings
feature_flags
```

## Public API

External consumers may import only:

```python
from backend.engines.platform_engine.public import platform_service
```

## Boundary Rules

```text
No provider API access
No business mutation in other engines
No direct worker mutation
No secret exposure
No raw environment value exposure
```

## MVP Limits

Runtime health checks are adapter-based. In sandbox or contract-only mode, PostgreSQL
and Redis health can be reported as `not_checked` instead of attempting live network
access. Production runtime can opt into live checks through the public service.
