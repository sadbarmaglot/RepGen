from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PhotoResponse(BaseModel):
    """Ответ с информацией о фотографии"""
    id: int = Field(..., description="ID фотографии")
    mark_id: int = Field(..., description="ID отметки")
    image_name: str = Field(..., description="Имя файла изображения")
    image_url: Optional[str] = Field(None, description="Подписанный URL изображения")
    type: Optional[str] = Field(None, description="Тип фотографии")
    description: Optional[str] = Field(None, description="Описание фотографии")
    created_at: datetime = Field(..., description="Дата создания фотографии")
    
    class Config:
        from_attributes = True

class PhotoListResponse(BaseModel):
    """Ответ со списком фотографий"""
    photos: list[PhotoResponse] = Field(..., description="Список фотографий")
    total: int = Field(..., description="Общее количество фотографий")
