from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Permission, Profile, Role, User


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SlugRelatedField(
        slug_field="code", many=True, read_only=True
    )

    class Meta:
        model = Role
        fields = ["id", "name", "description", "permissions"]


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "code", "name", "description"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["phone", "student_number", "employee_number", "bio"]


class CurrentUserSerializer(serializers.ModelSerializer):
    roles = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)
    profile = ProfileSerializer(read_only=True)
    department = serializers.SlugRelatedField(slug_field="code", read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "department",
            "roles",
            "permissions",
            "profile",
            "is_active",
        ]

    def get_permissions(self, obj):
        if obj.is_superuser:
            return ["*"]
        return list(
            Permission.objects.filter(roles__users=obj)
            .values_list("code", flat=True)
            .distinct()
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role_ids = serializers.PrimaryKeyRelatedField(
        source="roles_input",
        queryset=Role.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "department",
            "role_ids",
            "profile",
        ]

    def validate_email(self, value):
        return value.lower()

    def create(self, validated_data):
        from .services import UserFactory

        roles = validated_data.pop("roles_input", [])
        profile_data = validated_data.pop("profile", {})
        return UserFactory.create(
            actor=self.context["request"].user,
            request=self.context["request"],
            role_names=[role.name for role in roles],
            profile=profile_data,
            **validated_data,
        )


class UserListSerializer(CurrentUserSerializer):
    class Meta(CurrentUserSerializer.Meta):
        fields = CurrentUserSerializer.Meta.fields + ["date_joined", "deactivated_at"]


class UserUpdateSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "department",
            "is_active",
            "profile",
        ]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)
        instance = super().update(instance, validated_data)
        if profile_data is not None:
            profile, _ = Profile.objects.get_or_create(user=instance)
            for key, value in profile_data.items():
                setattr(profile, key, value)
            profile.save()
        return instance


class RoleAssignmentSerializer(serializers.Serializer):
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), many=True
    )
