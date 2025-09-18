import json
import uuid
import base64
import os
import logging
import tempfile
import subprocess
from pathlib import Path
from openai import OpenAI
from common.defects_db import SYSTEM_MESSAGE, PROMPT

# Настройка логирования для ИИ запросов
ai_logger = logging.getLogger('ai_requests')
ai_logger.setLevel(logging.INFO)

# Создаем обработчик для файла логов если еще не создан
if not ai_logger.handlers:
    log_handler = logging.FileHandler('ai_requests.log', encoding='utf-8')
    log_handler.setLevel(logging.INFO)
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(log_formatter)
    ai_logger.addHandler(log_handler)
    
    # Также выводим в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter)
    ai_logger.addHandler(console_handler)

# Ленивая инициализация клиента OpenAI
_client = None

def get_openai_client():
    """Получение клиента OpenAI с ленивой инициализацией"""
    global _client
    if _client is None:
        # Проверяем API ключ в переменных окружения
        api_key = os.environ.get('OPENAI_API_KEY')
        
        # Если нет, пытаемся загрузить из .env файла
        if not api_key:
            try:
                from dotenv import load_dotenv
                # Ищем .env файл в корневой папке проекта
                root_dir = Path(__file__).parent.parent
                env_file = root_dir / '.env'
                if env_file.exists():
                    load_dotenv(env_file)
                    api_key = os.environ.get('OPENAI_API_KEY')
            except ImportError:
                pass
        
        if not api_key:
            raise ValueError("OpenAI API ключ не найден. Установите переменную OPENAI_API_KEY или создайте .env файл.")
        
        _client = OpenAI(api_key=api_key)
    
    return _client

def convert_heic_to_jpeg(heic_path: str) -> str:
    """
    Конвертация HEIC файла в JPEG для совместимости с OpenAI API
    
    Args:
        heic_path: Путь к HEIC файлу
        
    Returns:
        str: Путь к временному JPEG файлу
    """
    # Создаем временный файл
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        # Пытаемся использовать pillow-heif (если установлен)
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
            
            from PIL import Image
            with Image.open(heic_path) as img:
                img.convert('RGB').save(temp_path, 'JPEG', quality=95)
                return temp_path
                
        except ImportError:
            # Если pillow-heif не установлен, пытаемся использовать ImageMagick
            try:
                result = subprocess.run(['magick', heic_path, temp_path], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    return temp_path
                else:
                    raise Exception(f"ImageMagick error: {result.stderr}")
                    
            except FileNotFoundError:
                # Если ничего не работает, пробуем с помощью macOS sips
                if os.name == 'posix':  # macOS/Linux
                    try:
                        result = subprocess.run([
                            'sips', '-s', 'format', 'jpeg', heic_path, '--out', temp_path
                        ], capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            return temp_path
                        else:
                            raise Exception(f"sips error: {result.stderr}")
                    except FileNotFoundError:
                        pass
                
                raise Exception("Не удалось конвертировать HEIC файл. Установите pillow-heif: pip install pillow-heif")
                
    except Exception as e:
        # Очищаем временный файл в случае ошибки
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass
        raise Exception(f"Ошибка конвертации HEIC: {str(e)}")

def analyze_local_photo(photo_path: str) -> dict:
    """
    Анализ локального фото без Telegram API и GCS
    
    Args:
        photo_path: Путь к локальному файлу изображения
        
    Returns:
        dict: Результат анализа с описанием дефекта и рекомендациями
    """
    request_id = str(uuid.uuid4())[:8]
    
    ai_logger.info(f"[{request_id}] 🔄 Начинаю анализ фото: {photo_path}")
    
    # Проверяем существование файла
    if not Path(photo_path).exists():
        ai_logger.error(f"[{request_id}] ❌ Файл не найден: {photo_path}")
        raise FileNotFoundError(f"Файл не найден: {photo_path}")
    
    # Проверяем, является ли файл HEIC/HEIF
    file_extension = Path(photo_path).suffix.lower()
    temp_file_path = None
    
    try:
        if file_extension in ['.heic', '.heif']:
            ai_logger.info(f"[{request_id}] 🔄 Конвертирую HEIC файл в JPEG...")
            temp_file_path = convert_heic_to_jpeg(photo_path)
            photo_path_to_use = temp_file_path
            ai_logger.info(f"[{request_id}] ✅ HEIC файл успешно конвертирован")
        else:
            photo_path_to_use = photo_path
        
        # Конвертируем в base64 для OpenAI
        with open(photo_path_to_use, "rb") as image_file:
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
        image_size_kb = len(image_data) / 1024
        ai_logger.info(f"[{request_id}] 📸 Размер изображения: {image_size_kb:.1f} KB")
        
    except Exception as e:
        # Очищаем временный файл в случае ошибки
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass
        raise e
    
    try:
        ai_logger.info(f"[{request_id}] 🤖 Отправляю запрос к OpenAI GPT-4o...")
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                SYSTEM_MESSAGE,
                {"role": "user", "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }}
                ]}
            ],
            temperature=0.2,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )
        
        # Логируем успешный ответ
        tokens_used = response.usage.total_tokens if response.usage else 0
        ai_logger.info(f"[{request_id}] ✅ Получен ответ от OpenAI. Токенов использовано: {tokens_used}")
        ai_logger.info(f"[{request_id}] 📝 Модель: {response.model}, ID: {response.id}")
        
        result = json.loads(response.choices[0].message.content)
        
        # Логируем результат анализа
        defect_type = result.get("defect_description", "Неизвестно")
        ai_logger.info(f"[{request_id}] 🎯 Результат анализа: {defect_type[:50]}...")
        
        result_data = {
            "defect": result.get("defect_description", "Не удалось определить"),
            "eliminating_method": result.get("recommendation", "Рекомендации отсутствуют"),
            "image_path": photo_path,
            "file_path": photo_path,
            "filename": Path(photo_path).name,
            "analyzed": True,
            "status": "completed"
        }
        
        return result_data
        
    except Exception as e:
        ai_logger.error(f"[{request_id}] ❌ Ошибка при анализе: {str(e)}")
        ai_logger.error(f"[{request_id}] 📱 Тип ошибки: {type(e).__name__}")
        print(f"[ERROR] Ошибка при анализе фото: {e}")
        raise e
        
    finally:
        # Очищаем временный файл
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                ai_logger.info(f"[{request_id}] 🗑️ Временный файл удален: {temp_file_path}")
            except Exception as cleanup_error:
                ai_logger.warning(f"[{request_id}] ⚠️ Не удалось удалить временный файл: {cleanup_error}")

def batch_analyze_photos(photo_paths: list) -> list:
    """
    Анализ нескольких фото одновременно
    
    Args:
        photo_paths: Список путей к файлам изображений
        
    Returns:
        list: Список результатов анализа
    """
    batch_id = str(uuid.uuid4())[:8]
    results = []
    total = len(photo_paths)
    
    ai_logger.info(f"[BATCH-{batch_id}] 🚀 Начинаю пакетный анализ {total} фотографий")
    
    for i, photo_path in enumerate(photo_paths):
        try:
            ai_logger.info(f"[BATCH-{batch_id}] 📸 Фото {i+1}/{total}: {Path(photo_path).name}")
            result = analyze_local_photo(photo_path)
            results.append(result)
        except Exception as e:
            results.append({
                "defect": f"Ошибка анализа: {str(e)}",
                "eliminating_method": "Проверьте файл и попробуйте снова",
                "image_path": photo_path,
                "file_path": photo_path,
                "filename": Path(photo_path).name,
                "error": True,
                "analyzed": False,
                "status": "error"
            })
    
    return results