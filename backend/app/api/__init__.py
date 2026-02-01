from fastapi import APIRouter

from app.api.chat import router as chat_router
from app.api.docs import router as docs_router
from app.api.health import router as health_router

router = APIRouter()
router.include_router(docs_router, prefix="/api")
router.include_router(chat_router, prefix="/api")
router.include_router(health_router, prefix="/api")
