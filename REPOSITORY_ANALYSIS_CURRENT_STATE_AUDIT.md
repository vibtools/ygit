# YGIT Repository Analysis Current-State Audit

Version: 1.0
Status: Approved Current-State Audit
Date: 2026-07-22
Owner: Repository Analysis Engine
Implementation Change: None

## Purpose

This document records the current Repository Analysis execution path and the exact gaps that prevent a repository with incomplete metadata from becoming deploy-ready.

This patch documents current behavior only. It does not implement repository acquisition, deep-analysis execution, Project mutation, provider calls, or deployment.

## Current Data Flow

```text
Project Create
    -> Repository Engine fetches GitHub repository metadata
    -> Repository metadata is persisted
    -> Repository Analysis Engine prepares analysis input
    -> Quick Analysis reads file_tree_snapshot
    -> framework, package manager, build command, output directory,
       render mode, warnings, readiness, and score are calculated
    -> Analysis result is stored
    -> Project is attached to Repository and Analysis
    -> Project status reflects Analysis deploy readiness
```

## Verified Current Behavior

### Project creation attaches the initial Analysis

Project creation fetches repository metadata, runs Quick Analysis with the new Project ID, and attaches the resulting Repository and Analysis records to the Project.

The Project becomes deploy-ready only when the stored Analysis reports `deploy_ready=true`.

### Quick Analysis depends on repository file paths

Quick Analysis obtains its file list exclusively from:

```text
RepositoryAnalysisInput.file_tree_snapshot
```

The file index recognizes path-like values under:

```text
path
name
file
filename
files
tree
items
children
paths
```

Framework, package-manager, static/dynamic, build-command, output-directory, readiness, score, warnings, and recommendations are derived from those extracted paths.

### Current GitHub metadata is incomplete for real Analysis

The current repository metadata path calls the GitHub repository metadata endpoint without an installation-token authorization header.

It currently stores:

```text
latest_commit_sha = None
file_tree_snapshot = {"default_branch": "<branch>"}
```

The default branch name is metadata, not a repository file path. It does not provide `package.json`, framework configuration, source files, or build-output evidence.

Therefore the current Quick Analysis path can legitimately return unknown framework/output/build information and keep the Project blocked.

### Deploy readiness is fail-closed

Readiness is blocked when any applicable condition is present:

- framework is unknown;
- output directory is unknown;
- dynamic server behavior is detected;
- a non-HTML framework has no known build command.

This behavior is correct for the current incomplete input. The Dashboard must display blockers; it must not bypass them.

### Deep Analysis is currently a queue boundary

The current Deep Analysis layer creates or enqueues a `repository_analysis_deep` job reference.

This audit does not establish evidence of a worker implementation that acquires repository contents, executes deep detection, stores a completed deep result, and updates the Project.

### Recalculation does not reattach the new result to the Project

The current recalculation path loads an existing Analysis and runs Quick Analysis again using the Repository ID.

It does not pass the previous Project ID and does not call the Project attachment boundary. A new Analysis result therefore does not automatically become the Project's active Analysis through this path.

## Current Blocking Chain

```text
GitHub metadata without installation-token repository acquisition
    -> no pinned commit SHA
    -> no actual file tree
    -> Quick Analysis receives insufficient paths
    -> framework/output/build may remain unknown
    -> deploy_ready=false
    -> Deploy Engine and Dashboard correctly block deployment
```

## Required Future Implementation Sequence

The future implementation should remain engine-owned and proceed in separate approved patches:

1. Resolve the user's GitHub App installation credential through Connected Accounts.
2. Acquire repository metadata using an installation token.
3. Resolve and persist the selected branch's commit SHA.
4. Acquire a normalized Git tree or equivalent bounded file-path snapshot.
5. Support private repositories through the GitHub App installation boundary.
6. Run Quick Analysis against the real, commit-pinned file tree.
7. Define and implement the deep-analysis worker execution contract.
8. Persist the completed Analysis result.
9. Reattach the latest approved Analysis to the Project through the Project Engine.
10. Re-evaluate Deploy Engine readiness and expose the result to the Dashboard.
11. Run controlled live GitHub and Cloudflare deployment validation.

## Security and Ownership Requirements

Future repository acquisition must:

- use the user's GitHub App installation authorization;
- never expose installation tokens to the Dashboard or job payload;
- keep provider calls inside the Provider Layer;
- keep Repository and Analysis business logic inside their engines;
- pin analysis to a commit SHA;
- bound tree size and API pagination;
- fail closed on missing or inconsistent repository data;
- preserve repository ownership and user-access checks;
- avoid logging credentials or private source contents.

## Explicit Non-Goals of This Patch

This audit patch does not:

- change Repository Analysis source;
- call GitHub or Cloudflare;
- clone a repository;
- acquire a Git tree;
- implement a deep-analysis worker;
- update a Project's active Analysis;
- change Deploy readiness rules;
- create a database migration;
- change Project Open or Deploy UI;
- change provider execution policy;
- integrate AG-001.

## Verification Boundary

The audit contract tests verify that this document matches the current source at the audited commit.

Passing tests do not prove:

- live private-repository access;
- installation-token repository acquisition;
- real Git tree retrieval;
- deep-analysis worker completion;
- Project reattachment after recalculation;
- live PostgreSQL or Redis behavior;
- a real Cloudflare Pages deployment.

## Revision History

| Date | Version | Summary |
|---|---|---|
| 2026-07-22 | 1.0 | Recorded the current metadata, Quick Analysis, readiness, deep-queue, recalculation, and Project-attachment boundaries |
