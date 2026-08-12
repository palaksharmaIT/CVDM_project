from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ReviewAssignment
from .serializers import ReviewAssignmentSerializer


class ReviewAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only list of review assignments. Supports filtering by
    content, e.g. /api/review-assignments/?content=5
    """

    serializer_class = ReviewAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ReviewAssignment.objects.select_related(
            "content",
            "reviewer",
            "assigned_by",
        ).all()

        content_id = self.request.query_params.get("content")

        if content_id:
            queryset = queryset.filter(content_id=content_id)

        return queryset

    @action(
        detail=False,
        methods=["get"],
        url_path="my-queue",
    )
    def my_queue(self, request):
        """
        Returns the current user's pending review assignments —
        their personal "to review" queue.
        """
        assignments = ReviewAssignment.objects.select_related(
            "content",
            "assigned_by",
        ).filter(
            reviewer=request.user,
            status=ReviewAssignment.Status.PENDING,
        )

        serializer = self.get_serializer(assignments, many=True)

        return Response(serializer.data)