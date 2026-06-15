from django.db import transaction
from .analysis import KeywordRequestAnalysisStrategy
from .models import Question
from .observers import QuestionEvent, QuestionEventPublisher

class QuestionService:
    @staticmethod
    @transaction.atomic
    def create(*, user, text):
        analysis = KeywordRequestAnalysisStrategy().analyze(text)
        question = Question.objects.create(
            user=user, text=text, category=analysis.category, priority=analysis.priority,
            analysis_confidence=analysis.confidence, suggested_workflow=analysis.suggested_workflow,
        )
        QuestionEventPublisher.publish(QuestionEvent(
            question=question, event="submitted", actor=user,
            to_status=Question.Status.PENDING,
            metadata={"category": analysis.category, "priority": analysis.priority},
        ))
        return question
