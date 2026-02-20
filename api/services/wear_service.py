import logging
from typing import List, Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.models.entities import WearElement, ObjectWearItem, Object
from api.models.responses.wear_responses import (
    WearItemResponse,
    WearCalculationResponse,
    WearElementResponse,
    WearElementListResponse,
    CONDITION_DISPLAY_MAP
)
from api.services.access_control_service import AccessControlService

logger = logging.getLogger(__name__)


class WearService:
    """Сервис для расчёта износа объектов"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.access_control = AccessControlService(db)

    @staticmethod
    def get_technical_condition(assessment_percent: Optional[float]) -> Optional[str]:
        """Определение категории технического состояния по проценту износа"""
        if assessment_percent is None:
            return None
        if assessment_percent <= 30:
            return "cat_1"
        elif assessment_percent <= 50:
            return "cat_2"
        elif assessment_percent <= 65:
            return "cat_3"
        else:
            return "cat_4"

    @staticmethod
    def calculate_weighted_average(
        assessment_percent: Optional[float],
        default_weight: Optional[float]
    ) -> Optional[float]:
        """Расчёт средневзвешенного значения износа"""
        if assessment_percent is None or default_weight is None:
            return None
        return round((assessment_percent / 100) * default_weight, 2)

    @staticmethod
    def get_overall_condition(total_wear: Optional[float]) -> Optional[str]:
        """Определение общей категории состояния по суммарному износу"""
        if total_wear is None:
            return None
        if total_wear <= 30:
            return "cat_1"
        elif total_wear <= 50:
            return "cat_2"
        elif total_wear <= 65:
            return "cat_3"
        else:
            return "cat_4"

    async def get_elements(self) -> WearElementListResponse:
        """Получение справочника элементов износа"""
        result = await self.db.execute(
            select(WearElement)
            .where(WearElement.is_active == True)
            .order_by(WearElement.sort_order)
        )
        elements = result.scalars().all()

        return WearElementListResponse(
            elements=[
                WearElementResponse(
                    id=el.id,
                    code=el.code,
                    name=el.name,
                    parent_id=el.parent_id,
                    default_weight=float(el.default_weight) if el.default_weight else None,
                    sort_order=el.sort_order
                )
                for el in elements
            ],
            total=len(elements)
        )

    async def get_object_wear(self, object_id: int, user_id: int) -> WearCalculationResponse:
        """Получение расчёта износа для объекта"""
        # Проверяем доступ
        if not await self.access_control.check_object_access(object_id, user_id):
            raise ValueError("Объект не найден или нет доступа")
        return await self.get_object_wear_internal(object_id)

    async def get_object_wear_internal(self, object_id: int) -> WearCalculationResponse:
        """Получение расчёта износа без проверки доступа (для web routes)"""
        # Получаем все элементы справочника
        elements_result = await self.db.execute(
            select(WearElement)
            .where(WearElement.is_active == True)
            .order_by(WearElement.sort_order)
        )
        elements = elements_result.scalars().all()

        # Получаем данные износа для объекта
        items_result = await self.db.execute(
            select(ObjectWearItem)
            .where(ObjectWearItem.object_id == object_id)
        )
        items_map = {item.element_id: item for item in items_result.scalars().all()}

        # Формируем ответ с расчётами
        response_items = []
        total_weighted = 0.0
        has_any_assessment = False

        for element in elements:
            item = items_map.get(element.id)

            default_weight = float(element.default_weight) if element.default_weight else None
            assessment = float(item.assessment_percent) if item and item.assessment_percent else None

            # Расчёты
            weighted_average = self.calculate_weighted_average(assessment, default_weight)
            condition = self.get_technical_condition(assessment)

            if weighted_average is not None:
                total_weighted += weighted_average
                has_any_assessment = True

            response_items.append(WearItemResponse(
                element_id=element.id,
                code=element.code,
                name=element.name,
                parent_id=element.parent_id,
                default_weight=default_weight,
                assessment_percent=assessment,
                weighted_average=weighted_average,
                technical_condition=condition,
                technical_condition_display=CONDITION_DISPLAY_MAP.get(condition) if condition else None,
                updated_at=item.updated_at if item else None
            ))

        # Итоговый износ и категория
        total_wear = round(total_weighted, 2) if has_any_assessment else None
        overall = self.get_overall_condition(total_wear)

        return WearCalculationResponse(
            object_id=object_id,
            items=response_items,
            total_wear=total_wear,
            overall_condition=overall,
            overall_condition_display=CONDITION_DISPLAY_MAP.get(overall) if overall else None
        )

    async def update_object_wear(
        self,
        object_id: int,
        user_id: int,
        items: List[dict]
    ) -> WearCalculationResponse:
        """Массовое обновление данных износа объекта"""
        # Проверяем доступ
        if not await self.access_control.check_object_access(object_id, user_id):
            raise ValueError("Объект не найден или нет доступа")

        # Получаем существующие записи
        existing_result = await self.db.execute(
            select(ObjectWearItem)
            .where(ObjectWearItem.object_id == object_id)
        )
        existing_map = {item.element_id: item for item in existing_result.scalars().all()}

        # Обновляем или создаём записи
        for item_data in items:
            element_id = item_data['element_id']
            assessment = item_data.get('assessment_percent')

            if element_id in existing_map:
                # Обновляем существующую запись
                existing_item = existing_map[element_id]
                if assessment is not None:
                    existing_item.assessment_percent = Decimal(str(assessment))
            else:
                # Создаём новую запись
                new_item = ObjectWearItem(
                    object_id=object_id,
                    element_id=element_id,
                    assessment_percent=Decimal(str(assessment)) if assessment is not None else None
                )
                self.db.add(new_item)

        await self.db.commit()

        # Возвращаем обновлённый расчёт
        return await self.get_object_wear(object_id, user_id)

    async def update_single_item(
        self,
        object_id: int,
        element_id: int,
        user_id: int,
        assessment_percent: Optional[float] = None
    ) -> WearCalculationResponse:
        """Обновление одного элемента износа"""
        # Проверяем доступ
        if not await self.access_control.check_object_access(object_id, user_id):
            raise ValueError("Объект не найден или нет доступа")

        # Проверяем что элемент существует
        element_result = await self.db.execute(
            select(WearElement).where(WearElement.id == element_id)
        )
        element = element_result.scalar_one_or_none()
        if not element:
            raise ValueError(f"Элемент с ID {element_id} не найден")

        # Ищем существующую запись
        existing_result = await self.db.execute(
            select(ObjectWearItem)
            .where(
                ObjectWearItem.object_id == object_id,
                ObjectWearItem.element_id == element_id
            )
        )
        existing_item = existing_result.scalar_one_or_none()

        if existing_item:
            # Обновляем
            if assessment_percent is not None:
                existing_item.assessment_percent = Decimal(str(assessment_percent))
        else:
            # Создаём
            new_item = ObjectWearItem(
                object_id=object_id,
                element_id=element_id,
                assessment_percent=Decimal(str(assessment_percent)) if assessment_percent is not None else None
            )
            self.db.add(new_item)

        await self.db.commit()

        # Возвращаем полный расчёт (чтобы фронт мог обновить total_wear)
        return await self.get_object_wear(object_id, user_id)

    async def initialize_object_wear(self, object_id: int) -> None:
        """Инициализация записей износа для нового объекта (вызывается при создании объекта)"""
        # Получаем все активные элементы
        elements_result = await self.db.execute(
            select(WearElement)
            .where(WearElement.is_active == True)
        )
        elements = elements_result.scalars().all()

        # Создаём пустые записи для каждого элемента
        for element in elements:
            item = ObjectWearItem(
                object_id=object_id,
                element_id=element.id,
                assessment_percent=None
            )
            self.db.add(item)

        await self.db.commit()
