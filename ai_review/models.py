from django.db import models

from content.models import Content
from versions.models import ContentVersion


class AIReviewResult(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name="ai_reviews",
    )

    content_version = models.ForeignKey(
        ContentVersion,
        on_delete=models.CASCADE,
        related_name="ai_reviews",
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Overall grammar/clarity score, 0-100.",
    )

    summary = models.TextField(blank=True)

    issues = models.JSONField(default=list, blank=True)

    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"AI Review for {self.content.title} ({self.status})"