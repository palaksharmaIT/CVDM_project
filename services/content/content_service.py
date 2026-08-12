from django.db import transaction
from django.utils import timezone

from content.models import Content

from audit.models import AuditLog
from services.audit.audit_service import create_audit_log

from .version_service import create_version


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

    return content


@transaction.atomic
def publish_content(*, content, user):

    content.status = Content.Status.PUBLISHED
    content.published_at = timezone.now()

    content.save(
        update_fields=[
            "status",
            "published_at",
            "updated_at",
        ]
    )

    create_audit_log(
        content=content,
        user=user,
        action=AuditLog.Action.PUBLISH,
        details="Content published.",
    )

    return content