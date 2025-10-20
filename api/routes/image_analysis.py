import logging

from fastapi import APIRouter, HTTPException, Depends

from api.services.defect_analyzer import DefectAnalyzer
from api.services.model_manager import ModelManager
from api.services.construction_analyzer import ConstructionAnalyzer
from api.services.redis_service import redis_service
from api.models.entities import User
from api.dependencies.auth_dependencies import get_current_user
from api.models.requests import ImageAnalysisRequest, ConstructionTypeRequest
from api.models.responses import ImageAnalysisResponse, ConstructionTypeResponse, DefectDescriptionResponse
from common.gc_utils import create_signed_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Инициализация сервисов
model_manager = ModelManager()
defect_analyzer = DefectAnalyzer(model_manager)
construction_analyzer = ConstructionAnalyzer(model_manager)

@router.post("/defect", response_model=ImageAnalysisResponse)
async def analyze_image(
    request: ImageAnalysisRequest,
    _: User = Depends(get_current_user)
):
    """
    Анализ изображения по имени файла
    
    Принимает имя изображения и возвращает анализ дефекта с использованием gpt-4o.
    Можно указать тип конструкции для фильтрации базы дефектов.
    """
    try:
        logger.info(f"Получен запрос на анализ изображения: {request.image_name}")
        if request.construction_type is not None:
            logger.info(f"Тип конструкции: {request.construction_type}")
        
        result = await defect_analyzer.analyze_single_image_by_name(
            image_name=request.image_name,
            construction_type=request.construction_type
        )
        
        return ImageAnalysisResponse(
            description=result["description"],
            recommendation=result["recommendation"],
            category=result["category"]
        )
        
    except Exception as e:
        logger.error(f"Ошибка при анализе изображения {request.image_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/construction_type", response_model=ConstructionTypeResponse)
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
            await redis_service.cache_signed_url(request.image_name, image_url, ttl_seconds=3000)
        
        result = await construction_analyzer.analyze_construction_type(
            image_url=image_url,
            image_name=request.image_name
        )
        
        return ConstructionTypeResponse(result=result)
        
    except Exception as e:
        logger.error(f"Ошибка при определении типа конструкции: {str(e)}")
        await redis_service.clear_signed_url(request.image_name)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/defect_description", response_model=DefectDescriptionResponse)
async def analyze_defect_description(
    request: ConstructionTypeRequest,
    _: User = Depends(get_current_user)
):
    """
    Генерация описания дефектов по имени изображения
    
    Требует аутентификации. Принимает имя изображения в GCS bucket и возвращает описание дефектов и повреждений
    """
    try:
        logger.info(f"Получен запрос на генерацию описания дефектов для изображения: {request.image_name}")
        
        cached_url = await redis_service.get_signed_url(request.image_name)
        
        if cached_url:
            logger.info(f"Использование кэшированного signed URL для {request.image_name}")
            image_url = cached_url
        else:
            logger.info(f"Создание нового signed URL для {request.image_name}")
            image_url = await create_signed_url(request.image_name, expiration_minutes=60)
            await redis_service.cache_signed_url(request.image_name, image_url, ttl_seconds=3000)
        
        result = await construction_analyzer.analyze_defect_description(
            image_url=image_url,
            image_name=request.image_name
        )
        
        return DefectDescriptionResponse(result=result)
        
    except Exception as e:
        logger.error(f"Ошибка при генерации описания дефектов: {str(e)}")
        await redis_service.clear_signed_url(request.image_name)
        raise HTTPException(status_code=500, detail=str(e))
