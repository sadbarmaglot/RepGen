import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.wear_service import WearService
from api.services.database import get_db
from api.models.entities import User
from api.dependencies.auth_dependencies import get_current_user
from api.models.requests import WearBulkUpdateRequest, WearItemPatchRequest
from api.models.responses import WearCalculationResponse, WearElementListResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wear", tags=["wear"])


@router.get("/elements", response_model=WearElementListResponse)
async def get_wear_elements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение справочника элементов износа

    Возвращает список всех элементов для таблицы расчёта износа
    с их кодами, названиями и дефолтными весами.
    """
    try:
        service = WearService(db)
        return await service.get_elements()
    except Exception as e:
        logger.error(f"Ошибка при получении справочника элементов: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/objects/{object_id}", response_model=WearCalculationResponse)
async def get_object_wear(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение расчёта износа для объекта

    Возвращает все элементы с их значениями и расчётами:
    - assessment_percent: введённый пользователем процент износа
    - weighted_average: (assessment_percent / 100) * effective_weight
    - technical_condition: категория состояния (cat_1..cat_4)
    - total_wear: сумма всех weighted_average
    - overall_condition: итоговая категория объекта
    """
    try:
        service = WearService(db)
        return await service.get_object_wear(object_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при получении износа объекта {object_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/objects/{object_id}", response_model=WearCalculationResponse)
async def update_object_wear(
    object_id: int,
    request: WearBulkUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Массовое обновление данных износа объекта

    Принимает массив элементов с их значениями assessment_percent.
    Возвращает полный расчёт износа с обновлёнными данными.
    """
    try:
        service = WearService(db)
        items_data = [item.model_dump() for item in request.items]
        return await service.update_object_wear(object_id, current_user.id, items_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при обновлении износа объекта {object_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/objects/{object_id}/items/{element_id}", response_model=WearCalculationResponse)
async def update_single_wear_item(
    object_id: int,
    element_id: int,
    request: WearItemPatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление одного элемента износа

    Используется для быстрого обновления при вводе в ячейку таблицы.
    Возвращает полный расчёт износа (чтобы обновить total_wear на фронте).
    """
    try:
        service = WearService(db)
        return await service.update_single_item(
            object_id=object_id,
            element_id=element_id,
            user_id=current_user.id,
            assessment_percent=request.assessment_percent
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при обновлении элемента {element_id} объекта {object_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
