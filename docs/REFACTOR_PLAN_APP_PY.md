# Refactoring Plan: Decompose src/admin/app.py

**Objective:** Split the monolithic `src/admin/app.py` (9637+ lines) into modular routers and schemas for better maintainability and performance.

## Strategy
1.  **Extract Shared Dependencies**:
    - Identify authentication, database, and utility functions used across multiple routers.
    - Move them to `src/admin/dependencies.py` or `src/admin/utils.py`.
2.  **Separate Schemas**:
    - Move Pydantic models (Request/Response) to `src/admin/schemas/`.
    - Group by domain (e.g., `schemas/leads.py`, `schemas/campaigns.py`).
3.  **Create Modular Routers**:
    - Create `src/admin/routes/` and define APIRouters for each domain.
    - Move endpoint logic from `app.py` to the respective router file.
4.  **Update app.py**:
    - Import and include the new routers.
    - Keep only core setup (FastAPI app, middleware, global error handlers) in `app.py`.

## Module Breakdown

| Module | Schema File | Router File | Key Responsibilities |
|---|---|---|---|
| **Auth** | `schemas/auth.py` | `routes/auth.py` | Login, Signup, Session management |
| **Leads** | `schemas/leads.py` | `routes/leads.py` | Lead CRUD, Status updates, Interactions |
| **Tasks** | `schemas/tasks.py` | `routes/tasks.py` | Task creation, assignment, completion |
| **Campaigns** | `schemas/campaigns.py` | `routes/campaigns.py` | Campaign/Sequence CRUD, Enrollment |
| **Opportunities** | `schemas/opportunities.py` | `routes/opportunities.py` | Pipeline stages, Opportunity CRUD |
| **Analytics** | `schemas/analytics.py` | `routes/analytics.py` | Dashboard stats, Reports |
| **Settings** | `schemas/settings.py` | `routes/settings.py` | User management, Webhooks, Integrations |
| **Assistant** | `schemas/assistant.py` | `routes/assistant.py` | AI actions, Chat, RAG |
| **Content** | `schemas/content.py` | `routes/content.py` | Landing pages, Document library |

## Execution Steps (Phase 1: Leads & Auth)
1.  **Extract Dependencies**: Move `require_admin`, `require_rate_limit`, `get_current_admin_user` to `dependencies.py`.
2.  **Extract Auth**: Move `AdminAuthLoginRequest`, `login_admin_v1`, etc.
3.  **Extract Leads**: Move `AdminLeadCreateRequest` (which we just edited), `create_lead_admin_v1`, etc.
4.  **Verify**: Ensure the application still runs and endpoints are accessible.

## Next Phases
- Phase 2: Tasks & Campaigns
- Phase 3: Analytics & Opportunities
- Phase 4: Settings & Assistant & Content
