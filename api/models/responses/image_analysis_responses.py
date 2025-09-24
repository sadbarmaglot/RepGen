from pydantic import BaseModel, Field

class ImageAnalysisResponse(BaseModel):
    """Ответ с результатом анализа изображения"""
    description: str = Field(..., description="Описание выявленного дефекта")
    recommendation: str = Field(..., description="Рекомендация по устранению")
    category: str = Field(..., description="Категория дефекта")
