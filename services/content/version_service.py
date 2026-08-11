from django.db import transaction

from content.models import Content
from versions.models import ContentVersion


@transaction.atomic
def create_version(content, user, change_note=""):
    latest_version = (
        ContentVersion.objects
        .filter(content=content)
        .order_by("-version_number")
        .first()
    )

    next_version_number = (
        latest_version.version_number + 1
        if latest_version
        else 1
    )

    version = ContentVersion.objects.create(
        content=content,
        version_number=next_version_number,
        title=content.title,
        body=content.body,
        change_note=change_note,
        created_by=user,
    )

    return version