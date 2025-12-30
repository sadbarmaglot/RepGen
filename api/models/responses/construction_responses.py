from pydantic import BaseModel, Field

class ConstructionTypeResult(BaseModel):
    """Результат определения типа конструкции"""
    image_name: str = Field(..., description="Имя проанализированного изображения")
    construction_type: str = Field(..., description="Определенный тип конструкции")
    confidence: float = Field(..., description="Уровень уверенности модели в определении типа конструкции (0.0-1.0)", ge=0.0, le=1.0)

class ConstructionTypeResponse(BaseModel):
    """Ответ с результатом определения типа конструкции"""
    result: ConstructionTypeResult = Field(..., description="Результат определения типа конструкции")

class DefectDescriptionResult(BaseModel):
    """Результат описания дефектов"""
    image_name: str = Field(..., description="Имя проанализированного изображения")
    description: str = Field(..., description="Описание дефектов и повреждений")

class DefectDescriptionResponse(BaseModel):
    """Ответ с результатом описания дефектов"""
    result: DefectDescriptionResult = Field(..., description="Результат описания дефектов")
