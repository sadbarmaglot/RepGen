from pydantic import BaseModel, Field
from typing import Optional

class UploadRequest(BaseModel):
    """Запрос на загрузку файла"""
    pass  # Обычно загрузка файлов происходит через multipart/form-data

class UploadResponse(BaseModel):
    """Ответ на загрузку файла"""
    filename: str = Field(..., description="Имя загруженного файла")
    public_url: str = Field(..., description="Публичный URL файла")
    signed_url: Optional[str] = Field(default=None, description="Подписной URL для Gemini Pro (если создан)")
    mime_type: str = Field(..., description="Тип содержимого")

class FileUploadResponseWithBlob(BaseModel):
    """Ответ на загрузку файла с blob"""
    image_name: str = Field(..., description="Имя загруженного изображения")
