"""API router aggregation."""
from fastapi import APIRouter

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.logs import router as logs_router

api_router = APIRouter()

api_router.include_router(logs_router, prefix="/logs", tags=["logs"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(health_router, tags=["health"])
