from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.database import get_db
from api.services.project_service import ProjectService
from api.models.requests import (
    ProjectCreateRequest, 
    ProjectUpdateRequest, 
    ProjectChangeOwnerRequest
)
from api.models.responses import (
    ProjectResponse, 
    ProjectListResponse
)
from api.dependencies.auth_dependencies import get_current_user, require_admin_role
from api.dependencies.access_dependencies import check_project_access, check_project_owner
from api.models.entities import User

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового проекта"""
    try:
        project_service = ProjectService(db)
        project = await project_service.create_project(current_user.id, project_data)
        return project
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=ProjectListResponse)
async def get_user_projects(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка проектов текущего пользователя"""
    project_service = ProjectService(db)
    return await project_service.get_user_projects(current_user.id, skip, limit)

@router.get("/all", response_model=ProjectListResponse)
async def get_all_projects(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    _: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех проектов (только для администраторов)"""
    project_service = ProjectService(db)
    return await project_service.get_all_projects(skip, limit)

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int = Depends(check_project_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение проекта по ID"""
    project_service = ProjectService(db)
    project = await project_service.get_project(project_id, current_user.id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int = Depends(check_project_owner),
    project_data: ProjectUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление проекта (название и описание)"""
    project_service = ProjectService(db)
    project = await project_service.update_project(project_id, current_user.id, project_data)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    return project

@router.patch("/{project_id}/change-owner", response_model=ProjectResponse)
async def change_project_owner(
    project_id: int,
    owner_data: ProjectChangeOwnerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Смена владельца проекта"""
    try:
        project_service = ProjectService(db)
        project = await project_service.change_project_owner(project_id, current_user.id, owner_data)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Проект не найден или у вас нет прав доступа к нему"
            )
        
        return project
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление проекта"""
    project_service = ProjectService(db)
    success = await project_service.delete_project(project_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден или у вас нет прав доступа к нему"
        )
