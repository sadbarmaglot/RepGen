import uuid
import asyncio
import io
import mimetypes

from google.cloud import storage
from PIL import Image
from typing import Tuple, List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from api.services.redis_service import redis_service
from settings import PROJECT_ID, BUCKET_NAME

storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

async def create_signed_url(
    blob_name: str, 
    expiration_minutes: int = 60,
    content_type: Optional[str] = None
) -> str:
    """
    Создает подписной URL для файла в GCP бакете
    
    Args:
        blob_name: Имя файла в бакете
        expiration_minutes: Время жизни URL в минутах (по умолчанию 60 минут)
        content_type: MIME тип файла (опционально, по умолчанию "image/*")
        
    Returns:
        str: Подписной URL для доступа к файлу
    """    
    blob = bucket.blob(blob_name)
    
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)
    
    # Определяем response_type на основе content_type
    if content_type:
        if content_type.startswith("image/"):
            response_type = "image/*"
        elif content_type == "application/dxf":
            response_type = "application/dxf"
        else:
            response_type = content_type
    else:
        # По умолчанию для обратной совместимости
        response_type = "image/*"
    
    try:
        signed_url = await asyncio.to_thread(
            blob.generate_signed_url,
            version="v4",
            expiration=expiration_time,
            method="GET",
            response_type=response_type
        )
        return signed_url
    except Exception as e:
        # Файл не существует или другая ошибка
        raise FileNotFoundError(f"Не удалось создать signed URL для {blob_name}: {e}")

async def upload_to_gcs_with_blob(file_path, suffix):
    """
    Асинхронная загрузка файла в Google Cloud Storage
    
    Args:
        file_path: Путь к файлу для загрузки
        suffix: Расширение файла (без точки)
        
    Returns:
        Blob: blob объект
    """
    filename = f"{uuid.uuid4()}.{suffix}"
    blob = bucket.blob(filename)
    
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "image/jpeg"

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, blob.upload_from_filename, file_path, mime_type)
    
    return blob

async def upload_to_gcs(file_path, suffix):
    """
    Асинхронная загрузка файла в Google Cloud Storage
    
    Args:
        file_path: Путь к файлу для загрузки
        suffix: Расширение файла (без точки)
        
    Returns:
        Tuple[Blob, str]: (blob объект, публичный URL)
    """
    filename = f"{uuid.uuid4()}.{suffix}"
    blob = bucket.blob(filename)
    
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "image/jpeg"

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, blob.upload_from_filename, file_path, mime_type)
    
    return blob, blob.public_url

async def download_file_from_gcs(blob_name: str) -> Tuple[bytes, str]:
    """
    Загружает файл из GCS по имени файла
    
    Args:
        blob_name: Имя файла в GCS bucket
        
    Returns:
        Tuple[bytes, str]: (байты файла, MIME тип)
        
    Raises:
        FileNotFoundError: Если файл не найден в GCS
    """
    blob = bucket.blob(blob_name)
    
    # Проверяем существование файла
    if not await asyncio.to_thread(blob.exists):
        raise FileNotFoundError(f"Файл {blob_name} не найден в GCS bucket")
    
    # Загружаем содержимое файла
    file_bytes = await asyncio.to_thread(blob.download_as_bytes)
    
    # Определяем MIME тип из метаданных
    mime_type = blob.content_type or "application/octet-stream"
    
    return file_bytes, mime_type

async def upload_file_to_gcs_with_signed_url(
    file_path: str,
    extension: str,
    prefix: str = "upload",
    content_type: Optional[str] = None,
    expiration_minutes: int = 60
) -> Tuple[str, str]:
    """
    Загружает файл в GCS с указанным префиксом и создает подписанный URL
    
    Args:
        file_path: Путь к файлу на диске
        extension: Расширение файла (без точки)
        prefix: Префикс для имени файла
        content_type: MIME тип файла (опционально, определяется автоматически)
        expiration_minutes: Время жизни подписанного URL в минутах
        
    Returns:
        Tuple[str, str]: (имя файла в GCS, подписанный URL)
    """
    # Генерируем уникальное имя файла
    filename = f"{prefix}_{uuid.uuid4()}.{extension}"
    blob = bucket.blob(filename)
    
    # Определяем MIME тип
    if not content_type:
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            # Определяем по расширению
            if extension.lower() == "png":
                content_type = "image/png"
            elif extension.lower() == "dxf":
                content_type = "application/dxf"
            elif extension.lower() in ["jpg", "jpeg"]:
                content_type = "image/jpeg"
            else:
                content_type = "application/octet-stream"
    
    # Устанавливаем content type
    blob.content_type = content_type
    
    # Загружаем файл в GCS
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, blob.upload_from_filename, file_path)
    
    # Создаем подписанный URL
    signed_url = await create_signed_url(filename, expiration_minutes, content_type)
    
    return filename, signed_url

async def upload_pil_image_to_gcs(image: Image.Image, filename_prefix: str = "model_comparison") -> Tuple[str, str]:
    """
    Асинхронная загрузка PIL изображения в Google Cloud Storage
    
    Args:
        image: PIL Image объект
        filename_prefix: Префикс для имени файла
        
    Returns:
        Tuple[str, str]: (имя файла, публичный URL)
    """
    # Генерируем уникальное имя файла
    filename = f"{filename_prefix}_{uuid.uuid4()}.jpg"
    blob = bucket.blob(filename)
    
    # Конвертируем PIL изображение в байты
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=95)
    img_byte_arr.seek(0)
    
    # Выполняем загрузку в отдельном потоке для избежания блокировки
    loop = asyncio.get_event_loop()
    
    # Создаем функцию-обертку для передачи именованных аргументов
    def upload_file():
        blob.upload_from_file(img_byte_arr, content_type='image/jpeg')
    
    await loop.run_in_executor(None, upload_file)
    
    return filename, blob.public_url

async def upload_pil_image_to_gcs_with_signed_url(
    image: Image.Image, 
    filename_prefix: str = "gemini_analysis",
    expiration_minutes: int = 60
) -> Tuple[str, str, str]:
    """
    Асинхронная загрузка PIL изображения в Google Cloud Storage с созданием подписного URL для Gemini Pro
    
    Args:
        image: PIL Image объект
        filename_prefix: Префикс для имени файла
        expiration_minutes: Время жизни подписного URL в минутах
        
    Returns:
        Tuple[str, str, str]: (имя файла, публичный URL, подписной URL для Gemini Pro)
    """
    # Генерируем уникальное имя файла
    filename = f"{filename_prefix}_{uuid.uuid4()}.jpg"
    blob = bucket.blob(filename)
    
    # Конвертируем PIL изображение в байты
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=95)
    img_byte_arr.seek(0)
    
    # Выполняем загрузку в отдельном потоке для избежания блокировки
    loop = asyncio.get_event_loop()
    
    # Создаем функцию-обертку для передачи именованных аргументов
    def upload_file():
        blob.upload_from_file(img_byte_arr, content_type='image/jpeg')
    
    await loop.run_in_executor(None, upload_file)
    
    # Создаем подписной URL для Gemini Pro
    signed_url = await create_signed_url(filename, expiration_minutes)
    
    return filename, blob.public_url, signed_url

async def list_model_comparison_images(prefix: str = "model_comparison", max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Получает список изображений для сравнения моделей из GCP bucket
    
    Args:
        prefix: Префикс для фильтрации файлов
        max_results: Максимальное количество результатов
        
    Returns:
        List[Dict[str, Any]]: Список информации об изображениях
    """
    blobs = bucket.list_blobs(prefix=prefix, max_results=max_results)
    
    images_info = []
    for blob in blobs:
        # Получаем метаданные blob
        blob.reload()
        
        image_info = {
            "filename": blob.name,
            "public_url": blob.public_url,
            "size_bytes": blob.size,
            "created": blob.time_created.isoformat() if blob.time_created else None,
            "updated": blob.updated.isoformat() if blob.updated else None,
            "content_type": blob.content_type
        }
        images_info.append(image_info)
    
    # Сортируем по дате создания (новые сначала)
    images_info.sort(key=lambda x: x["created"] or "", reverse=True)
    
    return images_info

async def delete_blob_by_name(blob_name: str) -> bool:
    """
    Удаляет файл из GCP bucket по названию и очищает кеш подписанного URL
    
    Args:
        blob_name: Имя файла для удаления
        
    Returns:
        bool: True если удаление прошло успешно, False в противном случае
    """
    try:
        blob = bucket.blob(blob_name)
        
        # Проверяем, что файл существует
        if not blob.exists():
            print(f"Файл {blob_name} не найден в бакете")
            return False
        
        blob.delete()
        
        try:
            await redis_service.clear_signed_url(blob_name)
        except Exception as cache_error:
            print(f"Ошибка при очистке кеша для {blob_name}: {cache_error}")
        
        print(f"Файл {blob_name} успешно удален из бакета")
        return True
    except Exception as e:
        print(f"Ошибка при удалении файла {blob_name}: {e}")
        return False

async def delete_model_comparison_image(filename: str) -> bool:
    """
    Удаляет изображение для сравнения моделей из GCP bucket и очищает кеш
    
    Args:
        filename: Имя файла для удаления
        
    Returns:
        bool: True если удаление прошло успешно, False в противном случае
    """
    try:
        blob = bucket.blob(filename)
        blob.delete()
        
        try:
            await redis_service.clear_signed_url(filename)
        except Exception as cache_error:
            print(f"Ошибка при очистке кеша для {filename}: {cache_error}")
        
        return True
    except Exception as e:
        print(f"Ошибка при удалении файла {filename}: {e}")
        return False

async def save_comparison_results_to_gcs(
    results_data: dict, 
    image_filename: str, 
    models_used: List[str],
    settings: dict
) -> Tuple[str, str]:
    """
    Сохраняет результаты сравнения моделей в GCP bucket в формате JSON
    
    Args:
        results_data: Словарь с результатами анализа по моделям
        image_filename: Имя сохраненного изображения
        models_used: Список использованных моделей
        settings: Настройки анализа (temperature, max_tokens)
        
    Returns:
        Tuple[str, str]: (имя файла результатов, публичный URL)
    """
    import json
    from datetime import datetime
    
    # Создаем структуру данных для сохранения
    comparison_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "image_filename": image_filename,
            "models_analyzed": models_used,
            "analysis_settings": settings,
            "total_models": len(models_used),
            "successful_analyses": len([r for r in results_data if isinstance(r, dict) and r.get("status") == "success"]),
            "failed_analyses": len([r for r in results_data if isinstance(r, Exception) or (isinstance(r, dict) and r.get("status") == "error")])
        },
        "results": results_data,
        "summary": {
            "best_model": None,
            "most_detailed_description": None,
            "most_specific_recommendations": None
        }
    }
    
    # Анализируем результаты для создания сводки
    successful_results = [r for r in results_data if isinstance(r, dict) and r.get("status") == "success"]
    
    if successful_results:
        # Находим модель с самым длинным описанием (предполагаем, что это более детальное)
        most_detailed = max(successful_results, key=lambda x: len(x.get("description", "")))
        comparison_data["summary"]["most_detailed_description"] = most_detailed["model"]
        
        # Находим модель с самыми конкретными рекомендациями
        most_specific = max(successful_results, key=lambda x: len(x.get("recommendation", "")))
        comparison_data["summary"]["most_specific_recommendations"] = most_specific["model"]
    
    # Генерируем имя файла для результатов
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_filename = f"comparison_results_{timestamp}_{uuid.uuid4()}.json"
    
    # Создаем blob и загружаем JSON
    blob = bucket.blob(results_filename)
    
    # Конвертируем в JSON строку
    json_data = json.dumps(comparison_data, ensure_ascii=False, indent=2)
    
    # Выполняем загрузку в отдельном потоке
    loop = asyncio.get_event_loop()
    
    def upload_json():
        blob.upload_from_string(json_data, content_type='application/json')
    
    await loop.run_in_executor(None, upload_json)
    
    return results_filename, blob.public_url

async def list_comparison_results(prefix: str = "comparison_results", max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Получает список файлов с результатами сравнения из GCP bucket
    
    Args:
        prefix: Префикс для фильтрации файлов
        max_results: Максимальное количество результатов
        
    Returns:
        List[Dict[str, Any]]: Список информации о файлах результатов
    """
    blobs = bucket.list_blobs(prefix=prefix, max_results=max_results)
    
    results_info = []
    for blob in blobs:
        # Получаем метаданные blob
        blob.reload()
        
        result_info = {
            "filename": blob.name,
            "public_url": blob.public_url,
            "size_bytes": blob.size,
            "created": blob.time_created.isoformat() if blob.time_created else None,
            "updated": blob.updated.isoformat() if blob.updated else None,
            "content_type": blob.content_type
        }
        results_info.append(result_info)
    
    # Сортируем по дате создания (новые сначала)
    results_info.sort(key=lambda x: x["created"] or "", reverse=True)
    
    return results_info

async def get_comparison_result_content(filename: str) -> Dict[str, Any]:
    """
    Получает содержимое файла с результатами сравнения
    
    Args:
        filename: Имя файла с результатами
        
    Returns:
        Dict[str, Any]: Содержимое JSON файла
    """
    import json
    
    try:
        blob = bucket.blob(filename)
        content = blob.download_as_text()
        return json.loads(content)
    except Exception as e:
        print(f"Ошибка при чтении файла {filename}: {e}")
        return {}
