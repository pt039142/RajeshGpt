"""Health check endpoints"""

from fastapi import APIRouter
from app.core.config import settings
from app.models.schemas import HealthCheck

router = APIRouter()


def llm_status() -> str:
    """Return a coarse LLM configuration status for the active provider."""
    provider = settings.llm_provider

    if provider == "huggingface":
        return "configured" if settings.huggingface_api_key else "missing_huggingface_api_key"
    if provider == "openai":
        return "configured" if settings.openai_api_key else "missing_openai_api_key"
    if provider == "ollama":
        return "configured_local"
    if settings.huggingface_api_key or settings.openai_api_key:
        return "configured"
    return "fallback_only"


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": settings.api_version,
        "components": {
            "api": "operational",
            "documents": "available",
            "llm": llm_status(),
            "rag": "initialized"
        }
    }


@router.get("/info")
async def app_info():
    """Get application information"""
    return {
        "app_name": settings.app_name,
        "version": settings.api_version,
        "provider": settings.llm_provider,
        "model": settings.huggingface_model if settings.llm_provider == "huggingface" else settings.model_name,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens
    }
