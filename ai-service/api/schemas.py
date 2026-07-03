"""Defines validated request and response models for the AI service API."""

from pydantic import BaseModel, Field


class ContextDocument(BaseModel):
    id: int
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=12000)


class AnswerRequest(BaseModel):
    question: str = Field(min_length=3, max_length=5000)
    prompt: str = Field(min_length=3, max_length=60000)
    documents: list[ContextDocument] = Field(default_factory=list, max_length=10)


class AnswerResponse(BaseModel):
    answer: str
    confidence: float = Field(ge=0, le=1)
    provider: str
    model_name: str = ""


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=3, max_length=5000)


class AnalyzeResponse(BaseModel):
    category: str
    priority: str
    confidence: float = Field(ge=0, le=1)
    suggested_workflow: str
    source: str
