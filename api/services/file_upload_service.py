import io
import os
import sys
import tempfile
import logging
from typing import List, Tuple
from fastapi import UploadFile, HTTPException
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from common.gc_utils import images_storage

logger = logging.getLogger(__name__)

register_heif_opener()

class FileUploadService:
    """Сервис для загрузки файлов в GCP Cloud Storage"""

    _HEIC_EXTENSIONS = {'.heic', '.heif'}

    def __init__(self):
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.heif'}
        self.max_file_size = 20 * 1024 * 1024  # 20MB

    def _convert_heic_to_jpeg(self, content: bytes, filename: str) -> Tuple[bytes, str]:
        """Конвертирует HEIC/HEIF байты в JPEG. Возвращает (jpeg_bytes, '.jpg')."""
        import time as _time

        original_size = len(content)
        t0 = _time.perf_counter()

        img = Image.open(io.BytesIO(content))
        img = ImageOps.exif_transpose(img)
        img.load()
        t_decode = _time.perf_counter()

        if img.mode in ("RGBA", "LA") or "transparency" in getattr(img, "info", {}):
            rgba = img.convert("RGBA")
            bg = Image.new("RGB", rgba.size, (255, 255, 255))
            bg.paste(rgba, mask=rgba.split()[-1])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        result = buf.getvalue()
        t_encode = _time.perf_counter()

        logger.info(
            "HEIC→JPEG: %s (%s -> %s bytes, decode=%.0fms, encode=%.0fms, total=%.0fms)",
            filename,
            original_size,
            len(result),
            (t_decode - t0) * 1000,
            (t_encode - t_decode) * 1000,
            (t_encode - t0) * 1000,
        )
        return result, ".jpg"

    def _maybe_compress(
        self,
        content: bytes,
        filename: str,
        file_extension: str,
        *,
        max_bytes: int = 6_000_000,
    ) -> Tuple[bytes, str]:
        """Сжимает изображение если > max_bytes. Возвращает (bytes, extension)."""
        if len(content) <= max_bytes:
            return content, file_extension

        original_size = len(content)
        img = Image.open(io.BytesIO(content))
        img = ImageOps.exif_transpose(img)
        img.load()

        if img.mode in ("RGBA", "LA") or "transparency" in getattr(img, "info", {}):
            rgba = img.convert("RGBA")
            bg = Image.new("RGB", rgba.size, (255, 255, 255))
            bg.paste(rgba, mask=rgba.split()[-1])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        def _encode(image: Image.Image, quality: int) -> bytes:
            buf = io.BytesIO()
            image.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
            return buf.getvalue()

        # 1) Только quality
        for q in (85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35):
            candidate = _encode(img, q)
            if len(candidate) <= max_bytes:
                logger.info(
                    "Compressed %s: %s -> %s bytes (q=%s)", filename, original_size, len(candidate), q
                )
                return candidate, ".jpg"

        # 2) Resize + quality
        w, h = img.size
        for scale in (0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.35, 0.3):
            new_w, new_h = max(int(w * scale), 320), max(int(h * scale), 320)
            if new_w == w and new_h == h:
                continue
            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            for q in (80, 70, 60, 50, 40, 35):
                candidate = _encode(resized, q)
                if len(candidate) <= max_bytes:
                    logger.info(
                        "Compressed %s: %s -> %s bytes (scale=%.2f, q=%s)",
                        filename, original_size, len(candidate), scale, q,
                    )
                    return candidate, ".jpg"

        logger.warning("Could not compress %s below %s bytes", filename, max_bytes)
        return content, file_extension

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
        import time as _time

        try:
            t0 = _time.perf_counter()
            file_extension = os.path.splitext(file.filename)[1].lower()

            if file.size and file.size > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"Файл слишком большой. Максимальный размер: {self.max_file_size // (1024*1024)}MB"
                )

            content = await file.read()
            t_read = _time.perf_counter()

            if file_extension in self._HEIC_EXTENSIONS:
                content, file_extension = self._convert_heic_to_jpeg(content, file.filename)

            content, file_extension = self._maybe_compress(content, file.filename, file_extension)
            t_process = _time.perf_counter()

            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(content)
                temp_file.flush()

                try:
                    blob = await images_storage.upload_from_file_blob_only(temp_file.name, file_extension[1:])
                    t_upload = _time.perf_counter()

                    logger.info(
                        "Upload %s -> %s (read=%.0fms, process=%.0fms, gcs=%.0fms, total=%.0fms)",
                        file.filename,
                        blob.name,
                        (t_read - t0) * 1000,
                        (t_process - t_read) * 1000,
                        (t_upload - t_process) * 1000,
                        (t_upload - t0) * 1000,
                    )
                    return {"image_name": blob.name}
                finally:
                    os.unlink(temp_file.name)

        except Exception as e:
            logger.error(f"Ошибка при загрузке файла {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ошибка при загрузке файла: {str(e)}")

    async def upload_multiple_files_with_blob(
        self,
        files: List[UploadFile]
    ) -> List[dict]:
        """
        Загружает несколько файлов в GCP Cloud Storage

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
