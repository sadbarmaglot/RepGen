import logging

from fastapi import APIRouter, HTTPException, Depends

from api.models.entities import User
from api.dependencies.auth_dependencies import get_current_user
from api.models.requests import ConstructionTypeRequest
from api.models.responses import ConstructionTypeResponse
from api.services.construction_analyzer import ConstructionAnalyzer
from api.services.model_manager import ModelManager
from api.services.redis_service import redis_service
from common.gc_utils import create_signed_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/construction", tags=["construction"])

model_manager = ModelManager()
construction_analyzer = ConstructionAnalyzer(model_manager)

@router.post("/analyze_type", response_model=ConstructionTypeResponse)
async def analyze_construction_type(
    request: ConstructionTypeRequest,
    _: User = Depends(get_current_user)
):
    """
    Определение типа конструкции по имени изображения
    
    Требует аутентификации. Принимает имя изображения в GCS bucket и возвращает определенный тип конструкции
    """
    try:
        logger.info(f"Получен запрос на определение типа конструкции для изображения: {request.image_name}")
        
        cached_url = await redis_service.get_signed_url(request.image_name)
        
        if cached_url:
            logger.info(f"Использование кэшированного signed URL для {request.image_name}")
            image_url = cached_url
        else:
            logger.info(f"Создание нового signed URL для {request.image_name}")
            image_url = await create_signed_url(request.image_name, expiration_minutes=60)
            await redis_service.cache_signed_url(request.image_name, image_url, ttl_seconds=3600)
        
        result = await construction_analyzer.analyze_construction_type(
            image_url=image_url,
            image_name=request.image_name
        )
        
        return ConstructionTypeResponse(result=result)
        
    except Exception as e:
        logger.error(f"Ошибка при определении типа конструкции: {str(e)}")
        await redis_service.clear_signed_url(request.image_name)
        raise HTTPException(status_code=500, detail=str(e))
