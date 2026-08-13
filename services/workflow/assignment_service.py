from django.utils import timezone

from audit.models import AuditLog
from services.audit.audit_service import create_audit_log
from services.notifications.notification_service import (
    notify_review_assigned,
)
from workflow.models import ReviewAssignment


def assign_reviewer(
    *,
    content,
    reviewer,
    assigned_by,
    note="",
):
    """
    Assigns a specific reviewer to a piece of content
    and logs it.
    """

    assignment = ReviewAssignment.objects.create(
        content=content,
        reviewer=reviewer,
        assigned_by=assigned_by,
        note=note,
    )

    create_audit_log(
        content=content,
        user=assigned_by,
        action=AuditLog.Action.ASSIGN_REVIEWER,
        details=f"Assigned {reviewer.username} as reviewer.",
    )

    # Create notification for the assigned reviewer
    notify_review_assigned(
        reviewer=reviewer,
        content=content,
        assigned_by=assigned_by,
    )

    return assignment


def complete_pending_assignments(
    *,
    content,
    reviewer,
):
    """
    Marks this reviewer's pending assignment(s) for this content
    as completed.

    Called automatically when the reviewer approves or rejects
    the content.
    """

    assignments = ReviewAssignment.objects.filter(
        content=content,
        reviewer=reviewer,
        status=ReviewAssignment.Status.PENDING,
    )

    updated_count = 0

    for assignment in assignments:
        assignment.status = ReviewAssignment.Status.COMPLETED
        assignment.completed_at = timezone.now()

        assignment.save(
            update_fields=[
                "status",
                "completed_at",
            ]
        )

        updated_count += 1

    return updated_count