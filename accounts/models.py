import uuid

from django.conf import settings
from django.db import models


class EmailVerification(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification",
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "verified" if self.is_verified else "pending"
        return f"Verification for {self.user.username} ({status})"