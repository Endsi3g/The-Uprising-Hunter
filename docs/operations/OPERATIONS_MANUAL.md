# Operations and Deployment Manual

This runbook explains how to configure, deploy, and operate the platform safely.

Provider-specific references:
- `docs/operations/KOYEB_DEPLOYMENT.md` (backend)
- `docs/operations/VERCEL_DEPLOYMENT.md` (frontend)

## 1. System overview

The application is composed of:

1. Backend API (`FastAPI`)
2. Admin Dashboard (`Next.js`)
3. System Playground (`Next.js`)
4. Database (`PostgreSQL` in production, `SQLite` locally)

## 2. Access management

Do not store credentials, emails, or live connection strings in the repository.

Use your secret manager and deployment platform variables for:

- database credentials,
- OpenAI/API provider keys,
- admin auth secrets,
- deployment tokens.

## 3. Environment configuration

Use `.env.example` as the canonical template.

Minimum production requirements:

- `APP_ENV=production`
- `ADMIN_AUTH_MODE=jwt`
- strong `JWT_SECRET`
- `DATABASE_URL` set to managed Postgres
- strict `ADMIN_CORS_ALLOW_ORIGINS`

Optional:

- `ADMIN_RATE_LIMIT_PER_MINUTE`
- `ADMIN_RATE_LIMIT_WINDOW_SECONDS`
- provider keys (`OPENAI_API_KEY`, `APIFY_API_TOKEN`, `OLLAMA_API_KEY`, etc.)

## 4. Deployment flow

### Backend

1. Build and deploy backend service from default branch.
2. Set/rotate environment variables.
3. Validate health endpoint:
   - `GET /healthz`

### Frontend apps

1. Deploy `admin-dashboard`.
2. Deploy `system-playground`.
3. Confirm frontend env vars point to the active backend URL.

## 5. Post-deploy checks

Run:

```powershell
.\deploy.ps1 check
```

Validate:

- backend health (`/healthz`),
- admin login flow,
- core API routes (`/api/v1/admin/stats`, `/api/v1/admin/leads`),
- frontend accessibility.

## 6. Local operations

Start stack:

```powershell
.\deploy.ps1 up
```

Stop stack:

```powershell
.\deploy.ps1 down
```

Logs:

```powershell
.\deploy.ps1 logs
```

## 7. Incident response basics

If login/API failures occur:

1. Check backend logs.
2. Verify `DATABASE_URL` and DB reachability.
3. Verify `JWT_SECRET` is present and consistent across instances.
4. Verify CORS origins include current frontend URL.
5. Re-run health checks.

## 8. Security guidelines

- Never commit real credentials, tokens, or production URLs with embedded secrets.
- Keep `ADMIN_AUTH_MODE=jwt` in production.
- Rotate secrets after any leak suspicion.
- Prefer least-privilege service accounts.
- Keep audit logging enabled for admin actions.

## 9. Hosted Ollama (private connectivity)

When running Ollama online for open-source AI inference:

1. Expose Ollama on a private endpoint reachable by backend only (VPC/internal network/private reverse proxy).
2. Configure backend environment:
   - `OLLAMA_API_BASE_URL`
   - `OLLAMA_API_KEY` (if your Ollama gateway enforces auth)
   - `OLLAMA_MODEL_RESEARCH`
   - `OLLAMA_MODEL_CONTENT`
   - `OLLAMA_MODEL_ASSISTANT`
3. Enable the `ollama` provider from `Settings > Integrations` in admin dashboard.
4. Validate end-to-end:
   - `GET /api/v1/admin/research/web?q=test&provider=ollama&limit=3`
   - `POST /api/v1/admin/content/generate` with `"provider":"ollama"`
   - `POST /api/v1/admin/assistant/prospect/execute` with Khoj unavailable (fallback path).

Operational notes:
- Keep Ollama private; do not expose it directly to frontend clients.
- If Ollama is down, research/content/assistant gracefully fall back according to current provider logic.
