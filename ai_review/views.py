from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db import models

from .models import AIReviewResult
from .serializers import AIReviewResultSerializer


class AIReviewResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only list of AI review results. Supports filtering by
    content, e.g. /api/ai-reviews/?content=3
    """

    serializer_class = AIReviewResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = AIReviewResult.objects.select_related(
            "content",
            "content_version",
        ).all()

        is_admin_or_editor = (
            user.is_superuser
            or user.groups.filter(name__in=["Admin", "Editor"]).exists()
        )

        if not is_admin_or_editor:
            queryset = queryset.filter(
                models.Q(content__created_by=user)
                | models.Q(content__review_assignments__reviewer=user)
            ).distinct()

        content_id = self.request.query_params.get("content")

        if content_id:
            queryset = queryset.filter(content_id=content_id)

        return queryset