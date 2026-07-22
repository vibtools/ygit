# YGIT Controlled Live Deployment Runbook

Version: 1.1
Status: Ready for Controlled Live Validation
Owner: YGIT Operations

## Purpose

This runbook moves YGIT from verified pre-live code into controlled production validation.

It does not declare production readiness before real PostgreSQL, Redis, GitHub, Cloudflare, worker, deployment-history, and public-URL evidence exists.

## Safety Rules

- Use dedicated test GitHub and Cloudflare accounts.
- Use a disposable public test repository.
- Never print OAuth secrets, session secrets, tokens, or database credentials.
- Keep `WORKER_PROVIDER_EXECUTION_MODE=disabled` during the first redeploy and infrastructure checks.
- Enable `cloudflare` only after the disabled-mode checks pass.
- Record the deployed Git commit before every redeploy.
- Revert provider mode to `disabled` immediately when provider behavior is uncertain.
- Do not integrate AG-001 during this validation. AG-001 remains reserved for future App Engine work.

## Phase 1 — Pre-Redeploy Validation

Use the `ygit-api-*` container for the post-redeploy HTTP check and the `ygit-worker-*` container for the worker-side preflight. Both containers must contain `/app/scripts/live_readiness.py` because they share the same runtime image.

Before running readiness checks:

```bash
test -f /app/scripts/live_readiness.py && echo LIVE_SCRIPT_PRESENT
test -f /app/LIVE_DEPLOYMENT_RUNBOOK.md && echo LIVE_RUNBOOK_PRESENT
```

Then run on the production application container or an equivalent environment containing the final secrets:

```bash
python scripts/live_readiness.py \
  --mode pre-redeploy \
  --expected-provider-mode disabled
```

Required result:

```text
overall_status: PASS
live_provider_execution: false
```

This checks required configuration presence, PostgreSQL `SELECT 1`, Redis `PING`, and the explicit disabled policy. It does not call GitHub or Cloudflare.

## Phase 2 — First Coolify Redeploy

Redeploy commit:

```text
<record the Batch 3-R2 runtime-image packaging commit SHA here>
```

Keep:

```text
WORKER_PROVIDER_EXECUTION_MODE=disabled
```

Confirm the API and worker use the same Git commit and production environment.

## Phase 3 — Post-Redeploy Disabled-Mode Smoke

Run:

```bash
python scripts/live_readiness.py \
  --mode post-redeploy \
  --expected-provider-mode disabled \
  --base-url https://ygit.net
```

Required evidence:

- version endpoint returns `200`;
- health endpoint returns `200`;
- unauthenticated Dashboard and Admin shells reject access;
- PostgreSQL probe passes;
- Redis probe passes;
- provider execution remains disabled.

## Phase 4 — Account and Repository Validation

Through the live UI:

1. Sign in through the configured identity provider.
2. Connect the dedicated GitHub test account.
3. Import a disposable supported repository.
4. Connect the dedicated Cloudflare test account.
5. Confirm that connection metadata is visible without exposing credentials.
6. Create a YGIT project but do not deploy while provider mode is disabled.

Record screenshots and relevant sanitized request IDs.

## Phase 5 — Controlled Provider Enablement

Change only:

```text
WORKER_PROVIDER_EXECUTION_MODE=cloudflare
```

Redeploy the API and worker so both consume the same policy.

Run:

```bash
python scripts/live_readiness.py \
  --mode post-redeploy \
  --expected-provider-mode cloudflare \
  --base-url https://ygit.net
```

A PASS only confirms configuration and infrastructure readiness. It does not prove a Cloudflare deployment.

## Phase 6 — First Real Deployment

Use the disposable repository and test Cloudflare account.

Verify:

1. one deployment job is created;
2. one worker leases the job;
3. repository checkout and build complete;
4. Cloudflare Pages provider operations complete;
5. Deployment History reaches `completed`;
6. provider project/deployment identifiers and deployment URL are stored;
7. the resulting URL loads the expected test site;
8. no secret appears in logs or API output.

## Phase 7 — Retry and Duplicate Validation

After the first successful deployment:

1. restart the worker without changing the completed deployment;
2. verify the completed-deployment guard prevents duplicate execution;
3. trigger one intentional safe failure using a disposable project configuration;
4. verify the job retry is bounded;
5. verify Deployment History logs are not duplicated;
6. correct the configuration and redeploy;
7. verify the new deployment reaches `completed`.

## Phase 8 — Release Decision

A controlled-live PASS requires evidence for all of the following:

```text
PostgreSQL: PASS
Redis worker loop: PASS
GitHub integration: PASS
Cloudflare integration: PASS
Real Pages deployment: PASS
Deployment History completion: PASS
Retry/duplicate behavior: PASS
Public deployment URL: PASS
Secret exposure scan: PASS
```

When any item fails:

- set provider mode back to `disabled`;
- redeploy;
- preserve sanitized logs and deployment IDs;
- create one targeted correction patch from the live evidence;
- repeat only the failed phase.

## Rollback

Immediate safe rollback:

```text
WORKER_PROVIDER_EXECUTION_MODE=disabled
```

Then redeploy the last known-good commit.

Do not delete user-owned GitHub repositories, Cloudflare accounts, domains, or infrastructure as part of application rollback.
