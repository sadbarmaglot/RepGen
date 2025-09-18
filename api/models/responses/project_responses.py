from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProjectResponse(BaseModel):
    """Ответ с информацией о проекте"""
    id: int = Field(..., description="ID проекта")
    owner_id: int = Field(..., description="ID владельца проекта")
    name: str = Field(..., description="Название проекта")
    description: Optional[str] = Field(None, description="Описание проекта")
    created_at: datetime = Field(..., description="Дата создания проекта")
    
    class Config:
        from_attributes = True

class ProjectListResponse(BaseModel):
    """Ответ со списком проектов"""
    projects: list[ProjectResponse] = Field(..., description="Список проектов")
    total: int = Field(..., description="Общее количество проектов")
