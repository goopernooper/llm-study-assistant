from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class UploadResponse(BaseModel):
    doc_id: str
    title: str
    num_pages: int
    status: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    num_pages: int
    created_at: datetime
    status: str


class Citation(BaseModel):
    ref: int
    doc_id: str
    doc_title: str
    page: int
    chunk_id: str
    snippet: str
    score: float


class ChatRequest(BaseModel):
    question: str
    doc_ids: Optional[List[str]] = None
    mode: str = Field("qa", pattern="^(qa|summarize_doc|summarize_multi|key_takeaways|flashcards)$")
    top_k: Optional[int] = None
    temperature: Optional[float] = None
    model: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    retrieved_chunks_count: int
