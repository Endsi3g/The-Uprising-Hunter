# Next Steps

## 1. Deja implemente

- Backend admin:
  - CRUD complet taches (`POST/GET/PATCH/DELETE /api/v1/admin/tasks`)
  - Import CSV intelligent (`/api/v1/admin/import/csv/preview` + `/commit`)
  - Diagnostics/autofix (`/api/v1/admin/diagnostics/*`, `/api/v1/admin/autofix/*`)
- Frontend:
  - Actions taches "Modifier/Supprimer" connectees au backend
  - Import CSV depuis la page Leads (preview + mapping + commit)
  - Skeleton loaders sur pages leads/tasks/projects/settings/help
  - Proxy Next compatible body binaire/multipart
- QA/Ops:
  - Script smoke root `test_localhost_all_features.ps1`
  - Pipeline QA intelligent `run_intelligent_tests.ps1` + `scripts/qa/*`
  - Tests backend pour tasks/import/diagnostics
- Leads:
  - Page detaillee avec score breakdown, taches et projets lies
  - Edition rapide des informations
  - Filtres serveur (recherche, statut), pagination et tri serveur
- Compte et facturation:
  - Endpoints profil et facturation (`/account`, `/billing`)
  - Generation de factures PDF
- Notifications:
  - Canaux in-app et email
  - Preferences de notification par evenement
- Rapports planifies:
  - Creation/edition de plannings (`/reports/schedules`)
  - Export PDF/CSV et envoi email
- Core leads:
  - Creation manuelle de lead
  - Suppression unitaire avec confirmation
  - Actions en masse (bulk delete)
- UX:
  - Navigation fluide (liens noms leads, breadcrumbs)
  - Indicateurs de fraicheur des donnees
  - Toasts globaux
  - Badges de statut colores

## 2. Priorites produit

### Critique (audit)

- Formulaire lead: validation email temps reel + toast succes (fait)
- Navigation leads: nom cliquable vers details (fait)
- UI: contraste dark mode + banniere donnees perimees (fait)

### Haute priorite

- Analytics: corriger etat vide/chargement
- UI globale: standardiser formulaires et toasts
- Exports: verifier CSV/PDF en bout en bout

### Priorite moyenne

- Ajouter filtres serveur + pagination serveur pour les taches
- Completer analytics avec vues concretes
- Ajouter autres bulk actions leads (export, assignation, ajout campagne)

## 3. Priorites techniques

- Migrer les deprecations SQLAlchemy/Pydantic signalees par `pytest`
- Ajouter tests frontend E2E (Playwright) pour:
  - Lead -> Projet
  - Lead -> Tache
  - Import CSV
  - Recherche globale (`Ctrl+K` / `Cmd+K`)
- Ajouter tests integration proxy Next (`/api/proxy/[...path]`) avec erreurs upstream

## 4. Securite

- Remplacer Basic Auth statique par session/JWT admin robuste
- Introduire credentials differencies par environnement
- Ajouter rotation des secrets et tests de non-regression d'acces

## 5. Observabilite et delivery

- Ajouter logs structures par endpoint admin (latence/statut)
- Ajouter metriques minimales (`request_count`, `error_rate`, `p95`)
- Ajouter CI:
  - `python -m pytest -q`
  - `cd admin-dashboard && npm run build`
  - `powershell -ExecutionPolicy Bypass -File .\deploy.ps1 check`

## 6. Documentation

- Maintenir `docs/api/admin_v1.md` a jour
- Ajouter guide "Troubleshooting localhost" (ports, auth, CORS, env)
- Ajouter mini guide utilisateur FR pour modales/import/recherche/diagnostics
