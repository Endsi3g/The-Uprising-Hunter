# Plan d’implémentation complet — Modale clés ENV chiffrées + Refonte Aide + Docs CompagnieDocs

## 2. Contexte et objectifs

Ce document détaille l'implémentation de trois blocs fonctionnels majeurs visant à améliorer la sécurité, l'expérience utilisateur et la documentation du système :

- **Modale clés ENV** : Interface sécurisée pour la gestion des secrets backend (API keys, etc.).
- **Refonte centre d’aide** : Amélioration de la structure et de l'accessibilité de l'aide utilisateur.
- **CompagnieDocs** : Intégration et mise à jour automatique de la documentation technique et de la bibliothèque à partir de l'index `CompagnieDocs`.

## 3. Décisions verrouillées

- **Secrets** : Stockage en base de données (DB) avec chiffrement fort.
- **Portée** : Uniquement les clés backend critiques (OpenAI, Apify, etc.).
- **Source docs** : `assets/reference/compagnie_docs/index/corpus_index.json`.
- **Livraison docs** : Déploiement dans `docs/` et affichage dynamique dans `/library`.
- **Refonte Aide** : Refonte UI/UX complète pour une navigation fluide.

## 4. Architecture cible

### Diagramme des flux

- **Secrets** : `UI /settings` -> `API secrets` -> `Chiffrement (Fernet)` -> `DB (DBAdminSetting)`.
- **Aide** : `/help` (Frontend) -> `Modale aide` -> `Payload enrichi (Backend)`.
- **Documentation** : `/library` (Frontend) -> `API docs` -> `Index CompagnieDocs`.

### Résolution des secrets (Ordre de priorité)

1. DB chiffrée (priorité haute)
2. Variables d'environnement OS (fallback)
3. Valeurs par défaut du code (si applicables)

## 5. Spécification API complète

### Endpoints Secrets

- **GET /api/v1/admin/secrets/schema** : Retourne la liste des clés attendues et leurs types.
- **GET /api/v1/admin/secrets** : Liste les clés configurées (valeurs masquées).
- **PUT /api/v1/admin/secrets** : Met à jour ou crée un secret (chiffre la valeur avant stockage).
- **DELETE /api/v1/admin/secrets/{key}** : Supprime un secret.

### Endpoints Docs & Aide

- **GET /api/v1/admin/docs/compagnie** : Récupère le catalogue depuis l'index JSON.
- **GET /api/v1/admin/help** : Retourne le payload d'aide (étendu pour supporter les nouvelles sections).

### Sécurité & Erreurs

- Accès restreint au rôle `ADMIN`.
- Erreur `401/403` si non autorisé.
- Erreur `400` si payload invalide.
- Erreur `500` si échec du chiffrement/déchiffrement.

## 6. Schéma de données et sécurité

### Stockage

- Modèle : `DBAdminSetting`
- Clé : `secure_secrets_v1`
- Format : JSON chiffré.

### Stratégie de chiffrement

- Utilisation de **Fernet** (cryptographie symétrique).
- Clé de chiffrement : `APP_ENCRYPTION_KEY` définie dans les variables d'environnement système.
- **Rotation** : Plan stratégique pour la rotation (V1 : mise à jour manuelle via API).
- **Audit Logs** : Chaque modification est loguée (horodatage, acteur), sans jamais logger la valeur secrète.

## 7. Liste canonique des clés gérées

| Domaine | Clés |
| :--- | :--- |
| **AI / NLP** | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OLLAMA_BASE_URL` |
| **Data Sourcing** | `APIFY_API_TOKEN`, `APOLLO_API_KEY` |
| **Communications** | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` |
| **Sécurité** | `JWT_SECRET`, `APP_ENCRYPTION_KEY` |
| **Infrastructure** | `DATABASE_URL`, `REDIS_URL` |

## 8. Plan frontend détaillé

### Modale "Clés d’environnement"

- **UI** : Formulaire dynamique basé sur le schéma API.
- **États** : Loading, Success, Error states.
- **Validation** : Client-side (format) + Server-side.
- **Sécurité** : Les champs secrets sont affichés comme `********` après sauvegarde ; jamais en clair.

### Refonte /help

- Navigation par sections (Guides, FAQ, API).
- Barre de recherche intégrée.
- Fallback vers documentation statique si API indisponible.

### /library dynamique

- Mapping automatique de `corpus_index.json` vers des cartes de composants.
- Filtres par catégorie et pagination.

## 9. Plan backend détaillé

- **Modules à modifier** : `services/secrets_manager.py`, `api/routes/admin.py`.
- **Validation** : Utilisation de Pydantic pour valider les payloads.
- **Compatibilité** : Maintien de la structure `HelpPayload` existante pour éviter les régressions.

## 10. Plan documentation (repo)

- **[NEW]** `docs/reference/COMPAGNIEDOCS_CATALOG.md`
- **[MOD]** `docs/README.md` (Update link structures)
- **[NEW]** `docs/operations/COMPAGNIE_DOCS_INGESTION.md`
- **[NEW]** `scripts/utilities/generate_compagniedocs_catalog.py`

## 11. Plan de tests complet

- **Unit Backend** : Tests de chiffrement/déchiffrement, validation de schéma API.
- **Unit Frontend** : Tests des composants de la modale et de la bibliothèque.
- **E2E** : Flux complet "Saisie secret -> Sauvegarde -> Vérification masquage".
- **Sécurité** : Test de non-fuite des secrets dans les logs et réponses API.
- **Cas dégradés** : Comportement si `APP_ENCRYPTION_KEY` manquante ou `corpus_index.json` corrompu.

## 12. Critères d’acceptation globaux

- Les secrets sont stockés chiffrés en DB.
- L'interface d'aide est fluide et réactive.
- La bibliothèque se met à jour dynamiquement selon l'index.
- Zéro régression sur les fonctionnalités admin existantes.
- Les commandes `npm run lint` et `pytest` passent à 100%.

## 13. Plan de livraison

1. **PR 1** : Infrastructure Backend (Secrets Manager + API).
2. **PR 2** : UI Modale Secrets + Refonte Help.
3. **PR 3** : Intégration CompagnieDocs + Scripts d'automatisation.
4. **Monitoring** : Vérification des logs système après déploiement.

## 14. Assumptions explicites

- `APP_ENCRYPTION_KEY` doit être configurée sur le serveur pour permettre l'écriture.
- Fallback automatique sur les variables d'environnement système si la clé n'existe pas en DB.
- V1 limitée à la gestion de texte (pas de fichiers secrets pour le moment).
