"""Contains reusable business logic for grounded question answering, retrieval, and AI orchestration."""

from django.db import transaction
from django.utils import timezone

from .analysis import KeywordRequestAnalysisStrategy
from .models import Question, QuestionResponse
from .observers import QuestionEvent, QuestionEventPublisher


class QuestionService:
    @staticmethod
    @transaction.atomic
    def create(*, user, text):
        analysis = KeywordRequestAnalysisStrategy().analyze(text)
        question = Question.objects.create(
            user=user,
            text=text,
            category=analysis.category,
            priority=analysis.priority,
            analysis_confidence=analysis.confidence,
            suggested_workflow=analysis.suggested_workflow,
        )
        QuestionEventPublisher.publish(
            QuestionEvent(
                question=question,
                event="submitted",
                actor=user,
                to_status=Question.Status.PENDING,
                metadata={"category": analysis.category, "priority": analysis.priority},
            )
        )
        return question

    @staticmethod
    @transaction.atomic
    def human_answer(*, question, actor, answer, sources=None):
        locked = Question.objects.select_for_update().get(pk=question.pk)
        old_status = locked.status
        response, _ = QuestionResponse.objects.update_or_create(
            question=locked,
            defaults={
                "answer": answer,
                "confidence": 1.0,
                "provider": "human-review",
                "model_name": "staff",
                "is_documented": bool(sources),
            },
        )
        response.sources.set(sources or [])
        locked.status = Question.Status.ANSWERED
        locked.processed_at = timezone.now()
        locked.error_message = ""
        locked.save(
            update_fields=["status", "processed_at", "error_message", "updated_at"]
        )
        QuestionEventPublisher.publish(
            QuestionEvent(
                question=locked,
                event="human_answered",
                actor=actor,
                from_status=old_status,
                to_status=Question.Status.ANSWERED,
                metadata={"source_ids": [d.pk for d in sources or []]},
            )
        )
        question.refresh_from_db()
        return response
