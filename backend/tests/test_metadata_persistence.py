from datetime import datetime

from sqlalchemy import select

from app.db.session import get_sessionmaker, init_db
from app.models.db_models import Chunk, Document


def test_metadata_persistence(temp_data_dir):
    init_db()
    session = get_sessionmaker()()

    doc = Document(
        id="doc-123",
        title="Test Doc",
        num_pages=2,
        source_type="note",
        path=str(temp_data_dir / "doc.txt"),
        status="indexed",
        created_at=datetime.utcnow(),
    )
    chunk = Chunk(
        doc_id=doc.id,
        page=1,
        chunk_id="doc-123-1-0",
        text="Sample chunk",
        embedding_id=1,
    )

    session.add(doc)
    session.add(chunk)
    session.commit()

    fetched = session.get(Document, "doc-123")
    assert fetched is not None
    assert fetched.title == "Test Doc"

    chunks = session.scalars(select(Chunk).where(Chunk.doc_id == "doc-123")).all()
    assert len(chunks) == 1
    assert chunks[0].text == "Sample chunk"
    session.close()
