# ProspectionApp

Plateforme de prospection B2B avec:
- sourcing de leads (manuel + API),
- enrichissement/recherche web,
- scoring ICP + Heat,
- pilotage admin (leads, tasks, projects, diagnostics, imports CSV),
- assistant de prospection et workflows de nurturing.

## Stack

- Backend: `FastAPI`, `SQLAlchemy`, `Pydantic`
- DB: `SQLite` (local) / `PostgreSQL` (prod)
- Frontend principal: `admin-dashboard` (Next.js)
- Frontend sandbox: `system-playground` (Next.js)
- Scripts ops/QA: PowerShell + Python (`scripts/`)

## Fonctionnalités clés

- Pipeline de leads (`Apollo`, `Apify`, création manuelle)
- Recherche web multi-provider (`duckduckgo`, `perplexity`, `firecrawl`)
- Scoring dual:
  - `icp_score` (fit)
  - `heat_score` (timing/engagement)
- Admin API v1:
  - auth admin (basic/jwt/hybrid),
  - leads/tasks/projects,
  - settings/integrations/webhooks,
  - notifications/reports,
  - import CSV intelligent,
  - diagnostics + autofix.
- Assistant prospect:
  - runs/actions confirmables,
  - exécution de plans (source/rescore/nurture/research/etc.).

## Structure du projet

```text
src/
  admin/            API admin, assistant, recherche, import, diagnostics
  ai_engine/        génération de messages/prompts
  core/             modèles, DB, migrations de compatibilité, logging
  enrichment/       sourcing + enrichissement
  intent/           providers intent (mock/bombora/6sense)
  outreach/         logique follow-up
  scoring/          moteur de scoring + config
  workflows/        orchestration pipeline

admin-dashboard/    UI principale Next.js
system-playground/  playground UI Next.js
scripts/            ops, QA, utilitaires, vérification
tests/              tests backend API et logique
docs/               docs stratégie/API/playbooks
assets/             assets de référence
archive/            artefacts historiques
```

## Démarrage local (backend)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

Créer le fichier d’environnement:

```powershell
Copy-Item .env.example .env
```

Lancer l’API admin:

```powershell
uvicorn src.admin.app:app --reload --port 8000
```

Healthcheck:

```powershell
Invoke-RestMethod http://localhost:8000/healthz
```

## Démarrage local (dashboard Next.js)

```powershell
cd admin-dashboard
npm install
npm run dev
```

Dashboard: `http://localhost:3000`  
API: `http://localhost:8000`

## Démarrage Docker

```powershell
.\deploy.ps1 up
.\deploy.ps1 check
```

## Variables d’environnement principales

```dotenv
# Auth admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me
ADMIN_AUTH_MODE=hybrid
JWT_SECRET=change-me

# API keys
OPENAI_API_KEY=
APOLLO_API_KEY=
APIFY_API_TOKEN=
PERPLEXITY_API_KEY=
FIRECRAWL_API_KEY=

# Intent provider
INTENT_PROVIDER=mock
INTENT_PROVIDER_API_KEY=
INTENT_PROVIDER_BASE_URL=

# DB
DATABASE_URL=sqlite:///./prospect.db

# CORS / rate limit
ADMIN_CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ADMIN_RATE_LIMIT_PER_MINUTE=120
ADMIN_RATE_LIMIT_WINDOW_SECONDS=60
```

## Endpoints API importants

- `GET /healthz`
- `GET /api/v1/admin/stats`
- `GET /api/v1/admin/metrics`
- `GET /api/v1/admin/leads`
- `POST /api/v1/admin/leads`
- `POST /api/v1/admin/rescore`
- `GET /api/v1/admin/research/web`
- `POST /api/v1/admin/research`
- `POST /api/v1/admin/import/csv/preview`
- `POST /api/v1/admin/import/csv/commit`
- `POST /api/v1/admin/diagnostics/run`
- `POST /api/v1/admin/autofix/run`
- `POST /api/v1/admin/assistant/prospect/execute`

Référence API détaillée: `docs/api/admin_v1.md`.

## Tests

Exécuter la suite:

```powershell
python -m pytest -q
```

Exécuter un fichier ciblé:

```powershell
python -m pytest tests/test_admin_assistant_api.py -v
```

## Scripts utiles

- `deploy.ps1` (up/down/logs/check)
- `scripts/ops/healthcheck.py`
- `scripts/ops/check_pipeline.py`
- `scripts/qa/run_intelligent_diagnostics.ps1`
- `scripts/verification/verify_advanced_system.py`

## Hygiène repo (cleanup)

Le dépôt ignore désormais explicitement:
- caches PyTest temporaires,
- backups `*.bak`,
- artefacts `node_modules/.next`,
- copie locale `prospecting_system/`.

Cela évite de polluer les commits avec des artefacts non source.
