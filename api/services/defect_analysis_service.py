import logging
from typing import List, Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from api.models.entities import Photo, PhotoDefectAnalysis
from api.models.entities.plan import Plan
from api.models.entities.mark import Mark
from api.models.database.enums import DefectCategory
from api.models.responses import PhotoDefectAnalysisResponse, PhotoDefectAnalysisListResponse, CATEGORY_DISPLAY_MAP
from api.services.access_control_service import AccessControlService

logger = logging.getLogger(__name__)

CATEGORY_INPUT_MAP = {
    "А": "A",
    "Б": "B",
    "В": "C",
}


class DefectAnalysisService:
    """Сервис для работы с анализом дефектов по фотографиям"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.access_control = AccessControlService(db)
    
    async def create_analysis(
        self,
        photo_id: int,
        defect_description: str,
        recommendation: str,
        category: str,
        confidence: Optional[float] = None,
        defect_code: Optional[str] = None,
        object_id: Optional[int] = None
    ) -> PhotoDefectAnalysis:
        """Создание или обновление анализа дефекта"""

        normalized_category = CATEGORY_INPUT_MAP.get(category)
        if normalized_category is None:
            raise ValueError(f"Неверная категория дефекта: {category}. Допустимые значения: А, Б, В (или A, B, C)")

        try:
            category_enum = DefectCategory(normalized_category)
        except ValueError:
            raise ValueError(f"Неверная категория дефекта: {category}")

        # Проверяем что фото существует
        result = await self.db.execute(
            select(Photo).where(Photo.id == photo_id)
        )
        photo = result.scalar_one_or_none()

        if not photo:
            raise ValueError(f"Фотография с ID {photo_id} не найдена")

        # Проверяем, есть ли уже анализ для этого фото
        existing_result = await self.db.execute(
            select(PhotoDefectAnalysis).where(PhotoDefectAnalysis.photo_id == photo_id)
        )
        existing_analysis = existing_result.scalar_one_or_none()

        try:
            if existing_analysis:
                # Обновляем существующий анализ
                if object_id is not None:
                    existing_analysis.object_id = object_id
                existing_analysis.defect_code = defect_code
                existing_analysis.defect_description = defect_description
                existing_analysis.recommendation = recommendation
                existing_analysis.category = category_enum
                existing_analysis.confidence = Decimal(str(confidence)) if confidence is not None else None
                await self.db.commit()
                await self.db.refresh(existing_analysis)
                return existing_analysis
            else:
                # Создаем новый анализ
                analysis = PhotoDefectAnalysis(
                    photo_id=photo_id,
                    object_id=object_id,
                    defect_code=defect_code,
                    defect_description=defect_description,
                    recommendation=recommendation,
                    category=category_enum,
                    confidence=Decimal(str(confidence)) if confidence is not None else None
                )
                self.db.add(analysis)
                await self.db.commit()
                await self.db.refresh(analysis)
                return analysis
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при сохранении анализа: {str(e)}")
    
    async def update_analysis(
        self,
        photo_id: int,
        user_id: int,
        defect_description: Optional[str] = None,
        recommendation: Optional[str] = None,
        category: Optional[str] = None,
        defect_code: Optional[str] = None,
        object_id: Optional[int] = None
    ) -> PhotoDefectAnalysis:
        """Обновление анализа дефекта пользователем (partial update)"""

        # Проверяем доступ к фото
        if not await self.access_control.check_photo_access(photo_id, user_id):
            raise ValueError("Фотография не найдена или нет доступа")

        # Нормализуем категорию если передана
        category_enum = None
        if category is not None:
            normalized_category = CATEGORY_INPUT_MAP.get(category)
            if normalized_category is None:
                raise ValueError(f"Неверная категория дефекта: {category}. Допустимые значения: А, Б, В (или A, B, C)")
            category_enum = DefectCategory(normalized_category)

        # Ищем существующий анализ
        result = await self.db.execute(
            select(PhotoDefectAnalysis).where(PhotoDefectAnalysis.photo_id == photo_id)
        )
        existing_analysis = result.scalar_one_or_none()

        try:
            if existing_analysis:
                # Обновляем только переданные поля
                if defect_description is not None:
                    existing_analysis.defect_description = defect_description
                    existing_analysis.defect_code = None  # Обнуляем код при ручном изменении описания
                if recommendation is not None:
                    existing_analysis.recommendation = recommendation
                    existing_analysis.defect_code = None  # Обнуляем код при ручном изменении рекомендации
                if category_enum is not None:
                    existing_analysis.category = category_enum
                if defect_code is not None:
                    existing_analysis.defect_code = defect_code  # Явно переданный код имеет приоритет
                if object_id is not None:
                    existing_analysis.object_id = object_id
                existing_analysis.confidence = Decimal("1.0")  # Пользовательский ввод = 100% уверенность
                await self.db.commit()
                await self.db.refresh(existing_analysis)
                return existing_analysis
            else:
                # Создаем новый анализ с переданными полями
                analysis = PhotoDefectAnalysis(
                    photo_id=photo_id,
                    object_id=object_id,
                    defect_code=defect_code,
                    defect_description=defect_description,
                    recommendation=recommendation,
                    category=category_enum,
                    confidence=Decimal("1.0")
                )
                self.db.add(analysis)
                await self.db.commit()
                await self.db.refresh(analysis)
                return analysis
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при обновлении анализа: {str(e)}")
    
    async def get_by_photo(self, photo_id: int, user_id: int) -> PhotoDefectAnalysisListResponse:
        """Получение анализов для конкретной фотографии"""
        
        # Проверяем доступ к фото
        if not await self.access_control.check_photo_access(photo_id, user_id):
            raise ValueError("Фотография не найдена или нет доступа")
        
        result = await self.db.execute(
            select(PhotoDefectAnalysis)
            .where(PhotoDefectAnalysis.photo_id == photo_id)
            .order_by(PhotoDefectAnalysis.created_at.desc())
        )
        analyses = result.scalars().all()
        
        return self._to_list_response(analyses)
    
    async def get_by_mark(self, mark_id: int, user_id: int) -> PhotoDefectAnalysisListResponse:
        """Получение анализов для всех фотографий марки"""
        
        # Проверяем доступ к марке
        if not await self.access_control.check_mark_access(mark_id, user_id):
            raise ValueError("Марка не найдена или нет доступа")
        
        # Получаем все анализы через цепочку mark -> photos -> analyses
        result = await self.db.execute(
            select(PhotoDefectAnalysis)
            .join(Photo, PhotoDefectAnalysis.photo_id == Photo.id)
            .where(Photo.mark_id == mark_id)
            .order_by(PhotoDefectAnalysis.created_at.desc())
        )
        analyses = result.scalars().all()
        
        return self._to_list_response(analyses)
    
    async def get_by_plan(self, plan_id: int, user_id: int) -> PhotoDefectAnalysisListResponse:
        """Получение анализов для всех фотографий плана"""
        
        # Проверяем доступ к плану
        if not await self.access_control.check_plan_access(plan_id, user_id):
            raise ValueError("План не найден или нет доступа")
        
        # Получаем все анализы через цепочку plan -> marks -> photos -> analyses
        result = await self.db.execute(
            select(PhotoDefectAnalysis)
            .join(Photo, PhotoDefectAnalysis.photo_id == Photo.id)
            .join(Mark, Photo.mark_id == Mark.id)
            .where(Mark.plan_id == plan_id)
            .order_by(PhotoDefectAnalysis.created_at.desc())
        )
        analyses = result.scalars().all()
        
        return self._to_list_response(analyses)
    
    async def get_by_object(self, object_id: int, user_id: int) -> PhotoDefectAnalysisListResponse:
        """Получение анализов для всех фотографий объекта"""

        # Проверяем доступ к объекту
        if not await self.access_control.check_object_access(object_id, user_id):
            raise ValueError("Объект не найден или нет доступа")

        # Прямой запрос по object_id
        result = await self.db.execute(
            select(PhotoDefectAnalysis)
            .where(PhotoDefectAnalysis.object_id == object_id)
            .order_by(PhotoDefectAnalysis.created_at.desc())
        )
        analyses = result.scalars().all()

        return self._to_list_response(analyses)
    
    def _to_response(self, analysis: PhotoDefectAnalysis) -> PhotoDefectAnalysisResponse:
        """Преобразование модели в ответ с маппингом категории"""
        # Маппим категорию A→А, B→Б, C→В
        category_value = analysis.category.value if hasattr(analysis.category, 'value') else str(analysis.category)
        display_category = CATEGORY_DISPLAY_MAP.get(category_value, category_value)

        return PhotoDefectAnalysisResponse(
            id=analysis.id,
            photo_id=analysis.photo_id,
            defect_code=analysis.defect_code,
            defect_description=analysis.defect_description,
            recommendation=analysis.recommendation,
            category=display_category,
            confidence=float(analysis.confidence) if analysis.confidence is not None else None,
            created_at=analysis.created_at
        )
    
    def _to_list_response(self, analyses: List[PhotoDefectAnalysis]) -> PhotoDefectAnalysisListResponse:
        """Преобразование списка моделей в ответ"""
        return PhotoDefectAnalysisListResponse(
            analyses=[self._to_response(a) for a in analyses],
            total=len(analyses)
        )
