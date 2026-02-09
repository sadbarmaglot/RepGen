"""
Сервис генерации отчётов.
Собирает данные из БД, генерирует DOCX, загружает в GCS, возвращает signed URL.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.entities import Plan, Mark, Photo, PhotoDefectAnalysis
from api.models.database.enums import MarkType
from api.services.access_control_service import AccessControlService
from api.services.redis_service import redis_service
from common.gc_utils import upload_bytes_to_gcs, create_signed_url
from docx_generator.generate_defects_statement_2_report import generate_defects_statement_2_report

logger = logging.getLogger(__name__)

# Типы конструкций (синхронизировано с веб-клиентом и десктопом)
CONSTRUCTION_TYPES = [
    'Фундамент',
    'Фасад',
    'Стена',
    'Пол',
    'Перекрытие',
    'Покрытие',
    'Отмостка',
    'Крыльцо',
    'Балкон/лоджия',
    'Лестница',
    'Перемычка',
    'Стропильная система',
    'Стропильная ферма покрытия',
    'Колонна каркаса',
    'Ригель каркаса',
    'Кровля',
    'Отделочное покрытие',
    'Козырёк',
    'Межпанельные швы',
    'Окна',
    'Двери',
    'Подвальное помещение',
    'Чердачное помещение',
    'Технический этаж',
    'Водосточная система',
    'Стойка',
    'Столб',
    'Инженерные сети: система холодного водоснабжения',
    'Инженерные сети: система горячего водоснабжения',
    'Инженерные сети: система водоотведения/канализация',
    'Инженерные сети: система отопления',
    'Инженерные сети: система электроснабжения',
    'Инженерные сети: система дымоудаления',
    'Инженерные сети: система вентиляции',
    'Инженерные сети: система газоснабжения',
    'Инженерные сети: система оповещения о пожаре и пожарной автоматике',
    'Лифт',
    'Другие конструкции',
]

# Приоритет единиц измерения (меньше = выше приоритет)
UNIT_PRIORITY = {
    'мм': 1,
    'ед.': 2,
    'м²': 3,
    'пог.м.': 4,
    'м³': 5,
}

# Маппинг единиц из enum в читаемый вид
UNIT_MAP = {
    'm2': 'м²',
    'm3': 'м³',
    'pog_m': 'пог.м.',
    'mm': 'мм',
    'pcs': 'ед.',
}

# Маппинг категорий (DB enum → кириллица)
CATEGORY_MAP = {
    'A': 'А',
    'B': 'Б',
    'C': 'В',
}

# Приоритет категорий (больше = выше приоритет)
CATEGORY_PRIORITY = {
    'A': 3,
    'B': 2,
    'C': 1,
}

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.access_control = AccessControlService(db)

    async def generate_defects_report(self, object_id: int, user_id: int) -> str:
        """
        Генерация отчёта «Ведомость дефектов и повреждений №2».
        Возвращает signed URL для скачивания.
        """
        # Проверяем доступ к объекту
        if not await self.access_control.check_object_access(object_id, user_id):
            raise ValueError("Объект не найден или у вас нет прав доступа к нему")

        # Проверяем кеш
        cache_key = f"report:defects:{object_id}"
        cached_url = await redis_service.get(cache_key)
        if cached_url:
            return cached_url

        # Собираем данные
        rows = await self._collect_defect_rows(object_id)

        # Генерируем DOCX
        buffer = generate_defects_statement_2_report(rows)

        # Загружаем в GCS
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/{object_id}/defects_{timestamp}.docx"
        await upload_bytes_to_gcs(buffer.getvalue(), filename, content_type=DOCX_CONTENT_TYPE)

        # Создаём signed URL
        signed_url = await create_signed_url(filename, expiration_minutes=60, content_type=DOCX_CONTENT_TYPE)

        # Кешируем
        await redis_service.set(cache_key, signed_url, ttl_seconds=3600)

        return signed_url

    async def _collect_defect_rows(self, object_id: int) -> list[dict]:
        """
        Собирает данные дефектов и группирует их — порт логики из DefectsPage.tsx.
        """
        # Загружаем все данные одним запросом с join-ами
        stmt = (
            select(Plan, Mark, Photo, PhotoDefectAnalysis)
            .join(Mark, Mark.plan_id == Plan.id)
            .join(Photo, Photo.mark_id == Mark.id)
            .join(PhotoDefectAnalysis, PhotoDefectAnalysis.photo_id == Photo.id)
            .where(Plan.object_id == object_id)
            .where(Mark.type == MarkType.defect)
            .order_by(Plan.id, Photo.id)
        )
        result = await self.db.execute(stmt)
        raw_rows = result.all()

        # Структурируем данные: plan_id -> plan_name, и список (plan, mark, photo, analysis)
        all_entries = []
        for plan, mark, photo, analysis in raw_rows:
            all_entries.append({
                "plan_id": plan.id,
                "plan_name": plan.name or "",
                "mark": mark,
                "photo": photo,
                "analysis": analysis,
            })

        # Группировка — идентична логике DefectsPage.tsx
        groups: dict[str, dict] = {}

        for construction_type in CONSTRUCTION_TYPES:
            for entry in all_entries:
                photo = entry["photo"]
                photo_type = (photo.type or "").strip()
                if photo_type != construction_type:
                    continue

                analysis = entry["analysis"]
                description = (analysis.defect_description or "").strip()
                recommendation = (analysis.recommendation or "").strip()
                if not description or not recommendation:
                    continue

                normalized_desc = " ".join(description.lower().split())
                group_key = f"{entry['plan_id']}|||{construction_type}|||{normalized_desc}"

                if group_key not in groups:
                    groups[group_key] = {
                        "description": description,
                        "construction_type": construction_type,
                        "plan_name": entry["plan_name"],
                        "volumes": [],
                        "photo_name": photo.image_name or "",
                        "category": analysis.category.value if analysis.category else "",
                        "recommendations": [],
                        "processed_mark_ids": set(),
                    }

                group = groups[group_key]
                mark = entry["mark"]

                if mark.id not in group["processed_mark_ids"]:
                    group["processed_mark_ids"].add(mark.id)

                    if mark.defect_volume_value is not None:
                        unit_raw = mark.defect_volume_unit.value if mark.defect_volume_unit else ""
                        unit = UNIT_MAP.get(unit_raw, unit_raw)
                        group["volumes"].append({
                            "value": float(mark.defect_volume_value),
                            "unit": unit,
                        })

                # Обновляем категорию (берём максимальный приоритет)
                if analysis.category:
                    new_priority = CATEGORY_PRIORITY.get(analysis.category.value, 0)
                    current_priority = CATEGORY_PRIORITY.get(group["category"], 0)
                    if new_priority > current_priority:
                        group["category"] = analysis.category.value

                if recommendation and recommendation not in group["recommendations"]:
                    group["recommendations"].append(recommendation)

                if not group["photo_name"] and photo.image_name:
                    group["photo_name"] = photo.image_name

        # Формируем строки для DOCX
        rows = []
        counter = 1
        for group in groups.values():
            total_volume = ""
            if group["volumes"]:
                volumes_by_unit: dict[str, list[float]] = {}
                for v in group["volumes"]:
                    volumes_by_unit.setdefault(v["unit"], []).append(v["value"])

                units = [u for u in volumes_by_unit if u]
                if units:
                    min_unit = min(units, key=lambda u: UNIT_PRIORITY.get(u, 999))
                    s = sum(volumes_by_unit[min_unit])
                    total_volume = f"{s:g}"
                else:
                    s = sum(v["value"] for v in group["volumes"])
                    total_volume = f"{s:g}"

            recommendations = group["recommendations"]
            work_recommendations = recommendations[0] if recommendations else ""
            work_types = "; ".join(recommendations[1:]) if len(recommendations) > 1 else work_recommendations

            # Маппинг категории из DB enum в кириллицу
            category_display = CATEGORY_MAP.get(group["category"], group["category"])

            rows.append({
                "number": str(counter),
                "scheme_name": group["plan_name"],
                "element_name": group["construction_type"],
                "defect_volume": total_volume,
                "defects_and_causes": group["description"],
                "photo": group["photo_name"],
                "danger_category": category_display,
                "work_recommendations": work_recommendations,
                "recommended_work_types": work_types,
            })
            counter += 1

        return rows
