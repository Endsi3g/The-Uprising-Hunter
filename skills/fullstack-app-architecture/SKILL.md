---
name: fullstack-app-architecture
description: Guide creation of complete, scalable full-stack applications across requirements planning, UI/UX design, frontend and backend implementation, database and API integration, testing, deployment, and monitoring. Use when starting a new product, defining MVP scope, or restructuring an existing app into production-ready frontend, backend, data, and delivery layers with TypeScript, React or Next.js, Node.js, and Supabase or PostgreSQL.
---

# Fullstack App Architecture

## Overview

Build production-ready full-stack applications with clear layers, delivery milestones, and quality gates.
Prioritize secure foundations, fast iteration, and maintainable structure over ad hoc implementation.

## Core Workflow

1. Define scope with user stories and acceptance criteria.
2. Draft wireframes and user flows for core journeys.
3. Define architecture boundaries for frontend, backend, data, and integrations.
4. Implement authentication and authorization first.
5. Implement feature slices end to end: UI, API, data model, and validation.
6. Add automated test coverage for critical paths before feature completion.
7. Deploy with CI and observability, then iterate from usage feedback.

## Recommended Stack Baseline

- Frontend: React or Next.js with TypeScript.
- Backend: Node.js APIs, or Supabase edge functions where suitable.
- Data: PostgreSQL with migrations and explicit schema ownership.
- Auth: Supabase Auth with JWT or OAuth flows.
- Delivery: Vercel for frontend and managed backend deployment path.

## Architecture Rules

- Use a monorepo with clear app and service boundaries.
- Separate concerns by domain: UI components, application services, and infrastructure adapters.
- Keep API contracts explicit and versionable.
- Design normalized schemas first, then optimize with targeted denormalization only when measured.
- Run migrations in CI and require rollback strategy for production changes.

## Security and Reliability Gates

- Enforce authentication on all protected routes before feature rollout.
- Validate all external input at API boundaries.
- Keep secrets in environment variables and never in source control.
- Block release when critical test suites fail.

## Deliverables Checklist

- Architecture overview with chosen stack and tradeoffs.
- Initial backlog mapped to user stories.
- DB schema and migration plan.
- API endpoint map and auth model.
- Test strategy across unit, integration, and end-to-end.
- Deployment and monitoring plan with rollback steps.

## Example Invocations

- "Set up an MVP contractor CRM with Supabase auth, Next.js UI, leads API, and deployment plan."
- "Design an e-commerce architecture with React frontend, Node API, PostgreSQL schema, and CI pipeline."
