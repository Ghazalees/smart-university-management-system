from rest_framework import serializers

from apps.core.validators import (
    normalize_keyword,
    validate_max_length,
    validate_non_empty_string,
)
from apps.documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    """Serialize document records for document-management APIs."""

    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)
    last_updated_by_email = serializers.EmailField(
        source="last_updated_by.email",
        read_only=True,
    )
    archived_by_email = serializers.EmailField(source="archived_by.email", read_only=True)
    last_updated_at = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "document_type",
            "access_level",
            "content",
            "summary",
            "keywords",
            "is_knowledge_base_enabled",
            "version",
            "is_active",
            "created_by",
            "created_by_email",
            "last_updated_by",
            "last_updated_by_email",
            "archived_by",
            "archived_by_email",
            "archived_at",
            "created_at",
            "updated_at",
            "last_updated_at",
        ]
        read_only_fields = [
            "id",
            "version",
            "is_active",
            "created_by",
            "created_by_email",
            "last_updated_by",
            "last_updated_by_email",
            "archived_by",
            "archived_by_email",
            "archived_at",
            "created_at",
            "updated_at",
            "last_updated_at",
        ]

    def validate_title(self, value):
        """Reject empty or whitespace-only document titles."""
        cleaned = validate_non_empty_string(value, "Document title")
        return validate_max_length(cleaned, 255, "Document title")

    def validate_content(self, value):
        """Normalize optional document content."""
        return value.strip() if isinstance(value, str) else value

    def validate_summary(self, value):
        """Normalize optional knowledge-base summary."""
        return value.strip() if isinstance(value, str) else value

    def validate_keywords(self, value):
        """Normalize comma-separated search/AI keywords."""
        if not isinstance(value, str):
            return value
        keywords = [item.strip() for item in value.split(",") if item.strip()]
        return ", ".join(dict.fromkeys(keywords))


class DocumentQuerySerializer(serializers.Serializer):
    """Validate query parameters for document list/search endpoints."""

    keyword = serializers.CharField(required=False, allow_blank=True, max_length=120)
    title = serializers.CharField(required=False, allow_blank=True, max_length=120)
    document_type = serializers.ChoiceField(
        choices=Document.DocumentType.choices,
        required=False,
    )
    access_level = serializers.ChoiceField(
        choices=Document.AccessLevel.choices,
        required=False,
    )
    knowledge_base_only = serializers.BooleanField(required=False, default=False)

    def validate_keyword(self, value):
        return normalize_keyword(value)

    def validate_title(self, value):
        return normalize_keyword(value)
