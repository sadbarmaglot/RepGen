import logging
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.services.database import get_db
from api.services.web_auth_service import WebAuthService
from api.services.report_service import ReportService
from api.services.redis_service import redis_service
from api.models.entities import (
    WebUser, Object, Plan, Mark, Photo,
    PhotoDefectAnalysis, ObjectGeneralInfo, WearElement, ObjectWearItem,
)
from api.models.responses import (
    ProjectResponse, ProjectListResponse,
    ObjectResponse, ObjectListResponse,
    PlanResponse, PlanListResponse,
    MarkWithPhotosResponse, MarkWithPhotosListResponse,
    PhotoResponse,
    PhotoDefectAnalysisListResponse, PhotoDefectAnalysisResponse,
    CATEGORY_DISPLAY_MAP,
    GeneralInfoResponse,
    WearCalculationResponse,
)
from api.models.database.enums import DefectCategory
from api.dependencies.auth_dependencies import get_current_web_user
from common.gc_utils import create_signed_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/web", tags=["web-data"])


async def _check_project_access(web_user: WebUser, project_id: int, db: AsyncSession):
    service = WebAuthService(db)
    if not await service.check_project_access(web_user, project_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к проекту")


async def _check_object_project_access(web_user: WebUser, object_id: int, db: AsyncSession):
    """Проверяет что объект существует и web_user имеет доступ к его проекту"""
    result = await db.execute(select(Object).where(Object.id == object_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объект не найден")
    await _check_project_access(web_user, obj.project_id, db)
    return obj


# --- Projects ---

@router.get("/projects", response_model=ProjectListResponse)
async def web_get_projects(
    web_user: WebUser = Depends(get_current_web_user),
    db: AsyncSession = Depends(get_db),
):
    service = WebAuthService(db)
    projects = await service.get_user_projects(web_user)
    return ProjectListResponse(
        projects=[ProjectResponse.model_validate(p) for p in projects],
        total=len(projects),
    )


# --- Objects ---

@router.get("/projects/{project_id}/objects", response_model=ObjectListResponse)
async def web_get_project_objects(
    project_id: int,
    web_user: WebUser = Depends(get_current_web_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_project_access(web_user, project_id, db)

    result = await db.execute(
        select(Object).where(Object.project_id == project_id).order_by(Object.id)
    )
    objects = result.scalars().all()

    return ObjectListResponse(
        objects=[ObjectResponse.model_validate(o) for o in objects],
        total=len(objects),
    )


# --- Plans ---

@router.get("/objects/{object_id}/plans", response_model=PlanListResponse)
async def web_get_object_plans(
    object_id: int,
    web_user: WebUser = Depends(get_current_web_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_object_project_access(web_user, object_id, db)

    result = await db.execute(
        select(Plan).where(Plan.object_id == object_id).order_by(Plan.id)
    )
    plans = result.scalars().all()

    plan_responses = []
    for plan in plans:
        image_url = None
        if plan.image_name:
            try:
                cached = await redis_service.get_signed_url(plan.image_name)
                if cached:
                    image_url = cached
                else:
                    image_url = await create_signed_url(plan.image_name, expiration_minutes=60)
                    await redis_service.cache_signed_url(plan.image_name, image_url, ttl_seconds=3000)
            except Exception:
                pass
        plan_responses.append(PlanResponse(
            id=plan.id, object_id=plan.object_id, name=plan.name,
            description=plan.description, image_url=image_url, created_at=plan.created_at,
        ))

    return PlanListResponse(plans=plan_responses, total=len(plan_responses))


# --- Marks with photos ---

@router.get("/plans/{plan_id}/marks-with-photos", response_model=MarkWithPhotosListResponse)
async def web_get_plan_marks_with_photos(
    plan_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(2000, ge=1, le=2000),
    web_user: WebUser = Depends(get_current_web_user),
    db: AsyncSession = Depends(get_db),
):
    # Проверяем доступ через plan -> object -> project
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="План не найден")
    await _check_object_project_access(web_user, plan.object_id, db)

    count_result = await db.execute(
        select(func.count(Mark.id)).where(Mark.plan_id == plan_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Mark)
        .options(selectinload(Mark.photos))
        .where(Mark.plan_id == plan_id)
        .order_by(Mark.id)
        .offset(skip)
        .limit(limit)
    )
    marks = result.scalars().all()

    # Collect all photos for parallel signed URL generation
    all_photos = []
    mark_photo_mapping = {}
    for mark in marks:
        sorted_photos = sorted(mark.photos, key=lambda p: (p.order if p.order is not None else float('inf'), p.id))
        mark_photo_mapping[mark.id] = sorted_photos
        all_photos.extend(sorted_photos)

    async def photo_to_response(photo: Photo) -> PhotoResponse:
        image_url = None
        if photo.image_name:
            try:
                cached = await redis_service.get_signed_url(photo.image_name)
                if cached:
                    image_url = cached
                else:
                    image_url = await create_signed_url(photo.image_name, expiration_minutes=60)
                    await redis_service.cache_signed_url(photo.image_name, image_url, ttl_seconds=3000)
            except Exception:
                pass
        return PhotoResponse(
            id=photo.id, mark_id=photo.mark_id, image_name=photo.image_name,
            image_url=image_url, type=photo.type, description=photo.description,
            order=photo.order,
            type_confidence=float(photo.type_confidence) if photo.type_confidence is not None else None,
            created_at=photo.created_at,
        )

    all_photo_responses = await asyncio.gather(*[photo_to_response(p) for p in all_photos])
    photo_response_map = {photo.id: resp for photo, resp in zip(all_photos, all_photo_responses)}

    mark_responses = []
    for mark in marks:
        photo_responses = [photo_response_map[p.id] for p in mark_photo_mapping[mark.id]]
        mark_responses.append(MarkWithPhotosResponse(
            id=mark.id, plan_id=mark.plan_id, name=mark.name,
            description=mark.description, type=mark.type,
            x=mark.x, y=mark.y, is_horizontal=mark.is_horizontal,
            defect_volume_value=mark.defect_volume_value,
            defect_volume_unit=mark.defect_volume_unit,
            defect_type=mark.defect_type,
            photos=photo_responses, created_at=mark.created_at,
        ))

    return MarkWithPhotosListResponse(marks=mark_responses, total=total)


# --- Defect analyses ---

@router.get("/objects/{object_id}/defect-analyses", response_model=PhotoDefectAnalysisListResponse)
async def web_get_defect_analyses(
    object_id: int,
    web_user: WebUser = Depends(get_current_web_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_object_project_access(web_user, object_id, db)

    result = await db.execute(
        select(PhotoDefectAnalysis)
        .where(PhotoDefectAnalysis.object_id == object_id)
        .order_by(PhotoDefectAnalysis.created_at.desc())
    )
    analyses = result.scalars().all()

    responses = []
    for a in analyses:
        cat_value = a.category.value if hasattr(a.category, 'value') else str(a.category)
        display_cat = CATEGORY_DISPLAY_MAP.get(cat_value, cat_value)
        responses.append(PhotoDefectAnalysisResponse(
            id=a.id, photo_id=a.photo_id, defect_code=a.defect_code,
            defect_description=a.defect_description, recommendation=a.recommendation,
            category=display_cat,
            confidence=float(a.confidence) if a.confidence is not None else None,
            created_at=a.created_at,
        ))

    return PhotoDefectAnalysisListResponse(analyses=responses, total=len(responses))


# --- General info ---

@router.get("/objects/{object_id}/general-info", response_model=GeneralInfoResponse)
async def web_get_general_info(
    object_id: int,
    web_user: WebUser = Depends(get_current_web_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_object_project_access(web_user, object_id, db)

    result = await db.execute(
        select(ObjectGeneralInfo).where(ObjectGeneralInfo.object_id == object_id)
    )
    info = result.scalar_one_or_none()

    if not info:
        return GeneralInfoResponse(object_id=object_id)

    return GeneralInfoResponse.model_validate(info)


# --- Wear ---

@router.get("/objects/{object_id}/wear", response_model=WearCalculationResponse)
async def web_get_wear(
    object_id: int,
    web_user: WebUser = Depends(get_current_web_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_object_project_access(web_user, object_id, db)

    from api.services.wear_service import WearService
    service = WearService(db)
    return await service.get_object_wear_internal(object_id)


# --- Reports ---

@router.post("/objects/{object_id}/reports/defects")
async def web_generate_defects_report(
    object_id: int,
    web_user: WebUser = Depends(get_current_web_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_object_project_access(web_user, object_id, db)

    service = ReportService(db)
    download_url = await service.generate_defects_report_internal(object_id)
    return {"download_url": download_url, "expires_in": 3600}
