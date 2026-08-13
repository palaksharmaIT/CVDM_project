from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):

    content_title = serializers.CharField(
        source="content.title",
        read_only=True,
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "content",
            "content_title",
            "notification_type",
            "message",
            "is_read",
            "created_at",
        ]

        read_only_fields = fields