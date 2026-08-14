from django.core.management.base import BaseCommand

from services.content.content_service import publish_due_scheduled_content


class Command(BaseCommand):
    help = (
        "Publishes any approved content whose scheduled publish "
        "time has arrived. Intended to be run periodically "
        "(e.g. every few minutes via cron / Task Scheduler)."
    )

    def handle(self, *args, **options):
        published = publish_due_scheduled_content()

        if not published:
            self.stdout.write("No scheduled content was due.")
            return

        for content in published:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Published: \"{content.title}\" (id={content.id})"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"{len(published)} item(s) published.")
        )