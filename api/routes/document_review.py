import os
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends

from api.dependencies.auth_dependencies import get_current_user
from api.models.entities import User
from api.models.requests.document_review_requests import DocumentReviewRequest
from api.models.responses.document_review_responses import (
    DocumentUploadResponse,
    DocumentReviewResponse,
)
from api.services.document_review_service import (
    DocumentReviewService,
    ALLOWED_EXTENSIONS,
    MAX_DOCUMENT_SIZE,
)
from common.gc_utils import documents_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

document_review_service = DocumentReviewService()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Документ (docx/pdf)"),
    _: User = Depends(get_current_user),
):
    """Загрузка документа в GCS (бакет documents)."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый формат файла. Допустимые: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_DOCUMENT_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Файл слишком большой. Максимум: {MAX_DOCUMENT_SIZE // (1024 * 1024)} MB",
        )

    mime_map = {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pdf": "application/pdf",
    }
    content_type = mime_map.get(ext, "application/octet-stream")

    import uuid

    document_name = f"{uuid.uuid4()}{ext}"
    await documents_storage.upload_bytes(content, document_name, content_type)

    logger.info("Документ %s загружен как %s", file.filename, document_name)
    return DocumentUploadResponse(document_name=document_name, mime_type=content_type)


@router.post("/review", response_model=DocumentReviewResponse)
async def review_document(
    request: DocumentReviewRequest,
    _: User = Depends(get_current_user),
):
    """Проверка технического отчёта: парсинг + LLM-анализ."""
    try:
        result = await document_review_service.review_document(
            document_name=request.document_name,
            prompt=request.prompt,
            model=request.model,
        )
        return DocumentReviewResponse(**result)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Документ не найден в хранилище")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
