# Worker Provider Execution Policy

Version: 0.2.0
Status: Runtime Handoff / Default Disabled
Owner: Worker Runtime

## Purpose

This policy defines the trusted server-owned decision that controls whether Worker Runtime may enable provider execution.

The decision is resolved by Worker Runtime, passed through Job Dispatcher as trusted runtime context, and consumed by deploy/redeploy handlers only as a validated policy object.

## Configuration

```text
WORKER_PROVIDER_EXECUTION_MODE=disabled
```

Supported modes:

| Mode | Policy result |
|---|---|
| `disabled` | Provider execution remains disabled |
| `cloudflare` | Cloudflare provider binding may be enabled |

The default is `disabled`.

An unsupported value or an inconsistent policy object fails closed.

## Trust Boundary

The policy is resolved only from the server-owned `Settings` boundary.

It does not accept:

- job payloads;
- deployment payloads;
- API request fields;
- repository configuration;
- AG-001 resolver output;
- direct environment reads inside the policy module.

Worker Runtime owns policy resolution. Job Dispatcher transports the immutable decision. Handlers do not call `get_settings()` and do not resolve policy from payload data.

## Runtime Handoff

```text
Server Settings
        ↓
Worker Runtime resolves policy
        ↓
Job Dispatcher passes policy keyword
        ↓
Deploy/Redeploy handler validates policy
        ↓
Neutral provider binding receives enabled=False/True
```

Default configuration produces `enabled=False`.

The explicit `cloudflare` mode permits the existing Cloudflare binding path. Setting this mode in a deployed environment may allow credential acquisition and provider execution when the deployment context is complete.

## Verification Status

```text
Settings field: implemented
Policy resolver: implemented
Policy invariant validation: implemented
Worker Runtime policy resolution: implemented
Dispatcher policy handoff: implemented
Deploy/redeploy handler handoff: implemented
Default mode: disabled
Job payload control: blocked
Live credential acquisition in verification: not executed
Live Cloudflare API execution in verification: not executed
```

## Relationship to AG-001

AG-001 resolves a future deployment-provider selection decision.

This policy controls whether Worker Runtime is permitted to execute a provider at all.

They remain separate contracts. AG-001 is not consumed by this policy handoff and remains unused by runtime execution.

## Architecture Boundaries

The policy module:

- belongs to Worker Runtime;
- does not import provider implementations;
- does not import Deploy Pipeline;
- does not access the database;
- does not read environment variables directly;
- does not mutate deployment state;
- does not persist history;
- does not create a YGIT App Engine;
- does not change the default Cloudflare-disabled behavior.
