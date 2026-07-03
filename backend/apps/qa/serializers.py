"""Validates and transforms API data for grounded question answering, retrieval, and AI orchestration."""

from rest_framework import serializers

from apps.documents.models import Document

from .models import Question, QuestionHistory, QuestionResponse
from .security import PromptSecurityPolicy, TextNormalizer


class QuestionResponseSerializer(serializers.ModelSerializer):
    sources = serializers.SerializerMethodField()

    class Meta:
        model = QuestionResponse
        fields = [
            "answer",
            "confidence",
            "provider",
            "model_name",
            "is_documented",
            "sources",
            "citations",
            "retrieval_metadata",
            "safety_status",
            "latency_ms",
            "user_rating",
            "user_feedback",
            "created_at",
            "updated_at",
        ]

    def get_sources(self, obj):
        from django.utils import timezone

        citation_excerpts = {
            item.get("document_id"): item.get("excerpt", "")
            for item in (obj.citations or [])
            if isinstance(item, dict)
        }
        return [
            {
                "id": d.id,
                "title": d.title,
                "document_type": d.document_type,
                "updated_at": d.updated_at,
                "index_version": d.index_version,
                "effective_from": d.effective_from,
                "expires_at": d.expires_at,
                "is_expired": bool(d.expires_at and d.expires_at <= timezone.now()),
                "excerpt": citation_excerpts.get(d.id)
                or " ".join(d.content.split())[:260],
                "url": f"/documents/{d.id}",
            }
            for d in obj.sources.all()
        ]


class QuestionSerializer(serializers.ModelSerializer):
    response = QuestionResponseSerializer(read_only=True)
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "user",
            "text",
            "status",
            "category",
            "priority",
            "analysis_confidence",
            "suggested_workflow",
            "error_message",
            "response",
            "created_at",
            "updated_at",
            "processed_at",
        ]
        read_only_fields = [
            "status",
            "category",
            "priority",
            "analysis_confidence",
            "suggested_workflow",
            "error_message",
            "processed_at",
        ]


class QuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "text"]

    def validate_text(self, value):
        value = TextNormalizer.normalize(value)
        if len(value) < 5:
            raise serializers.ValidationError(
                "Question must contain at least 5 characters."
            )
        if len(value) > 5000:
            raise serializers.ValidationError("Question cannot exceed 5000 characters.")
        PromptSecurityPolicy.validate(value)
        return value


class HumanAnswerSerializer(serializers.Serializer):
    answer = serializers.CharField(min_length=3, max_length=12000)
    source_ids = serializers.PrimaryKeyRelatedField(
        source="sources",
        queryset=Document.objects.all(),
        many=True,
        required=False,
    )


class QuestionHistorySerializer(serializers.ModelSerializer):
    actor = serializers.CharField(
        source="actor.username", allow_null=True, read_only=True
    )

    class Meta:
        model = QuestionHistory
        fields = [
            "id",
            "event",
            "from_status",
            "to_status",
            "actor",
            "metadata",
            "created_at",
        ]


class AnalyzeRequestSerializer(serializers.Serializer):
    text = serializers.CharField(min_length=3, max_length=5000)

    def validate_text(self, value):
        value = TextNormalizer.normalize(value)
        PromptSecurityPolicy.validate(value)
        return value


class AIResponseFeedbackSerializer(serializers.Serializer):
    rating = serializers.ChoiceField(choices=[-1, 1])
    comment = serializers.CharField(max_length=2000, required=False, allow_blank=True)
