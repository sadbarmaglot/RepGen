from pydantic import BaseModel, Field

class ConstructionTypeResult(BaseModel):
    """Результат определения типа конструкции"""
    image_name: str = Field(..., description="Имя проанализированного изображения")
    construction_type: str = Field(..., description="Определенный тип конструкции")
    description: str = Field(..., description="Описание дефектов и повреждений")

class ConstructionTypeResponse(BaseModel):
    """Ответ с результатом определения типа конструкции"""
    result: ConstructionTypeResult = Field(..., description="Результат определения типа конструкции")
