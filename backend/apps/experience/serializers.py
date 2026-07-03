"""Validates and transforms API data for user experience preferences, feedback, search, and calendar features."""

from rest_framework import serializers

from apps.accounts.models import User

from .models import Feedback, UserExperiencePreference


class UserExperiencePreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserExperiencePreference
        fields = [
            "accent_color",
            "density",
            "reduced_motion",
            "high_contrast",
            "language",
            "dashboard_layout",
            "onboarding_completed",
            "digest_frequency",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate_accent_color(self, value):
        allowed = {"indigo", "violet", "emerald", "coral", "amber", "rose", "cyan"}
        if value not in allowed:
            raise serializers.ValidationError("Unsupported accent color.")
        return value


class FeedbackSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            "id",
            "feedback_type",
            "title",
            "message",
            "page",
            "rating",
            "metadata",
            "status",
            "created_by_name",
            "assigned_to",
            "assigned_to_name",
            "admin_note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "status",
            "created_by_name",
            "assigned_to",
            "assigned_to_name",
            "admin_note",
            "created_at",
            "updated_at",
        ]

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username

    def get_assigned_to_name(self, obj):
        if not obj.assigned_to:
            return None
        return obj.assigned_to.get_full_name() or obj.assigned_to.username

    def validate_rating(self, value):
        if value is not None and not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class FeedbackManageSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True), required=False, allow_null=True
    )

    class Meta:
        model = Feedback
        fields = ["status", "assigned_to", "admin_note"]
