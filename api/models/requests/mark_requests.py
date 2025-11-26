from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from ..database.enums import MarkType, MarkVolumeUnit, DefectType

class MarkCreateRequest(BaseModel):
    """Запрос на создание отметки"""
    plan_id: int = Field(..., gt=0, description="ID плана")
    name: Optional[str] = Field(None, max_length=500, description="Название отметки")
    description: Optional[str] = Field(None, max_length=2000, description="Описание отметки")
    type: MarkType = Field(default=MarkType.other, description="Тип отметки")
    x: Optional[Decimal] = Field(None, ge=0, le=1, description="Координата X (от 0 до 1, не зависит от размеров изображения)")
    y: Optional[Decimal] = Field(None, ge=0, le=1, description="Координата Y (от 0 до 1, не зависит от размеров изображения)")
    is_horizontal: Optional[bool] = Field(default=True, description="Горизонтальная линия измерения")
    defect_volume_value: Optional[Decimal] = Field(None, ge=0, description="Значение объема дефекта")
    defect_volume_unit: Optional[MarkVolumeUnit] = Field(None, description="Единица измерения объема дефекта")
    defect_type: Optional[DefectType] = Field(None, description="Тип дефекта")

class MarkUpdateRequest(BaseModel):
    """Запрос на обновление отметки"""
    name: Optional[str] = Field(None, max_length=500, description="Новое название отметки")
    description: Optional[str] = Field(None, max_length=2000, description="Новое описание отметки")
    type: Optional[MarkType] = Field(None, description="Новый тип отметки")
    x: Optional[Decimal] = Field(None, ge=0, le=1, description="Новая координата X (от 0 до 1, не зависит от размеров изображения)")
    y: Optional[Decimal] = Field(None, ge=0, le=1, description="Новая координата Y (от 0 до 1, не зависит от размеров изображения)")
    is_horizontal: Optional[bool] = Field(None, description="Горизонтальная линия измерения")
    defect_volume_value: Optional[Decimal] = Field(None, ge=0, description="Новое значение объема дефекта")
    defect_volume_unit: Optional[MarkVolumeUnit] = Field(None, description="Новая единица измерения объема дефекта")
    defect_type: Optional[DefectType] = Field(None, description="Новый тип дефекта")
