"""Маршруты для генерации отчётов"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.database import get_db
from api.services.report_service import ReportService
from api.dependencies.auth_dependencies import get_current_user
from api.models.entities import User

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/objects/{object_id}/defects")
async def generate_defects_report(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Генерация отчёта «Ведомость дефектов и повреждений №2» в формате DOCX"""
    try:
        service = ReportService(db)
        download_url = await service.generate_defects_report(object_id, current_user.id)
        return {"download_url": download_url, "expires_in": 3600}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка генерации отчёта: {str(e)}",
        )
