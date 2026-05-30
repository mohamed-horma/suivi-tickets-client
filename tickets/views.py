from django.db.models import QuerySet
from rest_framework import permissions, serializers as drf_serializers, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from . import selectors
from .exceptions import TicketValidationError
from .models import Lot, Phase, Project, Ticket
from .serializers import (
    LotSerializer,
    PhaseSerializer,
    ProjectSerializer,
    TicketCreateSerializer,
    TicketSerializer,
)
from .services import create_ticket


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Project]:
        return selectors.list_projects()


class PhaseViewSet(viewsets.ModelViewSet):
    serializer_class = PhaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Phase]:
        return selectors.list_phases()


class LotViewSet(viewsets.ModelViewSet):
    serializer_class = LotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Lot]:
        return selectors.list_lots()


class TicketViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self) -> type[drf_serializers.BaseSerializer]:
        if self.action == "create":
            return TicketCreateSerializer
        return TicketSerializer

    def get_queryset(self) -> QuerySet[Ticket]:
        return selectors.list_tickets()

    def create(self, request: Request) -> Response:
        serializer = TicketCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            ticket = create_ticket(
                lot=data["lot"],
                created_by=request.user,
                ticket_type=data["type"],
                what_tested=data["what_tested"],
                observed_result=data["observed_result"],
                expected_result=data["expected_result"],
                note=data.get("note"),
            )
        except TicketValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(TicketSerializer(ticket).data, status=status.HTTP_201_CREATED)
