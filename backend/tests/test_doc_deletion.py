from pathlib import Path

import numpy as np

from sqlalchemy import select

from app.db.session import get_sessionmaker, init_db
from app.models.db_models import Chunk, Document
from app.rag.index import FaissIndex
from app.services.document_service import DocumentService


class DummyEmbedder:
    def embed_documents(self, texts):
        return np.array([[len(t), t.count("a"), t.count("b")] for t in texts], dtype="float32")


def test_document_deletion_cleans_index_and_db(temp_data_dir):
    init_db()
    session = get_sessionmaker()()

    file_path = Path(temp_data_dir / "doc.txt")
    file_path.write_text("alpha beta", encoding="utf-8")

    doc = Document(
        id="doc-2",
        title="Doc Two",
        num_pages=1,
        source_type="note",
        path=str(file_path),
        status="indexed",
    )
    chunk = Chunk(doc_id=doc.id, page=1, chunk_id="doc-2-1-0", text="alpha beta", embedding_id=10)
    session.add(doc)
    session.add(chunk)
    session.commit()

    index = FaissIndex(str(temp_data_dir / "index" / "faiss.index"))
    embedder = DummyEmbedder()
    embeddings = embedder.embed_documents([chunk.text])
    index.add_embeddings(embeddings, [10])
    assert index.count() == 1

    service = DocumentService(session, index)
    deleted = service.delete_document("doc-2")
    assert deleted is True

    assert session.get(Document, "doc-2") is None
    remaining = session.scalars(select(Chunk).where(Chunk.doc_id == "doc-2")).all()
    assert len(remaining) == 0
    assert index.count() == 0
    assert not file_path.exists()
    session.close()
