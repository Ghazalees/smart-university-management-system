from abc import ABC, abstractmethod

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .adapters import AIProviderFactory
from .exceptions import AIServiceUnavailable
from .models import Question, QuestionResponse
from .observers import QuestionEvent, QuestionEventPublisher
from .prompting import PromptBuilder
from .retrieval import KeywordKnowledgeRetrievalStrategy


class AnswerGenerationTemplate(ABC):
    """Template Method defining the invariant answer-generation algorithm."""

    def execute(self, question, actor):
        documents = self.retrieve_documents(question)
        prompt = self.build_prompt(question, documents)
        ai_answer = self.call_provider(question, prompt, documents)
        return self.persist(question, actor, documents, ai_answer)

    @abstractmethod
    def retrieve_documents(self, question): ...
    @abstractmethod
    def build_prompt(self, question, documents): ...
    @abstractmethod
    def call_provider(self, question, prompt, documents): ...
    @abstractmethod
    def persist(self, question, actor, documents, ai_answer): ...


class DocumentedAnswerWorkflow(AnswerGenerationTemplate):
    def __init__(self, provider=None, retrieval=None):
        self.provider = provider or AIProviderFactory.create()
        self.retrieval = retrieval or KeywordKnowledgeRetrievalStrategy()

    def retrieve_documents(self, question):
        return self.retrieval.retrieve(question.user, question.text)

    def build_prompt(self, question, documents):
        return (
            PromptBuilder()
            .with_policy()
            .with_question(question.text)
            .with_documents(documents)
            .build()
        )

    def call_provider(self, question, prompt, documents):
        return self.provider.answer(
            question=question.text, prompt=prompt, documents=documents
        )

    @transaction.atomic
    def persist(self, question, actor, documents, ai_answer):
        old_status = question.status
        target_status = Question.Status.ANSWERED
        if not documents or ai_answer.confidence < settings.AI_CONFIDENCE_THRESHOLD:
            target_status = Question.Status.ESCALATED
        response, _ = QuestionResponse.objects.update_or_create(
            question=question,
            defaults={
                "answer": ai_answer.answer,
                "confidence": ai_answer.confidence,
                "provider": ai_answer.provider,
                "model_name": ai_answer.model_name,
                "is_documented": bool(documents),
            },
        )
        response.sources.set(documents)
        question.status = target_status
        question.error_message = ""
        question.processed_at = timezone.now()
        question.save(
            update_fields=["status", "error_message", "processed_at", "updated_at"]
        )
        QuestionEventPublisher.publish(
            QuestionEvent(
                question=question,
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
        return response


class GenerateAnswerCommand:
    """Command pattern encapsulating the answer use case."""

    def __init__(self, question, actor, workflow=None):
        self.question = question
        self.actor = actor
        self.workflow = workflow or DocumentedAnswerWorkflow()

    def execute(self):
        try:
            return self.workflow.execute(self.question, self.actor)
        except AIServiceUnavailable:
            old_status = self.question.status
            self.question.status = Question.Status.FAILED
            self.question.error_message = "AI service unavailable"
            self.question.processed_at = timezone.now()
            self.question.save(
                update_fields=["status", "error_message", "processed_at", "updated_at"]
            )
            QuestionEventPublisher.publish(
                QuestionEvent(
                    question=self.question,
                    event="answer_failed",
                    actor=self.actor,
                    from_status=old_status,
                    to_status=Question.Status.FAILED,
                    metadata={"reason": "ai_service_unavailable"},
                )
            )
            raise
