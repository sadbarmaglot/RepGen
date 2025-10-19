import json

import redis.asyncio as redis
from typing import Optional, Any
from settings import REDIS_HOST, REDIS_PORT


class RedisService:
    """Сервис для работы с Redis кэшем"""
    
    def __init__(self):
        """Инициализация Redis клиента"""
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=int(REDIS_PORT),
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
    
    async def get(self, key: str) -> Optional[str]:
        """Получение значения по ключу"""
        try:
            return await self.redis_client.get(key)
        except Exception:
            # Тихо обрабатываем ошибку - Redis недоступен, вернем None
            return None
    
    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        """Сохранение значения по ключу с опциональным TTL"""
        try:
            if ttl_seconds:
                await self.redis_client.setex(key, ttl_seconds, value)
            else:
                await self.redis_client.set(key, value)
            return True
        except Exception as e:
            print(f"Ошибка сохранения в Redis для ключа {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удаление значения по ключу"""
        try:
            result = await self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            print(f"Ошибка удаления из Redis для ключа {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        try:
            result = await self.redis_client.exists(key)
            return bool(result)
        except Exception as e:
            print(f"Ошибка проверки существования ключа {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl_seconds: int) -> bool:
        """Установка TTL для существующего ключа"""
        try:
            result = await self.redis_client.expire(key, ttl_seconds)
            return bool(result)
        except Exception as e:
            print(f"Ошибка установки TTL для ключа {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """Получение оставшегося TTL для ключа"""
        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            print(f"Ошибка получения TTL для ключа {key}: {e}")
            return -1
    
    # Методы для работы с JSON данными
    async def get_json(self, key: str) -> Optional[Any]:
        """Получение JSON данных по ключу"""
        try:
            value = await self.get(key)
            if value:
                return json.loads(value)
            return None
        except (json.JSONDecodeError, Exception) as e:
            print(f"Ошибка получения JSON из Redis для ключа {key}: {e}")
            return None
    
    async def set_json(self, key: str, data: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Сохранение JSON данных по ключу"""
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            return await self.set(key, json_data, ttl_seconds)
        except Exception as e:
            print(f"Ошибка сохранения JSON в Redis для ключа {key}: {e}")
            return False
    
    # Специализированные методы для подписанных URL
    async def get_signed_url(self, image_name: str) -> Optional[str]:
        """Получение подписанного URL из кэша"""
        return await self.get(f"signed_url:{image_name}")
    
    async def cache_signed_url(self, image_name: str, signed_url: str, ttl_seconds: int = 3600) -> bool:
        """Кэширование подписанного URL"""
        return await self.set(f"signed_url:{image_name}", signed_url, ttl_seconds)
    
    async def clear_signed_url(self, image_name: str) -> bool:
        """Удаление подписанного URL из кэша"""
        return await self.delete(f"signed_url:{image_name}")
    
    # Методы для работы с сессиями (если понадобятся)
    async def get_session(self, session_id: str) -> Optional[Any]:
        """Получение данных сессии"""
        return await self.get_json(f"session:{session_id}")
    
    async def set_session(self, session_id: str, data: Any, ttl_seconds: int = 3600) -> bool:
        """Сохранение данных сессии"""
        return await self.set_json(f"session:{session_id}", data, ttl_seconds)
    
    async def clear_session(self, session_id: str) -> bool:
        """Удаление сессии"""
        return await self.delete(f"session:{session_id}")
    
    # Методы для работы с временными данными
    async def get_temp_data(self, key: str) -> Optional[Any]:
        """Получение временных данных"""
        return await self.get_json(f"temp:{key}")
    
    async def set_temp_data(self, key: str, data: Any, ttl_seconds: int = 300) -> bool:
        """Сохранение временных данных (по умолчанию 5 минут)"""
        return await self.set_json(f"temp:{key}", data, ttl_seconds)
    
    async def clear_temp_data(self, key: str) -> bool:
        """Удаление временных данных"""
        return await self.delete(f"temp:{key}")
    
    async def ping(self) -> bool:
        """Проверка соединения с Redis"""
        try:
            result = await self.redis_client.ping()
            return result is True
        except Exception as e:
            print(f"Ошибка ping Redis: {e}")
            return False
    
    async def close(self):
        """Закрытие соединения с Redis"""
        try:
            await self.redis_client.aclose()
        except Exception as e:
            print(f"Ошибка закрытия Redis соединения: {e}")


# Глобальный экземпляр сервиса
redis_service = RedisService()
