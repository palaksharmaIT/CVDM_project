from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Content
from .serializers import ContentSerializer, ContentVersionSerializer
from .permissions import (
    IsAuthor,
    IsReviewer,
    IsEditor,
    IsAdmin,
    CanApproveContent,
)

from ai_review.serializers import AIReviewResultSerializer

from services.content.content_service import (
    create_content,
    update_content,
    restore_version as restore_version_service,
    submit_for_review,
    approve_content,
    reject_content,
    publish_content,
)
from services.ai.ai_review_service import run_ai_review
from services.content.diff_service import compute_version_diff


class ContentViewSet(viewsets.ModelViewSet):

    serializer_class = ContentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Content.objects.select_related("created_by").all()

    def perform_create(self, serializer):
        create_content(
            title=serializer.validated_data["title"],
            body=serializer.validated_data["body"],
            user=self.request.user,
        )

    def perform_update(self, serializer):
        content = self.get_object()

        update_content(
            content=content,
            title=serializer.validated_data.get(
                "title",
                content.title,
            ),
            body=serializer.validated_data.get(
                "body",
                content.body,
            ),
            user=self.request.user,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="versions",
    )
    def versions(self, request, pk=None):
        content = self.get_object()

        versions = content.versions.all()

        serializer = ContentVersionSerializer(
            versions,
            many=True,
        )

        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        url_path=r"versions/(?P<version_id>\d+)/restore",
    )
    def restore_version(
        self,
        request,
        pk=None,
        version_id=None,
    ):
        content = self.get_object()

        version = content.versions.filter(
            id=version_id
        ).first()

        if version is None:
            return Response(
                {"detail": "Version not found."},
                status=404,
            )

        new_version = restore_version_service(
            content=content,
            version=version,
            user=request.user,
        )

        return Response(
            {
                "message": "Version restored successfully.",
                "new_version": new_version.version_number,
            }
        )
    @action(
        detail=True,
        methods=["get"],
        url_path="diff",
    )
    def diff(self, request, pk=None):
        """
        Compares two versions of this content, line by line.

        GET .../diff/?to=<version_id>
            Compares version <to> against the version right
            before it.

        GET .../diff/?from=<version_id>&to=<version_id>
            Compares two specific versions.
        """
        content = self.get_object()

        to_id = request.query_params.get("to")

        if not to_id:
            return Response(
                {"detail": "'to' query param (version id) is required."},
                status=400,
            )

        new_version = content.versions.filter(id=to_id).first()

        if new_version is None:
            return Response(
                {"detail": "'to' version not found."},
                status=404,
            )

        from_id = request.query_params.get("from")

        if from_id:
            old_version = content.versions.filter(id=from_id).first()

            if old_version is None:
                return Response(
                    {"detail": "'from' version not found."},
                    status=404,
                )
        else:
            old_version = content.versions.filter(
                version_number=new_version.version_number - 1
            ).first()

        diff = compute_version_diff(
            old_version=old_version,
            new_version=new_version,
        )

        return Response(diff)
    
    @action(
        detail=True,
        methods=["post"],
        url_path="ai-review",
    )
    def ai_review(self, request, pk=None):
        """
        Manually (re-)runs the AI grammar/clarity review on the
        content's current text. Useful for an Author who wants
        feedback before submitting for human review.
        """
        content = self.get_object()

        latest_version = (
            content.versions.order_by("-version_number").first()
        )

        result = run_ai_review(
            content=content,
            user=request.user,
            content_version=latest_version,
        )

        return Response(
            AIReviewResultSerializer(result).data
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="ai-review/latest",
    )
    def latest_ai_review(self, request, pk=None):
        content = self.get_object()

        result = content.ai_reviews.first()

        if result is None:
            return Response(
                {"detail": "No AI review has been run yet."},
                status=404,
            )

        return Response(
            AIReviewResultSerializer(result).data
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="submit-review",
        permission_classes=[IsAuthor | IsAdmin],
    )
    def submit_review(self, request, pk=None):
        content = self.get_object()

        content = submit_for_review(
            content=content,
            user=request.user,
        )

        return Response(
            {
                "message": "Content submitted for review.",
                "status": content.status,
            }
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="approve",
        permission_classes=[CanApproveContent],
    )
    def approve(self, request, pk=None):
        content = self.get_object()

        content = approve_content(
            content=content,
            user=request.user,
        )

        return Response(
            {
                "message": "Content approved successfully.",
                "status": content.status,
            }
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="reject",
        permission_classes=[CanApproveContent],
    )
    def reject(self, request, pk=None):
        content = self.get_object()

        content = reject_content(
            content=content,
            user=request.user,
        )

        return Response(
            {
                "message": "Content rejected.",
                "status": content.status,
            }
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="publish",
        permission_classes=[IsEditor | IsAdmin],
    )
    def publish(self, request, pk=None):
        content = self.get_object()

        try:
            content = publish_content(
                content=content,
                user=request.user,
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=400,
            )

        return Response(
            {
                "message": "Content published successfully.",
                "status": content.status,
                "published_at": content.published_at,
            }
        )