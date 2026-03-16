import uuid
import asyncio
import logging
import mimetypes
from typing import Tuple, Optional

from google.cloud import storage
from datetime import datetime, timedelta, timezone

from api.services.redis_service import redis_service
from settings import PROJECT_ID, BUCKET_NAME, DOCUMENTS_BUCKET_NAME

logger = logging.getLogger(__name__)

storage_client = storage.Client(project=PROJECT_ID)


class GCSClient:
    """Клиент для работы с Google Cloud Storage бакетом."""

    def __init__(self, bucket_name: str):
        self._bucket = storage_client.bucket(bucket_name)

    async def create_signed_url(
        self,
        blob_name: str,
        expiration_minutes: int = 60,
        content_type: Optional[str] = None,
    ) -> str:
        blob = self._bucket.blob(blob_name)
        expiration_time = datetime.now(timezone.utc) + timedelta(
            minutes=expiration_minutes
        )

        if content_type:
            if content_type.startswith("image/"):
                response_type = "image/*"
            else:
                response_type = content_type
        else:
            response_type = "image/*"

        try:
            return await asyncio.to_thread(
                blob.generate_signed_url,
                version="v4",
                expiration=expiration_time,
                method="GET",
                response_type=response_type,
            )
        except Exception as e:
            raise FileNotFoundError(
                f"Не удалось создать signed URL для {blob_name}: {e}"
            )

    async def upload_from_file_blob_only(
        self,
        file_path: str,
        suffix: str,
        content_type: Optional[str] = None,
    ):
        """Загрузка файла, возвращает blob."""
        filename = f"{uuid.uuid4()}.{suffix}"
        blob = self._bucket.blob(filename)

        if not content_type:
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = "image/jpeg"

        blob.content_type = content_type
        await asyncio.to_thread(blob.upload_from_filename, file_path, content_type)
        return blob

    async def upload_from_file_with_signed_url(
        self,
        file_path: str,
        extension: str,
        prefix: str = "upload",
        content_type: Optional[str] = None,
        expiration_minutes: int = 60,
    ) -> Tuple[str, str]:
        """Загрузка файла с префиксом, возвращает (blob_name, signed_url)."""
        filename = f"{prefix}_{uuid.uuid4()}.{extension}"
        blob = self._bucket.blob(filename)

        if not content_type:
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = "application/octet-stream"

        blob.content_type = content_type
        await asyncio.to_thread(blob.upload_from_filename, file_path)
        signed_url = await self.create_signed_url(
            filename, expiration_minutes, content_type
        )
        return filename, signed_url

    async def upload_bytes(
        self,
        data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Загрузка байтов, возвращает blob_name."""
        blob = self._bucket.blob(filename)
        blob.content_type = content_type

        def _upload():
            blob.upload_from_string(data, content_type=content_type)

        await asyncio.to_thread(_upload)
        return filename

    async def download(self, blob_name: str) -> Tuple[bytes, str]:
        """Скачивание файла, возвращает (bytes, mime_type)."""
        blob = self._bucket.blob(blob_name)

        if not await asyncio.to_thread(blob.exists):
            raise FileNotFoundError(
                f"Файл {blob_name} не найден в GCS bucket"
            )

        file_bytes = await asyncio.to_thread(blob.download_as_bytes)
        mime_type = blob.content_type or "application/octet-stream"
        return file_bytes, mime_type

    async def delete(self, blob_name: str) -> bool:
        """Удаление файла и очистка кэша signed URL."""
        try:
            blob = self._bucket.blob(blob_name)

            if not await asyncio.to_thread(blob.exists):
                logger.warning("Файл %s не найден в бакете", blob_name)
                return False

            await asyncio.to_thread(blob.delete)

            try:
                await redis_service.clear_signed_url(blob_name)
            except Exception:
                logger.warning(
                    "Ошибка при очистке кеша для %s", blob_name, exc_info=True
                )

            logger.info("Файл %s удален из бакета", blob_name)
            return True
        except Exception:
            logger.error(
                "Ошибка при удалении файла %s", blob_name, exc_info=True
            )
            return False

    async def get_blob_size(self, blob_name: str) -> Optional[int]:
        """Размер файла (bytes) без скачивания, или None."""
        blob = self._bucket.blob(blob_name)
        try:
            await asyncio.to_thread(blob.reload)
            return blob.size
        except Exception:
            return None


# ── Инстансы для бакетов ──────────────────────────────────────────

images_storage = GCSClient(BUCKET_NAME)
documents_storage = GCSClient(DOCUMENTS_BUCKET_NAME)


