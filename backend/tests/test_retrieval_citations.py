import numpy as np

from sqlalchemy import select

from app.db.session import get_sessionmaker, init_db
from app.models.db_models import Chunk, Document
from app.rag.index import FaissIndex
from app.services.retrieval_service import RetrievalService, build_citations


class DummyEmbedder:
    def embed_documents(self, texts):
        return np.array([[len(t), t.count("a"), t.count("b")] for t in texts], dtype="float32")

    def embed_query(self, text):
        return np.array([len(text), text.count("a"), text.count("b")], dtype="float32")


def test_retrieval_returns_citations(temp_data_dir):
    init_db()
    session = get_sessionmaker()()

    doc = Document(
        id="doc-1",
        title="Doc One",
        num_pages=1,
        source_type="note",
        path=str(temp_data_dir / "doc1.txt"),
        status="indexed",
    )
    session.add(doc)
    session.commit()

    chunks = [
        Chunk(doc_id=doc.id, page=1, chunk_id="doc-1-1-0", text="alpha beta", embedding_id=1),
        Chunk(doc_id=doc.id, page=1, chunk_id="doc-1-1-1", text="gamma delta", embedding_id=2),
    ]
    session.add_all(chunks)
    session.commit()

    index = FaissIndex(str(temp_data_dir / "index" / "faiss.index"))
    embedder = DummyEmbedder()
    embeddings = embedder.embed_documents([chunk.text for chunk in chunks])
    index.add_embeddings(embeddings, [1, 2])

    retrieval = RetrievalService(session, index, embedder)
    results = retrieval.retrieve("alpha", None, top_k=1)
    assert len(results) == 1

    citations = build_citations(results)
    assert citations[0].doc_title == "Doc One"
    assert citations[0].page == 1
    assert citations[0].chunk_id in {"doc-1-1-0", "doc-1-1-1"}

    session.close()
