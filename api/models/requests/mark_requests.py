from pydantic import BaseModel, Field
from typing import Optional
from ..database.enums import MarkType

class MarkCreateRequest(BaseModel):
    """Запрос на создание отметки"""
    plan_id: int = Field(..., gt=0, description="ID плана")
    name: Optional[str] = Field(None, max_length=500, description="Название отметки")
    description: Optional[str] = Field(None, max_length=2000, description="Описание отметки")
    type: MarkType = Field(default=MarkType.other, description="Тип отметки")

class MarkUpdateRequest(BaseModel):
    """Запрос на обновление отметки"""
    name: Optional[str] = Field(None, max_length=500, description="Новое название отметки")
    description: Optional[str] = Field(None, max_length=2000, description="Новое описание отметки")
    type: Optional[MarkType] = Field(None, description="Новый тип отметки")
