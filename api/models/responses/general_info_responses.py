from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel


class GeneralInfoResponse(BaseModel):
    """Ответ с общей информацией объекта"""

    object_id: int

    # Даты
    inspection_date: Optional[date] = None
    inspection_duration: Optional[int] = None

    # Адресация
    fias_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Характеристики дома
    apartments_count: Optional[int] = None
    non_residential_count: Optional[int] = None
    total_area: Optional[float] = None
    living_area: Optional[float] = None
    floors_count: Optional[int] = None
    entrances_count: Optional[int] = None
    construction_year: Optional[int] = None
    project_type: Optional[str] = None

    # Статус и история
    object_status: Optional[str] = None
    last_repair: Optional[str] = None
    replanning: Optional[str] = None

    # Организация
    organization: Optional[str] = None

    # Конструктивные решения
    construction_solutions: Optional[List[dict]] = None

    # Упрощенное заключение (для нежилых зданий)
    simplified_conclusion: Optional[dict] = None

    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
