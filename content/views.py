from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Content
from .serializers import ContentSerializer

from services.content.content_service import (
    create_content,
    update_content,
)


class ContentViewSet(viewsets.ModelViewSet):
    serializer_class = ContentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Content.objects.select_related("created_by").all()

    def perform_create(self, serializer):
        create_content(
            title=serializer.validated_data["title"],
            body=serializer.validated_data["body"],
            user=self.request.user,
        )

    def perform_update(self, serializer):
        content = self.get_object()

        update_content(
            content=content,
            title=serializer.validated_data.get(
                "title",
                content.title,
            ),
            body=serializer.validated_data.get(
                "body",
                content.body,
            ),
            user=self.request.user,
        )