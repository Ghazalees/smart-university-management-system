from fastapi import FastAPI
from .analysis import RequestAnalyzer
from .providers import LLMProviderFactory
from .schemas import AnalyzeRequest, AnalyzeResponse, AnswerRequest, AnswerResponse

app = FastAPI(title="Smart University AI Service", version="1.0.0")

@app.get("/health")
def health(): return {"service": "ai-service", "status": "ok"}

@app.post("/v1/answer", response_model=AnswerResponse)
def answer(request: AnswerRequest):
    text, confidence, provider, model_name = LLMProviderFactory.create().answer(request)
    return AnswerResponse(answer=text, confidence=confidence, provider=provider, model_name=model_name)

@app.post("/v1/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    return AnalyzeResponse(**RequestAnalyzer().analyze(request.text))
