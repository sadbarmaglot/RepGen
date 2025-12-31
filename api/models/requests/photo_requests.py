from pydantic import BaseModel, Field
from typing import Optional

class PhotoCreateRequest(BaseModel):
    """Запрос на создание фотографии"""
    mark_id: int = Field(..., gt=0, description="ID отметки")
    image_name: str = Field(..., max_length=255, description="Имя файла изображения")
    type: Optional[str] = Field(None, max_length=100, description="Тип фотографии")
    description: Optional[str] = Field(None, max_length=2000, description="Описание фотографии")
    order: Optional[int] = Field(None, ge=0, description="Порядковый номер фотографии в отметке (если не указан, будет установлен автоматически)")

class PhotoUpdateRequest(BaseModel):
    """Запрос на обновление фотографии"""
    type: Optional[str] = Field(None, max_length=100, description="Новый тип фотографии")
    description: Optional[str] = Field(None, max_length=2000, description="Новое описание фотографии")
    order: Optional[int] = Field(None, ge=0, description="Новый порядковый номер фотографии в отметке")
    type_confidence: Optional[float] = Field(None, description="Уверенность в определении типа конструкции (0.0-1.0). Если пользователь сам указал тип, обычно устанавливается 1.0", ge=0.0, le=1.0)
