from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from tickets.models import Lot, Phase, Project, Ticket, User
from tickets.services import create_ticket


class TicketImmutabilityAPITest(TestCase):
    """Immuabilité du contenu d'un ticket au travers de l'API.

    Le contenu déclaré par le client ne doit plus pouvoir être réécrit une fois
    le ticket créé : ni par PATCH, ni par PUT.
    """

    def setUp(self) -> None:
        self.api = APIClient()
        self.user = User.objects.create_user(
            email="client@example.com",
            password="StrongPass123!",
            role=User.Role.CLIENT,
        )
        project = Project.objects.create(
            name="Projet de test",
            slack_channel="https://slack.example.com/canal",
            notion_page_url="https://notion.example.com/page",
        )
        phase = Phase.objects.create(project=project, name="Phase 1")
        self.lot = Lot.objects.create(phase=phase, name="Lot 1")
        self.ticket = create_ticket(
            lot=self.lot,
            created_by=self.user,
            ticket_type=Ticket.Type.BUG,
            what_tested="Connexion avec un email valide et un mot de passe correct",
            observed_result="La page reste bloquée sur le formulaire de connexion",
            expected_result="L'utilisateur est redirigé vers son tableau de bord",
        )
        self.detail_url = f"/api/tickets/{self.ticket.id}/"
        self.api.force_authenticate(user=self.user)

    def test_patch_ticket__content_fields__are_ignored(self) -> None:
        # GIVEN: un ticket existant, dont le contenu est immuable

        # WHEN: un utilisateur authentifié tente de réécrire son contenu
        response = self.api.patch(
            self.detail_url,
            {
                "what_tested": "Contenu réécrit après coup par le client",
                "observed_result": "Résultat observé réécrit après coup",
                "expected_result": "Résultat attendu réécrit après coup",
                "type": Ticket.Type.SUGGESTION,
            },
            format="json",
        )

        # THEN: la requête aboutit mais aucun champ de contenu n'a changé
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(
            self.ticket.what_tested,
            "Connexion avec un email valide et un mot de passe correct",
        )
        self.assertEqual(
            self.ticket.observed_result,
            "La page reste bloquée sur le formulaire de connexion",
        )
        self.assertEqual(
            self.ticket.expected_result,
            "L'utilisateur est redirigé vers son tableau de bord",
        )
        self.assertEqual(self.ticket.type, Ticket.Type.BUG)

    def test_patch_ticket__reference_and_status__are_ignored(self) -> None:
        # GIVEN: un ticket dont la référence et le statut sont pilotés par le serveur
        original_reference = self.ticket.reference

        # WHEN: un utilisateur tente de les forcer
        response = self.api.patch(
            self.detail_url,
            {"reference": "#BP-1999-00001", "status": Ticket.Status.VALIDATED},
            format="json",
        )

        # THEN: ni la référence ni le statut ne sont modifiés
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.reference, original_reference)
        self.assertEqual(self.ticket.status, Ticket.Status.SUBMITTED)

    def test_patch_ticket__note__is_updated(self) -> None:
        # GIVEN: un ticket sans note

        # WHEN: une note est ajoutée
        response = self.api.patch(
            self.detail_url,
            {"note": "Précision ajoutée par le client"},
            format="json",
        )

        # THEN: la note est bien enregistrée — seul champ de contenu modifiable
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.note, "Précision ajoutée par le client")

    def test_ticket_detail__without_token__returns_401(self) -> None:
        # GIVEN: un client non authentifié
        anonymous = APIClient()

        # WHEN: il demande le détail d'un ticket
        response = anonymous.get(self.detail_url)

        # THEN: il reçoit HTTP 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
