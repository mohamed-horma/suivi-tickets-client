# AppliTicket

Backend Django REST API pour la gestion de tickets clients (bugs, suggestions, nouvelles demandes) sur des projets logiciels.

---

## Sommaire

- [INFRA-01 — Environnement de développement](#infra-01--environnement-de-développement)
- [INFRA-02 — Modèle de données](#infra-02--modèle-de-données)
- [INFRA-03 — Django REST Framework](#infra-03--django-rest-framework)

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
# API   : http://localhost:8000/api/
```

### Variables d'environnement

Toutes les variables sont documentées dans `.env.example` — ce fichier est commité, `.env` ne l'est jamais.

| Variable | Description | Valeur Docker | Valeur locale |
|---|---|---|---|
| `POSTGRES_DB` | Nom de la base | `appliTicket_DB` | `appliTicket_DB` |
| `POSTGRES_USER` | Utilisateur PostgreSQL | `suivi_tickets` | `suivi_tickets` |
| `POSTGRES_PASSWORD` | Mot de passe | à définir | à définir |
| `POSTGRES_HOST` | Hôte de la base | `appliTicket-database` | `localhost` |
| `POSTGRES_PORT` | Port PostgreSQL | `5432` | `5432` |

### Commandes utiles

```bash
# Migrations
docker exec appliTicket-backend python manage.py makemigrations
docker exec appliTicket-backend python manage.py migrate

# Shell Django interactif
docker exec -it appliTicket-backend python manage.py shell

# Rebuilder après modification de requirements.txt
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

### Hiérarchie des objets

```
Projet
  └── Phase
        └── Lot
              └── Ticket
                    ├── Comment
                    ├── Screenshot
                    └── Notification

User ──(Assignment)──► Projet
User ──(Abonnment)───► Lot
```

### Modèles

| Modèle | Rôle |
|---|---|
| `User` | Utilisateur avec rôle `admin` ou `client`, authentification par email |
| `Project` | Projet logiciel suivi dans l'application |
| `Phase` | Regroupement de lots dans un projet |
| `Lot` | Conteneur de tickets dans une phase |
| `Assignment` | Association entre un client et un projet |
| `Abonnment` | Abonnement d'un client aux notifications d'un lot |
| `Ticket` | Entité centrale — référence unique `#BP-AAAA-NNNNN` |
| `Comment` | Commentaire immuable attaché à un ticket |
| `Screenshot` | Capture d'écran attachée à un ticket |
| `Notification` | Notification email ou Slack envoyée pour un ticket |
| `SyncJob` | Job de synchronisation bidirectionnelle avec Notion |
| `SyncLog` | Détail de synchronisation par ticket |

### Champs d'un Ticket

| Champ | Type | Règle |
|---|---|---|
| `reference` | `CharField` | Auto-généré `#BP-AAAA-NNNNN` — immuable |
| `type` | `ChoiceField` | `bug` / `suggestion` / `new_request` — immuable |
| `what_tested` | `TextField` | Ce qui a été testé — immuable |
| `observed_result` | `TextField` | Résultat observé — immuable |
| `expected_result` | `TextField` | Résultat attendu — immuable |
| `note` | `TextField` | Commentaire optionnel — immuable |
| `status` | `ChoiceField` | 9 états (mutable par l'admin) |
| `created_by` | `FK User` | Auteur — immuable |
| `created_at` | `DateTime` | Date de création — automatique |

### Immuabilité des champs

Les champs de contenu d'un ticket et les commentaires sont **immuables après création**.
Enforcement double :
- **Admin** : `readonly_fields` dans `TicketAdmin` et `CommentAdmin`
- **API** : `read_only_fields` dans les serializers + service `update_ticket()` (INFRA-05)

### Générer et appliquer les migrations

```bash
docker exec appliTicket-backend python manage.py makemigrations
docker exec appliTicket-backend python manage.py migrate
```

### Critères d'évaluation

| # | Critère | Statut |
|---|---|---|
| 7 | Tous les objets métier modélisés | ✅ |
| 8 | Ticket contient tous les champs requis | ✅ |
| 9 | Référence `#BP-AAAA-NNNNN` (générée par le service) | ✅ |
| 10 | Relations correctement définies | ✅ |
| 11 | Migrations générées par `makemigrations` | ✅ |
| 12 | Admin affiche tous les objets avec leurs champs | ✅ |
| 13 | Champs immuables protégés (admin + serializers) | ✅ |

---

## INFRA-03 — Django REST Framework

### Objectif
Exposer une API REST complète pour la gestion des projets, phases, lots et tickets. L'architecture suit le pattern **Selectors / Services / Thin Views** défini dans `LLM-python.md`.

### Architecture

```
Request
   │
   ▼
View (orchestre uniquement — aucune logique métier)
   │
   ├──► Serializer  (validation des données d'entrée / sortie)
   │
   ├──► Service     (écriture, règles métier, @transaction.atomic)
   │
   └──► Selector    (lecture, select_related, pas de logique)
```

### Endpoints disponibles

| Méthode | URL | Description | Auth |
|---|---|---|---|
| `GET` | `/api/` | Index DRF (liste des routes) | Non |
| `GET` | `/api/projects/` | Liste tous les projets | Oui |
| `POST` | `/api/projects/` | Crée un projet | Oui |
| `GET` | `/api/projects/{id}/` | Détail d'un projet | Oui |
| `PUT/PATCH` | `/api/projects/{id}/` | Modifie un projet | Oui |
| `DELETE` | `/api/projects/{id}/` | Supprime un projet | Oui |
| `GET` | `/api/phases/` | Liste toutes les phases | Oui |
| `POST` | `/api/phases/` | Crée une phase | Oui |
| `GET` | `/api/phases/{id}/` | Détail d'une phase | Oui |
| `GET` | `/api/lots/` | Liste tous les lots | Oui |
| `POST` | `/api/lots/` | Crée un lot | Oui |
| `GET` | `/api/lots/{id}/` | Détail d'un lot | Oui |
| `GET` | `/api/tickets/` | Liste tous les tickets | Oui |
| `POST` | `/api/tickets/` | Crée un ticket | Oui |
| `GET` | `/api/tickets/{id}/` | Détail d'un ticket | Oui |

> **Note :** Toutes les routes nécessitent une authentification. L'authentification JWT sera ajoutée dans la branche `feature/authentification-jwt`. Pour l'instant, utiliser l'authentification de session via `/admin/`.

### Pagination

Toutes les listes sont paginées (10 résultats par page).

```json
{
  "count": 42,
  "next": "http://localhost:8000/api/tickets/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

### Créer un ticket — payload attendu

```json
POST /api/tickets/
{
  "lot": "uuid-du-lot",
  "type": "bug",
  "what_tested": "Description de ce qui a été testé (20 caractères minimum)",
  "observed_result": "Description du résultat observé (20 caractères minimum)",
  "expected_result": "Description du résultat attendu (20 caractères minimum)",
  "note": "Note optionnelle (10 caractères minimum si fournie)"
}
```

Réponse `201 Created` :
```json
{
  "id": "uuid",
  "lot": "uuid-du-lot",
  "reference": "#BP-2026-00001",
  "created_by": "uuid-user",
  "type": "bug",
  "status": "submitted",
  "what_tested": "...",
  "observed_result": "...",
  "expected_result": "...",
  "note": null,
  "created_at": "2026-05-31T10:00:00Z"
}
```

Réponse `400 Bad Request` si règle métier violée :
```json
{ "detail": "what_tested doit contenir au moins 20 caractères." }
```

### Règles métier — service `create_ticket`

| Champ | Règle |
|---|---|
| `what_tested` | 20 caractères minimum |
| `observed_result` | 20 caractères minimum |
| `expected_result` | 20 caractères minimum |
| `note` | 10 caractères minimum si fournie |
| `reference` | Auto-générée `#BP-{année}-{compteur:05d}` |

### Lancer les tests

```bash
# Tous les tests
docker exec appliTicket-backend python manage.py test

# Tests unitaires uniquement (services)
docker exec appliTicket-backend python manage.py test tickets.tests.unit

# En parallèle (plus rapide)
docker exec appliTicket-backend python manage.py test --parallel
```

### Structure des tests

```
tickets/
  tests/
    unit/
      test_services.py   ← 6 tests sur create_ticket (Given/When/Then)
    integration/
      (à compléter dans les prochaines branches)
```

### Démarrage complet depuis zéro

```bash
# 1. Démarrer l'environnement
docker compose up -d

# 2. Générer et appliquer les migrations
docker exec appliTicket-backend python manage.py makemigrations
docker exec appliTicket-backend python manage.py migrate

# 3. Créer un superuser pour tester via l'admin
docker exec -it appliTicket-backend python manage.py createsuperuser

# 4. Lancer les tests
docker exec appliTicket-backend python manage.py test --parallel
```
