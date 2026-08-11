from django.contrib import admin

from .models import ContentVersion


@admin.register(ContentVersion)
class ContentVersionAdmin(admin.ModelAdmin):
    list_display = (
        "content",
        "version_number",
        "change_note",
        "created_by",
        "created_at",
        "is_published",
    )

    list_filter = (
        "is_published",
        "created_at",
    )

    search_fields = (
        "content__title",
        "change_note",
        "created_by__username",
    )

    ordering = (
        "content",
        "-version_number",
    )