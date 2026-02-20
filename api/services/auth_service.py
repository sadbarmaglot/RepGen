from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from api.models.entities import User
from api.models.database import GlobalRoleType
from api.models.requests import UserCreate, UserLogin
from settings import (
    JWT_SECRET_KEY, 
    JWT_ALGORITHM, 
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES, 
    JWT_REFRESH_TOKEN_EXPIRE_DAYS
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Хеширование пароля"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Создание JWT access токена"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict):
        """Создание JWT refresh токена"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[dict]:
        """Проверка JWT токена. Возвращает {"email": ..., "scope": "internal"|"web"} или None"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != token_type:
                return None
            email: str = payload.get("sub")
            scope: str = payload.get("scope", "internal")
            return {"email": email, "scope": scope}
        except JWTError:
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def save_refresh_token(self, user: User, refresh_token: str):
        """Сохранение refresh токена в базе данных"""
        user.refresh_token = refresh_token
        user.refresh_token_expires = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        await self.db.commit()
    
    async def verify_refresh_token(self, refresh_token: str) -> Optional[User]:
        """Проверка refresh токена"""
        token_data = self.verify_token(refresh_token, "refresh")
        if not token_data:
            return None

        user = await self.get_user_by_email(token_data["email"])
        if not user or user.refresh_token != refresh_token:
            return None
        
        if user.refresh_token_expires:
            try:
                # Приводим к UTC если нужно
                if user.refresh_token_expires.tzinfo is None:
                    # Если дата без часового пояса, считаем её UTC
                    user.refresh_token_expires = user.refresh_token_expires.replace(tzinfo=timezone.utc)
                
                if user.refresh_token_expires < datetime.now(timezone.utc):
                    return None
            except Exception as e:
                print(f"Ошибка при проверке времени истечения refresh токена: {e}")
                return None
        
        return user
    
    async def revoke_refresh_token(self, user: User):
        """Отзыв refresh токена"""
        user.refresh_token = None
        user.refresh_token_expires = None
        await self.db.commit()
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Создание нового пользователя"""

        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
        
        hashed_password = self.get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            name=user_data.name
        )
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    async def login_user(self, login_data: UserLogin) -> dict:
        """Вход пользователя в систему"""
        user = await self.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user.last_login = datetime.now(timezone.utc)
        await self.db.commit()
        
        access_token = self.create_access_token(data={"sub": user.email, "scope": "internal"})
        refresh_token = self.create_refresh_token(data={"sub": user.email, "scope": "internal"})
        
        await self.save_refresh_token(user, refresh_token)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # в секундах
            "user": user
        }
    
    def is_admin(self, user: User) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user.global_role == GlobalRoleType.admin
    
    async def update_user_role(self, user_id: int, new_role: str) -> Optional[User]:
        """Обновление роли пользователя"""
        if new_role not in ["user", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Недопустимая роль. Доступные роли: user, admin"
            )
        
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.global_role = GlobalRoleType(new_role)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Обновление access токена с помощью refresh токена"""
        token_data = self.verify_token(refresh_token, "refresh")
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный или истекший refresh токен",
                headers={"WWW-Authenticate": "Bearer"},
            )

        scope = token_data.get("scope", "internal")
        user = await self.verify_refresh_token(refresh_token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный или истекший refresh токен",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = self.create_access_token(data={"sub": user.email, "scope": scope})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
