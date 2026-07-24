# YGIT Backend CI Specification

**Version:** 0.1.2
**Status:** Draft for Approval
**Product:** YGIT
**Company:** Vib Tools
**Document Type:** Engineering Specification
**Applies To:** YGIT Backend Repository
**Target Branch:** `main`
**Date:** 2026-07-23

---

## 1. Purpose

This document defines the required Continuous Integration contract for the YGIT backend repository.

The Backend CI workflow will provide automated, repeatable verification of backend source quality, static analysis, test execution, architecture boundaries, smoke behavior, and release-gate readiness before changes are accepted into `main`.

The workflow is a verification mechanism only.

It must not:

- deploy YGIT;
- connect to production infrastructure;
- execute GitHub or Cloudflare provider operations;
- require production credentials;
- modify repository contents;
- modify external systems;
- enable provider execution;
- replace controlled live validation.

---

## 2. Background

The current YGIT engineering baseline has been locally validated with:

```text
Python compilation: PASS
Approved scoped Ruff gates: PASS
Repository-wide Ruff scan: NOT A GREEN BASELINE; legacy findings remain
Full-backend MyPy: NOT A GREEN BASELINE; 744 errors in 81 files at the locked head
AG-002 regression: 9 passed
Full test suite: 579 passed, 1 warning
Smoke test --skip-db: PASS
Release gate --skip-db: PASS
Architecture boundaries: PASS
Basic secret scan: PASS
```

Draft Pull Request #1 currently contains the Phase 0 baseline reconciliation and AG-002 Repository Provider Gate foundation.

The pull request is structurally valid and mergeable, but no GitHub Actions workflow currently produces a remote CI status for the branch.

This specification establishes the CI contract that must be approved before workflow implementation begins.

---

## 3. Objectives

The Backend CI workflow must provide the following guarantees:

1. Every pull request targeting `main` receives automated backend validation.
2. Every push to `main` receives the same backend validation.
3. The workflow uses the repository’s authoritative Python and dependency configuration.
4. Static analysis failures block the workflow.
5. Test failures block the workflow.
6. Smoke-test failures block the workflow.
7. Release-gate failures block the workflow.
8. CI does not require PostgreSQL, Redis, GitHub provider access, Cloudflare provider access, or production secrets.
9. Provider execution remains disabled.
10. The workflow exposes one stable status check suitable for branch protection.

---

## 4. Scope

### 4.1 Included

The initial Backend CI implementation includes:

- repository checkout;
- Python runtime setup;
- dependency installation;
- Python source compilation;
- baseline-aware Ruff validation;
- full backend test execution;
- smoke testing with database checks skipped;
- release-gate execution with database checks skipped;
- stable workflow and job naming;
- minimal GitHub token permissions;
- pull-request and `main` branch triggers.

### 4.2 Excluded

The initial Backend CI implementation does not include:

- PostgreSQL service containers;
- Redis service containers;
- database migrations against a live database;
- Cloudflare API calls;
- Cloudflare Pages deployments;
- GitHub App installation-token operations;
- live repository acquisition;
- provider execution;
- Docker image publication;
- Coolify deployment;
- production smoke testing;
- browser end-to-end testing;
- performance testing;
- load testing;
- security penetration testing;
- dependency update automation;
- release creation;
- package publication;
- branch merging;
- automatic pull-request approval.

These capabilities require separate documentation and approval.

---

## 5. Workflow Identity

The workflow must use a stable identity.

### 5.1 Workflow File

```text
.github/workflows/backend-ci.yml
```

### 5.2 Workflow Display Name

```text
Backend CI
```

### 5.3 Validation Job ID

```text
validate
```

### 5.4 Validation Job Display Name

```text
Validate
```

### 5.5 Required Status Check

The resulting stable GitHub status check must be:

```text
Backend CI / Validate
```

This name must not be changed after branch protection begins using it unless a separate migration is approved.

---

## 6. Trigger Contract

The workflow must run for the following events.

### 6.1 Pull Requests

```text
Event: pull_request
Target branch: main
```

The workflow must execute when a pull request targeting `main` is:

- opened;
- reopened;
- synchronized by a new commit;
- updated in a way that causes GitHub to rerun the pull-request workflow.

The pull-request workflow must use the `pull_request` event.

It must not use `pull_request_target` because the CI workflow does not require privileged access and must not expose elevated repository permissions to untrusted pull-request code.

### 6.2 Pushes to Main

```text
Event: push
Branch: main
```

A push to `main` must execute the same validation contract used for pull requests.

The push workflow provides post-merge verification and detects discrepancies between pull-request validation and the final `main` state.

### 6.3 Unsupported Triggers

The initial workflow must not run on:

- tags;
- scheduled intervals;
- release events;
- deployment events;
- external repository dispatch events.

Manual execution is not required by this specification.

---

## 7. Permissions

The workflow must apply least-privilege GitHub token permissions.

Required workflow permission:

```yaml
permissions:
  contents: read
```

The workflow must not request:

- `contents: write`;
- `pull-requests: write`;
- `issues: write`;
- `actions: write`;
- `deployments: write`;
- `packages: write`;
- `id-token: write`;
- `security-events: write`.

The workflow must not:

- commit files;
- push branches;
- create tags;
- create releases;
- modify pull requests;
- submit reviews;
- write comments;
- upload deployment statuses.

---

## 8. Runner Environment

The initial Backend CI workflow must run on a GitHub-hosted Ubuntu runner.

```text
Runner family: Ubuntu
Architecture: x86-64
```

The workflow must not depend on:

- Windows-specific shell behavior;
- local developer paths;
- Coolify runtime paths;
- Docker Desktop;
- user-level credentials;
- persistent runner state.

Commands must run from the repository root.

---

## 9. Python Runtime Contract

The CI Python version must match the repository’s authoritative runtime version.

The implementation must determine the version from the existing repository configuration, such as:

- project metadata;
- runtime configuration;
- container configuration;
- documented backend runtime requirements.

The workflow must not introduce an unrelated Python version.

The Python version must be explicitly pinned in the workflow after the authoritative project version is confirmed.

A floating version such as the following is forbidden:

```text
latest
3.x
```

The exact value will be taken from the approved repository runtime configuration during implementation.

---

## 10. Dependency Installation Contract

CI must use the repository’s existing authoritative dependency declaration.

The workflow must not introduce a second dependency-management system.

Dependency installation must:

1. upgrade or initialize the package installer only when required;
2. install the project’s existing backend runtime dependencies;
3. install the project’s existing development and test dependencies;
4. fail immediately when dependency resolution fails;
5. avoid production credentials;
6. avoid installing unrelated global packages.

The implementation must identify and use the current repository-authoritative source, which may include an existing:

- requirements file;
- development requirements file;
- project metadata file;
- lock file;
- editable project installation contract.

The CI implementation must not silently generate or modify a dependency lock file.

---

## 11. Validation Pipeline

All required stages must execute inside the single `Validate` job.

The required execution order is:

```text
Checkout
↓
Python Setup
↓
Dependency Installation
↓
Python Compilation
↓
Baseline-Aware Ruff
↓
Full Test Suite
↓
Smoke Test --skip-db
↓
Release Gate --skip-db
↓
CI Success
```

A failed stage must stop the job and produce a failed status.

---

## 12. Repository Checkout

The workflow must check out the exact commit associated with the event.

For pull requests, validation must correspond to the GitHub-provided pull-request revision.

For pushes, validation must correspond to the pushed `main` commit.

Checkout must not:

- rewrite commit history;
- merge additional branches manually;
- modify tracked files;
- initialize credentials for later pushes;
- persist authenticated Git configuration unnecessarily.

---

## 13. Python Compilation Check

The workflow must validate that the applicable Python source can be compiled.

The compilation command must cover the backend and operational Python source currently exercised by the project.

The implementation must use the existing project-approved compilation scope.

Compilation failure must fail the CI job.

The compilation stage is intended to detect:

- syntax errors;
- invalid Python source;
- import-time parsing failures;
- accidentally committed malformed files.

Compilation success does not replace Ruff or tests.

---

## 14. Ruff Validation

The initial Backend CI workflow must use a baseline-aware changed-file Ruff gate.

The repository currently contains legacy Ruff findings outside the approved green validation scope. Therefore, the initial CI workflow must not use the following repository-wide command as a merge requirement:

```text
ruff check .
```

A repository-wide Ruff cleanup is a separate engineering task and requires its own approved scope.

### 14.1 Eligible Files

For pull requests, the workflow must identify changed Python files between the pull-request base SHA and the validated event SHA.

For pushes to `main`, the workflow must identify changed Python files between the event's `before` SHA and the pushed SHA.

Eligible paths are:

```text
backend/**/*.py
scripts/**/*.py
```

Deleted files must not be passed to Ruff.

When no eligible Python file changed, the Ruff stage must report that no Python lint target exists and succeed without invoking Ruff.

### 14.2 Default Changed-File Gate

All eligible changed Python files, except the controlled legacy-exception files listed below, must run with the repository-authoritative configuration:

```text
python -m ruff check <changed-files>
```

The workflow must not embed a second general Ruff rule set.

### 14.3 Controlled Legacy Exceptions

The current approved baseline contains two file-specific exception contracts established by earlier validated YGIT work:

```text
backend/core/config.py
  ignore: S105

scripts/release_gate.py
  ignore: E501,I001,UP035
```

These exceptions apply only when the corresponding file changed.

No other file may inherit these ignores.

Any new exception requires separate documentation and approval.

### 14.4 Prohibited Behavior

The CI workflow must not:

```text
run ruff --fix
run repository-wide ruff check . as the initial required gate
ignore the Ruff exit code
exclude an eligible changed Python file silently
apply the controlled exceptions to unrelated files
```

A Ruff failure within the approved changed-file scope must fail the job.

## 15. MyPy Deferral and Enablement Gate

The initial Backend CI required job must not run:

```text
python -m mypy backend
```

At the locked Phase 0 head, that command deterministically reports:

```text
744 errors
81 files with errors
342 source files checked
```

This is an existing repository type-safety baseline condition. It was not introduced by the Backend CI documentation files.

Running MyPy only against a changed file is not automatically isolated because MyPy follows imported modules and can surface errors from unchanged dependency paths.

Therefore, the initial required CI workflow must treat MyPy as deferred rather than:

- suppressing errors;
- adding broad ignore flags;
- using `continue-on-error`;
- comparing against an undocumented error count;
- retrying the same deterministic failure;
- declaring the repository type-clean.

MyPy may become a required CI stage only after a separately approved type-safety baseline and remediation specification defines:

1. the authoritative module or package scope;
2. the dependency-following policy;
3. approved temporary exceptions, if any;
4. a zero-error or explicitly versioned baseline transition;
5. tests for the scope resolver;
6. rollback behavior;
7. the branch-protection migration.

Until that approval, the required Backend CI job must verify that no MyPy command is present.

The existing `[tool.mypy]` configuration remains in `pyproject.toml` and is not modified by the initial CI patch.

---

## 16. Full Test Suite

The workflow must execute the complete automated test suite using the repository’s existing pytest configuration.

The success authority is the pytest process exit code.

The workflow must not hardcode an exact expected test count such as:

```text
579 passed
```

The current count is engineering evidence, not the CI acceptance algorithm.

The current observed evidence is:

```text
579 passed, 1 warning
```

A non-zero pytest exit code must fail CI.

The existing Starlette TestClient deprecation warning is currently non-blocking. Warning policy may be tightened only through a separately approved change.

---

## 17. Smoke Test

The workflow must execute the existing smoke test with database validation disabled:

```text
scripts/smoke_test.py --skip-db
```

The smoke stage must verify the existing smoke-test contract, including applicable checks for:

- required imports;
- route registration;
- platform/version endpoint behavior;
- protected Dashboard shell behavior;
- protected Admin shell behavior;
- migration artifact presence;
- release-gate artifact presence;
- live-runtime smoke artifact presence.

Expected unauthenticated responses for protected surfaces remain valid:

```text
/dashboard → 401 Unauthorized
/admin → 401 Unauthorized
```

The smoke test must report success and exit with code `0`.

The workflow must not bypass a non-zero smoke-test exit code.

---

## 18. Release Gate

The workflow must execute the existing release gate with database validation disabled:

```text
scripts/release_gate.py --skip-db
```

The release gate must continue to validate its existing contract, including:

- required import boundaries;
- API route registry;
- runtime smoke behavior;
- migration chain;
- manifest alignment;
- architecture boundaries;
- required release artifacts;
- basic committed-secret scanning.

The release gate must report:

```text
overall_status: PASS
```

and exit successfully.

The database check is expected to remain:

```text
SKIPPED
```

for this initial CI workflow.

The release gate must not execute:

- live PostgreSQL probes;
- GitHub API integration;
- Cloudflare API integration;
- Redis worker loops;
- production URL smoke tests;
- Cloudflare Pages deployments.

---

## 19. Environment and Secret Policy

The initial Backend CI workflow must run without repository production secrets.

It must not require:

- Keycloak production credentials;
- GitHub App private keys;
- GitHub App webhook secrets;
- GitHub installation tokens;
- Cloudflare OAuth tokens;
- Cloudflare API tokens;
- PostgreSQL credentials;
- Redis credentials;
- R2 credentials;
- Coolify credentials;
- production session secrets.

The workflow may define only safe non-secret environment values required to preserve fail-closed behavior.

Provider execution must remain disabled.

The CI workflow must not enable:

```text
GitHub provider execution
Cloudflare provider execution
Worker provider execution
Webhook processing
Live deployment
```

Pull requests originating from forks must remain safe because no privileged secrets are supplied to the workflow.

---

## 20. Architecture Boundary

The Backend CI workflow is infrastructure verification.

It is not a YGIT engine.

It must not contain business logic belonging to:

- Auth Engine;
- Project Engine;
- Repository Engine;
- Repository Analysis Engine;
- Deploy Engine;
- Deployment History Engine;
- Domain Engine;
- Audit Engine;
- Platform Engine;
- Notification Engine;
- provider adapters;
- Worker Runtime.

The workflow may invoke existing project validation commands, but it must not duplicate their internal business rules in YAML.

Business and architecture validation must remain implemented in project code and tests.

---

## 21. Failure Behavior

The workflow must fail when any required stage fails.

Required failure conditions include:

- repository checkout failure;
- unsupported or unavailable Python runtime;
- dependency installation failure;
- Python compilation failure;
- baseline-aware Ruff failure;
- pytest failure;
- smoke-test failure;
- release-gate failure.

The workflow must not:

- continue after a required failed stage;
- convert failures into warnings;
- use unconditional success overrides;
- suppress command exit codes;
- mark the job successful when a required validation failed.

Forbidden patterns include:

```yaml
continue-on-error: true
```

for required validation stages.

Commands must not append shell constructs that suppress failures, such as:

```text
|| true
```

---

## 22. Required Status and Branch Protection

After the workflow is implemented and successfully validated on Draft PR #1, the following check is intended to become required for `main`:

```text
Backend CI / Validate
```

Branch-protection configuration is an administrative repository setting and is not implemented by the workflow file itself.

The required-check policy must not be enabled until:

1. the workflow exists on the pull-request branch;
2. the workflow runs successfully;
3. the resulting status name is confirmed;
4. the status remains stable;
5. the pull-request and push triggers are verified;
6. no unexpected privileged permission is present.

Once required, a failed or missing Backend CI check must block merging into `main`.

---

## 23. Pull Request #1 Integration Plan

The Backend CI foundation will be implemented on:

```text
Branch:
phase0/baseline-reconciliation-ag002

Pull Request:
#1
```

The implementation must preserve the current approved Phase 0 and AG-002 behavior.

The CI implementation must be added as a separate controlled commit.

The implementation commit must not alter:

- AG-002 resolution logic;
- Repository Engine runtime wiring;
- GitHub default-provider behavior;
- API routes;
- database models;
- migrations;
- Worker Runtime;
- Deploy Engine;
- Cloudflare behavior;
- production configuration.

After the workflow commit is pushed:

1. GitHub Actions must trigger on PR #1.
2. The exact workflow and job names must be verified.
3. All CI stages must pass.
4. PR changed files must be re-audited.
5. Review threads and comments must be inspected.
6. PR #1 must remain draft until final approval.
7. No automatic merge may occur.

---

## 24. Acceptance Criteria

The Backend CI implementation is accepted only when all of the following are true.

### 24.1 Structural Acceptance

- `.github/workflows/backend-ci.yml` exists.
- Workflow name is `Backend CI`.
- Job ID is `validate`.
- Job display name is `Validate`.
- Required status resolves to `Backend CI / Validate`.
- Workflow targets pull requests to `main`.
- Workflow targets pushes to `main`.
- Permission is limited to `contents: read`.

### 24.2 Validation Acceptance

- Python runtime setup succeeds.
- Dependency installation succeeds.
- Python compilation passes.
- the baseline-aware changed-file Ruff gate passes.
- the required workflow contains no MyPy execution step.
- Full pytest suite passes.
- Smoke test with `--skip-db` passes.
- Release gate with `--skip-db` passes.

### 24.3 Safety Acceptance

- No production secret is used.
- No database service is required.
- No Redis service is required.
- No GitHub provider call is executed.
- No Cloudflare provider call is executed.
- No deployment is executed.
- Provider execution remains disabled.
- Workflow cannot write repository contents.
- Workflow cannot merge or modify pull requests.
- No unrelated source file is changed.

### 24.4 Pull Request Acceptance

- PR #1 remains open.
- PR #1 remains draft during CI validation.
- Head SHA matches the approved feature-branch commit.
- Backend CI appears as a GitHub status check.
- The status check passes.
- No unresolved review thread exists.
- No unexpected file is present in the final diff.

---

## 25. Rollback Strategy

The initial CI foundation is isolated to the GitHub Actions workflow and directly associated documentation or tests approved for that patch.

Rollback must be possible by reverting the CI implementation commit.

A rollback must:

- remove or restore the workflow file;
- restore any directly associated CI documentation;
- leave the Phase 0 baseline reconciliation intact;
- leave AG-002 intact;
- leave production runtime unchanged;
- leave provider execution disabled;
- leave database state unchanged.

Because the CI workflow is not a runtime deployment component, rollback does not require:

- database rollback;
- migration rollback;
- Cloudflare rollback;
- Coolify redeployment.

---

## 26. Deployment Impact

The Backend CI foundation does not deploy YGIT.

Before merge:

```text
Production runtime impact: none
main branch impact: none
Coolify redeploy required: no
```

After a future merge into `main`, the workflow file changes repository automation only.

A Coolify redeploy remains unnecessary unless the merged change also modifies production runtime code or deployment configuration through a separately approved patch.

---

## 27. Implementation Restrictions

Implementation must not begin until this specification is approved.

The implementation patch must:

- use the exact workflow identity defined here;
- contain only the approved CI scope;
- use existing project validation commands;
- avoid unrelated cleanup;
- avoid dependency upgrades unless strictly required and separately approved;
- avoid production secrets;
- avoid external provider execution;
- include rollback evidence;
- include local validation evidence before push;
- remain reviewable as a separate commit.

---

## 28. Post-CI Sequence

After Backend CI is implemented and passes on PR #1, the approved sequence is:

```text
Backend CI passes
↓
Remote workflow and status verification
↓
Final PR diff audit
↓
Review-thread inspection
↓
Draft PR marked ready for review
↓
Explicit merge approval
↓
Controlled merge into main
↓
Post-merge Backend CI verification
↓
Phase 0 completion record
↓
Primary MVP blocker implementation
```

The next MVP implementation area after Phase 0 completion remains:

```text
GitHub App Installation Token
↓
Repository Metadata Acquisition
↓
Pinned Commit SHA
↓
Bounded Repository Tree Acquisition
↓
Normalized Repository Snapshot
↓
Repository Analysis
```

Backend CI does not implement any part of that repository-acquisition path.

---

## 29. Approval Gate

Approval of this document authorizes preparation of the Backend CI implementation patch only.

It does not authorize:

- merging PR #1;
- marking PR #1 ready for review;
- enabling branch protection;
- changing repository secrets;
- running live provider tests;
- deploying to Coolify;
- starting repository acquisition implementation.

Each subsequent action remains a separate controlled step.

---

## 30. Revision History

| Date | Version | Status | Summary |
|---|---|---|---|
| 2026-07-23 | 0.1.0 | Draft for Approval | Initial Backend CI contract defining triggers, permissions, validation stages, security boundaries, stable required status, PR #1 integration, acceptance criteria, and rollback requirements |
| 2026-07-23 | 0.1.1 | Draft for Approval | Corrected Ruff validation from an unverified repository-wide gate to a baseline-aware changed-Python-file contract with explicit legacy exceptions |
| 2026-07-23 | 0.1.2 | Draft for Approval | Deferred full-backend MyPy from the initial required CI job after the locked head produced 744 deterministic errors across 81 files; added a separate enablement gate |

---

## 31. Decision Summary

```text
Workflow:
Backend CI

Required status:
Backend CI / Validate

Triggers:
pull_request → main
push → main

Permissions:
contents: read

Required stages:
Python compilation
Baseline-aware changed-file Ruff
Full pytest
Smoke --skip-db
Release gate --skip-db

Production secrets:
Forbidden

Provider execution:
Disabled

Database and Redis:
Not required

Deployment:
Not allowed

Current PR:
Remain draft

Automatic merge:
Forbidden

Coolify redeploy:
Not required
```
