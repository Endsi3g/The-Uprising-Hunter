## Prospect Admin Dashboard (FR)

Frontend Next.js connecte au backend FastAPI unique (`src/admin/app.py`) via un proxy serveur (`/api/proxy/*`).

### Demarrage rapide

Depuis la racine du repo:

```powershell
.\scripts\ops\start_localhost_one_shot.ps1
```

URLs:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Backend HTML admin: `http://localhost:8000/admin`

Arret:

```powershell
.\scripts\ops\stop_localhost.ps1
```

### Variables d'environnement frontend

`admin-dashboard/.env.local` (ecrit automatiquement par le script one-shot):

```dotenv
API_BASE_URL=http://localhost:8000
ADMIN_AUTH=admin:change-me
```

Ces variables sont **server-only** (aucune exposition navigateur).

### Fonctionnalites

- UI en francais
- CRUD projets avec modales globales
- Page Parametres persistante (`GET/PUT /api/v1/admin/settings`)
- Recherche globale (`Ctrl+K` / `Cmd+K`)
- Panneau et page d'aide (`/help`)
- Flows:
  - Lead -> Projet
  - Lead -> Tache
  - Tache -> Projet

### Build

```bash
cd admin-dashboard
npm run build
```
