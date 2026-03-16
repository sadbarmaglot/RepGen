from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Ответ на загрузку документа."""

    document_name: str = Field(..., description="Имя документа в GCS")
    mime_type: str = Field(..., description="MIME-тип документа")


class DocumentReviewResponse(BaseModel):
    """Ответ на проверку документа."""

    document_name: str = Field(..., description="Имя документа в GCS")
    extracted_text: str = Field(..., description="Извлечённый текст документа")
    review_result: str = Field(..., description="Результат LLM-проверки")
