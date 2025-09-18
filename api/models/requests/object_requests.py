from pydantic import BaseModel, Field
from typing import Optional

class ObjectCreateRequest(BaseModel):
    """Запрос на создание объекта"""
    project_id: int = Field(..., gt=0, description="ID проекта")
    name: str = Field(..., min_length=1, max_length=500, description="Название объекта")
    address: Optional[str] = Field(None, max_length=1000, description="Адрес объекта")
    description: Optional[str] = Field(None, max_length=2000, description="Описание объекта")

class ObjectUpdateRequest(BaseModel):
    """Запрос на обновление объекта"""
    name: Optional[str] = Field(None, min_length=1, max_length=500, description="Новое название объекта")
    address: Optional[str] = Field(None, max_length=1000, description="Новый адрес объекта")
    description: Optional[str] = Field(None, max_length=2000, description="Новое описание объекта")
