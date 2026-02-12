---
name: git-version-control-mastery
description: Establish robust Git workflows for solo and team delivery including repository setup, branching strategy, atomic commits, pull requests, conflict resolution, release tagging, and CI integration. Use when initializing a new codebase, enforcing collaboration standards, preparing deployment-safe merges, or improving repository hygiene for app projects.
---

# Git Version Control Mastery

## Overview

Run consistent, low-risk Git workflows that preserve clean history and prevent code loss.
Standardize collaboration across feature work, reviews, and release operations.

## Core Workflow

1. Initialize or audit repository settings and branch protections.
2. Define branch strategy for current team size and release cadence.
3. Require atomic commits with descriptive, convention-based messages.
4. Run CI checks on pull requests before merge.
5. Merge with clear policy, then clean up branches.
6. Tag releases and record version notes.

## Branching and Commit Rules

- Do not commit directly to `main`.
- Create one branch per feature, bug fix, or chore.
- Keep commits focused and reversible.
- Prefer conventional commit prefixes such as `feat:`, `fix:`, `chore:`, `refactor:`, `test:`.
- Rebase or merge frequently to avoid long-lived divergence.

## Pull Request Standards

- Keep PRs scoped to a single concern.
- Require passing lint and test checks before approval.
- Require at least one reviewer for shared repositories.
- Include rollback notes for risky changes.

## Release and Deployment Readiness

- Tag production releases with semantic versions.
- Protect release branches with required status checks.
- Ensure `.gitignore` includes `node_modules`, environment files, and build artifacts.
- Automate test and deploy workflows with GitHub Actions.

## Command Patterns

- Start new feature: `git checkout -b feature/<scope>`
- Commit atomically: `git add -p` then `git commit -m "feat: ..."`
- Sync before push: `git fetch --all` and rebase or merge target branch.
- Cleanup after merge: `git branch -d feature/<scope>`

## Example Invocations

- "Set up a Git strategy for a two-person project with protected main and CI gates."
- "Define a clean release flow with semantic tags and pull-request requirements."
