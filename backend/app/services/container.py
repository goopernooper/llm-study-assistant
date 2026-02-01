from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.rag.index import FaissIndex
from app.services.embeddings import Embedder, get_embedder as build_embedder
from app.services.llm_service import LLM, get_llm as build_llm
from app.utils.config import get_settings


@lru_cache
def get_index() -> FaissIndex:
    settings = get_settings()
    index_dir = settings.resolved_index_dir()
    return FaissIndex(str((Path(index_dir) / "faiss.index")))


@lru_cache
def get_embedder() -> Embedder:
    return build_embedder()


@lru_cache
def get_llm() -> LLM:
    return build_llm()
