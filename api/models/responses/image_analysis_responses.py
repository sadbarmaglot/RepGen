from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Маппинг категорий из БД в русскую нотацию
CATEGORY_DISPLAY_MAP = {
    "A": "А",
    "B": "Б", 
    "C": "В"
}

class ImageAnalysisResponse(BaseModel):
    """Ответ с результатом анализа изображения"""
    description: str = Field(..., description="Описание выявленного дефекта")
    recommendation: str = Field(..., description="Рекомендация по устранению")
    category: str = Field(..., description="Категория дефекта")


class PhotoDefectAnalysisResponse(BaseModel):
    """Ответ с информацией об анализе дефекта по фотографии"""
    id: int = Field(..., description="ID анализа")
    photo_id: int = Field(..., description="ID фотографии")
    defect_description: str = Field(..., description="Описание дефекта")
    recommendation: str = Field(..., description="Рекомендация по устранению")
    category: str = Field(..., description="Категория дефекта (А, Б, В)")
    confidence: Optional[float] = Field(None, description="Уверенность модели (0.0-1.0)")
    created_at: datetime = Field(..., description="Дата создания анализа")
    
    class Config:
        from_attributes = True


class PhotoDefectAnalysisListResponse(BaseModel):
    """Ответ со списком анализов дефектов"""
    analyses: list[PhotoDefectAnalysisResponse] = Field(..., description="Список анализов")
    total: int = Field(..., description="Общее количество анализов")
