"""Validates and transforms API data for university requests, assignments, statuses, and revisions."""

from rest_framework import serializers

from apps.accounts.models import Role, User
from apps.accounts.serializers import CurrentUserSerializer

from .models import WorkflowHistory, WorkflowRequest, WorkflowType


class WorkflowTypeSerializer(serializers.ModelSerializer):
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

    class Meta:
        model = WorkflowType
        fields = [
            "id",
            "code",
            "name",
            "description",
            "schema",
            "is_active",
            "allowed_role_ids",
            "allowed_roles",
        ]


class WorkflowHistorySerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowHistory
        fields = [
            "id",
            "event",
            "from_status",
            "to_status",
            "note",
            "metadata",
            "actor_name",
            "created_at",
        ]

    def get_actor_name(self, obj):
        if not obj.actor:
            return "System"
        return obj.actor.get_full_name() or obj.actor.username


class WorkflowRequestSerializer(serializers.ModelSerializer):
    request_type_detail = WorkflowTypeSerializer(source="request_type", read_only=True)
    requester_detail = CurrentUserSerializer(source="requester", read_only=True)
    assigned_to_detail = CurrentUserSerializer(source="assigned_to", read_only=True)
    history = WorkflowHistorySerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowRequest
        fields = [
            "id",
            "request_number",
            "request_type",
            "request_type_detail",
            "requester_detail",
            "title",
            "description",
            "payload",
            "status",
            "current_step",
            "assigned_to",
            "assigned_to_detail",
            "decision_reason",
            "version",
            "submitted_at",
            "decided_at",
            "created_at",
            "updated_at",
            "history",
        ]
        read_only_fields = [
            "request_number",
            "status",
            "current_step",
            "assigned_to",
            "decision_reason",
            "version",
            "submitted_at",
            "decided_at",
        ]

    def validate_request_type(self, value):
        request = self.context["request"]
        if not value.is_active:
            raise serializers.ValidationError("This request type is disabled.")
        if (
            value.allowed_roles.exists()
            and not request.user.roles.filter(
                id__in=value.allowed_roles.values_list("id", flat=True)
            ).exists()
        ):
            raise serializers.ValidationError(
                "This request type is not available to your role."
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        workflow_type = attrs.get("request_type") or getattr(
            self.instance, "request_type", None
        )
        payload = attrs.get("payload", getattr(self.instance, "payload", {})) or {}
        schema = workflow_type.schema if workflow_type else {}
        required_fields = []
        if isinstance(schema, dict):
            required_fields.extend(schema.get("required", []))
            required_fields.extend(
                name
                for name, definition in schema.items()
                if isinstance(definition, dict) and definition.get("required") is True
            )
        required_fields = list(dict.fromkeys(required_fields))
        missing = [
            field
            for field in required_fields
            if field not in payload or payload[field] in (None, "", [])
        ]
        if missing:
            raise serializers.ValidationError(
                {"payload": f"Missing required fields: {', '.join(missing)}"}
            )
        return attrs


class WorkflowAssignSerializer(serializers.Serializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True)
    )
    expected_version = serializers.IntegerField(min_value=1)

    def validate_assigned_to(self, value):
        if not value.has_system_permission("workflows.review"):
            raise serializers.ValidationError(
                "The selected user is not permitted to review workflow requests."
            )
        return value


class WorkflowTransitionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=["submit", "start_review", "request_revision", "approve", "reject"]
    )
    note = serializers.CharField(max_length=3000, required=False, allow_blank=True)
    expected_version = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        if (
            attrs["action"] in {"request_revision", "reject"}
            and not attrs.get("note", "").strip()
        ):
            raise serializers.ValidationError(
                {"note": "A reason is required for this action."}
            )
        return attrs
