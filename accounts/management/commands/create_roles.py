# from django.core.management.base import BaseCommand
# from django.contrib.auth.models import Group


# class Command(BaseCommand):
#     help = "Create default CVDM roles"

#     def handle(self, *args, **options):
#         roles = [
#             "Author",
#             "Reviewer",
#             "Editor",
#             "Admin",
#         ]

#         for role in roles:
#             group, created = Group.objects.get_or_create(name=role)

#             if created:
#                 self.stdout.write(
#                     self.style.SUCCESS(
#                         f"Created role: {role}"
#                     )
#                 )
#             else:
#                 self.stdout.write(
#                     self.style.WARNING(
#                         f"Role already exists: {role}"
#                     )
#                 )

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Create default CVDM roles"

    def handle(self, *args, **options):
        roles = settings.CVDM_ROLES

        for role in roles:
            group, created = Group.objects.get_or_create(name=role)

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created role: {role}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Role already exists: {role}"
                    )
                )