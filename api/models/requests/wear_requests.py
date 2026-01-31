from typing import Optional, List
from pydantic import BaseModel, Field


class WearItemUpdateRequest(BaseModel):
    """Запрос на обновление одного элемента износа"""
    element_id: int
    assessment_percent: Optional[float] = Field(None, ge=0, le=100)


class WearBulkUpdateRequest(BaseModel):
    """Запрос на массовое обновление элементов износа"""
    items: List[WearItemUpdateRequest]


class WearItemPatchRequest(BaseModel):
    """Запрос на обновление одного элемента (PATCH)"""
    assessment_percent: Optional[float] = Field(None, ge=0, le=100)
