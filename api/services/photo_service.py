import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from typing import Optional

from api.models.entities import Mark, Photo
from api.models.database.enums import MarkType
from api.models.requests import PhotoCreateRequest, PhotoUpdateRequest
from api.models.responses import PhotoResponse, PhotoListResponse
from common.gc_utils import create_signed_url, delete_blob_by_name
from common.logging_utils import get_user_logger
from api.services.redis_service import redis_service
from api.services.access_control_service import AccessControlService
from api.services.construction_queue_service import get_construction_queue_service

logger = get_user_logger(__name__)

class PhotoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.access_control = AccessControlService(db)

    async def create_photo(self, user_id: int, photo_data: PhotoCreateRequest) -> PhotoResponse:
        """Создание новой фотографии"""
        
        # Проверяем доступ к отметке
        if not await self.access_control.check_mark_access(photo_data.mark_id, user_id):
            raise ValueError("Отметка не найдена или у вас нет прав доступа к ней")
        
        # Проверяем что отметка существует
        result = await self.db.execute(
            select(Mark).where(Mark.id == photo_data.mark_id)
        )
        mark = result.scalar_one_or_none()
        
        if not mark:
            raise ValueError("Отметка не найдена")
        
        # Определяем порядковый номер: если не указан, вычисляем максимальный + 1
        if photo_data.order is not None:
            order = photo_data.order
        else:
            max_order_result = await self.db.execute(
                select(func.max(Photo.order)).where(
                    Photo.mark_id == photo_data.mark_id,
                    Photo.order.isnot(None)
                )
            )
            max_order = max_order_result.scalar_one_or_none()
            
            if max_order is not None:
                order = max_order + 1
            else:
                count_result = await self.db.execute(
                    select(func.count(Photo.id)).where(Photo.mark_id == photo_data.mark_id)
                )
                photo_count = count_result.scalar() or 0
                order = photo_count
        
        photo = Photo(
            mark_id=photo_data.mark_id,
            image_name=photo_data.image_name,
            type=photo_data.type,
            description=photo_data.description,
            order=order
        )
        
        try:
            self.db.add(photo)
            await self.db.commit()
            await self.db.refresh(photo)
            
            # Запускаем фоновую задачу для определения типа конструкции
            # Только для отметок типа "дефект" и если тип конструкции не был указан явно
            if mark.type == MarkType.defect and not photo_data.type and photo.image_name:
                queue_service = get_construction_queue_service()
                queued = await queue_service.queue_analysis(photo.id, photo.image_name)
                if not queued:
                    logger.warning(
                        f"Не удалось добавить задачу определения конструкции для фото {photo.id} "
                        f"в очередь (очередь переполнена). Статистика: {queue_service.get_queue_stats()}"
                    )
            
            return await self._photo_to_response(photo)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при создании фотографии: {str(e)}")

    async def get_photo(self, photo_id: int, user_id: int) -> Optional[PhotoResponse]:
        """Получение фотографии по ID (для владельца проекта или участника объекта)"""
        # Проверяем доступ к фото
        if not await self.access_control.check_photo_access(photo_id, user_id):
            return None
        
        result = await self.db.execute(
            select(Photo).where(Photo.id == photo_id)
        )
        photo = result.scalar_one_or_none()
        
        if not photo:
            return None
        
        return await self._photo_to_response(photo)

    async def get_mark_photos(self, mark_id: int, user_id: int, skip: int = 0, limit: int = 100) -> PhotoListResponse:
        """Получение списка фотографий отметки"""
        
        # Проверяем доступ к отметке
        if not await self.access_control.check_mark_access(mark_id, user_id):
            raise ValueError("Отметка не найдена или у вас нет прав доступа к ней")
        
        # Получаем общее количество фотографий
        count_result = await self.db.execute(
            select(Photo).where(Photo.mark_id == mark_id)
        )
        total = len(count_result.scalars().all())
        
        # Получаем фотографии с пагинацией, сортируем по order (NULL значения в конце)
        result = await self.db.execute(
            select(Photo)
            .where(Photo.mark_id == mark_id)
            .order_by(Photo.order.asc().nullslast(), Photo.id.asc())
            .offset(skip)
            .limit(limit)
        )
        photos = result.scalars().all()
        
        photo_responses = []
        for photo in photos:
            photo_responses.append(await self._photo_to_response(photo))
        
        return PhotoListResponse(
            photos=photo_responses,
            total=total
        )

    async def update_photo(self, photo_id: int, user_id: int, photo_data: PhotoUpdateRequest) -> Optional[PhotoResponse]:
        """Обновление фотографии (владельцем проекта или участником объекта)"""
        # Проверяем доступ к фото
        if not await self.access_control.check_photo_access(photo_id, user_id):
            return None
        
        # Получаем фото
        result = await self.db.execute(
            select(Photo).where(Photo.id == photo_id)
        )
        photo = result.scalar_one_or_none()
        
        if not photo:
            return None
        
        if photo_data.type is not None:
            photo.type = photo_data.type
            # Если пользователь сам указал тип, но не указал confidence, устанавливаем 1.0
            if photo_data.type_confidence is None:
                photo.type_confidence = 1.0
        if photo_data.type_confidence is not None:
            photo.type_confidence = photo_data.type_confidence
        if photo_data.description is not None:
            photo.description = photo_data.description
        if photo_data.order is not None:
            photo.order = photo_data.order
        
        try:
            await self.db.commit()
            await self.db.refresh(photo)
            return await self._photo_to_response(photo)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при обновлении фотографии: {str(e)}")

    async def delete_photo(self, photo_id: int, user_id: int) -> bool:
        """Удаление фотографии (владельцем проекта или участником объекта)"""
        # Проверяем доступ к фото
        if not await self.access_control.check_photo_access(photo_id, user_id):
            return False
        
        # Получаем фото
        result = await self.db.execute(
            select(Photo).where(Photo.id == photo_id)
        )
        photo = result.scalar_one_or_none()
        
        if not photo:
            return False
        
        try:
            await self.db.delete(photo)
            await self.db.commit()
            
            # Удаляем изображение из blob storage и очищаем кэш
            if photo.image_name:
                await delete_blob_by_name(photo.image_name)
                await redis_service.clear_signed_url(photo.image_name)
            
            return True
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при удалении фотографии: {str(e)}")

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
                    await redis_service.cache_signed_url(photo.image_name, image_url, ttl_seconds=3000)
            except Exception:
                # Тихо обрабатываем ошибку (файл не существует или Redis недоступен)
                image_url = None
        
        return PhotoResponse(
            id=photo.id,
            mark_id=photo.mark_id,
            image_name=photo.image_name,
            image_url=image_url,
            type=photo.type,
            description=photo.description,
            order=photo.order,
            type_confidence=float(photo.type_confidence) if photo.type_confidence is not None else None,
            created_at=photo.created_at
        )
