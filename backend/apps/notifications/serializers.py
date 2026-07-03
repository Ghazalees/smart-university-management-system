"""Validates and transforms API data for notification delivery and notification-center state."""

from rest_framework import serializers

from apps.accounts.models import Role, User

from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()
    is_pinned = serializers.SerializerMethodField()
    is_snoozed = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "category",
            "priority",
            "link",
            "metadata",
            "is_read",
            "read_at",
            "is_pinned",
            "pinned_at",
            "is_snoozed",
            "snoozed_until",
            "created_at",
        ]

    def get_is_read(self, obj):
        return obj.read_at is not None

    def get_is_pinned(self, obj):
        return obj.pinned_at is not None

    def get_is_snoozed(self, obj):
        from django.utils import timezone

        return bool(obj.snoozed_until and obj.snoozed_until > timezone.now())


class NotificationCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=180)
    message = serializers.CharField(max_length=3000)
    category = serializers.ChoiceField(choices=Notification.Category.choices)
    priority = serializers.ChoiceField(
        choices=["low", "normal", "high", "urgent"], default="normal"
    )
    link = serializers.CharField(max_length=300, required=False, allow_blank=True)
    recipient_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True), many=True, required=False
    )
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), many=True, required=False
    )

    def validate(self, attrs):
        if not attrs.get("recipient_ids") and not attrs.get("role_ids"):
            raise serializers.ValidationError(
                "At least one recipient or role must be selected."
            )
        return attrs


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "enabled_categories",
            "in_app_enabled",
            "email_enabled",
            "quiet_hours_start",
            "quiet_hours_end",
            "muted_until",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate_enabled_categories(self, value):
        valid = {choice[0] for choice in Notification.Category.choices}
        if not isinstance(value, list) or any(item not in valid for item in value):
            raise serializers.ValidationError(
                "One or more notification categories are invalid."
            )
        return list(dict.fromkeys(value))


class NotificationActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=["pin", "unpin", "snooze", "unsnooze", "read", "unread"]
    )
    snoozed_until = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        if attrs["action"] == "snooze" and not attrs.get("snoozed_until"):
            raise serializers.ValidationError(
                {"snoozed_until": "A snooze time is required."}
            )
        return attrs
