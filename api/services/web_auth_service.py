import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.entities import WebUser, WebUserProjectAccess, Project
from api.services.auth_service import AuthService, pwd_context
from settings import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_REFRESH_TOKEN_EXPIRE_DAYS


class WebAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._auth = AuthService(db)

    # --- Auth ---

    async def login(self, email: str, password: str) -> dict:
        result = await self.db.execute(
            select(WebUser).where(WebUser.email == email)
        )
        user = result.scalar_one_or_none()

        if not user or not pwd_context.verify(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Аккаунт деактивирован",
            )

        user.last_login = datetime.now(timezone.utc)

        access_token = self._auth.create_access_token(
            data={"sub": user.email, "scope": "web"}
        )
        refresh_token = self._auth.create_refresh_token(
            data={"sub": user.email, "scope": "web"}
        )

        user.refresh_token = hashlib.sha256(refresh_token.encode()).hexdigest()
        user.refresh_token_expires = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        await self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user,
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        token_data = self._auth.verify_token(refresh_token, "refresh")
        if not token_data or token_data.get("scope") != "web":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный или истекший refresh токен",
            )

        result = await self.db.execute(
            select(WebUser).where(WebUser.email == token_data["email"])
        )
        user = result.scalar_one_or_none()

        if not user or user.refresh_token != hashlib.sha256(refresh_token.encode()).hexdigest():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный или истекший refresh токен",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Аккаунт деактивирован",
            )

        if user.refresh_token_expires:
            expires = user.refresh_token_expires
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh токен истёк",
                )

        access_token = self._auth.create_access_token(
            data={"sub": user.email, "scope": "web"}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def revoke_token(self, web_user: WebUser):
        web_user.refresh_token = None
        web_user.refresh_token_expires = None
        await self.db.commit()

    # --- Admin CRUD ---

    @staticmethod
    def _generate_password(length: int = 12) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def create_client(self, email: str, name: Optional[str] = None, company: Optional[str] = None) -> tuple[WebUser, str]:
        existing = await self.db.execute(
            select(WebUser).where(WebUser.email == email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует",
            )

        raw_password = self._generate_password()
        user = WebUser(
            email=email,
            password_hash=pwd_context.hash(raw_password),
            name=name,
            company=company,
            role="client",
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user, raw_password

    async def update_client(self, client_id: int, data: dict) -> WebUser:
        result = await self.db.execute(
            select(WebUser).where(WebUser.id == client_id, WebUser.role == "client")
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клиент не найден")

        for field in ("name", "company", "email", "is_active"):
            if field in data and data[field] is not None:
                setattr(user, field, data[field])

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_client(self, client_id: int):
        result = await self.db.execute(
            select(WebUser).where(WebUser.id == client_id, WebUser.role == "client")
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клиент не найден")

        await self.db.delete(user)
        await self.db.commit()

    async def reset_password(self, client_id: int) -> tuple[WebUser, str]:
        result = await self.db.execute(
            select(WebUser).where(WebUser.id == client_id, WebUser.role == "client")
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клиент не найден")

        raw_password = self._generate_password()
        user.password_hash = pwd_context.hash(raw_password)
        user.refresh_token = None
        user.refresh_token_expires = None
        await self.db.commit()
        await self.db.refresh(user)
        return user, raw_password

    async def list_clients(self) -> list[WebUser]:
        result = await self.db.execute(
            select(WebUser).where(WebUser.role == "client").order_by(WebUser.id)
        )
        return list(result.scalars().all())

    async def get_client(self, client_id: int) -> WebUser:
        result = await self.db.execute(
            select(WebUser).where(WebUser.id == client_id, WebUser.role == "client")
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клиент не найден")
        return user

    # --- Project access ---

    async def assign_project(self, web_user_id: int, project_id: int) -> WebUserProjectAccess:
        # Проверяем существование пользователя и проекта
        user_result = await self.db.execute(select(WebUser).where(WebUser.id == web_user_id))
        if not user_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        project_result = await self.db.execute(select(Project).where(Project.id == project_id))
        if not project_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Проект не найден")

        # Проверяем дубликат
        existing = await self.db.execute(
            select(WebUserProjectAccess).where(
                WebUserProjectAccess.web_user_id == web_user_id,
                WebUserProjectAccess.project_id == project_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Проект уже назначен")

        access = WebUserProjectAccess(web_user_id=web_user_id, project_id=project_id)
        self.db.add(access)
        await self.db.commit()
        await self.db.refresh(access)
        return access

    async def unassign_project(self, web_user_id: int, project_id: int):
        result = await self.db.execute(
            select(WebUserProjectAccess).where(
                WebUserProjectAccess.web_user_id == web_user_id,
                WebUserProjectAccess.project_id == project_id,
            )
        )
        access = result.scalar_one_or_none()
        if not access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Назначение не найдено")

        await self.db.delete(access)
        await self.db.commit()

    async def get_user_projects(self, web_user: WebUser) -> list[Project]:
        if web_user.role == "admin":
            result = await self.db.execute(select(Project).order_by(Project.id))
            return list(result.scalars().all())

        result = await self.db.execute(
            select(Project)
            .join(WebUserProjectAccess, WebUserProjectAccess.project_id == Project.id)
            .where(WebUserProjectAccess.web_user_id == web_user.id)
            .order_by(Project.id)
        )
        return list(result.scalars().all())

    async def check_project_access(self, web_user: WebUser, project_id: int) -> bool:
        if web_user.role == "admin":
            return True

        result = await self.db.execute(
            select(WebUserProjectAccess).where(
                WebUserProjectAccess.web_user_id == web_user.id,
                WebUserProjectAccess.project_id == project_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_client_projects(self, client_id: int) -> list[Project]:
        result = await self.db.execute(
            select(Project)
            .join(WebUserProjectAccess, WebUserProjectAccess.project_id == Project.id)
            .where(WebUserProjectAccess.web_user_id == client_id)
            .order_by(Project.id)
        )
        return list(result.scalars().all())
