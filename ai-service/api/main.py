from fastapi import FastAPI

app = FastAPI(title="Smart University AI Service")


@app.get("/health")
def health_check():
    """Return AI service health for Docker and gateway checks."""
    return {
        "success": True,
        "data": {
            "service": "ai-service",
            "status": "ok",
        },
    }
