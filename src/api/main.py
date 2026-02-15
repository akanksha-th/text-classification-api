from fastapi import FastAPI, HTTPException, status
from typing import Dict
from src.api.routes import analyze
from src.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

@app.get("/")
def root():
    return {
        "message": "Social Sentiment API",
        "version": settings.VERSION,
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION
    }

app.include_router(
    analyze.router,
    prefix="/api/v1",
    tags=["Analysis"]
)