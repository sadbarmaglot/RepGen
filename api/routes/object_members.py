from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.database import get_db
from api.services.object_member_service import ObjectMemberService
from api.models.requests import (
    ObjectMemberAssignRequest,
    ObjectMemberUnassignRequest
)
from api.models.responses import (
    ObjectMemberResponse,
    ObjectMemberListResponse
)
from api.dependencies.auth_dependencies import get_current_user
from api.dependencies.access_dependencies import check_object_owner, check_object_access
from api.models.entities import User

router = APIRouter(prefix="/objects", tags=["object-members"])

@router.post("/{object_id}/members", response_model=ObjectMemberResponse, status_code=status.HTTP_201_CREATED)
async def assign_user_to_object(
    object_id: int = Depends(check_object_owner),
    assign_data: ObjectMemberAssignRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Назначение пользователя на объект (только владельцем проекта)"""
    try:
        service = ObjectMemberService(db)
        member = await service.assign_user_to_object(object_id, current_user.id, assign_data)
        return member
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{object_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_user_from_object(
    object_id: int = Depends(check_object_owner),
    unassign_data: ObjectMemberUnassignRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Снятие пользователя с объекта (только владельцем проекта)"""
    try:
        service = ObjectMemberService(db)
        success = await service.unassign_user_from_object(object_id, current_user.id, unassign_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Участник объекта не найден"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{object_id}/members", response_model=ObjectMemberListResponse)
async def get_object_members(
    object_id: int = Depends(check_object_access),
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка участников объекта"""
    try:
        service = ObjectMemberService(db)
        return await service.get_object_members(object_id, current_user, skip, limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
