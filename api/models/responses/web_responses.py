from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class WebUserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    company: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class WebTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: WebUserResponse


class WebTokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class WebClientCreatedResponse(BaseModel):
    user: WebUserResponse
    generated_password: str


class WebClientListResponse(BaseModel):
    clients: List[WebUserResponse]
    total: int


class WebProjectAccessResponse(BaseModel):
    id: int
    web_user_id: int
    project_id: int
    granted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
