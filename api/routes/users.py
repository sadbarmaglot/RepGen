from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from api.services.database import get_db
from api.models.entities import User
from api.models.responses import UserResponse
from api.dependencies.auth_dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка всех пользователей в системе
    
    Требует аутентификации. Возвращает список всех пользователей с их основной информацией.
    """
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    
    return [UserResponse.model_validate(user) for user in users]


