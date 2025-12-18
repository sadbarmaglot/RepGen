import io
import os
import hmac
import time
import uuid
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
from PIL import Image, ImageOps

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

    def _maybe_shrink_image_for_focus_api(
        self,
        image_bytes: bytes,
        filename: str,
        mime_type: str,
        *,
        max_image_bytes: int = 6_000_000,
    ) -> Tuple[bytes, str, str]:
        """
        Гарантирует, что изображение не превышает лимит Focus API по размеру.

        Стратегия:
        - если уже <= max_image_bytes: вернуть как есть
        - иначе: декодировать через Pillow, привести к RGB (с белым фоном при alpha),
          затем попытаться сохранить в JPEG, понижая quality; если не помогает — уменьшать размер.

        Returns:
            (bytes, filename, mime_type) — возможно изменённые байты/имя/тип (обычно image/jpeg)
        """
        if len(image_bytes) <= max_image_bytes:
            return image_bytes, filename, mime_type

        original_size = len(image_bytes)
        t0 = time.perf_counter()

        try:
            img = Image.open(io.BytesIO(image_bytes))
            img = ImageOps.exif_transpose(img)
            img.load()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Не удалось декодировать изображение для сжатия (>{max_image_bytes} bytes): {str(e)}",
            )

        try:
            if img.mode in ("RGBA", "LA") or ("transparency" in getattr(img, "info", {})):
                rgba = img.convert("RGBA")
                background = Image.new("RGB", rgba.size, (255, 255, 255))
                background.paste(rgba, mask=rgba.split()[-1])
                img_rgb = background
            else:
                img_rgb = img.convert("RGB") if img.mode != "RGB" else img
        except Exception:
            img_rgb = img.convert("RGB")

        def _encode_jpeg(image: Image.Image, quality: int) -> bytes:
            buf = io.BytesIO()
            image.save(
                buf,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )
            return buf.getvalue()

        # 1) Пытаемся только quality (без ресайза)
        for quality in (85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35):
            candidate = _encode_jpeg(img_rgb, quality)
            if len(candidate) <= max_image_bytes:
                new_filename = os.path.splitext(filename)[0] + ".jpg"
                logger.info(
                    "Сжали изображение для Focus API (quality-only): %s -> %s bytes (q=%s, %s -> %s, %.0fms)",
                    original_size,
                    len(candidate),
                    quality,
                    filename,
                    new_filename,
                    (time.perf_counter() - t0) * 1000,
                )
                return candidate, new_filename, "image/jpeg"

        # 2) Если не помогло — постепенно уменьшаем размер и снова крутим quality
        w, h = img_rgb.size
        # ограничиваем минимальный размер, чтобы не улететь в ноль при странных входных данных
        min_side_limit = 320

        for scale in (0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.35, 0.3):
            new_w = max(int(w * scale), min_side_limit)
            new_h = max(int(h * scale), min_side_limit)
            if new_w == w and new_h == h:
                continue

            resized = img_rgb.resize((new_w, new_h), Image.Resampling.LANCZOS)
            for quality in (80, 75, 70, 65, 60, 55, 50, 45, 40, 35):
                candidate = _encode_jpeg(resized, quality)
                if len(candidate) <= max_image_bytes:
                    new_filename = os.path.splitext(filename)[0] + ".jpg"
                    logger.info(
                        "Сжали изображение для Focus API (resize+quality): %s -> %s bytes (scale=%.2f, q=%s, %s -> %s, %.0fms)",
                        original_size,
                        len(candidate),
                        scale,
                        quality,
                        filename,
                        new_filename,
                        (time.perf_counter() - t0) * 1000,
                    )
                    return candidate, new_filename, "image/jpeg"

        raise HTTPException(
            status_code=413,
            detail=(
                f"Изображение слишком большое для Focus API: {original_size} bytes. "
                f"Не удалось сжать до <= {max_image_bytes} bytes."
            ),
        )
    
    async def download_image_from_gcs(
        self,
        image_name: str,
        trace_id: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        """
        Загружает изображение из GCS по имени файла
        
        Args:
            image_name: Имя файла в GCS bucket
            
        Returns:
            tuple[bytes, str]: (байты изображения, MIME тип)
            
        Raises:
            HTTPException: При ошибке загрузки из GCS
        """
        t0 = time.perf_counter()
        try:
            image_bytes, mime_type = await download_file_from_gcs(image_name)
            logger.info(
                "Focus API: downloaded image from GCS (trace=%s, name=%s, bytes=%s, mime=%s, %.0fms)",
                trace_id,
                image_name,
                len(image_bytes),
                mime_type,
                (time.perf_counter() - t0) * 1000,
            )
            return image_bytes, mime_type
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=404,
                detail=str(e)
            )
        except Exception as e:
            error_msg = f"Ошибка при загрузке изображения {image_name} из GCS: {str(e)}"
            logger.error(
                "Focus API: GCS download failed (trace=%s, name=%s, %.0fms): %s",
                trace_id,
                image_name,
                (time.perf_counter() - t0) * 1000,
                error_msg,
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=error_msg)
    
    async def process_image(
        self,
        image_bytes: bytes,
        filename: str,
        mime_type: Optional[str] = None,
        trace_id: Optional[str] = None,
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
        t_total = time.perf_counter()
        logger.info(
            "Focus API: process_image start (trace=%s, filename=%s, bytes=%s, mime=%s)",
            trace_id,
            filename,
            len(image_bytes),
            mime_type,
        )

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

        # Focus API имеет лимит по размеру изображений (6 МБ) — ужимаем сами, чтобы не падать на стороне API.
        before_bytes = len(image_bytes)
        image_bytes, filename, mime_type = self._maybe_shrink_image_for_focus_api(
            image_bytes=image_bytes,
            filename=filename,
            mime_type=mime_type,
        )
        after_bytes = len(image_bytes)
        if after_bytes != before_bytes:
            logger.info(
                "Focus API: image shrunk (trace=%s, bytes=%s -> %s, filename=%s, mime=%s)",
                trace_id,
                before_bytes,
                after_bytes,
                filename,
                mime_type,
            )
        
        try:
            t_payload = time.perf_counter()
            payload = self._prepare_image_payload(image_bytes, filename, mime_type)
            logger.info(
                "Focus API: payload prepared (trace=%s, payload_chars=%s, %.0fms)",
                trace_id,
                len(payload),
                (time.perf_counter() - t_payload) * 1000,
            )
            
            headers = self._prepare_headers(payload)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                t_http = time.perf_counter()
                response = await client.post(
                    self.api_url,
                    content=payload,
                    headers=headers
                )
                http_ms = (time.perf_counter() - t_http) * 1000
                
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "").lower()
                logger.info(
                    "Focus API: response received (trace=%s, status=%s, content_type=%s, bytes=%s, %.0fms)",
                    trace_id,
                    response.status_code,
                    content_type,
                    len(response.content),
                    http_ms,
                )
                
                if "application/zip" in content_type or "application/x-zip-compressed" in content_type:
                    zip_bytes = response.content
                    result = await self._process_zip_response(zip_bytes, filename, trace_id=trace_id)
                    logger.info(
                        "Focus API: process_image done (trace=%s, total=%.0fms, zip=true)",
                        trace_id,
                        (time.perf_counter() - t_total) * 1000,
                    )
                    return result
                
                try:
                    result = response.json()
                    logger.info(
                        "Focus API: process_image done (trace=%s, total=%.0fms, zip=false)",
                        trace_id,
                        (time.perf_counter() - t_total) * 1000,
                    )
                    return result
                except json.JSONDecodeError:
                    logger.warning(f"Ответ от Focus API не является JSON для файла {filename}")
                    logger.info(
                        "Focus API: process_image done (trace=%s, total=%.0fms, zip=false, json=false)",
                        trace_id,
                        (time.perf_counter() - t_total) * 1000,
                    )
                    return {"response": response.text}
                    
        except httpx.HTTPStatusError as e:
            error_msg = f"Ошибка HTTP при запросе к Focus API: {e.response.status_code}"
            if e.response.text:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {e.response.text}"
            logger.error(
                "Focus API: HTTP error (trace=%s, %.0fms): %s",
                trace_id,
                (time.perf_counter() - t_total) * 1000,
                error_msg,
            )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=error_msg
            )
        except httpx.TimeoutException:
            error_msg = f"Таймаут при запросе к Focus API (>{self.timeout}с)"
            logger.error(
                "Focus API: timeout (trace=%s, %.0fms): %s",
                trace_id,
                (time.perf_counter() - t_total) * 1000,
                error_msg,
            )
            raise HTTPException(status_code=504, detail=error_msg)
        except Exception as e:
            error_msg = f"Неожиданная ошибка при запросе к Focus API: {str(e)}"
            logger.error(
                "Focus API: unexpected error (trace=%s, %.0fms): %s",
                trace_id,
                (time.perf_counter() - t_total) * 1000,
                error_msg,
                exc_info=True,
            )
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
        trace_id = uuid.uuid4().hex[:12]
        t_total = time.perf_counter()
        logger.info(
            "Focus API: process_image_by_name start (trace=%s, name=%s, requested_mime=%s)",
            trace_id,
            image_name,
            mime_type,
        )

        image_bytes, detected_mime_type = await self.download_image_from_gcs(
            image_name,
            trace_id=trace_id,
        )
        
        final_mime_type = mime_type or detected_mime_type
        
        result = await self.process_image(
            image_bytes,
            image_name,
            final_mime_type,
            trace_id=trace_id,
        )

        logger.info(
            "Focus API: process_image_by_name done (trace=%s, name=%s, total=%.0fms)",
            trace_id,
            image_name,
            (time.perf_counter() - t_total) * 1000,
        )
        return result
    
    async def _process_zip_response(
        self,
        zip_bytes: bytes,
        original_filename: str,
        trace_id: Optional[str] = None,
    ) -> Dict:
        """
        Обрабатывает ZIP архив от Focus API: распаковывает, загружает PNG и DXF в GCS
        
        Args:
            zip_bytes: Байты ZIP архива
            original_filename: Имя исходного файла (для создания уникальных имен)
            
        Returns:
            dict: Словарь с подписанными ссылками на PNG и DXF файлы
        """
        temp_dir = None
        t_total = time.perf_counter()
        try:
            logger.info(
                "Focus API: ZIP processing start (trace=%s, zip_bytes=%s, original=%s)",
                trace_id,
                len(zip_bytes),
                original_filename,
            )
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "response.zip")
            
            with open(zip_path, "wb") as f:
                f.write(zip_bytes)
            
            image_files = []  # PNG, JPG, JPEG файлы
            dxf_files = []
            
            t_extract = time.perf_counter()
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
            logger.info(
                "Focus API: ZIP extracted (trace=%s, images=%s, dxf=%s, %.0fms)",
                trace_id,
                len(image_files),
                len(dxf_files),
                (time.perf_counter() - t_extract) * 1000,
            )
            
            if not image_files and not dxf_files:
                raise HTTPException(
                    status_code=500,
                    detail="В ZIP архиве не найдено изображений (PNG/JPG) или DXF файлов"
                )
            
            image_urls = []
            t_upload_images = time.perf_counter()
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
            if image_files:
                logger.info(
                    "Focus API: ZIP images uploaded (trace=%s, count=%s, %.0fms)",
                    trace_id,
                    len(image_files),
                    (time.perf_counter() - t_upload_images) * 1000,
                )
            
            dxf_urls = []
            t_upload_dxf = time.perf_counter()
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
            if dxf_files:
                logger.info(
                    "Focus API: ZIP dxf uploaded (trace=%s, count=%s, %.0fms)",
                    trace_id,
                    len(dxf_files),
                    (time.perf_counter() - t_upload_dxf) * 1000,
                )

            logger.info(
                "Focus API: ZIP processing done (trace=%s, total=%.0fms)",
                trace_id,
                (time.perf_counter() - t_total) * 1000,
            )
            
            return {
                "image_files": image_urls,
                "dxf_files": dxf_urls,
                "original_filename": original_filename
            }
            
        except zipfile.BadZipFile:
            error_msg = "Полученный файл не является валидным ZIP архивом"
            logger.error(
                "Focus API: ZIP bad file (trace=%s, %.0fms): %s",
                trace_id,
                (time.perf_counter() - t_total) * 1000,
                error_msg,
            )
            raise HTTPException(status_code=500, detail=error_msg)
        except Exception as e:
            error_msg = f"Ошибка при обработке ZIP архива: {str(e)}"
            logger.error(
                "Focus API: ZIP processing failed (trace=%s, %.0fms): %s",
                trace_id,
                (time.perf_counter() - t_total) * 1000,
                error_msg,
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=error_msg)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:   
                    shutil.rmtree(temp_dir, ignore_errors=True)
