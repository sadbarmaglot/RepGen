from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from api.models.entities import ObjectMember, Object, User, Project
from api.models.requests import ObjectMemberAssignRequest, ObjectMemberUnassignRequest
from api.models.responses import ObjectMemberResponse, ObjectMemberListResponse

class ObjectMemberService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _check_object_access(self, object_id: int, user_id: int) -> bool:
        """Проверка доступа к объекту (владелец проекта или участник объекта)"""
        # Проверяем является ли пользователь владельцем проекта
        owner_result = await self.db.execute(
            select(Object)
            .join(Project)
            .where(
                Object.id == object_id,
                Project.owner_id == user_id
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

    async def _check_project_owner(self, object_id: int, user_id: int) -> bool:
        """Проверка является ли пользователь владельцем проекта объекта"""
        result = await self.db.execute(
            select(Object)
            .join(Project)
            .where(
                Object.id == object_id,
                Project.owner_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def assign_user_to_object(
        self, 
        object_id: int, 
        request_user_id: int, 
        assign_data: ObjectMemberAssignRequest
    ) -> ObjectMemberResponse:
        """Назначение пользователя на объект (только владельцем проекта)"""
        
        # Проверяем, что запрашивающий пользователь является владельцем проекта
        if not await self._check_project_owner(object_id, request_user_id):
            raise ValueError("У вас нет прав для назначения пользователей на этот объект")
        
        # Проверяем, что назначаемый пользователь существует
        user_result = await self.db.execute(
            select(User).where(User.id == assign_data.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError("Пользователь не найден")
        
        # Проверяем, что объект существует
        object_result = await self.db.execute(
            select(Object).where(Object.id == object_id)
        )
        obj = object_result.scalar_one_or_none()
        if not obj:
            raise ValueError("Объект не найден")
        
        # Создаем связь
        object_member = ObjectMember(
            object_id=object_id,
            user_id=assign_data.user_id
        )
        
        try:
            self.db.add(object_member)
            await self.db.commit()
            await self.db.refresh(object_member)
            
            return ObjectMemberResponse(
                id=object_member.id,
                object_id=object_member.object_id,
                user_id=object_member.user_id,
                user_name=user.name or "",
                user_email=user.email
            )
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Пользователь уже назначен на этот объект")

    async def unassign_user_from_object(
        self, 
        object_id: int, 
        request_user_id: int, 
        unassign_data: ObjectMemberUnassignRequest
    ) -> bool:
        """Снятие пользователя с объекта (только владельцем проекта)"""
        
        # Проверяем, что запрашивающий пользователь является владельцем проекта
        if not await self._check_project_owner(object_id, request_user_id):
            raise ValueError("У вас нет прав для снятия пользователей с этого объекта")
        
        # Ищем связь
        result = await self.db.execute(
            select(ObjectMember).where(
                and_(
                    ObjectMember.object_id == object_id,
                    ObjectMember.user_id == unassign_data.user_id
                )
            )
        )
        object_member = result.scalar_one_or_none()
        
        if not object_member:
            raise ValueError("Пользователь не назначен на этот объект")
        
        try:
            await self.db.delete(object_member)
            await self.db.commit()
            return True
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при снятии пользователя с объекта: {str(e)}")

    async def get_object_members(
        self, 
        object_id: int, 
        request_user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> ObjectMemberListResponse:
        """Получение списка участников объекта"""
        
        # Проверяем доступ к объекту
        if not await self._check_object_access(object_id, request_user_id):
            raise ValueError("У вас нет доступа к этому объекту")
        
        # Получаем общее количество участников
        count_result = await self.db.execute(
            select(ObjectMember).where(ObjectMember.object_id == object_id)
        )
        total = len(count_result.scalars().all())
        
        # Получаем участников с информацией о пользователях
        result = await self.db.execute(
            select(ObjectMember)
            .options(selectinload(ObjectMember.user))
            .where(ObjectMember.object_id == object_id)
            .offset(skip)
            .limit(limit)
        )
        members = result.scalars().all()
        
        member_responses = []
        for member in members:
            member_responses.append(ObjectMemberResponse(
                id=member.id,
                object_id=member.object_id,
                user_id=member.user_id,
                user_name=member.user.name or "",
                user_email=member.user.email
            ))
        
        return ObjectMemberListResponse(
            members=member_responses,
            total=total
        )

    async def is_user_assigned_to_object(self, object_id: int, user_id: int) -> bool:
        """Проверка назначен ли пользователь на объект"""
        result = await self.db.execute(
            select(ObjectMember).where(
                and_(
                    ObjectMember.object_id == object_id,
                    ObjectMember.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none() is not None
