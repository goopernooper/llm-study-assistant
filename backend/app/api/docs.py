from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.schemas import DocumentOut, UploadResponse
from app.services.container import get_embedder, get_index
from app.services.document_service import DocumentService
from app.services.ingest_service import IngestService
from app.utils.config import get_settings
from app.utils.storage import ensure_dir

router = APIRouter(tags=["documents"])


@router.post("/docs/upload", response_model=UploadResponse)
async def upload_document(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    session: Session = Depends(get_session),
):
    if not file and not text:
        raise HTTPException(status_code=400, detail="Provide a PDF file or text notes")

    settings = get_settings()
    upload_dir = ensure_dir(settings.resolved_upload_dir())

    index = get_index()
    embedder = get_embedder()
    ingest_service = IngestService(session, index, embedder)

    doc_id = str(uuid.uuid4())

    if file:
        filename = file.filename or "document.pdf"
        suffix = Path(filename).suffix or ".pdf"
        if suffix.lower() != ".pdf":
            raise HTTPException(status_code=400, detail="Only PDF uploads are supported")
        stored_path = upload_dir / f"{doc_id}{suffix}"
        with stored_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        title = Path(filename).stem
        document = await run_in_threadpool(ingest_service.ingest_pdf, doc_id, str(stored_path), title)
    else:
        stored_path = upload_dir / f"note-{doc_id}.txt"
        stored_path.write_text(text or "", encoding="utf-8")
        title = f"Note {doc_id[:8]}"
        document = await run_in_threadpool(
            ingest_service.ingest_text, doc_id, str(stored_path), title, text or ""
        )

    return UploadResponse(
        doc_id=document.id,
        title=document.title,
        num_pages=document.num_pages,
        status=document.status,
    )


@router.get("/docs", response_model=List[DocumentOut])
def list_documents(session: Session = Depends(get_session)):
    service = DocumentService(session, get_index())
    return service.list_documents()


@router.delete("/docs/{doc_id}")
def delete_document(doc_id: str, session: Session = Depends(get_session)):
    service = DocumentService(session, get_index())
    deleted = service.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted"}
