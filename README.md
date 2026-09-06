# Suivi Tickets Client

API REST de suivi de tickets clients pour des projets logiciels : les clients déclarent des
bugs, des suggestions et des demandes d'évolution sur les lots auxquels ils sont abonnés,
l'équipe projet les traite et les suit jusqu'à la résolution.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.17-A30000)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)

---

## Sommaire

- [Le projet](#le-projet)
- [Stack technique](#stack-technique)
- [Démarrage rapide](#démarrage-rapide)
- [Architecture](#architecture)
- [Modèle de données](#modèle-de-données)
- [API REST](#api-rest)
- [Authentification JWT](#authentification-jwt)
- [Tests](#tests)
- [Configuration](#configuration)
- [Commandes utiles](#commandes-utiles)
- [État d'avancement](#état-davancement)

---

## Le projet

Une agence qui livre des projets logiciels a besoin d'un canal structuré pour recueillir les
retours de ses clients. Les échanges par email se perdent, rien n'est traçable, et personne ne
sait quel retour porte sur quelle partie du produit.

Ce backend répond à ce besoin avec un modèle hiérarchique — un **projet** se découpe en
**phases**, chaque phase en **lots** livrables, et chaque retour client est un **ticket**
rattaché à un lot précis. Chaque ticket reçoit une référence unique (`#BP-2026-00001`) et son
contenu devient immuable dès la création : ce que le client a déclaré ne peut plus être
réécrit après coup, seul le statut évolue.

**Fonctionnalités implémentées**

- Authentification par email et mot de passe, sessions JWT renouvelables et révocables
- Gestion des projets, phases et lots via une API REST complète
- Création de tickets avec validation des règles métier et génération automatique de référence
- Immuabilité du contenu des tickets et des commentaires, appliquée côté admin et côté API
- Interface d'administration Django pour l'ensemble des objets métier
- Environnement de développement reproductible, démarrable en une commande

---

## Stack technique

| Composant | Choix | Pourquoi |
|---|---|---|
| Langage | Python 3.13 | Typage natif (`str \| None`, génériques) utilisé dans tout le code |
| Framework | Django 5.2 | ORM, migrations et admin prêts à l'emploi |
| API | Django REST Framework 3.17 | ViewSets, serializers, pagination |
| Authentification | `djangorestframework-simplejwt` 5.5 | JWT avec rotation et blacklist des refresh tokens |
| Base de données | PostgreSQL 17 | Contraintes relationnelles, UUID natifs |
| Conteneurisation | Docker Compose | Même environnement sur toutes les machines |

---

## Démarrage rapide

**Prérequis :** Docker et Docker Compose.

```bash
# 1. Cloner le dépôt
git clone git@github.com:mohamed-horma/suivi-tickets-client.git
cd suivi-tickets-client

# 2. Créer le fichier d'environnement
cp .env.example .env
# Éditer .env — au minimum DJANGO_SECRET_KEY et POSTGRES_PASSWORD

# 3. Démarrer (PostgreSQL + Django + migrations automatiques)
docker compose up -d

# 4. Créer un compte administrateur
docker exec -it suivi-tickets-backend python manage.py createsuperuser
```

L'application est alors disponible :

- Admin Django — http://localhost:8000/admin/
- Racine de l'API — http://localhost:8000/api/

Django attend que PostgreSQL soit réellement prêt (healthcheck `pg_isready`) avant de démarrer,
et applique les migrations au lancement : la commande de l'étape 3 suffit sur une machine vierge.

---

## Architecture

Le code suit le découpage **Selectors / Services / Thin Views** : les vues orchestrent, les
services portent les écritures et les règles métier, les selectors portent les lectures.

```
Requête HTTP
   │
   ▼
View ──────────► orchestre uniquement, aucune logique métier
   │
   ├──► Serializer ──► validation des données d'entrée et de sortie
   │
   ├──► Service ─────► écriture, règles métier, @transaction.atomic
   │
   └──► Selector ────► lecture, select_related, aucune logique
```

Deux conséquences concrètes de ce découpage :

- **Les règles métier sont testables sans HTTP.** `_validate_ticket_content()` est une fonction
  pure, sans ORM ni effet de bord — les tests unitaires l'exercent directement.
- **Les requêtes N+1 sont traitées à la source.** Chaque selector déclare ses `select_related`,
  donc lister 100 tickets avec leur lot, leur phase, leur projet et leur auteur reste une
  seule requête SQL.

```
suivi-tickets-client/
├── config/
│   ├── settings.py          # Configuration, lue depuis l'environnement
│   └── urls.py              # Routage : /admin/, /api/, /api/auth/
├── tickets/
│   ├── models.py            # 12 modèles métier
│   ├── admin.py             # Admin Django, champs immuables en readonly
│   ├── serializers.py       # Validation entrée / sortie
│   ├── selectors.py         # Lectures
│   ├── services.py          # Écritures et règles métier
│   ├── views.py             # ViewSets DRF
│   ├── exceptions.py        # Exceptions métier
│   ├── migrations/          # Schéma versionné
│   └── tests/
│       ├── unit/            # 16 tests — services et authentification
│       └── integration/     # 4 tests — immuabilité des tickets via l'API
├── compose.yaml
├── Dockerfile
└── .env.example
```

---

## Modèle de données

```
Projet
  └── Phase
        └── Lot
              └── Ticket
                    ├── Comment
                    ├── Screenshot
                    └── Notification

User ──(Assignment)──► Projet      un client est assigné à des projets
User ──(Abonnment)───► Lot         un client s'abonne aux lots qui l'intéressent
```

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

Toutes les clés primaires sont des `UUIDField`, pour ne pas exposer de compteur séquentiel
dans les URLs de l'API.

### Champs d'un ticket

| Champ | Type | Règle |
|---|---|---|
| `reference` | `CharField` | Auto-générée `#BP-AAAA-NNNNN` — immuable |
| `type` | `ChoiceField` | `bug` / `suggestion` / `new_request` — immuable |
| `what_tested` | `TextField` | Ce qui a été testé — immuable |
| `observed_result` | `TextField` | Résultat observé — immuable |
| `expected_result` | `TextField` | Résultat attendu — immuable |
| `note` | `TextField` | Commentaire optionnel — seul champ de contenu modifiable |
| `status` | `ChoiceField` | 9 états — modifiable dans l'admin, piloté par le serveur côté API |
| `created_by` | `FK User` | Auteur — immuable |
| `created_at` | `DateTime` | Date de création — automatique |

### Immuabilité

Ce qu'un client a déclaré dans un ticket ne peut plus être réécrit après coup : `type`,
`what_tested`, `observed_result` et `expected_result` sont figés à la création, tout comme le
texte des commentaires. Seul `note` reste modifiable.

La règle est appliquée sur les deux chemins d'écriture, pour qu'aucun ne la contourne :

- **Admin** — `readonly_fields` dans `TicketAdmin` et `CommentAdmin`
- **API** — `read_only_fields` dans `TicketSerializer`, couvert par les tests d'intégration

`reference`, `created_by` et `status` sont également en lecture seule côté API : ils sont
déterminés par le serveur, jamais par le client.

---

## API REST

Toutes les routes `/api/` exigent un access token JWT valide (`IsAuthenticated`).

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/api/` | Index DRF — liste des routes |
| `GET` `POST` | `/api/projects/` | Liste / crée un projet |
| `GET` `PUT` `PATCH` `DELETE` | `/api/projects/{id}/` | Détail / modifie / supprime |
| `GET` `POST` | `/api/phases/` | Liste / crée une phase |
| `GET` `PUT` `PATCH` `DELETE` | `/api/phases/{id}/` | Détail / modifie / supprime |
| `GET` `POST` | `/api/lots/` | Liste / crée un lot |
| `GET` `PUT` `PATCH` `DELETE` | `/api/lots/{id}/` | Détail / modifie / supprime |
| `GET` `POST` | `/api/tickets/` | Liste / crée un ticket |
| `GET` `PATCH` `DELETE` | `/api/tickets/{id}/` | Détail / modifie la note / supprime |

### Pagination

Toutes les listes sont paginées, 10 résultats par page.

```json
{
  "count": 42,
  "next": "http://localhost:8000/api/tickets/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

### Créer un ticket

```http
POST /api/tickets/
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "lot": "uuid-du-lot",
  "type": "bug",
  "what_tested": "Description de ce qui a été testé (20 caractères minimum)",
  "observed_result": "Description du résultat observé (20 caractères minimum)",
  "expected_result": "Description du résultat attendu (20 caractères minimum)",
  "note": "Note optionnelle (10 caractères minimum si fournie)"
}
```

Réponse `201 Created` — la référence et l'auteur sont déterminés par le serveur, jamais par
le client :

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

Réponse `400 Bad Request` si une règle métier est violée :

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

La création passe par `create_ticket()`, décoré `@transaction.atomic` : si la génération de la
référence ou l'insertion échoue, rien n'est écrit en base.

---

## Authentification JWT

L'utilisateur se connecte avec son email et son mot de passe, et reçoit deux tokens signés.
L'access token est court, le refresh token est long et révocable.

```
POST /api/auth/login/
        │
        ▼
  access_token  (60 min)  ──► à envoyer dans chaque requête API
  refresh_token (7 jours) ──► à conserver, sert uniquement à renouveler

        │ access_token expiré (HTTP 401)
        ▼
POST /api/auth/refresh/
        │
        ▼
  nouvel access_token  ──► reprendre les appels API
  nouveau refresh_token ─► l'ancien est blacklisté automatiquement

        │ déconnexion volontaire
        ▼
POST /api/auth/logout/
        │
        ▼
  refresh_token blacklisté ──► toute tentative de refresh → HTTP 401
```

| Méthode | URL | Description | Token requis |
|---|---|---|---|
| `POST` | `/api/auth/login/` | Connexion — retourne access + refresh | Non |
| `POST` | `/api/auth/refresh/` | Renouvelle l'access token | Refresh token |
| `POST` | `/api/auth/logout/` | Déconnexion — blackliste le refresh | Refresh token |

**1. Connexion**

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "monmotdepasse"}'
```

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Identifiants invalides → `401 Unauthorized` :

```json
{ "detail": "No active account found with the given credentials" }
```

**2. Appeler une route protégée**

```bash
curl http://localhost:8000/api/projects/ \
  -H "Authorization: Bearer <access_token>"
```

Sans token, ou avec un token expiré → `401 Unauthorized` :

```json
{ "detail": "Authentication credentials were not provided." }
```

**3. Renouveler l'access token**

```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

```json
{
  "access": "eyJ...(nouveau)",
  "refresh": "eyJ...(nouveau — l'ancien est blacklisté)"
}
```

**4. Déconnexion**

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

Réponse `200 OK` — le refresh token est blacklisté, toute réutilisation retourne `401`.

### Paramètres

| Paramètre | Valeur | Raison |
|---|---|---|
| `ACCESS_TOKEN_LIFETIME` | 60 minutes | Durée courte — un token volé expire vite |
| `REFRESH_TOKEN_LIFETIME` | 7 jours | L'utilisateur reste connecté une semaine |
| `ROTATE_REFRESH_TOKENS` | `True` | Chaque refresh génère un nouveau refresh token |
| `BLACKLIST_AFTER_ROTATION` | `True` | L'ancien refresh token est révoqué automatiquement |

### Mots de passe

Les mots de passe sont hachés avec **PBKDF2-SHA256**, l'algorithme par défaut de Django, et ne
sont jamais stockés en clair — même en cas de fuite de la base, ils restent inexploitables.

```python
# Ce que Django stocke en base
"pbkdf2_sha256$870000$sel_aléatoire$hash_base64"
```

---

## Tests

20 tests, tous verts.

```bash
# Tous les tests, en parallèle
docker exec suivi-tickets-backend python manage.py test --parallel

# Règles métier des services uniquement
docker exec suivi-tickets-backend python manage.py test tickets.tests.unit.test_services

# Authentification uniquement
docker exec suivi-tickets-backend python manage.py test tickets.tests.unit.test_auth

# Tests d'intégration de l'API
docker exec suivi-tickets-backend python manage.py test tickets.tests.integration
```

```
tickets/tests/
├── unit/
│   ├── test_services.py     # 7 tests — création de ticket, règles métier, référence
│   └── test_auth.py         # 9 tests — login, refresh, logout, routes protégées
└── integration/
    └── test_ticket_api.py   # 4 tests — immuabilité du contenu via l'API
```

Les tests suivent la structure **Given / When / Then** et sont nommés selon le schéma
`test_<sujet>__<condition>__<résultat attendu>`, par exemple
`test_protected_route__valid_token__returns_200`.

---

## Configuration

Toutes les variables sont documentées dans `.env.example`, qui est versionné. Le fichier
`.env` ne l'est jamais : aucun secret ne se trouve dans le dépôt.

| Variable | Description | Valeur par défaut |
|---|---|---|
| `DJANGO_SECRET_KEY` | Clé de signature Django | à définir |
| `DJANGO_DEBUG` | Mode debug — `False` en production | `True` |
| `DJANGO_ALLOWED_HOSTS` | Hôtes autorisés, séparés par des virgules | `localhost,127.0.0.1` |
| `POSTGRES_DB` | Nom de la base | `suivi_tickets_db` |
| `POSTGRES_USER` | Utilisateur PostgreSQL | `suivi_tickets` |
| `POSTGRES_PASSWORD` | Mot de passe | à définir |
| `POSTGRES_HOST` | Hôte de la base | `suivi-tickets-database` en Docker, `localhost` en local |
| `POSTGRES_PORT` | Port PostgreSQL | `5432` |

Générer une clé de signature :

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## Commandes utiles

```bash
# Migrations — nécessaire seulement après modification des modèles
docker exec suivi-tickets-backend python manage.py makemigrations
docker exec suivi-tickets-backend python manage.py migrate

# Shell Django interactif
docker exec -it suivi-tickets-backend python manage.py shell

# Rebuilder après modification de requirements.txt
docker compose build django

# Recharger les variables .env
docker compose down && docker compose up -d

# Repartir d'une base vierge (supprime les données)
docker compose down -v && docker compose up -d
```

---

## État d'avancement

| Domaine | État |
|---|---|
| Environnement Docker reproductible, démarrage en une commande | ✅ |
| Configuration sensible sortie du code, `.env.example` complet | ✅ |
| Modèle de données — 12 modèles, relations, migrations versionnées | ✅ |
| Admin Django sur tous les objets, champs immuables protégés | ✅ |
| API REST — projets, phases, lots, tickets, pagination | ✅ |
| Règles métier isolées dans les services, référence auto-générée | ✅ |
| Authentification JWT — login, refresh, logout avec blacklist | ✅ |
| Tests — services, authentification, immuabilité de l'API | ✅ 20 tests |
| Contrôle d'accès par rôle | 🚧 Selectors filtrés par utilisateur écrits, à brancher dans les vues |
| Tests d'intégration — couverture complète des endpoints | 🚧 Immuabilité couverte, reste à étendre |
| Notifications email et Slack | 📋 Modèles en place, envoi à implémenter |
| Synchronisation Notion | 📋 Modèles `SyncJob` / `SyncLog` en place, sync à implémenter |
