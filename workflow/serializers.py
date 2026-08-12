from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import ReviewAssignment


User = get_user_model()


class ReviewAssignmentSerializer(serializers.ModelSerializer):

    reviewer_username = serializers.CharField(
        source="reviewer.username", read_only=True
    )
    assigned_by_username = serializers.CharField(
        source="assigned_by.username", read_only=True
    )
    content_title = serializers.CharField(
        source="content.title", read_only=True
    )

    class Meta:
        model = ReviewAssignment
        fields = [
            "id",
            "content",
            "content_title",
            "reviewer",
            "reviewer_username",
            "assigned_by",
            "assigned_by_username",
            "status",
            "note",
            "assigned_at",
            "completed_at",
        ]
        read_only_fields = fields


class AssignReviewerSerializer(serializers.Serializer):

    reviewer_id = serializers.IntegerField()
    note = serializers.CharField(
        required=False, allow_blank=True, default=""
    )

    def validate_reviewer_id(self, value):
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Reviewer not found.")

        is_eligible = (
            user.is_superuser
            or user.groups.filter(
                name__in=["Reviewer", "Admin"]
            ).exists()
        )

        if not is_eligible:
            raise serializers.ValidationError(
                "This user does not have the Reviewer or Admin role."
            )

        return value