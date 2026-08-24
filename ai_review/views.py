# from rest_framework import viewsets
# from rest_framework.permissions import IsAuthenticated
# from django.db import models

# from .models import AIReviewResult
# from .serializers import AIReviewResultSerializer


# class AIReviewResultViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     Read-only list of AI review results. Supports filtering by
#     content, e.g. /api/ai-reviews/?content=3
#     """

#     serializer_class = AIReviewResultSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         user = self.request.user

#         queryset = AIReviewResult.objects.select_related(
#             "content",
#             "content_version",
#         ).all()

#         is_admin_or_editor = (
#             user.is_superuser
#             or user.groups.filter(name__in=["Admin", "Editor"]).exists()
#         )

#         if not is_admin_or_editor:
#             queryset = queryset.filter(
#                 models.Q(content__created_by=user)
#                 | models.Q(content__review_assignments__reviewer=user)
#             ).distinct()

#         content_id = self.request.query_params.get("content")

#         if content_id:
#             queryset = queryset.filter(content_id=content_id)

#         return queryset


from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import models

from .models import AIReviewResult
from .serializers import AIReviewResultSerializer
from .services.writing_assistant import generate_writing_suggestion


class AIReviewResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only list of AI review results. Supports filtering by
    content, e.g. /api/ai-reviews/?content=3
    """

    serializer_class = AIReviewResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = AIReviewResult.objects.select_related(
            "content",
            "content_version",
        ).all()

        is_admin_or_editor = (
            user.is_superuser
            or user.groups.filter(
                name__in=["Admin", "Editor"]
            ).exists()
        )

        if not is_admin_or_editor:
            queryset = queryset.filter(
                models.Q(content__created_by=user)
                | models.Q(
                    content__review_assignments__reviewer=user
                )
            ).distinct()

        content_id = self.request.query_params.get("content")

        if content_id:
            queryset = queryset.filter(
                content_id=content_id
            )

        return queryset


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def writing_suggestion(request):
    """
    Generate an AI writing suggestion for the given content.

    POST /api/ai-suggestion/

    Request:
    {
        "content": "Employees can take leave when they need.",
        "action": "improve"
    }
    """

    content = request.data.get("content")
    action = request.data.get("action", "improve")

    if not content:
        return Response(
            {"error": "Content is required."},
            status=400
        )

    try:
        suggestion = generate_writing_suggestion(
            content,
            action
        )

        return Response({
            "suggestion": suggestion
        })

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=500
        )