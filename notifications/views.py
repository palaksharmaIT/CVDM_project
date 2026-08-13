from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Notification.objects
            .select_related("content")
            .filter(user=self.request.user)
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="unread",
    )
    def unread(self, request):
        notifications = self.get_queryset().filter(
            is_read=False
        )

        serializer = self.get_serializer(
            notifications,
            many=True,
        )

        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        url_path="mark-read",
    )
    def mark_read(self, request, pk=None):
        notification = self.get_object()

        notification.is_read = True
        notification.save(
            update_fields=["is_read"]
        )

        return Response(
            {
                "message": "Notification marked as read.",
                "id": notification.id,
            }
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="mark-all-read",
    )
    def mark_all_read(self, request):
        updated_count = self.get_queryset().filter(
            is_read=False
        ).update(
            is_read=True
        )

        return Response(
            {
                "message": "All notifications marked as read.",
                "updated_count": updated_count,
            }
        )