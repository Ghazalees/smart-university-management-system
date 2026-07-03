"""Configures the FastAPI application, middleware, health checks, and AI endpoints."""

from fastapi import Depends, FastAPI

from .analysis import RequestAnalyzer
from .providers import LLMProviderFactory
from .schemas import AnalyzeRequest, AnalyzeResponse, AnswerRequest, AnswerResponse
from .security import require_internal_api_key

app = FastAPI(
    title="Smart University AI Service",
    version="2.0.0",
    docs_url=None
    if __import__("os").getenv("AI_DISABLE_DOCS", "0") == "1"
    else "/docs",
)


@app.get("/health")
def health():
    return {"service": "ai-service", "status": "ok"}


@app.post(
    "/v1/answer",
    response_model=AnswerResponse,
    dependencies=[Depends(require_internal_api_key)],
)
def answer(request: AnswerRequest):
    text, confidence, provider, model_name = LLMProviderFactory.create().answer(request)
    return AnswerResponse(
        answer=text, confidence=confidence, provider=provider, model_name=model_name
    )


@app.post(
    "/v1/analyze",
    response_model=AnalyzeResponse,
    dependencies=[Depends(require_internal_api_key)],
)
def analyze(request: AnalyzeRequest):
    return AnalyzeResponse(**RequestAnalyzer().analyze(request.text))
