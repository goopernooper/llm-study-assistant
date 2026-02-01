from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.db_models import Chunk, Document
from app.rag.index import FaissIndex

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, session: Session, index: FaissIndex):
        self.session = session
        self.index = index

    def list_documents(self) -> List[Document]:
        stmt = select(Document).order_by(Document.created_at.desc())
        return list(self.session.scalars(stmt).all())

    def delete_document(self, doc_id: str) -> bool:
        document = self.session.get(Document, doc_id)
        if not document:
            return False

        chunk_ids = [row[0] for row in self.session.execute(select(Chunk.embedding_id).where(Chunk.doc_id == doc_id)).all()]
        if chunk_ids:
            self.index.delete(chunk_ids)

        self.session.execute(delete(Chunk).where(Chunk.doc_id == doc_id))
        self.session.execute(delete(Document).where(Document.id == doc_id))
        self.session.commit()

        try:
            path = Path(document.path)
            if path.exists():
                path.unlink()
        except Exception as exc:
            logger.warning("Failed to delete file for doc %s: %s", doc_id, exc)

        logger.info("Deleted document %s", doc_id)
        return True
