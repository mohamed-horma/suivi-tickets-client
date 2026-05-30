from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Abonnment,
    Assignment,
    Comment,
    Lot,
    Notification,
    Phase,
    Project,
    Screenshot,
    SyncJob,
    SyncLog,
    Ticket,
    User,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "role", "is_active"]
    list_filter = ["role", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informations", {"fields": ("first_name", "last_name", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "role")}),
    )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "notion_sync_enabled", "created_at"]
    list_filter = ["notion_sync_enabled"]
    search_fields = ["name"]


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "created_at"]
    list_filter = ["project"]


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ["name", "phase", "created_at"]
    list_filter = ["phase__project"]


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["user", "project", "created_at"]
    list_filter = ["project"]


@admin.register(Abonnment)
class AbonnmentAdmin(admin.ModelAdmin):
    list_display = ["user", "lot", "created_at"]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["reference", "type", "status", "lot", "created_by", "created_at"]
    list_filter = ["type", "status", "lot__phase__project"]
    search_fields = ["reference", "what_tested"]
    readonly_fields = [
        "reference", "lot", "created_by", "type",
        "what_tested", "observed_result", "expected_result", "created_at",
    ]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["ticket", "user", "created_at"]
    readonly_fields = ["ticket", "user", "text", "created_at"]


@admin.register(Screenshot)
class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ["ticket", "user", "upload_at"]
    readonly_fields = ["ticket", "user", "upload_at"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "channel", "user", "sent_at"]
    list_filter = ["channel"]


@admin.register(SyncJob)
class SyncJobAdmin(admin.ModelAdmin):
    list_display = ["sync_type", "status", "tickets_processed", "tickets_failed", "started_at"]
    list_filter = ["sync_type", "status"]


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ["ticket", "sync_job", "sync_status", "synced_at"]
    list_filter = ["sync_status"]
