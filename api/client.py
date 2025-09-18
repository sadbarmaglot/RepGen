import io
import aiohttp
import logging

from PIL import Image
from typing import List, Dict, Any, Optional

from api.models.config import AnalysisConfig, ImageInfo

logger = logging.getLogger(__name__)

class DefectAnalysisClient:
    """Клиент для работы с API анализа дефектов"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Убеждаемся, что сессия создана"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def _make_analysis_request(
        self, 
        image_infos: List[ImageInfo], 
        config: Optional[AnalysisConfig] = None
        ) -> List[Dict[str, Any]]:
        """Приватный метод для выполнения HTTP запроса анализа"""

        request_dict = {
            "image_infos": image_infos,
            "config": {
                "model_name": config.model_name if config else None,
                "temperature": config.temperature if config else 0.2,
                "max_tokens": config.max_tokens if config else 1024
            } if config else None
        }
        
        async with self.session.post(
            f"{self.base_url}/analyze_images",
            json=request_dict
        ) as response:
            if response.status == 200:
                data = await response.json()
                results = []
                
                for result in data.get("results", []):
                    results.append({
                        "description": result.get("description", ""),
                        "recommendation": result.get("recommendation", ""),
                        "model_used": result.get("model_used", ""),
                        "status": "success"
                    })
                
                return results
            else:
                error_text = await response.text()
                raise Exception(f"Ошибка анализа: {response.status} - {error_text}")
    
    async def analyze_images(
        self, 
        image_infos: List[ImageInfo], 
        config: Optional[AnalysisConfig] = None
    ) -> List[Dict[str, Any]]:
        """Анализируем уже загруженные изображения по их URL (без повторной загрузки)"""
        await self._ensure_session()
        
        if not image_infos:
            return []
        
        return await self._make_analysis_request(image_infos, config)

    async def upload_images(
        self, 
        images: List[Image.Image], 
        create_signed_urls: bool = True,
        expiration_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Загружаем изображения в GCP через API /upload/images (batch загрузка)"""
        await self._ensure_session()
        
        if not images:
            return []
        
        if len(images) > 20:
            raise Exception("Максимальное количество изображений: 20")
                
        data = aiohttp.FormData()
        
        if create_signed_urls:
            data.add_field('create_signed_urls', 'true')
            data.add_field('expiration_minutes', str(expiration_minutes))
        
        for image in images:
            
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=85, optimize=True)
            image_data = buffer.getvalue()
            
            data.add_field('files', image_data, content_type='image/jpeg')
        
        async with self.session.post(f"{self.base_url}/upload/images", data=data) as response:
            if response.status == 200:
                results = await response.json()
                
                if not isinstance(results, list):
                    raise Exception("Неверный формат ответа от сервера")
                
                validated_results = []
                for result in results:
                    if isinstance(result, dict) and "public_url" in result:
                        validated_results.append(result)
                    else:
                        logger.warning(f"Пропущен неверный результат: {result}")
                
                if len(validated_results) != len(images):
                    logger.warning(f"Загружено {len(validated_results)} из {len(images)} изображений")
                
                return validated_results
            elif response.status == 400:
                error_text = await response.text()
                raise Exception(f"Ошибка валидации: {error_text}")
            elif response.status == 413:
                raise Exception("Файлы слишком большие или превышен лимит")
            elif response.status >= 500:
                error_text = await response.text()
                raise Exception(f"Ошибка сервера: {response.status} - {error_text}")
            else:
                error_text = await response.text()
                raise Exception(f"Ошибка batch загрузки: {response.status} - {error_text}")
    

