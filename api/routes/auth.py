from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.database import get_db
from api.services.auth_service import AuthService
from api.models.requests import UserCreate, UserLogin, TokenRefresh
from api.models.responses import UserResponse, Token
from api.dependencies.auth_dependencies import get_current_user
from api.models.entities import User

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя
    
    Создает нового пользователя в системе, если пользователя с таким email еще нет.
    """
    auth_service = AuthService(db)
    user = await auth_service.create_user(user_data)
    return UserResponse.model_validate(user)

@router.post("/login", response_model=Token)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Вход пользователя в систему
    
    Проверяет email и пароль, возвращает access токен и refresh токен для аутентификации.
    Access токен живет 24 часа, refresh токен - 30 дней.
    """
    auth_service = AuthService(db)
    result = await auth_service.login_user(login_data)
    
    return Token(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"]
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Получение информации о текущем пользователе
    
    Требует аутентификации. Возвращает данные текущего пользователя.
    """
    return UserResponse.model_validate(current_user)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление JWT токена с помощью refresh токена
    
    Создает новый access токен для пользователя с валидным refresh токеном.
    """
    auth_service = AuthService(db)
    result = await auth_service.refresh_access_token(token_data.refresh_token)
    
    return Token(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"]
    )

@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Выход пользователя из системы
    
    Отзывает refresh токен пользователя.
    """
    auth_service = AuthService(db)
    await auth_service.revoke_refresh_token(current_user)
    
    return {"message": "Успешный выход из системы"}
