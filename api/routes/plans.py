from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.database import get_db
from api.services.plan_service import PlanService
from api.services.mark_service import MarkService
from api.models.requests import (
    PlanCreateRequest, 
    PlanUpdateRequest
)
from api.models.responses import (
    PlanResponse, 
    PlanListResponse,
    MarkWithPhotosListResponse
)
from api.dependencies.auth_dependencies import get_current_user
from api.dependencies.access_dependencies import check_plan_access
from api.models.entities import User

router = APIRouter(prefix="/plans", tags=["plans"])

@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: PlanCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового плана"""
    try:
        plan_service = PlanService(db)
        plan = await plan_service.create_plan(current_user.id, plan_data)
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/object/{object_id}", response_model=PlanListResponse)
async def get_object_plans(
    object_id: int,
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка планов объекта"""
    try:
        plan_service = PlanService(db)
        return await plan_service.get_object_plans(object_id, current_user.id, skip, limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение плана по ID"""
    plan_service = PlanService(db)
    plan = await plan_service.get_plan(plan_id, current_user.id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="План не найден или у вас нет прав доступа к нему"
        )
    
    return plan

@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: int = Depends(check_plan_access),
    plan_data: PlanUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление плана (владельцем проекта или участником объекта)"""
    try:
        plan_service = PlanService(db)
        plan = await plan_service.update_plan(plan_id, current_user.id, plan_data)
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="План не найден или у вас нет прав доступа к нему"
            )
        
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: int = Depends(check_plan_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление плана (владельцем проекта или участником объекта)"""
    try:
        plan_service = PlanService(db)
        success = await plan_service.delete_plan(plan_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="План не найден или у вас нет прав доступа к нему"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{plan_id}/marks-with-photos", response_model=MarkWithPhotosListResponse)
async def get_plan_marks_with_photos(
    plan_id: int,
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(500, ge=1, le=1000, description="Максимальное количество записей"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех отметок плана со всеми их фотографиями"""
    try:
        mark_service = MarkService(db)
        return await mark_service.get_plan_marks_with_photos(plan_id, current_user.id, skip, limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
