# Workflow Supabase & Edge Functions

Ce document décrit les processus pour développer et déployer avec Supabase en équipe.

## 🚀 Prérequis

1. **Docker Desktop** (Doit être lancé pour le développement local)
2. **Supabase CLI** (Installé via npm ou brew)

    ```bash
    npm install -g supabase
    # ou
    brew install supabase/tap/supabase
    ```

3. **Login**

    ```bash
    supabase login
    ```

## 🛠 Développement Local

1. **Démarrer Supabase localement**

    ```bash
    npx supabase start
    ```

    Cela lance une stack complète (Postgres, Studio, Edge Runtime, etc.) sur votre machine via Docker.
    Dashboard Studio: `http://localhost:54323`

2. **Arrêter**

    ```bash
    npx supabase stop
    ```

## 🔄 Gestion des Migrations (Travail d'Équipe)

Pour éviter les conflits de schéma, nous utilisons les migrations.

1. **Faire des changements**
    Utilisez le Studio local (`http://localhost:54323`) pour modifier vos tables.

2. **Générer une migration**

    ```bash
    npx supabase db diff -f nom_de_la_migration
    ```

    Cela crée un fichier SQL dans `supabase/migrations/`.

3. **Appliquer les migrations localement**
    Si un collègue a poussé une migration :

    ```bash
    git pull
    npx supabase db reset
    ```

4. **Déployer en Production**
    Lier le projet distant (si ce n'est pas fait):

    ```bash
    npx supabase link --project-ref frcfaxckvqojizwhbaac
    ```

    Pousser les migrations :

    ```bash
    npx supabase db push
    ```

## ⚡ Edge Functions

Les Edge Functions se trouvent dans `supabase/functions/`.

1. **Créer une nouvelle fonction**

    ```bash
    npx supabase functions new ma-fonction
    ```

2. **Tester localement**

    ```bash
    npx supabase functions serve ma-fonction --no-verify-jwt
    ```

    URL: `http://localhost:54321/functions/v1/ma-fonction`

3. **Déployer en Production**

    ```bash
    npx supabase functions deploy ma-fonction
    ```

## 🔐 Gestion des Secrets

Pour définir des secrets de production pour les Edge Functions :

```bash
npx supabase secrets set MY_SECRET=value
```

## 🌍 Configuration

Le fichier `supabase/config.toml` contient la configuration du projet et l'ID du projet distant (`frcfaxckvqojizwhbaac`).

## 📊 Monitoring (Prometheus & Grafana)

Nous avons mis en place une stack d'observabilité locale pour suivre les métriques de Supabase.

1. **Configuration**
    * Éditez `monitoring/prometheus.yml` et remplacez `INSERT_SERVICE_ROLE_KEY_HERE` par la clé `service_role` de votre projet Supabase (Project Settings > API Keys).

2. **Lancement**
    Dans le dossier `monitoring/` :

    ```bash
    docker-compose up -d
    ```

3. **Accès**
    * **Grafana** : `http://localhost:3001` (Login: `admin` / Password: `admin`)
    * **Prometheus** : `http://localhost:9090`

4. **Tableaux de bord**
    * Dans Grafana, allez dans **Dashboards > New > Import**.
    * Utilisez l'ID `14159` (Supabase Dashboard by Supabase) ou importez le JSON depuis le dépôt officiel.
