from rest_framework.routers import DefaultRouter

from .views import ReviewAssignmentViewSet


router = DefaultRouter()

router.register(
    r"review-assignments",
    ReviewAssignmentViewSet,
    basename="review-assignment",
)

urlpatterns = router.urls