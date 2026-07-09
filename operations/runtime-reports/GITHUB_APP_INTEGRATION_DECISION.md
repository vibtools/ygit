# GitHub App Integration Decision

Version: 1.0
Status: Approved
Product: YGIT
Environment: Production MVP

## Decision

YGIT will use GitHub App installation flow for GitHub repository access.

YGIT will not use GitHub OAuth App for repository provider integration.

YGIT authentication remains Vib ID / Keycloak.

## Final Boundary

YGIT Login/Auth:
- Vib ID
- Keycloak
- OIDC Authorization Code Flow with PKCE
- Server-side session
- Secure HttpOnly cookie

GitHub Integration:
- GitHub App
- User installs YGIT GitHub App
- User selects allowed repositories
- YGIT stores installation metadata only
- YGIT generates short-lived installation access tokens server-side
- Frontend never receives GitHub tokens
- Admin never sees GitHub tokens

## Rejected Option

Classic GitHub OAuth App is rejected for MVP repository provider integration.

Reason:
- Broader user OAuth scopes
- Weaker selected-repository model
- Less appropriate for organization/repository installation flow
- Worse fit for future marketplace/webhook/deployment automation

## Required Implementation Direction

1. Add GitHub App config keys
2. Add GitHub App install URL generation
3. Add installation callback handling
4. Validate installation server-side using GitHub App JWT
5. Store installation_id as provider account reference
6. Generate installation access tokens only when needed
7. Use installation token inside GitHub Provider only
8. Never expose GitHub token values in API responses, logs, dashboard, admin, or audit metadata

## Security Rules

- Do not store plaintext GitHub tokens
- Do not expose installation tokens to frontend
- Do not expose private key content
- Do not trust installation_id without server-side validation
- Do not use GitHub as YGIT login provider
- Do not remove existing Connected Accounts API routes
- Do not remove Cloudflare placeholder support

## Current Source Note

The current Connected Accounts Module still contains placeholder OAuth-style connect behavior. The next implementation phase must replace GitHub provider connection behavior with GitHub App installation behavior while preserving existing APIs and feature boundaries.

## Conclusion

YGIT GitHub provider integration will be implemented using GitHub App architecture.
