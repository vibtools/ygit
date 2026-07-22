# AG-001 Deploy Provider Gate

Version: 0.1.0
Status: Foundation / Not Runtime Wired
Engine: Deploy Engine
Phase: Before deploy completion

## Purpose

AG-001 provides a stable extension decision point for selecting the deployment provider without changing the current Deploy Engine workflow.

The gate is intended to support future YGIT App-based provider extensions. The YGIT App Engine does not exist in this patch.

## Decision Flow

```text
No build_target
        ↓
Default provider: cloudflare
        ↓
Return provider decision

build_target exists
        ↓
Resolve provider
        ↓
Return provider decision
        ↓
Existing deployment flow may deploy later
```

The gate itself never performs deployment.

## Current Core Behavior

- Missing or blank `build_target` resolves to `cloudflare`.
- Explicit `cloudflare` resolves through the core decision.
- Any other `build_target` requires an injected resolver.
- Missing, failed, or blank extension resolution fails closed.
- Provider keys and build targets are normalized for deterministic matching.

## Future Extension Boundary

A future YGIT App integration may supply a resolver callable:

```text
normalized build_target
        ↓
future extension resolver
        ↓
normalized provider key
```

The resolver is injected by the caller. AG-001 does not import or depend on an App Engine.

## Architecture Boundaries

AG-001:

- belongs to the Deploy Engine;
- is a pure decision contract;
- does not call a provider;
- does not import the Deploy Pipeline;
- does not access the database;
- does not access settings or environment variables;
- does not mutate deployment state;
- does not persist deployment history;
- does not change current Deploy Engine execution;
- is not wired into runtime execution in this patch.

## Runtime Status

```text
Gate contract: implemented
Gate tests: implemented
Current Deploy Engine flow: unchanged
Current provider default: cloudflare
Runtime integration: not wired
YGIT App Engine: not created
Live provider execution: not performed
```
