from django.test import TestCase

from tickets.exceptions import TicketValidationError
from tickets.models import Lot, Phase, Project, User
from tickets.services import create_ticket


class CreateTicketTest(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="client@example.com",
            password="pass123",
            role=User.Role.CLIENT,
        )
        project = Project.objects.create(
            name="Projet Test",
            slack_channel="https://slack.example.com/channel",
            notion_page_url="https://notion.example.com/page",
        )
        phase = Phase.objects.create(project=project, name="Phase 1")
        self.lot = Lot.objects.create(phase=phase, name="Lot 1")

    # ── Création valide ───────────────────────────────────────────────────

    def test_create_ticket__valid_data__returns_ticket_with_reference(self) -> None:
        # GIVEN: un lot valide et des données conformes aux règles métier

        # WHEN: create_ticket est appelé avec des données valides
        ticket = create_ticket(
            lot=self.lot,
            created_by=self.user,
            ticket_type="bug",
            what_tested="Description détaillée de ce qui a été testé dans l'application",
            observed_result="Description détaillée du résultat observé lors du test effectué",
            expected_result="Description détaillée du résultat attendu lors du test effectué",
        )

        # THEN: le ticket est persisté avec une référence au format #BP-AAAA-NNNNN
        self.assertIsNotNone(ticket.pk)
        self.assertRegex(ticket.reference, r"^#BP-\d{4}-\d{5}$")
        self.assertEqual(ticket.lot, self.lot)
        self.assertEqual(ticket.created_by, self.user)

    def test_create_ticket__increments_counter_per_year(self) -> None:
        # GIVEN: un premier ticket déjà créé dans l'année
        first = create_ticket(
            lot=self.lot,
            created_by=self.user,
            ticket_type="bug",
            what_tested="Description détaillée de ce qui a été testé dans l'application",
            observed_result="Description détaillée du résultat observé lors du test effectué",
            expected_result="Description détaillée du résultat attendu lors du test effectué",
        )

        # WHEN: un second ticket est créé dans la même année
        second = create_ticket(
            lot=self.lot,
            created_by=self.user,
            ticket_type="suggestion",
            what_tested="Description détaillée de ce qui a été testé dans l'application",
            observed_result="Description détaillée du résultat observé lors du test effectué",
            expected_result="Description détaillée du résultat attendu lors du test effectué",
        )

        # THEN: les deux références sont différentes et incrémentées
        self.assertNotEqual(first.reference, second.reference)
        self.assertIn("-00001", first.reference)
        self.assertIn("-00002", second.reference)

    # ── Violations des règles métier ──────────────────────────────────────

    def test_create_ticket__what_tested_too_short__raises_validation_error(self) -> None:
        # GIVEN: what_tested inférieur à 20 caractères

        # WHEN / THEN: TicketValidationError est levée
        with self.assertRaises(TicketValidationError):
            create_ticket(
                lot=self.lot,
                created_by=self.user,
                ticket_type="bug",
                what_tested="trop court",
                observed_result="Description détaillée du résultat observé lors du test effectué",
                expected_result="Description détaillée du résultat attendu lors du test effectué",
            )

    def test_create_ticket__observed_result_too_short__raises_validation_error(self) -> None:
        # GIVEN: observed_result inférieur à 20 caractères

        # WHEN / THEN: TicketValidationError est levée
        with self.assertRaises(TicketValidationError):
            create_ticket(
                lot=self.lot,
                created_by=self.user,
                ticket_type="bug",
                what_tested="Description détaillée de ce qui a été testé dans l'application",
                observed_result="trop court",
                expected_result="Description détaillée du résultat attendu lors du test effectué",
            )

    def test_create_ticket__expected_result_too_short__raises_validation_error(self) -> None:
        # GIVEN: expected_result inférieur à 20 caractères

        # WHEN / THEN: TicketValidationError est levée
        with self.assertRaises(TicketValidationError):
            create_ticket(
                lot=self.lot,
                created_by=self.user,
                ticket_type="bug",
                what_tested="Description détaillée de ce qui a été testé dans l'application",
                observed_result="Description détaillée du résultat observé lors du test effectué",
                expected_result="court",
            )

    def test_create_ticket__note_too_short__raises_validation_error(self) -> None:
        # GIVEN: note fournie mais inférieure à 10 caractères

        # WHEN / THEN: TicketValidationError est levée
        with self.assertRaises(TicketValidationError):
            create_ticket(
                lot=self.lot,
                created_by=self.user,
                ticket_type="suggestion",
                what_tested="Description détaillée de ce qui a été testé dans l'application",
                observed_result="Description détaillée du résultat observé lors du test effectué",
                expected_result="Description détaillée du résultat attendu lors du test effectué",
                note="court",
            )

    def test_create_ticket__note_none__creates_ticket_without_note(self) -> None:
        # GIVEN: note non fournie (optionnelle)

        # WHEN: create_ticket est appelé sans note
        ticket = create_ticket(
            lot=self.lot,
            created_by=self.user,
            ticket_type="new_request",
            what_tested="Description détaillée de ce qui a été testé dans l'application",
            observed_result="Description détaillée du résultat observé lors du test effectué",
            expected_result="Description détaillée du résultat attendu lors du test effectué",
            note=None,
        )

        # THEN: le ticket est créé sans note
        self.assertIsNone(ticket.note)
