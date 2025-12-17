from pydantic import BaseModel, Field


class FocusImageProcessRequest(BaseModel):
    """Запрос на обработку изображения через Focus API для генерации плана"""
    image_name: str = Field(..., description="Имя изображения в хранилище GCS (файл должен быть загружен через /upload/images)")
