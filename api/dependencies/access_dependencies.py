from fastapi import HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.database import get_db
from api.services.access_control_service import AccessControlService
from api.dependencies.auth_dependencies import get_current_user
from api.models.entities import User, Object, Plan, Mark, Photo


async def check_project_access(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dependency для проверки доступа к проекту"""
    access_control = AccessControlService(db, is_admin=current_user.is_admin)

    if not await access_control.check_project_access(project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет доступа к этому проекту"
        )

    return project_id

async def check_object_access(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dependency для проверки доступа к объекту"""
    access_control = AccessControlService(db, is_admin=current_user.is_admin)

    if not await access_control.check_object_access(object_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет доступа к этому объекту"
        )

    return object_id

async def check_plan_access(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dependency для проверки доступа к плану"""
    access_control = AccessControlService(db, is_admin=current_user.is_admin)

    if not await access_control.check_plan_access(plan_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет доступа к этому плану"
        )

    return plan_id

async def check_mark_access(
    mark_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dependency для проверки доступа к отметке"""
    access_control = AccessControlService(db, is_admin=current_user.is_admin)

    if not await access_control.check_mark_access(mark_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет доступа к этой отметке"
        )

    return mark_id

async def check_photo_access(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dependency для проверки доступа к фото"""
    access_control = AccessControlService(db, is_admin=current_user.is_admin)

    if not await access_control.check_photo_access(photo_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет доступа к этому фото"
        )

    return photo_id

async def check_project_owner(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dependency для проверки что пользователь является владельцем проекта"""
    access_control = AccessControlService(db, is_admin=current_user.is_admin)

    if not await access_control.is_project_owner(project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только владелец проекта может выполнить это действие"
        )

    return project_id

async def check_object_owner(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dependency для проверки что пользователь является владельцем проекта объекта"""
    if current_user.is_admin:
        return object_id

    result = await db.execute(select(Object.project_id).where(Object.id == object_id))
    project_id = result.scalar_one_or_none()

    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объект не найден"
        )

    access_control = AccessControlService(db)
    if not await access_control.is_project_owner(project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только владелец проекта может редактировать этот объект"
        )

    return object_id

async def check_plan_owner(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dependency для проверки что пользователь является владельцем проекта плана"""
    if current_user.is_admin:
        return plan_id

    result = await db.execute(
        select(Object.project_id)
        .select_from(Plan)
        .join(Object)
        .where(Plan.id == plan_id)
    )
    project_id = result.scalar_one_or_none()

    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="План не найден"
        )

    access_control = AccessControlService(db)
    if not await access_control.is_project_owner(project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только владелец проекта может редактировать этот план"
        )

    return plan_id

async def check_mark_owner(
    mark_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dependency для проверки что пользователь является владельцем проекта отметки"""
    if current_user.is_admin:
        return mark_id

    result = await db.execute(
        select(Object.project_id)
        .select_from(Mark)
        .join(Plan)
        .join(Object)
        .where(Mark.id == mark_id)
    )
    project_id = result.scalar_one_or_none()

    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отметка не найдена"
        )

    access_control = AccessControlService(db)
    if not await access_control.is_project_owner(project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только владелец проекта может редактировать эту отметку"
        )

    return mark_id

async def check_photo_owner(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dependency для проверки что пользователь является владельцем проекта фото"""
    if current_user.is_admin:
        return photo_id

    result = await db.execute(
        select(Object.project_id)
        .select_from(Photo)
        .join(Mark)
        .join(Plan)
        .join(Object)
        .where(Photo.id == photo_id)
    )
    project_id = result.scalar_one_or_none()

    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фото не найдено"
        )

    access_control = AccessControlService(db)
    if not await access_control.is_project_owner(project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только владелец проекта может редактировать это фото"
        )

    return photo_id
