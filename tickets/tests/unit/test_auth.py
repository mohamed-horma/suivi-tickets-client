from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from tickets.models import User


class AuthenticationTest(TestCase):
    """INFRA-04 — Tests du système d'authentification JWT.

    Couvre : connexion valide/invalide, renouvellement, déconnexion,
    routes protégées, et stockage sécurisé des mots de passe.
    """

    def setUp(self) -> None:
        self.api = APIClient()
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPass123!",
            role=User.Role.CLIENT,
        )
        self.login_url = "/api/auth/login/"
        self.refresh_url = "/api/auth/refresh/"
        self.logout_url = "/api/auth/logout/"

    # ── Connexion ─────────────────────────────────────────────────────────

    def test_login__valid_credentials__returns_access_and_refresh_tokens(self) -> None:
        # GIVEN: un utilisateur avec des identifiants valides

        # WHEN: il envoie ses identifiants à l'endpoint de connexion
        response = self.api.post(
            self.login_url,
            {"email": "user@example.com", "password": "StrongPass123!"},
            format="json",
        )

        # THEN: il reçoit un access token et un refresh token
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login__invalid_password__returns_401(self) -> None:
        # GIVEN: un mot de passe incorrect pour un email existant

        # WHEN: il tente de se connecter
        response = self.api.post(
            self.login_url,
            {"email": "user@example.com", "password": "mauvaismdp"},
            format="json",
        )

        # THEN: il reçoit HTTP 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login__unknown_email__returns_401(self) -> None:
        # GIVEN: un email qui n'existe pas en base

        # WHEN: il tente de se connecter
        response = self.api.post(
            self.login_url,
            {"email": "inconnu@example.com", "password": "nimporte"},
            format="json",
        )

        # THEN: il reçoit HTTP 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Renouvellement ────────────────────────────────────────────────────

    def test_refresh__valid_token__returns_new_access_token(self) -> None:
        # GIVEN: un utilisateur connecté avec un refresh token valide
        login = self.api.post(
            self.login_url,
            {"email": "user@example.com", "password": "StrongPass123!"},
            format="json",
        )
        refresh_token = login.data["refresh"]

        # WHEN: il envoie son refresh token pour renouveler l'accès
        response = self.api.post(
            self.refresh_url,
            {"refresh": refresh_token},
            format="json",
        )

        # THEN: il reçoit un nouveau access token
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh__invalid_token__returns_401(self) -> None:
        # GIVEN: un token refresh falsifié ou invalide

        # WHEN: il tente de renouveler avec ce token
        response = self.api.post(
            self.refresh_url,
            {"refresh": "token.invalide.falsifie"},
            format="json",
        )

        # THEN: il reçoit HTTP 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Déconnexion ───────────────────────────────────────────────────────

    def test_logout__valid_token__blacklists_refresh_token(self) -> None:
        # GIVEN: un utilisateur connecté avec un refresh token valide
        login = self.api.post(
            self.login_url,
            {"email": "user@example.com", "password": "StrongPass123!"},
            format="json",
        )
        refresh_token = login.data["refresh"]

        # WHEN: il se déconnecte en envoyant son refresh token
        logout = self.api.post(
            self.logout_url,
            {"refresh": refresh_token},
            format="json",
        )

        # THEN: la déconnexion réussit
        self.assertEqual(logout.status_code, status.HTTP_200_OK)

        # AND: tenter de réutiliser le refresh token retourne HTTP 401
        reuse = self.api.post(
            self.refresh_url,
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(reuse.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Routes protégées ──────────────────────────────────────────────────

    def test_protected_route__no_token__returns_401(self) -> None:
        # GIVEN: aucun token dans la requête

        # WHEN: on appelle une route protégée sans s'authentifier
        response = self.api.get("/api/projects/")

        # THEN: HTTP 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_route__valid_token__returns_200(self) -> None:
        # GIVEN: un utilisateur connecté avec un access token valide
        login = self.api.post(
            self.login_url,
            {"email": "user@example.com", "password": "StrongPass123!"},
            format="json",
        )
        access_token = login.data["access"]

        # WHEN: il appelle une route protégée avec son access token
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.api.get("/api/projects/")

        # THEN: HTTP 200
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ── Sécurité des mots de passe ────────────────────────────────────────

    def test_password__never_stored_in_plain_text(self) -> None:
        # GIVEN: un utilisateur créé avec un mot de passe en clair

        # WHEN: on inspecte le champ password stocké en base

        # THEN: le mot de passe est haché — jamais stocké en clair
        self.assertNotEqual(self.user.password, "StrongPass123!")
        self.assertTrue(self.user.check_password("StrongPass123!"))
