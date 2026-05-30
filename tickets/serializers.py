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
        read_only_fields = [
            "id", "reference", "created_by", "status", "created_at",
        ]


class TicketCreateSerializer(serializers.Serializer):
    """Validation des données d'entrée pour la création d'un ticket."""

    lot = serializers.PrimaryKeyRelatedField(queryset=Lot.objects.all())
    type = serializers.ChoiceField(choices=Ticket.Type.choices)
    what_tested = serializers.CharField(min_length=20)
    observed_result = serializers.CharField(min_length=20)
    expected_result = serializers.CharField(min_length=20)
    note = serializers.CharField(min_length=10, required=False, allow_null=True)
