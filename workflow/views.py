from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ReviewAssignment, ReviewComment
from .serializers import (
    ReviewAssignmentSerializer,
    ReviewCommentSerializer,
)


class ReviewAssignmentViewSet(viewsets.ReadOnlyModelViewSet):

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
            queryset = queryset.filter(
                content_id=content_id
            )

        return queryset

    @action(
        detail=False,
        methods=["get"],
        url_path="my-queue",
    )
    def my_queue(self, request):

        assignments = ReviewAssignment.objects.select_related(
            "content",
            "assigned_by",
        ).filter(
            reviewer=request.user,
            status=ReviewAssignment.Status.PENDING,
        )

        serializer = self.get_serializer(
            assignments,
            many=True,
        )

        return Response(serializer.data)

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="comments",
    )
    def comments(self, request, pk=None):

        assignment = self.get_object()

        # GET comments
        if request.method == "GET":

            comments = assignment.comments.select_related(
                "user"
            ).all()

            serializer = ReviewCommentSerializer(
                comments,
                many=True,
            )

            return Response(serializer.data)

        # POST comment
        serializer = ReviewCommentSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        comment = serializer.save(
            assignment=assignment,
            user=request.user,
        )

        return Response(
            ReviewCommentSerializer(comment).data,
            status=201,
        )

    @login_required
    def review_queue_page(request):
        assignments = (
            ReviewAssignment.objects
            .select_related("content", "assigned_by")
            .prefetch_related("comments__user")
            .filter(
                reviewer=request.user,
                status=ReviewAssignment.Status.PENDING,
            )
        )

        return render(
            request,
            "workflow/review_queue.html",
            {
                "assignments": assignments,
            },
        )