from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Optional

from common.gc_utils import create_signed_url, delete_blob_by_name
from api.models.entities import Plan
from api.models.entities import Object
from api.models.requests import PlanCreateRequest, PlanUpdateRequest
from api.models.responses import PlanResponse, PlanListResponse
from api.services.redis_service import redis_service
from api.services.access_control_service import AccessControlService

class PlanService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.access_control = AccessControlService(db)

    async def create_plan(self, user_id: int, plan_data: PlanCreateRequest) -> PlanResponse:
        """Создание нового плана"""
        
        # Проверяем доступ к объекту
        if not await self.access_control.check_object_access(plan_data.object_id, user_id):
            raise ValueError("Объект не найден или у вас нет прав доступа к нему")
        
        # Проверяем что объект существует
        result = await self.db.execute(
            select(Object).where(Object.id == plan_data.object_id)
        )
        object_ = result.scalar_one_or_none()
        
        if not object_:
            raise ValueError("Объект не найден")
        
        plan = Plan(
            object_id=plan_data.object_id,
            name=plan_data.name,
            description=plan_data.description,
            image_name=plan_data.image_name
        )
        
        try:
            self.db.add(plan)
            await self.db.commit()
            await self.db.refresh(plan)
            return await self._plan_to_response(plan)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при создании плана: {str(e)}")

    async def get_plan(self, plan_id: int, user_id: int) -> Optional[PlanResponse]:
        """Получение плана по ID (для владельца проекта или участника объекта)"""
        # Проверяем доступ к плану
        if not await self.access_control.check_plan_access(plan_id, user_id):
            return None
        
        result = await self.db.execute(
            select(Plan).where(Plan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            return None
        
        return await self._plan_to_response(plan)

    async def get_object_plans(self, object_id: int, user_id: int, skip: int = 0, limit: int = 100) -> PlanListResponse:
        """Получение списка планов объекта"""
        
        # Проверяем доступ к объекту
        if not await self.access_control.check_object_access(object_id, user_id):
            raise ValueError("Объект не найден или у вас нет прав доступа к нему")
        
        count_result = await self.db.execute(
            select(Plan).where(Plan.object_id == object_id)
        )
        total = len(count_result.scalars().all())
        
        result = await self.db.execute(
            select(Plan)
            .where(Plan.object_id == object_id)
            .offset(skip)
            .limit(limit)
        )
        plans = result.scalars().all()
        
        plan_responses = []
        for plan in plans:
            plan_responses.append(await self._plan_to_response(plan))
        
        return PlanListResponse(
            plans=plan_responses,
            total=total
        )

    async def update_plan(self, plan_id: int, user_id: int, plan_data: PlanUpdateRequest) -> Optional[PlanResponse]:
        """Обновление плана (владельцем проекта или участником объекта)"""
        # Проверяем доступ к плану
        if not await self.access_control.check_plan_access(plan_id, user_id):
            return None
        
        # Получаем план
        result = await self.db.execute(
            select(Plan).where(Plan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            return None
        
        if plan_data.name is not None:
            plan.name = plan_data.name
        if plan_data.description is not None:
            plan.description = plan_data.description
        
        try:
            await self.db.commit()
            await self.db.refresh(plan)
            return await self._plan_to_response(plan)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при обновлении плана: {str(e)}")

    async def delete_plan(self, plan_id: int, user_id: int) -> bool:
        """Удаление плана (владельцем проекта или участником объекта)"""
        # Проверяем доступ к плану
        if not await self.access_control.check_plan_access(plan_id, user_id):
            return False
        
        # Получаем план
        result = await self.db.execute(
            select(Plan).where(Plan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            return False
        
        try:
            await self.db.delete(plan)
            await self.db.commit()
            
            # Удаляем изображение из blob storage и очищаем кэш
            if plan.image_name:
                await delete_blob_by_name(plan.image_name)
                await redis_service.clear_signed_url(plan.image_name)
            
            return True
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при удалении плана: {str(e)}")

    async def _plan_to_response(self, plan: Plan) -> PlanResponse:
        """Преобразование модели Plan в PlanResponse с подписным URL"""
        image_url = None
        if plan.image_name:
            try:
                cached_url = await redis_service.get_signed_url(plan.image_name)
                if cached_url:
                    image_url = cached_url
                else:
                    image_url = await create_signed_url(plan.image_name, expiration_minutes=60)
                    await redis_service.cache_signed_url(plan.image_name, image_url, ttl_seconds=3600)
            except Exception as e:
                print(f"Ошибка создания подписного URL для {plan.image_name}: {e}")
                image_url = None
        
        return PlanResponse(
            id=plan.id,
            object_id=plan.object_id,
            name=plan.name,
            description=plan.description,
            image_url=image_url,
            created_at=plan.created_at
        )
