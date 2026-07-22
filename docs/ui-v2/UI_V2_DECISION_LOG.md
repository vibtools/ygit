# YGIT UI V2 Decision Log

**Document ID:** YGIT-UIV2-DEC-001<br>
**Version:** 0.1.0<br>
**Status:** Active Draft<br>
**Owner:** YGIT Platform<br>
**Product:** YGIT<br>
**Company:** Vib Tools<br>
**Related Documents:**<br>
- `UI_V2_MASTER_ARCHITECTURE.md`<br>
- `UI_V2_API_ARCHITECTURE.md`<br>
- `UI_V2_DESIGN_SYSTEM_FREEZE.md`<br>
- `UI_V2_MIGRATION_PLAN.md`<br>
- `UI_V2_TESTING_AND_RELEASE_GATE.md`<br>

**Last Updated:** 2026-07-22<br>

---

## Revision History

| Version | Date | Status | Summary |
|---|---|---|---|
| 0.1.0 | 2026-07-22 | Active Draft | Initial UI V2 architectural decision log |

---

## 1. Purpose

This document records the significant architectural, technical, visual, migration, testing, and governance decisions for YGIT UI V2.

Its purpose is to ensure that future YGIT developers can understand:

- what was decided;
- why it was decided;
- which alternatives were rejected;
- what consequences the decision creates;
- which documents and implementation areas are affected;
- whether the decision is proposed, approved, frozen, superseded, or deprecated.

This log prevents the UI V2 architecture from depending on undocumented assumptions or personal memory.

---

## 2. Decision Log Authority

This document is the authoritative index of UI V2 decisions.

Detailed specifications remain authoritative for implementation behavior.

The relationship is:

```text
Decision Log
    → records why and when a decision was made

Architecture Documents
    → define the complete approved behavior

Implementation
    → must conform to both
```

When this log conflicts with a frozen architecture specification, the frozen specification remains authoritative until an approved change updates both documents.

---

## 3. Decision Status Model

Every decision uses one of the following statuses:

| Status | Meaning |
|---|---|
| Proposed | Under discussion; not approved |
| Accepted | Approved architectural direction |
| Frozen | Mandatory for implementation |
| Deferred | Valid topic postponed to a later phase |
| Rejected | Evaluated and not approved |
| Superseded | Replaced by a newer decision |
| Deprecated | Still present temporarily but scheduled for removal |
| Withdrawn | Proposal removed before approval |

---

## 4. Decision Record Format

Every decision record must include:

```text
Decision ID
Title
Date
Status
Context
Decision
Rationale
Alternatives Considered
Consequences
Risks and Controls
Affected Areas
Related Decisions
Supersedes / Superseded By
Approval
```

Decision IDs use:

```text
UIV2-ADR-###
```

ADR means Architecture Decision Record.

---

# UIV2-ADR-001 — Build UI V2 as a Separate Frontend Application

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

The current YGIT dashboard uses framework-free HTML, CSS, and JavaScript.

The existing UI has accumulated:

- multiple stylesheet authorities;
- broad selectors;
- appended visual corrections;
- responsive overrides;
- layout dependence on absolute positioning;
- mutable static asset names;
- limited browser-level layout validation.

Continuing to extend the existing frontend would increase maintenance cost and make future pages harder to manage.

## Decision

Create UI V2 as a separate frontend application located at:

```text
frontend-v2/
```

The current frontend remains at:

```text
frontend/dashboard/
```

UI V2 will be built and tested independently before replacing the current dashboard.

## Rationale

This provides:

- strict source isolation;
- safe parallel development;
- independent build tooling;
- controlled migration;
- simple rollback;
- no need to rewrite backend engines;
- no need to destabilize the current production dashboard.

## Alternatives Considered

### Continue Patching the Current Frontend

**Rejected because:**

- existing CSS architecture is fragile;
- future pages would increase selector conflicts;
- browser visual behavior is difficult to predict;
- stale asset problems would remain;
- long-term maintenance would worsen.

### Rewrite the Existing Frontend In Place

**Rejected because:**

- production UI would be modified during migration;
- rollback would be harder;
- partial migration would mix old and new patterns;
- unrelated pages could be affected.

## Consequences

Positive:

- UI V2 can fail without replacing the legacy dashboard;
- developers gain a clean structure;
- page-by-page migration becomes possible.

Negative:

- two frontends exist temporarily;
- build and route packaging must support both;
- feature parity must be tracked.

## Risks and Controls

| Risk | Control |
|---|---|
| Duplicate frontend behavior | Migration plan and feature-parity tracking |
| Conflicting asset paths | Separate route namespace and hashed assets |
| Legacy UI retained too long | Stabilization and retirement phases |
| Developers update wrong frontend | Documentation and directory ownership |

## Affected Areas

```text
frontend-v2/
frontend/dashboard/
backend UI delivery routes
docs/ui-v2/
```

## Related Decisions

- UIV2-ADR-007
- UIV2-ADR-008
- UIV2-ADR-021

## Approval

Pending.

---

# UIV2-ADR-002 — Use React as the UI Framework

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

YGIT will require many future pages, reusable controls, status views, tables, forms, dialogs, and feature-specific interfaces.

A component-oriented framework is required to avoid rebuilding page structure repeatedly.

## Decision

Use:

```text
React
```

as the UI V2 rendering framework.

## Rationale

React provides:

- reusable components;
- predictable composition;
- broad developer familiarity;
- strong TypeScript support;
- compatibility with the selected component and testing tools;
- maintainable feature isolation.

## Alternatives Considered

### Continue with Vanilla JavaScript

**Rejected because:**

- repeated UI patterns would require manual lifecycle management;
- future feature growth would increase DOM complexity;
- reusable stateful components would be harder to standardize.

### Vue

**Rejected for this architecture because:**

- React better matches the selected Mantine ecosystem;
- the project requires one clear official stack;
- no product requirement justifies supporting multiple frontend frameworks.

### Angular

**Rejected because:**

- higher initial framework complexity;
- unnecessary for the selected isolated frontend model;
- heavier architecture than required for the MVP dashboard.

## Consequences

- pages and components use React conventions;
- React-specific testing and lint rules become mandatory;
- developers must avoid direct DOM manipulation except approved integrations.

## Risks and Controls

| Risk | Control |
|---|---|
| Unstructured component growth | Feature and component ownership rules |
| Excessive global state | Minimal global-state policy |
| Direct API calls in components | Shared API client and lint rules |

## Related Decisions

- UIV2-ADR-003
- UIV2-ADR-005
- UIV2-ADR-012

## Approval

Pending.

---

# UIV2-ADR-003 — Use TypeScript in Strict Mode

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

UI V2 must consume backend API contracts safely and support future development teams.

Untyped frontend data would increase the risk of:

- invalid API assumptions;
- object rendering errors;
- unsafe optional fields;
- broken feature integrations;
- difficult refactoring.

## Decision

Use:

```text
TypeScript
```

with strict compiler validation.

## Rationale

TypeScript provides:

- compile-time API shape validation;
- safer component interfaces;
- clearer feature contracts;
- easier refactoring;
- reduced accidental misuse of backend data.

## Alternatives Considered

### JavaScript with JSDoc

**Rejected because:**

- weaker enforcement;
- less predictable API contract integration;
- easier for invalid types to enter production.

### Partial TypeScript

**Rejected because:**

- inconsistent safety;
- migration between typed and untyped modules creates hidden risk.

## Consequences

- all UI V2 source uses TypeScript or TSX;
- generated API types become part of the build;
- TypeScript failures block release.

## Risks and Controls

| Risk | Control |
|---|---|
| Developers bypass types with `any` | ESLint restrictions |
| Generated types become stale | OpenAPI contract gate |
| Strict settings slow initial work | Shared patterns and generated types |

## Related Decisions

- UIV2-ADR-010
- UIV2-ADR-011
- UIV2-ADR-026

## Approval

Pending.

---

# UIV2-ADR-004 — Use Vite for Development and Production Builds

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

UI V2 requires:

- fast local development;
- TypeScript support;
- production bundling;
- content-hashed assets;
- predictable static output;
- simple backend delivery.

## Decision

Use:

```text
Vite
```

as the UI V2 development server and production build tool.

## Rationale

Vite provides:

- fast local startup;
- React and TypeScript support;
- production bundling;
- content-hashed output;
- clear static build artifacts;
- straightforward subpath deployment.

## Alternatives Considered

### Custom Build Scripts

**Rejected because:**

- unnecessary maintenance;
- higher risk of asset mistakes;
- no product-specific benefit.

### Next.js

**Rejected for the initial UI V2 architecture because:**

- YGIT already has FastAPI as the backend;
- server-side rendering is not required for the authenticated dashboard;
- another server runtime would increase deployment complexity.

### Create React App

**Rejected because:**

- less suitable for the selected modern build architecture;
- unnecessary legacy tooling.

## Consequences

- the production UI is a static build;
- build assets use content hashes;
- Vite configuration becomes part of the frozen platform foundation.

## Risks and Controls

| Risk | Control |
|---|---|
| Incorrect base path | Route and asset tests |
| Stale build assets | Content hashes and cache contract |
| Build metadata mismatch | Build identity gate |

## Related Decisions

- UIV2-ADR-018
- UIV2-ADR-019
- UIV2-ADR-025

## Approval

Pending.

---

# UIV2-ADR-005 — Use Mantine UI as the Primary Component Framework

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

YGIT requires professional components without building a full component library from zero.

Required components include:

- buttons;
- inputs;
- forms;
- cards;
- tables;
- modals;
- drawers;
- notifications;
- navigation;
- tooltips;
- badges.

## Decision

Use:

```text
Mantine UI
```

as the primary UI component framework.

## Rationale

Mantine provides:

- ready-made React components;
- theme configuration;
- dark-theme support;
- accessibility foundations;
- responsive primitives;
- reduced custom CSS;
- fast page development.

## Alternatives Considered

### Build All Components Internally

**Rejected because:**

- high implementation cost;
- more accessibility risk;
- more testing burden;
- unnecessary duplication of mature infrastructure.

### Bootstrap

**Rejected because:**

- strong generic template appearance;
- weaker match for the intended premium developer-product identity.

### Material UI

**Rejected because:**

- risk of a recognizable Material Design appearance;
- conflicts with the requested visual direction.

### Tailwind Plus Multiple Headless Libraries

**Rejected for the initial phase because:**

- more composition work;
- larger design-system burden;
- less beginner-friendly than one primary component framework.

## Consequences

- YGIT components should wrap Mantine only where repeated product behavior requires it;
- feature developers should prefer Mantine primitives;
- theme values are centralized.

## Risks and Controls

| Risk | Control |
|---|---|
| Generic Mantine appearance | Frozen YGIT theme and component defaults |
| Excessive wrapper components | Wrapper governance |
| Framework-specific lock-in | Keep business logic outside UI components |

## Related Decisions

- UIV2-ADR-014
- UIV2-ADR-015
- UIV2-ADR-016

## Approval

Pending.

---

# UIV2-ADR-006 — Use React Router for Client-Side Routing

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

UI V2 needs:

- multiple pages;
- deep links;
- route parameters;
- browser back and forward support;
- preview subpath routing;
- centralized route registration.

## Decision

Use:

```text
React Router
```

for UI V2 navigation.

## Rationale

React Router integrates directly with React and supports the required page model without introducing another application framework.

## Alternatives Considered

### Custom Router

**Rejected because:**

- unnecessary maintenance;
- increased deep-link and history risk.

### Full-Page Server Navigation

**Rejected because:**

- less suitable for the isolated React application;
- repeated application reloads;
- weaker page composition.

## Consequences

- all UI V2 routes are centrally registered;
- the backend must provide SPA fallback;
- routes remain under the approved base path.

## Risks and Controls

| Risk | Control |
|---|---|
| Backend/API route conflict | Route namespace and tests |
| Deep-link 404 | SPA fallback |
| Route mutation replay | Mutation and navigation tests |

## Related Decisions

- UIV2-ADR-007
- UIV2-ADR-008
- UIV2-ADR-022

## Approval

Pending.

---

# UIV2-ADR-007 — Use `/dashboard-v2` as the Preview Route

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

UI V2 must be testable in a deployed environment while the existing dashboard remains operational.

## Decision

During migration:

```text
/dashboard
    → legacy dashboard

/dashboard-v2
    → UI V2 preview
```

## Rationale

This provides:

- production-safe isolation;
- easy comparison;
- explicit preview access;
- no premature route replacement;
- simple rollback.

## Alternatives Considered

### Replace `/dashboard` Immediately

**Rejected because:**

- no safe stabilization period;
- production becomes the first full integration environment;
- rollback becomes more urgent and error-prone.

### Use a Separate Domain

**Deferred because:**

- not required for the initial architecture;
- same-origin authentication and API access are simpler under one application domain.

## Consequences

- UI V2 router needs a base path;
- backend delivery must distinguish legacy and V2 routes;
- preview tests must validate authentication and deep links.

## Related Decisions

- UIV2-ADR-001
- UIV2-ADR-008
- UIV2-ADR-021

## Approval

Pending.

---

# UIV2-ADR-008 — Add a Minimal UI Delivery Gate, Not a UI Engine

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

The backend must serve UI V2 and protect its routes.

A large new backend subsystem is unnecessary.

## Decision

Add a lightweight UI Delivery Gate responsible only for:

- authentication protection;
- serving the UI V2 entry document;
- serving static assets;
- SPA fallback;
- safe build metadata delivery where approved.

The gate is not an engine.

## Rationale

UI delivery is presentation infrastructure, not business logic.

Creating a UI Engine would violate the YGIT engine-responsibility model and add unnecessary complexity.

## Alternatives Considered

### Create a UI Engine

**Rejected because:**

- no business domain requires it;
- would mix presentation delivery with engine architecture;
- unnecessary models and services.

### Serve UI from an Independent Frontend Server

**Deferred because:**

- adds deployment and authentication complexity;
- not required for the initial isolated migration.

## Consequences

- backend changes remain narrow;
- no new database model is required;
- no provider or worker behavior changes.

## Risks and Controls

| Risk | Control |
|---|---|
| Business logic enters delivery route | Route tests and architecture review |
| Arbitrary file serving | Restricted static path and traversal tests |
| Auth inconsistency | Reuse existing authentication guard |

## Related Decisions

- UIV2-ADR-007
- UIV2-ADR-009
- UIV2-ADR-020

## Approval

Pending.

---

# UIV2-ADR-009 — Reuse Existing YGIT Authentication and Session Handling

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

YGIT already uses Vib ID and Keycloak through the existing backend authentication architecture.

UI V2 does not require a second authentication system.

## Decision

UI V2 reuses:

- existing login flow;
- existing session cookie;
- existing backend authorization;
- same-origin authenticated API requests.

## Rationale

This avoids:

- duplicated authentication logic;
- additional secrets;
- new token storage;
- inconsistent authorization;
- unnecessary user migration.

## Alternatives Considered

### Store Access Tokens in the Browser

**Rejected because:**

- increases secret-exposure risk;
- conflicts with existing session architecture.

### Implement a Separate UI V2 Login

**Rejected because:**

- duplicates identity behavior;
- creates inconsistent user experience;
- introduces new backend and security work.

## Consequences

- API client uses `credentials: include`;
- 401 and 403 behavior is centralized;
- UI controls are not authoritative authorization.

## Risks and Controls

| Risk | Control |
|---|---|
| Session-expiry loops | Central 401 handling |
| Hidden button treated as authorization | Backend enforcement |
| Credential exposure | No provider or auth secrets in browser storage |

## Related Decisions

- UIV2-ADR-008
- UIV2-ADR-010
- UIV2-ADR-020

## Approval

Pending.

---

# UIV2-ADR-010 — Use Existing `/api/v1` Endpoints First

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

The current backend already exposes APIs for YGIT features.

Building a new API system solely for UI V2 would duplicate behavior and increase risk.

## Decision

UI V2 uses:

```text
/api/v1/*
```

as the authoritative backend boundary.

New endpoints may be added only when current APIs cannot support an approved feature.

## Rationale

This preserves:

- engine authority;
- API reuse;
- backward compatibility;
- smaller migration scope;
- lower backend risk.

## Alternatives Considered

### Build a Separate UI V2 API Namespace

**Rejected because:**

- duplicates existing contracts;
- creates parallel backend behavior;
- increases maintenance.

### Call Engine Services Directly

**Rejected because:**

- frontend cannot import backend internals;
- violates architecture layers.

## Consequences

- current API limitations may require isolated approved extensions;
- UI V2 must adapt current response shapes centrally.

## Related Decisions

- UIV2-ADR-011
- UIV2-ADR-012
- UIV2-ADR-013

## Approval

Pending.

---

# UIV2-ADR-011 — Use One Shared Frontend API Client

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

Direct API calls across pages would create inconsistent:

- authentication handling;
- timeout behavior;
- retries;
- errors;
- headers;
- response parsing.

## Decision

All UI V2 API requests pass through one shared API client.

Approved flow:

```text
Page
    ↓
Feature hook/service
    ↓
Domain API module
    ↓
Shared API client
    ↓
/api/v1/*
```

## Rationale

This centralizes transport behavior while preserving feature ownership.

## Alternatives Considered

### Raw `fetch()` in Every Feature

**Rejected because:**

- duplicated error logic;
- inconsistent credentials;
- inconsistent retries;
- difficult contract migration.

### Separate HTTP Client Per Feature

**Rejected because:**

- transport behavior would drift;
- unnecessary duplication.

## Consequences

- routine features do not modify transport behavior;
- transport-client changes receive broader review;
- direct page-level `fetch()` is prohibited.

## Risks and Controls

| Risk | Control |
|---|---|
| Shared client becomes feature-heavy | Transport-only responsibility |
| One change affects all modules | Dedicated tests and release gate |
| Pages bypass client | Lint rules and code review |

## Related Decisions

- UIV2-ADR-010
- UIV2-ADR-012
- UIV2-ADR-026

## Approval

Pending.

---

# UIV2-ADR-012 — Use FastAPI OpenAPI as the Frontend Type Source

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

Manually duplicated API interfaces can become stale when backend schemas change.

## Decision

Use FastAPI OpenAPI to generate reproducible frontend TypeScript API types.

## Rationale

This provides:

- one schema source;
- contract drift detection;
- safer frontend compilation;
- easier feature onboarding.

## Alternatives Considered

### Manually Define All Types

**Rejected because:**

- duplicate source of truth;
- high drift risk;
- repeated maintenance.

### Runtime-Only Validation Without Generated Types

**Rejected for the initial architecture because:**

- weaker compile-time integration;
- insufficient as the sole contract mechanism.

## Consequences

- generated files are not manually edited;
- OpenAPI changes affect frontend validation;
- contract generation becomes part of the release gate.

## Risks and Controls

| Risk | Control |
|---|---|
| Generator output changes unexpectedly | Locked tool and reproducible generation |
| Backend leaks secret schema | OpenAPI security review |
| Generated types are hard to consume directly | Domain modules and adapters |

## Related Decisions

- UIV2-ADR-003
- UIV2-ADR-010
- UIV2-ADR-026

## Approval

Pending.

---

# UIV2-ADR-013 — Centralize API Error Normalization and Session Failure Handling

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

Current and future endpoints may return different success and error shapes.

Pages must not independently interpret HTTP errors or render raw objects.

## Decision

The shared API client will normalize failures into one typed frontend error model.

401 and 403 behavior will be centralized.

## Rationale

This prevents:

- `[object Object]`;
- raw backend error rendering;
- login loops;
- inconsistent retry behavior;
- duplicated page logic.

## Alternatives Considered

### Handle Errors Inside Every Page

**Rejected because:**

- duplicated and inconsistent behavior;
- higher security and UX risk.

### Show Raw Backend Payload

**Rejected because:**

- may expose implementation details;
- produces unreadable UI;
- unsafe for structured errors.

## Consequences

- features map normalized errors to user-facing messages;
- raw backend exceptions remain hidden;
- request IDs can be presented safely.

## Related Decisions

- UIV2-ADR-011
- UIV2-ADR-020
- UIV2-ADR-027

## Approval

Pending.

---

# UIV2-ADR-014 — Use a Dark-First Product Theme

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

YGIT is a developer-first infrastructure product.

The intended brand feeling is:

```text
Professional
Premium
Modern
Reliable
Minimal
Enterprise Grade
Focused
```

## Decision

The initial production UI uses one dark-first theme.

```text
Dark is the product.
Light is deferred.
```

## Rationale

A single frozen theme:

- matches the intended developer-product identity;
- reduces implementation and testing scope;
- improves visual consistency;
- avoids premature theme complexity.

## Alternatives Considered

### Ship Dark and Light Together

**Deferred because:**

- doubles visual testing and component-state scope;
- not required for initial UI V2.

### Pure Black Background

**Rejected because:**

- harsher visual contrast;
- weaker navy infrastructure feeling.

## Consequences

- all initial components are designed and tested for dark surfaces;
- light theme requires a later approved design revision.

## Related Decisions

- UIV2-ADR-015
- UIV2-ADR-016
- UIV2-ADR-017

## Approval

Pending.

---

# UIV2-ADR-015 — Freeze the Core Color System

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

Uncontrolled feature colors would make the product appear inconsistent and overly decorative.

## Decision

Freeze the initial semantic colors:

```text
Background       #030712
Surface          #111827
Elevated Surface #0F172A
Input Surface    #070D18
Border           rgba(255,255,255,.08)
Primary          #2563EB
Primary Hover    #1D4ED8
Accent           #38BDF8
Success          #10B981
Warning          #F59E0B
Danger           #EF4444
Info             #3B82F6
```

## Rationale

This palette supports a dark, professional, infrastructure-oriented product without excessive color.

## Alternatives Considered

### Feature-Specific Palettes

**Rejected because:**

- reduces consistency;
- creates maintenance overhead;
- encourages colorful dashboard patterns.

### Gradient-Based Branding

**Rejected because:**

- conflicts with the minimal enterprise direction.

## Consequences

- raw colors remain inside theme definitions;
- feature code uses semantic tokens;
- new colors require formal revision.

## Related Decisions

- UIV2-ADR-014
- UIV2-ADR-016
- UIV2-ADR-028

## Approval

Pending.

---

# UIV2-ADR-016 — Use Inter and JetBrains Mono Only

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

YGIT needs one readable interface font and one technical monospace font.

## Decision

Use:

```text
Inter
JetBrains Mono
```

No additional font family is approved for initial UI V2.

## Rationale

This combination supports:

- clean application typography;
- technical values;
- code and identifiers;
- consistent developer-product identity.

## Alternatives Considered

### Multiple Display Fonts

**Rejected because:**

- unnecessary complexity;
- weaker visual consistency.

### System Fonts Only

**Rejected because:**

- less predictable brand presentation;
- weaker typography control.

## Consequences

- font loading becomes part of asset validation;
- all components use the frozen typography tokens;
- weights are limited to 400, 500, 600, and 700.

## Related Decisions

- UIV2-ADR-014
- UIV2-ADR-017
- UIV2-ADR-019

## Approval

Pending.

---

# UIV2-ADR-017 — Use Compact Dashboard Typography and Medium Density

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

YGIT must remain information-dense without becoming crowded.

Oversized hero typography is inappropriate for the authenticated dashboard.

## Decision

Use:

```text
Global H1 36px
Global H2 30px
Global H3 24px
Global H4 20px
Dashboard Page Title 28px
Section Title 22px
Card Title 18px
Body 16px
Small 14px
Caption 13px
Badge 12px
```

Use medium UI density and the approved spacing scale.

## Rationale

This supports:

- clear hierarchy;
- operational information density;
- GitHub/Linear/Vercel-like compactness;
- responsive behavior.

## Alternatives Considered

### 40px Dashboard Hero

**Rejected because:**

- too large for an operational dashboard;
- consumes unnecessary space.

### Very Dense Bootstrap-Style Layout

**Rejected because:**

- reduces readability;
- creates visual crowding.

### Large Notion-Style Whitespace

**Rejected because:**

- wastes operational space;
- weakens information density.

## Consequences

- dashboard pages do not use marketing-style hero sections;
- spacing primarily uses 8–32px;
- page templates remain compact.

## Related Decisions

- UIV2-ADR-014
- UIV2-ADR-016
- UIV2-ADR-028

## Approval

Pending.

---

# UIV2-ADR-018 — Use Content-Hashed Production Assets

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

The existing frontend has used stable asset names, which can allow stale browser or proxy caching.

## Decision

UI V2 production assets use content-hashed filenames.

Example:

```text
app.a83d21f4.js
styles.91b7d04c.css
```

## Rationale

Content hashes provide:

- reliable cache invalidation;
- versioned rollback;
- build traceability;
- lower stale-asset risk.

## Alternatives Considered

### Permanent `styles.css` and `app.js`

**Rejected because:**

- stale cache risk;
- weak build identity;
- hard rollback diagnostics.

### Cache Purge Only

**Rejected as the primary mechanism because:**

- operational purge can fail;
- correctness should come from asset identity.

## Consequences

- build and packaging must preserve generated names;
- HTML entry documents must point to the correct asset build;
- cache rules differ for HTML and hashed assets.

## Related Decisions

- UIV2-ADR-004
- UIV2-ADR-019
- UIV2-ADR-025

## Approval

Pending.

---

# UIV2-ADR-019 — Use Revalidating HTML and Immutable Hashed Asset Caching

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

Even hashed assets can be served incorrectly if the entry HTML is cached too aggressively.

## Decision

Use:

```text
index.html:
Cache-Control: no-cache, must-revalidate

Hashed assets:
Cache-Control: public, max-age=31536000, immutable
```

## Rationale

This ensures:

- the browser checks for the current asset manifest;
- immutable files remain efficiently cached;
- new releases load new asset names;
- old assets remain valid for rollback.

## Alternatives Considered

### Disable All Caching

**Rejected because:**

- slower user experience;
- unnecessary load;
- hashed assets are safe to cache.

### Long Cache for HTML

**Rejected because:**

- can reference stale build assets;
- delays new releases.

## Consequences

- response-header tests become mandatory;
- asset serving must distinguish entry documents from hashed assets.

## Related Decisions

- UIV2-ADR-018
- UIV2-ADR-025
- UIV2-ADR-027

## Approval

Pending.

---

# UIV2-ADR-020 — Keep Secrets and Provider Communication Out of UI V2

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

YGIT integrates with Keycloak, GitHub, Cloudflare, PostgreSQL, Redis, and workers.

The browser is not a trusted location for provider credentials.

## Decision

UI V2 must never store or use:

```text
Keycloak client secrets
GitHub App private key
GitHub installation token
Cloudflare client secret
Cloudflare access token
Database credentials
Redis credentials
Session signing secrets
```

UI V2 communicates only with YGIT APIs.

## Rationale

This preserves the current secure architecture and prevents direct provider exposure.

## Alternatives Considered

### Direct GitHub or Cloudflare API Calls

**Rejected because:**

- secrets or user tokens would enter the browser;
- provider logic would move outside the Provider Layer;
- authorization and auditing would fragment.

## Consequences

- provider actions require backend endpoints;
- frontend environment variables contain only safe public metadata;
- secret scanning includes generated bundles.

## Related Decisions

- UIV2-ADR-009
- UIV2-ADR-010
- UIV2-ADR-027

## Approval

Pending.

---

# UIV2-ADR-021 — Migrate Page by Page and Preserve Legacy Rollback

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

A single full rewrite cutover would create excessive risk.

## Decision

Migrate in the following order:

```text
Application Shell
Shared API Foundation
Dashboard
Projects
Project Details
Deployments
Connected Accounts
Settings
Feature Parity
Production Cutover
Stabilization
Legacy Retirement
```

After cutover:

```text
/dashboard
    → UI V2

/dashboard-legacy
    → legacy rollback
```

## Rationale

This allows:

- smaller reviews;
- isolated failures;
- progressive feature parity;
- safer production switching.

## Alternatives Considered

### Big-Bang Rewrite

**Rejected because:**

- high regression risk;
- difficult review;
- weak rollback granularity.

### Remove Legacy UI at Cutover

**Rejected because:**

- eliminates immediate rollback;
- creates unnecessary operational risk.

## Consequences

- migration takes multiple phases;
- duplicate route support is temporary;
- legacy removal becomes a separate approved change.

## Related Decisions

- UIV2-ADR-001
- UIV2-ADR-007
- UIV2-ADR-022

## Approval

Pending.

---

# UIV2-ADR-022 — Production Is Not the First Visual Test Environment

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

Previous UI behavior showed that source-level tests alone do not prove browser layout correctness.

## Decision

Every frozen UI V2 page must pass browser, responsive, geometry, and visual validation before production release.

Preview or staging must be the first deployed visual environment.

## Rationale

This detects:

- clipping;
- overlapping;
- incorrect breakpoints;
- stale assets;
- invisible elements;
- unexpected computed styles;
- responsive defects.

## Alternatives Considered

### Source Tests Only

**Rejected because:**

- cannot prove computed layout;
- cannot detect many responsive defects.

### Manual Production Review

**Rejected because:**

- production would become the first real validation environment;
- defects would affect users.

## Consequences

- Playwright becomes mandatory;
- visual baselines require review;
- viewport matrix becomes part of release gates.

## Related Decisions

- UIV2-ADR-023
- UIV2-ADR-024
- UIV2-ADR-027

## Approval

Pending.

---

# UIV2-ADR-023 — Use Playwright for Browser and Visual Validation

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

UI V2 requires real-browser testing across navigation, responsive layouts, geometry, and screenshots.

## Decision

Use:

```text
Playwright
```

for browser, responsive, geometry, and visual regression testing.

## Rationale

Playwright supports:

- Chromium;
- Firefox;
- WebKit;
- viewport testing;
- screenshots;
- network inspection;
- console error detection;
- geometry assertions;
- route interaction.

## Alternatives Considered

### Manual Browser Testing Only

**Rejected because:**

- not repeatable;
- weak regression protection;
- depends on individual reviewer consistency.

### Unit Tests Only

**Rejected because:**

- do not validate actual browser layout.

## Consequences

- browser environments become part of CI;
- screenshot baselines require governance;
- browser launch failures may be retried only when transient.

## Related Decisions

- UIV2-ADR-022
- UIV2-ADR-024
- UIV2-ADR-027

## Approval

Pending.

---

# UIV2-ADR-024 — Target WCAG 2.1 AA

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

YGIT must be keyboard-friendly and professionally usable.

Accessible behavior must be part of the component system rather than a later patch.

## Decision

Target:

```text
WCAG 2.1 AA
```

for UI V2.

## Rationale

This establishes a practical accessibility standard for:

- keyboard navigation;
- focus;
- contrast;
- form labels;
- modal behavior;
- status communication.

## Alternatives Considered

### No Formal Accessibility Target

**Rejected because:**

- inconsistent component behavior;
- higher remediation cost;
- conflicts with professional product requirements.

## Consequences

- critical accessibility failures block release;
- component wrappers must preserve accessibility;
- status colors require text or icon meaning.

## Related Decisions

- UIV2-ADR-005
- UIV2-ADR-022
- UIV2-ADR-023

## Approval

Pending.

---

# UIV2-ADR-025 — Expose Safe UI Build Identity

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

Support and release validation must identify exactly which frontend build a browser loaded.

## Decision

Expose safe immutable metadata through:

```text
window.YGIT_UI_BUILD
```

or an approved equivalent.

The metadata includes:

```text
UI version
Git commit SHA
Build identifier
Environment label
```

## Rationale

This enables:

- deployed-build verification;
- stale-asset diagnosis;
- production support;
- exact release evidence.

## Alternatives Considered

### Infer Build from Asset Names Only

**Rejected because:**

- harder for browser diagnostics;
- incomplete support context.

### Expose Full Environment Configuration

**Rejected because:**

- unnecessary;
- may leak secrets.

## Consequences

- build tooling injects safe metadata;
- tests compare browser build SHA with release SHA;
- secret scanning validates metadata.

## Related Decisions

- UIV2-ADR-004
- UIV2-ADR-018
- UIV2-ADR-019

## Approval

Pending.

---

# UIV2-ADR-026 — Use Domain API Modules and Feature Adapters

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

Generated backend types alone are not sufficient for readable UI behavior.

Pages also should not know transport details.

## Decision

Use:

```text
Shared API Client
    ↓
Domain API Modules
    ↓
Feature Adapters
    ↓
Feature Hooks/Services
    ↓
Pages and Components
```

## Rationale

This keeps:

- transport centralized;
- backend domains isolated;
- presentation transformations explicit;
- compatibility handling out of pages.

## Alternatives Considered

### Generated Client Directly in Pages

**Rejected because:**

- couples pages to backend transport shapes;
- spreads error and transformation logic.

### One Large API Service File

**Rejected because:**

- weak domain ownership;
- difficult future maintenance.

## Consequences

- each backend domain has one frontend module;
- adapters cannot invent backend state;
- feature onboarding follows a predictable structure.

## Related Decisions

- UIV2-ADR-011
- UIV2-ADR-012
- UIV2-ADR-013

## Approval

Pending.

---

# UIV2-ADR-027 — Use Layered, Evidence-Based Release Gates

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

A successful UI build does not prove:

- browser correctness;
- authentication correctness;
- API compatibility;
- asset integrity;
- production deployment identity.

## Decision

Every UI V2 release must pass applicable gates for:

```text
Documentation
Source scope
Formatting
Lint
TypeScript
Unit tests
Component tests
API client tests
Contract tests
Browser tests
Responsive tests
Accessibility
Visual regression
Build
Asset integrity
Backend regression
Git verification
Post-deployment verification
```

## Rationale

This reduces production surprises and creates verifiable release evidence.

## Alternatives Considered

### Manual Approval Only

**Rejected because:**

- non-repeatable;
- weak traceability.

### Unit and Build Tests Only

**Rejected because:**

- no real-browser or deployed-asset proof.

## Consequences

- releases require more structured evidence;
- deterministic failures block release;
- mocks cannot be presented as live-system proof.

## Related Decisions

- UIV2-ADR-013
- UIV2-ADR-022
- UIV2-ADR-023
- UIV2-ADR-025

## Approval

Pending.

---

# UIV2-ADR-028 — Keep Initial Theme Configuration in Source Code

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

The product owner wants future control over logo, favicon, fonts, and colors.

Building a full database-driven UI configuration system during initial UI V2 would add unnecessary complexity and create another large source of errors.

## Decision

Initial UI V2 theme and brand configuration remain code-defined under:

```text
frontend-v2/src/theme/
frontend-v2/public/brand/
```

Future admin control is deferred to a separate approved feature.

## Rationale

This is the safest balance between:

- easy UI maintenance;
- professional consistency;
- low implementation complexity;
- future extensibility.

## Alternatives Considered

### Build Full Theme CMS Now

**Rejected because:**

- increases backend, database, validation, preview, and rollback scope;
- UI V2 does not require it to launch.

### Store Arbitrary CSS in Database

**Rejected because:**

- severe stability and security risk;
- breaks design-system governance;
- turns YGIT toward a CMS or page builder.

## Consequences

- visual changes require source update and release;
- future admin configuration may expose only approved semantic presets;
- arbitrary CSS, HTML, JavaScript, and layout editing remain prohibited.

## Related Decisions

- UIV2-ADR-014
- UIV2-ADR-015
- UIV2-ADR-017
- UIV2-ADR-029

## Approval

Pending.

---

# UIV2-ADR-029 — Defer Admin-Controlled Branding and Theme Presets

**Date:** 2026-07-22<br>
**Status:** Deferred<br>

## Context

Future administrators may need to change selected brand and theme values without editing UI source.

## Decision

Defer implementation until UI V2 is stable.

A future approved configuration system may expose only:

```text
Primary color preset
Logo reference
Favicon reference
Approved font preset
Density preset
Radius preset
```

## Rationale

The initial priority is a stable frontend architecture.

Admin-driven theming should not block or destabilize UI V2 migration.

## Rejected Future Scope

The future system must not allow:

```text
Arbitrary CSS
Arbitrary HTML
Arbitrary JavaScript
Page layout JSON
Route editing
Per-component visual editing
Backend business-logic editing
```

## Consequences

- no database model is required now;
- no UI configuration API is required now;
- the future feature requires its own architecture and security documentation.

## Related Decisions

- UIV2-ADR-028
- UIV2-ADR-030

## Approval

Deferred by architecture.

---

# UIV2-ADR-030 — Do Not Build a CMS or Page Builder

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

YGIT is a deployment automation platform.

A database-driven arbitrary UI system would change the product boundary and create unnecessary complexity.

## Decision

UI V2 will not become:

```text
CMS
Website Builder
Page Builder
Arbitrary Theme Editor
Runtime Component Editor
```

## Rationale

This preserves:

- YGIT product identity;
- design consistency;
- security;
- maintainability;
- implementation focus.

## Alternatives Considered

### Runtime Page Layout Configuration

**Rejected because:**

- high validation burden;
- unstable responsive behavior;
- difficult testing;
- product-scope drift.

## Consequences

- new pages remain source-controlled;
- components remain reviewed and tested;
- admin configuration stays semantic and bounded if introduced later.

## Related Decisions

- UIV2-ADR-028
- UIV2-ADR-029

## Approval

Pending.

---

# UIV2-ADR-031 — Do Not Introduce a Global State Framework Initially

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

UI V2 requires local state, route state, server data, and limited global presentation state.

A global state framework is not currently required.

## Decision

Initial UI V2 uses:

- component state;
- feature hooks;
- React context only for true application-level presentation state;
- URL state for routes and approved filters.

No dedicated global state library is approved initially.

## Rationale

This reduces:

- dependencies;
- architecture complexity;
- hidden shared state;
- onboarding burden.

## Alternatives Considered

### Redux or Equivalent at Project Start

**Rejected because:**

- no demonstrated global business-state need;
- backend remains authoritative;
- can create unnecessary indirection.

## Consequences

- state ownership must remain explicit;
- a future global store requires a new decision record;
- server-state behavior remains feature-owned initially.

## Related Decisions

- UIV2-ADR-002
- UIV2-ADR-011
- UIV2-ADR-026

## Approval

Pending.

---

# UIV2-ADR-032 — Do Not Automatically Retry Mutations

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

Mutation requests may create projects, request deployments, disconnect providers, or change settings.

Automatic retry could create duplicate or unsafe state changes.

## Decision

Automatic retry is prohibited for mutations.

Allowed automatic retry is limited to explicitly safe read requests.

## Rationale

A timeout does not prove that a backend mutation failed.

Replaying a mutation could create duplicate operations.

## Alternatives Considered

### Retry All Network Failures

**Rejected because:**

- unsafe for non-idempotent actions;
- could duplicate deployment requests.

## Consequences

- mutation failures require backend-state reconciliation;
- duplicate-submit controls are mandatory;
- idempotency is used only when explicitly documented.

## Related Decisions

- UIV2-ADR-011
- UIV2-ADR-013
- UIV2-ADR-027

## Approval

Pending.

---

# UIV2-ADR-033 — Require Fresh Backend Readiness Before Deployment

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

Deployment readiness is a backend-owned decision and may change after the page initially loads.

## Decision

Before requesting a deployment, UI V2 must fetch current backend readiness.

```text
Fresh readiness
    ↓
deploy_ready?
    ├── No  → show blockers
    └── Yes → allow explicit deployment request
```

## Rationale

This prevents stale UI state from authorizing an unsafe deployment action.

## Alternatives Considered

### Use Cached Page State

**Rejected because:**

- readiness may have changed;
- frontend state is not authoritative.

### Reimplement Readiness Logic in UI

**Rejected because:**

- duplicates Deploy Engine behavior;
- creates inconsistent decisions.

## Consequences

- deploy action has an additional read before mutation;
- backend blockers are rendered through approved adapters;
- blocked state creates no deployment request.

## Related Decisions

- UIV2-ADR-010
- UIV2-ADR-032
- UIV2-ADR-034

## Approval

Pending.

---

# UIV2-ADR-034 — Exclude Real Provider Execution from Ordinary UI Tests

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

UI tests must validate presentation and request safety without creating real Cloudflare deployments or modifying provider state.

## Decision

Ordinary UI testing uses:

- mocks;
- local integrated APIs;
- preview reads;
- controlled non-destructive browser checks.

Real provider execution requires separate explicit approval.

## Rationale

This separates:

- UI correctness;
- API correctness;
- provider execution validation.

It prevents visual or browser testing from causing infrastructure mutations.

## Alternatives Considered

### Run a Real Deployment in Every UI Release

**Rejected because:**

- unnecessary cost and risk;
- unrelated to most UI changes;
- difficult cleanup.

## Consequences

- test evidence must identify mocked versus live behavior;
- production smoke remains read-only by default;
- live provider tests are separately documented.

## Related Decisions

- UIV2-ADR-020
- UIV2-ADR-027
- UIV2-ADR-033

## Approval

Pending.

---

# UIV2-ADR-035 — Use Lucide as the Only Icon Family

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

Mixed icon libraries create inconsistent stroke, sizing, and visual language.

## Decision

Use:

```text
Lucide
```

as the only initial icon family.

## Rationale

Lucide supports:

- clean outline style;
- broad application coverage;
- consistent developer-product appearance;
- accessible React integration.

## Alternatives Considered

### Multiple Icon Libraries

**Rejected because:**

- inconsistent visual appearance;
- larger dependency surface.

### Filled Material Icons

**Rejected because:**

- conflicts with the requested non-Material visual direction.

## Consequences

- new icons are selected from Lucide first;
- custom icons require explicit design review;
- icon-only actions require accessible labels.

## Related Decisions

- UIV2-ADR-005
- UIV2-ADR-014
- UIV2-ADR-024

## Approval

Pending.

---

# UIV2-ADR-036 — Use Normal Document Flow for Primary Layout

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

Absolute positioning and overflow workarounds caused fragile layout behavior in the current dashboard.

## Decision

Primary UI V2 layout uses:

```text
Normal document flow
CSS Grid
Flexbox
Mantine layout primitives
```

Absolute positioning is prohibited for primary page structure.

## Rationale

This improves:

- responsive behavior;
- predictable geometry;
- content growth;
- accessibility;
- browser consistency.

## Alternatives Considered

### Absolute-Positioned Dashboard Composition

**Rejected because:**

- breaks when content or viewport changes;
- requires spacer and z-index workarounds;
- difficult to test reliably.

## Consequences

- cards and sections occupy real document space;
- primary content cannot depend on hidden overflow;
- geometry assertions become easier.

## Related Decisions

- UIV2-ADR-017
- UIV2-ADR-022
- UIV2-ADR-023

## Approval

Pending.

---

# UIV2-ADR-037 — Keep the Initial Frontend Dependency Set Small

**Date:** 2026-07-22<br>
**Status:** Proposed for Acceptance<br>

## Context

The UI V2 goal is a professional but beginner-friendly frontend platform.

Excessive dependencies create maintenance and onboarding cost.

## Decision

The initial core dependency set is limited to the approved stack:

```text
React
TypeScript
Vite
Mantine UI
React Router
Lucide
Vitest
React Testing Library
Playwright
ESLint
Prettier
OpenAPI type-generation tooling
```

Additional dependencies require justification.

## Rationale

This reduces:

- upgrade burden;
- supply-chain exposure;
- duplicated functionality;
- architectural confusion.

## Alternatives Considered

### Add Specialized Libraries Preemptively

**Rejected because:**

- features should drive dependencies;
- unnecessary packages increase risk.

## Consequences

- routine features use existing stack capabilities;
- new libraries require license, maintenance, security, and overlap review.

## Related Decisions

- UIV2-ADR-005
- UIV2-ADR-031
- UIV2-ADR-027

## Approval

Pending.

---

# UIV2-ADR-038 — Preserve Business Logic in Engines

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

YGIT architecture requires business logic to remain inside independent engines.

UI V2 must not become an alternative business layer.

## Decision

The following remain backend-owned:

```text
Project state
Repository Analysis decisions
Deployment readiness
Provider authorization
Deployment execution
Connected account validity
Worker orchestration
Infrastructure behavior
```

## Rationale

This preserves:

- one source of truth;
- testable engine ownership;
- API consistency;
- secure provider behavior.

## Alternatives Considered

### Duplicate Logic in Frontend for Speed

**Rejected because:**

- inconsistent decisions;
- unsafe stale state;
- duplicated maintenance.

## Consequences

- UI may present state but not authorize it;
- backend revalidates every mutation;
- frontend tests do not replace engine tests.

## Related Decisions

- UIV2-ADR-008
- UIV2-ADR-010
- UIV2-ADR-033

## Approval

Pending.

---

# UIV2-ADR-039 — Require Documentation Approval Before Implementation

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

YGIT follows:

```text
Documentation first
Architecture second
Implementation third
Testing fourth
Release last
```

## Decision

UI V2 implementation may not begin until the required documents reach their defined approval status.

## Rationale

This prevents:

- architecture drift;
- undocumented assumptions;
- premature code;
- repeated rewrites;
- inconsistent developer handoff.

## Alternatives Considered

### Implement While Architecture Is Still Changing

**Rejected because:**

- creates rework;
- makes documents descriptive instead of authoritative.

## Consequences

- current phase remains documentation-only;
- document revisions use version history;
- approved changes require change requests.

## Related Decisions

- UIV2-ADR-027
- UIV2-ADR-040

## Approval

Pending.

---

# UIV2-ADR-040 — Govern Frozen Changes Through Formal Revision

**Date:** 2026-07-22<br>
**Status:** Proposed for Freeze<br>

## Context

Silent changes to frozen architecture would make implementation and documentation inconsistent.

## Decision

A frozen decision changes only through:

```text
Change Request
    ↓
Impact Analysis
    ↓
Decision Log Update
    ↓
Specification Revision
    ↓
Version Increment
    ↓
Approval
```

## Rationale

This provides:

- traceability;
- controlled evolution;
- clear developer handoff;
- reliable release expectations.

## Alternatives Considered

### Edit Frozen Documents Directly

**Rejected because:**

- loses architectural history;
- creates silent contract changes.

## Consequences

- revision history is mandatory;
- superseded decisions remain recorded;
- implementation must reference the active version.

## Related Decisions

- UIV2-ADR-039

## Approval

Pending.

---

## 5. Rejected Architecture Summary

The following directions are rejected for initial UI V2:

| Rejected Direction | Reason |
|---|---|
| Continue patching legacy CSS as the long-term strategy | Fragile and difficult to scale |
| Rewrite legacy UI in place | Weak isolation and rollback |
| New UI Engine | No independent business responsibility |
| Separate UI V2 authentication system | Duplicates current identity architecture |
| Direct browser calls to GitHub or Cloudflare | Security and architecture violation |
| New parallel UI V2 API namespace | Unnecessary duplication |
| Raw `fetch()` in pages | Inconsistent transport behavior |
| Arbitrary database-driven CSS | Stability and security risk |
| Runtime page builder | Product-scope violation |
| Multiple UI frameworks | Inconsistent architecture |
| Material Design visual language | Conflicts with brand direction |
| Bootstrap admin-template style | Conflicts with premium custom identity |
| Pure black visual system | Too harsh; dark navy selected |
| Multiple font families | Inconsistent typography |
| Mixed icon libraries | Inconsistent visual language |
| Absolute primary layout | Fragile responsive behavior |
| Automatic mutation retry | Duplicate-operation risk |
| Production-first visual testing | Unsafe release process |
| Real provider execution in ordinary UI tests | Unnecessary infrastructure risk |
| Immediate legacy removal at cutover | Removes safe rollback |

---

## 6. Deferred Decision Summary

The following are intentionally deferred:

| Decision | Reason | Revisit Condition |
|---|---|---|
| Light theme | Initial release is dark-first | UI V2 stable and separate theme scope approved |
| Admin theme presets | Not required for migration | Stable UI V2 and approved configuration architecture |
| Global state library | No demonstrated requirement | Cross-feature state becomes difficult to manage |
| Real-time deployment updates | Separate API and worker contract required | Backend event architecture approved |
| Independent frontend deployment service | Not required initially | Scaling or operational need demonstrated |
| Public developer API integration | Outside UI V2 scope | Developer Portal architecture approved |
| Storybook | Useful but not required by current simplified foundation | Shared component inventory grows sufficiently |
| Analytics SDK | Privacy and product requirements undefined | Separate analytics architecture approved |

---

## 7. Decision Dependency Map

```text
ADR-001 Separate Frontend
    ├── ADR-002 React
    ├── ADR-003 TypeScript
    ├── ADR-004 Vite
    ├── ADR-005 Mantine
    ├── ADR-006 React Router
    ├── ADR-007 Preview Route
    └── ADR-021 Page-by-Page Migration

ADR-008 UI Delivery Gate
    ├── ADR-009 Existing Authentication
    ├── ADR-018 Hashed Assets
    ├── ADR-019 Cache Contract
    └── ADR-025 Build Identity

ADR-010 Existing APIs
    ├── ADR-011 Shared API Client
    ├── ADR-012 OpenAPI Types
    ├── ADR-013 Error Normalization
    ├── ADR-026 Domain API Modules
    ├── ADR-032 No Mutation Retry
    └── ADR-033 Fresh Readiness

ADR-014 Dark First
    ├── ADR-015 Color System
    ├── ADR-016 Fonts
    ├── ADR-017 Typography and Density
    ├── ADR-035 Lucide
    └── ADR-036 Normal Flow Layout

ADR-022 Pre-Production Visual Validation
    ├── ADR-023 Playwright
    ├── ADR-024 Accessibility
    ├── ADR-027 Release Gates
    └── ADR-034 No Ordinary Live Provider Execution

ADR-028 Source-Controlled Theme
    ├── ADR-029 Deferred Admin Presets
    └── ADR-030 No CMS/Page Builder

ADR-039 Documentation First
    └── ADR-040 Formal Revision Governance
```

---

## 8. Decision Approval Matrix

| Decision Range | Primary Approval |
|---|---|
| ADR-001–ADR-013 | Architecture Owner and Frontend Owner |
| ADR-014–ADR-017 | Product Owner and Design Owner |
| ADR-018–ADR-020 | Architecture Owner, Backend Owner, Security Owner |
| ADR-021–ADR-027 | Product Owner, Frontend Owner, Release Owner |
| ADR-028–ADR-031 | Product Owner and Architecture Owner |
| ADR-032–ADR-034 | Backend Owner, Security Owner, Release Owner |
| ADR-035–ADR-037 | Design Owner and Frontend Owner |
| ADR-038–ADR-040 | Architecture Owner and Product Owner |

---

## 9. Decision Change Procedure

To change an accepted or frozen decision:

1. create a new decision record;
2. reference the existing decision;
3. describe the problem;
4. document impact on architecture, APIs, design, migration, testing, and release;
5. state whether the old decision is superseded or amended;
6. update related specifications;
7. update revision history;
8. obtain required approval;
9. implement only after approval.

Existing decisions must not be deleted.

---

## 10. Decision Review Checklist

Before accepting a decision, confirm:

```text
Product boundary preserved
Engine ownership preserved
Security impact reviewed
API impact reviewed
Frontend complexity justified
Migration impact documented
Testing impact documented
Rollback impact documented
Future developer usability considered
Alternative options recorded
No unapproved feature invented
```

---

## 11. Current Decision Status Summary

| ID | Title | Status |
|---|---|---|
| UIV2-ADR-001 | Separate Frontend Application | Proposed |
| UIV2-ADR-002 | React | Proposed |
| UIV2-ADR-003 | TypeScript Strict Mode | Proposed |
| UIV2-ADR-004 | Vite | Proposed |
| UIV2-ADR-005 | Mantine UI | Proposed |
| UIV2-ADR-006 | React Router | Proposed |
| UIV2-ADR-007 | `/dashboard-v2` Preview Route | Proposed |
| UIV2-ADR-008 | Minimal UI Delivery Gate | Proposed |
| UIV2-ADR-009 | Existing Authentication | Proposed |
| UIV2-ADR-010 | Existing `/api/v1` First | Proposed |
| UIV2-ADR-011 | Shared API Client | Proposed |
| UIV2-ADR-012 | OpenAPI Type Source | Proposed |
| UIV2-ADR-013 | Central Error Normalization | Proposed |
| UIV2-ADR-014 | Dark-First Theme | Proposed for Freeze |
| UIV2-ADR-015 | Core Color System | Proposed for Freeze |
| UIV2-ADR-016 | Inter and JetBrains Mono | Proposed for Freeze |
| UIV2-ADR-017 | Compact Typography and Medium Density | Proposed for Freeze |
| UIV2-ADR-018 | Content-Hashed Assets | Proposed |
| UIV2-ADR-019 | Cache Contract | Proposed |
| UIV2-ADR-020 | No Browser Secrets or Provider Calls | Proposed for Freeze |
| UIV2-ADR-021 | Page-by-Page Migration | Proposed |
| UIV2-ADR-022 | Production Not First Visual Test | Proposed for Freeze |
| UIV2-ADR-023 | Playwright | Proposed |
| UIV2-ADR-024 | WCAG 2.1 AA | Proposed |
| UIV2-ADR-025 | UI Build Identity | Proposed |
| UIV2-ADR-026 | Domain API Modules and Adapters | Proposed |
| UIV2-ADR-027 | Layered Release Gates | Proposed for Freeze |
| UIV2-ADR-028 | Source-Controlled Initial Theme | Proposed |
| UIV2-ADR-029 | Admin Theme Presets | Deferred |
| UIV2-ADR-030 | No CMS or Page Builder | Proposed for Freeze |
| UIV2-ADR-031 | No Initial Global State Framework | Proposed |
| UIV2-ADR-032 | No Automatic Mutation Retry | Proposed for Freeze |
| UIV2-ADR-033 | Fresh Readiness Before Deploy | Proposed for Freeze |
| UIV2-ADR-034 | No Ordinary Live Provider Execution | Proposed for Freeze |
| UIV2-ADR-035 | Lucide Only | Proposed for Freeze |
| UIV2-ADR-036 | Normal Document Flow | Proposed for Freeze |
| UIV2-ADR-037 | Small Dependency Set | Proposed |
| UIV2-ADR-038 | Business Logic Remains in Engines | Proposed for Freeze |
| UIV2-ADR-039 | Documentation Before Implementation | Proposed for Freeze |
| UIV2-ADR-040 | Formal Revision Governance | Proposed for Freeze |

---

## 12. Approval Record

| Role | Name | Decision | Date |
|---|---|---|---|
| Product Owner | Pending | Pending | Pending |
| Architecture Owner | Pending | Pending | Pending |
| Design Owner | Pending | Pending | Pending |
| Frontend Owner | Pending | Pending | Pending |
| Backend Owner | Pending | Pending | Pending |
| API Owner | Pending | Pending | Pending |
| Security Owner | Pending | Pending | Pending |
| Release Owner | Pending | Pending | Pending |
| Accessibility Reviewer | Pending | Pending | Pending |

---

## 13. Next Documentation Step

After this document is reviewed, the UI V2 documentation entry point must be created:

```text
docs/ui-v2/README.md
```

The repository root README must then receive a concise UI V2 documentation section.

No UI V2 implementation is authorized by this draft.

---

**End of Document**
