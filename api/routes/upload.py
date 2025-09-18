import logging
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends

from api.services.file_upload_service import FileUploadService
from api.models.requests import UploadResponse as FileUploadResponse, FileUploadResponseWithBlob
from api.dependencies.auth_dependencies import get_current_user
from api.models.entities import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# Инициализация сервиса загрузки файлов
file_upload_service = FileUploadService()

@router.post("/images", response_model=List[FileUploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="Файлы для загрузки"),
    create_signed_urls: bool = True,
    expiration_minutes: int = 60,
    _: User = Depends(get_current_user)
):
    """
    Загрузка нескольких файлов в GCP Cloud Storage
    
    Требует аутентификации. Максимальный размер файла: 10MB
    Максимальное количество файлов: 20
    
    Параметры:
    - create_signed_urls: Создавать ли подписные URL для Gemini Pro
    - expiration_minutes: Время жизни подписных URL в минутах
    """
    try:
        logger.info(f"Получен запрос на загрузку {len(files)} файлов")
        
        upload_results = await file_upload_service.upload_multiple_files(
            files, 
            create_signed_urls_flag=create_signed_urls, 
            expiration_minutes=expiration_minutes
        )

        responses = []
        for i, image_info in enumerate(upload_results):
            if i < len(files):
                responses.append(FileUploadResponse(**image_info))
        
        return responses
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке файлов: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/images/blob", response_model=List[FileUploadResponseWithBlob])
async def upload_multiple_files_blob(
    files: List[UploadFile] = File(..., description="Файлы для загрузки"),
    _: User = Depends(get_current_user)
):
    """
    Загрузка нескольких файлов в GCP Cloud Storage
    
    Требует аутентификации. Максимальный размер файла: 10MB
    Максимальное количество файлов: 20
    """
    try:
        logger.info(f"Получен запрос на загрузку {len(files)} файлов")
        
        upload_results = await file_upload_service.upload_multiple_files_with_blob(files)

        responses = []
        for i, image_info in enumerate(upload_results):
            if i < len(files):
                responses.append(FileUploadResponseWithBlob(**image_info))
        
        return responses
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке файлов: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
