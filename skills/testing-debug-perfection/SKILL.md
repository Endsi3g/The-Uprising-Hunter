---
name: testing-debug-perfection
description: Design and automate comprehensive testing and debugging workflows across unit, integration, and end-to-end layers with coverage, flake management, and performance checks. Use when creating quality gates for a new app, diagnosing regressions, hardening critical user flows, or preparing client-ready releases that must pass QA consistently.
---

# Testing Debug Perfection

## Overview

Build reliable validation pipelines that catch defects before deployment.
Debug failures systematically with reproducible evidence instead of ad hoc trial and error.

## Core Workflow

1. Translate requirements into testable acceptance criteria.
2. Define testing layers: unit, integration, and end-to-end.
3. Implement core test suites for high-risk paths first.
4. Add observability hooks and deterministic debug logs.
5. Run full test matrix in CI and block merges on failures.
6. Track coverage and flaky tests, then improve continuously.

## Testing Standards

- Write tests close to business behavior, not implementation details.
- Cover success paths, auth failures, validation errors, and network edge cases.
- Mock external services such as Supabase and Stripe where appropriate.
- Target at least 80 percent coverage on critical domains, with branch coverage for high-risk logic.

## Tooling Baseline

- Unit and integration: Jest or Vitest.
- Frontend behavior: Testing Library.
- End-to-end: Cypress or Playwright.
- Accessibility: axe checks on key pages.
- Performance and SEO: Lighthouse checks in CI where practical.

## Debugging Procedure

1. Reproduce the issue with exact inputs and environment.
2. Minimize the failing case.
3. Inspect logs, network traces, and runtime state with debugger tools.
4. Isolate root cause and write a regression test first.
5. Apply fix, run affected suites, then run full suite before merge.

## CI Quality Gates

- Fail pipeline on test failures, coverage drops below threshold, or lint errors.
- Quarantine flaky tests only with a tracked follow-up issue.
- Publish coverage and test trend artifacts for each pull request.

## Example Invocations

- "Set up Jest plus Playwright tests for auth, lead management, and checkout flows."
- "Debug an intermittent API failure and add regression coverage to prevent recurrence."
