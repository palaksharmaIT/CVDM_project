# from django.db import transaction
# from django.utils import timezone

# from content.models import Content

# from audit.models import AuditLog
# from services.audit.audit_service import create_audit_log
# from services.ai.ai_review_service import run_ai_review
# from services.workflow.assignment_service import complete_pending_assignments

# from .version_service import create_version
# from services.notifications.notification_service import (
#     notify_content_rejected,
#     notify_review_submitted,
#     notify_content_approved,
#     notify_content_published,
# )


# @transaction.atomic
# def create_content(*, title, body, user):

#     content = Content.objects.create(
#         title=title,
#         body=body,
#         created_by=user,
#     )

#     create_version(
#         content=content,
#         user=user,
#         change_note="Initial version",
#     )

#     create_audit_log(
#         content=content,
#         user=user,
#         action=AuditLog.Action.CREATE,
#         details="Content created.",
#     )

#     return content


# @transaction.atomic
# def update_content(
#     *,
#     content,
#     title,
#     body,
#     user,
#     change_note="Content updated",
# ):

#     content.title = title
#     content.body = body
#     content.save()

#     create_version(
#         content=content,
#         user=user,
#         change_note=change_note,
#     )

#     create_audit_log(
#         content=content,
#         user=user,
#         action=AuditLog.Action.UPDATE,
#         details=change_note,
#     )

#     return content


# @transaction.atomic
# def restore_version(*, content, version, user):

#     content.title = version.title
#     content.body = version.body
#     content.save()

#     new_version = create_version(
#         content=content,
#         user=user,
#         change_note=f"Restored from version {version.version_number}",
#     )

#     create_audit_log(
#         content=content,
#         user=user,
#         action=AuditLog.Action.VERSION_RESTORE,
#         details=f"Restored from version {version.version_number}.",
#     )

#     return new_version


# @transaction.atomic
# def submit_for_review(*, content, user):

#     content.status = Content.Status.IN_REVIEW

#     content.save(
#         update_fields=["status", "updated_at"]
#     )

#     create_audit_log(
#         content=content,
#         user=user,
#         action=AuditLog.Action.SUBMIT_FOR_REVIEW,
#         details="Content submitted for review.",
#     )

#     latest_version = (
#         content.versions.order_by("-version_number").first()
#     )

#     run_ai_review(
#         content=content,
#         user=user,
#         content_version=latest_version,
#     )

#     # Notify all pending reviewers assigned to this content
#     assignments = content.review_assignments.filter(
#         status="pending"
#     )

#     for assignment in assignments:
#         notify_review_submitted(
#             reviewer=assignment.reviewer,
#             content=content,
#         )

#     return content


# @transaction.atomic
# def approve_content(*, content, user):

#     content.status = Content.Status.APPROVED

#     content.save(
#         update_fields=["status", "updated_at"]
#     )

#     create_audit_log(
#         content=content,
#         user=user,
#         action=AuditLog.Action.APPROVE,
#         details="Content approved.",
#     )

#     complete_pending_assignments(
#         content=content,
#         reviewer=user,
#     )

#     # Notify the content author
#     notify_content_approved(
#         author=content.created_by,
#         content=content,
#     )

#     return content


# @transaction.atomic
# def reject_content(*, content, user):

#     content.status = Content.Status.REJECTED

#     content.save(
#         update_fields=["status", "updated_at"]
#     )

#     create_audit_log(
#         content=content,
#         user=user,
#         action=AuditLog.Action.REJECT,
#         details="Content rejected.",
#     )

#     complete_pending_assignments(
#         content=content,
#         reviewer=user,
#     )

#     # Notify the content author
#     notify_content_rejected(
#         author=content.created_by,
#         content=content,
#     )

#     return content


# @transaction.atomic
# def publish_content(*, content, user):

#     content.status = Content.Status.PUBLISHED
#     content.published_at = timezone.now()
#     content.scheduled_at = None

#     content.save(
#         update_fields=[
#             "status",
#             "published_at",
#             "scheduled_at",
#             "updated_at",
#         ]
#     )

#     create_audit_log(
#         content=content,
#         user=user,
#         action=AuditLog.Action.PUBLISH,
#         details="Content published.",
#     )

#     # Notify the content author
#     notify_content_published(
#         author=content.created_by,
#         content=content,
#     )

#     return content


# @transaction.atomic
# def schedule_content(*, content, user, scheduled_at):
#     """
#     Schedules approved content to be auto-published at a future
#     time. The content stays in "approved" status until the
#     scheduled time arrives — publish_due_scheduled_content() (run
#     periodically, e.g. via a management command / cron) does the
#     actual publish.
#     """

#     if content.status != Content.Status.APPROVED:
#         raise ValueError(
#             "Only approved content can be scheduled for publishing."
#         )

#     if scheduled_at <= timezone.now():
#         raise ValueError("scheduled_at must be in the future.")

#     content.scheduled_at = scheduled_at

#     content.save(
#         update_fields=["scheduled_at", "updated_at"]
#     )

#     create_audit_log(
#         content=content,
#         user=user,
#         action=AuditLog.Action.SCHEDULE_PUBLISH,
#         details=f"Scheduled to publish at {scheduled_at.isoformat()}.",
#     )

#     return content


# @transaction.atomic
# def cancel_scheduled_publish(*, content, user):

#     content.scheduled_at = None

#     content.save(
#         update_fields=["scheduled_at", "updated_at"]
#     )

#     create_audit_log(
#         content=content,
#         user=user,
#         action=AuditLog.Action.SCHEDULE_PUBLISH,
#         details="Cancelled scheduled publish.",
#     )

#     return content


# def publish_due_scheduled_content():
#     """
#     Publishes every approved piece of content whose scheduled_at
#     has arrived. Intended to be called periodically (management
#     command run via cron / task scheduler). Returns the list of
#     published Content objects.
#     """

#     due_items = Content.objects.filter(
#         status=Content.Status.APPROVED,
#         scheduled_at__isnull=False,
#         scheduled_at__lte=timezone.now(),
#     )

#     published = []

#     for content in due_items:
#         publish_content(content=content, user=content.created_by)
#         published.append(content)

#     return published


from django.db import transaction
from django.utils import timezone

from content.models import Content

from audit.models import AuditLog
from services.audit.audit_service import create_audit_log
from services.ai.ai_review_service import run_ai_review
from services.ai.category_service import detect_and_set_category
from services.workflow.assignment_service import complete_pending_assignments

from .version_service import create_version
from services.notifications.notification_service import (
    notify_content_rejected,
    notify_review_submitted,
    notify_content_approved,
    notify_content_published,
)


@transaction.atomic
def create_content(*, title, body, user):

    content = Content.objects.create(
        title=title,
        body=body,
        created_by=user,
    )

    create_version(
        content=content,
        user=user,
        change_note="Initial version",
    )

    create_audit_log(
        content=content,
        user=user,
        action=AuditLog.Action.CREATE,
        details="Content created.",
    )

    # Runs after the transaction commits — it's a network call to the
    # AI provider and best-effort only, so it shouldn't hold up (or
    # ride inside) the DB transaction above.
    transaction.on_commit(lambda: detect_and_set_category(content=content))

    return content


@transaction.atomic
def update_content(
    *,
    content,
    title,
    body,
    user,
    change_note="Content updated",
):

    content.title = title
    content.body = body
    content.save()

    create_version(
        content=content,
        user=user,
        change_note=change_note,
    )

    create_audit_log(
        content=content,
        user=user,
        action=AuditLog.Action.UPDATE,
        details=change_note,
    )

    transaction.on_commit(lambda: detect_and_set_category(content=content))

    return content


@transaction.atomic
def restore_version(*, content, version, user):

    content.title = version.title
    content.body = version.body
    content.save()

    new_version = create_version(
        content=content,
        user=user,
        change_note=f"Restored from version {version.version_number}",
    )

    create_audit_log(
        content=content,
        user=user,
        action=AuditLog.Action.VERSION_RESTORE,
        details=f"Restored from version {version.version_number}.",
    )

    return new_version


@transaction.atomic
def submit_for_review(*, content, user):

    content.status = Content.Status.IN_REVIEW

    content.save(
        update_fields=["status", "updated_at"]
    )

    create_audit_log(
        content=content,
        user=user,
        action=AuditLog.Action.SUBMIT_FOR_REVIEW,
        details="Content submitted for review.",
    )

    latest_version = (
        content.versions.order_by("-version_number").first()
    )

    run_ai_review(
        content=content,
        user=user,
        content_version=latest_version,
    )

    # Notify all pending reviewers assigned to this content
    assignments = content.review_assignments.filter(
        status="pending"
    )

    for assignment in assignments:
        notify_review_submitted(
            reviewer=assignment.reviewer,
            content=content,
        )

    return content


@transaction.atomic
def approve_content(*, content, user):

    content.status = Content.Status.APPROVED

    content.save(
        update_fields=["status", "updated_at"]
    )

    create_audit_log(
        content=content,
        user=user,
        action=AuditLog.Action.APPROVE,
        details="Content approved.",
    )

    complete_pending_assignments(
        content=content,
        reviewer=user,
    )

    # Notify the content author
    notify_content_approved(
        author=content.created_by,
        content=content,
    )

    return content


@transaction.atomic
def reject_content(*, content, user):

    content.status = Content.Status.REJECTED

    content.save(
        update_fields=["status", "updated_at"]
    )

    create_audit_log(
        content=content,
        user=user,
        action=AuditLog.Action.REJECT,
        details="Content rejected.",
    )

    complete_pending_assignments(
        content=content,
        reviewer=user,
    )

    # Notify the content author
    notify_content_rejected(
        author=content.created_by,
        content=content,
    )

    return content


@transaction.atomic
def publish_content(*, content, user):

    content.status = Content.Status.PUBLISHED
    content.published_at = timezone.now()
    content.scheduled_at = None

    content.save(
        update_fields=[
            "status",
            "published_at",
            "scheduled_at",
            "updated_at",
        ]
    )

    create_audit_log(
        content=content,
        user=user,
        action=AuditLog.Action.PUBLISH,
        details="Content published.",
    )

    # Notify the content author
    notify_content_published(
        author=content.created_by,
        content=content,
    )

    return content


@transaction.atomic
def schedule_content(*, content, user, scheduled_at):
    """
    Schedules approved content to be auto-published at a future
    time. The content stays in "approved" status until the
    scheduled time arrives — publish_due_scheduled_content() (run
    periodically, e.g. via a management command / cron) does the
    actual publish.
    """

    if content.status != Content.Status.APPROVED:
        raise ValueError(
            "Only approved content can be scheduled for publishing."
        )

    if scheduled_at <= timezone.now():
        raise ValueError("scheduled_at must be in the future.")

    content.scheduled_at = scheduled_at

    content.save(
        update_fields=["scheduled_at", "updated_at"]
    )

    create_audit_log(
        content=content,
        user=user,
        action=AuditLog.Action.SCHEDULE_PUBLISH,
        details=f"Scheduled to publish at {scheduled_at.isoformat()}.",
    )

    return content


@transaction.atomic
def cancel_scheduled_publish(*, content, user):

    content.scheduled_at = None

    content.save(
        update_fields=["scheduled_at", "updated_at"]
    )

    create_audit_log(
        content=content,
        user=user,
        action=AuditLog.Action.SCHEDULE_PUBLISH,
        details="Cancelled scheduled publish.",
    )

    return content


def publish_due_scheduled_content():
    """
    Publishes every approved piece of content whose scheduled_at
    has arrived. Intended to be called periodically (management
    command run via cron / task scheduler). Returns the list of
    published Content objects.
    """

    due_items = Content.objects.filter(
        status=Content.Status.APPROVED,
        scheduled_at__isnull=False,
        scheduled_at__lte=timezone.now(),
    )

    published = []

    for content in due_items:
        publish_content(content=content, user=content.created_by)
        published.append(content)

    return published