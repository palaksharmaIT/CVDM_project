from django.conf import settings
from django.db import models

from content.models import Content


class ContentVersion(models.Model):

    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name="versions",
    )

    version_number = models.PositiveIntegerField()

    title = models.CharField(max_length=255)

    body = models.TextField()

    change_note = models.CharField(
        max_length=500,
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_versions",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    is_published = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ["-version_number"]

        constraints = [
            models.UniqueConstraint(
                fields=["content", "version_number"],
                name="unique_content_version",
            )
        ]

    def __str__(self):
        return f"{self.content.title} - v{self.version_number}"