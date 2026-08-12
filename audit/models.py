from django.conf import settings
from django.db import models


class AuditLog(models.Model):

    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        VERSION_RESTORE = "version_restore", "Version Restore"
        SUBMIT_FOR_REVIEW = "submit_for_review", "Submit For Review"
        AI_REVIEW = "ai_review", "AI Review"
        APPROVE = "approve", "Approve"
        REJECT = "reject", "Reject"
        PUBLISH = "publish", "Publish"

    content = models.ForeignKey(
        "content.Content",
        on_delete=models.CASCADE,
        related_name="audit_logs",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="audit_logs",
    )

    action = models.CharField(
        max_length=30,
        choices=Action.choices,
    )

    details = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.content}"