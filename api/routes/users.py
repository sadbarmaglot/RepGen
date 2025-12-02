from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from api.services.database import get_db
from api.services.user_service import UserService
from api.services.auth_service import AuthService
from api.models.entities import User
from api.models.responses import UserResponse
from api.models.database.enums import GlobalRoleType
from api.dependencies.auth_dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка пользователей в системе
    
    Требует аутентификации. 
    - Администраторы видят всех пользователей
    - Обычные пользователи видят только пользователей из своей группы (role_type)
    """
    auth_service = AuthService(db)
    is_admin = auth_service.is_admin(current_user)
    
    if is_admin:
        result = await db.execute(select(User).order_by(User.created_at.desc()))
    else:
        result = await db.execute(
            select(User)
            .where(User.role_type == current_user.role_type)
            .order_by(User.created_at.desc())
        )
    
    users = result.scalars().all()
    return [UserResponse.model_validate(user) for user in users]


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Удаление пользователя
    
    Пользователь может удалить только себя, администратор может удалить любого пользователя.
    При удалении пользователя:
    - Проекты пользователя передаются другому пользователю (администратору или первому пользователю)
    - Если новый владелец был участником объектов в передаваемых проектах, его записи ObjectMember удаляются
      (так как владелец проекта автоматически имеет доступ ко всем объектам)
    - Записи участия удаляемого пользователя в объектах (ObjectMember) удаляются автоматически
    - Проекты и связанные данные (объекты, планы, отметки, фотографии) НЕ удаляются
    """
    auth_service = AuthService(db)
    is_admin = auth_service.is_admin(current_user)
    
    if not is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете удалить только свой аккаунт"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user_to_delete = result.scalar_one_or_none()
    
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Не позволяем удалить самого себя, если это последний администратор
    if is_admin and current_user.id == user_id:
        # Проверяем, есть ли другие администраторы
        admin_result = await db.execute(
            select(User).where(
                User.global_role == GlobalRoleType.admin,
                User.id != user_id
            )
        )
        other_admins = admin_result.scalars().all()
        if not other_admins:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невозможно удалить последнего администратора системы"
            )
    
    try:
        user_service = UserService(db)
        success = await user_service.delete_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

