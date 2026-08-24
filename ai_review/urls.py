# from rest_framework.routers import DefaultRouter

# from .views import AIReviewResultViewSet


# router = DefaultRouter()

# router.register(
#     r"ai-reviews",
#     AIReviewResultViewSet,
#     basename="ai-review",
# )

# urlpatterns = router.urls

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AIReviewResultViewSet,
    writing_suggestion,
)

router = DefaultRouter()

router.register(
    r"ai-reviews",
    AIReviewResultViewSet,
    basename="ai-review",
)

urlpatterns = router.urls + [
    path(
        "ai-suggestion/",
        writing_suggestion,
        name="ai-suggestion",
    ),
]