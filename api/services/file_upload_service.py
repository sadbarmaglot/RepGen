import os
import sys
import tempfile
import logging
from typing import List
from fastapi import UploadFile, HTTPException

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from common.gc_utils import upload_to_gcs, create_signed_url, upload_to_gcs_with_blob

logger = logging.getLogger(__name__)

class FileUploadService:
    """Сервис для загрузки файлов в GCP Cloud Storage"""
    
    def __init__(self):
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
    async def upload_file(
        self, 
        file: UploadFile, 
        create_signed_url_flag: bool = False, 
        expiration_minutes: int = 60
        ) -> dict:
        """
        Загружает файл в GCP Cloud Storage
        
        Args:
            file: Загружаемый файл
            create_signed_url_flag: Создавать ли подписной URL для Gemini Pro
            expiration_minutes: Время жизни подписного URL в минутах
            
        Returns:
            Tuple[str, str, str]: (имя файла, публичный URL, подписной URL)
        """
        try:
            file_extension = os.path.splitext(file.filename)[1].lower()
            
            if file.size and file.size > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"Файл слишком большой. Максимальный размер: {self.max_file_size // (1024*1024)}MB"
                )
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file.flush()
                
                try:
                    blob, public_url = await upload_to_gcs(temp_file.name, file_extension[1:])
                    
                    result = {
                        "filename": blob.name,
                        "public_url": public_url,
                        "signed_url": "",
                        "mime_type": blob.content_type
                    }

                    if not create_signed_url_flag:
                        logger.info(f"Файл {file.filename} успешно загружен в GCS: {public_url}")
                        return result

                    signed_url = await create_signed_url(blob.name, expiration_minutes)
                    result["signed_url"] = signed_url
                    logger.info(f"Файл {file.filename} успешно загружен в GCS с подписным URL для Gemini Pro: {signed_url}")
                    return result
                    
                finally:
                    os.unlink(temp_file.name)
                    
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ошибка при загрузке файла: {str(e)}")
    
    async def _upload_file_to_gcs(
        self, 
        file: UploadFile,
        ) -> dict:
        """
        Загружает файл в GCP Cloud Storage
        
        Args:
            file: Загружаемый файл
            
        Returns:
            Dict[str]: (имя файла)
        """
        try:
            file_extension = os.path.splitext(file.filename)[1].lower()
            
            if file.size and file.size > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"Файл слишком большой. Максимальный размер: {self.max_file_size // (1024*1024)}MB"
                )
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file.flush()
                
                try:
                    blob = await upload_to_gcs_with_blob(temp_file.name, file_extension[1:])
                    
                    result = {"image_name": blob.name}

                    logger.info(f"Файл {file.filename} успешно загружен в GCS: {blob.name}")
                    return result
                finally:
                    os.unlink(temp_file.name)
                    
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ошибка при загрузке файла: {str(e)}")

    async def upload_multiple_files(
        self, 
        files: List[UploadFile], 
        create_signed_urls_flag: bool = False, 
        expiration_minutes: int = 60
    ) -> List[dict]:
        """
        Загружает несколько файлов в GCP Cloud Storage
        
        Args:
            files: Список загружаемых файлов
            create_signed_urls: Создавать ли подписные URL для Gemini Pro
            expiration_minutes: Время жизни подписных URL в минутах
            
        Returns:
            List[Tuple[str, str, str]]: Список кортежей (имя файла, публичный URL, подписной URL)
        """
        if len(files) > 20:
            raise HTTPException(
                status_code=400,
                detail="Максимальное количество файлов: 20"
            )
        
        results = []
        for file in files:
            try:
                result = await self.upload_file(file, create_signed_urls_flag, expiration_minutes)
                results.append(result)
            except Exception as e:
                logger.error(f"Ошибка при загрузке файла {file.filename}: {str(e)}")
                continue
        
        return results

    async def upload_multiple_files_with_blob(
        self, 
        files: List[UploadFile]
    ) -> List[dict]:
        """
        Загружает несколько файлов в GCP Cloud Storage с blob
        
        Args:
            files: Список загружаемых файлов
            
        Returns:
            List[Dict]: Список имен файлов
        """
        if len(files) > 20:
            raise HTTPException(
                status_code=400,
                detail="Максимальное количество файлов: 20"
            )
        
        results = []
        for file in files:
            try:
                result = await self._upload_file_to_gcs(file)
                results.append(result)
            except Exception as e:
                logger.error(f"Ошибка при загрузке файла {file.filename}: {str(e)}")
                continue
        return results