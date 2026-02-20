from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from api.services.database import get_db
from api.services.auth_service import AuthService
from api.models.entities import User, WebUser

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Получение текущего internal пользователя по JWT токену. Отклоняет web-токены."""
    auth_service = AuthService(db)

    token = credentials.credentials

    token_data = auth_service.verify_token(token, "access")
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен аутентификации",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.get("scope") == "web":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Веб-токен не может использоваться для internal API",
        )

    user = await auth_service.get_user_by_email(token_data["email"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Получение текущего пользователя (опционально)"""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None

async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Получение текущего пользователя с проверкой роли администратора"""
    auth_service = AuthService(None)

    if not auth_service.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа"
        )

    return current_user

async def require_admin_role(
    current_user: User = Depends(get_current_user)
) -> User:
    """Зависимость для проверки роли администратора"""
    auth_service = AuthService(None)

    if not auth_service.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )

    return current_user


async def get_current_web_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> WebUser:
    """Получение текущего web-пользователя. Принимает только scope=web."""
    auth_service = AuthService(db)

    token = credentials.credentials

    token_data = auth_service.verify_token(token, "access")
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен аутентификации",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.get("scope") != "web":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется веб-токен",
        )

    result = await db.execute(
        select(WebUser).where(WebUser.email == token_data["email"])
    )
    web_user = result.scalar_one_or_none()

    if web_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not web_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт деактивирован",
        )

    return web_user


async def get_current_web_admin(
    web_user: WebUser = Depends(get_current_web_user)
) -> WebUser:
    """Web-пользователь с проверкой роли admin."""
    if web_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    return web_user
