from pydantic import BaseModel, EmailStr
from typing import Optional
from ..database.enums import GlobalRoleType

class UserCreate(BaseModel):
    """Запрос на создание пользователя"""
    email: EmailStr
    password: str
    name: Optional[str] = None
    global_role: Optional[GlobalRoleType] = GlobalRoleType.user

class UserLogin(BaseModel):
    """Запрос на вход пользователя"""
    email: EmailStr
    password: str
    
class TokenRefresh(BaseModel):
    """Запрос на обновление токена"""
    refresh_token: str

class TokenData(BaseModel):
    """Данные токена"""
    email: Optional[str] = None
