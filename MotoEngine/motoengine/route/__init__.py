"""Route package."""

from fastapi import APIRouter

from .admin_router import router as admin_router
from .health import router as health_router
from .chat_router import router as chat_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(admin_router)
