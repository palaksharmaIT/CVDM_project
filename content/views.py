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

from services.content.content_service import (
    create_content,
    update_content,
    restore_version as restore_version_service,
    submit_for_review,
    approve_content,
    reject_content,
    publish_content,
)


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