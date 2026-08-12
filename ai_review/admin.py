from django.contrib import admin

from .models import AIReviewResult


@admin.register(AIReviewResult)
class AIReviewResultAdmin(admin.ModelAdmin):
    list_display = ("content", "status", "score", "created_at")
    list_filter = ("status",)