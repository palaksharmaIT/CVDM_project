from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q

from content.models import Content
from notifications.models import Notification
from workflow.models import ReviewAssignment
from audit.models import AuditLog

from services.content.content_service import (
    approve_content,
    reject_content,
)


@login_required
def dashboard(request):
    contents = Content.objects.all()

    unread_notifications = (
        Notification.objects
        .filter(
            user=request.user,
            is_read=False,
        )
        .select_related("content")
        .order_by("-created_at")
    )

    review_queue = (
        ReviewAssignment.objects
        .filter(
            reviewer=request.user,
            status=ReviewAssignment.Status.PENDING,
        )
        .select_related("content", "assigned_by")
        .order_by("-assigned_at")
    )

    recent_activity = (
        AuditLog.objects
        .select_related("content", "user")
        .exclude(
            Q(
                action=AuditLog.Action.AI_REVIEW,
                details__startswith="AI pre-review failed:"
            )
        )
    .order_by("-created_at")[:10]
)

    context = {
        "total_content": contents.count(),

        "draft_count": contents.filter(
            status=Content.Status.DRAFT
        ).count(),

        "review_count": contents.filter(
            status=Content.Status.IN_REVIEW
        ).count(),

        "approved_count": contents.filter(
            status=Content.Status.APPROVED
        ).count(),

        "published_count": contents.filter(
            status=Content.Status.PUBLISHED
        ).count(),

        "unread_notifications": unread_notifications,
        "unread_notification_count": unread_notifications.count(),

        "review_queue": review_queue,

        "recent_activity": recent_activity,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )


@login_required
def review_content(request, content_id):

    content = get_object_or_404(
        Content.objects.select_related("created_by"),
        id=content_id,
    )

    # Make sure this reviewer is actually assigned
    assignment = get_object_or_404(
        ReviewAssignment,
        content=content,
        reviewer=request.user,
        status=ReviewAssignment.Status.PENDING,
    )

    latest_version = (
        content.versions
        .order_by("-version_number")
        .first()
    )

    latest_ai_review = (
        content.ai_reviews
        .order_by("-created_at")
        .first()
    )

    if request.method == "POST":

        action = request.POST.get("action")

        if action == "approve":
            approve_content(
                content=content,
                user=request.user,
            )

            return redirect("dashboard")

        if action == "reject":
            reject_content(
                content=content,
                user=request.user,
            )

            return redirect("dashboard")

    context = {
        "content": content,
        "assignment": assignment,
        "latest_version": latest_version,
        "latest_ai_review": latest_ai_review,
    }

    return render(
        request,
        "dashboard/review_content.html",
        context,
    )