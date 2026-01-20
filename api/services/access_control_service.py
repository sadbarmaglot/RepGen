from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional

from api.models.entities import Project, Object, Plan, Mark, Photo, ObjectMember

class AccessControlService:
    """Сервис для проверки прав доступа к ресурсам"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_project_access(self, project_id: int, user_id: int) -> bool:
        """Проверка доступа к проекту (владелец или участник объектов)"""
        # Проверяем является ли пользователь владельцем проекта
        owner_result = await self.db.execute(
            select(Project).where(
                and_(
                    Project.id == project_id,
                    Project.owner_id == user_id
                )
            )
        )
        if owner_result.scalar_one_or_none():
            return True
        
        # Проверяем является ли пользователь участником любого объекта в проекте
        member_result = await self.db.execute(
            select(ObjectMember)
            .join(Object)
            .where(
                and_(
                    Object.project_id == project_id,
                    ObjectMember.user_id == user_id
                )
            )
        )
        return member_result.scalars().first() is not None

    async def check_object_access(self, object_id: int, user_id: int) -> bool:
        """Проверка доступа к объекту (владелец проекта или участник объекта)"""
        # Проверяем является ли пользователь владельцем проекта
        owner_result = await self.db.execute(
            select(Object)
            .join(Project)
            .where(
                and_(
                    Object.id == object_id,
                    Project.owner_id == user_id
                )
            )
        )
        if owner_result.scalar_one_or_none():
            return True
        
        # Проверяем является ли пользователь участником объекта
        member_result = await self.db.execute(
            select(ObjectMember).where(
                and_(
                    ObjectMember.object_id == object_id,
                    ObjectMember.user_id == user_id
                )
            )
        )
        return member_result.scalar_one_or_none() is not None

    async def check_plan_access(self, plan_id: int, user_id: int) -> bool:
        """Проверка доступа к плану (через доступ к объекту)"""
        result = await self.db.execute(
            select(Plan).where(Plan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            return False
            
        return await self.check_object_access(plan.object_id, user_id)

    async def check_mark_access(self, mark_id: int, user_id: int) -> bool:
        """Проверка доступа к отметке (через доступ к плану)"""
        result = await self.db.execute(
            select(Mark).where(Mark.id == mark_id)
        )
        mark = result.scalar_one_or_none()
        
        if not mark:
            return False
            
        return await self.check_plan_access(mark.plan_id, user_id)

    async def check_photo_access(self, photo_id: int, user_id: int) -> bool:
        """Проверка доступа к фото (через доступ к отметке)"""
        result = await self.db.execute(
            select(Photo).where(Photo.id == photo_id)
        )
        photo = result.scalar_one_or_none()
        
        if not photo:
            return False
            
        return await self.check_mark_access(photo.mark_id, user_id)

    async def get_object_id_by_plan(self, plan_id: int) -> Optional[int]:
        """Получение ID объекта по ID плана"""
        result = await self.db.execute(
            select(Plan.object_id).where(Plan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def get_object_id_by_mark(self, mark_id: int) -> Optional[int]:
        """Получение ID объекта по ID отметки"""
        result = await self.db.execute(
            select(Plan.object_id)
            .select_from(Mark)
            .join(Plan)
            .where(Mark.id == mark_id)
        )
        return result.scalar_one_or_none()

    async def get_object_id_by_photo(self, photo_id: int) -> Optional[int]:
        """Получение ID объекта по ID фото"""
        result = await self.db.execute(
            select(Plan.object_id)
            .select_from(Photo)
            .join(Mark)
            .join(Plan)
            .where(Photo.id == photo_id)
        )
        return result.scalar_one_or_none()

    async def is_project_owner(self, project_id: int, user_id: int) -> bool:
        """Проверка является ли пользователь владельцем проекта"""
        return await self.check_project_access(project_id, user_id)

    async def is_object_member(self, object_id: int, user_id: int) -> bool:
        """Проверка является ли пользователь участником объекта"""
        result = await self.db.execute(
            select(ObjectMember).where(
                and_(
                    ObjectMember.object_id == object_id,
                    ObjectMember.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none() is not None
