from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Content
from .serializers import ContentSerializer
from services.content.version_service import create_version


class ContentViewSet(viewsets.ModelViewSet):
    serializer_class = ContentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Content.objects.select_related("created_by").all()

    def perform_create(self, serializer):
        content = serializer.save(
            created_by=self.request.user
        )

        create_version(
            content=content,
            user=self.request.user,
            change_note="Initial version",
        )

    def perform_update(self, serializer):
        content = serializer.save()

        create_version(
            content=content,
            user=self.request.user,
            change_note="Content updated",
        )