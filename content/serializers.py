from rest_framework import serializers

from .models import Content


class ContentSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    class Meta:
        model = Content
        fields = [
            "id",
            "title",
            "body",
            "status",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
            "published_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "published_at",
        ]