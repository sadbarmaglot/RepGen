from pydantic import BaseModel, Field
from typing import Optional

class ImageAnalysisRequest(BaseModel):
    """Запрос на анализ изображения"""
    image_name: str = Field(..., description="Имя изображения для анализа")
    construction_type: Optional[str] = Field(None, description="Тип конструкции для фильтрации базы дефектов")
    photo_id: Optional[int] = Field(None, description="ID фотографии для сохранения результата в БД")
    object_id: Optional[int] = Field(None, description="ID объекта для денормализации")


class DefectAnalysisUpdateRequest(BaseModel):
    """Запрос на обновление анализа дефекта пользователем"""
    defect_description: Optional[str] = Field(None, description="Описание дефекта")
    recommendation: Optional[str] = Field(None, description="Рекомендация по устранению")
    category: Optional[str] = Field(None, description="Категория дефекта (А, Б, В)")
    defect_code: Optional[str] = Field(None, description="Код дефекта из базы")
    object_id: Optional[int] = Field(None, description="ID объекта")
