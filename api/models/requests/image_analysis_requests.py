from pydantic import BaseModel, Field
from typing import Optional

class ImageAnalysisRequest(BaseModel):
    """Запрос на анализ изображения"""
    image_name: str = Field(..., description="Имя изображения для анализа")
    construction_type: Optional[str] = Field(None, description="Тип конструкции для фильтрации базы дефектов")
