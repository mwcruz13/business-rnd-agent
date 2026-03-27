from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    #llm_backend: str = "azure"
    llm_backend: str = "ollama"
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2025-01-01-preview"
    azure_openai_deployment_reasoning: str = ""
    azure_openai_deployment_chat: str = ""
    azure_openai_deployment_embedding: str = ""
    ollama_base_url: str = "http://192.168.10.250:11434"
    ollama_model: str = "nemotron-3-super:latest"
    postgres_host: str = "bmi-postgres"
    postgres_port: int = 5432
    postgres_db: str = "postgres"
    postgres_user: str = "postgres"
    postgres_password: str = ""
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file="backend/.env", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
