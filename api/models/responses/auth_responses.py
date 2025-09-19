from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserResponse(BaseModel):
    """Ответ с информацией о пользователе"""
    id: int
    email: str
    name: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """Ответ с токенами"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
