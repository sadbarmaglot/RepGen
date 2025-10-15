from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.database import get_db
from api.services.mark_service import MarkService
from api.models.requests import (
    MarkCreateRequest, 
    MarkUpdateRequest
)
from api.models.responses import (
    MarkResponse, 
    MarkListResponse
)
from api.dependencies.auth_dependencies import get_current_user
from api.dependencies.access_dependencies import check_mark_access
from api.models.entities import User

router = APIRouter(prefix="/marks", tags=["marks"])

@router.post("/", response_model=MarkResponse, status_code=status.HTTP_201_CREATED)
async def create_mark(
    mark_data: MarkCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание новой отметки"""
    try:
        mark_service = MarkService(db)
        mark = await mark_service.create_mark(current_user.id, mark_data)
        return mark
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/plan/{plan_id}", response_model=MarkListResponse)
async def get_plan_marks(
    plan_id: int,
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(500, ge=1, le=1000, description="Максимальное количество записей"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка отметок плана"""
    try:
        mark_service = MarkService(db)
        return await mark_service.get_plan_marks(plan_id, current_user.id, skip, limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{mark_id}", response_model=MarkResponse)
async def get_mark(
    mark_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение отметки по ID"""
    mark_service = MarkService(db)
    mark = await mark_service.get_mark(mark_id, current_user.id)
    
    if not mark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отметка не найдена или у вас нет прав доступа к ней"
        )
    
    return mark

@router.put("/{mark_id}", response_model=MarkResponse)
async def update_mark(
    mark_id: int = Depends(check_mark_access),
    mark_data: MarkUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление отметки (владельцем проекта или участником объекта)"""
    try:
        mark_service = MarkService(db)
        mark = await mark_service.update_mark(mark_id, current_user.id, mark_data)
        
        if not mark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Отметка не найдена или у вас нет прав доступа к ней"
            )
        
        return mark
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{mark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mark(
    mark_id: int = Depends(check_mark_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление отметки (владельцем проекта или участником объекта)"""
    try:
        mark_service = MarkService(db)
        success = await mark_service.delete_mark(mark_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Отметка не найдена или у вас нет прав доступа к ней"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
