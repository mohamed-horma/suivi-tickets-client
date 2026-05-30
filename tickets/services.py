from django.db import transaction
from django.utils import timezone

from .exceptions import TicketValidationError
from .models import Lot, Ticket, User
from .selectors import get_ticket_count_for_year


def _build_ticket_reference(year: int, count: int) -> str:
    return f"#BP-{year}-{count:05d}"


def _validate_ticket_content(
    what_tested: str,
    observed_result: str,
    expected_result: str,
    note: str | None,
) -> None:
    """
    Valide les règles métier sur le contenu d'un ticket.
    Fonction pure — aucun effet de bord, aucune dépendance ORM.

    Raises:
        TicketValidationError: si une règle métier est violée.
    """
    if len(what_tested) < 20:
        raise TicketValidationError(
            "what_tested doit contenir au moins 20 caractères."
        )
    if len(observed_result) < 20:
        raise TicketValidationError(
            "observed_result doit contenir au moins 20 caractères."
        )
    if len(expected_result) < 20:
        raise TicketValidationError(
            "expected_result doit contenir au moins 20 caractères."
        )
    if note is not None and len(note) < 10:
        raise TicketValidationError(
            "note doit contenir au moins 10 caractères."
        )


@transaction.atomic
def create_ticket(
    *,
    lot: Lot,
    created_by: User | None,
    ticket_type: Ticket.Type,
    what_tested: str,
    observed_result: str,
    expected_result: str,
    note: str | None = None,
) -> Ticket:
    """
    Crée un nouveau ticket avec une référence unique #BP-AAAA-NNNNN.

    Orchestre la validation du contenu et la persistance.
    La référence est auto-incrémentée par année dans une transaction atomique
    pour protéger la séquence lecture-écriture du compteur.

    Raises:
        TicketValidationError: si une règle métier est violée.
    """
    _validate_ticket_content(what_tested, observed_result, expected_result, note)

    year = timezone.now().year
    count = get_ticket_count_for_year(year) + 1

    return Ticket.objects.create(
        lot=lot,
        created_by=created_by,
        reference=_build_ticket_reference(year, count),
        type=ticket_type,
        what_tested=what_tested,
        observed_result=observed_result,
        expected_result=expected_result,
        note=note,
    )
