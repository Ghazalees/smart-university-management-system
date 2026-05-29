from rest_framework import serializers

from apps.core.validators import normalize_keyword, validate_max_length, validate_non_empty_string
from apps.documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    """Serialize document records for document-management APIs."""

    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "document_type",
            "access_level",
            "content",
            "is_active",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_by_email", "created_at", "updated_at"]

    def validate_title(self, value):
        """Reject empty or whitespace-only document titles."""
        cleaned = validate_non_empty_string(value, "Document title")
        return validate_max_length(cleaned, 255, "Document title")

    def validate_content(self, value):
        """Normalize optional document content."""
        return value.strip() if isinstance(value, str) else value


class DocumentQuerySerializer(serializers.Serializer):
    """Validate query parameters for document list/search endpoints."""

    keyword = serializers.CharField(required=False, allow_blank=True, max_length=120)
    document_type = serializers.ChoiceField(
        choices=Document.DocumentType.choices,
        required=False,
    )
    access_level = serializers.ChoiceField(
        choices=Document.AccessLevel.choices,
        required=False,
    )

    def validate_keyword(self, value):
        return normalize_keyword(value)
