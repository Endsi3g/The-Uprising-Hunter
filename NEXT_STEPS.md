# Next Steps

## 1. Stabilisation Technique
- Ajouter des tests frontend (Playwright) pour les flows critiques:
  - Lead -> Projet
  - Lead -> Tache
  - Tache -> Projet
  - Recherche globale (`Ctrl+K` / `Cmd+K`)
- Ajouter des tests d'integration pour le proxy Next (`/api/proxy/[...path]`) avec gestion des erreurs upstream.
- Traiter les warnings de deprecation Python (SQLAlchemy + Pydantic) pour preparer la migration future.

## 2. Securite
- Remplacer les credentials Basic statiques par une authentification admin plus robuste (session/JWT + rotation secrets).
- Ajouter une configuration de credentials differenciee par environnement (dev/staging/prod).
- Ajouter des tests de non-regression sur rate limiting et controle d'acces admin.

## 3. UX Produit
- Finaliser les actions "Modifier/Supprimer" cote taches (actuellement placeholders UX).
- Ajouter pagination/tri/filtrage serveur pour leads et taches (au lieu du mode 100 items client).
- Ajouter confirmation unifiee sur toutes les actions destructives restantes.
- Ajouter indicateurs de chargement plus explicites (skeletons) sur pages `projects`, `settings`, `help`.

## 4. Performance
- Cacher certaines reponses peu volatiles (`help`, `settings`) avec invalidation sur update.
- Optimiser `search` (index SQLite complementaires sur colonnes sollicitees).
- Introduire revalidation selective SWR par cle d'entite au lieu de reload global.

## 5. Observabilite
- Ajouter logs structures par endpoint admin (latence + statut + utilisateur).
- Ajouter metriques techniques minimales (`request_count`, `error_rate`, `p95`) pour l'API admin.
- Ajouter script de verification smoke unique pour API + UI proxy.

## 6. Delivery / Ops
- Ajouter une CI qui execute:
  - `python -m pytest -q`
  - `cd admin-dashboard && npm run build`
- Ajouter versionnement de release (changelog) apres stabilisation.
- Ajouter un script de seed local pour demos (leads, taches, projets, settings).

## 7. Documentation
- Documenter le contrat exact des nouveaux endpoints dans un fichier API dedie (`docs/api/admin_v1.md`).
- Ajouter un guide "Troubleshooting localhost" pour erreurs frequentes (`port used`, `auth`, `CORS`).
- Ajouter un guide utilisateur FR court pour les nouveaux flows modaux.
