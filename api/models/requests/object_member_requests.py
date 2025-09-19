from pydantic import BaseModel, Field
from typing import Optional

class ObjectMemberAssignRequest(BaseModel):
    """Запрос на назначение пользователя на объект"""
    user_id: int = Field(..., description="ID пользователя")
    
class ObjectMemberUnassignRequest(BaseModel):
    """Запрос на снятие пользователя с объекта"""
    user_id: int = Field(..., description="ID пользователя")

class ObjectMemberListRequest(BaseModel):
    """Запрос на получение списка участников объекта"""
    skip: Optional[int] = Field(0, ge=0, description="Количество пропускаемых записей")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Максимальное количество записей")
