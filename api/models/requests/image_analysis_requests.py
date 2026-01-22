from pydantic import BaseModel, Field
from typing import Optional

class ImageAnalysisRequest(BaseModel):
    """Запрос на анализ изображения"""
    image_name: str = Field(..., description="Имя изображения для анализа")
    construction_type: Optional[str] = Field(None, description="Тип конструкции для фильтрации базы дефектов")
    photo_id: Optional[int] = Field(None, description="ID фотографии для сохранения результата в БД")


class DefectAnalysisUpdateRequest(BaseModel):
    """Запрос на обновление анализа дефекта пользователем"""
    defect_description: str = Field(..., description="Описание дефекта")
    recommendation: str = Field(..., description="Рекомендация по устранению")
    category: str = Field(..., description="Категория дефекта (А, Б, В)")
