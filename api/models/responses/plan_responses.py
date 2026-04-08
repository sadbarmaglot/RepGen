from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

class PlanResponse(BaseModel):
    """Ответ с информацией о плане"""
    id: int = Field(..., description="ID плана")
    object_id: int = Field(..., description="ID объекта")
    name: str = Field(..., description="Название плана")
    description: Optional[str] = Field(None, description="Описание плана")
    image_url: Optional[str] = Field(None, description="Подписной URL изображения")
    axes: Optional[List[Any]] = Field(None, description="Оси плана [{name, x1, y1, x2, y2}, ...]")
    created_at: datetime = Field(..., description="Дата создания плана")
    
    class Config:
        from_attributes = True

class PlanListResponse(BaseModel):
    """Ответ со списком планов"""
    plans: list[PlanResponse] = Field(..., description="Список планов")
    total: int = Field(..., description="Общее количество планов")
