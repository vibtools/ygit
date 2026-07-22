# YGIT UI V2 Master Architecture Specification

**Document ID:** YGIT-UIV2-ARCH-001<br>
**Version:** 0.1.0<br>
**Status:** Draft for Review<br>
**Owner:** YGIT Platform<br>
**Product:** YGIT<br>
**Company:** Vib Tools<br>
**Last Updated:** 2026-07-22<br>

---

## Revision History

| Version | Date | Status | Summary |
|---|---|---|---|
| 0.1.0 | 2026-07-22 | Draft for Review | Initial UI V2 master architecture specification |

---

## 1. Purpose

This document defines the master architecture for YGIT UI V2.

UI V2 will replace the current framework-free dashboard through a controlled, parallel migration. The existing YGIT backend, engines, provider integrations, worker system, authentication model, database, Redis, and production execution behavior remain authoritative and unchanged unless a later approved document explicitly defines a required change.

This specification establishes:

- the official UI V2 technology stack;
- the frontend-to-backend boundary;
- the UI delivery model;
- the application structure;
- page, feature, component, and shared-module responsibilities;
- authentication and session integration boundaries;
- state ownership rules;
- build and static asset delivery principles;
- migration isolation;
- rollback safety;
- extension rules for future YGIT pages and features.

This document does not define detailed API contracts or final visual design values. Those subjects will be frozen in separate documents.

---

## 2. Scope

### 2.1 In Scope

UI V2 architecture includes:

- a separate frontend application;
- React-based page rendering;
- TypeScript application code;
- Vite development and production builds;
- Mantine UI as the primary component framework;
- React Router for frontend navigation;
- an isolated `frontend-v2/` source directory;
- an authenticated preview route;
- reuse of existing YGIT APIs;
- a minimal backend UI Delivery Gate;
- frontend module and ownership boundaries;
- safe page-by-page migration;
- temporary coexistence with the legacy dashboard;
- production cutover and rollback architecture;
- extension patterns for future YGIT features.

### 2.2 Out of Scope

This document does not authorize:

- implementation of UI V2;
- removal of the current dashboard;
- modification of YGIT engines;
- modification of provider execution behavior;
- database schema changes;
- a CMS;
- a page builder;
- arbitrary database-driven layouts;
- arbitrary CSS, HTML, or JavaScript configuration;
- a new authentication system;
- a new backend business-logic layer;
- a new UI Engine;
- API contract changes;
- final colors, typography, spacing, or component appearance;
- production route switching.

---

## 3. Product Boundary

YGIT is an open-source deployment automation platform.

UI V2 is a presentation client for YGIT. It must not become a separate business-logic authority.

The permanent ownership model is:

```text
UI V2 renders and collects user intent
        ↓
FastAPI validates requests and sessions
        ↓
YGIT Engines own business rules
        ↓
Provider Layer communicates with GitHub and Cloudflare
        ↓
Infrastructure executes storage, database, queue, and deployment work
```

The following rule is mandatory:

> Frontend renders. Backend validates. Engines decide. Providers communicate. Workers execute.

UI V2 must never duplicate engine-owned rules as authoritative frontend logic.

---

## 4. Architecture Goals

UI V2 must:

1. allow new pages and features to be added without modifying unrelated pages;
2. reduce direct custom CSS and layout fragility;
3. provide reusable, consistent components;
4. preserve current YGIT backend behavior;
5. operate as a client of existing APIs;
6. remain independently buildable;
7. support isolated preview before production cutover;
8. allow the legacy UI to remain available during migration;
9. support future developer teams without requiring knowledge of all frontend internals;
10. keep production rollback simple;
11. prevent frontend failures from changing deployment execution;
12. keep authentication and provider secrets outside the browser;
13. produce versioned production assets;
14. support future visual and browser testing;
15. remain beginner-friendly for routine page development.

---

## 5. Architecture Non-Goals

UI V2 will not:

- own deployment readiness rules;
- determine provider permissions;
- store GitHub or Cloudflare credentials;
- communicate directly with provider APIs;
- access PostgreSQL or Redis directly;
- enqueue worker jobs directly;
- replace FastAPI;
- replace Keycloak or Vib ID;
- expose backend secrets;
- dynamically execute administrator-provided code;
- allow feature pages to bypass the shared API client;
- use arbitrary per-page design systems;
- mix legacy DOM scripting with React inside the same UI V2 application root.

---

## 6. Official Technology Decisions

The official UI V2 stack is:

| Layer | Decision |
|---|---|
| UI framework | React |
| Language | TypeScript |
| Build tool | Vite |
| Component framework | Mantine UI |
| Client-side routing | React Router |
| Styling foundation | Mantine theme system and controlled CSS modules where required |
| HTTP transport | Browser Fetch API through a shared API client |
| Authentication | Existing YGIT session and Vib ID/Keycloak flow |
| Backend | Existing FastAPI application |
| Production delivery | Static Vite build served through the YGIT application |
| Preview route | `/dashboard-v2` |
| Legacy route during migration | `/dashboard` |
| Future rollback route after cutover | `/dashboard-legacy` |

No additional frontend framework is approved by this document.

---

## 7. High-Level System Architecture

```text
User Browser
    |
    | GET /dashboard-v2
    v
UI Delivery Gate
    |
    | authenticated session required
    v
Vite Production Build
    |
    | React + TypeScript + Mantine
    v
UI V2 Application
    |
    | relative same-origin requests
    | /api/v1/*
    v
FastAPI API Layer
    |
    v
YGIT Engine Layer
    |
    v
Provider Layer
    |
    v
PostgreSQL / Redis / R2 / GitHub / Cloudflare
```

UI V2 is delivered by the YGIT application but remains architecturally independent from backend business logic.

---

## 8. Repository Structure

The approved source structure is:

```text
ygit-platform/
├── backend/
├── frontend/
│   └── dashboard/                 # Existing legacy UI
├── frontend-v2/                   # New UI V2 source
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   ├── pages/
│   │   ├── features/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── api/
│   │   ├── hooks/
│   │   ├── theme/
│   │   ├── assets/
│   │   ├── types/
│   │   └── utils/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
└── docs/
    └── ui-v2/
```

Generated build output must not be treated as hand-maintained source code.

The final generated static output location will be defined by the implementation and delivery documents. The source of truth remains `frontend-v2/`.

---

## 9. Frontend Application Structure

### 9.1 `src/app/`

Owns application bootstrap and global composition.

Responsibilities:

- React application entry;
- router creation;
- global providers;
- authentication bootstrap state;
- error boundary registration;
- Mantine provider setup;
- application-level loading state;
- UI build metadata exposure.

It must not contain feature-specific business behavior.

Suggested structure:

```text
src/app/
├── App.tsx
├── bootstrap.tsx
├── router.tsx
├── providers.tsx
└── error-boundary.tsx
```

### 9.2 `src/pages/`

Owns route-level page composition.

A page:

- maps to a frontend route;
- composes layouts and feature components;
- may request data through feature modules;
- does not call raw APIs directly;
- does not contain provider or engine business logic.

Suggested initial pages:

```text
src/pages/
├── dashboard/
├── projects/
├── project-details/
├── deployments/
├── connected-accounts/
├── settings/
└── not-found/
```

Future pages must follow the same structure.

### 9.3 `src/features/`

Owns feature-specific UI behavior.

Examples:

```text
src/features/
├── projects/
├── repository-analysis/
├── deployments/
├── connected-accounts/
├── github/
├── cloudflare/
└── platform-status/
```

A feature may contain:

- feature components;
- feature hooks;
- frontend-only data transformation;
- API module adapters;
- typed view models;
- feature tests.

A feature must not:

- access another feature’s private internals;
- implement backend business rules as authority;
- communicate directly with GitHub or Cloudflare;
- access browser storage for secrets;
- call raw endpoints outside the shared API layer.

### 9.4 `src/components/`

Owns reusable UI components that are not feature-specific.

Categories:

```text
src/components/
├── actions/
├── data-display/
├── feedback/
├── forms/
├── navigation/
└── surfaces/
```

Examples:

- action buttons;
- status badges;
- page headers;
- loading indicators;
- empty states;
- error states;
- confirmation dialogs;
- pagination controls;
- reusable cards and panels.

Feature-specific cards remain inside their owning feature.

### 9.5 `src/layouts/`

Owns reusable page shells.

Initial layout responsibilities:

- application shell;
- sidebar;
- topbar;
- page content frame;
- authenticated layout;
- preview environment indicator when required.

Layouts must not fetch feature data.

### 9.6 `src/api/`

Owns all frontend communication with YGIT APIs.

This directory will be fully specified in the separate UI V2 API Architecture document.

At master-architecture level, it must provide:

- one shared request client;
- typed request and response boundaries;
- standard error normalization;
- session-expiry handling;
- same-origin request behavior;
- feature-specific API modules;
- no direct endpoint calls from pages or components.

### 9.7 `src/hooks/`

Owns reusable frontend hooks that are not private to a single feature.

Hooks must remain presentation-focused and must not become an alternative business-logic layer.

### 9.8 `src/theme/`

Owns the code-defined UI theme.

Initial responsibilities:

- Mantine theme configuration;
- semantic color tokens;
- typography tokens;
- spacing and radius presets;
- component defaults;
- dark-first appearance.

The first UI V2 release will not require database-driven theme control.

### 9.9 `src/assets/`

Owns source-controlled UI assets imported by the application.

Examples:

- logos;
- icons not provided by the approved icon source;
- illustrations;
- local image assets.

Secrets and provider credentials are prohibited.

### 9.10 `src/types/`

Owns shared frontend-only TypeScript types.

Backend API models should be generated or defined through the API architecture rather than duplicated across pages.

### 9.11 `src/utils/`

Owns small pure utilities.

Utilities must:

- have no hidden network calls;
- have no feature ownership;
- remain independently testable;
- avoid global mutable state.

---

## 10. UI Delivery Gate

UI V2 requires one lightweight backend delivery boundary.

The UI Delivery Gate is not a business engine.

Its responsibility is limited to:

1. protecting the UI V2 route with the existing session model;
2. serving the generated React application;
3. serving hashed static assets;
4. returning the application entry document for valid frontend routes;
5. preserving existing `/api/v1/*` behavior;
6. preventing path traversal and invalid static access;
7. supporting a controlled preview route.

The initial route model is:

```text
/dashboard
    → existing legacy dashboard

/dashboard-v2
    → UI V2 preview application

/dashboard-v2/*
    → UI V2 application route fallback

/dashboard-v2/assets/*
    → generated hashed static assets
```

The UI Delivery Gate must not:

- add engine logic;
- modify deployment state;
- access provider credentials;
- perform GitHub or Cloudflare actions;
- change API response contracts;
- create a new user session mechanism;
- expose filesystem paths;
- serve arbitrary files.

---

## 11. Authentication Architecture

UI V2 will reuse the existing YGIT authentication architecture.

```text
User requests /dashboard-v2
        ↓
Existing YGIT authentication/session guard
        ↓
Unauthenticated
        → existing Vib ID/Keycloak login flow
        ↓
Authenticated
        → UI V2 application served
        ↓
UI V2 calls /api/v1/* with session cookie
        ↓
FastAPI validates the session
```

Frontend requirements:

- use same-origin API URLs;
- include browser credentials for authenticated requests;
- never receive or store Keycloak client secrets;
- never store GitHub or Cloudflare access tokens;
- handle expired sessions through the shared API client;
- treat backend authorization responses as authoritative.

UI V2 must not determine access by hiding buttons alone. Backend authorization remains mandatory.

---

## 12. Routing Architecture

React Router owns client-side navigation under the UI V2 base route.

Initial route intent:

```text
/dashboard-v2
/dashboard-v2/projects
/dashboard-v2/projects/:projectId
/dashboard-v2/deployments
/dashboard-v2/connected-accounts
/dashboard-v2/settings
```

Rules:

- all UI V2 routes remain under one base path during preview;
- route definitions are centralized;
- each page is independently lazy-loadable when appropriate;
- unknown routes render a UI V2 not-found page;
- backend API routes are never handled by React Router;
- route paths do not define business authorization;
- deep links must load the same application entry document.

Detailed route names may be refined before implementation, but the centralized route ownership rule is frozen.

---

## 13. Data and State Ownership

UI V2 state is divided into four categories.

### 13.1 Server State

Examples:

- projects;
- repository analysis;
- deployment history;
- connected accounts;
- platform status.

Authority: FastAPI and YGIT engines.

Frontend responsibility:

- request;
- display;
- refresh;
- show loading and error states;
- submit explicit user actions.

Frontend must not treat cached values as permanent authority.

### 13.2 Route State

Examples:

- current page;
- selected project identifier;
- filters represented in the URL;
- pagination represented in the URL where approved.

Authority: React Router and URL state.

### 13.3 Local UI State

Examples:

- modal open or closed;
- selected tab;
- temporary form input;
- local disclosure state;
- transient notification visibility.

Authority: the owning component or feature.

### 13.4 Global Presentation State

Examples:

- current theme preset;
- shell navigation state;
- application-wide notification channel;
- authenticated-user presentation details.

Authority: application providers.

Global state must be kept minimal. A global store is not approved by this document.

---

## 14. API Integration Boundary

UI V2 uses existing YGIT APIs first.

```text
Page
    ↓
Feature module
    ↓
Feature API module
    ↓
Shared API client
    ↓
/api/v1/*
```

Mandatory rules:

- pages do not call `fetch()` directly;
- reusable UI components do not call APIs;
- feature modules cannot call provider APIs;
- backend errors are normalized centrally;
- authentication failures are handled centrally;
- API types are not manually redefined in multiple files;
- new endpoints require separate backend documentation and approval;
- UI V2 cannot create undocumented API behavior.

Detailed request, response, error, pagination, versioning, and compatibility contracts will be defined in `UI_V2_API_ARCHITECTURE.md`.

---

## 15. Component Architecture

Mantine UI is the primary component foundation.

UI V2 will prefer:

1. Mantine primitives;
2. YGIT wrappers around repeated patterns;
3. feature-specific composition;
4. custom CSS only where Mantine configuration is insufficient.

A component wrapper is justified when it standardizes:

- YGIT naming;
- default variants;
- accessibility behavior;
- loading behavior;
- error behavior;
- common spacing;
- repeated application patterns.

Examples:

```text
YGITPageHeader
YGITStatusBadge
YGITEmptyState
YGITErrorState
YGITConfirmDialog
YGITDataPanel
```

Rules:

- feature pages must not define independent button systems;
- page-specific colors are prohibited unless approved by the design freeze;
- inline absolute positioning for primary page structure is prohibited;
- layout must use normal document flow, Flexbox, Grid, or Mantine layout components;
- z-index values must not be invented per feature;
- reusable components must expose typed props;
- component behavior must remain deterministic.

The final component inventory and visual variants will be defined by the UI V2 Design System Freeze document.

---

## 16. Styling Architecture

The styling hierarchy is:

```text
Mantine theme
    ↓
YGIT semantic theme tokens
    ↓
YGIT shared component defaults
    ↓
Feature-level composition
    ↓
Minimal scoped CSS modules when required
```

Prohibited patterns:

- multiple global stylesheets overriding each other;
- historical CSS patches appended indefinitely;
- broad global selectors for feature-specific behavior;
- uncontrolled `!important`;
- page layout based on invisible spacer elements;
- primary content placed outside normal document flow;
- arbitrary runtime CSS from the database;
- inline style values repeated across pages.

The detailed typography, color, spacing, radius, component, icon, logo, and responsive values are deferred to the Design System Freeze.

---

## 17. Asset Architecture

Vite will produce versioned production assets.

Expected build characteristics:

```text
index.html
assets/
├── app.<content-hash>.js
├── app.<content-hash>.css
└── imported-assets.<content-hash>.*
```

Rules:

- generated asset names must be content-versioned;
- source HTML must reference the generated manifest or build output;
- the browser must not depend on a permanently named mutable CSS file;
- the UI build must expose a build identifier;
- the deployed UI build must be traceable to a Git commit;
- legacy and UI V2 assets must not overwrite each other;
- UI V2 assets remain under the UI V2 route namespace.

Detailed cache headers will be specified in the UI V2 Testing and Release Gate document.

---

## 18. Error Handling Architecture

Every route and feature must support:

- initial loading;
- successful data;
- empty data;
- recoverable error;
- partial data where supported;
- session expiration;
- authorization denial;
- not found;
- unexpected application error.

Rules:

- raw backend objects must never be rendered directly;
- raw JavaScript errors must not be shown to users;
- error messages must preserve safe backend meaning;
- failed optional reads must not delete previously loaded page data;
- destructive actions require explicit confirmation;
- retry behavior must be bounded;
- deployment actions must never be automatically retried by the UI;
- application-level crashes must be contained by an error boundary.

---

## 19. Security Architecture

UI V2 must:

- use same-origin API requests;
- rely on backend session validation;
- escape or safely render backend-provided text;
- avoid raw HTML rendering;
- avoid browser storage for secrets;
- avoid embedding provider tokens in URLs;
- avoid direct provider API requests;
- protect destructive actions with confirmation and backend authorization;
- preserve CSRF protections required by the existing backend model;
- use generated assets only from approved build output;
- avoid runtime code injection from configuration values.

Security-sensitive decisions remain backend-owned.

---

## 20. Extensibility Model

Future YGIT developers must be able to add a feature through an isolated path.

Approved feature extension flow:

```text
1. Document backend capability
2. Confirm or define API contract
3. Add typed API module
4. Add feature directory
5. Add route-level page when required
6. Compose approved shared components
7. Add tests
8. Pass preview and release gates
```

A future feature must not require modifying unrelated feature internals.

Example:

```text
src/features/analytics/
├── api.ts
├── types.ts
├── hooks.ts
├── components/
└── tests/
```

If the feature has a page:

```text
src/pages/analytics/
└── AnalyticsPage.tsx
```

If the feature has navigation:

- route registration is updated centrally;
- navigation registration is updated centrally;
- permissions remain backend-authoritative.

---

## 21. Page Creation Standard

Every new page must define:

- route;
- page title;
- page purpose;
- APIs used;
- loading state;
- empty state;
- error state;
- authorization behavior;
- responsive behavior;
- test coverage;
- acceptance criteria.

A page should primarily compose:

```text
App Layout
    ↓
Page Header
    ↓
Feature Sections
    ↓
Shared Feedback States
```

A page must not:

- introduce a new global layout system;
- create its own theme;
- access APIs directly;
- duplicate a shared component without justification;
- bypass the route registry;
- define backend business rules.

---

## 22. Development Modes

### 22.1 Local Development

```text
Vite development server
    ↓ proxy or configured same-origin development path
FastAPI local application
```

The detailed proxy configuration will be documented during implementation.

### 22.2 Preview Deployment

```text
/dashboard
    → legacy UI

/dashboard-v2
    → UI V2 preview
```

Preview must use the same backend APIs and authentication model as the current dashboard.

### 22.3 Production Cutover

Only after documentation, implementation, testing, and visual approval:

```text
/dashboard
    → UI V2

/dashboard-legacy
    → legacy UI rollback route
```

The route switch must be independently reversible.

### 22.4 Legacy Retirement

The legacy UI may be removed only after:

- UI V2 feature parity is approved;
- production stability period is complete;
- rollback requirements are satisfied;
- a separate removal change is approved.

---

## 23. Build and Deployment Boundary

UI V2 build steps may add frontend build tooling, but must not change YGIT runtime business behavior.

The final deployment pipeline must:

1. install locked frontend dependencies;
2. run TypeScript validation;
3. build UI V2;
4. verify generated assets;
5. package the UI V2 build;
6. start the existing FastAPI application;
7. serve UI V2 through the approved delivery route.

A frontend build failure must fail the UI V2 build stage. It must not partially overwrite the active legacy UI.

---

## 24. Rollback Architecture

Rollback is based on route isolation.

Before cutover:

```text
/dashboard       → legacy
/dashboard-v2    → UI V2 preview
```

After cutover:

```text
/dashboard        → UI V2
/dashboard-legacy → legacy
```

Rollback principles:

- no database migration is required solely to switch frontend routes;
- rollback must not change engine state;
- rollback must not modify connected accounts;
- rollback must not cancel deployments;
- UI asset versions must remain distinguishable;
- old and new builds must not share mutable filenames;
- route switching must be independently testable.

---

## 25. Observability Requirements

UI V2 must expose enough information to identify the running frontend build.

Required build metadata:

- UI version;
- Git commit SHA;
- build timestamp or build identifier;
- application environment label where approved.

Minimum diagnostic availability:

```text
window.YGIT_UI_BUILD
```

or an equivalent immutable application metadata object.

The exact implementation will be defined later.

UI V2 must not expose secrets, environment credentials, or provider tokens through diagnostics.

---

## 26. Documentation Set

This master architecture is the first document in the UI V2 documentation set.

The complete planned set is:

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

Document responsibilities:

| Document | Responsibility |
|---|---|
| UI V2 Master Architecture | System structure and boundaries |
| UI V2 API Architecture | Request, response, error, typing, and compatibility contracts |
| UI V2 Design System Freeze | Final visual tokens and component variants |
| UI V2 Migration Plan | Page-by-page transition |
| UI V2 Testing and Release Gate | Build, browser, responsive, release, and rollback checks |
| UI V2 Decision Log | Architectural decisions and revisions |
| UI V2 README | Documentation entry point |

---

## 27. Governance and Freeze Process

Document status lifecycle:

```text
Draft
  ↓
Review
  ↓
Approved
  ↓
Frozen
  ↓
Implementation
```

A frozen architectural decision may be changed only through:

1. a documented change request;
2. impact analysis;
3. revision history update;
4. version increment;
5. explicit approval.

Implementation must not begin before this document is approved.

---

## 28. Architecture Acceptance Criteria

This specification is ready for approval when all of the following are accepted:

- React is confirmed as the UI framework;
- TypeScript is mandatory;
- Vite is confirmed as the build tool;
- Mantine UI is confirmed as the component framework;
- React Router is confirmed for frontend routing;
- `frontend-v2/` is confirmed as the source boundary;
- the legacy UI remains untouched during initial UI V2 work;
- `/dashboard-v2` is confirmed as the preview route;
- existing `/api/v1/*` APIs remain authoritative;
- no new UI Engine is created;
- the UI Delivery Gate remains delivery-only;
- authentication reuses the existing YGIT session;
- UI V2 contains no engine or provider business logic;
- generated assets are versioned;
- migration is page-by-page;
- route-level rollback remains available;
- detailed API and visual contracts are deferred to their dedicated documents.

---

## 29. Frozen Architectural Rules After Approval

After approval, the following rules become mandatory:

1. UI V2 source lives in `frontend-v2/`.
2. UI V2 uses React, TypeScript, Vite, Mantine UI, and React Router.
3. UI V2 is a client of YGIT APIs.
4. Existing engines remain the business-logic authority.
5. UI V2 does not communicate directly with providers.
6. UI V2 does not access the database or Redis.
7. The backend addition is a minimal UI Delivery Gate, not a UI Engine.
8. Legacy UI and UI V2 coexist during migration.
9. UI V2 begins at `/dashboard-v2`.
10. New pages use centralized routing and shared components.
11. Pages and components do not call raw APIs directly.
12. UI V2 uses code-defined theme configuration in its initial release.
13. Arbitrary database-driven CSS, HTML, layout, or JavaScript is prohibited.
14. Static assets are content-versioned.
15. Production cutover occurs only after separate migration and release approvals.
16. Legacy removal requires a separate approved change.

---

## 30. Next Documentation Step

After this document is reviewed and approved, the next document is:

```text
YGIT UI V2 API Architecture Specification
```

No UI V2 implementation is authorized by this draft.

---

## 31. Approval Record

| Role | Name | Decision | Date |
|---|---|---|---|
| Product Owner | Pending | Pending | Pending |
| Architecture Owner | Pending | Pending | Pending |
| Engineering Owner | Pending | Pending | Pending |

---

**End of Document**
