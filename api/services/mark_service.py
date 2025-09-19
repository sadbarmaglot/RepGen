from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Optional
from api.models.entities import Mark
from api.models.entities import Plan
from api.models.entities import Object
from api.models.entities import Project
from api.models.requests import MarkCreateRequest, MarkUpdateRequest
from api.models.responses import MarkResponse, MarkListResponse
from api.services.access_control_service import AccessControlService

class MarkService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.access_control = AccessControlService(db)

    async def create_mark(self, user_id: int, mark_data: MarkCreateRequest) -> MarkResponse:
        """Создание новой отметки"""
        
        # Проверяем доступ к плану
        if not await self.access_control.check_plan_access(mark_data.plan_id, user_id):
            raise ValueError("План не найден или у вас нет прав доступа к нему")
        
        # Проверяем что план существует
        result = await self.db.execute(
            select(Plan).where(Plan.id == mark_data.plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise ValueError("План не найден")
        
        mark = Mark(
            plan_id=mark_data.plan_id,
            name=mark_data.name,
            description=mark_data.description,
            type=mark_data.type
        )
        
        try:
            self.db.add(mark)
            await self.db.commit()
            await self.db.refresh(mark)
            return self._mark_to_response(mark)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при создании отметки: {str(e)}")

    async def get_mark(self, mark_id: int, user_id: int) -> Optional[MarkResponse]:
        """Получение отметки по ID (для владельца проекта или участника объекта)"""
        # Проверяем доступ к отметке
        if not await self.access_control.check_mark_access(mark_id, user_id):
            return None
        
        result = await self.db.execute(
            select(Mark).where(Mark.id == mark_id)
        )
        mark = result.scalar_one_or_none()
        
        if not mark:
            return None
        
        return self._mark_to_response(mark)

    async def get_plan_marks(self, plan_id: int, user_id: int, skip: int = 0, limit: int = 100) -> MarkListResponse:
        """Получение списка отметок плана"""
        
        # Проверяем доступ к плану
        if not await self.access_control.check_plan_access(plan_id, user_id):
            raise ValueError("План не найден или у вас нет прав доступа к нему")
        
        # Получаем общее количество отметок
        count_result = await self.db.execute(
            select(Mark).where(Mark.plan_id == plan_id)
        )
        total = len(count_result.scalars().all())
        
        # Получаем отметки с пагинацией
        result = await self.db.execute(
            select(Mark)
            .where(Mark.plan_id == plan_id)
            .offset(skip)
            .limit(limit)
        )
        marks = result.scalars().all()
        
        mark_responses = []
        for mark in marks:
            mark_responses.append(self._mark_to_response(mark))
        
        return MarkListResponse(
            marks=mark_responses,
            total=total
        )

    async def update_mark(self, mark_id: int, user_id: int, mark_data: MarkUpdateRequest) -> Optional[MarkResponse]:
        """Обновление отметки (владельцем проекта или участником объекта)"""
        # Проверяем доступ к отметке
        if not await self.access_control.check_mark_access(mark_id, user_id):
            return None
        
        # Получаем отметку
        result = await self.db.execute(
            select(Mark).where(Mark.id == mark_id)
        )
        mark = result.scalar_one_or_none()
        
        if not mark:
            return None
        
        if mark_data.name is not None:
            mark.name = mark_data.name
        if mark_data.description is not None:
            mark.description = mark_data.description
        if mark_data.type is not None:
            mark.type = mark_data.type
        
        try:
            await self.db.commit()
            await self.db.refresh(mark)
            return self._mark_to_response(mark)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при обновлении отметки: {str(e)}")

    async def delete_mark(self, mark_id: int, user_id: int) -> bool:
        """Удаление отметки (владельцем проекта или участником объекта)"""
        # Проверяем доступ к отметке
        if not await self.access_control.check_mark_access(mark_id, user_id):
            return False
        
        # Получаем отметку
        result = await self.db.execute(
            select(Mark).where(Mark.id == mark_id)
        )
        mark = result.scalar_one_or_none()
        
        if not mark:
            return False
        
        try:
            await self.db.delete(mark)
            await self.db.commit()
            return True
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при удалении отметки: {str(e)}")

    def _mark_to_response(self, mark: Mark) -> MarkResponse:
        """Преобразование модели Mark в MarkResponse"""
        return MarkResponse(
            id=mark.id,
            plan_id=mark.plan_id,
            name=mark.name,
            description=mark.description,
            type=mark.type,
            created_at=mark.created_at
        )
