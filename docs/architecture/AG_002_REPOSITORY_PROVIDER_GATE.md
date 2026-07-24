# AG-002 — Repository Provider Gate

Version: 0.1.0
Status: Foundation Ready / Not Runtime-Wired
Engine: Repository Engine
Audit Name: AG-002 Repository Provider Gate
Date: 2026-07-23

## Purpose

Allow the Repository Engine to resolve a repository provider while preserving GitHub as the current default.

## Decision Contract

```text
Repository Request
        │
        ▼
Resolve Repository Provider
        │
        ├── provider missing
        │       ▼
        │    github
        │
        └── provider exists
                ▼
        selected provider
```

## Current Default

```text
github
```

## Future Provider Candidates

- GitHub
- GitLab
- Bitbucket
- Azure DevOps
- Other providers approved by future architecture documentation

## Current Runtime Boundary

AG-002 is a standalone decision contract only.

It does not:

- import or call repository providers;
- access PostgreSQL or Redis;
- change repository URL parsing;
- change GitHub App installation or credential behavior;
- change metadata acquisition or persistence;
- change Repository Analysis input;
- add API routes;
- add database models or migrations;
- wire GitLab, Bitbucket, Azure DevOps, or any other future provider;
- alter deployment behavior.

The current Repository Engine service remains GitHub-based and does not import AG-002.

## Resolution Rules

1. A missing, empty, or whitespace-only provider resolves to `github`.
2. An explicit provider remains the selected provider.
3. The gate does not validate provider availability or execute provider logic.
4. Runtime integration requires a separate approved post-MVP architecture and implementation phase.

## Safety and Rollback

The foundation consists of one pure Repository Engine module, isolated regression tests, and documentation/manifest records. Removing those additions and reverting the associated documentation restores the exact locked baseline behavior.
