from django.conf import settings
from django.db import models

class Content(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_REVIEW = "in_review", "In Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        PUBLISHED = "published", "Published"
    title = models.CharField(max_length=255)
    body = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_content",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="If set, this content will be auto-published at this time.",
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title