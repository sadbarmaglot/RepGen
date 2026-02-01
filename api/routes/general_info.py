import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.general_info_service import GeneralInfoService
from api.services.database import get_db
from api.models.entities import User
from api.dependencies.auth_dependencies import get_current_user
from api.models.requests import GeneralInfoUpdateRequest
from api.models.responses import GeneralInfoResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/general-info", tags=["general-info"])


@router.get("/objects/{object_id}", response_model=GeneralInfoResponse)
async def get_object_general_info(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение общей информации объекта

    Возвращает данные из раздела "Общая информация" заключения:
    даты, адресация, характеристики дома, статус и организация.
    """
    try:
        service = GeneralInfoService(db)
        return await service.get_by_object(object_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при получении общей информации объекта {object_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/objects/{object_id}", response_model=GeneralInfoResponse)
async def update_object_general_info(
    object_id: int,
    request: GeneralInfoUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление общей информации объекта

    Обновляет данные раздела "Общая информация" заключения.
    Создаёт запись если не существует.
    """
    try:
        service = GeneralInfoService(db)
        data = request.model_dump(exclude_unset=True)
        return await service.update(object_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при обновлении общей информации объекта {object_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
