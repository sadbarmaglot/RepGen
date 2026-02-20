from pydantic import BaseModel, EmailStr
from typing import Optional


class WebUserLogin(BaseModel):
    email: EmailStr
    password: str


class WebClientCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    company: Optional[str] = None


class WebClientUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class WebProjectAssign(BaseModel):
    project_id: int
