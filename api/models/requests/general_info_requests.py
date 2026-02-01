from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class GeneralInfoUpdateRequest(BaseModel):
    """Запрос на обновление общей информации объекта"""

    # Даты
    inspection_date: Optional[date] = None
    inspection_duration: Optional[int] = Field(None, ge=0)

    # Адресация
    fias_code: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    # Характеристики дома
    apartments_count: Optional[int] = Field(None, ge=0)
    non_residential_count: Optional[int] = Field(None, ge=0)
    total_area: Optional[float] = Field(None, ge=0)
    living_area: Optional[float] = Field(None, ge=0)
    floors_count: Optional[int] = Field(None, ge=0)
    entrances_count: Optional[int] = Field(None, ge=0)
    construction_year: Optional[int] = Field(None, ge=1700, le=2200)
    project_type: Optional[str] = Field(None, max_length=255)

    # Статус и история
    object_status: Optional[str] = None
    last_repair: Optional[str] = None
    replanning: Optional[str] = None

    # Организация
    organization: Optional[str] = Field(None, max_length=255)
