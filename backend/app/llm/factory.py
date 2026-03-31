from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI

from backend.app.config import Settings


def get_chat_model(settings: Settings, llm_backend: str | None = None) -> BaseChatModel:
    backend_name = (llm_backend or settings.llm_backend).strip().lower()

    if backend_name == "ollama":
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            format="json",
        )

    if backend_name != "azure":
        raise ValueError(f"Unsupported llm_backend: {backend_name}")

    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_deployment_chat,
    )