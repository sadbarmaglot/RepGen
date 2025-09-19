from pydantic import BaseModel, Field

class ConstructionTypeRequest(BaseModel):
    """Запрос на определение типа конструкции"""
    image_name: str = Field(..., description="Имя изображения в GCS bucket для анализа")
