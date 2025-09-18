from pydantic import BaseModel, Field
from typing import Optional

class ProjectCreateRequest(BaseModel):
    """Запрос на создание проекта"""
    name: str = Field(..., min_length=1, max_length=500, description="Название проекта")
    description: Optional[str] = Field(None, max_length=2000, description="Описание проекта")

class ProjectUpdateRequest(BaseModel):
    """Запрос на обновление проекта"""
    name: Optional[str] = Field(None, min_length=1, max_length=500, description="Новое название проекта")
    description: Optional[str] = Field(None, max_length=2000, description="Новое описание проекта")

class ProjectChangeOwnerRequest(BaseModel):
    """Запрос на смену владельца проекта"""
    new_owner_id: int = Field(..., gt=0, description="ID нового владельца проекта")
