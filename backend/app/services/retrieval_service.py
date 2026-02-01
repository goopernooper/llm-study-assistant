from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db_models import Chunk, Document
from app.models.schemas import Citation
from app.rag.index import FaissIndex
from app.services.embeddings import Embedder


@dataclass
class RetrievedChunk:
    embedding_id: int
    score: float
    doc_id: str
    doc_title: str
    page: int
    chunk_id: str
    text: str


class RetrievalService:
    def __init__(self, session: Session, index: FaissIndex, embedder: Embedder):
        self.session = session
        self.index = index
        self.embedder = embedder

    def retrieve(self, question: str, doc_ids: Optional[Iterable[str]], top_k: int) -> List[RetrievedChunk]:
        query_vector = self.embedder.embed_query(question)
        search_k = max(top_k * 4, top_k)
        results = self.index.search(query_vector, search_k)
        if not results:
            return []

        embedding_ids = [embedding_id for embedding_id, _score in results]
        score_map = {embedding_id: score for embedding_id, score in results}

        stmt = select(Chunk, Document).join(Document, Chunk.doc_id == Document.id).where(Chunk.embedding_id.in_(embedding_ids))
        if doc_ids:
            stmt = stmt.where(Chunk.doc_id.in_(list(doc_ids)))
        rows = self.session.execute(stmt).all()

        chunks: List[RetrievedChunk] = []
        for chunk, document in rows:
            chunks.append(
                RetrievedChunk(
                    embedding_id=chunk.embedding_id,
                    score=score_map.get(chunk.embedding_id, 0.0),
                    doc_id=chunk.doc_id,
                    doc_title=document.title,
                    page=chunk.page,
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                )
            )

        chunks.sort(key=lambda item: score_map.get(item.embedding_id, 0.0), reverse=True)
        return chunks[:top_k]


def build_citations(chunks: List[RetrievedChunk]) -> List[Citation]:
    citations: List[Citation] = []
    for idx, chunk in enumerate(chunks, start=1):
        snippet = chunk.text.strip().replace("\n", " ")
        if len(snippet) > 180:
            snippet = snippet[:177].rstrip() + "..."
        citations.append(
            Citation(
                ref=idx,
                doc_id=chunk.doc_id,
                doc_title=chunk.doc_title,
                page=chunk.page,
                chunk_id=chunk.chunk_id,
                snippet=snippet,
                score=chunk.score,
            )
        )
    return citations


def build_context(chunks: List[RetrievedChunk]) -> str:
    lines = []
    for idx, chunk in enumerate(chunks, start=1):
        lines.append(
            f"Source [{idx}] ({chunk.doc_title}, page {chunk.page}, chunk {chunk.chunk_id}):\n{chunk.text.strip()}"
        )
    return "\n\n".join(lines)


def system_prompt() -> str:
    return (
        "You are a research assistant. Use only the provided sources. "
        "Cite sources with [n] after each claim. "
        "If the sources do not contain enough information, say: "
        "I don't have enough information in the uploaded documents."
    )


def user_prompt(mode: str, question: str, context: str) -> str:
    instructions = {
        "qa": "Answer the question concisely using the sources.",
        "summarize_doc": "Summarize the selected document concisely.",
        "summarize_multi": "Summarize the selected documents concisely.",
        "key_takeaways": "Provide 5-8 key takeaways as bullet points.",
        "flashcards": "Create 5-10 flashcards in Q/A format.",
    }
    task = instructions.get(mode, instructions["qa"])
    return (
        f"Task: {task}\n"
        f"Question: {question}\n\n"
        f"Sources:\n{context}\n\n"
        "Remember to cite sources like [1]."
    )
