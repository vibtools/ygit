# YGIT UI V2 API Architecture Specification

**Document ID:** YGIT-UIV2-API-001<br>
**Version:** 0.1.0<br>
**Status:** Draft for Review<br>
**Owner:** YGIT Platform<br>
**Product:** YGIT<br>
**Company:** Vib Tools<br>
**Depends On:** `UI_V2_MASTER_ARCHITECTURE.md`<br>
**Last Updated:** 2026-07-22<br>

---

## Revision History

| Version | Date | Status | Summary |
|---|---|---|---|
| 0.1.0 | 2026-07-22 | Draft for Review | Initial UI V2 API architecture specification |

---

## 1. Purpose

This document defines the API architecture used by YGIT UI V2.

The goal is to provide one safe, predictable, and extensible method for connecting any current or future YGIT frontend page to the existing FastAPI backend.

The architecture must allow a YGIT developer to:

1. add a new backend capability;
2. expose or extend a documented API contract;
3. generate or update frontend API types;
4. add one isolated frontend API module;
5. connect a feature or page without modifying unrelated UI code;
6. preserve authentication, error handling, and response normalization;
7. detect compatibility problems before deployment.

This specification does not authorize API implementation or backend modification. It freezes the integration model that later implementation must follow.

---

## 2. Relationship to the UI V2 Master Architecture

The master boundary remains:

```text
UI V2 renders and collects user intent
        ↓
FastAPI validates requests and sessions
        ↓
YGIT Engines own business rules
        ↓
Provider Layer communicates with GitHub and Cloudflare
        ↓
Infrastructure executes persistent and asynchronous work
```

The API layer is the only supported communication boundary between UI V2 and YGIT backend capabilities.

UI V2 must not:

- access PostgreSQL directly;
- access Redis directly;
- call GitHub directly;
- call Cloudflare directly;
- invoke worker processes directly;
- duplicate engine decisions as frontend authority;
- depend on private backend module imports;
- construct provider credentials;
- bypass API authorization.

---

## 3. Scope

### 3.1 In Scope

This document defines:

- the central frontend API client;
- same-origin API communication;
- frontend API module structure;
- OpenAPI-derived type generation;
- request and response normalization;
- error contracts;
- authentication and session-expiry handling;
- request identifiers;
- timeouts;
- retry rules;
- cancellation;
- pagination;
- filtering and sorting conventions;
- mutation safety;
- idempotency expectations;
- capability discovery;
- API versioning;
- backward compatibility;
- deprecation;
- frontend feature onboarding;
- testing and release requirements;
- ownership boundaries.

### 3.2 Out of Scope

This document does not define:

- final endpoint inventory;
- implementation of new backend endpoints;
- YGIT engine internals;
- provider API contracts;
- database schemas;
- Redis queue schemas;
- webhook contracts;
- real-time transport;
- GraphQL;
- public developer API access;
- admin theme configuration APIs;
- final UI component behavior;
- production deployment commands.

---

## 4. API Architecture Principles

The following principles are mandatory.

### 4.1 Existing API First

UI V2 must use existing `/api/v1/*` endpoints whenever they already provide the required capability.

A new endpoint may be proposed only when:

- required data is not available;
- the missing capability is documented;
- engine ownership is clear;
- authorization behavior is defined;
- backward compatibility is considered;
- tests are included;
- the API change is separately approved.

### 4.2 One API Entry Point

All frontend requests must pass through one shared API client.

Prohibited:

```text
Page → raw fetch()
Component → raw fetch()
Hook → direct provider URL
Feature → custom request implementation
```

Approved:

```text
Page
  ↓
Feature hook/service
  ↓
Feature API module
  ↓
Shared API client
  ↓
/api/v1/*
```

### 4.3 Backend Authority

The frontend may present backend state, but it must not create competing business rules.

Examples:

- Deploy Engine decides deployment readiness.
- Project Engine decides project state.
- Repository Analysis Engine decides analysis results.
- Connected Accounts backend decides provider connection status.
- Backend authorization decides whether an action is permitted.

The UI may disable or hide an action for usability, but backend validation remains mandatory.

### 4.4 Typed Contracts

Frontend API code must use TypeScript types derived from or aligned with the FastAPI OpenAPI schema.

The same API response shape must not be manually redefined across multiple pages.

### 4.5 Safe Failure

A failed API request must:

- produce a normalized frontend error;
- preserve already loaded data when possible;
- avoid creating duplicate mutations;
- avoid leaking backend internals;
- avoid exposing secrets;
- avoid automatic destructive retries.

---

## 5. High-Level API Flow

```text
React Page
    ↓
Feature Hook or Feature Service
    ↓
Feature API Module
    ↓
Shared API Client
    ↓
Same-Origin HTTP Request
    ↓
FastAPI Route
    ↓
Engine Service
    ↓
Provider or Infrastructure Layer
    ↓
Normalized HTTP Response
    ↓
Shared API Client Normalization
    ↓
Typed Frontend Result
    ↓
Feature View Model
    ↓
UI Component
```

---

## 6. Approved API Base Path

The official backend API base path is:

```text
/api/v1
```

UI V2 must use relative same-origin requests.

Example:

```text
/api/v1/projects
```

UI V2 must not hardcode production domains such as:

```text
https://ygit.net/api/v1
```

Relative same-origin requests preserve:

- existing session cookies;
- environment portability;
- preview-route compatibility;
- local proxy compatibility;
- staging compatibility;
- reduced CORS complexity.

---

## 7. Frontend API Directory Structure

The approved structure is:

```text
frontend-v2/src/api/
├── client/
│   ├── api-client.ts
│   ├── api-request.ts
│   ├── api-response.ts
│   ├── api-error.ts
│   ├── api-timeout.ts
│   └── api-types.ts
├── generated/
│   └── openapi.ts
├── modules/
│   ├── auth.ts
│   ├── platform.ts
│   ├── projects.ts
│   ├── repositories.ts
│   ├── repository-analysis.ts
│   ├── deployments.ts
│   └── connected-accounts.ts
├── adapters/
│   ├── project-adapter.ts
│   ├── repository-adapter.ts
│   ├── analysis-adapter.ts
│   ├── deployment-adapter.ts
│   └── connected-account-adapter.ts
├── capabilities/
│   └── capability-registry.ts
└── index.ts
```

### 7.1 `client/`

Owns transport behavior shared by all endpoints.

It must contain:

- base path handling;
- credentials configuration;
- headers;
- body serialization;
- response parsing;
- error normalization;
- timeout handling;
- cancellation;
- request identifier capture;
- safe retry decisions.

It must not contain feature-specific data mapping.

### 7.2 `generated/`

Owns machine-generated TypeScript definitions derived from FastAPI OpenAPI.

Rules:

- generated files are not manually edited;
- generation must be reproducible;
- schema drift must fail validation;
- frontend code should consume generated types through feature modules or adapters;
- generated transport code is optional, but generated types are required unless a later approved decision replaces this model.

### 7.3 `modules/`

Owns endpoint-specific frontend functions.

Examples:

```text
listProjects()
getProject(projectId)
getProjectReadiness(projectId)
createProject(input)
listProjectDeployments(projectId, query)
requestDeployment(projectId)
listConnectedAccounts()
```

Each module must:

- use the shared API client;
- use generated request and response types;
- expose stable frontend-facing functions;
- remain independent from React rendering;
- avoid direct DOM access;
- avoid feature presentation state.

### 7.4 `adapters/`

Owns safe transformation from backend API data into frontend view models where transformation is necessary.

Adapters may:

- normalize optional fields;
- convert timestamps to typed values;
- map backend enums to safe frontend labels;
- convert structured warning objects to readable view data;
- isolate temporary compatibility handling.

Adapters must not:

- invent backend state;
- alter authorization;
- infer deployment readiness independently;
- hide required API contract failures silently.

### 7.5 `capabilities/`

Owns frontend knowledge of explicitly reported backend capabilities.

It does not replace backend authorization.

---

## 8. Shared API Client Contract

The shared API client will expose a small, typed interface.

Conceptual interface:

```ts
type ApiRequestOptions<TBody> = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: TBody;
  query?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
  timeoutMs?: number;
  retryPolicy?: "none" | "safe-read";
  headers?: Record<string, string>;
};

async function apiRequest<TResponse, TBody = never>(
  path: string,
  options?: ApiRequestOptions<TBody>,
): Promise<TResponse>;
```

This is an architectural contract, not an implementation authorization.

### 8.1 Required Request Behavior

Every request must:

- use `/api/v1` as the base path;
- use `credentials: "include"`;
- send JSON only when a body exists;
- send `Accept: application/json`;
- avoid sending empty JSON bodies for read requests;
- support `AbortSignal`;
- apply a bounded timeout;
- parse JSON only when the response content type supports it;
- capture safe request correlation metadata when returned.

### 8.2 Required Response Behavior

The client must:

- return typed data on success;
- detect unsuccessful HTTP status codes;
- detect API envelopes reporting failure;
- normalize errors into one frontend error type;
- preserve HTTP status;
- preserve stable backend error code;
- preserve safe backend message;
- preserve request identifier when available;
- avoid exposing stack traces or secret details.

---

## 9. Canonical Frontend Response Model

Existing YGIT endpoints may return either an envelope or a direct data object during migration.

The shared client must normalize supported responses into one frontend result model.

### 9.1 Preferred Backend Success Envelope

The preferred future-safe success format is:

```json
{
  "success": true,
  "data": {},
  "meta": {
    "request_id": "optional-request-id"
  }
}
```

### 9.2 Preferred Backend Error Envelope

The preferred error format is:

```json
{
  "success": false,
  "error": {
    "code": "STABLE_ERROR_CODE",
    "message": "Safe human-readable message.",
    "details": {}
  },
  "meta": {
    "request_id": "optional-request-id"
  }
}
```

### 9.3 Compatibility Rule

During UI V2 migration, the client may also accept:

- direct success payloads;
- existing `{data: ...}` payloads;
- existing `{success: false, error: ...}` failures.

Compatibility logic must exist only in the shared client or approved adapters.

Pages must never implement their own response-envelope detection.

---

## 10. Canonical Frontend Error Model

All API failures must become one typed frontend error.

```ts
type YgitApiError = {
  name: "YgitApiError";
  code: string;
  message: string;
  status: number | null;
  requestId: string | null;
  details: unknown | null;
  causeType:
    | "http"
    | "network"
    | "timeout"
    | "abort"
    | "parse"
    | "contract";
  retryable: boolean;
};
```

### 10.1 Required Error Codes

When the backend does not provide a stable code, the client may use transport-level codes:

```text
HTTP_400
HTTP_401
HTTP_403
HTTP_404
HTTP_409
HTTP_422
HTTP_429
HTTP_500
NETWORK_ERROR
REQUEST_TIMEOUT
REQUEST_ABORTED
INVALID_RESPONSE
API_CONTRACT_MISMATCH
```

### 10.2 User Message Boundary

The API client stores the normalized technical error.

Feature-level presentation decides the safe user-facing message.

Raw values such as the following must never be rendered directly:

```text
[object Object]
Python exception repr
database connection string
provider token
stack trace
internal filesystem path
```

### 10.3 Error Details

`details` may contain structured validation or blocker information.

UI code must render only approved fields through typed adapters.

Arbitrary object dumping is prohibited.

---

## 11. Authentication and Session Handling

UI V2 reuses the existing YGIT session.

Required client behavior:

```text
Request
  ↓
credentials: include
  ↓
FastAPI session validation
```

### 11.1 HTTP 401

A `401 Unauthorized` means the session is missing or expired.

The shared client must:

1. normalize the error;
2. avoid infinite retry loops;
3. notify the application authentication boundary;
4. allow the existing login flow to recover the session;
5. preserve the intended frontend route where safely supported.

Pages must not each implement separate 401 behavior.

### 11.2 HTTP 403

A `403 Forbidden` means the authenticated user is not authorized.

The UI must:

- show an authorization-safe message;
- not redirect repeatedly to login;
- not reveal hidden resource details;
- preserve backend authority.

### 11.3 Secrets

UI V2 must never receive or store:

- Keycloak client secrets;
- GitHub App private keys;
- GitHub installation tokens;
- Cloudflare OAuth client secrets;
- Cloudflare access tokens;
- database credentials;
- Redis credentials;
- session signing secrets.

---

## 12. Request Headers

The shared client may send:

```text
Accept: application/json
Content-Type: application/json
X-YGIT-UI-Version: <ui-version>
X-YGIT-UI-Build: <commit-or-build-id>
```

The final header names require implementation review.

The frontend must not send secrets through custom headers.

The backend may return:

```text
X-Request-ID
```

or equivalent request metadata.

The client must capture this value when available for diagnostics.

---

## 13. Timeouts

Every request must have a bounded timeout.

Initial architectural defaults:

| Request Type | Default Timeout |
|---|---:|
| Normal read request | 15 seconds |
| Normal write request | 20 seconds |
| Explicit long-running API acknowledgement | 30 seconds |
| Static asset request | Browser-managed |

These values may be revised in the Testing and Release Gate document.

A timeout means the frontend stopped waiting. It does not prove that the backend operation was cancelled.

Therefore:

- a timed-out mutation must not be automatically replayed;
- the UI should refresh authoritative backend state before offering another mutation;
- deployment requests require special duplicate-prevention handling.

---

## 14. Retry Policy

### 14.1 Safe Automatic Retries

Automatic retries are allowed only for explicitly safe read requests.

Examples:

```text
GET platform status
GET project list
GET project detail
GET deployment history
GET connected accounts
```

Retry policy:

- maximum two additional attempts;
- bounded delay;
- retry only for network failure, timeout, HTTP 408, HTTP 429, or HTTP 5xx;
- respect `Retry-After` when supported;
- abort retry when the route or component no longer needs the request.

### 14.2 Prohibited Automatic Retries

Automatic retries are prohibited for:

```text
POST create project
POST request deployment
DELETE connected account
PATCH settings
any provider connection mutation
any destructive action
```

A failed mutation must be reconciled against backend state before another attempt.

---

## 15. Cancellation and Stale Requests

Read requests must support cancellation through `AbortController`.

Cancellation is required when:

- the user leaves a page;
- a search query changes;
- a newer request replaces an older request;
- a component unmounts;
- the application session changes.

A cancelled request must not show a generic failure notification.

A cancelled request must not update state after a newer request succeeds.

---

## 16. Mutation Safety

A mutation is any request that may change backend state.

Examples:

- create project;
- request deployment;
- connect provider;
- disconnect provider;
- update project settings.

Mutation rules:

1. user intent must be explicit;
2. destructive actions require confirmation;
3. the frontend must show an in-progress state;
4. duplicate submission controls are required;
5. backend validation remains authoritative;
6. failures must preserve prior loaded state;
7. successful mutations must refresh authoritative backend data;
8. mutations must not be automatically retried;
9. a route change must not silently repeat a mutation;
10. deployment creation must not occur before a fresh readiness response.

---

## 17. Idempotency

Backend endpoints that may safely support repeated client submissions should define an idempotency contract.

Where supported, the frontend may send:

```text
Idempotency-Key: <unique-operation-key>
```

This is especially relevant to:

- deployment requests;
- project creation;
- provider connection completion;
- other operations where duplicate execution is harmful.

The frontend must not assume idempotency unless the endpoint contract explicitly documents it.

Idempotency implementation is not authorized by this draft; this section freezes the expected future pattern.

---

## 18. Pagination Contract

List endpoints should use one consistent pagination model.

Preferred request parameters:

```text
page
page_size
```

Preferred response metadata:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total_items": 0,
  "total_pages": 0
}
```

If existing endpoints use another supported shape, a feature adapter may normalize it.

Rules:

- page numbers start at 1;
- `page_size` must have a backend maximum;
- frontend route state should preserve pagination where useful;
- pages must not infer total counts from current item length;
- pagination data must remain typed.

---

## 19. Filtering, Search, and Sorting

Preferred query conventions:

```text
search=<text>
status=<stable-status-value>
sort=<field>
order=asc|desc
```

Rules:

- supported fields must be documented per endpoint;
- arbitrary backend field access is prohibited;
- invalid filters must return a stable validation error;
- frontend must URL-encode values;
- frontend must debounce text search where appropriate;
- frontend must cancel stale search requests;
- frontend must not fetch unrestricted result sets to perform large filtering in the browser.

---

## 20. Date and Time Contract

Backend timestamps should use ISO 8601 with timezone information.

Preferred format:

```text
2026-07-22T17:30:00Z
```

Rules:

- backend sends machine-readable timestamps;
- frontend formats timestamps for display;
- frontend does not modify authoritative timestamps;
- invalid timestamps must show a safe fallback;
- API modules must preserve raw values where needed;
- display formatting belongs in frontend adapters or utilities.

---

## 21. Identifier Contract

Backend identifiers must be treated as opaque strings unless a specific contract says otherwise.

Examples:

- project ID;
- repository ID;
- analysis ID;
- deployment ID;
- connected account ID.

Frontend must not:

- derive permissions from identifier shape;
- expose internal database assumptions;
- convert opaque IDs to numbers without a documented contract;
- generate backend IDs locally unless explicitly approved.

---

## 22. Enum and Status Contract

Statuses must use stable machine values.

Example:

```text
draft
repository_attached
analysis_ready
deploy_ready
deployed
failed
deleted
```

Frontend adapters may convert these to display labels.

Rules:

- machine values remain lowercase stable identifiers;
- labels are presentation concerns;
- unknown enum values must use a safe fallback;
- frontend must not crash when a new backend enum is introduced;
- unsupported states must remain visible for diagnostics;
- frontend must not reinterpret an unknown value as success.

---

## 23. Structured Messages

Warnings, blockers, and errors may be structured objects.

Preferred shape:

```json
{
  "code": "FRAMEWORK_UNKNOWN",
  "message": "Framework could not be detected.",
  "severity": "warning"
}
```

Rules:

- stable `code` is machine-readable;
- `message` is safe human-readable text;
- optional structured fields must be documented;
- frontend adapters render approved fields;
- arbitrary object serialization is prohibited;
- unknown structured messages use a safe fallback;
- backend objects must never become `[object Object]` in the UI.

---

## 24. API Type Generation

FastAPI OpenAPI is the backend schema source.

The approved type flow is:

```text
FastAPI route and schema
        ↓
OpenAPI document
        ↓
Reproducible TypeScript type generation
        ↓
frontend-v2/src/api/generated/openapi.ts
        ↓
Feature API modules
        ↓
Feature adapters and UI
```

### 24.1 Generation Rules

- type generation must be deterministic;
- generated output must not be edited manually;
- schema generation must run in CI or an approved local gate;
- stale generated types must fail validation;
- generated output must identify the source API version;
- type generation must not require production credentials;
- private secrets must not appear in the OpenAPI schema.

### 24.2 Frontend Type Rules

Generated transport types describe backend contracts.

Frontend view models may be separately defined when:

- multiple API fields are composed;
- display normalization is needed;
- compatibility adaptation is required;
- a page needs a presentation-specific shape.

View models must not replace or conceal the underlying API contract.

---

## 25. API Modules

Each backend domain has one frontend API module.

Initial modules:

| Module | Backend Domain |
|---|---|
| `auth.ts` | session and authentication entry information |
| `platform.ts` | version, health, and platform status |
| `projects.ts` | project creation, listing, detail, and readiness |
| `repositories.ts` | repository metadata |
| `repository-analysis.ts` | analysis records and results |
| `deployments.ts` | deployment request and history |
| `connected-accounts.ts` | GitHub and Cloudflare connection state |

A module may export only documented endpoint functions.

Example:

```ts
export async function getProject(
  projectId: string,
  options?: ApiCallOptions,
): Promise<ProjectResponse>;
```

Modules must not:

- import React;
- manipulate UI state;
- display notifications;
- access the DOM;
- define component text;
- directly access local storage for credentials.

---

## 26. Feature Integration Pattern

A feature consumes an API module through a feature-owned hook or service.

Example:

```text
ProjectsPage
    ↓
useProjects()
    ↓
projects API module
    ↓
shared API client
```

The feature layer may own:

- loading state;
- route-specific query state;
- data refresh;
- view-model adaptation;
- user-facing action coordination.

The feature layer must not own:

- backend authorization;
- deployment eligibility;
- provider token management;
- database persistence rules.

---

## 27. Capability Discovery

Future backend versions may add optional features.

UI V2 should not rely only on frontend version assumptions.

A future capability response may report:

```json
{
  "api_version": "1.0",
  "capabilities": {
    "projects.readiness": true,
    "deployments.cancel": false,
    "repository_analysis.deep": false
  }
}
```

Capability discovery may be included in a platform endpoint or dedicated endpoint after separate approval.

Rules:

- capabilities describe availability, not user authorization;
- unavailable capabilities must not be invoked;
- unknown capabilities default to unavailable;
- backend authorization remains mandatory;
- capability names are stable and namespaced.

---

## 28. API Versioning

The current API major version remains:

```text
/api/v1
```

### 28.1 Compatible Changes Within v1

Compatible changes may include:

- adding an optional response field;
- adding a new endpoint;
- adding an optional query parameter;
- adding a new capability flag;
- adding a new enum value when clients use safe fallbacks.

### 28.2 Breaking Changes

Breaking changes include:

- removing a field;
- changing a field type;
- renaming an endpoint;
- changing authentication behavior;
- changing required request fields;
- changing error semantics;
- changing identifier meaning.

Breaking changes require:

- a new API major version or an approved compatibility layer;
- migration documentation;
- frontend impact analysis;
- release coordination;
- deprecation period where practical.

---

## 29. Backward Compatibility

UI V2 must tolerate compatible backend evolution.

Required frontend behavior:

- ignore unknown optional fields;
- safely handle unknown enum values;
- avoid depending on object property order;
- avoid assuming all optional fields exist;
- use capability checks for optional features;
- isolate compatibility logic in adapters;
- fail clearly on required contract mismatch.

Required backend behavior:

- preserve documented v1 fields;
- avoid silent semantic changes;
- use stable error codes;
- publish OpenAPI changes;
- document deprecations.

---

## 30. Deprecation Policy

A deprecated API contract must define:

- deprecated endpoint or field;
- replacement;
- reason;
- first deprecated version;
- planned removal version or condition;
- frontend migration owner;
- tests protecting the migration.

Frontend code must not add new dependencies on deprecated contracts.

A deprecation may be considered complete only after:

- UI V2 no longer uses the contract;
- tests are updated;
- compatibility requirements are satisfied;
- removal is separately approved.

---

## 31. Contract Mismatch Handling

A contract mismatch occurs when a required response does not match the expected schema.

The frontend must:

1. stop unsafe processing;
2. create `API_CONTRACT_MISMATCH`;
3. preserve safe already loaded data;
4. show a controlled error state;
5. capture endpoint and request ID;
6. avoid dumping the invalid payload to the user;
7. allow diagnostic logging without secrets.

The frontend must not silently treat malformed required data as success.

---

## 32. Caching Rules

The browser may cache static UI assets, but API response caching must be intentional.

Default API behavior:

- do not assume browser HTTP caching;
- maintain loaded server state in the owning feature;
- refresh after successful mutations;
- refresh on explicit user request;
- refresh when route context requires current authority;
- use fresh readiness checks before deployment actions.

A dedicated client-side server-state library is not approved by this document.

Adding one later requires a decision-log entry and compatibility review.

---

## 33. Freshness Rules by Domain

### 33.1 Project Lists

May use recently loaded data for page presentation, but must refresh after project creation or modification.

### 33.2 Project Readiness

Must be fetched fresh before a deployment request.

### 33.3 Deployment History

Must refresh after a deployment request and through explicit user refresh.

Future polling or real-time updates require a separate approved contract.

### 33.4 Connected Accounts

Must refresh after connect, reconnect, or disconnect completion.

### 33.5 Platform Status

May use bounded read retry and controlled refresh.

---

## 34. Logging and Diagnostics

Frontend diagnostics may record:

- endpoint path without secret query values;
- HTTP status;
- stable error code;
- request ID;
- UI build ID;
- API version;
- timing category;
- feature name.

Frontend diagnostics must not record:

- session cookies;
- authorization headers;
- provider tokens;
- private keys;
- database URLs;
- Redis URLs;
- full sensitive response payloads;
- personal data unless explicitly approved.

Production diagnostics must remain user-safe.

---

## 35. Testing Architecture

Every API integration requires tests at the appropriate levels.

### 35.1 Shared Client Tests

Must cover:

- success envelope;
- direct payload compatibility;
- error envelope;
- HTTP error without JSON;
- network failure;
- timeout;
- abort;
- malformed JSON;
- session expiry;
- request ID capture;
- safe read retries;
- no mutation retries.

### 35.2 API Module Tests

Must cover:

- correct method;
- correct path;
- query serialization;
- request body;
- response typing;
- adapter invocation;
- stable error propagation.

### 35.3 Feature Integration Tests

Must cover:

- loading;
- success;
- empty state;
- recoverable error;
- authorization error;
- session expiry;
- mutation busy state;
- mutation success refresh;
- duplicate-submit prevention.

### 35.4 Contract Validation

The release gate must verify:

- current OpenAPI can generate frontend types;
- generated types are current;
- required endpoints exist;
- required response schemas remain compatible;
- UI V2 build compiles against the generated contracts.

---

## 36. New Backend Feature Workflow

When a YGIT backend developer adds a capability, the required sequence is:

```text
1. Document the engine-owned capability
2. Define or update FastAPI schema
3. Define authorization behavior
4. Define stable error codes
5. Update OpenAPI
6. Add backend tests
7. Regenerate frontend API types
8. Add or update one frontend API module
9. Add feature adapter when required
10. Add feature UI
11. Add integration tests
12. Pass preview and release gates
```

No frontend feature may depend on undocumented backend behavior.

---

## 37. New Frontend Feature Workflow

When the backend capability already exists:

```text
1. Identify documented endpoint
2. Confirm generated types
3. Add function to the owning API module
4. Add feature adapter when needed
5. Add feature hook or service
6. Compose approved UI components
7. Add route if required
8. Add loading, empty, error, and authorization states
9. Add tests
10. Pass preview validation
```

A developer must not modify the central API client for routine feature work.

The central client changes only when the transport contract itself changes.

---

## 38. API Ownership

| Area | Owner |
|---|---|
| Engine business capability | Owning YGIT Engine |
| FastAPI route | API Layer |
| Authentication and authorization | Existing YGIT authentication/API boundaries |
| OpenAPI schema | Backend API implementation |
| Generated frontend types | UI V2 build/tooling process |
| Shared API client | UI V2 platform layer |
| Domain API module | Owning UI V2 feature domain |
| View adapter | Owning UI V2 feature |
| Page presentation | UI V2 page/feature |
| Provider communication | Provider Layer only |

---

## 39. Security Requirements

The API architecture must preserve:

- same-origin session use;
- backend authorization;
- secure cookie behavior;
- CSRF controls required by the existing session model;
- no provider secrets in the browser;
- no secrets in OpenAPI;
- no raw exception display;
- no unvalidated arbitrary HTML;
- no direct provider calls;
- no credential persistence in local storage;
- no sensitive data in URLs;
- confirmation for destructive operations.

Any endpoint accepting user-provided repository URLs, names, slugs, or settings must validate them in the backend.

Frontend validation improves usability but is not authoritative.

---

## 40. Performance Requirements

UI V2 API usage must:

- avoid duplicate requests caused by repeated renders;
- cancel obsolete reads;
- paginate large lists;
- avoid unbounded parallel requests;
- avoid loading deployment history for every project without a documented limit;
- avoid blocking initial shell rendering on unrelated optional requests;
- load route-specific data only when needed;
- keep transformation functions pure and bounded.

Performance optimization must not weaken data freshness required for deployment safety.

---

## 41. Initial Endpoint Domains

UI V2 is expected to consume existing API domains including:

```text
/api/v1/platform/*
/api/v1/projects/*
/api/v1/repositories/*
/api/v1/repository-analysis/*
/api/v1/connected-accounts/*
```

Deployment history and deployment actions remain under the existing documented project/deployment routes.

This section does not redefine route paths. The current FastAPI route registry and later endpoint inventory remain authoritative.

---

## 42. Prohibited API Patterns

The following patterns are prohibited:

```text
fetch() inside React page components
axios instance per feature
direct GitHub API request
direct Cloudflare API request
database request from frontend
provider token in localStorage
silent catch returning empty array for required data
automatic POST retry
rendering raw response objects
hardcoded production API domain
duplicated API response interfaces
feature-specific 401 redirect logic
undocumented endpoint usage
frontend-only deployment readiness decision
```

---

## 43. Implementation Boundary

This document does not authorize:

- creation of `frontend-v2/`;
- installation of API-generation tools;
- modification of FastAPI;
- modification of OpenAPI;
- new endpoints;
- response-envelope migration;
- capability endpoints;
- idempotency implementation;
- route changes;
- production deployment.

Implementation begins only after:

1. this document is reviewed;
2. required corrections are applied;
3. status becomes Approved;
4. status becomes Frozen;
5. the UI V2 Design System Freeze and Migration Plan reach their required approval states.

---

## 44. Acceptance Criteria

This document is ready for approval when the following are accepted:

- `/api/v1` remains the UI V2 backend boundary;
- same-origin requests are mandatory;
- one shared API client is mandatory;
- pages and reusable components cannot call raw APIs;
- domain API modules are mandatory;
- FastAPI OpenAPI is the type source;
- generated types are not manually edited;
- current response compatibility is normalized centrally;
- one frontend error model is used;
- 401 and 403 behavior is centralized;
- automatic retries are read-only and bounded;
- mutations are not automatically retried;
- deployment readiness is fetched fresh before deployment;
- structured backend objects are rendered through adapters;
- API v1 backward compatibility is preserved;
- optional capabilities use explicit capability discovery when introduced;
- provider credentials never enter the frontend;
- future feature development follows the documented workflow.

---

## 45. Frozen Rules After Approval

After approval, these rules become mandatory:

1. UI V2 communicates with YGIT only through documented HTTP APIs.
2. The base API path is `/api/v1`.
3. API requests are same-origin and include the existing session.
4. Every request passes through the shared API client.
5. Pages and reusable components do not call `fetch()` directly.
6. Each backend domain has one frontend API module.
7. FastAPI OpenAPI is the canonical schema source.
8. Generated API types are reproducible and never manually edited.
9. Response compatibility logic is centralized.
10. All failures use one normalized frontend error model.
11. Session-expiry handling is centralized.
12. Safe read retries are bounded.
13. Mutations are never automatically retried.
14. Deployment readiness is backend-authoritative and freshly checked.
15. Provider APIs are never called from UI V2.
16. Secrets are never stored in browser storage.
17. Structured messages use approved adapters.
18. API breaking changes require versioning or an approved compatibility plan.
19. New backend features update documentation and OpenAPI before frontend integration.
20. Routine feature work must not modify the shared transport client.

---

## 46. Next Documentation Step

After this document is approved, the next document is:

```text
YGIT UI V2 Design System Freeze Specification
```

No UI V2 API implementation is authorized by this draft.

---

## 47. Approval Record

| Role | Name | Decision | Date |
|---|---|---|---|
| Product Owner | Pending | Pending | Pending |
| Architecture Owner | Pending | Pending | Pending |
| API Owner | Pending | Pending | Pending |
| Frontend Owner | Pending | Pending | Pending |
| Security Owner | Pending | Pending | Pending |

---

**End of Document**
