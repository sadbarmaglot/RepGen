from typing import Optional, List
from pydantic import BaseModel, Field


class WearItemUpdateRequest(BaseModel):
    """Запрос на обновление одного элемента износа.

    Все поля кроме element_id опциональны. Используем семантику
    `model_dump(exclude_unset=True)` на стороне сервиса: поле обновляется
    только если оно явно передано (включая null, который означает «снять override»).
    """
    element_id: int
    assessment_percent: Optional[float] = Field(None, ge=0, le=100)
    group_weight: Optional[float] = Field(None, ge=0, le=100)
    element_weight: Optional[float] = Field(None, ge=0, le=100)
    calculated_weight: Optional[float] = Field(None, ge=0, le=100)


class WearBulkUpdateRequest(BaseModel):
    """Запрос на массовое обновление элементов износа"""
    items: List[WearItemUpdateRequest]


class WearItemPatchRequest(BaseModel):
    """Запрос на обновление одного элемента (PATCH).

    Все поля опциональны и имеют ту же семантику exclude_unset, что и в bulk.
    """
    assessment_percent: Optional[float] = Field(None, ge=0, le=100)
    group_weight: Optional[float] = Field(None, ge=0, le=100)
    element_weight: Optional[float] = Field(None, ge=0, le=100)
    calculated_weight: Optional[float] = Field(None, ge=0, le=100)