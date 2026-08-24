from django.contrib.auth import get_user_model

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from audit.models import AuditLog
from audit.serializers import AuditLogSerializer

from .models import Content
from .serializers import ContentSerializer, ContentVersionSerializer
from .permissions import (
    IsAuthor,
    IsReviewer,
    IsEditor,
    IsAdmin,
    CanApproveContent,
    IsContentOwnerOrAdmin,
    CanEditContent,
    CanViewContent,
    CanAssignReviewer,
    CanSubmitForReview,
)

from ai_review.serializers import AIReviewResultSerializer
from workflow.serializers import (
    AssignReviewerSerializer,
    ReviewAssignmentSerializer,
)

from services.content.content_service import (
    create_content,
    update_content,
    restore_version as restore_version_service,
    submit_for_review,
    approve_content,
    reject_content,
    publish_content,
    schedule_content,
    cancel_scheduled_publish,
)
from services.ai.ai_review_service import run_ai_review
from services.content.diff_service import compute_version_diff
from services.workflow.assignment_service import assign_reviewer


User = get_user_model()


class ContentViewSet(viewsets.ModelViewSet):

    serializer_class = ContentSerializer
    permission_classes = [IsAuthenticated, IsContentOwnerOrAdmin]

    def get_queryset(self):
        return Content.objects.select_related("created_by").all()

    def perform_create(self, serializer):
        create_content(
            title=serializer.validated_data["title"],
            body=serializer.validated_data["body"],
            user=self.request.user,
        )
    def get_serializer_class(self):
        if self.action == "assign_reviewer_action":
            return AssignReviewerSerializer

        return ContentSerializer        

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
        permission_classes=[IsAuthenticated, CanViewContent],
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
        permission_classes=[IsAuthenticated, CanEditContent],
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
        permission_classes=[IsAuthenticated, CanViewContent],
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
        permission_classes=[IsAuthenticated, CanViewContent],
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
        permission_classes=[IsAuthenticated, CanViewContent],
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
        url_path="assign-reviewer",
        permission_classes=[IsAuthenticated, CanAssignReviewer],
    )
    def assign_reviewer_action(self, request, pk=None):
        """
        Assigns a specific reviewer to this content. reviewer_id
        must belong to a user in the Reviewer or Admin role.
        """
        content = self.get_object()

        serializer = AssignReviewerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reviewer = User.objects.get(
            id=serializer.validated_data["reviewer_id"]
        )

        assignment = assign_reviewer(
            content=content,
            reviewer=reviewer,
            assigned_by=request.user,
            note=serializer.validated_data.get("note", ""),
        )

        return Response(
            ReviewAssignmentSerializer(assignment).data,
            status=201,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="submit-review",
        permission_classes=[IsAuthenticated, CanSubmitForReview],
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

    @action(
        detail=True,
        methods=["post"],
        url_path="schedule",
        permission_classes=[IsEditor | IsAdmin],
    )
    def schedule(self, request, pk=None):
        content = self.get_object()

        from django.utils.dateparse import parse_datetime
        from django.utils import timezone

        raw = request.data.get("scheduled_at")

        if not raw:
            return Response(
                {"detail": "'scheduled_at' is required (ISO 8601 format)."},
                status=400,
            )

        scheduled_at = parse_datetime(raw)

        if scheduled_at is None:
            return Response(
                {"detail": "'scheduled_at' must be a valid ISO 8601 datetime."},
                status=400,
            )

        if timezone.is_naive(scheduled_at):
            scheduled_at = timezone.make_aware(scheduled_at)

        try:
            content = schedule_content(
                content=content,
                user=request.user,
                scheduled_at=scheduled_at,
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=400,
            )

        return Response(
            {
                "message": "Content scheduled for publishing.",
                "status": content.status,
                "scheduled_at": content.scheduled_at,
            }
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="cancel-schedule",
        permission_classes=[IsEditor | IsAdmin],
    )
    def cancel_schedule(self, request, pk=None):
        content = self.get_object()

        content = cancel_scheduled_publish(
            content=content,
            user=request.user,
        )

        return Response(
            {
                "message": "Scheduled publish cancelled.",
                "status": content.status,
                "scheduled_at": content.scheduled_at,
            }
        )
    
    @action(
        detail=True,
        methods=["get"],
        url_path="history",
        permission_classes=[IsAuthenticated, CanViewContent],
    )
    def history(self, request, pk=None):
        content = self.get_object()

        logs = AuditLog.objects.select_related(
            "user",
            "content",
        ).filter(
            content=content,
        ).order_by("created_at")

        serializer = AuditLogSerializer(
            logs,
            many=True,
        )

        return Response(serializer.data)