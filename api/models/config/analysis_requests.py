from pydantic import BaseModel, Field
from typing import List, Optional

from .analysis_config import AnalysisConfig

class ImageInfo(BaseModel):
    """Информация о изображении"""
    url: str = Field(..., description="URL изображения")
    mime_type: str = Field(..., description="Тип содержимого")

class DefectAnalysisRequest(BaseModel):
    """Запрос на анализ дефектов"""
    image_infos: List[ImageInfo] = Field(..., description="Список информации о изображениях для анализа")
    config: Optional[AnalysisConfig] = Field(default=None, description="Конфигурация анализа")

class DefectResult(BaseModel):
    """Результат анализа одного изображения"""
    image_url: str = Field(..., description="URL проанализированного изображения")
    description: str = Field(..., description="Описание выявленного дефекта")
    recommendation: str = Field(..., description="Рекомендация по устранению")
    model_used: str = Field(..., description="Использованная модель")

class DefectAnalysisResponse(BaseModel):
    """Ответ с результатами анализа"""
    results: List[DefectResult] = Field(..., description="Результаты анализа")

