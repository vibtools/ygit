# YGIT UI V2 Migration Plan

**Document ID:** YGIT-UIV2-MIG-001<br>
**Version:** 0.1.0<br>
**Status:** Draft for Review<br>
**Owner:** YGIT Platform<br>
**Product:** YGIT<br>
**Company:** Vib Tools<br>
**Depends On:**<br>
- `UI_V2_MASTER_ARCHITECTURE.md`<br>
- `UI_V2_API_ARCHITECTURE.md`<br>
- `UI_V2_DESIGN_SYSTEM_FREEZE.md`<br>

**Last Updated:** 2026-07-22<br>

---

## Revision History

| Version | Date | Status | Summary |
|---|---|---|---|
| 0.1.0 | 2026-07-22 | Draft for Review | Initial UI V2 migration plan |

---

## 1. Purpose

This document defines the controlled migration from the current framework-free YGIT dashboard to UI V2.

The migration must:

- preserve the current production dashboard during development;
- keep all existing YGIT engines authoritative;
- avoid unnecessary backend changes;
- introduce UI V2 through an isolated route;
- migrate pages in small, reviewable stages;
- allow rollback without changing deployment state;
- prevent frontend failures from affecting providers, workers, PostgreSQL, Redis, or infrastructure;
- preserve current authentication and API behavior;
- require approval before production cutover;
- provide a repeatable path for future YGIT developers.

This document does not authorize implementation. It freezes the migration sequence, scope boundaries, acceptance criteria, and rollback model.

---

## 2. Migration Principle

The migration model is:

```text
Document
    ↓
Review
    ↓
Freeze
    ↓
Build UI V2 in isolation
    ↓
Validate against existing APIs
    ↓
Preview under /dashboard-v2
    ↓
Migrate page by page
    ↓
Complete feature parity
    ↓
Approve production cutover
    ↓
Keep legacy rollback route
    ↓
Retire legacy UI later
```

The primary rule is:

> UI V2 will be added beside the current dashboard before it replaces the current dashboard.

---

## 3. Current and Target States

### 3.1 Current State

```text
/dashboard
    → Current Vanilla HTML/CSS/JavaScript dashboard

/api/v1/*
    → Existing FastAPI API layer

YGIT Engines
    → Existing business logic

Provider Layer
    → Existing GitHub and Cloudflare integrations

Worker
    → Existing deployment execution
```

### 3.2 Migration State

```text
/dashboard
    → Current legacy dashboard

/dashboard-v2
    → New React UI V2 preview

/api/v1/*
    → Shared existing backend APIs
```

### 3.3 Target State After Approved Cutover

```text
/dashboard
    → UI V2

/dashboard-legacy
    → Legacy dashboard rollback route

/api/v1/*
    → Existing YGIT APIs
```

### 3.4 Final State After Separate Legacy Retirement

```text
/dashboard
    → UI V2

/dashboard-legacy
    → Removed only after separate approval

frontend/dashboard
    → Removed only after separate approval
```

---

## 4. Migration Goals

The migration must achieve:

1. isolated UI V2 development;
2. zero direct changes to YGIT engine behavior;
3. zero direct changes to provider execution behavior;
4. zero database migration solely for UI V2;
5. zero frontend access to provider secrets;
6. versioned UI assets;
7. same-origin API access;
8. reuse of current authentication;
9. page-level migration;
10. explicit acceptance gates;
11. reversible route switching;
12. legacy UI availability during the stabilization period;
13. documented ownership for every migrated page;
14. predictable onboarding for future developers.

---

## 5. Non-Goals

This migration does not include:

- rebuilding YGIT engines;
- changing the provider architecture;
- changing the worker architecture;
- changing PostgreSQL models;
- changing Redis contracts;
- changing GitHub App architecture;
- changing Cloudflare OAuth architecture;
- creating a CMS;
- creating a UI Engine;
- adding database-driven arbitrary layouts;
- redesigning unrelated backend APIs;
- implementing future features not already approved;
- removing the legacy dashboard during initial migration;
- production cutover before feature parity.

---

## 6. Protected Boundaries

The following areas are protected during UI V2 migration:

```text
backend/engines/
backend/providers/
backend/workers/
database migrations
Redis queue contracts
GitHub App credentials
Cloudflare OAuth credentials
provider execution mode
deployment readiness rules
deployment execution behavior
```

A migration phase must explicitly state when it touches any backend file.

Default assumption:

```text
Frontend-only unless documented otherwise.
```

---

## 7. Approved Migration Strategy

The approved strategy is a parallel frontend migration.

### 7.1 Legacy UI

```text
frontend/dashboard/
```

Status during migration:

```text
Production active
Source preserved
No visual redesign work
Only critical security or functional fixes if separately approved
```

### 7.2 UI V2

```text
frontend-v2/
```

Status during migration:

```text
New isolated source
React + TypeScript + Vite + Mantine UI
Served under /dashboard-v2
Uses existing /api/v1/*
```

### 7.3 Backend Addition

The only initial backend addition is the UI Delivery Gate.

It may:

- protect `/dashboard-v2`;
- serve UI V2 entry document;
- serve versioned assets;
- return SPA fallback;
- expose safe build metadata if approved.

It may not:

- contain business logic;
- call providers;
- change deployment state;
- change database state;
- change worker behavior.

---

## 8. Migration Workstreams

The migration is divided into six workstreams.

### 8.1 Documentation

- architecture;
- API contracts;
- design system;
- migration plan;
- testing and release gate;
- decision log.

### 8.2 UI Platform Foundation

- React application shell;
- TypeScript;
- Vite;
- Mantine;
- React Router;
- theme;
- shared API client;
- build metadata.

### 8.3 UI Delivery Gate

- authenticated route;
- static assets;
- SPA fallback;
- preview route.

### 8.4 Page Migration

- Dashboard;
- Projects;
- Project Details;
- Deployments;
- Connected Accounts;
- Settings.

### 8.5 Validation

- TypeScript;
- unit tests;
- API contract tests;
- browser tests;
- responsive checks;
- preview validation.

### 8.6 Cutover and Stabilization

- production route switch;
- legacy rollback route;
- stabilization period;
- legacy retirement decision.

---

## 9. Migration Phase Summary

| Phase | Name | Primary Outcome |
|---|---|---|
| 0 | Documentation Freeze | Architecture approved |
| 1 | Repository and Tooling Foundation | `frontend-v2/` exists and builds |
| 2 | UI Delivery Gate | `/dashboard-v2` serves protected UI V2 |
| 3 | Application Shell | Navigation and theme foundation |
| 4 | Shared API Foundation | Central typed API access |
| 5 | Dashboard Migration | Operational overview in UI V2 |
| 6 | Projects Migration | Project list and creation |
| 7 | Project Details Migration | Read-only project detail and readiness |
| 8 | Deployments Migration | Deployment history and actions |
| 9 | Connected Accounts Migration | GitHub and Cloudflare account UI |
| 10 | Settings Migration | Approved settings UI |
| 11 | Feature Parity and Hardening | UI V2 matches approved MVP scope |
| 12 | Production Cutover | `/dashboard` switches to UI V2 |
| 13 | Stabilization Period | Legacy route retained |
| 14 | Legacy Retirement | Separate approved removal |

---

# Phase 0 — Documentation Freeze

## 10. Objective

Complete and approve all UI V2 documents before implementation.

Required documents:

```text
docs/ui-v2/
├── README.md
├── UI_V2_MASTER_ARCHITECTURE.md
├── UI_V2_API_ARCHITECTURE.md
├── UI_V2_DESIGN_SYSTEM_FREEZE.md
├── UI_V2_MIGRATION_PLAN.md
├── UI_V2_TESTING_AND_RELEASE_GATE.md
└── UI_V2_DECISION_LOG.md
```

## 10.1 Scope

- review architecture;
- review API boundary;
- review design system;
- review migration phases;
- define testing and release gate;
- record decisions;
- update repository documentation entry point.

## 10.2 Exit Criteria

- all required documents exist;
- master architecture is Approved;
- API architecture is Approved;
- design system is Approved and Frozen;
- migration plan is Approved;
- testing and release gate is Approved;
- root README links to UI V2 documentation;
- no implementation has started before approval.

## 10.3 Rollback

Not applicable. Documentation changes may be revised through version history.

---

# Phase 1 — Repository and Tooling Foundation

## 11. Objective

Create the isolated UI V2 application without changing production routing.

## 11.1 Intended Source Scope

```text
frontend-v2/
package metadata required for frontend tooling
approved ignore rules
UI V2 documentation references
```

## 11.2 Required Foundation

```text
React
TypeScript
Vite
Mantine UI
React Router
Lucide icons
locked dependency versions
```

## 11.3 Initial Output

```text
frontend-v2/
├── public/
├── src/
│   ├── app/
│   ├── pages/
│   ├── features/
│   ├── components/
│   ├── layouts/
│   ├── api/
│   ├── hooks/
│   ├── theme/
│   ├── assets/
│   ├── types/
│   └── utils/
├── package.json
├── lockfile
├── tsconfig.json
└── vite.config.ts
```

## 11.4 Required Behavior

- local development server starts;
- TypeScript compiles;
- Vite production build succeeds;
- generated asset filenames are content-versioned;
- no existing frontend file changes;
- no backend route changes;
- no environment-variable requirement;
- no provider execution;
- no database change.

## 11.5 Acceptance Criteria

```text
frontend-v2 exists
dependency lock exists
TypeScript check passes
production build passes
hashed assets generated
legacy UI unchanged
backend unchanged
```

## 11.6 Rollback

Delete only the unreferenced `frontend-v2/` foundation and related tooling changes.

Production behavior remains unchanged because no route points to UI V2.

---

# Phase 2 — UI Delivery Gate

## 12. Objective

Expose UI V2 under an authenticated preview route without affecting `/dashboard`.

## 12.1 Backend Scope

Only the delivery boundary may change.

Potential areas:

```text
backend route registration
static asset serving
authentication route protection
SPA fallback
build path configuration
```

Exact file ownership must be established before implementation.

## 12.2 Required Routes

```text
/dashboard
    → legacy dashboard

/dashboard-v2
    → UI V2 entry document

/dashboard-v2/*
    → UI V2 SPA fallback

/dashboard-v2/assets/*
    → versioned assets
```

## 12.3 Required Security

- existing authentication guard reused;
- unauthenticated UI V2 access rejected or redirected through existing login flow;
- no provider tokens served;
- no filesystem traversal;
- assets restricted to generated UI V2 output;
- `/api/v1/*` remains unaffected.

## 12.4 Acceptance Criteria

```text
/dashboard unchanged
/dashboard-v2 protected
UI V2 index loads
UI V2 assets load
deep link loads
unauthenticated protection works
version and health routes unchanged
dashboard and admin guards unchanged
no provider execution
```

## 12.5 Rollback

Remove or disable only the `/dashboard-v2` delivery route.

Legacy `/dashboard` remains active.

---

# Phase 3 — Application Shell

## 13. Objective

Build the stable UI V2 shell before migrating feature pages.

## 13.1 Scope

```text
AppShell
Sidebar
Topbar
Route outlet
Theme provider
Error boundary
Loading boundary
Not-found page
Preview indicator
build metadata
```

## 13.2 Approved Navigation Shell

Initial shell may display approved MVP navigation:

```text
Dashboard
Projects
Deployments
Connected Accounts
Settings
```

Future navigation items remain out of scope until their feature is approved.

## 13.3 Requirements

- dark-first design tokens;
- `240px` desktop sidebar;
- responsive mobile drawer;
- keyboard navigation;
- visible focus;
- no absolute-positioned primary layout;
- no global CSS patch layers;
- no feature API requests;
- no hardcoded production domain.

## 13.4 Acceptance Criteria

```text
shell renders
navigation changes routes
mobile navigation works
unknown route shows not-found
theme matches frozen tokens
no horizontal overflow
no console errors
build metadata available
```

## 13.5 Rollback

Remove shell changes from UI V2 only. Preview route may continue to serve a minimal placeholder.

---

# Phase 4 — Shared API Foundation

## 14. Objective

Create one safe API integration path before feature pages consume backend data.

## 14.1 Scope

```text
shared API client
normalized API error
session-expiry handling
request timeout
abort support
safe read retry
OpenAPI type generation
domain API module skeletons
```

## 14.2 Required API Modules

Initial modules:

```text
auth
platform
projects
repositories
repository-analysis
deployments
connected-accounts
```

Only functions needed by migrated pages should be implemented.

## 14.3 Requirements

- same-origin `/api/v1`;
- `credentials: include`;
- no direct `fetch()` in pages;
- generated types not manually edited;
- one normalized error type;
- read-only bounded retries;
- no mutation retries;
- no provider calls;
- no secret storage;
- no API contract changes unless separately approved.

## 14.4 Acceptance Criteria

```text
platform version read works
platform health read works
401 handling is centralized
timeout works
abort works
safe read retry works
mutation retry is absent
generated types are current
```

## 14.5 Rollback

Remove UI V2 API foundation without affecting backend APIs or legacy UI.

---

# Phase 5 — Dashboard Migration

## 15. Objective

Rebuild the Dashboard page in UI V2 using existing backend APIs.

## 15.1 Dashboard Scope

Approved dashboard content:

```text
Operational overview
Project count
Deployment count
Deploy success
Connected accounts
Live sites
Last deployment
Framework usage
Platform status
Queue status
Recent projects
Recent deployment summary
Provider connection summary
```

Content availability depends on current API contracts.

## 15.2 Prohibited Dashboard Patterns

- oversized hero;
- absolute-positioned provider cards;
- decorative blank space;
- duplicated metrics;
- client-invented platform health;
- frontend-invented deployment readiness;
- direct provider requests.

## 15.3 API Dependencies

Potential existing APIs:

```text
platform status
projects list
connected accounts
project deployment history
```

The API Architecture document remains authoritative.

## 15.4 Acceptance Criteria

```text
dashboard loads from existing APIs
all cards visible
no object-object rendering
provider cards render in normal flow
loading state works
empty state works
partial failure works
responsive layouts pass
no legacy CSS dependency
no provider execution
```

## 15.5 Rollback

UI V2 Dashboard route returns to placeholder or previous UI V2 build.

Legacy `/dashboard` remains unchanged.

---

# Phase 6 — Projects Migration

## 16. Objective

Migrate project listing and project creation into UI V2.

## 16.1 Scope

```text
project list
project status
project repository reference
create project form
pagination where supported
loading state
empty state
error state
```

## 16.2 Existing Backend Authority

Project Engine remains authoritative for:

- project creation;
- project state;
- slug validation;
- repository attachment;
- analysis association;
- deployment readiness.

## 16.3 Mutation Safety

Project creation must:

- disable duplicate submission;
- never retry automatically;
- show backend validation;
- refresh project list after success;
- preserve form values on recoverable failure where appropriate;
- not access GitHub directly.

## 16.4 Acceptance Criteria

```text
project list loads
empty state works
create form validates usability
backend validation remains authoritative
duplicate submit prevented
successful create refreshes list
failed create creates no duplicate
no provider execution
```

## 16.5 Rollback

Remove or disable UI V2 project routes. Legacy Projects remains available through legacy dashboard.

---

# Phase 7 — Project Details Migration

## 17. Objective

Migrate read-only project details, repository metadata, repository analysis, and readiness presentation.

## 17.1 Scope

```text
project identity
project status
repository URL
default branch
visibility
latest commit SHA
framework
package manager
build command
output directory
analysis score
warnings
errors
deployment readiness
blocking reasons
partial-read notices
```

## 17.2 Required Behavior

- load primary project data first;
- load optional detail data safely;
- preserve partial data when an optional read fails;
- format structured warning and error objects safely;
- never render raw objects;
- show technical identifiers in monospace;
- keep page read-only except approved actions.

## 17.3 Acceptance Criteria

```text
project detail loads
repository metadata loads when available
analysis loads when available
readiness loads
structured warnings readable
structured errors readable
unknown objects use safe fallback
partial reads preserve available data
no [object Object]
```

## 17.4 Rollback

Disable UI V2 project-detail route. Legacy Open behavior remains available.

---

# Phase 8 — Deployments Migration

## 18. Objective

Migrate deployment history and approved deployment actions.

## 18.1 Scope

```text
deployment list
deployment status
timestamps
deployment URL
history pagination
empty state
manual refresh
request deployment
readiness blocker display
```

## 18.2 Safety Rules

Before deployment request:

```text
fresh project readiness fetch
    ↓
deploy_ready?
    ├── No  → show blockers; no deployment request
    └── Yes → explicit deployment request
```

UI V2 must not:

- infer readiness from old project state alone;
- auto-retry deployment POST;
- automatically submit after a transient error;
- directly call Cloudflare;
- create provider configuration.

## 18.3 Acceptance Criteria

```text
history loads
empty state works
manual refresh works
fresh readiness checked
blocked project creates no deployment
ready project request follows backend contract
duplicate click prevented
mutation not automatically retried
provider execution occurs only after explicit approved user action
```

## 18.4 Live Provider Boundary

A real deployment test is not part of ordinary UI migration testing.

Any real Cloudflare Pages execution requires a separately approved controlled production test.

## 18.5 Rollback

Disable UI V2 deployment routes. Existing backend deployment records remain unchanged.

---

# Phase 9 — Connected Accounts Migration

## 19. Objective

Migrate GitHub and Cloudflare account presentation and approved account actions.

## 19.1 Scope

```text
provider identity
connection state
account name
connection date
last sync
permission summary
repository-access summary
connect
reconnect
disconnect
provider manage link
```

## 19.2 Security Rules

UI V2 must never display:

- access tokens;
- refresh tokens;
- private keys;
- OAuth client secrets;
- installation tokens;
- session secrets.

## 19.3 GitHub Boundary

GitHub connection remains based on the approved GitHub App architecture.

Legacy GitHub OAuth variables remain prohibited.

## 19.4 Cloudflare Boundary

Cloudflare connection remains based on the approved Cloudflare OAuth architecture.

## 19.5 Acceptance Criteria

```text
connection state loads
status labels are readable
permissions render safely
connect uses backend route
reconnect uses backend route
disconnect requires confirmation
successful action refreshes state
no secret appears
no direct provider API request
```

## 19.6 Rollback

Disable UI V2 Connected Accounts page. Existing provider connections remain unchanged.

---

# Phase 10 — Settings Migration

## 20. Objective

Migrate only approved existing settings.

## 20.1 Scope

The settings page may expose only backend-supported settings.

This phase does not authorize:

- arbitrary theme editing;
- arbitrary CSS;
- page-builder controls;
- new account permissions;
- provider execution policy changes;
- environment variable editing;
- infrastructure configuration.

## 20.2 Acceptance Criteria

```text
only documented settings shown
backend remains authoritative
invalid values blocked
destructive changes confirmed
no secret values exposed
no arbitrary UI configuration
```

## 20.3 Rollback

Disable UI V2 Settings route. Backend settings remain unchanged.

---

# Phase 11 — Feature Parity and Hardening

## 21. Objective

Confirm UI V2 covers the approved MVP dashboard scope before cutover.

## 21.1 Required Feature Parity

At minimum:

```text
Authentication shell
Dashboard
Projects
Project creation
Project details
Repository Analysis presentation
Deployment readiness presentation
Deployment history
Deployment request flow
Connected Accounts
Settings
Navigation
Loading states
Empty states
Error states
Responsive behavior
```

## 21.2 Hardening Areas

```text
TypeScript strictness
API contract alignment
keyboard navigation
accessibility
responsive layouts
long-content behavior
timeouts
session expiry
partial failures
mutation duplicate prevention
asset versioning
build metadata
```

## 21.3 Exit Criteria

- every approved page has parity;
- no page depends on legacy CSS or JavaScript;
- preview route is stable;
- all release gates pass;
- no known critical defect;
- no known high-severity accessibility defect;
- product owner approves visual design;
- architecture owner approves boundaries;
- backend owner confirms no unauthorized backend behavior.

---

# Phase 12 — Production Cutover

## 22. Objective

Switch the primary dashboard route to UI V2 while preserving rollback.

## 22.1 Route Change

Before:

```text
/dashboard       → legacy
/dashboard-v2    → UI V2
```

After:

```text
/dashboard        → UI V2
/dashboard-legacy → legacy
```

## 22.2 Preconditions

Cutover requires:

- all documentation Frozen;
- feature parity approved;
- testing and release gate PASS;
- production build verified;
- authenticated preview approved;
- rollback route tested;
- local and remote source alignment;
- clean worktree;
- deployment commit identified;
- no unrelated backend changes;
- no database migration solely for route switch.

## 22.3 Cutover Verification

```text
/dashboard protected
/dashboard loads UI V2
/dashboard/projects deep link works
/dashboard-legacy protected
/dashboard-legacy loads legacy UI
/api/v1 unchanged
platform version and health PASS
worker process unchanged
PostgreSQL readiness PASS
Redis readiness PASS
no provider execution during verification
```

## 22.4 Rollback Trigger

Rollback should occur for:

- authentication failure;
- route failure;
- asset loading failure;
- broad API incompatibility;
- inaccessible critical workflow;
- deployment action safety defect;
- severe responsive breakage;
- significant data rendering corruption.

## 22.5 Rollback Action

Switch `/dashboard` back to the legacy UI route.

Do not:

- roll back database state;
- modify provider connections;
- cancel deployments automatically;
- alter engine state;
- delete UI V2 source.

---

# Phase 13 — Stabilization Period

## 23. Objective

Operate UI V2 as primary while retaining legacy rollback.

## 23.1 Stabilization Requirements

During the stabilization period:

- `/dashboard-legacy` remains available to authorized users;
- critical defects are tracked;
- UI V2 build metadata is recorded;
- browser and API failures are reviewed;
- no new large UI redesign begins;
- security and deployment safety defects receive priority;
- legacy UI receives no feature development.

## 23.2 Exit Criteria

- no unresolved critical defect;
- no unresolved high-risk deployment-flow defect;
- stable authentication;
- stable asset loading;
- stable page navigation;
- stable API compatibility;
- product owner approves legacy retirement review.

The duration is defined later by the Testing and Release Gate document or explicit approval.

---

# Phase 14 — Legacy Retirement

## 24. Objective

Remove the legacy dashboard only after a separate approved decision.

## 24.1 Required Approval

Legacy removal requires:

- a new change request;
- stabilization evidence;
- rollback decision;
- file inventory;
- route inventory;
- test update;
- documentation update;
- source and deployment rollback plan.

## 24.2 Removal Scope

Potential removal:

```text
legacy dashboard route
legacy frontend assets
legacy contract tests
legacy compatibility markers
legacy UI documentation
```

## 24.3 Protected Scope

Legacy retirement must not remove:

- shared authentication;
- existing APIs;
- engine logic;
- provider logic;
- worker logic;
- deployment records;
- project records;
- connected account records.

---

## 25. Page Migration Dependency Order

The approved dependency order is:

```text
Application Shell
    ↓
Shared API Client
    ↓
Dashboard
    ↓
Projects
    ↓
Project Details
    ↓
Deployments
    ↓
Connected Accounts
    ↓
Settings
```

Reasoning:

- Dashboard validates the shell and read-only API integration.
- Projects validates list and form behavior.
- Project Details validates composed reads and structured messages.
- Deployments validates safety-sensitive mutations.
- Connected Accounts validates authentication-sensitive provider flows.
- Settings is migrated after stable shared patterns exist.

A later phase must not start when an earlier foundational phase is unstable.

---

## 26. Per-Phase Change Workflow

Every implementation phase must use the following sequence:

```text
1. Confirm expected Git base
2. Confirm clean worktree
3. Confirm source file hashes or approved source state
4. Apply exact scoped update
5. Verify exact dirty file set
6. Run formatting and static checks
7. Run focused tests
8. Run full regression tests
9. Run UI build
10. Run browser smoke tests
11. Run release gate
12. Verify exact staged files
13. Commit with approved subject
14. Push
15. Verify local HEAD equals remote HEAD
16. Verify clean worktree
```

No phase may silently include unrelated changes.

---

## 27. Retry Policy for Migration Runners

Automated runner retries are allowed only for transient system failures.

Allowed retry categories:

```text
process launch failure
known transient Windows native exit
temporary network fetch failure
temporary package registry failure when source remains unchanged
temporary browser launch failure
```

Not retryable:

```text
TypeScript error
test failure
lint failure
API contract mismatch
browser assertion failure
source hash mismatch
unexpected file change
unexpected Git HEAD
build configuration error
```

A retry may occur only when:

```text
HEAD unchanged
worktree clean
no partial source mutation
```

---

## 28. Testing Requirements by Phase

| Phase | Minimum Test Types |
|---|---|
| Tooling Foundation | TypeScript, build |
| UI Delivery Gate | route, auth, assets, SPA fallback |
| Application Shell | route, navigation, responsive |
| API Foundation | client unit, contract, auth handling |
| Dashboard | component, integration, browser |
| Projects | form, list, mutation safety |
| Project Details | partial reads, structured messages |
| Deployments | readiness, no duplicate mutation |
| Connected Accounts | provider state, secret boundary |
| Settings | validation, authorization |
| Cutover | production readiness, route rollback |

Full requirements will be frozen in `UI_V2_TESTING_AND_RELEASE_GATE.md`.

---

## 29. Browser Validation Matrix

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

Every migrated page must verify:

- no horizontal overflow;
- no clipped primary content;
- visible controls;
- readable typography;
- stable navigation;
- valid card geometry;
- valid modal geometry;
- keyboard focus;
- no console error.

---

## 30. Data Safety Rules

UI migration must never:

- delete projects during read-only validation;
- disconnect provider accounts during routine UI tests;
- create real deployments during ordinary visual tests;
- expose secrets in browser logs;
- mutate backend state through page load;
- retry mutations automatically;
- use production provider execution for layout testing.

Where mutation tests are required, they must use approved test environments, mocks, or explicitly approved controlled production actions.

---

## 31. Environment Variable Policy

UI V2 should not require backend secrets.

Frontend build-time values may include only safe public metadata such as:

```text
UI version
Git commit SHA
build identifier
base route
environment label
```

Prohibited frontend environment exposure:

```text
DATABASE_URL
REDIS_URL
SESSION_SECRET
GITHUB_APP_PRIVATE_KEY
GITHUB_APP_ID when not required for public presentation
CLOUDFLARE_OAUTH_CLIENT_SECRET
provider tokens
```

Backend UI Delivery Gate should reuse current backend configuration where possible.

---

## 32. Asset Migration Rules

UI V2 assets must:

- use content-hashed filenames;
- remain isolated from legacy asset paths;
- include approved brand assets;
- expose build metadata;
- avoid mutable permanently named production CSS;
- support rollback to prior builds;
- not overwrite legacy assets.

Legacy and UI V2 asset directories must remain separate until legacy retirement.

---

## 33. Documentation Updates During Migration

Each phase must update:

```text
UI_V2_DECISION_LOG.md
relevant architecture document revision history when required
migration phase status
testing evidence reference
README links where applicable
```

Documents must not be silently changed after freeze.

Architecture change requires:

```text
Change Request
    ↓
Impact Analysis
    ↓
Version Update
    ↓
Approval
```

---

## 34. Migration Status Tracking

Each phase status must use:

```text
Not Started
In Documentation
Ready for Implementation
In Progress
Blocked
In Review
Approved
Released
Rolled Back
```

Suggested phase table:

| Phase | Status | Commit | Evidence | Approval |
|---|---|---|---|---|
| 0 | In Documentation | — | Documents | Pending |
| 1 | Not Started | — | — | Pending |
| 2 | Not Started | — | — | Pending |
| 3 | Not Started | — | — | Pending |
| 4 | Not Started | — | — | Pending |
| 5 | Not Started | — | — | Pending |
| 6 | Not Started | — | — | Pending |
| 7 | Not Started | — | — | Pending |
| 8 | Not Started | — | — | Pending |
| 9 | Not Started | — | — | Pending |
| 10 | Not Started | — | — | Pending |
| 11 | Not Started | — | — | Pending |
| 12 | Not Started | — | — | Pending |
| 13 | Not Started | — | — | Pending |
| 14 | Not Started | — | — | Pending |

---

## 35. Change Scope Classification

Each migration change must be classified.

### Class A — Documentation Only

```text
No runtime change
No redeploy required
```

### Class B — UI V2 Source Only

```text
No backend behavior change
Preview redeploy may be required
```

### Class C — UI Delivery Gate

```text
Backend route/static delivery change
No engine/provider change
Redeploy required
```

### Class D — API Contract Extension

```text
Backend API change
Separate API approval required
Full regression required
```

### Class E — Production Route Cutover

```text
Primary route change
Rollback route required
Production redeploy required
```

UI implementation work must not be misclassified as engine work.

---

## 36. Rollback Matrix

| Failure | Rollback |
|---|---|
| UI V2 build failure | Do not package or deploy |
| Preview asset failure | Disable `/dashboard-v2` |
| Preview authentication failure | Restore prior delivery-gate commit |
| Page-specific UI failure | Revert UI V2 page commit |
| API adapter failure | Revert adapter/module commit |
| Production cutover failure | Route `/dashboard` back to legacy |
| Legacy route failure after cutover | Restore prior legacy route mapping |
| Provider or engine issue unrelated to UI | Follow owning engine/provider rollback, not UI rollback |

---

## 37. Migration Risks

### 37.1 API Contract Drift

Risk:

```text
Backend changes while UI V2 types are stale
```

Control:

```text
OpenAPI generation
contract validation
typed modules
release gate
```

### 37.2 Legacy and UI V2 Route Conflict

Control:

```text
separate route prefixes
separate asset paths
route tests
```

### 37.3 Authentication Inconsistency

Control:

```text
reuse existing session guard
same-origin requests
401 tests
```

### 37.4 CSS and Asset Cache Defects

Control:

```text
content-hashed assets
build metadata
no shared mutable CSS filename
```

### 37.5 Duplicate Mutations

Control:

```text
busy state
no automatic mutation retry
fresh backend reconciliation
```

### 37.6 Feature Creep

Control:

```text
phase scope
documentation approval
no unapproved future features
```

### 37.7 Legacy Removal Too Early

Control:

```text
stabilization period
separate retirement approval
```

---

## 38. Developer Handoff Standard

A developer receiving the repository must be able to identify:

```text
Where UI V2 source lives
How UI V2 is built
How it reaches FastAPI
How routes are registered
How APIs are called
How components are styled
How pages are added
How tests are run
How preview works
How rollback works
```

Required handoff references:

```text
docs/ui-v2/README.md
UI_V2_MASTER_ARCHITECTURE.md
UI_V2_API_ARCHITECTURE.md
UI_V2_DESIGN_SYSTEM_FREEZE.md
UI_V2_MIGRATION_PLAN.md
UI_V2_TESTING_AND_RELEASE_GATE.md
UI_V2_DECISION_LOG.md
```

---

## 39. Migration Completion Criteria

UI V2 migration is complete only when:

1. UI V2 is the primary `/dashboard`;
2. approved MVP pages are migrated;
3. backend engine behavior remains preserved;
4. provider integrations remain preserved;
5. authentication remains preserved;
6. API contracts are documented;
7. UI V2 release gates pass;
8. build assets are versioned;
9. rollback route has been tested;
10. stabilization criteria are satisfied;
11. legacy retirement has been separately approved or explicitly deferred.

Migration completion does not automatically authorize legacy removal.

---

## 40. Acceptance Criteria

This migration plan is ready for approval when the following are accepted:

- UI V2 is developed in parallel;
- legacy `/dashboard` remains active initially;
- UI V2 uses `/dashboard-v2`;
- backend addition is limited to a UI Delivery Gate;
- pages migrate one at a time;
- existing APIs are used first;
- page dependency order is approved;
- deployment actions retain fresh backend readiness checks;
- real provider execution is excluded from ordinary UI testing;
- production cutover is a separate phase;
- `/dashboard-legacy` remains after cutover;
- legacy removal requires separate approval;
- per-phase tests and rollback are mandatory;
- exact change scope is mandatory;
- unrelated changes are prohibited;
- all architecture documents remain authoritative.

---

## 41. Frozen Rules After Approval

After approval:

1. UI V2 migration is parallel, not in-place.
2. Legacy UI remains active during development.
3. UI V2 begins under `/dashboard-v2`.
4. `frontend-v2/` is the only UI V2 source location.
5. Existing engines remain unchanged unless separately approved.
6. Existing APIs are used first.
7. UI Delivery Gate contains no business logic.
8. Page migration follows the approved dependency order.
9. Each phase has explicit acceptance criteria.
10. Each phase has an independent rollback.
11. UI V2 assets do not overwrite legacy assets.
12. Production cutover requires full approval.
13. `/dashboard-legacy` remains after cutover.
14. Legacy removal is a separate project change.
15. Ordinary UI validation must not execute a real provider deployment.
16. Mutations are not automatically retried.
17. Exact file scope and clean Git state are required for every phase.
18. Documentation changes follow revision governance.
19. No unapproved future feature is introduced during migration.
20. Production is not the first visual validation environment.

---

## 42. Next Documentation Step

After this document is reviewed and approved, the next document is:

```text
YGIT UI V2 Testing and Release Gate Specification
```

No UI V2 migration implementation is authorized by this draft.

---

## 43. Approval Record

| Role | Name | Decision | Date |
|---|---|---|---|
| Product Owner | Pending | Pending | Pending |
| Architecture Owner | Pending | Pending | Pending |
| Frontend Owner | Pending | Pending | Pending |
| Backend Owner | Pending | Pending | Pending |
| Release Owner | Pending | Pending | Pending |

---

**End of Document**
