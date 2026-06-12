from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.models import AuditLog, Permission, Profile, Role


class LoginSerializer(serializers.Serializer):
    """Validate login input for the authentication API."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class LogoutSerializer(serializers.Serializer):
    """Represent an empty logout request body for API documentation and consistency."""

    pass


class ProfileSerializer(serializers.ModelSerializer):
    """Serialize editable profile fields for user management APIs."""

    class Meta:
        model = Profile
        fields = [
            "full_name",
            "phone",
            "student_number",
            "employee_number",
            "department",
        ]
        extra_kwargs = {"department": {"required": False, "allow_null": True}}


class RoleSerializer(serializers.ModelSerializer):
    """Serialize role records and their permission codes."""

    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["id", "name", "description", "permissions", "created_at"]

    def get_permissions(self, obj):
        """Return assigned permission codes for the role."""
        return list(obj.permissions.order_by("code").values_list("code", flat=True))


class PermissionSerializer(serializers.ModelSerializer):
    """Serialize permission records for RBAC management views."""

    class Meta:
        model = Permission
        fields = ["id", "code", "name", "description"]


class UserReadSerializer(serializers.ModelSerializer):
    """Serialize user accounts with profile and primary role data."""

    role = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_active",
            "role",
            "profile",
            "created_at",
            "updated_at",
        ]

    def get_role(self, obj):
        """Return the primary role assigned to the user."""
        return obj.primary_role()

    def get_profile(self, obj):
        """Return profile data when a profile exists for the user."""
        if hasattr(obj, "profile"):
            return ProfileSerializer(obj.profile).data
        return None


class UserCreateSerializer(serializers.Serializer):
    """Validate account creation data for administrative user management."""

    email = serializers.EmailField()
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    role = serializers.CharField(max_length=80)
    profile = ProfileSerializer(required=False)

    def validate_email(self, value):
        """Prevent duplicate email addresses during account creation."""
        User = get_user_model()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        """Prevent duplicate usernames when a username is provided."""
        if not value:
            return value
        User = get_user_model()
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_role(self, value):
        """Require the requested role to exist before creating the user."""
        if not Role.objects.filter(name=value).exists():
            raise serializers.ValidationError("Requested role does not exist.")
        return value


class UserUpdateSerializer(serializers.Serializer):
    """Validate partial user and profile updates."""

    email = serializers.EmailField(required=False)
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    profile = ProfileSerializer(required=False)

    def validate_email(self, value):
        """Prevent an email update from colliding with another user account."""
        user = self.context.get("user")
        User = get_user_model()
        queryset = User.objects.filter(email=value)
        if user is not None:
            queryset = queryset.exclude(id=user.id)
        if queryset.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        """Prevent a username update from colliding with another user account."""
        user = self.context.get("user")
        if not value:
            return value
        User = get_user_model()
        queryset = User.objects.filter(username=value)
        if user is not None:
            queryset = queryset.exclude(id=user.id)
        if queryset.exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value


class UserRoleUpdateSerializer(serializers.Serializer):
    """Validate role assignment requests for a selected user."""

    role = serializers.CharField(max_length=80)

    def validate_role(self, value):
        """Require the requested role to exist before assigning it to a user."""
        if not Role.objects.filter(name=value).exists():
            raise serializers.ValidationError("Requested role does not exist.")
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    """Serialize audit log events with compact actor and target identifiers."""

    actor_email = serializers.SerializerMethodField()
    target_user_email = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "action",
            "actor_email",
            "target_user_email",
            "metadata",
            "created_at",
        ]

    def get_actor_email(self, obj):
        """Return the actor email when the actor still exists."""
        return obj.actor.email if obj.actor else None

    def get_target_user_email(self, obj):
        """Return the target user email when the target still exists."""
        return obj.target_user.email if obj.target_user else None
