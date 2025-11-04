from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from ..database.enums import MarkType
from .photo_responses import PhotoResponse

class MarkResponse(BaseModel):
    """Ответ с информацией об отметке"""
    id: int = Field(..., description="ID отметки")
    plan_id: int = Field(..., description="ID плана")
    name: Optional[str] = Field(None, description="Название отметки")
    description: Optional[str] = Field(None, description="Описание отметки")
    type: MarkType = Field(..., description="Тип отметки")
    x: Optional[Decimal] = Field(None, description="Координата X (от 0 до 1, не зависит от размеров изображения)")
    y: Optional[Decimal] = Field(None, description="Координата Y (от 0 до 1, не зависит от размеров изображения)")
    is_horizontal: bool = Field(..., description="Горизонтальная линия измерения")
    photo_count: Optional[int] = Field(None, description="Количество фотографий для этой метки")
    created_at: datetime = Field(..., description="Дата создания отметки")
    
    class Config:
        from_attributes = True
        use_enum_values = True

class MarkListResponse(BaseModel):
    """Ответ со списком отметок"""
    marks: list[MarkResponse] = Field(..., description="Список отметок")
    total: int = Field(..., description="Общее количество отметок")

class MarkWithPhotosResponse(BaseModel):
    """Ответ с информацией об отметке вместе с фотографиями"""
    id: int = Field(..., description="ID отметки")
    plan_id: int = Field(..., description="ID плана")
    name: Optional[str] = Field(None, description="Название отметки")
    description: Optional[str] = Field(None, description="Описание отметки")
    type: MarkType = Field(..., description="Тип отметки")
    x: Optional[Decimal] = Field(None, description="Координата X (от 0 до 1, не зависит от размеров изображения)")
    y: Optional[Decimal] = Field(None, description="Координата Y (от 0 до 1, не зависит от размеров изображения)")
    is_horizontal: bool = Field(..., description="Горизонтальная линия измерения")
    photos: list[PhotoResponse] = Field(default_factory=list, description="Фотографии метки")
    created_at: datetime = Field(..., description="Дата создания отметки")
    
    class Config:
        from_attributes = True
        use_enum_values = True

class MarkWithPhotosListResponse(BaseModel):
    """Ответ со списком отметок с фотографиями"""
    marks: list[MarkWithPhotosResponse] = Field(..., description="Список отметок с фотографиями")
    total: int = Field(..., description="Общее количество отметок")
