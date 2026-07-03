"""Orchestrates grounded answers, escalation, citations, and audit metadata."""

from abc import ABC, abstractmethod
import time

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .adapters import AIProviderFactory
from .exceptions import AIServiceUnavailable
from .models import Question, QuestionResponse
from .observers import QuestionEvent, QuestionEventPublisher
from .prompting import PromptBuilder
from .retrieval import RetrievalStrategyFactory, document_context


class AnswerGenerationTemplate(ABC):
    """Template Method defining the invariant RAG answer-generation algorithm."""

    def execute(self, question, actor):
        started = time.monotonic()
        documents = self.retrieve_documents(question)
        prompt = self.build_prompt(question, documents)
        ai_answer = self.call_provider(question, prompt, documents)
        latency_ms = int((time.monotonic() - started) * 1000)
        return self.persist(question, actor, documents, ai_answer, latency_ms)

    @abstractmethod
    def retrieve_documents(self, question): ...

    @abstractmethod
    def build_prompt(self, question, documents): ...

    @abstractmethod
    def call_provider(self, question, prompt, documents): ...

    @abstractmethod
    def persist(self, question, actor, documents, ai_answer, latency_ms): ...


class DocumentedAnswerWorkflow(AnswerGenerationTemplate):
    def __init__(self, provider=None, retrieval=None):
        self.provider = provider
        self.retrieval = retrieval or RetrievalStrategyFactory.create()

    def retrieve_documents(self, question):
        return self.retrieval.retrieve(question.user, question.text)

    def build_prompt(self, question, documents):
        return (
            PromptBuilder()
            .with_policy()
            .with_user_role(question.user.role_names)
            .with_question(question.text)
            .with_documents(documents)
            .build()
        )

    def call_provider(self, question, prompt, documents):
        if not documents:
            from .adapters import AIAnswer

            return AIAnswer(
                "I could not find an authorized university document that reliably answers this question. The request has been escalated for human review.",
                0.0,
                "retrieval-guard",
                "rag-v2",
            )
        provider = self.provider or AIProviderFactory.create()
        return provider.answer(
            question=question.text, prompt=prompt, documents=documents
        )

    @transaction.atomic
    def persist(self, question, actor, documents, ai_answer, latency_ms):
        locked = Question.objects.select_for_update().get(pk=question.pk)
        old_status = locked.status
        target_status = Question.Status.ANSWERED
        if not documents or ai_answer.confidence < settings.AI_CONFIDENCE_THRESHOLD:
            target_status = Question.Status.ESCALATED
        response, _ = QuestionResponse.objects.update_or_create(
            question=locked,
            defaults={
                "answer": ai_answer.answer,
                "confidence": ai_answer.confidence,
                "provider": ai_answer.provider,
                "model_name": ai_answer.model_name,
                "is_documented": bool(documents),
                "citations": [
                    {
                        "document_id": d.id,
                        "title": d.title,
                        "index_version": d.index_version,
                        "updated_at": d.updated_at.isoformat(),
                        "excerpt": " ".join(document_context(d).split())[:500],
                    }
                    for d in documents
                ],
                "retrieval_metadata": {
                    "strategy": getattr(settings, "AI_RETRIEVAL_STRATEGY", "hybrid"),
                    "candidate_count": len(documents),
                    "threshold": settings.AI_CONFIDENCE_THRESHOLD,
                },
                "safety_status": "grounded" if documents else "escalated_no_source",
                "latency_ms": latency_ms,
            },
        )
        response.sources.set(documents)
        locked.status = target_status
        locked.error_message = ""
        locked.processed_at = timezone.now()
        locked.save(
            update_fields=["status", "error_message", "processed_at", "updated_at"]
        )
        QuestionEventPublisher.publish(
            QuestionEvent(
                question=locked,
                event="answer_generated",
                actor=actor,
                from_status=old_status,
                to_status=target_status,
                metadata={
                    "confidence": ai_answer.confidence,
                    "source_ids": [d.id for d in documents],
                },
            )
        )
        question.refresh_from_db()
        return response


class GenerateAnswerCommand:
    def __init__(self, question, actor, workflow=None):
        self.question = question
        self.actor = actor
        self.workflow = workflow or DocumentedAnswerWorkflow()

    def execute(self):
        try:
            return self.workflow.execute(self.question, self.actor)
        except AIServiceUnavailable:
            with transaction.atomic():
                locked = Question.objects.select_for_update().get(pk=self.question.pk)
                old_status = locked.status
                locked.status = Question.Status.FAILED
                locked.error_message = "AI service unavailable"
                locked.processed_at = timezone.now()
                locked.save(
                    update_fields=[
                        "status",
                        "error_message",
                        "processed_at",
                        "updated_at",
                    ]
                )
                QuestionEventPublisher.publish(
                    QuestionEvent(
                        question=locked,
                        event="answer_failed",
                        actor=self.actor,
                        from_status=old_status,
                        to_status=Question.Status.FAILED,
                        metadata={"reason": "ai_service_unavailable"},
                    )
                )
            self.question.refresh_from_db()
            raise
