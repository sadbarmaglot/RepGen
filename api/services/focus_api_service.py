import os
import hmac
import time
import json
import httpx
import base64
import logging
import zipfile
import hashlib
import tempfile
import shutil

from typing import Optional, Tuple, Dict
from fastapi import HTTPException

from settings import FOCUS_API_URL, FOCUS_API_KEY, FOCUS_API_SECRET
from common.gc_utils import upload_file_to_gcs_with_signed_url, download_file_from_gcs

logger = logging.getLogger(__name__)


class FocusAPIService:
    """Сервис для работы с Focus API"""
    
    def __init__(self):
        self.api_url = FOCUS_API_URL
        self.api_key = FOCUS_API_KEY
        self.secret = FOCUS_API_SECRET
        self.timeout = 120.0  # 2 минуты для долгих операций генерации плана
        
    def _generate_signature(self, timestamp: str, body_sha256: str) -> str:
        """Генерирует HMAC подпись для запроса"""
        to_sign = f"{timestamp}.{body_sha256}".encode("utf-8")
        signature = hmac.new(
            self.secret.encode("utf-8"),
            to_sign,
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _prepare_headers(self, payload: str) -> dict:
        """Подготавливает заголовки с подписью для запроса"""
        timestamp = str(int(time.time()))
        body_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        signature = self._generate_signature(timestamp, body_sha256)
        
        return {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "x-webhook-timestamp": timestamp,
            "x-body-sha256": body_sha256,
            "x-webhook-signature": signature
        }
    
    def _prepare_image_payload(self, image_bytes: bytes, filename: str, mime_type: str = "image/jpeg") -> str:
        """Подготавливает payload с изображением в формате base64 data URL"""
        b64_data = base64.b64encode(image_bytes).decode("utf-8")
        payload_data = {
            "data": f"data:{mime_type};base64,{b64_data}",
            "filename": filename
        }
        return json.dumps(payload_data)
    
    async def download_image_from_gcs(self, image_name: str) -> Tuple[bytes, str]:
        """
        Загружает изображение из GCS по имени файла
        
        Args:
            image_name: Имя файла в GCS bucket
            
        Returns:
            tuple[bytes, str]: (байты изображения, MIME тип)
            
        Raises:
            HTTPException: При ошибке загрузки из GCS
        """
        try:
            image_bytes, mime_type = await download_file_from_gcs(image_name)
            return image_bytes, mime_type
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=404,
                detail=str(e)
            )
        except Exception as e:
            error_msg = f"Ошибка при загрузке изображения {image_name} из GCS: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    async def process_image(
        self,
        image_bytes: bytes,
        filename: str,
        mime_type: Optional[str] = None
    ) -> dict:
        """
        Отправляет изображение на обработку в Focus API
        
        Args:
            image_bytes: Байты изображения
            filename: Имя файла
            mime_type: MIME тип изображения (по умолчанию image/jpeg)
            
        Returns:
            dict: Ответ от API
            
        Raises:
            HTTPException: При ошибке запроса к API
        """
        if mime_type is None:
            ext = filename.lower().split('.')[-1] if '.' in filename else 'jpg'
            mime_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')
        
        try:
            payload = self._prepare_image_payload(image_bytes, filename, mime_type)
            
            headers = self._prepare_headers(payload)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    content=payload,
                    headers=headers
                )
                
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "").lower()
                
                if "application/zip" in content_type or "application/x-zip-compressed" in content_type:
                    zip_bytes = response.content
                    return await self._process_zip_response(zip_bytes, filename)
                
                try:
                    result = response.json()
                    return result
                except json.JSONDecodeError:
                    logger.warning(f"Ответ от Focus API не является JSON для файла {filename}")
                    return {"response": response.text}
                    
        except httpx.HTTPStatusError as e:
            error_msg = f"Ошибка HTTP при запросе к Focus API: {e.response.status_code}"
            if e.response.text:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {e.response.text}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=error_msg
            )
        except httpx.TimeoutException:
            error_msg = f"Таймаут при запросе к Focus API (>{self.timeout}с)"
            logger.error(error_msg)
            raise HTTPException(status_code=504, detail=error_msg)
        except Exception as e:
            error_msg = f"Неожиданная ошибка при запросе к Focus API: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    async def process_image_by_name(
        self,
        image_name: str,
        mime_type: Optional[str] = None
    ) -> dict:
        """
        Загружает изображение из GCS и отправляет на обработку в Focus API
        
        Args:
            image_name: Имя файла в GCS bucket
            mime_type: MIME тип изображения (опционально, определяется автоматически)
            
        Returns:
            dict: Ответ от API
            
        Raises:
            HTTPException: При ошибке загрузки или запроса к API
        """
        image_bytes, detected_mime_type = await self.download_image_from_gcs(image_name)
        
        final_mime_type = mime_type or detected_mime_type
        
        return await self.process_image(image_bytes, image_name, final_mime_type)
    
    async def _process_zip_response(self, zip_bytes: bytes, original_filename: str) -> Dict:
        """
        Обрабатывает ZIP архив от Focus API: распаковывает, загружает PNG и DXF в GCS
        
        Args:
            zip_bytes: Байты ZIP архива
            original_filename: Имя исходного файла (для создания уникальных имен)
            
        Returns:
            dict: Словарь с подписанными ссылками на PNG и DXF файлы
        """
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "response.zip")
            
            with open(zip_path, "wb") as f:
                f.write(zip_bytes)
            
            image_files = []  # PNG, JPG, JPEG файлы
            dxf_files = []
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.namelist():
                    if file_info.endswith('/'):
                        continue
                    
                    extracted_path = zip_ref.extract(file_info, temp_dir)
                    
                    file_ext = os.path.splitext(file_info)[1].lower()
                    
                    if file_ext in ['.png', '.jpg', '.jpeg']:
                        image_files.append((extracted_path, file_ext))
                    elif file_ext == '.dxf':
                        dxf_files.append(extracted_path)
            
            if not image_files and not dxf_files:
                raise HTTPException(
                    status_code=500,
                    detail="В ZIP архиве не найдено изображений (PNG/JPG) или DXF файлов"
                )
            
            image_urls = []
            for image_path, file_ext in image_files:
                if file_ext == '.png':
                    extension = "png"
                    content_type = "image/png"
                elif file_ext in ['.jpg', '.jpeg']:
                    extension = "jpg"
                    content_type = "image/jpeg"
                else:
                    extension = file_ext.lstrip('.')
                    content_type = "image/jpeg"
                
                image_name, signed_url = await upload_file_to_gcs_with_signed_url(
                    image_path, 
                    extension,
                    "focus_plan",
                    content_type
                )
                image_urls.append({
                    "filename": image_name,
                    "signed_url": signed_url
                })
            
            dxf_urls = []
            for dxf_path in dxf_files:
                dxf_name, signed_url = await upload_file_to_gcs_with_signed_url(
                    dxf_path,
                    "dxf",
                    "focus_plan",
                    "application/dxf"
                )
                dxf_urls.append({
                    "filename": dxf_name,
                    "signed_url": signed_url
                })
            
            return {
                "image_files": image_urls,
                "dxf_files": dxf_urls,
                "original_filename": original_filename
            }
            
        except zipfile.BadZipFile:
            error_msg = "Полученный файл не является валидным ZIP архивом"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        except Exception as e:
            error_msg = f"Ошибка при обработке ZIP архива: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    shutil.rmtree(temp_dir, ignore_errors=True)
