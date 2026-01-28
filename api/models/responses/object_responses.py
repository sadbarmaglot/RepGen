from pydantic import BaseModel, Field, computed_field
from typing import Optional
from datetime import datetime
from ..database.enums import ObjectStatus

# Маппинг статусов на русский язык (по строковым значениям)
OBJECT_STATUS_DISPLAY = {
    "not_started": "не начат",
    "in_progress": "в работе",
    "completed": "выполнено",
}

class ObjectResponse(BaseModel):
    """Ответ с информацией об объекте"""
    id: int = Field(..., description="ID объекта")
    project_id: int = Field(..., description="ID проекта")
    name: str = Field(..., description="Название объекта")
    address: Optional[str] = Field(None, description="Адрес объекта")
    description: Optional[str] = Field(None, description="Описание объекта")
    status: ObjectStatus = Field(..., description="Статус объекта")
    created_at: datetime = Field(..., description="Дата создания объекта")

    @computed_field
    @property
    def status_display(self) -> str:
        """Статус объекта на русском языке"""
        status_value = self.status.value if isinstance(self.status, ObjectStatus) else self.status
        return OBJECT_STATUS_DISPLAY.get(status_value, status_value)

    class Config:
        from_attributes = True
        use_enum_values = True

class ObjectListResponse(BaseModel):
    """Ответ со списком объектов"""
    objects: list[ObjectResponse] = Field(..., description="Список объектов")
    total: int = Field(..., description="Общее количество объектов")
