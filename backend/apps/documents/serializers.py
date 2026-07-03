"""Validates and transforms API data for knowledge documents, versions, extraction, and governance."""

from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import Role

from .models import Document, DocumentVersion


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
    last_updated_by = serializers.CharField(
        source="last_updated_by.username", read_only=True, allow_null=True
    )
    review_owner_name = serializers.SerializerMethodField()
    version_count = serializers.IntegerField(read_only=True, required=False)
    is_expired = serializers.SerializerMethodField()
    governance_status = serializers.SerializerMethodField()
    change_summary = serializers.CharField(
        write_only=True, required=False, allow_blank=True, max_length=300
    )

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
            "knowledge_enabled",
            "created_by",
            "last_updated_by",
            "created_at",
            "updated_at",
            "published_at",
            "archived_at",
            "indexed_at",
            "index_version",
            "effective_from",
            "expires_at",
            "review_due_at",
            "review_owner",
            "review_owner_name",
            "tags",
            "version_count",
            "is_expired",
            "governance_status",
            "change_summary",
        ]
        read_only_fields = [
            "created_by",
            "last_updated_by",
            "created_at",
            "updated_at",
            "published_at",
            "archived_at",
            "indexed_at",
            "index_version",
            "version_count",
            "is_expired",
            "governance_status",
            "review_owner_name",
        ]

    def get_review_owner_name(self, obj):
        if not obj.review_owner:
            return None
        return obj.review_owner.get_full_name() or obj.review_owner.username

    def get_is_expired(self, obj):
        return bool(obj.expires_at and obj.expires_at <= timezone.now())

    def get_governance_status(self, obj):
        now = timezone.now()
        if obj.expires_at and obj.expires_at <= now:
            return "expired"
        if obj.review_due_at and obj.review_due_at <= now:
            return "review_overdue"
        if obj.review_due_at and obj.review_due_at <= now + timedelta(days=14):
            return "review_due_soon"
        return "current"

    def validate_tags(self, value):
        if not isinstance(value, list) or any(
            not isinstance(item, str) for item in value
        ):
            raise serializers.ValidationError("Tags must be a list of strings.")
        return list(dict.fromkeys(item.strip()[:40] for item in value if item.strip()))[
            :20
        ]

    def validate_review_owner(self, value):
        if value and not value.has_system_permission("documents.manage"):
            raise serializers.ValidationError(
                "Review owner must be a document manager."
            )
        return value

    def validate(self, attrs):
        access_level = attrs.get(
            "access_level", getattr(self.instance, "access_level", None)
        )
        roles = attrs.get(
            "allowed_roles",
            list(self.instance.allowed_roles.all()) if self.instance else [],
        )
        if access_level == Document.AccessLevel.ROLE and not roles:
            raise serializers.ValidationError(
                {
                    "allowed_role_ids": "At least one role is required for role-restricted documents."
                }
            )
        if access_level != Document.AccessLevel.ROLE and "allowed_roles" in attrs:
            attrs["allowed_roles"] = []
        effective = attrs.get(
            "effective_from", getattr(self.instance, "effective_from", None)
        )
        expires = attrs.get("expires_at", getattr(self.instance, "expires_at", None))
        if effective and expires and expires <= effective:
            raise serializers.ValidationError(
                {"expires_at": "Expiry must be after the effective date."}
            )
        return attrs


class DocumentVersionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DocumentVersion
        fields = [
            "id",
            "version_number",
            "snapshot",
            "content_checksum",
            "change_summary",
            "created_by_name",
            "created_at",
        ]

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return "System"
        return obj.created_by.get_full_name() or obj.created_by.username
