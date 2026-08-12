from rest_framework.routers import DefaultRouter

from .views import AIReviewResultViewSet


router = DefaultRouter()

router.register(
    r"ai-reviews",
    AIReviewResultViewSet,
    basename="ai-review",
)

urlpatterns = router.urls