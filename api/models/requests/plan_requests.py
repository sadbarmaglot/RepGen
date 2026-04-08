from pydantic import BaseModel, Field
from typing import Optional, List, Any

class PlanCreateRequest(BaseModel):
    """Запрос на создание плана"""
    object_id: int = Field(..., gt=0, description="ID объекта")
    name: str = Field(..., min_length=1, max_length=500, description="Название плана")
    description: Optional[str] = Field(None, max_length=2000, description="Описание плана")
    image_name: Optional[str] = Field(None, max_length=255, description="Имя изображения")

class PlanUpdateRequest(BaseModel):
    """Запрос на обновление плана"""
    name: Optional[str] = Field(None, min_length=1, max_length=500, description="Новое название плана")
    description: Optional[str] = Field(None, max_length=2000, description="Новое описание плана")
    axes: Optional[List[Any]] = Field(None, description="Оси плана [{name, x1, y1, x2, y2}, ...]")
