from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


# Маппинг категорий для отображения
CONDITION_DISPLAY_MAP = {
    "cat_1": "Категория 1 (капитальный ремонт не требуется)",
    "cat_2": "Категория 2 (капитальный ремонт требуется)",
    "cat_3": "Категория 3 (требуется в приоритетном порядке)",
    "cat_4": "Категория 4 (требуется инструментальное обследование)",
}


class WearElementResponse(BaseModel):
    """Элемент справочника износа"""
    id: int
    code: str
    name: str
    parent_id: Optional[int] = None
    default_weight: Optional[float] = None
    sort_order: int

    class Config:
        from_attributes = True


class WearItemResponse(BaseModel):
    """Элемент износа с расчётами"""
    element_id: int
    code: str
    name: str
    parent_id: Optional[int] = None
    default_weight: Optional[float] = None
    assessment_percent: Optional[float] = None
    weighted_average: Optional[float] = None  # расчётное
    technical_condition: Optional[str] = None  # расчётное
    technical_condition_display: Optional[str] = None  # человекочитаемое
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WearCalculationResponse(BaseModel):
    """Полный ответ с расчётом износа объекта"""
    object_id: int
    items: List[WearItemResponse]
    total_wear: Optional[float] = None  # сумма weighted_average
    overall_condition: Optional[str] = None  # итоговая категория
    overall_condition_display: Optional[str] = None  # человекочитаемое

    class Config:
        from_attributes = True


class WearElementListResponse(BaseModel):
    """Список элементов справочника"""
    elements: List[WearElementResponse]
    total: int

    class Config:
        from_attributes = True
