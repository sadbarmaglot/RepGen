import logging
import time
import jwt

from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from settings import JWT_SECRET_KEY, JWT_ALGORITHM

logger = logging.getLogger(__name__)

class UserLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware для логирования HTTP запросов с информацией о пользователе
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("api_requests")
        
        # Очищаем существующие обработчики чтобы избежать дублирования
        self.logger.handlers.clear()
        
        # Настройка форматирования логов
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(user_email)s] - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
    
    def _extract_user_from_token(self, token: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Извлекает информацию о пользователе из JWT токена
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_email = payload.get("sub", "")  # В нашем случае sub содержит email
            user_id = user_email  # Используем email как ID для отображения
            user_name = user_email.split("@")[0] if "@" in user_email else user_email  # Извлекаем имя из email
            return user_id, user_email, user_name
        except jwt.ExpiredSignatureError:
            return "expired_token", "expired_token", "expired_token"
        except jwt.InvalidTokenError:
            return "invalid_token", "invalid_token", "invalid_token"
        except Exception:
            return None, None, None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Пропускаем логирование для health endpoint
        if request.url.path == "/health" or request.url.path == "/repgen/health":
            response = await call_next(request)
            return response
        
        # Извлекаем информацию о пользователе из заголовков или токена
        user_email = "anonymous"
        
        # Пытаемся получить информацию о пользователе из Authorization заголовка
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            _, extracted_email, _ = self._extract_user_from_token(token)
            if extracted_email:
                user_email = extracted_email
        
        # Логируем начало запроса
        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={"user_email": user_email}
        )
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Вычисляем время выполнения
        process_time = time.time() - start_time
        
        # Логируем завершение запроса
        self.logger.info(
            f"Request completed: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.3f}s",
            extra={"user_email": user_email}
        )
        
        return response
