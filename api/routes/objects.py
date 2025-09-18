from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.database import get_db
from api.services.object_service import ObjectService
from api.models.requests import (
    ObjectCreateRequest, 
    ObjectUpdateRequest
)
from api.models.responses import (
    ObjectResponse, 
    ObjectListResponse
)
from api.dependencies.auth_dependencies import get_current_user
from api.dependencies.access_dependencies import check_object_access, check_object_owner, check_project_access
from api.models.entities import User

router = APIRouter(prefix="/objects", tags=["objects"])

@router.post("/", response_model=ObjectResponse, status_code=status.HTTP_201_CREATED)
async def create_object(
    object_data: ObjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового объекта"""
    try:
        object_service = ObjectService(db)
        object_ = await object_service.create_object(current_user.id, object_data)
        return object_
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/project/{project_id}", response_model=ObjectListResponse)
async def get_project_objects(
    project_id: int = Depends(check_project_access),
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка объектов проекта (для владельцев и участников объектов)"""
    try:
        object_service = ObjectService(db)
        return await object_service.get_project_objects(project_id, current_user.id, skip, limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{object_id}", response_model=ObjectResponse)
async def get_object(
    object_id: int = Depends(check_object_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение объекта по ID"""
    object_service = ObjectService(db)
    object_ = await object_service.get_object(object_id, current_user.id)
    
    if not object_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объект не найден"
        )
    
    return object_

@router.put("/{object_id}", response_model=ObjectResponse)
async def update_object(
    object_id: int = Depends(check_object_owner),
    object_data: ObjectUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление объекта (название, адрес и описание)"""
    try:
        object_service = ObjectService(db)
        object_ = await object_service.update_object(object_id, current_user.id, object_data)
        
        if not object_:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Объект не найден"
            )
        
        return object_
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_object(
    object_id: int = Depends(check_object_owner),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление объекта"""
    try:
        object_service = ObjectService(db)
        success = await object_service.delete_object(object_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Объект не найден"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
