"""Main FastAPI application"""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routes import health, documents, queries

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"

# Create uploads directory
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.embeddings_dir, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(queries.router, prefix="/api", tags=["Queries"])

if FRONTEND_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS_DIR), name="assets")


# Root endpoint
@app.get("/")
async def root():
    """Serve the built frontend when available."""
    if FRONTEND_DIST_DIR.exists():
        return FileResponse(FRONTEND_DIST_DIR / "index.html")

    return {
        "name": "RajeshGPT",
        "version": settings.api_version,
        "description": "Income Tax AI Assistant",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/{full_path:path}")
async def frontend_routes(request: Request, full_path: str):
    """Support direct navigation for the React SPA without intercepting API routes."""
    reserved_paths = {"api", "docs", "redoc", "openapi.json", "assets"}

    if not FRONTEND_DIST_DIR.exists():
        return JSONResponse(
            status_code=404,
            content={"detail": f"Path '{full_path}' not found."},
        )

    if full_path.split("/", 1)[0] in reserved_paths:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Path '{request.url.path}' not found."},
        )

    return FileResponse(FRONTEND_DIST_DIR / "index.html")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "details": {"type": type(exc).__name__}
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
