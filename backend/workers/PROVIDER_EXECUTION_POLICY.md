# Worker Provider Execution Policy

Version: 0.1.0
Status: Foundation / Not Runtime Wired
Owner: Worker Runtime

## Purpose

This policy defines the trusted server-owned decision that may allow provider execution in a future runtime integration patch.

The policy is not connected to deploy or redeploy handlers in this foundation.

## Configuration

```text
WORKER_PROVIDER_EXECUTION_MODE=disabled
```

Supported foundation modes:

| Mode | Policy result |
|---|---|
| `disabled` | Provider execution disabled |
| `cloudflare` | Cloudflare provider execution permitted by policy |

The default is `disabled`.

An unsupported value fails closed.

## Trust Boundary

The policy may be resolved only from the server-owned `Settings` boundary.

It does not accept:

- job payloads;
- deployment payloads;
- API request fields;
- repository configuration;
- AG-001 resolver output;
- direct environment reads inside the policy module.

## Runtime Status

```text
Settings field: implemented
Policy resolver: implemented
Default mode: disabled
Deploy/redeploy handler wiring: not added
Provider pipeline enablement: not added
Credential acquisition: not executed
Cloudflare API execution: not executed
```

## Relationship to AG-001

AG-001 resolves a future deployment-provider selection decision.

This policy controls whether the Worker Runtime is permitted to execute a provider at all.

They are separate contracts and are not integrated in this patch.

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
- does not change current Cloudflare behavior.
