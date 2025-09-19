from pydantic import BaseModel, Field
from typing import List

class ObjectMemberResponse(BaseModel):
    """Ответ с информацией об участнике объекта"""
    id: int = Field(..., description="ID связи")
    object_id: int = Field(..., description="ID объекта")
    user_id: int = Field(..., description="ID пользователя")
    user_name: str = Field(..., description="Имя пользователя")
    user_email: str = Field(..., description="Email пользователя")
    
    class Config:
        from_attributes = True

class ObjectMemberListResponse(BaseModel):
    """Ответ со списком участников объекта"""
    members: List[ObjectMemberResponse] = Field(default_factory=list, description="Список участников")
    total: int = Field(..., description="Общее количество участников")
