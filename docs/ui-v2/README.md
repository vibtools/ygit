# YGIT UI V2 Documentation

**Product:** YGIT<br>
**Company:** Vib Tools<br>
**Documentation Status:** Documentation Freeze Phase<br>
**Implementation Status:** Not Started<br>

---

## Purpose

This directory is the official documentation entry point for YGIT UI V2.

UI V2 is a separate frontend application planned for controlled, page-by-page migration. The current YGIT backend, engines, providers, workers, authentication, PostgreSQL, Redis, and deployment behavior remain authoritative.

No UI V2 implementation is authorized until the required documents complete review and approval.

---

## Official Documents

| Order | Document | Responsibility |
|---:|---|---|
| 1 | [UI V2 Master Architecture](./UI_V2_MASTER_ARCHITECTURE.md) | Frontend platform, boundaries, routing, delivery, and ownership |
| 2 | [UI V2 API Architecture](./UI_V2_API_ARCHITECTURE.md) | API client, OpenAPI contracts, errors, compatibility, and feature integration |
| 3 | [UI V2 Design System Freeze](./UI_V2_DESIGN_SYSTEM_FREEZE.md) | Brand, colors, typography, spacing, components, responsive rules, and accessibility |
| 4 | [UI V2 Migration Plan](./UI_V2_MIGRATION_PLAN.md) | Parallel migration phases, page order, cutover, stabilization, and rollback |
| 5 | [UI V2 Testing and Release Gate](./UI_V2_TESTING_AND_RELEASE_GATE.md) | Test layers, browser gates, asset integrity, release evidence, and production verification |
| 6 | [UI V2 Decision Log](./UI_V2_DECISION_LOG.md) | Architectural decisions, rejected alternatives, deferred scope, and governance |

---

## Documentation Workflow

```text
Draft
  â†“
Review
  â†“
Approved
  â†“
Frozen
  â†“
Implementation
```

A frozen decision may be changed only through a documented revision and approval process.

---

## Core UI V2 Boundary

```text
Frontend renders
Backend validates
Engines decide
Providers communicate
Workers execute
```

UI V2 must not contain engine business logic, provider credentials, database access, Redis access, or direct GitHub/Cloudflare communication.

---

## Planned Technology Stack

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
FastAPI OpenAPI generated TypeScript types
```

---

## Planned Migration Routes

Before cutover:

```text
/dashboard       â†’ Legacy dashboard
/dashboard-v2    â†’ UI V2 preview
```

After approved cutover:

```text
/dashboard        â†’ UI V2
/dashboard-legacy â†’ Legacy rollback route
```

Legacy retirement requires a separate approved change.

---

## Current Restriction

This documentation set does not authorize:

- React application creation;
- dependency installation;
- backend route changes;
- API changes;
- database changes;
- provider execution;
- production route cutover;
- legacy UI removal.

---

**End of Document**
