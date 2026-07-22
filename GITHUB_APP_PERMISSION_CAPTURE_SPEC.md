# YGIT GitHub App Installation Permission Capture Specification

Version: 1.0
Status: Approved for Implementation
Owner: Connected Accounts / GitHub Provider

## Purpose

Capture the actual permission map returned by the GitHub App installation API and persist it as safe Connected Account scope metadata.

## Provider Contract

`GitHubAppInstallation` includes a normalized permission map:

```text
permission name -> access level
```

The GitHub provider parses the installation response and must not expose an installation access token.

## Connected Account Scope Contract

The GitHub Connected Account stores:

```text
github_app:installation
repositories:<selection>
<permission>:read
<permission>:write
```

Permission entries are sorted by permission name for deterministic output.

Only `read` and `write` access values are persisted. Missing, null, `none`, or unknown access values are ignored.

## Minimum Permission Target

The current YGIT MVP least-privilege target is:

```text
metadata:read
contents:read
```

Other GitHub App permissions are not introduced or requested by this patch.

## Existing Installations

Existing Connected Account records do not gain permission metadata automatically. The controlled GitHub App installation must be reconnected after the GitHub App permission settings are corrected.

## Safety Boundary

This patch does not:

- change GitHub App settings on GitHub;
- request additional permissions;
- create installation access tokens;
- expose secrets or credentials;
- change Dashboard UI;
- modify Repository Analysis;
- change deployment provider execution;
- create a database migration.

A later independent UI patch will display the captured permission posture.
