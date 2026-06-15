from rest_framework import serializers
from .models import Question, QuestionHistory, QuestionResponse

class QuestionResponseSerializer(serializers.ModelSerializer):
    sources = serializers.SerializerMethodField()
    class Meta:
        model = QuestionResponse
        fields = ["answer", "confidence", "provider", "model_name", "is_documented", "sources", "created_at", "updated_at"]
    def get_sources(self, obj):
        return [{"id": d.id, "title": d.title, "document_type": d.document_type, "updated_at": d.updated_at} for d in obj.sources.all()]

class QuestionSerializer(serializers.ModelSerializer):
    response = QuestionResponseSerializer(read_only=True)
    user = serializers.CharField(source="user.username", read_only=True)
    class Meta:
        model = Question
        fields = ["id", "user", "text", "status", "category", "priority", "analysis_confidence", "suggested_workflow", "error_message", "response", "created_at", "updated_at", "processed_at"]
        read_only_fields = ["status", "category", "priority", "analysis_confidence", "suggested_workflow", "error_message", "processed_at"]

class QuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "text"]
    def validate_text(self, value):
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError("Question must contain at least 5 characters.")
        return value

class QuestionHistorySerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source="actor.username", allow_null=True, read_only=True)
    class Meta:
        model = QuestionHistory
        fields = ["id", "event", "from_status", "to_status", "actor", "metadata", "created_at"]

class AnalyzeRequestSerializer(serializers.Serializer):
    text = serializers.CharField(min_length=3, max_length=5000)
