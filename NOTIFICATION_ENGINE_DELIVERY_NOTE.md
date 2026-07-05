# YGIT Notification Engine v0.1.0 — Delivery Note

## Package

```text
YGIT_Notification_Engine_v0.1.0
```

## Scope

Implemented Notification Engine as an MVP in-app notification engine.

Included:

```text
Notification Engine public/internal boundary
In-app notification creation
Event-based notification input contract
Notification list API
Unread count API
Mark notification read API
Secret-safe metadata validation
notifications SQLAlchemy model
Notification repository owned by Notification Engine
Alembic migration 0012_notification_engine_notifications
Architecture boundary tests
Route contract tests
Service tests
Smoke script update
Release manifest update
Version registry update
```

## MVP Limits

```text
Email notifications: future
Slack notifications: future
Webhook notifications: future
Push notifications: future
Notification preferences: future
Provider token access: forbidden
```

## Boundary

```text
No GitHub Provider import
No Cloudflare Provider import
No Deploy Pipeline import
No provider token access
No project mutation
No direct dashboard/admin/worker database writes
```

## Verification

```text
python -m compileall -q backend
pytest -q
python scripts/smoke_test.py --skip-db
python -m zipfile -t YGIT_Notification_Engine_v0.1.0.zip
basic secret scan
```
