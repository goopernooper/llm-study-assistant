from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.schemas import ChatRequest, ChatResponse
from app.services.container import get_embedder, get_index, get_llm
from app.services.retrieval_service import (
    RetrievalService,
    build_citations,
    build_context,
    system_prompt,
    user_prompt,
)
from app.utils.config import get_settings

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, session: Session = Depends(get_session)):
    settings = get_settings()
    if request.mode == "summarize_doc" and not request.doc_ids:
        raise HTTPException(status_code=400, detail="summarize_doc requires a doc_ids selection")

    top_k = request.top_k or settings.default_top_k
    top_k = min(top_k, settings.max_context_chunks)

    retrieval = RetrievalService(session, get_index(), get_embedder())
    chunks = await run_in_threadpool(retrieval.retrieve, request.question, request.doc_ids, top_k)

    if not chunks:
        return ChatResponse(
            answer="I don't have enough information in the uploaded documents.",
            citations=[],
            retrieved_chunks_count=0,
        )

    citations = build_citations(chunks)
    context = build_context(chunks)

    llm = get_llm()
    temperature = request.temperature if request.temperature is not None else settings.default_temperature
    model = request.model or settings.llm_model

    answer = await run_in_threadpool(
        llm.generate,
        system_prompt(),
        user_prompt(request.mode, request.question, context),
        temperature,
        model,
    )

    return ChatResponse(
        answer=answer,
        citations=citations,
        retrieved_chunks_count=len(chunks),
    )
