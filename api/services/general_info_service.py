import logging
from typing import Optional
from decimal import Decimal
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.models.entities import ObjectGeneralInfo
from api.models.responses import GeneralInfoResponse
from api.services.access_control_service import AccessControlService

logger = logging.getLogger(__name__)


class GeneralInfoService:
    """Сервис для работы с общей информацией объекта"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.access_control = AccessControlService(db)

    async def get_by_object(self, object_id: int, user_id: int) -> GeneralInfoResponse:
        """Получение общей информации объекта"""
        # Проверяем доступ
        if not await self.access_control.check_object_access(object_id, user_id):
            raise ValueError("Объект не найден или нет доступа")

        result = await self.db.execute(
            select(ObjectGeneralInfo)
            .where(ObjectGeneralInfo.object_id == object_id)
        )
        info = result.scalar_one_or_none()

        if not info:
            # Возвращаем пустой ответ
            return GeneralInfoResponse(object_id=object_id)

        return self._to_response(info)

    async def update(
        self,
        object_id: int,
        user_id: int,
        data: dict
    ) -> GeneralInfoResponse:
        """Обновление общей информации объекта"""
        # Проверяем доступ
        if not await self.access_control.check_object_access(object_id, user_id):
            raise ValueError("Объект не найден или нет доступа")

        # Ищем существующую запись
        result = await self.db.execute(
            select(ObjectGeneralInfo)
            .where(ObjectGeneralInfo.object_id == object_id)
        )
        info = result.scalar_one_or_none()

        if info:
            # Обновляем существующую запись
            for field, value in data.items():
                if value is not None and hasattr(info, field):
                    if field in ('total_area', 'living_area'):
                        setattr(info, field, Decimal(str(value)) if value is not None else None)
                    elif field in ('latitude', 'longitude'):
                        setattr(info, field, Decimal(str(value)) if value is not None else None)
                    else:
                        setattr(info, field, value)
        else:
            # Создаём новую запись
            info = ObjectGeneralInfo(object_id=object_id)
            for field, value in data.items():
                if value is not None and hasattr(info, field):
                    if field in ('total_area', 'living_area'):
                        setattr(info, field, Decimal(str(value)) if value is not None else None)
                    elif field in ('latitude', 'longitude'):
                        setattr(info, field, Decimal(str(value)) if value is not None else None)
                    else:
                        setattr(info, field, value)
            self.db.add(info)

        await self.db.commit()
        await self.db.refresh(info)

        return self._to_response(info)

    def _to_response(self, info: ObjectGeneralInfo) -> GeneralInfoResponse:
        """Преобразование модели в ответ"""
        return GeneralInfoResponse(
            object_id=info.object_id,
            inspection_date=info.inspection_date,
            inspection_duration=info.inspection_duration,
            fias_code=info.fias_code,
            latitude=float(info.latitude) if info.latitude else None,
            longitude=float(info.longitude) if info.longitude else None,
            apartments_count=info.apartments_count,
            non_residential_count=info.non_residential_count,
            total_area=float(info.total_area) if info.total_area else None,
            living_area=float(info.living_area) if info.living_area else None,
            floors_count=info.floors_count,
            entrances_count=info.entrances_count,
            construction_year=info.construction_year,
            project_type=info.project_type,
            object_status=info.object_status,
            last_repair=info.last_repair,
            replanning=info.replanning,
            organization=info.organization,
            updated_at=info.updated_at
        )
