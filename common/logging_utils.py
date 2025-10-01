import logging
import sys
from typing import Optional, Dict, Any
from contextvars import ContextVar

# Контекстные переменные для хранения информации о пользователе
user_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('user_context', default=None)

class UserAwareFormatter(logging.Formatter):
    """
    Форматтер логов, который включает информацию о пользователе
    """
    
    def format(self, record):
        # Получаем контекст пользователя
        user_info = user_context.get()
        
        if user_info:
            record.user_id = user_info.get('user_id', 'unknown')
            record.user_email = user_info.get('user_email', 'unknown')
            record.user_name = user_info.get('user_name', 'unknown')
        else:
            record.user_id = 'anonymous'
            record.user_email = 'anonymous'
            record.user_name = 'anonymous'
        
        return super().format(record)

def setup_user_logging():
    """
    Настраивает логирование с поддержкой информации о пользователе
    """
    # Создаем логгер для API запросов
    api_logger = logging.getLogger("api_requests")
    api_logger.setLevel(logging.INFO)
    
    # Удаляем существующие обработчики
    for handler in api_logger.handlers[:]:
        api_logger.removeHandler(handler)
    
    # Создаем обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Настраиваем форматтер
    formatter = UserAwareFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(user_id)s:%(user_email)s:%(user_name)s] - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    api_logger.addHandler(console_handler)
    api_logger.propagate = False
    
    return api_logger

def set_user_context(user_id: Optional[str] = None, 
                    user_email: Optional[str] = None, 
                    user_name: Optional[str] = None):
    """
    Устанавливает контекст пользователя для логирования
    """
    context = {
        'user_id': user_id or 'anonymous',
        'user_email': user_email or 'anonymous', 
        'user_name': user_name or 'anonymous'
    }
    user_context.set(context)

def clear_user_context():
    """
    Очищает контекст пользователя
    """
    user_context.set(None)

def get_user_logger(name: str) -> logging.Logger:
    """
    Получает логгер с поддержкой информации о пользователе
    """
    logger = logging.getLogger(name)
    
    # Если у логгера еще нет обработчиков, добавляем их
    if not logger.handlers:
        # Создаем обработчик для консоли
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Настраиваем форматтер
        formatter = UserAwareFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(user_id)s:%(user_email)s:%(user_name)s] - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    
    return logger

# Создаем глобальные логгеры
api_logger = setup_user_logging()
bot_logger = get_user_logger("telegram_bot")
