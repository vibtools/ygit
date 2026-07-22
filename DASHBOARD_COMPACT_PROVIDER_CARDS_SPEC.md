# YGIT Dashboard Compact Provider Cards Specification

Version: 1.0
Status: Approved for Implementation
Owner: Dashboard

## Purpose

Use the existing desktop gap below the Dashboard hero actions for two compact provider cards.

The full Connected Accounts page remains unchanged.

## Desktop Placement

The compact section is positioned below:

```text
Create Project / Connect Accounts
```

and inside the existing unused space before the following Dashboard sections.

At desktop width, the section must not contribute additional layout height. It uses the existing open area beside the Deployment Timeline.

## Card Layout

```text
GitHub card             Cloudflare card
50 percent              50 percent
```

Contract:

- section height: 200px;
- card gap: 22px;
- card padding: 20px;
- border radius: existing `var(--radius)`;
- existing Dashboard surface, border, and shadow language;
- two equal columns at desktop width;
- responsive static layout below 1180px;
- one column below 760px.

## GitHub Fields

The Dashboard card displays only:

- Status;
- Username;
- Repository Access;
- Scopes;
- Last Sync;
- Manage.

Repository Access is derived from the stored `repositories:<selection>` scope.

## Cloudflare Fields

The Dashboard card displays only:

- Status;
- Account;
- Token Status;
- Permissions;
- Last Sync;
- Manage.

Token Status is derived from the safe Connected Account status. No token value is displayed.

## Data Boundary

The cards use only the existing Connected Accounts response already loaded by the Dashboard.

They must not:

- request provider APIs;
- expose token references, access tokens, refresh tokens, or secrets;
- mutate Connected Accounts;
- change GitHub or Cloudflare permissions;
- change Project Open or Deploy behavior.

## Existing Sections

The following remain byte-for-byte unchanged:

- Dashboard metrics;
- Deployment Timeline content;
- Active Workspace panel content;
- full Connected Accounts page;
- Project Open UI;
- Project Deploy UI.

The obsolete narrow Dashboard Provider Readiness panel is removed because its two-column full account cards caused the layout break.
