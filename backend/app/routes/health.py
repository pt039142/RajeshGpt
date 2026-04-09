"""Health check endpoints"""

from fastapi import APIRouter
from app.core.config import settings
from app.models.schemas import HealthCheck

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": settings.api_version,
        "components": {
            "api": "operational",
            "documents": "available",
            "llm": "configured",
            "rag": "initialized"
        }
    }


@router.get("/info")
async def app_info():
    """Get application information"""
    return {
        "app_name": settings.app_name,
        "version": settings.api_version,
        "model": settings.model_name,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens
    }
