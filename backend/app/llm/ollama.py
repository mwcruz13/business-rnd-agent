from backend.app.config import Settings


def get_ollama_config(settings: Settings) -> dict[str, str]:
    return {
        "base_url": settings.ollama_base_url,
        "model": settings.ollama_model,
    }
