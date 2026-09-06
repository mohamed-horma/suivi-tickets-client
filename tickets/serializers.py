from rest_framework import serializers

from .models import Lot, Phase, Project, Ticket


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id", "name", "slack_channel",
            "notion_page_url", "notion_sync_enabled", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phase
        fields = ["id", "project", "name", "created_at"]
        read_only_fields = ["id", "created_at"]


class LotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lot
        fields = ["id", "phase", "name", "created_at"]
        read_only_fields = ["id", "created_at"]


class TicketSerializer(serializers.ModelSerializer):
    """Sérialisation en lecture d'un ticket."""

    class Meta:
        model = Ticket
        fields = [
            "id", "lot", "reference", "created_by", "type", "status",
            "what_tested", "observed_result", "expected_result", "note",
            "created_at",
        ]
        # Le contenu d'un ticket est immuable après création : seul `note`
        # reste modifiable, comme dans l'admin. `status` le deviendra quand le
        # contrôle d'accès par rôle sera en place.
        read_only_fields = [
            "id", "reference", "lot", "created_by", "type",
            "what_tested", "observed_result", "expected_result",
            "status", "created_at",
        ]


class TicketCreateSerializer(serializers.Serializer):
    """Validation IO des données d'entrée pour la création d'un ticket.

    Valide uniquement la présence et le type des champs.
    Les règles métier (longueurs minimales) sont enforçées dans create_ticket().
    """

    lot = serializers.PrimaryKeyRelatedField(queryset=Lot.objects.all())
    type = serializers.ChoiceField(choices=Ticket.Type.choices)
    what_tested = serializers.CharField()
    observed_result = serializers.CharField()
    expected_result = serializers.CharField()
    note = serializers.CharField(required=False, allow_null=True)
