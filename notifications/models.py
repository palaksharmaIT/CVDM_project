from django.conf import settings
from django.db import models

from content.models import Content


class Notification(models.Model):

    class NotificationType(models.TextChoices):
        REVIEW_ASSIGNED = "review_assigned", "Review Assigned"
        REVIEW_SUBMITTED = "review_submitted", "Review Submitted"
        CONTENT_APPROVED = "content_approved", "Content Approved"
        CONTENT_REJECTED = "content_rejected", "Content Rejected"
        CONTENT_PUBLISHED = "content_published", "Content Published"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
    )

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.message}"