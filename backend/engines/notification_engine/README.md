# YGIT Notification Engine v0.1.0

**Contract Version:** Engine Contract Specification v1.0
**Architecture Baseline:** YGIT Architecture Freeze v1.1
**Owner:** Vib Tools
**Status:** Implemented MVP engine

## Responsibility

Notification Engine owns **in-app notifications** and safe event-based notification records.

MVP notification scope is intentionally limited to:

```text
In-app notifications
Deployment success/failure notifications
Connected account warning notifications
Platform/system notices
Unread count
Mark-as-read state
```

Email, Slack, webhook, push notifications, and notification preference engines are future scope.

## Owned Table

```text
notifications
```

## Public API

External consumers may import only:

```python
from backend.engines.notification_engine.public import notification_service
```

## Boundary Rules

```text
No GitHub Provider import
No Cloudflare Provider import
No Deploy Pipeline import
No provider token access
No project mutation
No deployment mutation
No direct writes by Dashboard/Admin/Worker
```

Notification Engine may be called by approved engines, pipelines, and workers through its
public service contract only.
