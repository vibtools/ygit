# YGIT UI V2 Testing and Release Gate Specification

**Document ID:** YGIT-UIV2-TEST-001<br>
**Version:** 0.1.0<br>
**Status:** Draft for Review<br>
**Owner:** YGIT Platform<br>
**Product:** YGIT<br>
**Company:** Vib Tools<br>
**Depends On:**<br>
- `UI_V2_MASTER_ARCHITECTURE.md`<br>
- `UI_V2_API_ARCHITECTURE.md`<br>
- `UI_V2_DESIGN_SYSTEM_FREEZE.md`<br>
- `UI_V2_MIGRATION_PLAN.md`<br>

**Last Updated:** 2026-07-22<br>

---

## Revision History

| Version | Date | Status | Summary |
|---|---|---|---|
| 0.1.0 | 2026-07-22 | Draft for Review | Initial UI V2 testing and release gate specification |

---

## 1. Purpose

This document defines the mandatory testing, validation, release, deployment, rollback, and evidence requirements for YGIT UI V2.

Its purpose is to ensure that UI changes remain isolated from YGIT engines, provider integrations, workers, database behavior, Redis behavior, authentication, and production deployment execution.

No UI V2 phase is considered complete only because:

- the page looks correct locally;
- TypeScript compiles;
- a developer manually clicked through the interface;
- a unit test passes;
- a production deployment succeeds.

Every change must pass the appropriate layered gate defined in this document.

---

## 2. Testing Philosophy

The official testing philosophy is:

```text
Source correctness
    ↓
Type correctness
    ↓
Component correctness
    ↓
API contract correctness
    ↓
Route and authentication correctness
    ↓
Browser behavior correctness
    ↓
Responsive correctness
    ↓
Visual correctness
    ↓
Build and asset correctness
    ↓
Release safety
    ↓
Production verification
```

The following rule is mandatory:

> Production must never be the first environment where a UI layout, route, or interaction is visually validated.

---

## 3. Scope

### 3.1 In Scope

This specification defines:

- test layers;
- static validation;
- TypeScript validation;
- linting and formatting;
- unit testing;
- component testing;
- API client testing;
- API contract testing;
- route testing;
- authentication testing;
- browser testing;
- responsive testing;
- visual regression testing;
- accessibility testing;
- build validation;
- asset integrity validation;
- release classification;
- staging and preview gates;
- production cutover gates;
- rollback criteria;
- evidence requirements;
- Git safety;
- retry rules;
- test data policy;
- provider execution boundaries;
- post-deployment verification.

### 3.2 Out of Scope

This document does not define:

- implementation code;
- final CI vendor;
- cloud build provider;
- monitoring vendor;
- production analytics platform;
- public SLA;
- engine-specific test strategy;
- provider-specific live execution strategy;
- database migration testing outside UI-related API compatibility;
- worker job execution testing outside UI request boundaries.

---

## 4. Release Gate Principles

Every release gate must be:

```text
Deterministic
Repeatable
Scoped
Evidence-based
Fail-closed
Rollback-aware
Non-destructive by default
```

A failed gate must block release.

A warning may be accepted only when:

- it is documented;
- it is not security-related;
- it is not deployment-safety-related;
- it is not an accessibility blocker;
- it is not an asset-integrity failure;
- the product owner and engineering owner explicitly accept it.

---

## 5. Test Environments

YGIT UI V2 uses four logical environments.

### 5.1 Local Development

Purpose:

- rapid implementation;
- TypeScript checks;
- component tests;
- local browser testing;
- API mocking;
- responsive review.

Production provider execution is prohibited.

### 5.2 Local Integrated Environment

Purpose:

- UI V2 with local FastAPI;
- real authentication simulation where available;
- real local API contracts;
- route and session testing;
- OpenAPI contract validation.

Production provider execution is prohibited.

### 5.3 Preview or Staging

Purpose:

- authenticated `/dashboard-v2` validation;
- real deployed static assets;
- real backend route integration;
- full browser matrix;
- visual approval;
- rollback-route verification;
- safe production-like behavior.

Real provider execution remains prohibited unless separately approved.

### 5.4 Production

Purpose:

- final route and asset verification;
- authentication verification;
- health and readiness verification;
- post-cutover smoke validation.

Production verification must not create a real deployment unless an explicit live deployment test is separately approved.

---

## 6. Test Layer Matrix

| Layer | Purpose | Mandatory |
|---|---|---|
| Documentation validation | Confirm approved architecture and scope | Yes |
| Source-scope validation | Prevent unrelated changes | Yes |
| Formatting | Maintain source consistency | Yes |
| Linting | Detect unsafe or invalid patterns | Yes |
| TypeScript | Validate static types | Yes |
| Unit tests | Validate pure functions and adapters | Yes |
| Component tests | Validate reusable UI behavior | Yes |
| API client tests | Validate transport behavior | Yes |
| API contract tests | Validate FastAPI/OpenAPI compatibility | Yes |
| Route tests | Validate navigation and deep links | Yes |
| Authentication tests | Validate protected routes and session behavior | Yes |
| Browser tests | Validate real browser behavior | Yes |
| Responsive tests | Validate supported viewport range | Yes |
| Accessibility tests | Validate keyboard and semantic behavior | Yes |
| Visual regression | Detect unintended appearance changes | Yes for frozen pages |
| Build tests | Validate production build | Yes |
| Asset integrity | Validate hashed assets and build identity | Yes |
| Full backend regression | Detect unintended backend impact | Yes when repository-integrated |
| Release gate | Validate commit, push, remote, clean state | Yes |
| Production smoke | Validate deployed target | Yes for release |

---

## 7. Approved Testing Tools

The initial approved tool categories are:

| Test Area | Approved Tool |
|---|---|
| TypeScript | TypeScript compiler |
| Linting | ESLint |
| Formatting | Prettier |
| Unit/component tests | Vitest and React Testing Library |
| Browser/E2E tests | Playwright |
| Accessibility automation | Playwright accessibility checks and approved accessibility tooling |
| API contract source | FastAPI OpenAPI |
| Backend regression | Existing Python test suite |
| Build | Vite production build |

A replacement tool requires a Decision Log entry and approval.

---

## 8. Test Directory Structure

The recommended structure is:

```text
frontend-v2/
├── src/
│   ├── api/
│   │   └── __tests__/
│   ├── components/
│   │   └── __tests__/
│   ├── features/
│   │   └── <feature>/
│   │       └── __tests__/
│   └── pages/
│       └── <page>/
│           └── __tests__/
├── tests/
│   ├── browser/
│   ├── accessibility/
│   ├── visual/
│   ├── contract/
│   ├── fixtures/
│   └── helpers/
└── playwright.config.ts
```

Test files must remain close to their owner unless they are cross-application browser or contract tests.

---

## 9. Documentation Gate

Before implementation begins, the following documents must exist and have the required status:

```text
UI_V2_MASTER_ARCHITECTURE.md
UI_V2_API_ARCHITECTURE.md
UI_V2_DESIGN_SYSTEM_FREEZE.md
UI_V2_MIGRATION_PLAN.md
UI_V2_TESTING_AND_RELEASE_GATE.md
UI_V2_DECISION_LOG.md
docs/ui-v2/README.md
```

Minimum status before implementation:

| Document | Required Status |
|---|---|
| Master Architecture | Approved |
| API Architecture | Approved |
| Design System | Frozen |
| Migration Plan | Approved |
| Testing and Release Gate | Approved |
| Decision Log | Active |
| UI V2 README | Active |

A missing or unapproved document blocks implementation.

---

## 10. Source-Scope Gate

Every UI V2 change must declare an exact file scope before mutation.

Required checks:

```text
Expected Git HEAD
Expected remote HEAD
Clean worktree
Approved source files
Expected file hashes or source markers where necessary
No untracked generated secrets
No unrelated modifications
```

After mutation:

```text
Exact dirty file set
Exact staged file set
No unrelated files
No generated build output committed unless approved
No secret files
No environment files
```

Unexpected scope is an immediate failure.

---

## 11. Formatting Gate

All changed UI V2 source files must pass formatting validation.

Formatting must cover:

```text
TypeScript
TSX
CSS modules
JSON
Markdown
configuration files
```

Formatting failure blocks commit.

Formatting tools must not rewrite unrelated files.

---

## 12. Lint Gate

Linting must detect at minimum:

- invalid React hook usage;
- unused imports;
- unsafe `any`;
- floating promises;
- direct raw API calls from pages;
- inaccessible interactive elements;
- duplicate imports;
- invalid dependency arrays;
- unsafe HTML rendering;
- forbidden browser storage usage for secrets;
- direct provider URLs;
- missing accessible labels where detectable.

The following patterns must be treated as violations:

```text
fetch() inside page component
dangerouslySetInnerHTML without approved exception
window.localStorage for credentials
hardcoded production API domain
direct api.github.com request
direct api.cloudflare.com request
unbounded setInterval
ignored promise from mutation
```

---

## 13. TypeScript Gate

UI V2 must compile in strict mode.

Required baseline:

```text
strict: true
noImplicitAny: true
noUncheckedIndexedAccess: true
useUnknownInCatchVariables: true
noFallthroughCasesInSwitch: true
```

Exact compiler settings may be adjusted only through approved implementation documentation.

TypeScript errors are deterministic failures and must never be automatically retried.

---

## 14. Unit Test Gate

Unit tests must cover pure logic such as:

- API response adapters;
- structured warning formatting;
- date formatting;
- enum fallback behavior;
- query serialization;
- pagination calculation;
- route helper behavior;
- build metadata normalization;
- error normalization;
- safe text rendering helpers.

Unit tests must not depend on:

- production network;
- provider APIs;
- real credentials;
- external mutable services.

---

## 15. Component Test Gate

Shared components require tests for approved variants and states.

Minimum required states:

```text
Default
Hover-equivalent behavior where testable
Focus
Disabled
Loading
Error
Long content
Keyboard activation
Accessible label
```

Examples:

- Button;
- IconButton;
- StatusBadge;
- PageHeader;
- EmptyState;
- ErrorState;
- ConfirmationDialog;
- DataTable;
- Pagination;
- FormField.

A component is not complete until all approved states are represented.

---

## 16. API Client Test Gate

The shared API client must test:

```text
Successful JSON response
Direct payload response
Success envelope
Error envelope
HTTP error without JSON
Malformed JSON
Network failure
Timeout
Abort
401
403
404
409
422
429
500
Request ID capture
Safe read retry
No mutation retry
Credentials inclusion
Query serialization
Empty-body handling
```

The API client must never be tested against real provider APIs.

---

## 17. API Contract Gate

FastAPI OpenAPI is the contract source.

The gate must verify:

1. OpenAPI generation succeeds;
2. generated TypeScript types are reproducible;
3. generated output is current;
4. required endpoints exist;
5. required schemas remain compatible;
6. UI V2 compiles against current generated types;
7. no secret field appears in the public API schema;
8. unsupported breaking changes are rejected.

Contract drift blocks release.

---

## 18. Route Test Gate

Route tests must validate:

```text
/dashboard-v2
/dashboard-v2/projects
/dashboard-v2/projects/:projectId
/dashboard-v2/deployments
/dashboard-v2/connected-accounts
/dashboard-v2/settings
unknown route
deep link reload
browser back
browser forward
```

Required behavior:

- correct page renders;
- navigation state is correct;
- deep links return the SPA entry document;
- API routes are not intercepted by React Router;
- unknown routes render a controlled not-found page;
- route changes do not repeat mutations.

---

## 19. Authentication Test Gate

Authentication tests must verify:

### Unauthenticated

```text
/dashboard-v2 is protected
deep routes are protected
API returns expected unauthorized behavior
login flow is invoked through existing architecture
no UI content leak before authentication
```

### Authenticated

```text
UI shell loads
same-origin API calls include session
authorized data renders
session remains backend-authoritative
```

### Expired Session

```text
401 normalized centrally
no infinite retry
user returns to approved login flow
intended route preserved where supported
no duplicate mutation
```

### Forbidden

```text
403 does not trigger login loop
safe authorization message shown
hidden resource details not leaked
```

---

## 20. Browser Test Gate

Playwright browser tests are mandatory for every migrated page.

Minimum browser engines:

```text
Chromium
Firefox
WebKit
```

A temporary exception for one engine requires explicit documentation and must not apply to production cutover without approval.

Browser tests must validate:

- page load;
- navigation;
- API data presentation;
- loading state;
- empty state;
- error state;
- primary actions;
- keyboard focus;
- no uncaught page error;
- no failed required asset request;
- no critical console error;
- no `[object Object]`;
- no clipped primary content;
- no unexpected horizontal overflow.

---

## 21. Responsive Test Gate

Minimum viewport matrix:

```text
1920 × 1080
1600 × 900
1440 × 900
1366 × 768
1200 × 800
992 × 768
768 × 1024
390 × 844
```

Every frozen page must validate:

```text
Sidebar behavior
Mobile navigation
Page header wrapping
Card grid collapse
Table behavior
Modal containment
Button wrapping
No clipped content
No horizontal page overflow
Readable typography
Valid touch targets
```

A page that works only at one desktop width fails the gate.

---

## 22. Geometry Assertions

Critical components require geometry checks.

Examples:

```text
Element exists
Display is not none
Visibility is visible
Opacity is greater than zero
Bounding box width is greater than zero
Bounding box height is greater than zero
Element remains inside expected container
Element does not overlap protected controls
Primary content remains inside viewport
```

Critical geometry checks apply to:

- provider cards;
- project cards;
- page header;
- primary action;
- sidebar;
- mobile drawer;
- modals;
- deployment blocker panel;
- connected account status cards.

---

## 23. Visual Regression Gate

Visual regression is mandatory after a page enters frozen visual status.

Baseline screenshots must be created in a controlled environment.

Required baseline states may include:

```text
Default
Loading
Empty
Error
Populated
Long content
Mobile
Tablet
Desktop
Modal open
Dropdown open where stable
```

Rules:

- baselines must be reviewed before acceptance;
- threshold changes require justification;
- masks may be used only for truly dynamic values;
- broad masking is prohibited;
- screenshot updates must not be automatic;
- every changed baseline requires human review;
- a visual difference does not automatically mean failure, but an unreviewed difference blocks release.

---

## 24. Accessibility Gate

Target:

```text
WCAG 2.1 AA
```

Required checks:

- keyboard navigation;
- visible focus;
- semantic heading order;
- form labels;
- error association;
- modal focus trap;
- escape behavior;
- icon-button accessible name;
- color contrast;
- non-color status meaning;
- reduced-motion support;
- screen-reader-readable status text;
- table semantics;
- skip or equivalent navigation behavior where needed.

Critical accessibility failures block release.

---

## 25. Console and Network Gate

Browser tests must fail on:

```text
Uncaught exception
Unhandled promise rejection
Required asset 404
Required API 5xx in success scenario
Mixed-content error
CORS error
Content Security Policy violation affecting UI
React hydration or render fatal error
```

Approved exclusions must be exact and documented.

Warnings must not be globally ignored.

---

## 26. Build Gate

The production build must verify:

```text
Dependency install from lockfile
TypeScript compile
Vite production build
No missing import
No unresolved asset
No source-map secret exposure
No environment secret embedded
No mutable unversioned primary CSS
No mutable unversioned primary JavaScript
```

The build output must be reproducible from the same source and lockfile within the supported build environment.

---

## 27. Asset Integrity Gate

The generated UI V2 build must contain:

```text
index.html
content-hashed JavaScript
content-hashed CSS
content-hashed imported assets
build metadata
```

Required checks:

- HTML references existing generated assets;
- no asset path points to legacy mutable files;
- UI V2 assets remain under UI V2 namespace;
- asset hashes differ when content changes;
- build identifier matches target commit;
- no stale asset from previous build is required;
- no missing font or logo asset;
- no path traversal;
- no secret file is copied.

---

## 28. Cache Contract Gate

Required production cache behavior:

### Application Entry Document

```text
Cache-Control: no-cache, must-revalidate
```

### Content-Hashed Assets

```text
Cache-Control: public, max-age=31536000, immutable
```

The gate must verify actual response headers in preview or staging.

A cache purge may be used as an operational safeguard, but cache purge is not a substitute for content-hashed assets.

---

## 29. Build Identity Gate

UI V2 must expose safe build identity.

Minimum values:

```text
UI version
Git commit SHA
Build identifier
Environment label
```

The UI build identity must be available through:

```text
window.YGIT_UI_BUILD
```

or an approved equivalent.

The gate must verify:

```text
browser build SHA == expected release SHA
HTML build marker == expected release SHA
asset manifest belongs to expected release
```

No secret environment values may appear.

---

## 30. Backend Regression Gate

Repository-integrated UI V2 changes must run the existing backend regression suite when:

- backend route files change;
- static delivery changes;
- authentication guards change;
- API schemas change;
- API routes change;
- Docker or packaging changes;
- shared repository configuration changes.

UI-only changes may still require the full regression suite according to repository release policy.

The current baseline pass count must be recorded as evidence, but pass count alone is not sufficient; all tests must pass.

---

## 31. UI Delivery Gate Tests

The backend UI Delivery Gate must test:

```text
/dashboard remains legacy before cutover
/dashboard-v2 returns UI V2 entry
/dashboard-v2/assets/* serves generated assets
/dashboard-v2/projects deep link returns UI entry
/api/v1/* remains API behavior
unauthenticated access protected
authenticated access allowed
invalid static path rejected
path traversal rejected
missing asset returns controlled 404
build metadata available
```

The UI Delivery Gate must contain no engine or provider test behavior.

---

## 32. Page-Specific Release Tests

### 32.1 Dashboard

```text
Metrics render
Provider cards visible
Recent projects render
Recent deployments render
Partial failure remains readable
No blank structural gap
No absolute-positioning dependency
```

### 32.2 Projects

```text
List loads
Pagination works where supported
Empty state works
Create project validates
Duplicate submit blocked
Successful create refreshes list
Failed create does not duplicate
```

### 32.3 Project Details

```text
Primary project data loads
Repository metadata loads
Analysis data loads
Readiness loads
Structured warnings render
Structured errors render
Partial data survives optional failure
No raw object rendering
```

### 32.4 Deployments

```text
History loads
Fresh readiness checked
Blocked deployment is not submitted
Ready deployment request uses documented API
Duplicate submission blocked
Mutation not automatically retried
```

### 32.5 Connected Accounts

```text
GitHub state loads
Cloudflare state loads
Permission summary renders
Connect uses backend route
Reconnect uses backend route
Disconnect requires confirmation
No token appears
```

### 32.6 Settings

```text
Only approved settings appear
Backend validation shown
Destructive changes confirmed
No arbitrary CSS or HTML configuration
No secret value exposed
```

---

## 33. Test Data Policy

Test data must be:

```text
Synthetic
Non-secret
Repeatable
Scoped
Disposable
```

Prohibited:

```text
Production tokens
Real private keys
Real customer data
Real provider credentials
Real session cookies in committed fixtures
Real production deployment creation for visual tests
```

Fixtures must not contain sensitive repository data unless explicitly approved and sanitized.

---

## 34. Mocking Policy

Mocks are allowed for:

- API client unit tests;
- component tests;
- loading states;
- error states;
- rare API responses;
- destructive-action prevention;
- provider state presentation.

Mocks do not prove:

- live PostgreSQL connectivity;
- live Redis connectivity;
- live GitHub App behavior;
- live Cloudflare OAuth behavior;
- live provider execution;
- worker job processing;
- production route correctness.

Test evidence must clearly state whether a result is mocked, integrated, staging, or production.

---

## 35. Live System Claim Policy

The following claims require explicit live evidence:

```text
PostgreSQL connected
Redis connected
GitHub App live
Cloudflare OAuth live
Worker running
Worker processed a job
Provider deployment executed
Production route live
```

A unit test, mock, or browser fixture cannot support these claims.

A process command such as:

```text
python -m backend.workers.main
```

proves the worker entrypoint is running, but does not prove a job was processed.

---

## 36. Provider Execution Safety Gate

Ordinary UI testing must not execute a real provider deployment.

Real provider execution requires:

1. explicit approval;
2. approved test repository;
3. approved Cloudflare account;
4. approved target project;
5. provider mode verification;
6. readiness verification;
7. rollback or cleanup plan;
8. evidence capture;
9. no unrelated production change.

A real deployment test belongs to a separate controlled release step.

---

## 37. Security Test Gate

Minimum security checks:

```text
No secret in frontend bundle
No provider token in browser storage
No secret in HTML
No secret in build metadata
No direct provider request
No unsafe raw HTML rendering
Protected routes require authentication
Forbidden responses handled safely
Path traversal blocked
Sensitive errors normalized
Destructive actions confirmed
```

A secret scan must include:

```text
source diff
generated bundle
source map when generated
committed fixtures
configuration files
```

---

## 38. Performance Gate

Initial performance requirements:

- application shell loads without unrelated API dependency;
- route-level code splitting is used where practical;
- no unbounded request fan-out;
- obsolete reads are cancelled;
- duplicate requests caused by rerender are prevented;
- large lists are paginated;
- provider details are not fetched for every row without documented need;
- production bundle sizes are measured and recorded;
- severe bundle growth requires review.

No fixed public performance SLA is established by this document.

---

## 39. Dependency Gate

Dependency changes must verify:

```text
Lockfile updated
License compatible with YGIT open-source strategy
Package maintained
No known critical vulnerability
No duplicate unnecessary framework
No provider SDK exposed in frontend
No unapproved analytics SDK
No unapproved state-management framework
```

A package must not be added for functionality already provided adequately by the approved stack without justification.

---

## 40. CI Gate Sequence

The recommended CI sequence is:

```text
1. Repository validation
2. Documentation validation
3. Dependency install from lockfile
4. Formatting check
5. Lint
6. TypeScript check
7. Unit tests
8. Component tests
9. API client tests
10. OpenAPI contract generation
11. Contract drift check
12. Vite production build
13. Asset integrity check
14. Browser tests
15. Accessibility tests
16. Visual regression
17. Backend focused tests
18. Full backend regression
19. Release packaging validation
```

A later stage must not hide an earlier failure.

---

## 41. Local Pre-Commit Gate

Minimum local pre-commit validation:

```text
Formatting
Lint
TypeScript
Focused tests
Affected page browser smoke
```

Full release validation may run before commit or before push according to the approved runner workflow.

---

## 42. Commit Gate

Before commit:

```text
Expected HEAD verified
Clean base verified
Exact dirty files verified
Secret scan passed
Diff reviewed
Focused tests passed
Full required tests passed
Build passed
Browser gate passed
Exact staged files verified
```

Commit subject must describe one scoped change.

Unrelated changes must not be combined.

---

## 43. Push Gate

After commit:

```text
Commit SHA recorded
Commit subject recorded
Push accepted
Remote branch SHA fetched
Local HEAD == remote HEAD
Worktree clean
No untracked generated output
```

A successful local commit without remote verification is not a completed release gate.

---

## 44. Release Classification

### Class A — Documentation Only

Required:

```text
Markdown validation
Exact file scope
Commit and push verification
```

Redeploy:

```text
Not required
```

### Class B — UI V2 Source Only

Required:

```text
Formatting
Lint
TypeScript
Unit/component tests
Build
Browser tests
Visual tests where frozen
Backend regression according to repository policy
```

Redeploy:

```text
Preview or production redeploy required only when deployment validation is requested
```

### Class C — UI Delivery Gate

Required:

```text
All Class B gates
Backend route tests
Authentication tests
Static asset tests
Full backend regression
Production readiness validation after deploy
```

Redeploy:

```text
Required
```

### Class D — API Contract Change

Required:

```text
All Class C gates
OpenAPI diff review
Generated type update
Backend API tests
Compatibility review
Migration evidence
```

Redeploy:

```text
Required
```

### Class E — Production Cutover

Required:

```text
All prior gates
Feature parity approval
Rollback route verification
Production build identity verification
Production route verification
Legacy route verification
Post-deploy readiness checks
```

Redeploy:

```text
Required
```

---

## 45. Preview Release Gate

Before deploying `/dashboard-v2` preview:

```text
All source gates PASS
All required tests PASS
Production build PASS
Asset integrity PASS
Build identity PASS
No secret PASS
Expected commit recorded
Local == remote
Worktree clean
Rollback path documented
```

After preview deploy:

```text
/dashboard unchanged
/dashboard-v2 authenticated
assets return 200
entry HTML returns expected build
deep links work
API calls work
no critical console errors
responsive smoke passes
no provider execution
```

---

## 46. Production Cutover Gate

Production cutover requires:

1. all UI V2 documentation Frozen;
2. all migration phases through hardening Approved;
3. feature parity Approved;
4. preview stability Approved;
5. visual approval completed;
6. browser matrix PASS;
7. accessibility PASS;
8. API contract PASS;
9. full backend regression PASS;
10. production build PASS;
11. asset integrity PASS;
12. rollback route tested;
13. cutover commit pushed;
14. local SHA equals remote SHA;
15. worktree clean;
16. production deployment target confirmed;
17. no unrelated deployment change.

---

## 47. Post-Deployment Production Verification

Production verification must check:

```text
Expected commit
Expected UI build SHA
Version endpoint
Health endpoint
Readiness endpoint where approved
/dashboard authentication
/dashboard page load
/dashboard deep link
/dashboard assets
/dashboard-legacy authentication
/dashboard-legacy page load
API protection
No required asset 404
No critical console error
PostgreSQL readiness
Redis readiness
Worker entrypoint
```

Post-deployment verification must state:

```text
live_provider_execution: false
```

unless a separately approved live provider test actually ran.

---

## 48. Production Smoke Boundaries

Production smoke may:

- load pages;
- read existing project data;
- read deployment history;
- read connected-account state;
- test navigation;
- validate build metadata;
- validate authentication.

Production smoke must not:

- create a project;
- disconnect an account;
- create a real deployment;
- modify settings;
- delete data;
- rotate credentials;
- change provider permissions.

Any mutation requires separate approval.

---

## 49. Rollback Triggers

Immediate rollback may be required for:

```text
Authentication failure
Dashboard route failure
Widespread asset 404
Stale or incorrect build identity
Critical API incompatibility
Deployment action safety defect
Provider credential exposure
Secret in frontend bundle
Critical navigation failure
Critical accessibility blocker
Severe layout clipping across supported viewports
Legacy rollback route unavailable after cutover
```

---

## 50. Rollback Procedure

For UI V2 cutover failure:

```text
1. Stop further UI mutation testing
2. Record failing build SHA
3. Record route and asset evidence
4. Switch /dashboard back to legacy route
5. Verify /dashboard legacy loads
6. Verify /api/v1 remains healthy
7. Verify PostgreSQL readiness
8. Verify Redis readiness
9. Verify worker entrypoint
10. Confirm no provider execution
11. Open corrective change
```

Rollback must not:

- modify database records;
- disconnect providers;
- cancel deployments automatically;
- delete UI V2 source;
- delete diagnostic evidence.

---

## 51. Evidence Requirements

Every release must record:

```text
Expected base SHA
Actual starting SHA
Runner or workflow identifier
Runner SHA-256 when external runner is used
Exact changed files
Focused test results
Full test results
TypeScript result
Build result
Browser result
Visual result
Secret scan result
Commit subject
Commit SHA
Push result
Remote SHA
Local == remote
Final worktree status
Deployment target when applicable
Post-deploy verification result
Live provider execution status
```

Evidence must distinguish:

```text
Mock
Local integrated
Preview/staging
Production
Live provider execution
```

---

## 52. External Runner Safety

When an external PowerShell or shell runner is used:

- runner remains outside repository;
- runner SHA-256 is recorded;
- expected base SHA is hardcoded or explicitly supplied;
- clean worktree is required;
- local and remote base must match;
- exact file scope is enforced;
- deterministic failures stop immediately;
- no secret is embedded;
- staged file set is verified;
- commit subject is verified;
- push result is verified;
- final clean worktree is verified.

Safeguards reduce risk but do not guarantee zero risk.

---

## 53. Retry Policy

Retry is allowed only for transient system failures.

### Retryable

```text
Browser process failed to launch
Temporary package registry failure
Temporary network fetch failure
Known transient Windows native exit
Temporary test-process startup failure
```

### Not Retryable

```text
TypeScript failure
Lint failure
Unit test failure
Browser assertion failure
Visual difference
Contract mismatch
Source hash mismatch
Unexpected Git status
Unexpected changed file
Build configuration error
Authentication test failure
Asset integrity failure
```

Maximum retry:

```text
2 additional attempts
```

A retry is allowed only when:

```text
HEAD unchanged
worktree clean
no partial mutation
no staged files
```

---

## 54. Flaky Test Policy

A flaky test is a defect.

Rules:

- do not automatically ignore;
- do not add broad retry to hide it;
- identify root cause;
- quarantine only with explicit approval;
- record owner and expiry condition;
- block production cutover for flaky deployment-safety tests;
- remove quarantine after correction.

---

## 55. Warning Policy

Warnings must be classified.

### Allowed Temporarily

- known non-security deprecation;
- known framework warning with approved issue;
- non-blocking test-environment warning.

### Not Allowed

- secret exposure warning;
- accessibility critical warning;
- failed asset request;
- API contract warning;
- authentication warning;
- deployment mutation warning;
- unhandled promise warning.

All accepted warnings require evidence and an owner.

---

## 56. Release Approval Roles

| Role | Responsibility |
|---|---|
| Product Owner | Scope and visual approval |
| Architecture Owner | Boundary compliance |
| Frontend Owner | UI implementation and tests |
| Backend Owner | API and delivery-gate safety |
| Security Owner | Secret and auth review |
| Release Owner | Commit, deploy, evidence, rollback |
| Accessibility Reviewer | Accessibility acceptance |

One person may hold multiple roles in early development, but each responsibility must still be explicitly checked.

---

## 57. Phase Exit Criteria

A migration phase exits only when:

```text
Scope complete
Acceptance criteria met
Focused tests pass
Required full tests pass
Build passes
Browser checks pass
Documentation updated
Decision log updated
Commit pushed
Local equals remote
Worktree clean
Evidence stored
Approval recorded
```

Partial success is not phase completion.

---

## 58. Documentation-Only Release Rule

For documentation-only changes:

- no UI build is required unless the document itself changes tooling contracts that must be validated;
- no Coolify redeploy is required;
- exact file scope and Git verification remain mandatory;
- implementation status must remain unchanged;
- documentation must not claim code exists when it does not.

---

## 59. Acceptance Criteria

This specification is ready for approval when the following are accepted:

- layered test architecture;
- Playwright browser testing;
- responsive viewport matrix;
- visual regression for frozen pages;
- WCAG 2.1 AA target;
- OpenAPI contract validation;
- strict TypeScript;
- content-hashed asset validation;
- cache header validation;
- UI build identity validation;
- exact Git scope validation;
- full backend regression where required;
- no real provider execution during ordinary UI testing;
- evidence-based production verification;
- explicit rollback triggers;
- bounded transient retry only;
- production not used as first visual test environment;
- clear distinction between mock and live evidence.

---

## 60. Frozen Rules After Approval

After approval:

1. Every UI V2 release must pass the applicable layered gates.
2. TypeScript strict validation is mandatory.
3. Pages require real browser tests.
4. Frozen pages require visual regression tests.
5. Responsive validation uses the approved viewport matrix.
6. Critical components require geometry assertions.
7. Accessibility target is WCAG 2.1 AA.
8. FastAPI OpenAPI contract drift blocks release.
9. Mutations are not automatically retried.
10. Ordinary UI testing does not execute providers.
11. Production is not the first visual test environment.
12. Assets must be content-hashed.
13. Entry HTML must revalidate.
14. Hashed assets must be immutable.
15. UI build SHA must match the expected release SHA.
16. Source scope must be exact.
17. Local and remote Git SHA must match after push.
18. Final worktree must be clean.
19. Production smoke is read-only unless separately approved.
20. Rollback must preserve engine, provider, and data state.
21. Test evidence must state mock, preview, production, and live-execution status.
22. Deterministic failures are never retried.
23. Flaky tests are defects, not acceptable release noise.
24. Documentation-only changes require no redeploy.
25. Production cutover requires explicit approval.

---

## 61. Next Documentation Step

After this document is reviewed and approved, the next document is:

```text
YGIT UI V2 Decision Log
```

No UI V2 implementation is authorized by this draft.

---

## 62. Approval Record

| Role | Name | Decision | Date |
|---|---|---|---|
| Product Owner | Pending | Pending | Pending |
| Architecture Owner | Pending | Pending | Pending |
| Frontend Owner | Pending | Pending | Pending |
| Backend Owner | Pending | Pending | Pending |
| Security Owner | Pending | Pending | Pending |
| Release Owner | Pending | Pending | Pending |
| Accessibility Reviewer | Pending | Pending | Pending |

---

**End of Document**
