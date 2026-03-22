from backend.app.config import Settings


def get_azure_config(settings: Settings) -> dict[str, str]:
    return {
        "endpoint": settings.azure_openai_endpoint,
        "deployment": settings.azure_openai_deployment_chat,
        "api_version": settings.azure_openai_api_version,
    }
