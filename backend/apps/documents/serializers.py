from rest_framework import serializers

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
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Document title cannot be empty.")
        return cleaned
