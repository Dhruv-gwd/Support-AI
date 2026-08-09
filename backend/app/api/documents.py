import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from fastapi import status
from sqlalchemy.orm import Session

from app.models.schemas import UploadResponse, SourceListResponse
from app.services.document_service import extract_text, extract_images
from app.services.chunking_service import chunk_text
from app.services.embedding_service import EmbeddingService, EmbeddingServiceError
from app.services.vector_store_service import VectorStoreService
from app.services.image_store import add_document_images, get_document_images, remove_document_images, cleanup_image_files
from app.config import MAX_FILE_SIZE_MB, RATE_LIMIT_PER_MINUTE
from app.api.auth import get_current_user, require_admin
from app.models.database import SessionLocal, Document

router = APIRouter()

embedding_service = EmbeddingService()
vector_store = VectorStoreService()

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "csv", "xlsx", "xls", "md", "html", "png", "jpg", "jpeg", "gif", "bmp", "webp"}
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "images")
IMAGES_DIR = os.path.abspath(IMAGES_DIR)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_admin),
):
    original_filename = Path(file.filename or "").name
    if not original_filename:
        raise HTTPException(status_code=400, detail="A filename is required")

    ext = original_filename.lower().rsplit(".", 1)[-1] if "." in original_filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = bytearray()
    while chunk := await file.read(1024 * 1024):
        content.extend(chunk)
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB.",
            )

    is_image_only = ext in {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

    if is_image_only:
        saved_name = original_filename
        out_path = os.path.join(IMAGES_DIR, saved_name)
        with open(out_path, "wb") as f:
            f.write(content)
        add_document_images(saved_name, [saved_name])
        doc = Document(filename=saved_name, tenant_id=current_user.tenant_id, uploaded_by=current_user.id)
        db.add(doc)
        db.commit()
        return UploadResponse(filename=saved_name, chunks_added=0)

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    text = ""
    image_files = []
    try:
        text = extract_text(tmp_path, original_filename)
        image_files = extract_images(tmp_path, original_filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not read the uploaded file") from e
    finally:
        os.remove(tmp_path)

    if not text.strip():
        raise HTTPException(
            status_code=400, detail="No extractable text found in this document"
        )

    chunks = chunk_text(text)

    try:
        embeddings = embedding_service.embed_documents(chunks)
    except EmbeddingServiceError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    vector_store.add_chunks(chunks, embeddings, original_filename, tenant_id=current_user.tenant_id)
    add_document_images(original_filename, image_files)

    doc = Document(filename=original_filename, tenant_id=current_user.tenant_id, uploaded_by=current_user.id)
    db.add(doc)
    db.commit()

    return UploadResponse(filename=original_filename, chunks_added=len(chunks))


@router.get("/documents", response_model=SourceListResponse)
def list_documents(db: Session = Depends(get_db), current_user = Depends(require_admin)):
    sources = vector_store.list_sources(tenant_id=current_user.tenant_id)
    return SourceListResponse(sources=sources)


@router.delete("/documents/{filename}")
def delete_document(filename: str, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    deleted = vector_store.delete_source(filename, tenant_id=current_user.tenant_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"No chunks found for '{filename}'")

    image_files = get_document_images(filename)
    cleanup_image_files(image_files)
    remove_document_images(filename)

    doc = db.query(Document).filter(Document.filename == filename, Document.tenant_id == current_user.tenant_id).first()
    if doc:
        db.delete(doc)
        db.commit()

    return {"filename": filename, "chunks_deleted": deleted}


@router.get("/images/{image_name}")
def get_image(image_name: str, current_user = Depends(get_current_user)):
    safe_name = os.path.basename(image_name)
    tenant_sources = vector_store.list_sources(tenant_id=current_user.tenant_id)
    if not any(safe_name in get_document_images(source) for source in tenant_sources):
        raise HTTPException(status_code=404, detail="Image not found")
    image_path = os.path.join(IMAGES_DIR, safe_name)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)
