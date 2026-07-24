# YGIT Backend CI Implementation Plan

**Version:** 0.1.2
**Status:** Draft for Approval
**Product:** YGIT
**Company:** Vib Tools
**Document Type:** Engineering Implementation Plan
**Related Specification:** `BACKEND_CI_SPECIFICATION.md`
**Target Repository:** `vibtools/ygit`
**Target Branch:** `phase0/baseline-reconciliation-ag002`
**Target Pull Request:** `#1`
**Date:** 2026-07-23

---

## 1. Purpose

This document defines the controlled implementation plan for the first YGIT Backend Continuous Integration workflow.

The plan translates the approved Backend CI specification into an exact, reviewable, rollbackable implementation sequence.

This document does not authorize implementation by itself.

Implementation may begin only after:

1. `BACKEND_CI_SPECIFICATION.md` is approved;
2. this implementation plan is approved;
3. the exact patch scope is locked;
4. the current feature branch and Pull Request #1 remain unchanged and auditable.

---

## 2. Current Repository Evidence

The implementation plan is based on the current authoritative repository state at:

```text
Repository:
vibtools/ygit

Feature branch:
phase0/baseline-reconciliation-ag002

Current approved head:
d89e0d8101acf4ba05dccfd4083bdc8f6915897f

Base branch:
main

Locked base:
b9019b79d1af3fe73d1a74769792ebb6958c4f4c
```

### 2.1 Runtime Python

The production Docker runtime uses:

```text
Python 3.12
```

The CI workflow will therefore use:

```yaml
python-version: "3.12"
```

### 2.2 Project Compatibility

The project metadata declares:

```text
requires-python = ">=3.11"
```

Static-analysis compatibility remains:

```text
Ruff target: py311
MyPy configured python_version: 3.11
Full-backend MyPy status: deferred; current locked head is not type-clean
```

This means:

- CI execution runtime will match the current production container at Python 3.12;
- Ruff will enforce the approved changed-file compatibility contract;
- the existing MyPy configuration remains recorded but is not an initial required CI gate;
- this CI patch will not change project runtime compatibility.

### 2.3 Dependency Source

The authoritative dependency source is:

```text
pyproject.toml
```

Development dependencies are defined in:

```text
[project.optional-dependencies]
dev
```

The approved installation command is:

```bash
python -m pip install -e ".[dev]"
```

No new requirements file, lock file, or package-management system will be introduced.

### 2.4 Existing Validation Commands

The existing repository commands are:

```bash
python -m compileall -q backend scripts
python -m ruff check <eligible changed Python files>
python -m ruff check --ignore S105 backend/core/config.py  # when changed
python -m ruff check --ignore E501,I001,UP035 scripts/release_gate.py  # when changed
python -m mypy backend  # diagnostic only; currently non-zero and not an initial CI gate
python -m pytest -q
python scripts/smoke_test.py --skip-db
python scripts/release_gate.py --skip-db
```

The CI workflow will invoke these existing validation boundaries.

It will not duplicate their internal business or architecture rules in YAML.

### 2.5 Safe Configuration Defaults

Current project settings provide safe local defaults for test and smoke execution.

Relevant defaults include:

```text
APP_ENV=development
GITHUB_APP_WEBHOOK_ENABLED=false
WORKER_PROVIDER_EXECUTION_MODE=disabled
```

No production credential is required for the initial CI workflow.

---

## 3. Implementation Goal

The implementation will add one GitHub Actions workflow:

```text
.github/workflows/backend-ci.yml
```

The workflow will produce one stable status:

```text
Backend CI / Validate
```

The implementation will verify:

```text
Checkout
↓
Python 3.12 setup
↓
Development dependency installation
↓
Python compilation
↓
Baseline-aware Ruff
↓
Full pytest suite
↓
Smoke test with database skipped
↓
Release gate with database skipped
```

---

## 4. Planned Repository Changes

### 4.1 Required Implementation File

```text
.github/workflows/backend-ci.yml
```

### 4.2 Approved Documentation Files

The final documentation patch may also add the approved CI documentation set:

```text
docs/ci/BACKEND_CI_SPECIFICATION.md
docs/ci/BACKEND_CI_IMPLEMENTATION_PLAN.md
```

Additional CI documentation may be included only after it is separately created and approved.

### 4.3 Forbidden Changes

The CI implementation patch must not modify:

```text
backend/engines/
backend/providers/
backend/pipelines/
backend/workers/
backend/app/
backend/db/
backend/models/
backend/migrations/
frontend/
scripts/smoke_test.py
scripts/release_gate.py
pyproject.toml
Dockerfile
docker-compose.yml
.env
.env.example
```

An exception requires a separate documented defect and explicit approval.

---

## 5. Workflow Design

### 5.1 Workflow Name

```yaml
name: Backend CI
```

### 5.2 Trigger Contract

```yaml
on:
  pull_request:
    branches:
      - main
  push:
    branches:
      - main
```

The workflow must not use:

```text
pull_request_target
workflow_run
repository_dispatch
deployment
schedule
release
```

### 5.3 Permissions

```yaml
permissions:
  contents: read
```

No write permission is allowed.

### 5.4 Concurrency

The workflow should use pull-request-aware concurrency to avoid wasting runner capacity on superseded commits.

Planned contract:

```yaml
concurrency:
  group: backend-ci-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

This provides:

- one active Backend CI run per pull request;
- cancellation of obsolete runs after a new push;
- one active run per pushed branch reference;
- no functional effect on repository contents.

### 5.5 Job Identity

```yaml
jobs:
  validate:
    name: Validate
```

The stable resulting check will be:

```text
Backend CI / Validate
```

### 5.6 Runner

```yaml
runs-on: ubuntu-latest
```

The workflow will use a GitHub-hosted Ubuntu x86-64 runner.

The Python runtime itself will be explicitly pinned to `3.12`.

### 5.7 Timeout

A bounded timeout must prevent an indefinitely blocked validation job.

Planned value:

```yaml
timeout-minutes: 20
```

The timeout may be adjusted only if real CI evidence proves the value insufficient.

---

## 6. Environment Contract

The workflow may define the following safe environment variables:

```yaml
env:
  PYTHONUTF8: "1"
  PYTHONDONTWRITEBYTECODE: "1"
  PYTHONUNBUFFERED: "1"
  APP_ENV: test
  GITHUB_APP_WEBHOOK_ENABLED: "false"
  WORKER_PROVIDER_EXECUTION_MODE: disabled
```

These values provide:

- consistent UTF-8 behavior;
- cleaner runner state;
- immediate unbuffered logs;
- explicit test mode;
- disabled GitHub webhook processing;
- disabled worker provider execution.

The workflow must not define:

```text
DATABASE_URL pointing to production
REDIS_URL pointing to production
SESSION_SECRET production value
TOKEN_ENCRYPTION_KEY production value
KEYCLOAK_CLIENT_SECRET
GITHUB_APP_PRIVATE_KEY
GITHUB_APP_WEBHOOK_SECRET
CLOUDFLARE_OAUTH_CLIENT_SECRET
CLOUDFLARE_API_TOKEN
R2 credentials
Coolify credentials
```

---

## 7. Planned Workflow Steps

### 7.1 Step 1 — Checkout

Action:

```yaml
uses: actions/checkout@v4
```

Required configuration:

```yaml
with:
  persist-credentials: false
```

Purpose:

- checkout the exact event revision;
- avoid retaining write-capable Git credentials;
- preserve a read-only workflow boundary.

### 7.2 Step 2 — Set Up Python

Action:

```yaml
uses: actions/setup-python@v5
```

Required configuration:

```yaml
with:
  python-version: "3.12"
  cache: pip
  cache-dependency-path: pyproject.toml
```

Purpose:

- match the current Docker runtime;
- cache pip downloads using the authoritative dependency metadata;
- avoid floating Python versions.

### 7.3 Step 3 — Upgrade Packaging Tooling

Command:

```bash
python -m pip install --upgrade pip
```

This step must not upgrade application dependencies outside the constraints already defined in `pyproject.toml`.

### 7.4 Step 4 — Install Project and Development Dependencies

Command:

```bash
python -m pip install -e ".[dev]"
```

Purpose:

- install the YGIT backend package;
- install pytest, pytest-asyncio, Ruff, MyPy, Bandit, and pip-audit as currently declared;
- preserve the existing package source and dependency constraints.

The initial CI validation job will not run Bandit or pip-audit unless separately approved.

They are installed because they are part of the existing `dev` dependency group.

### 7.5 Step 5 — Compile Python Sources

Command:

```bash
python -m compileall -q backend scripts
```

Purpose:

- detect invalid Python syntax;
- cover backend source and operational scripts;
- avoid compiling irrelevant virtual-environment or runner files.

### 7.6 Step 6 — Baseline-Aware Ruff

The workflow must resolve changed Python files before invoking Ruff.

#### Pull-request comparison

```text
base:
github.event.pull_request.base.sha

head:
github.sha
```

#### Push comparison

```text
base:
github.event.before

head:
github.sha
```

Checkout must use complete history for deterministic comparison:

```yaml
with:
  persist-credentials: false
  fetch-depth: 0
```

Eligible files:

```text
backend/**/*.py
scripts/**/*.py
```

The Bash step must:

1. determine the correct base SHA for the event;
2. resolve added, copied, modified, or renamed eligible Python files;
3. exclude deleted files;
4. sort and deduplicate the result;
5. separate the two controlled legacy-exception files;
6. run Ruff on every remaining eligible file;
7. succeed with an explicit message when no eligible file changed.

Default command:

```bash
python -m ruff check "${general_files[@]}"
```

Controlled exception commands:

```bash
python -m ruff check --ignore S105 backend/core/config.py
python -m ruff check --ignore E501,I001,UP035 scripts/release_gate.py
```

Each exception command runs only when its exact file changed.

Restrictions:

- no `--fix`;
- no repository-wide `ruff check .` required gate;
- no ignored exit code;
- no unapproved path exclusion;
- no propagation of file-specific ignores to other files;
- repository `pyproject.toml` remains authoritative.

### 7.7 Step 7 — Verify MyPy Deferral

The initial workflow must not execute MyPy.

Static workflow validation must reject:

```text
python -m mypy
mypy backend
continue-on-error applied to a MyPy step
an error-count comparison used to make MyPy appear green
```

Reason:

```text
Locked head:
d89e0d8101acf4ba05dccfd4083bdc8f6915897f

Observed full-backend result:
744 errors in 81 files
342 source files checked
```

A separate `Backend MyPy Baseline and Remediation Specification` is required before adding a blocking MyPy step.

The `mypy` package remains installed through the existing `dev` dependency group, but the initial workflow does not invoke it.

### 7.8 Step 8 — Full Test Suite

Command:

```bash
python -m pytest -q
```

Acceptance authority:

```text
pytest exit code
```

The workflow must not parse or hardcode:

```text
579 passed
```

The observed count remains evidence only.

### 7.9 Step 9 — Smoke Test

Command:

```bash
python scripts/smoke_test.py --skip-db
```

Expected result:

```text
success: true
database: skipped
```

The workflow must accept the existing expected protected-shell responses:

```text
/dashboard → 401
/admin → 401
```

### 7.10 Step 10 — Release Gate

Command:

```bash
python scripts/release_gate.py --skip-db
```

Expected result:

```text
overall_status: PASS
database_runtime: SKIPPED
```

The command exit code remains the CI authority.

---

## 8. Proposed Workflow Structure

The implementation will follow this structural form:

```yaml
name: Backend CI

on:
  pull_request:
    branches:
      - main
  push:
    branches:
      - main

permissions:
  contents: read

concurrency:
  group: backend-ci-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

env:
  PYTHONUTF8: "1"
  PYTHONDONTWRITEBYTECODE: "1"
  PYTHONUNBUFFERED: "1"
  APP_ENV: test
  GITHUB_APP_WEBHOOK_ENABLED: "false"
  WORKER_PROVIDER_EXECUTION_MODE: disabled

jobs:
  validate:
    name: Validate
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          persist-credentials: false
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: pyproject.toml

      - name: Upgrade pip
        run: python -m pip install --upgrade pip

      - name: Install project dependencies
        run: python -m pip install -e ".[dev]"

      - name: Compile Python sources
        run: python -m compileall -q backend scripts

      - name: Run baseline-aware Ruff
        shell: bash
        run: |
          set -euo pipefail

          if [[ "${{ github.event_name }}" == "pull_request" ]]; then
            base_sha="${{ github.event.pull_request.base.sha }}"
          else
            base_sha="${{ github.event.before }}"
          fi

          if [[ -z "$base_sha" || "$base_sha" =~ ^0+$ ]]; then
            base_sha="$(git rev-parse HEAD^)"
          fi

          mapfile -t changed_files < <(
            git diff \
              --name-only \
              --diff-filter=ACMR \
              "$base_sha" \
              "$GITHUB_SHA" \
              -- \
              'backend/**/*.py' \
              'scripts/**/*.py' |
            sort -u
          )

          general_files=()
          config_changed=false
          release_gate_changed=false

          for file in "${changed_files[@]}"; do
            case "$file" in
              backend/core/config.py)
                config_changed=true
                ;;
              scripts/release_gate.py)
                release_gate_changed=true
                ;;
              *)
                general_files+=("$file")
                ;;
            esac
          done

          if (( ${#general_files[@]} > 0 )); then
            python -m ruff check "${general_files[@]}"
          fi

          if [[ "$config_changed" == "true" ]]; then
            python -m ruff check --ignore S105 backend/core/config.py
          fi

          if [[ "$release_gate_changed" == "true" ]]; then
            python -m ruff check \
              --ignore E501,I001,UP035 \
              scripts/release_gate.py
          fi

          if (( ${#changed_files[@]} == 0 )); then
            echo "No eligible changed Python files."
          fi

      - name: Run full test suite
        run: python -m pytest -q

      - name: Run smoke test
        run: python scripts/smoke_test.py --skip-db

      - name: Run release gate
        run: python scripts/release_gate.py --skip-db
```

This block is the planned implementation structure.

The final workflow must be generated and validated through the controlled patch process rather than copied manually into the repository.

---

## 9. Local Pre-Push Validation

Before committing the workflow, the patch must verify:

### 9.1 Repository State

```text
Current branch:
phase0/baseline-reconciliation-ag002

Expected current head:
d89e0d8101acf4ba05dccfd4083bdc8f6915897f

Working tree:
clean

Remote main:
b9019b79d1af3fe73d1a74769792ebb6958c4f4c

Remote feature branch:
d89e0d8101acf4ba05dccfd4083bdc8f6915897f
```

### 9.2 Workflow Syntax

The patch must parse the YAML using a deterministic parser.

Validation must confirm:

- document is valid YAML;
- `name` is exactly `Backend CI`;
- trigger includes pull requests to `main`;
- trigger includes pushes to `main`;
- `permissions.contents` is `read`;
- job ID is `validate`;
- job display name is `Validate`;
- runner is Ubuntu;
- Python version is `3.12`;
- no `pull_request_target`;
- no write permission;
- no production secret reference;
- no provider execution enablement;
- no `continue-on-error`;
- no `|| true`;
- no MyPy execution step in the initial required job.

### 9.3 Existing Project Gates

Before the workflow commit is created, local validation must rerun:

```bash
python -m compileall -q backend scripts
python -m ruff check   backend/engines/repository_engine/repository_provider_gate.py   backend/tests/test_ag_002_repository_provider_gate.py   backend/tests/test_repository_analysis_current_state_audit.py
python -m pytest -q
python scripts/smoke_test.py --skip-db
python scripts/release_gate.py --skip-db
```

### 9.4 Exact File Scope

The initial CI implementation commit must contain only the approved files.

If the documentation bundle is not yet ready, the implementation commit scope must be:

```text
.github/workflows/backend-ci.yml
```

If all CI documents are approved and intentionally bundled, the exact scope may be:

```text
.github/workflows/backend-ci.yml
docs/ci/BACKEND_CI_SPECIFICATION.md
docs/ci/BACKEND_CI_IMPLEMENTATION_PLAN.md
<other separately approved CI documents>
```

No unrelated file is allowed.

---

## 10. Commit and Push Plan

### 10.1 Commit Strategy

The CI foundation must be a separate commit on the existing feature branch.

Planned commit message:

```text
Add backend CI validation workflow
```

If the documentation set is bundled in the same approved patch, the message may be:

```text
Add backend CI workflow and documentation
```

The exact message will be locked in the patch manifest.

### 10.2 Push Target

```text
origin/phase0/baseline-reconciliation-ag002
```

The patch must not push directly to:

```text
origin/main
```

### 10.3 Pull Request Behavior

Pushing the workflow commit must update:

```text
PR #1
```

The PR must remain:

```text
OPEN
DRAFT
NOT MERGED
AUTO-MERGE DISABLED
```

---

## 11. Remote Validation Plan

After push, GitHub must be inspected for:

### 11.1 Workflow Discovery

Expected workflow:

```text
Backend CI
```

### 11.2 Job Discovery

Expected job:

```text
Validate
```

### 11.3 Stable Check

Expected check name:

```text
Backend CI / Validate
```

### 11.4 Required Step Results

Every step must complete successfully:

```text
Check out repository
Set up Python
Upgrade pip
Install project dependencies
Compile Python sources
Run Ruff
Run full test suite
Run smoke test
Run release gate
```

### 11.5 Pull Request Verification

After CI completes, verify:

```text
PR state: OPEN
PR draft: true
Base: main
Head: phase0/baseline-reconciliation-ag002
Head SHA: exact workflow commit
Changed files: exact approved set
Review threads: none unresolved
Reviews: no requested changes
Merge performed: no
```

---

## 12. Failure Handling

### 12.1 Workflow Fails Before Commit

If local YAML or project validation fails:

- no commit is created;
- no push is performed;
- workflow and documentation changes remain available for forensic review;
- staging is reset;
- evidence is preserved;
- a corrected patch version is prepared.

### 12.2 Commit Exists but Push Fails

If the local commit succeeds but push fails:

- preserve the local commit;
- do not reset or rewrite it automatically;
- report the local commit SHA;
- preserve a recovery bundle;
- verify remote branch remains unchanged;
- prepare a push-recovery patch.

### 12.3 Workflow Pushes but CI Fails

If GitHub Actions runs and fails:

- keep PR #1 in draft;
- do not enable auto-merge;
- do not merge;
- inspect the exact failed job and logs;
- classify the failure as:
  - workflow syntax;
  - dependency installation;
  - Python compatibility;
  - lint;
  - type checking;
  - test;
  - smoke;
  - release gate;
  - GitHub-hosted runner issue;
- prepare a narrowly scoped correction;
- rerun the complete CI workflow.

### 12.4 Workflow Does Not Trigger

If the workflow file is present but no run appears:

- verify file path;
- verify workflow trigger syntax;
- verify PR base branch;
- verify GitHub Actions repository settings;
- verify actions are enabled;
- do not merge without a real remote status.

### 12.5 Check Name Differs

If GitHub produces a status other than:

```text
Backend CI / Validate
```

the implementation is not accepted for branch protection.

The workflow identity must be corrected before proceeding.

---

## 13. Rollback Plan

Rollback is performed by reverting the CI implementation commit.

Rollback must restore:

- the previous PR branch state;
- absence of the CI workflow when required;
- the prior documentation state if bundled;
- unchanged AG-002 behavior;
- unchanged runtime configuration;
- unchanged provider execution state.

Rollback does not require:

```text
Database migration
Database rollback
Redis operation
Cloudflare operation
Coolify redeploy
Production secret rotation
```

---

## 14. Security Review Checklist

Before push, verify:

- [ ] `permissions` contains only `contents: read`
- [ ] checkout credentials are not persisted
- [ ] no `pull_request_target`
- [ ] no repository secrets are referenced
- [ ] no environment secrets are embedded
- [ ] no third-party action beyond approved official actions
- [ ] no provider execution is enabled
- [ ] no deployment command exists
- [ ] no Docker registry login exists
- [ ] no artifact contains credentials
- [ ] no branch write occurs
- [ ] no PR write occurs
- [ ] no auto-merge occurs
- [ ] no shell failure suppression exists

---

## 15. Implementation Acceptance Criteria

The implementation is accepted only when:

1. the approved workflow file exists;
2. the exact workflow identity is preserved;
3. the exact job identity is preserved;
4. Python 3.12 is used;
5. project dependencies install from `pyproject.toml`;
6. compile validation passes;
7. Ruff passes;
8. MyPy execution is absent from the initial required job;
9. full pytest passes;
10. smoke test passes with database skipped;
11. release gate passes with database skipped;
12. the remote GitHub Actions run is successful;
13. the resulting check is `Backend CI / Validate`;
14. PR #1 remains draft;
15. no unexpected file is present;
16. no production secret is used;
17. no provider operation is executed;
18. no deployment is executed;
19. no merge is performed;
20. rollback evidence exists.

---

## 16. Documentation Bundle Strategy

The CI documentation set will be accumulated as downloadable Markdown artifacts.

Each approved document will later be added to the repository through one controlled documentation patch.

Current planned documentation paths:

```text
docs/ci/BACKEND_CI_SPECIFICATION.md
docs/ci/BACKEND_CI_IMPLEMENTATION_PLAN.md
```

Future approved CI documents may include:

```text
docs/ci/BACKEND_CI_TESTING_AND_ROLLBACK_SPECIFICATION.md
docs/ci/BRANCH_PROTECTION_SPECIFICATION.md
docs/ci/CI_OPERATIONS_RUNBOOK.md
```

No document will be added to the repository until the CI documentation set is complete and explicitly approved for patching.

---

## 17. Next Controlled Document

After approval of this implementation plan, the next document will be:

```text
YGIT Backend CI Testing and Rollback Specification
```

That document will define:

- test scenarios;
- expected GitHub Actions evidence;
- failure classification;
- retry policy;
- rollback execution;
- post-merge verification;
- evidence retention;
- completion criteria.

---

## 18. Approval Gate

Approval of this plan authorizes preparation of the Backend CI workflow implementation patch only after the required documentation set is complete.

It does not authorize:

- repository file changes immediately;
- pushing a workflow immediately;
- marking PR #1 ready;
- merging PR #1;
- enabling branch protection;
- changing secrets;
- executing providers;
- deploying to Coolify;
- beginning repository acquisition implementation.

---

## 19. Revision History

| Date | Version | Status | Summary |
|---|---|---|---|
| 2026-07-23 | 0.1.0 | Draft for Approval | Initial implementation plan locking Python 3.12, project dependency installation, workflow structure, local and remote validation, failure handling, rollback, security checks, and documentation bundling |
| 2026-07-23 | 0.1.1 | Draft for Approval | Replaced repository-wide Ruff execution with a deterministic changed-Python-file resolver and retained approved file-specific legacy exceptions |
| 2026-07-23 | 0.1.2 | Draft for Approval | Removed full-backend MyPy from the initial workflow plan after deterministic baseline failure; added static deferral verification and a separate future enablement requirement |

---

## 20. Decision Summary

```text
Implementation file:
.github/workflows/backend-ci.yml

Workflow:
Backend CI

Job:
Validate

Required check:
Backend CI / Validate

Runner:
ubuntu-latest

Runtime Python:
3.12

Project compatibility:
>=3.11

Dependency source:
pyproject.toml

Install command:
python -m pip install -e ".[dev]"

Validation:
compileall
Baseline-aware changed-file Ruff
MyPy deferred and absent
pytest
smoke --skip-db
release gate --skip-db

Permissions:
contents: read

Production secrets:
none

Provider execution:
disabled

Target:
existing Draft PR #1

Direct push to main:
forbidden

Automatic merge:
forbidden

Coolify redeploy:
not required
```
