from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct
from sqlalchemy.exc import IntegrityError
from typing import Optional
from api.models.entities import Project, User, Object, ObjectMember
from api.models.requests import ProjectCreateRequest, ProjectUpdateRequest, ProjectChangeOwnerRequest
from api.models.responses import ProjectResponse, ProjectListResponse

class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(self, owner_id: int, project_data: ProjectCreateRequest) -> ProjectResponse:
        """Создание нового проекта"""

        result = await self.db.execute(select(User).where(User.id == owner_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Пользователь с указанным ID не найден")
        
        project = Project(
            owner_id=owner_id,
            name=project_data.name,
            description=project_data.description
        )
        
        try:
            self.db.add(project)
            await self.db.commit()
            await self.db.refresh(project)
            return ProjectResponse.model_validate(project)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при создании проекта: {str(e)}")

    async def get_project(self, project_id: int, user_id: int) -> Optional[ProjectResponse]:
        """Получение проекта по ID (для владельца или участника объектов)"""
        # Сначала проверяем является ли пользователь владельцем
        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.owner_id == user_id
            )
        )
        project = result.scalar_one_or_none()
        
        if project:
            return ProjectResponse.model_validate(project)
        
        # Если не владелец, проверяем участие в объектах проекта
        member_result = await self.db.execute(
            select(Project)
            .join(Object)
            .join(ObjectMember)
            .where(
                Project.id == project_id,
                ObjectMember.user_id == user_id
            )
        )
        project = member_result.scalar_one_or_none()
        
        if not project:
            return None
        
        return ProjectResponse.model_validate(project)

    async def get_user_projects(self, user_id: int, skip: int = 0, limit: int = 100) -> ProjectListResponse:
        """Получение списка проектов пользователя (владелец или участник объектов)"""
        
        # Получаем проекты где пользователь владелец
        owned_projects_result = await self.db.execute(
            select(Project).where(Project.owner_id == user_id)
        )
        owned_projects = owned_projects_result.scalars().all()
        
        # Получаем проекты где пользователь участник объектов
        member_projects_result = await self.db.execute(
            select(Project)
            .join(Object)
            .join(ObjectMember)
            .where(ObjectMember.user_id == user_id)
            .distinct()
        )
        member_projects = member_projects_result.scalars().all()
        
        # Объединяем проекты, исключая дубликаты
        all_projects = {}
        for project in owned_projects:
            all_projects[project.id] = project
        for project in member_projects:
            all_projects[project.id] = project
        
        projects_list = list(all_projects.values())
        total = len(projects_list)
        
        # Применяем пагинацию
        paginated_projects = projects_list[skip:skip + limit]
        
        project_responses = [ProjectResponse.model_validate(project) for project in paginated_projects]
        
        return ProjectListResponse(
            projects=project_responses,
            total=total
        )

    async def update_project(self, project_id: int, user_id: int, project_data: ProjectUpdateRequest) -> Optional[ProjectResponse]:
        """Обновление проекта (только владельцем)"""
        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.owner_id == user_id
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            return None
        
        if project_data.name is not None:
            project.name = project_data.name
        if project_data.description is not None:
            project.description = project_data.description
        
        try:
            await self.db.commit()
            await self.db.refresh(project)
            return ProjectResponse.model_validate(project)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при обновлении проекта: {str(e)}")

    async def change_project_owner(self, project_id: int, current_owner_id: int, new_owner_data: ProjectChangeOwnerRequest) -> Optional[ProjectResponse]:
        """Смена владельца проекта"""

        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.owner_id == current_owner_id
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            return None
        
        user_result = await self.db.execute(select(User).where(User.id == new_owner_data.new_owner_id))
        new_owner = user_result.scalar_one_or_none()
        if not new_owner:
            raise ValueError("Пользователь с указанным ID не найден")
        
        project.owner_id = new_owner_data.new_owner_id
        
        try:
            await self.db.commit()
            await self.db.refresh(project)
            return ProjectResponse.model_validate(project)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при смене владельца проекта: {str(e)}")

    async def delete_project(self, project_id: int, user_id: int) -> bool:
        """Удаление проекта (только владельцем)"""
        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.owner_id == user_id
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            return False
        
        try:
            await self.db.delete(project)
            await self.db.commit()
            return True
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при удалении проекта: {str(e)}")

    async def get_all_projects(self, skip: int = 0, limit: int = 100) -> ProjectListResponse:
        """Получение всех проектов (для администраторов)"""
        # Получаем общее количество
        count_result = await self.db.execute(select(Project))
        total = len(count_result.scalars().all())
        
        # Получаем проекты с пагинацией
        result = await self.db.execute(
            select(Project)
            .offset(skip)
            .limit(limit)
        )
        projects = result.scalars().all()
        
        project_responses = [ProjectResponse.model_validate(project) for project in projects]
        
        return ProjectListResponse(
            projects=project_responses,
            total=total
        )
