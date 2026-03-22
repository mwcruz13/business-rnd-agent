from fastapi import FastAPI

from backend.app.config import get_settings


settings = get_settings()
app = FastAPI(title="BMI Consultant Backend", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "llm_backend": settings.llm_backend}
