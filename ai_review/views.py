from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

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
        queryset = AIReviewResult.objects.select_related(
            "content",
            "content_version",
        ).all()

        content_id = self.request.query_params.get("content")

        if content_id:
            queryset = queryset.filter(content_id=content_id)

        return queryset