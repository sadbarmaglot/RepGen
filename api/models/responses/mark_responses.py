from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from ..database.enums import MarkType

class MarkResponse(BaseModel):
    """Ответ с информацией об отметке"""
    id: int = Field(..., description="ID отметки")
    plan_id: int = Field(..., description="ID плана")
    name: Optional[str] = Field(None, description="Название отметки")
    description: Optional[str] = Field(None, description="Описание отметки")
    type: MarkType = Field(..., description="Тип отметки")
    created_at: datetime = Field(..., description="Дата создания отметки")
    
    class Config:
        from_attributes = True
        use_enum_values = True

class MarkListResponse(BaseModel):
    """Ответ со списком отметок"""
    marks: list[MarkResponse] = Field(..., description="Список отметок")
    total: int = Field(..., description="Общее количество отметок")
