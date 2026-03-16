from pydantic import BaseModel, Field

class FileUploadResponseWithBlob(BaseModel):
    """Ответ на загрузку файла"""
    image_name: str = Field(..., description="Имя загруженного изображения")
