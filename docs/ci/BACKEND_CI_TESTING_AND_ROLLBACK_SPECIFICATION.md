# YGIT Backend CI Testing and Rollback Specification

**Version:** 0.1.2
**Status:** Draft for Approval
**Product:** YGIT
**Company:** Vib Tools
**Document Type:** Engineering Testing and Rollback Specification
**Related Documents:**
- `BACKEND_CI_SPECIFICATION.md`
- `BACKEND_CI_IMPLEMENTATION_PLAN.md`

**Target Repository:** `vibtools/ygit`
**Target Branch:** `phase0/baseline-reconciliation-ag002`
**Target Pull Request:** `#1`
**Date:** 2026-07-23

---

## 1. Purpose

This document defines the testing, evidence, failure-handling, retry, rollback, and post-merge verification contract for the initial YGIT Backend Continuous Integration workflow.

The objective is to ensure that the Backend CI workflow is:

- functionally correct;
- deterministic;
- fail-closed;
- secure;
- reviewable;
- rollbackable;
- suitable for later branch-protection enforcement.

This document governs validation of:

```text
.github/workflows/backend-ci.yml
```

It does not authorize deployment, provider execution, branch protection, pull-request merge, or production changes.

---

## 2. Testing Scope

The testing scope includes:

- local workflow-file validation;
- local backend validation;
- GitHub Actions trigger verification;
- GitHub Actions job and step verification;
- remote status-check verification;
- failure-path verification;
- retry behavior;
- branch and pull-request safety;
- rollback preparation;
- rollback execution;
- post-merge verification;
- evidence capture and retention.

The testing scope excludes:

- live PostgreSQL validation;
- live Redis worker execution;
- GitHub App installation-token execution;
- GitHub provider API operations;
- Cloudflare OAuth operations;
- Cloudflare API operations;
- Cloudflare Pages deployments;
- Coolify deployments;
- production URL smoke testing;
- browser end-to-end testing;
- performance testing;
- load testing;
- penetration testing.

---

## 3. Authoritative Test Baseline

The current verified local baseline is:

```text
Python compilation: PASS
Approved scoped Ruff gates: PASS
Repository-wide Ruff scan: NOT A GREEN BASELINE; legacy findings remain
Full-backend MyPy: DEFERRED; locked-head diagnostic reports 744 errors in 81 files
Full pytest suite: 579 passed, 1 warning
Smoke test --skip-db: PASS
Release gate --skip-db: PASS
```

The exact test count is evidence only.

The authoritative success criteria for CI are:

```text
Process exit code = 0
Required workflow steps = successful
Workflow conclusion = success
Stable status check = Backend CI / Validate
```

The workflow must not hardcode:

```text
579 passed
```

A legitimate test-count change must not require editing the CI acceptance algorithm.

---

## 4. Test Environment

### 4.1 Local Environment

Local pre-push validation is performed from the project root on the approved feature branch.

Expected branch:

```text
phase0/baseline-reconciliation-ag002
```

Expected pre-workflow head:

```text
d89e0d8101acf4ba05dccfd4083bdc8f6915897f
```

The local environment must use:

```text
Python 3.12
UTF-8 mode
Existing project virtual environment or clean temporary environment
Existing pyproject.toml dependency source
```

### 4.2 GitHub Actions Environment

The remote workflow must use:

```text
Runner: ubuntu-latest
Python: 3.12
Architecture: x86-64
Permissions: contents: read
```

The workflow must run without production secrets.

### 4.3 Safe CI Environment Values

Approved safe environment values are:

```text
PYTHONUTF8=1
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
APP_ENV=test
GITHUB_APP_WEBHOOK_ENABLED=false
WORKER_PROVIDER_EXECUTION_MODE=disabled
```

No provider or deployment mode may be enabled during CI.

---

## 5. Test Categories

The testing contract is divided into the following categories:

1. Static workflow validation
2. Local repository validation
3. Pull-request trigger validation
4. Push trigger validation
5. Required-step validation
6. Failure-path validation
7. Security validation
8. Pull-request safety validation
9. Rollback validation
10. Post-merge verification

---

## 6. Static Workflow Validation

Before commit, the workflow file must be parsed and inspected.

### 6.1 YAML Parsing

The workflow must be valid YAML.

Validation must fail when:

- YAML syntax is invalid;
- indentation is invalid;
- duplicate structural keys produce ambiguous behavior;
- required fields are missing.

### 6.2 Workflow Identity

The following values must be exact:

```text
Workflow name: Backend CI
Job ID: validate
Job name: Validate
Expected check: Backend CI / Validate
```

### 6.3 Trigger Validation

The workflow must contain:

```text
pull_request → main
push → main
```

The workflow must not contain:

```text
pull_request_target
schedule
deployment
release
repository_dispatch
workflow_run
```

### 6.4 Permission Validation

Required:

```yaml
permissions:
  contents: read
```

Forbidden:

```text
contents: write
pull-requests: write
issues: write
actions: write
deployments: write
packages: write
id-token: write
security-events: write
```

### 6.5 Runner and Runtime Validation

Required:

```text
runs-on: ubuntu-latest
python-version: 3.12
```

Forbidden Python selectors:

```text
latest
3.x
```

### 6.6 Failure-Suppression Validation

The workflow must not contain:

```text
continue-on-error: true
|| true
exit 0 after a failed command
error-action suppression
manual success override
```

### 6.7 Secret-Reference Validation

The workflow must not reference production secrets.

Forbidden examples include:

```text
secrets.DATABASE_URL
secrets.REDIS_URL
secrets.GITHUB_APP_PRIVATE_KEY
secrets.GITHUB_APP_WEBHOOK_SECRET
secrets.CLOUDFLARE_API_TOKEN
secrets.CLOUDFLARE_OAUTH_CLIENT_SECRET
secrets.KEYCLOAK_CLIENT_SECRET
secrets.SESSION_SECRET
secrets.TOKEN_ENCRYPTION_KEY
secrets.COOLIFY_TOKEN
```

### 6.8 Action Validation

Approved external actions:

```text
actions/checkout@v4
actions/setup-python@v5
```

Any additional third-party action requires separate review and approval.

---

## 7. Local Repository Validation

Before the CI workflow is committed, the following commands must pass:

```bash
python -m compileall -q backend scripts
python -m ruff check   backend/engines/repository_engine/repository_provider_gate.py   backend/tests/test_ag_002_repository_provider_gate.py   backend/tests/test_repository_analysis_current_state_audit.py
python -m pytest -q
python scripts/smoke_test.py --skip-db
python scripts/release_gate.py --skip-db
```

### 7.1 Compilation Acceptance

Accepted when:

```text
Exit code: 0
```

Rejected when:

- any Python syntax error exists;
- any backend or script file cannot compile;
- the command scope is reduced without approval.

### 7.2 Baseline-Aware Ruff Acceptance

The initial CI Ruff gate is accepted when:

```text
Every eligible changed Python file is resolved deterministically
Every required Ruff process exits with code 0
No eligible changed Python file is silently excluded
```

Eligible files are changed `.py` files under:

```text
backend/
scripts/
```

Controlled legacy exceptions:

```text
backend/core/config.py
  --ignore S105

scripts/release_gate.py
  --ignore E501,I001,UP035
```

The gate is rejected when:

- Ruff reports a violation in the approved changed-file scope;
- the changed-file resolver omits an eligible file;
- a deleted file is passed to Ruff;
- a file-specific exception is applied to another file;
- CI uses `--fix`;
- CI uses repository-wide `ruff check .` as the initial required baseline;
- the Ruff exit code is ignored.

When no eligible Python file changed, the Ruff stage must report that condition and pass.

Repository-wide Ruff cleanup remains a separate engineering task.

### 7.3 MyPy Deferral Acceptance

Accepted when:

```text
The initial required workflow contains no MyPy command
No MyPy failure is suppressed
No MyPy error count is used as a success threshold
The existing pyproject.toml MyPy configuration remains unchanged
```

Rejected when:

- the workflow runs `python -m mypy backend`;
- the workflow uses `continue-on-error` for MyPy;
- the workflow adds broad MyPy ignore flags;
- the workflow retries a deterministic MyPy failure;
- documentation claims that the full backend is type-clean.

The locked-head diagnostic evidence is:

```text
744 errors in 81 files
342 source files checked
```

MyPy enablement requires a separate approved baseline and remediation specification.

### 7.4 Pytest Acceptance

Accepted when:

```text
Exit code: 0
```

Rejected when:

- any test fails;
- collection fails;
- test execution is skipped;
- tests are selectively excluded without approval.

The existing Starlette TestClient deprecation warning remains non-blocking.

### 7.5 Smoke Acceptance

Accepted when:

```text
success: true
database: skipped
failures: []
```

Expected protected-shell behavior:

```text
/dashboard → 401 Unauthorized
/admin → 401 Unauthorized
```

These responses are successful smoke evidence, not failures.

### 7.6 Release-Gate Acceptance

Accepted when:

```text
overall_status: PASS
database_runtime: SKIPPED
failures: []
```

The release gate must continue validating:

- import boundaries;
- route registry;
- runtime smoke;
- migration chain;
- manifest alignment;
- architecture boundaries;
- release artifacts;
- basic secret scanning.

---

## 8. Pull Request Trigger Test

The first remote test occurs after the workflow commit is pushed to:

```text
phase0/baseline-reconciliation-ag002
```

The target pull request is:

```text
PR #1
```

### 8.1 Expected Trigger

A new commit on the PR branch must produce one pull-request workflow run.

Expected event:

```text
pull_request
```

Expected base:

```text
main
```

Expected head:

```text
phase0/baseline-reconciliation-ag002
```

### 8.2 Expected Workflow

```text
Backend CI
```

### 8.3 Expected Job

```text
Validate
```

### 8.4 Expected Check

```text
Backend CI / Validate
```

### 8.5 Trigger Failure

The trigger test fails when:

- no workflow run appears;
- the event is not `pull_request`;
- the workflow targets the wrong branch;
- the check name differs;
- more than one unintended workflow runs;
- the workflow is skipped because of incorrect path filtering.

---

## 9. Push Trigger Test

The `push` trigger to `main` cannot be fully validated until an approved merge occurs.

After the future controlled merge, the same workflow must run on the resulting `main` commit.

Expected event:

```text
push
```

Expected branch:

```text
main
```

Expected workflow:

```text
Backend CI
```

Expected job:

```text
Validate
```

Expected conclusion:

```text
success
```

A pull-request success does not replace post-merge push verification.

---

## 10. Required Step Test Matrix

| Step | Command or Action | Required Result |
|---|---|---|
| Check out repository | `actions/checkout@v4` | Success |
| Set up Python | `actions/setup-python@v5` | Python 3.12 available |
| Upgrade pip | `python -m pip install --upgrade pip` | Exit code 0 |
| Install dependencies | `python -m pip install -e ".[dev]"` | Exit code 0 |
| Compile sources | `python -m compileall -q backend scripts` | Exit code 0 |
| Baseline-aware Ruff | Changed eligible Python files with controlled file-specific exceptions | Exit code 0 |
| MyPy deferral audit | No MyPy execution step in the initial required job | PASS |
| Full tests | `python -m pytest -q` | Exit code 0 |
| Smoke | `python scripts/smoke_test.py --skip-db` | PASS |
| Release gate | `python scripts/release_gate.py --skip-db` | PASS |

Any failed required step must make the job fail.

---

## 11. Concurrency Test

The workflow should define:

```text
cancel-in-progress: true
```

### 11.1 Test Procedure

1. Push workflow commit.
2. Push a follow-up correction before the first run finishes, only when a real correction is required.
3. Verify the superseded run is cancelled.
4. Verify the newest commit receives the active run.
5. Verify no successful status is copied from the older commit.

### 11.2 Acceptance

Accepted when:

- obsolete run is cancelled;
- newest commit runs fully;
- status attaches to the correct SHA;
- no branch or PR state is modified.

---

## 12. Failure-Path Validation

The initial implementation should not intentionally corrupt the main feature branch merely to prove failures.

Failure-path validation may use:

- static workflow inspection;
- a temporary disposable branch;
- a local temporary copy;
- a later controlled test branch.

Any deliberate remote failure test requires explicit approval.

### 12.1 Syntax Failure

Expected behavior:

```text
Workflow cannot start or is rejected
PR remains draft
No merge occurs
```

### 12.2 Dependency Failure

Expected behavior:

```text
Install step fails
Later steps do not run
Job conclusion: failure
```

### 12.3 Baseline-Aware Ruff Failure

Expected behavior:

```text
Changed-file Ruff step fails
Later required steps do not run
Job conclusion: failure
```

### 12.4 Unexpected MyPy Execution

Expected behavior:

```text
Static workflow validation fails
No workflow commit is accepted
PR remains draft
No merge occurs
```

The initial required workflow must not contain a MyPy execution step.

### 12.5 Test Failure

Expected behavior:

```text
Pytest step fails
Smoke and release gate do not run
Job conclusion: failure
```

### 12.6 Smoke Failure

Expected behavior:

```text
Smoke step fails
Release gate does not run
Job conclusion: failure
```

### 12.7 Release-Gate Failure

Expected behavior:

```text
Release gate fails
Job conclusion: failure
Check conclusion: failure
```

### 12.8 Runner Failure

A GitHub-hosted runner outage or infrastructure failure is not automatically classified as a code defect.

It must be classified separately and rerun only after evidence review.

---

## 13. Failure Classification

Every failed run must be classified into one of the following categories.

| Code | Category | Description |
|---|---|---|
| CI-001 | Workflow Syntax | Invalid YAML or GitHub Actions structure |
| CI-002 | Trigger | Workflow did not trigger or triggered incorrectly |
| CI-003 | Permissions | Missing or excessive token permission |
| CI-004 | Runtime Setup | Python or runner setup failure |
| CI-005 | Dependency Install | Project or dev dependency installation failure |
| CI-006 | Compilation | Python source compilation failure |
| CI-007 | Baseline-Aware Ruff | Changed-file lint failure or resolver defect |
| CI-008 | MyPy Deferral Violation | MyPy was executed or suppressed before baseline approval |
| CI-009 | Pytest | Test failure or collection failure |
| CI-010 | Smoke | Smoke-test failure |
| CI-011 | Release Gate | Release-gate failure |
| CI-012 | Secret Safety | Secret reference or exposure risk |
| CI-013 | Provider Safety | Provider execution unexpectedly enabled |
| CI-014 | GitHub Infrastructure | Runner or GitHub Actions service issue |
| CI-015 | Scope Drift | Unexpected repository file or behavior change |
| CI-016 | Status Identity | Check name differs from approved stable name |

The failure record must include:

```text
Failure code
Workflow run ID
Commit SHA
Failed step
Relevant log excerpt
Root cause
Corrective action
Retest result
```

---

## 14. Retry Policy

### 14.1 Code or Workflow Defect

Do not rerun an unchanged failing commit when evidence proves a deterministic defect.

Required action:

1. identify root cause;
2. prepare a narrow correction;
3. run local validation;
4. commit the correction;
5. push the new commit;
6. verify a new workflow run.

### 14.2 GitHub Infrastructure Failure

A rerun is allowed when evidence indicates:

- runner provisioning failure;
- GitHub-hosted service outage;
- transient package-index network failure;
- temporary action-download failure;
- non-deterministic external infrastructure problem.

### 14.3 Retry Limit

Maximum automatic or manual retry attempts for the same unchanged commit:

```text
2
```

After two failed infrastructure retries:

- stop retrying;
- preserve evidence;
- classify the issue;
- wait for a corrected environment or workflow change;
- do not merge.

### 14.4 Forbidden Retry Behavior

Do not:

- repeatedly rerun until a flaky result becomes green;
- hide a deterministic failure;
- use retry as a replacement for root-cause analysis;
- mark a failed run as acceptable;
- merge because local validation passed while remote CI remains failed.

---

### 14.5 Patch-Runner Read-Only Retry Boundary

Local patch automation may retry only transient, read-only control-plane operations.

Approved retry examples:

```text
git fetch
gh auth status
gh repo view
gh api user
gh collaborator permission lookup
gh pr view
gh pr diff --name-only
post-push read-only verification
```

Maximum attempts:

```text
3
```

Retry logic must not:

```text
copy files
edit files
remove files
stage files
commit
push
run Ruff again after a lint failure
run pytest again after a test failure
run smoke or release gate again after a deterministic failure
run or suppress MyPy
```

Commit and push are single-attempt operations. A failed push preserves the local commit and recovery bundle for a separately controlled recovery step.

## 15. Security Validation

The remote run must be inspected for security compliance.

### 15.1 Required Security Evidence

- token permission is read-only;
- checkout credentials are not persisted;
- no secret is printed;
- no secret is requested;
- no production endpoint is contacted;
- no provider operation is executed;
- no deployment operation is executed;
- no write operation is performed.

### 15.2 Log Inspection

Logs must be inspected for accidental values resembling:

```text
Private keys
Bearer tokens
OAuth secrets
API tokens
Database passwords
Redis passwords
Session secrets
Encryption keys
Webhook secrets
```

A suspected secret exposure is a release-blocking incident.

### 15.3 Fork Safety

The workflow must remain safe for pull requests from forks because:

- it uses `pull_request`;
- it has `contents: read`;
- it receives no production secrets;
- it cannot push or modify pull requests.

---

## 16. Pull Request Safety Validation

After the workflow run, verify PR #1 remains:

```text
State: OPEN
Draft: true
Merged: false
Auto-merge: disabled
Base: main
Head: phase0/baseline-reconciliation-ag002
```

Verify:

- no reviewer was added automatically;
- no comment was posted automatically;
- no label was changed automatically;
- no branch was deleted;
- no merge queue was enabled;
- no deployment was created.

A successful workflow must not mutate PR state.

---

## 17. Evidence Requirements

Every implementation and rollback stage must preserve evidence.

### 17.1 Local Evidence

Required:

```text
Git branch
Git HEAD
Remote main SHA
Remote feature SHA
Git status
Approved file list
Workflow file SHA-256
YAML validation result
Compilation result
Ruff result
MyPy deferral audit result
Pytest result
Smoke result
Release-gate result
Commit SHA
Push result
```

### 17.2 Remote Evidence

Required:

```text
PR number
PR URL
Workflow run ID
Workflow URL
Event type
Head SHA
Base branch
Workflow name
Job name
Step conclusions
Overall conclusion
Check name
Check status
Review-thread state
Changed-file list
```

### 17.3 Rollback Evidence

Required:

```text
Rollback reason
Original workflow commit SHA
Rollback commit SHA
Files reverted
Local validation result
Remote workflow result
PR state
Main state
Provider execution state
Coolify redeploy requirement
```

---

## 18. Evidence Storage

Local patch evidence should be stored under:

```text
D:\VibTools_Workspace\14_Vib.Tools\ygit\_backups\
```

Recommended directory patterns:

```text
backend_ci_implementation_<timestamp>
backend_ci_failure_<timestamp>
backend_ci_rollback_<timestamp>
backend_ci_post_merge_<timestamp>
```

Each evidence directory should contain:

```text
TRANSCRIPT.txt
GIT_STATE.txt
FILE_MANIFEST.json
VALIDATION_RESULTS.json
WORKFLOW_METADATA.json
SHA256SUMS.txt
```

Recovery bundles should be stored separately in the user’s Downloads directory.

---

## 19. Evidence Retention

Minimum retention contract:

| Evidence | Minimum Retention |
|---|---:|
| Local implementation transcript | Until Phase 0 completion |
| Recovery bundle | Until Phase 0 completion |
| Failed CI logs | Until defect closure |
| Successful PR CI evidence | Permanent project audit reference |
| Rollback evidence | Permanent project audit reference |
| Post-merge CI evidence | Permanent project audit reference |

GitHub-hosted logs may expire according to repository settings.

Critical evidence must therefore be summarized into project-owned Markdown or JSON records before expiration.

---

## 20. Rollback Triggers

Rollback is required or considered when:

- workflow blocks all valid pull requests because of a workflow defect;
- workflow uses excessive permissions;
- workflow exposes or requests a secret;
- workflow enables provider execution;
- workflow contacts production infrastructure;
- workflow check identity is unstable;
- workflow causes persistent false failures;
- workflow introduces unacceptable dependency behavior;
- workflow modifies repository or PR state;
- workflow conflicts with the approved architecture;
- post-merge CI fails because of the workflow itself;
- explicit project approval orders rollback.

Rollback is not automatically required for:

- a legitimate baseline-aware Ruff failure;
- a legitimate test failure;
- a legitimate smoke failure;
- a legitimate release-gate failure.

Those failures indicate code or project defects, not necessarily CI defects.

---

## 21. Rollback Scope

The initial rollback scope is limited to:

```text
.github/workflows/backend-ci.yml
```

If the documentation set is committed in the same patch, rollback may also include:

```text
docs/ci/BACKEND_CI_SPECIFICATION.md
docs/ci/BACKEND_CI_IMPLEMENTATION_PLAN.md
docs/ci/BACKEND_CI_TESTING_AND_ROLLBACK_SPECIFICATION.md
```

Rollback must not remove or modify:

```text
AG-002 Repository Provider Gate
Phase 0 baseline reconciliation
Repository Engine runtime behavior
Worker Runtime behavior
Deploy Engine behavior
Database models
Migrations
Provider configuration
Production configuration
```

---

## 22. Pre-Merge Rollback Procedure

When the workflow exists only on the feature branch and PR #1 is still draft:

1. verify current branch;
2. verify current head;
3. fetch remote state;
4. confirm `main` is unchanged;
5. identify the CI implementation commit;
6. create a revert commit or restore the approved pre-CI file state;
7. run local validation;
8. push the rollback commit to the feature branch;
9. verify PR #1 remains draft;
10. verify workflow removal or correction;
11. preserve rollback evidence.

A destructive history rewrite is not preferred.

The default rollback method is:

```text
revert commit
```

not:

```text
force push
```

Force push requires separate explicit approval.

---

## 23. Post-Merge Rollback Procedure

If the CI workflow has already been merged into `main`:

1. create a dedicated rollback branch from current `main`;
2. revert the CI workflow commit;
3. preserve approved non-CI changes;
4. run local validation;
5. open a controlled rollback pull request;
6. verify rollback CI behavior where possible;
7. obtain explicit approval;
8. merge the rollback PR;
9. verify the `push` workflow result on `main`;
10. record the final state.

Direct edits to `main` are forbidden.

---

## 24. Rollback Validation

A rollback is accepted only when:

- the targeted workflow behavior is removed or corrected;
- no unrelated file changes exist;
- project tests still pass;
- smoke still passes with database skipped;
- release gate still passes with database skipped;
- AG-002 remains unchanged;
- provider execution remains disabled;
- PR and branch state are correct;
- no deployment occurs;
- evidence is preserved.

---

## 25. Post-Merge Verification

After an approved future merge of PR #1:

### 25.1 Main Branch Verification

Verify:

```text
main contains the approved merge
main contains backend-ci.yml
feature branch changes match approved scope
no unexpected commit exists
```

### 25.2 Push Workflow Verification

Verify:

```text
Event: push
Branch: main
Workflow: Backend CI
Job: Validate
Check: Backend CI / Validate
Conclusion: success
```

### 25.3 Repository Verification

Verify:

- workflow file content matches approved implementation;
- documentation paths are correct;
- no production secret exists;
- no provider execution is enabled;
- no deployment action exists;
- branch protection has not changed unless separately approved.

### 25.4 Production Impact Verification

Expected:

```text
Application runtime change: none
Database change: none
Provider change: none
Deployment change: none
Coolify redeploy required: no
```

---

## 26. Branch Protection Readiness

This document does not authorize branch protection.

Backend CI is ready to become a required check only when:

1. PR-triggered workflow succeeds;
2. post-merge push workflow succeeds;
3. check name is stable;
4. workflow permissions are verified;
5. no secret is required;
6. no flaky behavior is observed;
7. rollback procedure is proven;
8. the required-check specification is separately approved.

Expected required check:

```text
Backend CI / Validate
```

---

## 27. Test Completion Criteria

Backend CI testing is complete only when:

- static workflow validation passes;
- all local project gates pass;
- PR workflow triggers;
- every required remote step succeeds;
- stable check name is confirmed;
- PR #1 remains draft and unmodified;
- no review thread is unresolved;
- security inspection passes;
- evidence bundle is complete;
- rollback plan is verified;
- no merge is performed without explicit approval.

---

## 28. Phase 0 Completion Dependency

Backend CI validation is a Phase 0 completion dependency.

The sequence remains:

```text
Backend CI documentation approved
↓
CI workflow implementation patch
↓
Local validation
↓
Push to Draft PR #1
↓
Remote CI success
↓
Final diff audit
↓
Ready-for-review decision
↓
Explicit merge approval
↓
Controlled merge
↓
Post-merge CI success
↓
Phase 0 completion record
```

The next MVP implementation area begins only after this sequence is complete.

---

## 29. Next MVP Boundary

After Phase 0 completion, the next implementation boundary remains:

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

Backend CI testing and rollback must not introduce any part of that feature.

---

## 30. Approval Gate

Approval of this document authorizes:

- preparation of a controlled Backend CI implementation patch;
- execution of local CI validation;
- push to the existing Draft PR #1;
- remote GitHub Actions inspection;
- rollback preparation if required.

Approval does not authorize:

- marking PR #1 ready for review;
- merging PR #1;
- enabling branch protection;
- changing repository secrets;
- provider execution;
- live database testing;
- Cloudflare deployment;
- Coolify redeployment;
- starting repository acquisition implementation.

---

## 31. Revision History

| Date | Version | Status | Summary |
|---|---|---|---|
| 2026-07-23 | 0.1.0 | Draft for Approval | Initial testing and rollback contract covering local validation, remote workflow verification, test matrix, failure classification, retry policy, evidence retention, rollback procedures, post-merge verification, and completion criteria |
| 2026-07-23 | 0.1.1 | Draft for Approval | Corrected Ruff acceptance and failure testing to use the baseline-aware changed-Python-file gate rather than the non-green repository-wide scope |
| 2026-07-23 | 0.1.2 | Draft for Approval | Replaced the invalid full-backend MyPy success requirement with a deferral audit based on the locked-head 744-error diagnostic and a separate future enablement gate |

---

## 32. Decision Summary

```text
Testing authority:
Process exit codes and GitHub Actions conclusions

Stable check:
Backend CI / Validate

Local tests:
compileall
Baseline-aware changed-file Ruff
MyPy deferral audit
pytest
smoke --skip-db
release gate --skip-db

Remote test:
pull_request workflow on PR #1

Post-merge test:
push workflow on main

Production secrets:
forbidden

Provider execution:
disabled

Database and Redis:
not required

Retry limit:
2 infrastructure retries per unchanged commit

Default rollback:
revert commit

Force push:
forbidden without separate approval

PR state during validation:
OPEN and DRAFT

Automatic merge:
forbidden

Coolify redeploy:
not required
```
