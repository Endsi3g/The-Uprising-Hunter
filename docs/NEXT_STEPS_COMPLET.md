# 📋 The Uprising Hunter — Next Steps Complet

**Date :** 20 février 2026  
**Auteur :** Analyse automatisée complète du codebase  
**Email de connexion :** `sitavex909@cameltok.com`

---

## 🔐 Informations de Connexion & Base de Données

| Clé | Valeur |
|---|---|
| **Email de connexion** | `sitavex909@cameltok.com` |
| **Base de données locale** | `uprising_hunter.db` (SQLite, ~1.1 MB) |
| **Supabase Project ID** | `frcfaxckvqojizwhbaac` |
| **Supabase local** | `http://localhost:54323` (Studio) |
| **Backend API** | `http://localhost:8000/docs` (Swagger) |
| **Frontend** | `http://localhost:3000` |
| **Grafana** | `http://localhost:3001` |
| **Prometheus** | `http://localhost:9090` |

---

## 🚨 CRITIQUES — À Réparer Immédiatement

### 1. Backend ne démarre pas — `uvicorn` introuvable

```
startup_errors.log:
C:\The Hunter\The-Uprising-Hunter\.venv\Scripts\python.exe: No module named uvicorn
```

**Action :** Installer les dépendances manquantes dans le venv :

```powershell
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

**Cause probable :** Le venv a été recréé ou les dépendances n'ont pas été installées correctement. Le fichier `requirements.txt` inclut `uvicorn>=0.30.0` mais il n'est pas installé.

---

### 2. Monolithe `app.py` (350 KB) — Refactoring urgent

Le fichier `src/admin/app.py` fait **350 801 octets** (~8 000+ lignes). C'est le plus gros risque technique du projet :

- Impossible à maintenir ou déboguer efficacement
- Temps de rechargement lent en développement
- Conflits de merge fréquents
- Difficile à tester unitairement

**Action :** Découper en sous-modules par domaine :

| Module cible | Endpoints à extraire |
|---|---|
| `admin/routes/leads.py` | CRUD leads, lead detail, bulk operations |
| `admin/routes/tasks.py` | CRUD tâches, assignation |
| `admin/routes/campaigns.py` | Campagnes, séquences, enrollments |
| `admin/routes/opportunities.py` | Pipeline, opportunités |
| `admin/routes/analytics.py` | Stats, KPIs, forecasts |
| `admin/routes/auth.py` | Login, JWT, sessions |
| `admin/routes/settings.py` | Config admin, webhooks, intégrations |
| `admin/routes/assistant.py` | Prospect AI, runs, actions |

---

### 3. Supabase non connecté en production

La DB est actuellement SQLite locale (`uprising_hunter.db`). La migration vers Supabase PostgreSQL est prévue mais jamais finalisée :

- `supabase/config.toml` est configuré (project ID, ports)
- `supabase/functions/` contient 3 edge functions squelettes
- Aucune migration SQL dans `supabase/migrations/`

**Action :**
1. Exporter le schéma SQLite actuel en SQL
2. Créer les migrations Supabase correspondantes
3. Migrer les données de dev
4. Configurer `DATABASE_URL` vers PostgreSQL

---

## ⚠️ IMPORTANTS — Fonctionnalités Incomplètes

### 4. Module Outreach — Squelette uniquement

`src/outreach/` ne contient qu'un seul fichier (`follow_up.py`, 83 lignes). C'est le cœur de la proposition de valeur (engagement multi-canal) mais il est à peine commencé :

- ✅ `FollowUpManager` avec logique par tiers et stages
- ❌ Pas d'envoi d'email réel (ni SMTP, ni SendGrid, ni Mailgun)
- ❌ Pas d'intégration LinkedIn API
- ❌ Pas d'envoi WhatsApp (Twilio/MessageBird)
- ❌ Pas de séquences automatisées (les campagnes sont définies en DB mais jamais exécutées)
- ❌ Pas de tracking d'ouverture/clic (pixels, webhooks)

**Action :** Implémenter le pipeline d'envoi :
1. Service SMTP/API pour emails transactionnels
2. Intégration Twilio pour SMS/WhatsApp
3. Worker asynchrone pour exécuter les séquences
4. Webhooks entrants pour tracking (opens, clicks, bounces)

---

### 5. Module Workflows — Minimal

`src/workflows/` contient `manager.py` (4 KB) et `rules_engine.py` (3.5 KB). Le workflow engine est fonctionnel mais basique :

- ✅ Rules engine avec triggers et conditions
- ❌ Pas d'exécution asynchrone (tout est synchrone)
- ❌ Pas de retry/erreur handling
- ❌ Pas de logs d'exécution dans l'UI
- ❌ Page `/workflows` du frontend est vide (placeholder)

**Action :** Ajouter Celery ou un task queue pour exécution asynchrone + logger les runs.

---

### 6. Module AI Engine — Partiel

`src/ai_engine/` contient 5 fichiers. L'intégration Ollama/OpenAI est en place pour :
- ✅ Génération de contenu personnalisé
- ✅ Research automatique via Perplexity
- ❌ Scoring IA non connecté au scoring engine
- ❌ Assistant IA (`/assistant`) dépend de Khoj (service externe) — non fonctionnel sans Docker

---

### 7. Pages Frontend — Fonctionnalité manquante

| Page | État | Problème |
|---|---|---|
| `/workflows` | ❌ Placeholder | UI non implémentée, backend minimal |
| `/reports` | ⚠️ Basic | Affiche des rapports mais pas de génération/export |
| `/research` | ⚠️ Basic | Recherche web via Perplexity, dépend de clé API |
| `/builder` | ⚠️ Basic | Landing page builder, manque preview live |
| `/billing` | ⚠️ Partiel | Stripe configuré mais non testé en production |
| `/help` | ⚠️ Basic | Page d'aide statique |
| `/demo` | ⚠️ Basic | Mode démo, données mock |
| `/notifications` | ⚠️ Basic | Liste notifications, pas de push réel |
| `/library` | ⚠️ Basic | Gestion documents, upload fonctionnel |
| `/assistant` | ⚠️ Dépendant | Nécessite Khoj (Docker) pour fonctionner |

---

### 8. Monitoring — Service Role Key manquant

`monitoring/prometheus.yml` contient `INSERT_SERVICE_ROLE_KEY_HERE`. Le script `launch_full_stack.ps1` détecte cette placeholder et skip le monitoring :

```powershell
if ($PromConfig -match "INSERT_SERVICE_ROLE_KEY_HERE") {
    Write-Warning "⚠️ Service Role Key not set..."
}
```

**Action :** Remplacer par la vraie service role key de Supabase après `npx supabase start`.

---

## 📊 Inventaire Technique Complet

### Backend — 11 Modules Python

| Module | Fichiers | Rôle | État |
|---|---|---|---|
| `src/admin` | 16 services + app.py | API admin complète | ⚠️ Monolithe |
| `src/api` | 5 fichiers (server + routers) | API publique | ✅ OK |
| `src/core` | 7 fichiers (DB, models, migrations) | Socle technique | ✅ OK |
| `src/scoring` | 4 fichiers (engine, config, optimizer) | Scoring leads | ✅ OK |
| `src/enrichment` | 3 fichiers | Enrichissement via Apify | ✅ OK |
| `src/ai_engine` | 5 fichiers | Moteur IA (OpenAI/Ollama) | ⚠️ Partiel |
| `src/intent` | 7 fichiers | Signaux d'achat (Bombora/6sense) | ✅ OK |
| `src/outreach` | 1 fichier | Engagement multi-canal | ❌ Squelette |
| `src/sales` | 2 fichiers | Logique vente | ⚠️ Minimal |
| `src/workflows` | 2 fichiers | Automatisation | ⚠️ Basic |
| `src/landing` | 2 fichiers | Landing pages | ✅ OK |

### Base de Données — 37 Modèles SQLAlchemy

| Catégorie | Modèles |
|---|---|
| **CRM Core** | DBCompany, DBLead, DBInteraction, DBTask, DBProject, DBOpportunity, DBAppointment |
| **Funnel** | DBStageEvent, DBSmartRecommendation, DBTeamQueue |
| **Campaigns** | DBCampaignSequence, DBCampaign, DBCampaignEnrollment, DBCampaignRun |
| **Admin** | DBAdminSetting, DBAdminUser, DBAdminRole, DBAdminUserRole, DBAuditLog, DBAdminSession |
| **Intégrations** | DBWebhookConfig, DBIntegrationConfig, DBAccountProfile |
| **Billing** | DBBillingProfile, DBBillingInvoice |
| **Notifications** | DBNotificationPreference, DBNotification |
| **Reports** | DBReportSchedule, DBReportRun |
| **IA** | DBAssistantRun, DBAssistantAction, DBContentGeneration, DBEnrichmentJob |
| **Content** | DBLandingPage, DBDocument |
| **Workflows** | DBWorkflowRule |

### Frontend — 25 Routes Next.js

| Route | Statut | Notes |
|---|---|---|
| `/` | ✅ | Landing page |
| `/login` | ✅ | Authentification JWT |
| `/create-account` | ✅ | Inscription |
| `/dashboard` | ✅ | KPIs, graphiques, pipeline |
| `/leads` | ✅ | Table + Kanban, filtres avancés |
| `/leads/[id]` | ✅ | Détail lead, 7 onglets |
| `/tasks` | ✅ | Table tâches, filtres |
| `/tasks/[id]` | ✅ | Détail tâche |
| `/campaigns` | ✅ | Création, séquences, wizard |
| `/analytics` | ✅ | Graphiques, bar chart |
| `/appointments` | ✅ | Calendrier RDV |
| `/opportunities` | ✅ | Pipeline commercial |
| `/projects` | ✅ | Gestion projets |
| `/projects/[id]` | ✅ | Détail projet |
| `/settings` | ✅ | Config, intégrations, webhook |
| `/settings/team` | ✅ | Gestion utilisateurs |
| `/settings/changelog` | ✅ | Historique versions |
| `/systems` | ✅ | Diagnostic système |
| `/notifications` | ⚠️ | Basique |
| `/reports` | ⚠️ | Basique, pas d'export |
| `/research` | ⚠️ | Dépend de Perplexity API |
| `/builder` | ⚠️ | Landing builder basique |
| `/workflows` | ❌ | Placeholder vide |
| `/billing` | ⚠️ | Stripe non testé |
| `/assistant` | ⚠️ | Dépend de Khoj |

### Tests — 40 Fichiers pytest

- 30 tests API admin (auth, leads, campaigns, tasks, etc.)
- 6 tests unitaires (scoring, intent, workflows)
- 4 scripts de vérification manuelle

---

## 🎯 Prochaines Étapes — Plan d'Action Priorisé

### Phase 1 : Stabilisation (1-2 jours)

- [ ] **Réparer le backend** — `pip install -r requirements.txt` dans le venv
- [ ] **Vérifier que toute l'app démarre** via `launch_full_stack.ps1`
- [ ] **Tester les 25 routes frontend** dans le navigateur
- [ ] **Exécuter la suite de tests** — `pytest tests/ -v`
- [ ] **Fixer les erreurs de build** restantes (lints signalées)

### Phase 2 : Refactoring critique (3-5 jours)

- [ ] **Découper `app.py`** en sous-modules par domaine (au moins 8 fichiers)
- [ ] **Migrer vers PostgreSQL/Supabase** — écrire les scripts de migration
- [ ] **Configurer le monitoring** avec la vraie service role key
- [ ] **Nettoyer les variables d'environnement** — `.env` vs `.env.local` vs `.env.example`

### Phase 3 : Fonctionnalités business (1-2 semaines)

- [ ] **Implémenter Outreach** — emails réels, SMS, tracking
- [ ] **Compléter Workflows** — exécution asynchrone, UI complète
- [ ] **Activer le billing Stripe** — tests en sandbox
- [ ] **Faire fonctionner l'assistant IA** sans dépendance Khoj (fallback OpenAI direct)
- [ ] **Compléter la page Reports** — génération PDF, export CSV avancé

### Phase 4 : Production-ready (1 semaine)

- [ ] **Déployer sur Cloud Run** (Dockerfile existant)
- [ ] **CI/CD GitHub Actions** (workflow existant dans `.github/`)
- [ ] **Configurer les secrets de production** — Fernet key, JWT, Stripe live
- [ ] **Optimiser les performances** — pagination, indexes DB, caching
- [ ] **Documentation API** — OpenAPI spec est à 291 KB, vérifier l'exhaustivité

### Phase 5 : Growth features (en continu)

- [ ] **Scoring IA** — connecter l'AI engine au scoring engine
- [ ] **Intent data** — activer Bombora/6sense en production
- [ ] **Landing page builder** — preview live, A/B testing
- [ ] **Notifications push** — intégrer Firebase Cloud Messaging
- [ ] **Multi-tenant** — support multi-utilisateurs avec permissions granulaires

---

## 🐛 Bugs et Lints Connus

| Fichier | Problème | Priorité |
|---|---|---|
| `menu-toggle-icon.tsx` | Inline CSS (devrait être externe) | Basse |
| `modal-system-provider.tsx:432` | Formulaire sans label/title/placeholder | Moyenne |
| `opportunities/page.tsx:124` | `min-h-[12rem]` → `min-h-48` | Basse |
| `opportunities/page.tsx:129` | Inline CSS | Basse |
| `projects/[id]/page.tsx:301` | Inline CSS | Basse |
| `analytics/page.tsx:180` | Inline CSS (progress bar width) | Basse |
| `campaigns/page.tsx` | Variable inutilisée `setUseFormForSteps` | Basse |
| `projects/page.tsx` | Import inutilisé `IconSearch` | Basse |
| `leads/page.tsx` | Import inutilisé `Skeleton` | Basse |

---

> **Dernière mise à jour :** 20 février 2026, 00h42 EST  
> **Prochain review :** Après Phase 1 (stabilisation complète)
