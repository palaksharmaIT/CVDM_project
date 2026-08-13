from notifications.models import Notification


def create_notification(
    *,
    user,
    message,
    notification_type,
    content=None,
):
    return Notification.objects.create(
        user=user,
        content=content,
        notification_type=notification_type,
        message=message,
    )


def notify_review_assigned(
    *,
    reviewer,
    content,
    assigned_by,
):
    return create_notification(
        user=reviewer,
        content=content,
        notification_type=Notification.NotificationType.REVIEW_ASSIGNED,
        message=(
            f'You have been assigned to review '
            f'"{content.title}" by {assigned_by.username}.'
        ),
    )


def notify_review_submitted(
    *,
    reviewer,
    content,
):
    return create_notification(
        user=reviewer,
        content=content,
        notification_type=Notification.NotificationType.REVIEW_SUBMITTED,
        message=(
            f'Content "{content.title}" has been submitted '
            f'for your review.'
        ),
    )


def notify_content_approved(
    *,
    author,
    content,
):
    return create_notification(
        user=author,
        content=content,
        notification_type=Notification.NotificationType.CONTENT_APPROVED,
        message=(
            f'Your content "{content.title}" has been approved.'
        ),
    )


def notify_content_rejected(
    *,
    author,
    content,
):
    return create_notification(
        user=author,
        content=content,
        notification_type=Notification.NotificationType.CONTENT_REJECTED,
        message=(
            f'Your content "{content.title}" has been rejected.'
        ),
    )


def notify_content_published(
    *,
    author,
    content,
):
    return create_notification(
        user=author,
        content=content,
        notification_type=Notification.NotificationType.CONTENT_PUBLISHED,
        message=(
            f'Your content "{content.title}" has been published.'
        ),
    )