from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ObjectResponse(BaseModel):
    """Ответ с информацией об объекте"""
    id: int = Field(..., description="ID объекта")
    project_id: int = Field(..., description="ID проекта")
    name: str = Field(..., description="Название объекта")
    address: Optional[str] = Field(None, description="Адрес объекта")
    description: Optional[str] = Field(None, description="Описание объекта")
    created_at: datetime = Field(..., description="Дата создания объекта")
    
    class Config:
        from_attributes = True

class ObjectListResponse(BaseModel):
    """Ответ со списком объектов"""
    objects: list[ObjectResponse] = Field(..., description="Список объектов")
    total: int = Field(..., description="Общее количество объектов")
