# YGIT Audit Engine v0.1.0

## Responsibility

Audit Engine owns immutable audit event persistence for YGIT MVP.

It stores:

- User actions
- Admin actions
- Deployment/security-sensitive actions
- Engine events that require auditability
- Safe metadata only

## Owned Table

```text
audit_logs
```

## Public API

```text
record_event(db, input_data) -> AuditLogRecord
record_envelope(db, event, actor_type) -> AuditLogRecord
get_audit_log(db, audit_id) -> AuditLogRecord
list_audit_logs(db, filters) -> AuditLogPage
delete_audit_log_forbidden(db, audit_id) -> never allowed
```

## Boundary

Allowed:

```text
Other engines -> Audit Engine public API
Admin Surface -> Audit Engine public API
Platform Engine -> Audit Engine public API/read contract
```

Forbidden:

```text
Audit Engine -> GitHub Provider
Audit Engine -> Cloudflare Provider
Audit Engine -> Deploy Pipeline
API route -> audit repository
Admin route -> audit_logs direct mutation
```

## Immutability

Audit logs are append-only.

```text
INSERT allowed
SELECT allowed
UPDATE forbidden
DELETE forbidden
```

## Secret Safety

Audit metadata is sanitized before write. Keys containing token, secret, password, authorization, cookie, or session markers are redacted.
