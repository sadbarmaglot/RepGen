from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProjectResponse(BaseModel):
    """Ответ с информацией о проекте"""
    id: int = Field(..., description="ID проекта")
    owner_id: int = Field(..., description="ID владельца проекта")
    owner_name: Optional[str] = Field(None, description="Имя владельца проекта")
    client_company: Optional[str] = Field(None, description="Компания назначенного клиента")
    name: str = Field(..., description="Название проекта")
    description: Optional[str] = Field(None, description="Описание проекта")
    created_at: datetime = Field(..., description="Дата создания проекта")

    @classmethod
    def from_project(cls, project) -> "ProjectResponse":
        client_company = None
        if project.web_user_access:
            first_access = project.web_user_access[0]
            if first_access.web_user:
                client_company = first_access.web_user.company
        return cls(
            id=project.id,
            owner_id=project.owner_id,
            owner_name=project.owner.name if project.owner else None,
            client_company=client_company,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
        )

    class Config:
        from_attributes = True

class ProjectListResponse(BaseModel):
    """Ответ со списком проектов"""
    projects: list[ProjectResponse] = Field(..., description="Список проектов")
    total: int = Field(..., description="Общее количество проектов")
