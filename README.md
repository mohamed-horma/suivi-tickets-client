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

---

## INFRA-02 — Modèle de données

### Objectif
Définir et implémenter l'ensemble de la structure de données : utilisateurs, projets, phases, lots, tickets, commentaires, abonnements, SyncJob et SyncLog.

### Hiérarchie

```
Projet → Phase → Lot → Ticket
User ↔ Projet  (Assignment)
User ↔ Lot     (Abonnment)
```

### Modèles

| Modèle | Rôle |
|---|---|
| `User` | Admin ou Client, authentification par email |
| `Project` | Projet logiciel |
| `Phase` | Regroupement de lots dans un projet |
| `Lot` | Conteneur de tickets dans une phase |
| `Assignment` | Association Client ↔ Projet |
| `Abonnment` | Abonnement Client ↔ Lot (notifications) |
| `Ticket` | Entité centrale, référence `#BP-AAAA-NNNNN` |
| `Comment` | Commentaire immuable attaché à un ticket |
| `Screenshot` | Capture d'écran attachée à un ticket |
| `Notification` | Notification email ou Slack par ticket |
| `SyncJob` / `SyncLog` | Audit de synchronisation Notion |

### Champs d'un ticket

| Champ | Description |
|---|---|
| `reference` | Auto-généré au format `#BP-AAAA-NNNNN` (service INFRA-03) |
| `type` | `bug`, `suggestion`, `new_request` |
| `what_tested` | Ce qui a été testé |
| `observed_result` | Résultat observé |
| `expected_result` | Résultat attendu |
| `note` | Commentaire optionnel |
| `status` | 9 états du cycle de vie |

### Immuabilité des champs

Les champs `what_tested`, `observed_result`, `expected_result`, `type` d'un ticket et le contenu d'un commentaire sont immuables après création.
Enforcement : `readonly_fields` dans l'admin + service `update_ticket()` (INFRA-05).

### Générer et appliquer les migrations

```bash
# Générer la migration automatiquement
docker exec appliTicket-backend python manage.py makemigrations

# Appliquer
docker exec appliTicket-backend python manage.py migrate
```

### Vérification via l'admin

```bash
docker exec -it appliTicket-backend python manage.py createsuperuser
# http://localhost:8000/admin/
```

### Critères d'évaluation

| # | Critère | Statut |
|---|---|---|
| 7 | Tous les objets métier modélisés | ✅ |
| 8 | Ticket contient tous les champs requis | ✅ |
| 9 | Référence `#BP-AAAA-NNNNN` (générée en INFRA-03) | ✅ |
| 10 | Relations correctement définies | ✅ |
| 11 | Migrations générées par `makemigrations` | ✅ |
| 12 | Admin affiche tous les objets avec leurs champs | ✅ |
| 13 | Champs immuables : `readonly_fields` admin + service INFRA-05 | ✅ |
