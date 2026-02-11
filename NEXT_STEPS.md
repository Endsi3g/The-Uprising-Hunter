# 🚀 Next Steps : Système de Prospection Automatisé

Félicitations ! Le cœur du système (Core, Enrichment, Scoring, AI) est en place. Voici comment transformer ce prototype en machine de guerre opérationnelle.

## 🛠 1. Installation & Setup (Nouvel Emplacement)

Puisque vous avez déplacé le projet, il est recommandé de recréer l'environnement virtuel pour éviter les conflits de chemins.

```bash
# Supprimer l'ancien venv (si existe)
Remove-Item -Recurse -Force venv

# Créer un nouveau venv
python -m venv venv

# Activer
.\venv\Scripts\Activate

# Installer les dépendances
pip install -r requirements.txt
```

## 🔗 2. Connecter les "Vraies" APIs

Actuellement, le système utilise des mocks (données simulées). Pour passer en production :

### Sourcing (Apollo/ZoomInfo)
1. Obtenez une clé API Apollo.io.
2. Modifiez `src/enrichment/client.py` pour remplacer `MockApolloClient` par une vraie implémentation `Requests`.
3. Stockez la clé API dans un fichier `.env` (ne pas commiter !).

### AI Generation (OpenAI/Anthropic)
1. Installez le client : `pip install openai`.
2. Dans `src/ai_engine/generator.py`, remplacez la logique "mock" par un appel réel :
   ```python
   client = OpenAI(api_key="sk-...")
   response = client.chat.completions.create(...)
   ```

## 🤖 3. Automatisation & Base de Données

### Base de Données
Le système utilise des objets en mémoire. Pour la persistance :
- Installez SQLite ou PostgreSQL.
- Utilisez **SQLAlchemy** (déjà dans requirements) pour mapper les modèles `src/core/models.py` vers des tables DB.

### Scheduling
Pour tourner tous les jours automatiquement :
- Créez une tâche Cron ou Windows Task Scheduler qui lance `python run_system.py`.
- Ou déployez sur un service Cloud (Render, Railway, AWS Lambda).

## 📦 4. Gestion du Code (GitHub)

Le dépôt est initialisé localement. Pour le pousser sur GitHub :

1. Créez un nouveau dépôt **vide** sur [GitHub.com](https://github.com/new).
2. Exécutez les commandes suivantes :

```bash
git remote add origin https://github.com/VOTRE_USER/ProspectionApp.git
git branch -M main
git push -u origin main
```

## 📈 Roadmap

- [ ] **J+1** : Brancher la vraie API OpenAI pour générer les emails.
- [ ] **J+2** : Configurer la base de données SQLite.
- [ ] **J+5** : Tester l'envoi réel d'emails (via SMTP ou Gmail API).
