from django.contrib import admin

from .models import ReviewAssignment


@admin.register(ReviewAssignment)
class ReviewAssignmentAdmin(admin.ModelAdmin):

    list_display = (
        "content",
        "reviewer",
        "assigned_by",
        "status",
        "assigned_at",
    )

    list_filter = (
        "status",
    )