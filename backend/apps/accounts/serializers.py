"""Validates and transforms API data for user accounts, roles, permissions, and authentication."""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Department, Permission, Profile, Role, User


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "code", "name", "description"]


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = ["id", "name", "description", "permissions", "is_system"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "code", "is_active"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "phone",
            "student_number",
            "employee_number",
            "bio",
            "avatar_url",
            "job_title",
            "office_location",
            "website",
            "preferred_language",
            "timezone",
            "emergency_contact",
        ]


class CurrentUserSerializer(serializers.ModelSerializer):
    roles = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)
    profile = ProfileSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    permissions = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
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
            .order_by("code")
        )

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=False, max_length=254)
    username = serializers.CharField(required=False, max_length=254)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        identifier = (
            attrs.get("identifier") or attrs.get("username") or attrs.get("email")
        )
        if not identifier:
            raise serializers.ValidationError(
                {"identifier": "Username or email is required."}
            )
        attrs["identifier"] = identifier
        attrs.pop("username", None)
        attrs.pop("email", None)
        return attrs


class TokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(trim_whitespace=False)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(
        write_only=True, validators=[validate_password]
    )


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    role_ids = serializers.PrimaryKeyRelatedField(
        source="roles_input",
        queryset=Role.objects.all(),
        many=True,
        required=True,
        allow_empty=False,
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
        value = value.strip().lower()
        qs = User.objects.filter(email__iexact=value)
        if qs.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        value = value.strip()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already in use.")
        return value

    def validate(self, attrs):
        roles = attrs.get("roles_input", [])
        profile = dict(attrs.get("profile", {}))
        role_names = {role.name for role in roles}

        candidate = User(
            username=attrs.get("username", ""),
            email=attrs.get("email", ""),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )
        validate_password(attrs.get("password", ""), user=candidate)

        student_number = str(profile.get("student_number", "")).strip()
        employee_number = str(profile.get("employee_number", "")).strip()
        if Role.STUDENT in role_names and not student_number:
            raise serializers.ValidationError(
                {
                    "profile": {
                        "student_number": "Student number is required for a student account."
                    }
                }
            )
        if (
            student_number
            and Profile.objects.filter(student_number__iexact=student_number).exists()
        ):
            raise serializers.ValidationError(
                {
                    "profile": {
                        "student_number": "This student number is already in use."
                    }
                }
            )
        if (
            employee_number
            and Profile.objects.filter(employee_number__iexact=employee_number).exists()
        ):
            raise serializers.ValidationError(
                {
                    "profile": {
                        "employee_number": "This employee number is already in use."
                    }
                }
            )

        profile["student_number"] = student_number
        profile["employee_number"] = employee_number
        attrs["profile"] = profile
        return attrs

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

    def validate_email(self, value):
        value = value.strip().lower()
        qs = User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)
        was_active = instance.is_active
        instance = super().update(instance, validated_data)
        if not was_active and instance.is_active:
            instance.deactivated_at = None
            instance.save(update_fields=["deactivated_at", "updated_at"])
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


class RoleUpdateSerializer(serializers.ModelSerializer):
    permission_ids = serializers.PrimaryKeyRelatedField(
        source="permissions",
        queryset=Permission.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = Role
        fields = ["description", "permission_ids"]
