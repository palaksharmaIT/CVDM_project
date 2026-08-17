from django.conf import settings
from django.db import models

from content.models import Content


class ReviewAssignment(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name="review_assignments",
    )

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_assignments",
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments_made",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    note = models.TextField(blank=True)

    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-assigned_at"]

    def __str__(self):
        return (
            f"{self.reviewer} assigned to '{self.content}' "
            f"({self.status})"
        )
class ReviewComment(models.Model):

    assignment = models.ForeignKey(
        ReviewAssignment,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_comments",
    )

    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"Comment by {self.user} "
            f"on '{self.assignment.content}'"
        )    