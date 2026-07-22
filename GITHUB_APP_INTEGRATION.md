# YGIT GitHub App Integration Architecture

Version: 1.0
Status: Architecture Locked
Owner: Repository Integration

## Purpose

YGIT uses a GitHub App for GitHub repository access and installation-scoped integration.

This document locks the GitHub integration model so GitHub OAuth client authentication is not introduced accidentally.

## Authentication and Provider Boundaries

```text
YGIT user authentication
        ↓
Vib ID / Keycloak OIDC

GitHub repository integration
        ↓
GitHub App installation

Cloudflare account connection
        ↓
Cloudflare OAuth
```

These are separate contracts and must not be merged.

## GitHub App Contract

The production GitHub integration uses:

```text
GITHUB_APP_SLUG
GITHUB_APP_ID
GITHUB_APP_PRIVATE_KEY
GITHUB_APP_WEBHOOK_SECRET
```

The application configuration also owns:

```text
GITHUB_APP_NAME
GITHUB_APP_INSTALL_URL
GITHUB_API_BASE_URL
```

`GITHUB_APP_INSTALL_URL` and `GITHUB_API_BASE_URL` may use their approved defaults unless an environment-specific override is required.

Installation identifiers and repository permissions belong to the GitHub App installation workflow. They are not global OAuth client credentials.

## Forbidden GitHub OAuth Contract

The following variables are not part of the YGIT GitHub integration architecture:

```text
GITHUB_OAUTH_CLIENT_ID
GITHUB_OAUTH_CLIENT_SECRET
```

The live-readiness validator fails closed when either legacy variable is configured.

No YGIT document, readiness check, provider service, API route, or worker path may treat these variables as required GitHub credentials.

## User Authentication Boundary

GitHub does not authenticate YGIT users.

YGIT user authentication remains:

```text
Vib ID / Keycloak
OIDC Authorization Code Flow
PKCE S256
Server-side session
Secure HttpOnly cookie
```

GitHub App installation authorizes repository integration only.

## Cloudflare Boundary

Cloudflare remains a separate OAuth-connected provider.

GitHub App credentials must never be reused as Cloudflare credentials, and Cloudflare OAuth credentials must never be used for GitHub integration.

## Secret Handling

The following values are secrets and must never be printed, returned by APIs, committed, or included in screenshots:

```text
GITHUB_APP_PRIVATE_KEY
GITHUB_APP_WEBHOOK_SECRET
```

Readiness output reports only configured, missing, invalid, or forbidden state.

## Change Control

Changing YGIT from GitHub App integration to another GitHub authentication model requires all of the following before implementation:

1. A separately approved architecture document.
2. A versioned revision of this contract.
3. Security and permission-model review.
4. Provider, API, worker, database, test, and migration impact review.
5. Explicit project-owner approval.

Until that process is completed, the GitHub App model is authoritative.

## Non-Goals

This contract does not:

- create a new authentication engine;
- replace Vib ID / Keycloak;
- add GitHub OAuth login;
- add GitHub OAuth repository authorization;
- change Cloudflare OAuth;
- change AG-001;
- create a YGIT App Engine.
