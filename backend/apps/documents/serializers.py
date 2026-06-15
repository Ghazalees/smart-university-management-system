from rest_framework import serializers

from apps.accounts.models import Role

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    allowed_role_ids = serializers.PrimaryKeyRelatedField(
        source="allowed_roles",
        queryset=Role.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )
    allowed_roles = serializers.SlugRelatedField(
        slug_field="name", many=True, read_only=True
    )
    created_by = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "document_type",
            "content",
            "access_level",
            "allowed_role_ids",
            "allowed_roles",
            "status",
            "created_by",
            "created_at",
            "updated_at",
            "archived_at",
        ]
        read_only_fields = [
            "status",
            "created_by",
            "created_at",
            "updated_at",
            "archived_at",
        ]

    def validate(self, attrs):
        access_level = attrs.get(
            "access_level", getattr(self.instance, "access_level", None)
        )
        roles = attrs.get("allowed_roles")
        if (
            access_level == Document.AccessLevel.ROLE
            and self.instance is None
            and not roles
        ):
            raise serializers.ValidationError(
                {
                    "allowed_role_ids": "At least one role is required for role-restricted documents."
                }
            )
        return attrs
