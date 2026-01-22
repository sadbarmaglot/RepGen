import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.defect_analyzer import DefectAnalyzer
from api.services.model_manager import ModelManager
from api.services.construction_analyzer import ConstructionAnalyzer
from api.services.redis_service import redis_service
from api.services.defect_analysis_service import DefectAnalysisService
from api.services.database import get_db
from api.models.entities import User
from api.dependencies.auth_dependencies import get_current_user
from api.models.requests import ImageAnalysisRequest, ConstructionTypeRequest, DefectAnalysisUpdateRequest
from api.models.responses import (
    ImageAnalysisResponse,
    ConstructionTypeResponse,
    DefectDescriptionResponse,
    PhotoDefectAnalysisListResponse,
    PhotoDefectAnalysisResponse,
    CATEGORY_DISPLAY_MAP
)
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Анализ изображения по имени файла
    
    Принимает имя изображения и возвращает анализ дефекта с использованием gpt-4o.
    Можно указать тип конструкции для фильтрации базы дефектов.
    Если указан photo_id, результат будет сохранен в БД.
    """
    try:
        logger.info(f"Получен запрос на анализ изображения: {request.image_name}")
        if request.construction_type is not None:
            logger.info(f"Тип конструкции: {request.construction_type}")
        
        result = await defect_analyzer.analyze_single_image_by_name(
            image_name=request.image_name,
            construction_type=request.construction_type
        )
        
        # Если указан photo_id, сохраняем результат в БД
        if request.photo_id is not None:
            try:
                service = DefectAnalysisService(db)
                await service.create_analysis(
                    photo_id=request.photo_id,
                    defect_description=result["description"],
                    recommendation=result["recommendation"],
                    category=result["category"]
                )
                logger.info(f"Анализ сохранен в БД для фото {request.photo_id}")
            except ValueError as e:
                logger.warning(f"Не удалось сохранить анализ в БД: {e}")
                # Не прерываем выполнение - возвращаем результат анализа
        
        return ImageAnalysisResponse(
            description=result["description"],
            recommendation=result["recommendation"],
            category=result["category"]
        )
        
    except Exception as e:
        logger.error(f"Ошибка при анализе изображения {request.image_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/defect/{photo_id}", response_model=PhotoDefectAnalysisListResponse)
async def get_defect_analysis_by_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение анализов дефектов для конкретной фотографии
    """
    try:
        service = DefectAnalysisService(db)
        return await service.get_by_photo(photo_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при получении анализов для фото {photo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/defect/{photo_id}", response_model=PhotoDefectAnalysisResponse)
async def update_defect_analysis(
    photo_id: int,
    request: DefectAnalysisUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление анализа дефекта пользователем
    
    Позволяет пользователю ввести свою версию анализа дефекта.
    Если анализ для фото не существует, создается новый.
    """
    try:
        service = DefectAnalysisService(db)
        analysis = await service.update_analysis(
            photo_id=photo_id,
            user_id=current_user.id,
            defect_description=request.defect_description,
            recommendation=request.recommendation,
            category=request.category
        )
        
        # Маппим категорию для ответа
        category_value = analysis.category.value if hasattr(analysis.category, 'value') else str(analysis.category)
        display_category = CATEGORY_DISPLAY_MAP.get(category_value, category_value)
        
        return PhotoDefectAnalysisResponse(
            id=analysis.id,
            photo_id=analysis.photo_id,
            defect_description=analysis.defect_description,
            recommendation=analysis.recommendation,
            category=display_category,
            confidence=float(analysis.confidence) if analysis.confidence else None,
            created_at=analysis.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при обновлении анализа для фото {photo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/defect/by-mark/{mark_id}", response_model=PhotoDefectAnalysisListResponse)
async def get_defect_analysis_by_mark(
    mark_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение анализов дефектов для всех фотографий марки
    """
    try:
        service = DefectAnalysisService(db)
        return await service.get_by_mark(mark_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при получении анализов для марки {mark_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/defect/by-plan/{plan_id}", response_model=PhotoDefectAnalysisListResponse)
async def get_defect_analysis_by_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение анализов дефектов для всех фотографий плана
    """
    try:
        service = DefectAnalysisService(db)
        return await service.get_by_plan(plan_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при получении анализов для плана {plan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/defect/by-object/{object_id}", response_model=PhotoDefectAnalysisListResponse)
async def get_defect_analysis_by_object(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение анализов дефектов для всех фотографий объекта
    """
    try:
        service = DefectAnalysisService(db)
        return await service.get_by_object(object_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при получении анализов для объекта {object_id}: {str(e)}")
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
