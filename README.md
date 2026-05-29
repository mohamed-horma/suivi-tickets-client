# AppliTicket

Backend Django pour la gestion de tickets clients (feedbacks, bugs, suggestions) sur des projets logiciels.

---

## INFRA-01 — Environnement de développement

### Objectif
Environnement de développement local reproductible, démarrable en une seule commande depuis n'importe quelle machine de l'équipe.

### Prérequis
- Docker et Docker Compose
- Git

### Démarrage rapide

```bash
# 1. Cloner le dépôt
git clone git@github.com:mohamed-horma/AppliTicket.git
cd AppliTicket

# 2. Créer le fichier d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# 3. Démarrer (DB + Django + migrations automatiques)
docker compose up -d

# 4. (Optionnel) Créer un compte admin
docker exec -it appliTicket-backend python manage.py createsuperuser

# 5. Ouvrir l'application
# Admin : http://localhost:8000/admin/
```

### Variables d'environnement

Toutes les variables sont documentées dans `.env.example` — ce fichier est commité, `.env` ne l'est jamais.

| Variable | Description |
|---|---|
| `POSTGRES_DB` | Nom de la base de données |
| `POSTGRES_USER` | Utilisateur PostgreSQL |
| `POSTGRES_PASSWORD` | Mot de passe |
| `POSTGRES_HOST` | `appliTicket-database` en Docker, `localhost` en local |
| `POSTGRES_PORT` | `5432` |

### Commandes utiles

```bash
# Appliquer les migrations (dans le conteneur)
docker exec appliTicket-backend python manage.py migrate

# Shell Django
docker exec -it appliTicket-backend python manage.py shell

# Rebuilder après modif requirements.txt
docker compose build django

# Recharger les variables .env
docker compose down && docker compose up -d
```

### Critères d'évaluation

| # | Critère | Statut |
|---|---|---|
| 1 | Démarre en une commande : `docker compose up -d` | ✅ |
| 2 | Variables sensibles séparées du code | ✅ |
| 3 | `.env.example` liste toutes les variables | ✅ |
| 4 | Application accessible sur http://localhost:8000 | ✅ |
| 5 | Migrations appliquées automatiquement au démarrage | ✅ |
| 6 | Guide de démarrage en moins de 10 étapes | ✅ (5 étapes) |
