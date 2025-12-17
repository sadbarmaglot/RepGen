import logging

from fastapi import APIRouter, HTTPException, Depends

from api.services.focus_api_service import FocusAPIService
from api.models.entities import User
from api.dependencies.auth_dependencies import get_current_user
from api.models.requests import FocusImageProcessRequest
from api.models.responses import FileUrlInfo, FocusImageProcessResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/focus", tags=["focus"])

focus_api_service = FocusAPIService()


@router.post("/generate-plan", response_model=FocusImageProcessResponse)
async def generate_plan(
    request: FocusImageProcessRequest,
    _: User = Depends(get_current_user)
):
    """
    Генерация плана через Focus API
    
    Принимает имя изображения, которое уже загружено в хранилище GCS (через /upload/images),
    загружает его и отправляет в Focus API для генерации плана.
    Требует аутентификации.
    
    Порядок использования:
    1. Загрузите изображение через POST /upload/images
    2. Используйте полученное имя файла (image_name) в этом запросе
    
    MIME тип определяется автоматически из метаданных файла в GCS.
    
    Args:
        request: Запрос с именем изображения из хранилища
        
    Returns:
        FocusImageProcessResponse: Результат генерации плана от Focus API
    """
    try:
        logger.info(f"Получен запрос на генерацию плана через Focus API для изображения: {request.image_name}")
        
        result = await focus_api_service.process_image_by_name(
            image_name=request.image_name
        )
        
        if isinstance(result, dict) and ("image_files" in result or "dxf_files" in result):
            image_files = None
            dxf_files = None
            
            if "image_files" in result:
                image_files = [FileUrlInfo(**item) for item in result["image_files"]]
            
            if "dxf_files" in result:
                dxf_files = [FileUrlInfo(**item) for item in result["dxf_files"]]
            
            return FocusImageProcessResponse(
                success=True,
                image_files=image_files,
                dxf_files=dxf_files,
                original_filename=result.get("original_filename", request.image_name),
                message="План успешно сгенерирован и файлы загружены в хранилище"
            )
        else:
            return FocusImageProcessResponse(
                success=True,
                image_files=None,
                dxf_files=None,
                original_filename=request.image_name,
                message="План успешно сгенерирован"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации плана для изображения {request.image_name}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при генерации плана: {str(e)}"
        )
