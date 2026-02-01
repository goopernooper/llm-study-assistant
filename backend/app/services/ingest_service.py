from __future__ import annotations

import logging
from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db_models import Chunk, Document
from app.rag.chunking import chunk_text
from app.rag.index import FaissIndex
from app.services.embeddings import Embedder
from app.services.pdf_service import PageText, extract_text_pages

logger = logging.getLogger(__name__)


class IngestService:
    def __init__(self, session: Session, index: FaissIndex, embedder: Embedder):
        self.session = session
        self.index = index
        self.embedder = embedder

    def ingest_pdf(self, doc_id: str, file_path: str, title: str) -> Document:
        pages = extract_text_pages(file_path)
        return self._ingest_pages(doc_id, file_path, title, pages, source_type="pdf")

    def ingest_text(self, doc_id: str, file_path: str, title: str, text: str) -> Document:
        pages = [PageText(page_number=1, text=text)]
        return self._ingest_pages(doc_id, file_path, title, pages, source_type="note")

    def _ingest_pages(self, doc_id: str, file_path: str, title: str, pages: List[PageText], source_type: str) -> Document:
        document = Document(
            id=doc_id,
            title=title,
            num_pages=len(pages),
            source_type=source_type,
            path=file_path,
            status="indexing",
        )
        self.session.add(document)
        self.session.flush()

        chunks: List[Tuple[int, str, int]] = []  # (page, text, chunk_index)
        for page in pages:
            for idx, chunk in enumerate(chunk_text(page.text)):
                chunks.append((page.page_number, chunk, idx))

        if not chunks:
            document.status = "empty"
            self.session.commit()
            return document

        texts = [chunk_text_value for _page, chunk_text_value, _idx in chunks]
        embeddings = self.embedder.embed_documents(texts)

        max_embedding_id = self.session.scalar(select(func.max(Chunk.embedding_id)))
        next_embedding_id = int(max_embedding_id or 0) + 1
        embedding_ids = list(range(next_embedding_id, next_embedding_id + len(chunks)))

        chunk_rows: List[Chunk] = []
        for (page, text, idx), embedding_id in zip(chunks, embedding_ids, strict=False):
            chunk_rows.append(
                Chunk(
                    doc_id=doc_id,
                    page=page,
                    chunk_id=f"{doc_id}-{page}-{idx}",
                    text=text,
                    embedding_id=embedding_id,
                )
            )

        self.session.add_all(chunk_rows)
        self.session.commit()

        try:
            self.index.add_embeddings(embeddings, embedding_ids)
            document.status = "indexed"
            self.session.commit()
            logger.info("Ingested document %s with %s chunks", doc_id, len(chunk_rows))
        except Exception as exc:
            document.status = "error"
            self.session.commit()
            logger.exception("Failed to add embeddings for doc %s: %s", doc_id, exc)
            raise
        return document
