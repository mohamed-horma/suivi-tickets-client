from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import uuid


class UserManager(BaseUserManager):
    def create_user(
        self, email: str, password: str | None = None, **extra_fields
    ) -> "User":
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Utilisateur de l'application. Rôle admin ou client."""

    class Role(models.TextChoices):
        CLIENT = "client", "Client"
        ADMIN = "admin", "Admin"

    username = None
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CLIENT)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.email


class Project(models.Model):
    """Projet logiciel suivi dans l'application de suivi des tickets client."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slack_channel = models.URLField()
    notion_page_url = models.URLField()
    notion_sync_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Phase(models.Model):
    """Phase d'un projet (regroupement de lots)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="phases")
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Lot(models.Model):
    """Lot de tickets au sein d'une phase."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="lots")
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Assignment(models.Model):
    """Association entre un utilisateur client et un projet."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assignment",
        limit_choices_to={"role": User.Role.CLIENT},
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="assignment")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "project")

    def __str__(self) -> str:
        # user_id / project_id accèdent aux colonnes FK directement — aucune query
        return f"user={self.user_id} → project={self.project_id}"


class Abonnment(models.Model):
    """Abonnement aux notifications d'un lot."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="abonnment")
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="abonnment")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "lot")

    def __str__(self) -> str:
        # user_id / lot_id accèdent aux colonnes FK directement — aucune query
        return f"user={self.user_id} ↔ lot={self.lot_id}"


class Ticket(models.Model):
    """
    Ticket client : bug, suggestion ou nouvelle demande.
    Référence unique au format #BP-AAAA-NNNNN, générée à la création.
    Les champs de contenu (what_tested, observed_result, expected_result, type)
    sont immuables après création — enforcement via readonly_fields dans
    TicketAdmin et read_only_fields dans TicketSerializer.
    """

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Soumis"
        IN_REVIEW = "in_review", "En révision"
        REJECTED = "rejected", "Rejeté"
        TODO = "todo", "À faire"
        IN_PROGRESS = "in_progress", "En cours"
        DEVELOPED = "developed", "Développé"
        CLIENT_TESTING = "client_testing", "Test client"
        VALIDATED = "validated", "Validé"
        ON_HOLD = "on_hold", "En attente"

    class Type(models.TextChoices):
        BUG = "bug", "Bug"
        SUGGESTION = "suggestion", "Suggestion"
        NEW_REQUEST = "new_request", "Nouvelle demande"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="tickets")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="tickets", null=True
    )
    reference = models.CharField(max_length=20, unique=True, blank=True)
    type = models.CharField(max_length=20, choices=Type.choices)
    what_tested = models.TextField()
    observed_result = models.TextField()
    expected_result = models.TextField()
    note = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SUBMITTED
    )
    synced_to_notion = models.BooleanField(default=False)
    notion_ticket_id = models.CharField(max_length=100, blank=True)
    requires_sync = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.reference or "DRAFT"


class Comment(models.Model):
    """
    Commentaire attaché à un ticket.
    Immuable après création — enforcement au niveau du service.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comment")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comment")
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.text[:50]


class Screenshot(models.Model):
    """Capture d'écran attachée à un ticket."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="screenshot")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="screenshot")
    url = models.URLField()
    upload_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Capture de {self.ticket}"


class Notification(models.Model):
    """Notification email ou Slack envoyée à un utilisateur pour un ticket."""

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SLACK = "slack", "Slack"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="notification")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notification")
    title = models.CharField(max_length=100)
    text = models.TextField(max_length=300)
    channel = models.CharField(max_length=20, choices=Channel.choices)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"[{self.channel}] {self.title}"


class SyncJob(models.Model):
    """Job de synchronisation bidirectionnelle avec Notion."""

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        COMPLETED = "completed", "Terminé"
        FAILED = "failed", "Échoué"

    class SyncType(models.TextChoices):
        APP_TO_NOTION = "app_to_notion", "App → Notion"
        NOTION_TO_APP = "notion_to_app", "Notion → App"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sync_type = models.CharField(max_length=20, choices=SyncType.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    tickets_processed = models.IntegerField(default=0)
    tickets_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.get_sync_type_display()} — {self.get_status_display()}"


class SyncLog(models.Model):
    """Journal d'une synchronisation par ticket."""

    class SyncStatus(models.TextChoices):
        SUCCESS = "success", "Succès"
        FAILURE = "failure", "Échec"
        SKIPPED = "skipped", "Ignoré"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sync_job = models.ForeignKey(SyncJob, on_delete=models.CASCADE, related_name="sync_log")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="sync_log")
    sync_status = models.CharField(max_length=20, choices=SyncStatus.choices)
    error_message = models.TextField(blank=True, null=True)
    notion_ticket_id = models.CharField(max_length=100, blank=True, default="")
    synced_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.ticket} — {self.get_sync_status_display()}"
