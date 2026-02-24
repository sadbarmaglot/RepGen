import asyncio
import logging

from typing import Optional

from api.services.defect_analyzer import DefectAnalyzer
from api.services.defect_analysis_service import DefectAnalysisService
from api.services.model_manager import ModelManager
from api.services.database import AsyncSessionLocal
from settings import DEFECT_QUEUE_MAX_CONCURRENT, DEFECT_QUEUE_MAX_SIZE

logger = logging.getLogger(__name__)


class DefectAnalysisQueueService:
    """Сервис для управления очередью групповых запросов анализа дефектов.

    Паттерн аналогичен ConstructionQueueService: fire-and-forget с семафором
    для ограничения параллельных AI-вызовов.
    """

    def __init__(self, max_concurrent: int = 3, max_queue_size: int = 200):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_queue_size = max_queue_size
        self.model_manager = ModelManager()
        self.defect_analyzer = DefectAnalyzer(self.model_manager)

        self.active_tasks: set[asyncio.Task] = set()
        self.pending_count = 0
        self._lock = asyncio.Lock()

    async def queue_group_analysis(
        self,
        image_name: str,
        construction_type: Optional[str],
        photo_ids: list[int],
        object_id: Optional[int]
    ) -> bool:
        """
        Поставить групповой анализ в очередь.

        AI анализирует одно репрезентативное изображение, результат
        сохраняется для всех photo_ids группы.

        Returns:
            True если задача поставлена в очередь, False если очередь переполнена
        """
        async with self._lock:
            if self.pending_count >= self.max_queue_size:
                logger.warning(
                    f"Очередь анализа дефектов переполнена "
                    f"(pending: {self.pending_count}, max: {self.max_queue_size}). "
                    f"Группа из {len(photo_ids)} фото отклонена."
                )
                return False

            self.pending_count += 1

        task = asyncio.create_task(
            self._process_group_analysis(image_name, construction_type, photo_ids, object_id)
        )

        async with self._lock:
            self.active_tasks.add(task)

        task.add_done_callback(lambda t: self._cleanup_task(t))

        return True

    def _cleanup_task(self, task: asyncio.Task) -> None:
        """Очистка завершенной задачи"""
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

    async def _process_group_analysis(
        self,
        image_name: str,
        construction_type: Optional[str],
        photo_ids: list[int],
        object_id: Optional[int]
    ) -> None:
        """
        Обработка группового анализа:
        1. AI анализ репрезентативного изображения
        2. Сохранение результата для всех photo_ids группы
        """
        async with self.semaphore:
            max_retries = 3
            retry_delay = 2

            for attempt in range(max_retries):
                try:
                    logger.info(
                        f"Начало группового анализа: image={image_name}, "
                        f"construction_type={construction_type}, "
                        f"photo_ids={photo_ids} (попытка {attempt + 1}/{max_retries})"
                    )

                    # 1. AI анализ репрезентативного фото
                    result = await self.defect_analyzer.analyze_single_image_by_name(
                        image_name=image_name,
                        construction_type=construction_type
                    )

                    description = result.get("description", "Дефект не определен")
                    recommendation = result.get("recommendation", "Рекомендация не предоставлена")
                    category = result.get("category", "Не определена")
                    defect_code = result.get("code", "")

                    logger.info(
                        f"AI анализ завершён для группы: code={defect_code}, "
                        f"category={category}, photo_count={len(photo_ids)}"
                    )

                    # 2. Сохранение результата для всех photo_ids
                    async with AsyncSessionLocal() as db:
                        service = DefectAnalysisService(db)

                        saved_count = 0
                        error_count = 0

                        for photo_id in photo_ids:
                            try:
                                await service.create_analysis(
                                    photo_id=photo_id,
                                    defect_description=description,
                                    recommendation=recommendation,
                                    category=category,
                                    defect_code=defect_code,
                                    object_id=object_id
                                )
                                saved_count += 1
                            except Exception as save_error:
                                error_count += 1
                                logger.error(
                                    f"Ошибка сохранения анализа для фото {photo_id}: {save_error}"
                                )

                        logger.info(
                            f"Групповой анализ завершён: "
                            f"saved={saved_count}, errors={error_count}, "
                            f"image={image_name}"
                        )

                    # Успех — выходим из retry-цикла
                    return

                except Exception as e:
                    error_msg = str(e).lower()
                    is_rate_limit = "rate limit" in error_msg or "превышен лимит" in error_msg

                    if is_rate_limit and attempt < max_retries - 1:
                        delay = retry_delay * (2 ** attempt)
                        logger.warning(
                            f"Rate limit при групповом анализе ({image_name}). "
                            f"Повтор через {delay}с (попытка {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(
                            f"Ошибка группового анализа ({image_name}, "
                            f"попытка {attempt + 1}/{max_retries}): {e}",
                            exc_info=True
                        )
                        if attempt == max_retries - 1:
                            logger.error(
                                f"Не удалось выполнить групповой анализ для {image_name} "
                                f"после {max_retries} попыток"
                            )
                            return

    def get_queue_stats(self) -> dict:
        """Статистика очереди"""
        return {
            "pending_count": self.pending_count,
            "active_tasks_count": len(self.active_tasks),
            "max_queue_size": self.max_queue_size,
            "max_concurrent": self.semaphore._value
        }


# Глобальный экземпляр сервиса
_defect_analysis_queue_service: Optional[DefectAnalysisQueueService] = None


def get_defect_analysis_queue_service() -> DefectAnalysisQueueService:
    """Получить глобальный экземпляр DefectAnalysisQueueService"""
    global _defect_analysis_queue_service
    if _defect_analysis_queue_service is None:
        _defect_analysis_queue_service = DefectAnalysisQueueService(
            max_concurrent=DEFECT_QUEUE_MAX_CONCURRENT,
            max_queue_size=DEFECT_QUEUE_MAX_SIZE
        )
    return _defect_analysis_queue_service
