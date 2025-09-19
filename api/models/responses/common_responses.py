from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ErrorResponse(BaseModel):
    """Модель ошибки"""
    error: str = Field(..., description="Описание ошибки")
    detail: Optional[str] = Field(default=None, description="Детали ошибки")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
