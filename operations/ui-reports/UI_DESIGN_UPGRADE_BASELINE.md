# YGIT UI Design Upgrade Baseline

**Status:** Draft for local verification  
**Scope:** Dashboard, Admin Panel, logo SVG assets, favicon SVG assets  
**Baseline Commit:** fe84268 — Record VPS domain runtime verification

## Design Direction

```text
Vercel layout discipline
Linear typography/card density
Cloudflare enterprise dashboard structure
GitHub developer workflow feel
Dark-first, developer-first, dense, professional
```

## Implemented UI Rules

```text
Sidebar width: 240px
Card radius: 12px
Button height: 40px
Section gap: 24px
Border: rgba(255,255,255,.06)
Background: #090D14
Surface: #11161F
Hover: #161D29
Primary: #2F6BFF
Accent: #20B8FF
```

## Dashboard Changes

```text
Marketing-like hero reduced to compact Core Flow step strip
Metrics expanded: Projects, Deployments, Success Rate, Connected Accounts, Live Sites
Deployment Timeline added
Feature-preview items grouped under Feature Preview instead of many sidebar items
Sidebar icons added
Topbar changed to search, notifications, workspace, profile, New Project
Empty states improved
Mojibake arrows replaced with UTF-8 text
```

## Admin Changes

```text
Admin remains Platform Operations Console
Monitor → Support → Audit → Investigate flow added
Operational metrics density improved
Sidebar width, typography, cards, buttons, and borders aligned with dashboard
Logo and favicon assets match dashboard
No user dashboard flow moved into Admin
```

## Boundary

```text
No backend engine change
No API contract change
No database migration change
No provider logic change
No worker change
No GitHub push before local verification and approval
```
