from typing import Optional

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


class ReviewRemark(BaseModel):
    """Одно замечание с данными для автоисправления."""

    id: int
    category: str
    where: str
    problem: str
    fix: str
    find: Optional[str] = None
    replace: Optional[str] = None
    context: Optional[str] = None
    auto_fixable: bool = False


class DocumentReviewFixesResponse(BaseModel):
    """Ответ с структурированными замечаниями для автоисправления."""

    document_name: str = Field(..., description="Имя документа в GCS")
    remarks: list[ReviewRemark] = Field(default_factory=list)
    summary: str = Field(default="", description="Итоговая строка")
