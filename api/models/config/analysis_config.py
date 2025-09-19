from pydantic import BaseModel, Field
from typing import Optional

class AnalysisConfig(BaseModel):
    """Конфигурация анализа дефектов"""
    model_name: Optional[str] = Field(default=None, description="Название модели для анализа")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0, description="Температура генерации")
    max_tokens: int = Field(default=1024, ge=100, le=4000, description="Максимальное количество токенов")
    language: str = Field(default="ru", description="Язык ответа")
    response_format: str = Field(default="json_object", description="Формат ответа")
    
    class Config:
        schema_extra = {
            "example": {
                "model_name": "gpt-4o-mini",
                "temperature": 0.2,
                "max_tokens": 1024,
                "language": "ru",
                "response_format": "json_object"
            }
        }
