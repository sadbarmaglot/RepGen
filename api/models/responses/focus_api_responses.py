from pydantic import BaseModel, Field
from typing import Any, Optional, List


class FileUrlInfo(BaseModel):
    """Информация о файле с подписанной ссылкой"""
    filename: str = Field(..., description="Имя файла в хранилище")
    signed_url: str = Field(..., description="Подписанная ссылка для доступа к файлу")


class FocusImageProcessResponse(BaseModel):
    """Ответ с результатом генерации плана через Focus API"""
    success: bool = Field(..., description="Успешность генерации плана")
    image_files: Optional[List[FileUrlInfo]] = Field(None, description="Список изображений (PNG/JPG) с подписанными ссылками")
    dxf_files: Optional[List[FileUrlInfo]] = Field(None, description="Список DXF файлов с подписанными ссылками")
    original_filename: Optional[str] = Field(None, description="Имя исходного файла")
    message: Optional[str] = Field(None, description="Сообщение о результате")
