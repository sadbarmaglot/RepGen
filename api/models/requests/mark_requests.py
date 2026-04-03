from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from decimal import Decimal
from ..database.enums import MarkType, MarkVolumeUnit, DefectType

# Маппинг устаревших значений defect_type на актуальные
LEGACY_DEFECT_TYPE_MAP = {
    "non_project_holes": "through_hole",
}

def _migrate_legacy_defect_type(v):
    if isinstance(v, str) and v in LEGACY_DEFECT_TYPE_MAP:
        return LEGACY_DEFECT_TYPE_MAP[v]
    return v

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
    zone_points: Optional[List[float]] = Field(None, description="Полигон зоны покрытия [x1,y1, x2,y2, ...]")
    crack_points: Optional[List[float]] = Field(None, description="Трещина [x1,y1, x2,y2]")

    @field_validator("defect_type", mode="before")
    @classmethod
    def migrate_defect_type(cls, v):
        return _migrate_legacy_defect_type(v)

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
    zone_points: Optional[List[float]] = Field(None, description="Полигон зоны покрытия [x1,y1, x2,y2, ...]")
    crack_points: Optional[List[float]] = Field(None, description="Трещина [x1,y1, x2,y2]")

    @field_validator("defect_type", mode="before")
    @classmethod
    def migrate_defect_type(cls, v):
        return _migrate_legacy_defect_type(v)
