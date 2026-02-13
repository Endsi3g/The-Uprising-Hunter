# AI Integration Plan: Prospect Assistant via Khoj

## Summary

Implement a specialized assistant for this application using a dedicated Khoj service (Docker), exposed in a dedicated assistant experience in `admin-dashboard`.

Assistant responsibilities:

- source leads (Apify first),
- run nurturing and scoring workflows,
- create/update entities in the app,
- notify users (in-app + email depending on preferences),
- audit all actions.

## Target architecture

Environment variables:

- `KHOJ_API_BASE_URL`
- `KHOJ_API_BEARER_TOKEN`

Backend orchestrator:

- `src/admin/assistant_service.py` (Khoj call + action plan parsing)
- typed payloads in `src/admin/assistant_types.py`
- run storage in `src/admin/assistant_store.py`

## Admin API surface

Under `/api/v1/admin/assistant`:

- `POST /prospect/execute`
- `GET /prospect/runs`
- `GET /prospect/runs/{run_id}`
- `POST /prospect/confirm`

Notifications:

- add event `assistant_run_completed`

## Functional flow

1. Source leads:
   - `source_leads_apify` + enrichment + scoring + upsert.
2. Nurture leads:
   - `nurture_leads` via `FollowUpManager`.
3. Score:
   - global or targeted rescoring with current engine.
4. Notify:
   - in-app always, email by preference.
5. Audit:
   - run-level + action-level traceability.

## Guardrails

Auto-execution allowed:

- create/update leads/tasks/projects,
- sourcing,
- nurturing,
- rescoring.

Explicit confirmation required:

- deletions,
- large bulk actions,
- irreversible operations.

## Files in scope

Backend:

- `src/admin/app.py`
- `src/admin/assistant_service.py` (new)
- `src/admin/assistant_types.py` (new)
- `src/admin/assistant_store.py` (new)
- `src/core/db_models.py`
- `src/core/db_migrations.py`

Frontend:

- `admin-dashboard/app/assistant/page.tsx`
- `admin-dashboard/components/assistant-prospect-panel.tsx`
- `admin-dashboard/components/assistant-action-plan.tsx` (new)
- `admin-dashboard/components/assistant-run-result.tsx`

Config/Ops:

- `.env.example`
- `docker-compose.yml` (Khoj service)

## Test strategy

Backend:

- complete run with lead creation + nurturing + scoring
- sensitive action blocked pending confirmation
- Khoj unavailable fallback handling
- notifications emitted correctly
- full audit log
- idempotence on replay

Frontend:

- assistant view rendering
- plan rendering + execution + partial error handling
- run history
- navigation to created entities

E2E example:

- command: "Find 20 dental leads in Lyon, score them, run nurturing, notify me."
- expected: leads present, scores present, nurturing tasks created, notifications present, audit trace present.

## Rollout

- feature flag: `assistant_prospect_enabled=false`
- enable in local QA
- progressive rollout with monitoring
