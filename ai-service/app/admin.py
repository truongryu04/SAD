from django.contrib import admin

from .models import AIRequest


@admin.register(AIRequest)
class AIRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "model_name", "status", "created_at")
    search_fields = ("prompt", "response", "model_name")
    list_filter = ("status", "model_name")
