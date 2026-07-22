# YGIT Project Open UI Specification

Version: 1.1
Status: Approved for Implementation
Owner: Dashboard

## Purpose

Make the existing Project `Open` button load real backend-owned Project context without moving business logic into the Dashboard.

## Read Flow

```text
Open Project
    -> GET /api/v1/projects/{project_id}
    -> GET /api/v1/projects/{project_id}/readiness
    -> GET /api/v1/repositories/{repository_id}, when attached
    -> GET /api/v1/repository-analysis/{analysis_id}, when attached
    -> render read-only Project details
```

## Displayed Values

The panel displays available backend values for:

- Project identity, slug, and status;
- Repository URL, branch, visibility, and commit;
- Analysis framework, package manager, build command, output directory, score, warnings, and errors;
- Deploy Engine readiness and blocking reasons.

## Error Handling

The Project record is loaded first.

Repository, Analysis, and readiness reads use independent settled results. A secondary read may fail without removing or mutating the Project list.

Analysis warnings and errors may be structured objects. The Dashboard formatter must:

- prefer the human-readable `message`, `detail`, `reason`, `description`, `title`, or `name` field;
- retain a safe `code` when it adds useful context;
- preserve primitive string, number, and boolean values;
- format nested arrays without exposing raw objects;
- use `Unspecified analysis detail.` for an unknown object shape;
- never render `[object Object]`;
- never dump arbitrary object properties or serialize the complete object.

The UI must:

- show a safe partial-data warning;
- preserve existing Project data;
- escape all backend-rendered values;
- prevent duplicate Open requests while the selected button is busy;
- restore the button after success or failure.

## Safety Boundary

This action is read-only.

It must not:

- send `POST`, `PATCH`, or `DELETE`;
- create or enqueue a Deployment;
- update or delete a Project;
- run or recalculate Repository Analysis;
- call GitHub or Cloudflare directly;
- change Deploy button behavior.

Deploy behavior remains unchanged and will be handled in a later independent patch.
