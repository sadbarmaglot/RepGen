from pydantic import BaseModel, Field
from typing import Optional


class DocumentReviewRequest(BaseModel):
    """Запрос на проверку документа."""

    document_name: str = Field(..., description="Имя документа в GCS")
    prompt: Optional[str] = Field(
        default=None,
        description="Дополнительный промпт для LLM-проверки",
    )
    model: Optional[str] = Field(
        default=None,
        description="Модель для проверки (например gpt-5.4, gpt-5.4-mini)",
    )
