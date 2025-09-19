from pydantic import BaseModel, Field
from typing import Optional

class PhotoCreateRequest(BaseModel):
    """Запрос на создание фотографии"""
    mark_id: int = Field(..., gt=0, description="ID отметки")
    image_name: str = Field(..., max_length=255, description="Имя файла изображения")
    type: Optional[str] = Field(None, max_length=100, description="Тип фотографии")
    description: Optional[str] = Field(None, max_length=2000, description="Описание фотографии")

class PhotoUpdateRequest(BaseModel):
    """Запрос на обновление фотографии"""
    type: Optional[str] = Field(None, max_length=100, description="Новый тип фотографии")
    description: Optional[str] = Field(None, max_length=2000, description="Новое описание фотографии")
