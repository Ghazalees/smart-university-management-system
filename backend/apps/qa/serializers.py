from rest_framework import serializers

from apps.accounts.services import AuthFacade
from apps.qa.models import Question, QuestionHistory, QuestionResponse


class QuestionCreateSerializer(serializers.Serializer):
    """Validate question submission input."""

    title = serializers.CharField(max_length=180)
    body = serializers.CharField()
    category = serializers.CharField(max_length=80, required=False, allow_blank=True)


class QuestionResponseReadSerializer(serializers.ModelSerializer):
    """Serialize stored responses for a question."""

    responder = serializers.SerializerMethodField()

    class Meta:
        model = QuestionResponse
        fields = ["id", "body", "confidence", "source_documents", "responder", "created_at"]

    def get_responder(self, obj):
        """Return safe responder identity data when a responder exists."""
        return AuthFacade.user_payload(obj.responder) if obj.responder else None


class QuestionReadSerializer(serializers.ModelSerializer):
    """Serialize questions with submitter and latest response data."""

    submitted_by = serializers.SerializerMethodField()
    latest_response = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "body",
            "category",
            "status",
            "submitted_by",
            "latest_response",
            "created_at",
            "updated_at",
        ]

    def get_submitted_by(self, obj):
        """Return safe submitter identity data."""
        return AuthFacade.user_payload(obj.submitted_by)

    def get_latest_response(self, obj):
        """Return the newest response attached to the question."""
        response = obj.responses.order_by("-created_at").first()
        if response is None:
            return None
        return QuestionResponseReadSerializer(response).data


class QuestionAnswerSerializer(serializers.Serializer):
    """Validate question answer and status update input."""

    body = serializers.CharField()
    status = serializers.ChoiceField(
        choices=[Question.STATUS_ANSWERED, Question.STATUS_ESCALATED, Question.STATUS_FAILED],
        default=Question.STATUS_ANSWERED,
    )
    confidence = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    source_documents = serializers.JSONField(required=False)
    note = serializers.CharField(required=False, allow_blank=True)

    def validate_source_documents(self, value):
        """Require source documents to be a list when provided."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Source documents must be a list.")
        return value


class QuestionHistorySerializer(serializers.ModelSerializer):
    """Serialize question processing history events."""

    actor = serializers.SerializerMethodField()

    class Meta:
        model = QuestionHistory
        fields = ["id", "event", "status_from", "status_to", "note", "actor", "created_at"]

    def get_actor(self, obj):
        """Return safe actor identity data when an actor exists."""
        return AuthFacade.user_payload(obj.actor) if obj.actor else None
