#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Клиент для работы с API планов
"""

import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlansAPIClient:
    """Клиент для работы с API планов"""
    
    def __init__(self, base_url: str = "https://auto-gens.com/repgen", auth_client=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Используем существующий клиент аутентификации
        self.auth_client = auth_client
        
        # Обновляем заголовки авторизации при инициализации
        self._update_auth_headers()
    
    def _update_auth_headers(self):
        """Обновление заголовков авторизации"""
        if self.auth_client and self.auth_client.access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.auth_client.access_token}'
            })
    
    def _ensure_auth(self) -> bool:
        """Обеспечение валидности авторизации"""
        if not self.auth_client:
            return False
        
        # Обновляем заголовки авторизации
        self._update_auth_headers()
        
        # Проверяем валидность токена
        return self.auth_client.ensure_valid_token()
    
    def create_plan(self, object_id: int, name: str, description: str, image_name: str) -> Dict[str, Any]:
        """Создание нового плана"""
        try:
            if not self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/plans/"
            
            data = {
                'object_id': object_id,
                'name': name,
                'description': description,
                'image_name': image_name
            }
            
            response = self.session.post(url, json=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"План '{name}' успешно создан")
                return {
                    'success': True,
                    'plan': result,
                    'message': 'План создан успешно'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка создания плана: {response.status_code}')
                logger.error(f"Ошибка создания плана: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при создании плана: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании плана: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def get_plans_by_object(self, object_id: int) -> Dict[str, Any]:
        """Получение списка планов для объекта"""
        try:
            print(f"DEBUG API: Запрос планов для объекта {object_id}")
            
            if not self._ensure_auth():
                print("DEBUG API: Ошибка авторизации")
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/plans/object/{object_id}"
            print(f"DEBUG API: URL запроса: {url}")
            print(f"DEBUG API: Заголовки: {self.session.headers}")
            
            response = self.session.get(url, timeout=30)
            print(f"DEBUG API: Статус ответа: {response.status_code}")
            print(f"DEBUG API: Текст ответа: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                plans = result.get('plans', [])
                total = result.get('total', len(plans))
                
                print(f"DEBUG API: Получено {len(plans)} планов для объекта {object_id}")
                print(f"DEBUG API: Данные планов: {plans}")
                logger.info(f"Получено {len(plans)} планов для объекта {object_id}")
                return {
                    'success': True,
                    'plans': plans,
                    'total': total,
                    'message': f'Получено {len(plans)} планов'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка получения планов: {response.status_code}')
                print(f"DEBUG API: Ошибка получения планов: {error_message}")
                logger.error(f"Ошибка получения планов: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            print(f"DEBUG API: Ошибка сети при получении планов: {e}")
            logger.error(f"Ошибка сети при получении планов: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            print(f"DEBUG API: Неожиданная ошибка при получении планов: {e}")
            logger.error(f"Неожиданная ошибка при получении планов: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def update_plan(self, plan_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Обновление информации о плане"""
        try:
            if not self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/plans/{plan_id}"
            
            data = {}
            if name is not None:
                data['name'] = name
            if description is not None:
                data['description'] = description
            
            if not data:
                return {
                    'success': False,
                    'error': 'Не указаны данные для обновления'
                }
            
            response = self.session.put(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"План {plan_id} успешно обновлен")
                return {
                    'success': True,
                    'plan': result,
                    'message': 'План обновлен успешно'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка обновления плана: {response.status_code}')
                logger.error(f"Ошибка обновления плана: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при обновлении плана: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обновлении плана: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def delete_plan(self, plan_id: int) -> Dict[str, Any]:
        """Удаление плана"""
        try:
            if not self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/plans/{plan_id}"
            
            response = self.session.delete(url, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"План {plan_id} успешно удален")
                return {
                    'success': True,
                    'message': 'План удален успешно'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка удаления плана: {response.status_code}')
                logger.error(f"Ошибка удаления плана: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при удалении плана: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при удалении плана: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def upload_image(self, image_path: str) -> Dict[str, Any]:
        """Загрузка изображения в GCP бакет"""
        try:
            if not self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/upload/images/blob"
            
            # Проверяем существование файла
            if not Path(image_path).exists():
                return {
                    'success': False,
                    'error': f'Файл не найден: {image_path}'
                }
            
            # Подготавливаем multipart form data
            with open(image_path, 'rb') as f:
                files = {'file': f}
                
                # Временно убираем Content-Type для multipart
                headers = self.session.headers.copy()
                if 'Content-Type' in headers:
                    del headers['Content-Type']
                
                response = self.session.post(url, files=files, headers=headers, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    image_name = result[0].get('image_name')
                    if image_name:
                        logger.info(f"Изображение успешно загружено: {image_name}")
                        return {
                            'success': True,
                            'image_name': image_name,
                            'message': 'Изображение загружено успешно'
                        }
                
                return {
                    'success': False,
                    'error': 'Неожиданный формат ответа сервера'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка загрузки изображения: {response.status_code}')
                logger.error(f"Ошибка загрузки изображения: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при загрузке изображения: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при загрузке изображения: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }


# Глобальный экземпляр клиента планов
plans_api_client = None

def get_plans_api_client(auth_client=None):
    """Получение экземпляра клиента планов"""
    global plans_api_client
    if plans_api_client is None:
        plans_api_client = PlansAPIClient(auth_client=auth_client)
    return plans_api_client
