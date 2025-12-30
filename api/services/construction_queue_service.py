import asyncio
import logging

from typing import Optional
from sqlalchemy import select

from api.models.entities import Photo
from api.services.construction_analyzer import ConstructionAnalyzer
from api.services.database import AsyncSessionLocal
from api.services.model_manager import ModelManager
from api.services.redis_service import redis_service
from common.gc_utils import create_signed_url
from settings import CONSTRUCTION_QUEUE_MAX_CONCURRENT, CONSTRUCTION_QUEUE_MAX_SIZE

logger = logging.getLogger(__name__)

class ConstructionQueueService:
    """Сервис для управления очередью запросов определения типа конструкции"""
    
    def __init__(self, max_concurrent: int = 3, max_queue_size: int = 100):
        """
        Args:
            max_concurrent: Максимальное количество параллельных запросов к OpenAI
            max_queue_size: Максимальный размер очереди ожидающих задач
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_queue_size = max_queue_size
        self.model_manager = ModelManager()
        self.construction_analyzer = ConstructionAnalyzer(self.model_manager)
        
        # Отслеживание активных задач
        self.active_tasks: set[asyncio.Task] = set()
        self.pending_count = 0
        self._lock = asyncio.Lock()
    
    async def queue_analysis(
        self,
        photo_id: int,
        image_name: str
    ) -> bool:
        """
        Добавить задачу анализа в очередь
        
        Args:
            photo_id: ID фотографии
            image_name: Имя файла изображения
            
        Returns:
            True если задача добавлена, False если очередь переполнена
        """
        async with self._lock:
            # Проверяем размер очереди
            if self.pending_count >= self.max_queue_size:
                logger.warning(
                    f"Очередь переполнена (pending: {self.pending_count}, max: {self.max_queue_size}). "
                    f"Задача для фото {photo_id} отклонена."
                )
                return False
            
            self.pending_count += 1
        
        # Создаем задачу
        task = asyncio.create_task(
            self._process_analysis(photo_id, image_name)
        )
        
        async with self._lock:
            self.active_tasks.add(task)
        
        # Удаляем задачу из отслеживания после завершения
        task.add_done_callback(lambda t: self._cleanup_task(t))
        
        return True
    
    def _cleanup_task(self, task: asyncio.Task) -> None:
        """Очистка завершенной задачи (вызывается из callback)"""
        async def _cleanup():
            async with self._lock:
                self.active_tasks.discard(task)
                if self.pending_count > 0:
                    self.pending_count -= 1
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_cleanup())
        except RuntimeError:
            logger.warning("Не удалось получить event loop для очистки задачи")
    
    async def _process_analysis(
        self,
        photo_id: int,
        image_name: str
    ) -> None:
        """
        Обработка анализа типа конструкции для фото
        
        Args:
            photo_id: ID фотографии
            image_name: Имя файла изображения
        """
        async with self.semaphore:
            max_retries = 3
            retry_delay = 2  # секунды
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Начало определения типа конструкции для фото {photo_id} (image_name: {image_name}, попытка {attempt + 1}/{max_retries})")
                    
                    # Получаем signed URL для изображения
                    cached_url = await redis_service.get_signed_url(image_name)
                    if cached_url:
                        image_url = cached_url
                    else:
                        image_url = await create_signed_url(image_name, expiration_minutes=60)
                        await redis_service.cache_signed_url(image_name, image_url, ttl_seconds=3000)
                    
                    # Определяем тип конструкции
                    result = await self.construction_analyzer.analyze_construction_type(
                        image_url=image_url,
                        image_name=image_name
                    )
                    
                    # Успешно получили результат, обновляем фото в БД
                    try:
                        async with AsyncSessionLocal() as db:
                            result_query = await db.execute(
                                select(Photo).where(Photo.id == photo_id)
                            )
                            photo = result_query.scalar_one_or_none()
                            
                            if photo:
                                photo.type = result.construction_type
                                photo.type_confidence = result.confidence
                                await db.commit()
                                logger.info(
                                    f"Тип конструкции '{result.construction_type}' "
                                    f"(confidence: {result.confidence}) установлен для фото {photo_id}"
                                )
                            else:
                                logger.warning(f"Фото {photo_id} не найдено в БД при попытке обновления типа конструкции")
                    except Exception as db_error:
                        logger.error(f"Ошибка при обновлении фото {photo_id} в БД: {db_error}", exc_info=True)
                    
                    # Успешно завершили, выходим из цикла retry
                    return
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    is_rate_limit = "rate limit" in error_msg or "превышен лимит" in error_msg
                    
                    if is_rate_limit and attempt < max_retries - 1:
                        # Экспоненциальная задержка при rate limit
                        delay = retry_delay * (2 ** attempt)
                        logger.warning(
                            f"Rate limit при определении типа конструкции для фото {photo_id}. "
                            f"Повтор через {delay}с (попытка {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Другие ошибки или последняя попытка
                        logger.error(
                            f"Ошибка при определении типа конструкции для фото {photo_id} "
                            f"(попытка {attempt + 1}/{max_retries}): {e}",
                            exc_info=True
                        )
                        if attempt == max_retries - 1:
                            # Последняя попытка неудачна, выходим
                            logger.error(f"Не удалось определить тип конструкции для фото {photo_id} после {max_retries} попыток")
                            return
    
    def get_queue_stats(self) -> dict:
        """
        Получить статистику очереди
        
        Returns:
            Словарь со статистикой: pending_count, active_tasks_count, max_queue_size, max_concurrent
        """
        return {
            "pending_count": self.pending_count,
            "active_tasks_count": len(self.active_tasks),
            "max_queue_size": self.max_queue_size,
            "max_concurrent": self.semaphore._value
        }

# Глобальный экземпляр сервиса
_construction_queue_service: Optional[ConstructionQueueService] = None

def get_construction_queue_service() -> ConstructionQueueService:
    """Получить глобальный экземпляр ConstructionQueueService"""
    global _construction_queue_service
    if _construction_queue_service is None:
        _construction_queue_service = ConstructionQueueService(
            max_concurrent=CONSTRUCTION_QUEUE_MAX_CONCURRENT,
            max_queue_size=CONSTRUCTION_QUEUE_MAX_SIZE
        )
    return _construction_queue_service

