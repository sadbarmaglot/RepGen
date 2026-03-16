from pydantic import BaseModel, Field
from typing import Optional


class DocumentReviewRequest(BaseModel):
    """Запрос на проверку документа."""

    document_name: str = Field(..., description="Имя документа в GCS")
    prompt: Optional[str] = Field(
        default=None,
        description="Дополнительный промпт для LLM-проверки",
    )
