from rest_framework import serializers

from .models import Content
from versions.models import ContentVersion


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
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
            "published_at",
        ]


class ContentVersionSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    class Meta:
        model = ContentVersion
        fields = [
            "id",
            "version_number",
            "title",
            "body",
            "change_note",
            "created_by",
            "created_by_username",
            "created_at",
            "is_published",
        ]
        read_only_fields = fields