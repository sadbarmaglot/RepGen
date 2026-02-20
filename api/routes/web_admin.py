from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.database import get_db
from api.services.web_auth_service import WebAuthService
from api.models.requests import WebClientCreate, WebClientUpdate, WebProjectAssign
from api.models.responses import (
    WebUserResponse, WebClientCreatedResponse, WebClientListResponse,
    WebProjectAccessResponse, ProjectResponse, ProjectListResponse,
)
from api.models.entities import WebUser
from api.dependencies.auth_dependencies import get_current_web_admin

router = APIRouter(prefix="/web/admin", tags=["web-admin"])


@router.get("/clients", response_model=WebClientListResponse)
async def list_clients(
    _: WebUser = Depends(get_current_web_admin),
    db: AsyncSession = Depends(get_db),
):
    service = WebAuthService(db)
    clients = await service.list_clients()
    return WebClientListResponse(
        clients=[WebUserResponse.model_validate(c) for c in clients],
        total=len(clients),
    )


@router.post("/clients", response_model=WebClientCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: WebClientCreate,
    _: WebUser = Depends(get_current_web_admin),
    db: AsyncSession = Depends(get_db),
):
    service = WebAuthService(db)
    user, raw_password = await service.create_client(data.email, data.name, data.company)
    return WebClientCreatedResponse(
        user=WebUserResponse.model_validate(user),
        generated_password=raw_password,
    )


@router.get("/clients/{client_id}", response_model=WebUserResponse)
async def get_client(
    client_id: int,
    _: WebUser = Depends(get_current_web_admin),
    db: AsyncSession = Depends(get_db),
):
    service = WebAuthService(db)
    client = await service.get_client(client_id)
    return WebUserResponse.model_validate(client)


@router.patch("/clients/{client_id}", response_model=WebUserResponse)
async def update_client(
    client_id: int,
    data: WebClientUpdate,
    _: WebUser = Depends(get_current_web_admin),
    db: AsyncSession = Depends(get_db),
):
    service = WebAuthService(db)
    client = await service.update_client(client_id, data.model_dump(exclude_unset=True))
    return WebUserResponse.model_validate(client)


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    _: WebUser = Depends(get_current_web_admin),
    db: AsyncSession = Depends(get_db),
):
    service = WebAuthService(db)
    await service.delete_client(client_id)


@router.post("/clients/{client_id}/reset-password", response_model=WebClientCreatedResponse)
async def reset_client_password(
    client_id: int,
    _: WebUser = Depends(get_current_web_admin),
    db: AsyncSession = Depends(get_db),
):
    service = WebAuthService(db)
    user, raw_password = await service.reset_password(client_id)
    return WebClientCreatedResponse(
        user=WebUserResponse.model_validate(user),
        generated_password=raw_password,
    )


@router.get("/clients/{client_id}/projects", response_model=ProjectListResponse)
async def get_client_projects(
    client_id: int,
    _: WebUser = Depends(get_current_web_admin),
    db: AsyncSession = Depends(get_db),
):
    service = WebAuthService(db)
    projects = await service.get_client_projects(client_id)
    return ProjectListResponse(
        projects=[ProjectResponse.model_validate(p) for p in projects],
        total=len(projects),
    )


@router.post("/clients/{client_id}/projects", response_model=WebProjectAccessResponse, status_code=status.HTTP_201_CREATED)
async def assign_project(
    client_id: int,
    data: WebProjectAssign,
    _: WebUser = Depends(get_current_web_admin),
    db: AsyncSession = Depends(get_db),
):
    service = WebAuthService(db)
    access = await service.assign_project(client_id, data.project_id)
    return WebProjectAccessResponse.model_validate(access)


@router.delete("/clients/{client_id}/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_project(
    client_id: int,
    project_id: int,
    _: WebUser = Depends(get_current_web_admin),
    db: AsyncSession = Depends(get_db),
):
    service = WebAuthService(db)
    await service.unassign_project(client_id, project_id)
