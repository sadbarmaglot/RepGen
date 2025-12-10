import asyncio
import logging

from api.services.model_manager import ModelManager
from api.models.config import DefectResult, AnalysisConfig, ImageInfo
from common.gc_utils import create_signed_url
from typing import List, Optional

logger = logging.getLogger(__name__)

class DefectAnalyzer:
    """Сервис анализа дефектов строительных конструкций"""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
    async def analyze_images(
        self, 
        image_infos: List[ImageInfo], 
        config: Optional[AnalysisConfig] = None
    ) -> List[DefectResult]:
        """
        Анализ списка изображений
        
        Args:
            image_urls: Список URL изображений
            config: Конфигурация анализа
            
        Returns:
            Список результатов анализа
        """
        if config is None:
            config = AnalysisConfig()
        
        logger.info(f"Начинаю анализ {len(image_infos)} изображений")
        
        tasks = []
        for image_info in image_infos:
            task = self._analyze_single_image(image_info, config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Ошибка при анализе изображения {image_infos[i].url}: {result}")
                processed_results.append(DefectResult(
                    image_url=str(image_infos[i].url),
                    description="Ошибка анализа",
                    recommendation="Требуется повторный анализ",
                    model_used="error"
                ))
            else:
                processed_results.append(result)
        
        logger.info(f"Анализ завершен. Обработано: {len(processed_results)} изображений")
        return processed_results
    
    async def _analyze_single_image(
        self, 
        image_info: ImageInfo,
        config: AnalysisConfig
    ) -> DefectResult:
        """
        Анализ одного изображения
        
        Args:
            image_url: URL изображения
            config: Конфигурация анализа
            
        Returns:
            Результат анализа
        """
        try:            
            analysis_result = await self.model_manager.analyze_image(
                image_url=image_info.url,
                mime_type=image_info.mime_type,
                config={
                    "model_name": config.model_name,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens
                }
            )
            
            model_used = config.model_name or "default"
            
            return DefectResult(
                image_url=image_info.url,
                description=analysis_result.get("description", "Дефект не определен"),
                recommendation=analysis_result.get("recommendation", "Рекомендация не предоставлена"),
                model_used=model_used
            )
            
        except Exception as e:
            logger.error(f"Ошибка при анализе изображения {image_info.url}: {e}")
            
            return DefectResult(
                image_url=image_info.url,
                description="Ошибка анализа",
                recommendation="Требуется повторный анализ",
                model_used="error"
            )
    
    async def analyze_single_image_by_name(
        self, 
        image_name: str,
        construction_type: str = None
    ) -> dict:
        """
        Анализ одного изображения по имени файла
        
        Args:
            image_name: Имя файла изображения в GCP bucket
            construction_type: Тип конструкции для фильтрации базы дефектов
            
        Returns:
            Словарь с результатом анализа (description, recommendation)
        """
        try:
            # Создаем подписной URL для изображения
            signed_url = await create_signed_url(image_name, expiration_minutes=60)
            
            # Определяем MIME тип по расширению файла
            if image_name.lower().endswith('.png'):
                mime_type = "image/png"
            elif image_name.lower().endswith('.jpg') or image_name.lower().endswith('.jpeg'):
                mime_type = "image/jpeg"
            elif image_name.lower().endswith('.gif'):
                mime_type = "image/gif"
            elif image_name.lower().endswith('.webp'):
                mime_type = "image/webp"
            else:
                mime_type = "image/jpeg"  # по умолчанию
            
            # Конфигурация для gpt-5.1 с дефолтными параметрами
            config = {
                "model_name": "gpt-5.1",
                "temperature": 0.2,
                "max_tokens": 1024
            }
            
            logger.info(f"Начинаю анализ изображения {image_name} с моделью gpt-5.1")
            if construction_type is not None:
                logger.info(f"Используется фильтрация по типу конструкции: {construction_type}")
            
            # Анализируем изображение
            analysis_result = await self.model_manager.analyze_image(
                image_url=signed_url,
                mime_type=mime_type,
                config=config,
                construction_type=construction_type
            )
            
            # Возвращаем description, recommendation и category
            return {
                "description": analysis_result.get("description", "Дефект не определен"),
                "recommendation": analysis_result.get("recommendation", "Рекомендация не предоставлена"),
                "category": analysis_result.get("category", "Не определена")
            }
            
        except Exception as e:
            logger.error(f"Ошибка при анализе изображения {image_name}: {e}")
            
            return {
                "description": "Ошибка анализа",
                "recommendation": "Требуется повторный анализ",
                "category": "Не определена"
            }