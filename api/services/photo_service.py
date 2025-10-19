from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Optional
from api.models.entities import Photo
from api.models.entities import Mark
from api.models.requests import PhotoCreateRequest, PhotoUpdateRequest
from api.models.responses import PhotoResponse, PhotoListResponse
from common.gc_utils import create_signed_url, delete_blob_by_name
from api.services.redis_service import redis_service
from api.services.access_control_service import AccessControlService

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
        
        photo = Photo(
            mark_id=photo_data.mark_id,
            image_name=photo_data.image_name,
            type=photo_data.type,
            description=photo_data.description
        )
        
        try:
            self.db.add(photo)
            await self.db.commit()
            await self.db.refresh(photo)
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
        
        # Получаем фотографии с пагинацией
        result = await self.db.execute(
            select(Photo)
            .where(Photo.mark_id == mark_id)
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
        if photo_data.description is not None:
            photo.description = photo_data.description
        
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
                    # Сохраняем в кэш с TTL = 60 минут (3600 секунд)
                    await redis_service.cache_signed_url(photo.image_name, image_url, ttl_seconds=3600)
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
            created_at=photo.created_at
        )
