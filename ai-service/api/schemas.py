from pydantic import BaseModel, Field

class ContextDocument(BaseModel):
    id: int
    title: str
    content: str

class AnswerRequest(BaseModel):
    question: str = Field(min_length=3, max_length=5000)
    prompt: str = Field(min_length=3)
    documents: list[ContextDocument] = Field(default_factory=list)

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
