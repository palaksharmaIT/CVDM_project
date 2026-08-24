from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = AuditLog.objects.select_related(
            "user",
            "content",
        ).all()

        is_admin_or_editor = (
            user.is_superuser
            or user.groups.filter(name__in=["Admin", "Editor"]).exists()
        )

        if not is_admin_or_editor:
            queryset = queryset.filter(content__created_by=user)

        return queryset