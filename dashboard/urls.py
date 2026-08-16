from django.urls import path

from .views import (
    dashboard,
    review_content,
    content_list,
    content_create,
    content_edit,
    content_diff,
    login_view,
    register_view,
    logout_view,
    verify_email_view,
)


urlpatterns = [
    path(
        "login/",
        login_view,
        name="login",
    ),

    path(
        "register/",
        register_view,
        name="register",
    ),

    path(
        "verify/<uuid:token>/",
        verify_email_view,
        name="verify-email",
    ),

    path(
        "logout/",
        logout_view,
        name="logout",
    ),

    path(
        "",
        dashboard,
        name="dashboard",
    ),

    path(
        "review/<int:content_id>/",
        review_content,
        name="review-content",
    ),

    path(
        "content/",
        content_list,
        name="content_list",
    ),

    path(
        "content/new/",
        content_create,
        name="content_create",
    ),

    path(
        "content/<int:content_id>/edit/",
        content_edit,
        name="content_edit",
    ),

    path(
        "content/<int:content_id>/diff/",
        content_diff,
        name="content_diff",
    ),
]