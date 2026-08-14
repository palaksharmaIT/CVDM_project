from django.urls import path

from .views import dashboard, review_content


urlpatterns = [
    path("", dashboard, name="dashboard"),

    path(
        "review/<int:content_id>/",
        review_content,
        name="review-content",
    ),
]