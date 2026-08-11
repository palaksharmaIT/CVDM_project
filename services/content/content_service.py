from django.db import transaction

from content.models import Content

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

    return content