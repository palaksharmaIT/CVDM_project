from rest_framework import serializers

from .models import AIReviewResult


class AIReviewResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = AIReviewResult
        fields = [
            "id",
            "content",
            "content_version",
            "status",
            "score",
            "summary",
            "issues",
            "error_message",
            "created_at",
        ]
        read_only_fields = fields