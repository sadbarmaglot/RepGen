from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import aliased
from typing import Optional

from api.models.entities import Project, Object, Plan, Mark, Photo, ObjectMember, User
from api.models.database.enums import RoleType

class AccessControlService:
    """Сервис для проверки прав доступа к ресурсам"""

    def __init__(self, db: AsyncSession, is_admin: bool = False):
        self.db = db
        self.is_admin = is_admin
        # Кэш role_type запрашивающих пользователей в рамках одного запроса
        # (чтобы не делать lookup на каждый объект при фильтрации списков)
        self._role_type_cache: dict[int, Optional[RoleType]] = {}

    async def _get_role_type(self, user_id: int) -> Optional[RoleType]:
        """Получение группы (role_type) пользователя с кэшированием на время запроса"""
        if user_id not in self._role_type_cache:
            result = await self.db.execute(
                select(User.role_type).where(User.id == user_id)
            )
            self._role_type_cache[user_id] = result.scalar_one_or_none()
        return self._role_type_cache[user_id]

    async def _check_group_access(self, project_id: int, user_id: int) -> bool:
        """Доступ по группе: role_type пользователя совпадает с role_type владельца проекта.

        Для пользователей с role_type=all групповое правило не применяется.
        """
        user_role_type = await self._get_role_type(user_id)
        if user_role_type is None or user_role_type == RoleType.all:
            return False

        owner = aliased(User)
        result = await self.db.execute(
            select(Project.id)
            .join(owner, Project.owner_id == owner.id)
            .where(
                and_(
                    Project.id == project_id,
                    owner.role_type == user_role_type,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def check_project_access(self, project_id: int, user_id: int) -> bool:
        """Проверка доступа к проекту (владелец или участник объектов)"""
        if self.is_admin:
            return True
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
        if member_result.scalars().first() is not None:
            return True

        # Проверяем доступ по группе (role_type владельца проекта)
        return await self._check_group_access(project_id, user_id)

    async def check_object_access(self, object_id: int, user_id: int) -> bool:
        """Проверка доступа к объекту (владелец проекта или участник объекта)"""
        if self.is_admin:
            return True
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
        if member_result.scalar_one_or_none() is not None:
            return True

        # Проверяем доступ по группе (role_type владельца проекта объекта)
        project_id_result = await self.db.execute(
            select(Object.project_id).where(Object.id == object_id)
        )
        project_id = project_id_result.scalar_one_or_none()
        if project_id is None:
            return False
        return await self._check_group_access(project_id, user_id)

    async def check_plan_access(self, plan_id: int, user_id: int) -> bool:
        """Проверка доступа к плану (через доступ к объекту)"""
        if self.is_admin:
            return True
        result = await self.db.execute(
            select(Plan).where(Plan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            return False
            
        return await self.check_object_access(plan.object_id, user_id)

    async def check_mark_access(self, mark_id: int, user_id: int) -> bool:
        """Проверка доступа к отметке (через доступ к плану)"""
        if self.is_admin:
            return True
        result = await self.db.execute(
            select(Mark).where(Mark.id == mark_id)
        )
        mark = result.scalar_one_or_none()
        
        if not mark:
            return False
            
        return await self.check_plan_access(mark.plan_id, user_id)

    async def check_photo_access(self, photo_id: int, user_id: int) -> bool:
        """Проверка доступа к фото (через доступ к отметке)"""
        if self.is_admin:
            return True
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
        if self.is_admin:
            return True
        result = await self.db.execute(
            select(Project).where(
                and_(Project.id == project_id, Project.owner_id == user_id)
            )
        )
        return result.scalar_one_or_none() is not None

    async def can_manage_project(self, project_id: int, user_id: int) -> bool:
        """Право управления проектом и его содержимым (владелец, та же группа или admin).

        Групповое правило не применяется к пользователям с role_type=all.
        """
        if await self.is_project_owner(project_id, user_id):  # покрывает admin и владельца
            return True
        return await self._check_group_access(project_id, user_id)

    async def can_manage_object(self, object_id: int, user_id: int) -> bool:
        """Право управления объектом (через право управления его проектом)"""
        if self.is_admin:
            return True
        result = await self.db.execute(
            select(Object.project_id).where(Object.id == object_id)
        )
        project_id = result.scalar_one_or_none()
        if project_id is None:
            return False
        return await self.can_manage_project(project_id, user_id)

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
