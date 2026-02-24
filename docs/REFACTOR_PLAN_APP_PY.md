# Refactoring Plan: Decompose src/admin/app.py

**Objective:** Split the monolithic `src/admin/app.py` (9600+ lines) into modular routers and schemas to improve code maintainability, testability, and developer navigability.

## Architectural Rules
1.  **Package Initialization**: Ensure `src/admin/routes/__init__.py` and `src/admin/schemas/__init__.py` exist to define clean package exports.
2.  **Anti-Circular Imports**:
    - Routers may import schemas and dependencies.
    - Schemas MUST NOT import routers.
    - Dependencies/Utils MUST NOT import routers or domain-specific router schemas (shared entity models in `schemas/common.py` are exempt).
3.  **Layering**: Shared logic resides in `src/admin/dependencies.py` or `src/admin/utils.py`. `dependencies.py` contains FastAPI dependencies using `Depends(...)` and request context, while `utils.py` contains pure, framework-agnostic business logic. These modules sit at the bottom of the dependency graph.
4.  **Router Structure**: APIRouters should be defined in `src/admin/routes/<domain>.py` and included in the main `app.py`.

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

| Module | Schema File | Router File | Key Responsibilities | Prefix | Tags |
|---|---|---|---|---|---|
| **Common** | `schemas/common.py` | n/a | Shared models, pagination, errors | n/a | n/a |
| **Auth** | `schemas/auth.py` | `routes/auth.py` | Login, Session management | `/admin/auth` | `Auth` |
| **Leads** | `schemas/leads.py` | `routes/leads.py` | Lead CRUD, Status updates | `/admin/v1/leads` | `Leads` |
| **Tasks** | `schemas/tasks.py` | `routes/tasks.py` | Task creation, assignment | `/admin/v1/tasks` | `Tasks` |
| **Campaigns** | `schemas/campaigns.py` | `routes/campaigns.py` | Campaign/Sequence CRUD | `/admin/v1/campaigns` | `Campaigns` |
| **Opportunities** | `schemas/opportunities.py` | `routes/opportunities.py` | Pipeline stages, Opportunity CRUD | `/admin/v1/opportunities` | `Opportunities` |
| **Analytics** | `schemas/analytics.py` | `routes/analytics.py` | Dashboard stats, Reports | `/admin/v1/analytics` | `Analytics` |
| **Settings** | `schemas/settings.py` | `routes/settings.py` | User management, Webhooks | `/admin/v1/settings` | `Settings` |
| **Assistant** | `schemas/assistant.py` | `routes/assistant.py` | AI actions, Chat, RAG | `/admin/v1/assistant` | `Assistant` |
| **Content** | `schemas/content.py` | `routes/content.py` | Landing pages, Document library | `/admin/v1/content` | `Content` |

## Execution Steps (Phase 1: Leads & Auth)
1.  **Extract Dependencies**: Move `require_admin`, `require_rate_limit`, `get_current_admin_user` to `dependencies.py`.
2.  **Extract Auth**: Move `AdminAuthLoginRequest`, `login_admin_v1`, etc.
3.  **Extract Leads**: Move `AdminLeadCreateRequest`, `create_lead_admin_v1`, etc.
4.  **Verify**: Ensure the application still runs and endpoints are accessible.

## Next Phases
- Phase 2: Tasks & Campaigns
- Phase 3: Analytics & Opportunities
- Phase 4: Settings & Assistant & Content
