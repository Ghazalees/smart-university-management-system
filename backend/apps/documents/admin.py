from django.contrib import admin

from apps.documents.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "document_type", "access_level", "is_active", "created_by", "created_at")
    list_filter = ("document_type", "access_level", "is_active")
    search_fields = ("title", "content")
    readonly_fields = ("created_at", "updated_at")
