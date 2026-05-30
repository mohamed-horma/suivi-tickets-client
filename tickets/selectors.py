from django.db.models import QuerySet

from .models import Lot, Phase, Project, Ticket, User


def get_ticket_count_for_year(year: int) -> int:
    """Nombre de tickets créés dans l'année donnée. Utilisé pour générer la référence."""
    return Ticket.objects.filter(created_at__year=year).count()


def list_projects() -> QuerySet[Project]:
    """Tous les projets, du plus récent au plus ancien."""
    return Project.objects.order_by("-created_at")


def list_phases() -> QuerySet[Phase]:
    """Toutes les phases avec leur projet associé."""
    return Phase.objects.select_related("project").order_by("-created_at")


def list_lots() -> QuerySet[Lot]:
    """Tous les lots avec leur phase et projet associés."""
    return Lot.objects.select_related("phase__project").order_by("-created_at")


def list_tickets() -> QuerySet[Ticket]:
    """Tous les tickets avec leurs relations chargées en une seule requête."""
    return Ticket.objects.select_related(
        "lot__phase__project", "created_by"
    ).order_by("-created_at")


def list_projects_for_user(user: User) -> QuerySet[Project]:
    """Projets auxquels le client est assigné via Assignment."""
    return Project.objects.filter(
        assignment__user=user
    ).order_by("-created_at")


def list_phases_for_user(user: User) -> QuerySet[Phase]:
    """Phases des projets assignés au client."""
    return Phase.objects.filter(
        project__assignment__user=user
    ).select_related("project").order_by("-created_at")


def list_lots_for_user(user: User) -> QuerySet[Lot]:
    """Lots des projets assignés au client."""
    return Lot.objects.filter(
        phase__project__assignment__user=user
    ).select_related("phase__project").order_by("-created_at")


def list_tickets_for_user(user: User) -> QuerySet[Ticket]:
    """Tickets des lots auxquels le client est abonné via Abonnment."""
    subscribed_lots = user.abonnment.values_list("lot_id", flat=True)
    return Ticket.objects.filter(lot__in=subscribed_lots).select_related(
        "lot__phase__project", "created_by"
    ).order_by("-created_at")
