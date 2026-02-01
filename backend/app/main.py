from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.db.session import init_db
from app.utils.config import get_settings
from app.utils.logging import setup_logging
from app.utils.storage import ensure_dir

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    ensure_dir(settings.resolved_upload_dir())
    ensure_dir(settings.resolved_index_dir())
    init_db()


app.include_router(api_router)
