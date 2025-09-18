from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.database import get_db
from api.services.photo_service import PhotoService
from api.models.requests import (
    PhotoCreateRequest, 
    PhotoUpdateRequest
)
from api.models.responses import (
    PhotoResponse, 
    PhotoListResponse
)
from api.dependencies.auth_dependencies import get_current_user
from api.dependencies.access_dependencies import check_photo_access
from api.models.entities import User

router = APIRouter(prefix="/photos", tags=["photos"])

@router.post("/", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def create_photo(
    photo_data: PhotoCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание новой фотографии"""
    try:
        photo_service = PhotoService(db)
        photo = await photo_service.create_photo(current_user.id, photo_data)
        return photo
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/mark/{mark_id}", response_model=PhotoListResponse)
async def get_mark_photos(
    mark_id: int,
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка фотографий отметки"""
    try:
        photo_service = PhotoService(db)
        return await photo_service.get_mark_photos(mark_id, current_user.id, skip, limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение фотографии по ID"""
    photo_service = PhotoService(db)
    photo = await photo_service.get_photo(photo_id, current_user.id)
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фотография не найдена или у вас нет прав доступа к ней"
        )
    
    return photo

@router.put("/{photo_id}", response_model=PhotoResponse)
async def update_photo(
    photo_id: int = Depends(check_photo_access),
    photo_data: PhotoUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление фотографии (владельцем проекта или участником объекта)"""
    try:
        photo_service = PhotoService(db)
        photo = await photo_service.update_photo(photo_id, current_user.id, photo_data)
        
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Фотография не найдена или у вас нет прав доступа к ней"
            )
        
        return photo
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    photo_id: int = Depends(check_photo_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление фотографии (владельцем проекта или участником объекта)"""
    try:
        photo_service = PhotoService(db)
        success = await photo_service.delete_photo(photo_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Фотография не найдена или у вас нет прав доступа к ней"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
