import logging
from typing import Dict, Any

from api.models.responses.construction_responses import ConstructionTypeResult, DefectDescriptionResult
from api.services.model_manager import ModelManager
from common.defects_db import SYSTEM_PROMPT, USER_PROMPT_CONSTRUCTIONS, USER_PROMPT_DEFECT_DESCRIPTION

logger = logging.getLogger(__name__)

class ConstructionAnalyzer:
    """Сервис для определения типа конструкции по изображению"""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.system_prompt = SYSTEM_PROMPT
        self.user_prompt = USER_PROMPT_CONSTRUCTIONS
    
    async def analyze_construction_type(
        self, 
        image_url: str,
        image_name: str,
    ) -> ConstructionTypeResult:
        """
        Определение типа конструкции по изображению
        
        Args:
            image_url: URL изображения
            image_name: Имя изображения
            
        Returns:
            Результат определения типа конструкции
        """
        try:
            gen_cfg = {
                "temperature": 0.2,
                "max_output_tokens": 4096,
                "model_name": "gpt-5.1",
            }
            result = await self._analyze_with_model(
                image_url=image_url,
                system_prompt=self.system_prompt,
                user_prompt=self.user_prompt,
                config=gen_cfg
            )
            
            return ConstructionTypeResult(
                image_name=image_name,
                construction_type=result.get("construction_type", "Не определен"),
                confidence=result.get("confidence", 0.0),
            )
            
        except Exception as e:
            logger.error(f"Ошибка при определении типа конструкции для {image_url}: {e}")
            raise
    
    async def analyze_defect_description(
        self, 
        image_url: str,
        image_name: str,
    ) -> DefectDescriptionResult:
        """
        Генерация описания дефектов по изображению
        
        Args:
            image_url: URL изображения
            image_name: Имя изображения
            
        Returns:
            Результат описания дефектов
        """
        try:
            gen_cfg = {
                "temperature": 0.2,
                "max_output_tokens": 4096,
                "model_name": "gpt-4o",
            }
            result = await self._analyze_with_model(
                image_url=image_url,
                system_prompt=self.system_prompt,
                user_prompt=USER_PROMPT_DEFECT_DESCRIPTION,
                config=gen_cfg
            )
            
            return DefectDescriptionResult(
                image_name=image_name,
                description=result.get("description", "Описание не получено"),
            )
            
        except Exception as e:
            logger.error(f"Ошибка при генерации описания дефектов для {image_url}: {e}")
            raise
    
    async def _analyze_with_model(
        self, 
        image_url: str,
        system_prompt: str,
        user_prompt: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Анализ с помощью модели
        
        Args:
            image_url: URL изображения
            system_prompt: Системный промпт
            user_prompt: Пользовательский промпт
            config: Конфигурация анализа
            
        Returns:
            Результат анализа
        """
        try:
            model_name = config.get("model_name")
            provider = self.model_manager.get_provider(model_name)
            
            result = await provider.analyze_image(
                image_url=image_url,
                mime_type="image/jpeg",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                config=config
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при анализе с моделью: {e}")
            raise
