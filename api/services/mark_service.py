from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from typing import Optional
import asyncio
from api.models.entities import Mark, Plan, Photo
from api.models.requests import MarkCreateRequest, MarkUpdateRequest
from api.models.responses import (
    MarkResponse, 
    MarkListResponse, 
    MarkWithPhotosResponse, 
    MarkWithPhotosListResponse,
    PhotoResponse
)
from api.services.access_control_service import AccessControlService
from common.gc_utils import create_signed_url
from api.services.redis_service import redis_service

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
            type=mark_data.type,
            x=mark_data.x,
            y=mark_data.y
        )
        
        try:
            self.db.add(mark)
            await self.db.commit()
            await self.db.refresh(mark)
            return self._mark_to_response(mark, photo_count=0)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при создании отметки: {str(e)}")

    async def get_mark(self, mark_id: int, user_id: int) -> Optional[MarkResponse]:
        """Получение отметки по ID (для владельца проекта или участника объекта)"""
        # Проверяем доступ к отметке
        if not await self.access_control.check_mark_access(mark_id, user_id):
            return None
        
        # Получаем метку с подсчетом фотографий
        result = await self.db.execute(
            select(
                Mark,
                func.count(Photo.id).label('photo_count')
            )
            .outerjoin(Photo, Photo.mark_id == Mark.id)
            .where(Mark.id == mark_id)
            .group_by(Mark.id)
        )
        
        row = result.first()
        
        if not row:
            return None
        
        mark, photo_count = row
        return self._mark_to_response(mark, photo_count)

    async def get_plan_marks(self, plan_id: int, user_id: int, skip: int = 0, limit: int = 500) -> MarkListResponse:
        """Получение списка отметок плана с количеством фотографий для каждой метки"""
        
        # Проверяем доступ к плану
        if not await self.access_control.check_plan_access(plan_id, user_id):
            raise ValueError("План не найден или у вас нет прав доступа к нему")
        
        # Получаем общее количество отметок
        count_result = await self.db.execute(
            select(Mark).where(Mark.plan_id == plan_id)
        )
        total = len(count_result.scalars().all())
        
        # Получаем отметки с пагинацией и подсчетом фотографий
        result = await self.db.execute(
            select(
                Mark,
                func.count(Photo.id).label('photo_count')
            )
            .outerjoin(Photo, Photo.mark_id == Mark.id)
            .where(Mark.plan_id == plan_id)
            .group_by(Mark.id)
            .order_by(Mark.id)
            .offset(skip)
            .limit(limit)
        )
        
        marks_with_counts = result.all()
        
        mark_responses = []
        for mark, photo_count in marks_with_counts:
            mark_responses.append(self._mark_to_response(mark, photo_count))
        
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
        if mark_data.x is not None:
            mark.x = mark_data.x
        if mark_data.y is not None:
            mark.y = mark_data.y
        
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

    async def get_plan_marks_with_photos(self, plan_id: int, user_id: int, skip: int = 0, limit: int = 500) -> MarkWithPhotosListResponse:
        """Получение списка отметок плана со всеми фотографиями для каждой метки (оптимизировано)"""
        
        # Проверяем доступ к плану
        if not await self.access_control.check_plan_access(plan_id, user_id):
            raise ValueError("План не найден или у вас нет прав доступа к нему")
        
        # Получаем общее количество отметок
        count_result = await self.db.execute(
            select(func.count(Mark.id)).where(Mark.plan_id == plan_id)
        )
        total = count_result.scalar() or 0
        
        # Получаем отметки с фотографиями за один запрос используя eager loading
        result = await self.db.execute(
            select(Mark)
            .options(selectinload(Mark.photos))
            .where(Mark.plan_id == plan_id)
            .order_by(Mark.id)
            .offset(skip)
            .limit(limit)
        )
        
        marks = result.scalars().all()
        
        # Собираем все фотографии для параллельной генерации signed URLs
        all_photos = []
        mark_photo_mapping = {}  # {mark_id: [photos]}
        
        for mark in marks:
            mark_photo_mapping[mark.id] = list(mark.photos)
            all_photos.extend(mark.photos)
        
        # Генерируем signed URLs для всех фотографий параллельно
        photo_tasks = [self._photo_to_response(photo) for photo in all_photos]
        all_photo_responses = await asyncio.gather(*photo_tasks)
        
        # Создаем индекс для быстрого доступа к photo responses
        photo_response_map = {photo.id: response for photo, response in zip(all_photos, all_photo_responses)}
        
        # Преобразуем метки с фотографиями
        mark_responses = []
        for mark in marks:
            # Получаем photo responses для этой метки
            photo_responses = [
                photo_response_map[photo.id] 
                for photo in mark_photo_mapping[mark.id]
            ]
            
            # Создаем ответ с меткой и фотографиями
            mark_response = MarkWithPhotosResponse(
                id=mark.id,
                plan_id=mark.plan_id,
                name=mark.name,
                description=mark.description,
                type=mark.type,
                x=mark.x,
                y=mark.y,
                photos=photo_responses,
                created_at=mark.created_at
            )
            mark_responses.append(mark_response)
        
        return MarkWithPhotosListResponse(
            marks=mark_responses,
            total=total
        )

    async def _photo_to_response(self, photo: Photo) -> PhotoResponse:
        """Преобразование модели Photo в PhotoResponse с подписным URL"""
        image_url = None
        if photo.image_name:
            try:
                # Сначала проверяем кэш Redis
                cached_url = await redis_service.get_signed_url(photo.image_name)
                if cached_url:
                    image_url = cached_url
                else:
                    # Если нет в кэше, создаем новый подписанный URL
                    image_url = await create_signed_url(photo.image_name, expiration_minutes=60)
                    # Сохраняем в кэш с TTL = 60 минут (3600 секунд)
                    await redis_service.cache_signed_url(photo.image_name, image_url, ttl_seconds=3600)
            except Exception as e:
                # Логируем ошибку, но не прерываем выполнение
                print(f"Ошибка создания подписного URL для {photo.image_name}: {e}")
                image_url = None
        
        return PhotoResponse(
            id=photo.id,
            mark_id=photo.mark_id,
            image_name=photo.image_name,
            image_url=image_url,
            type=photo.type,
            description=photo.description,
            created_at=photo.created_at
        )

    def _mark_to_response(self, mark: Mark, photo_count: Optional[int] = None) -> MarkResponse:
        """Преобразование модели Mark в MarkResponse"""
        return MarkResponse(
            id=mark.id,
            plan_id=mark.plan_id,
            name=mark.name,
            description=mark.description,
            type=mark.type,
            x=mark.x,
            y=mark.y,
            photo_count=photo_count,
            created_at=mark.created_at
        )
