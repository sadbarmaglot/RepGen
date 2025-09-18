#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Клиент для работы с API проектов
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

class ProjectAPIClient:
    """Клиент для работы с API проектов"""
    
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
    
    def create_project(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Создание нового проекта"""
        try:
            if not self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/projects/"
            
            data = {
                'name': name,
                'description': description
            }
            
            response = self.session.post(url, json=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"Проект '{name}' успешно создан")
                return {
                    'success': True,
                    'project': result,
                    'message': 'Проект создан успешно'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка создания проекта: {response.status_code}')
                logger.error(f"Ошибка создания проекта: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при создании проекта: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании проекта: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def get_projects(self) -> Dict[str, Any]:
        """Получение списка проектов пользователя"""
        try:
            if not self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/projects/"
            
            # Разрешаем автоматические редиректы
            response = self.session.get(url, timeout=30, allow_redirects=True)
            
            # Отладочная информация
            logger.info(f"Запрос к: {url}")
            logger.info(f"Статус ответа: {response.status_code}")
            logger.info(f"Финальный URL: {response.url}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                projects = result.get('projects', [])
                total = result.get('total', len(projects))
                
                logger.info(f"Получено {len(projects)} проектов")
                return {
                    'success': True,
                    'projects': projects,
                    'total': total,
                    'message': f'Получено {len(projects)} проектов'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка получения проектов: {response.status_code}')
                logger.error(f"Ошибка получения проектов: {error_message}")
                logger.error(f"Ответ сервера: {response.text}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при получении проектов: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении проектов: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def update_project(self, project_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Обновление проекта"""
        try:
            if not self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/projects/{project_id}"
            
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
                logger.info(f"Проект {project_id} успешно обновлен")
                return {
                    'success': True,
                    'project': result,
                    'message': 'Проект обновлен успешно'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка обновления проекта: {response.status_code}')
                logger.error(f"Ошибка обновления проекта: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при обновлении проекта: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обновлении проекта: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def delete_project(self, project_id: int) -> Dict[str, Any]:
        """Удаление проекта"""
        try:
            if not self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/projects/{project_id}"
            
            response = self.session.delete(url, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Проект {project_id} успешно удален")
                return {
                    'success': True,
                    'message': 'Проект удален успешно'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка удаления проекта: {response.status_code}')
                logger.error(f"Ошибка удаления проекта: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при удалении проекта: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при удалении проекта: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def get_project_by_id(self, project_id: int) -> Dict[str, Any]:
        """Получение проекта по ID"""
        try:
            if not self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/projects/{project_id}"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Проект {project_id} получен")
                return {
                    'success': True,
                    'project': result,
                    'message': 'Проект получен успешно'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка получения проекта: {response.status_code}')
                logger.error(f"Ошибка получения проекта: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при получении проекта: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении проекта: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def create_object(self, project_id: int, name: str, address: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Создание нового объекта"""
        try:
            if not self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/objects/"
            
            data = {
                'project_id': project_id,
                'name': name
            }
            
            if address is not None:
                data['address'] = address
            if description is not None:
                data['description'] = description
            
            response = self.session.post(url, json=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"Объект '{name}' успешно создан")
                return {
                    'success': True,
                    'object': result,
                    'message': 'Объект создан успешно'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка создания объекта: {response.status_code}')
                logger.error(f"Ошибка создания объекта: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при создании объекта: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании объекта: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def get_objects_by_project(self, project_id: int) -> Dict[str, Any]:
        """Получение списка объектов проекта"""
        try:
            if not self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/objects/project/{project_id}"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                objects = result.get('objects', [])
                total = result.get('total', len(objects))
                
                logger.info(f"Получено {len(objects)} объектов для проекта {project_id}")
                return {
                    'success': True,
                    'objects': objects,
                    'total': total,
                    'message': f'Получено {len(objects)} объектов'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка получения объектов: {response.status_code}')
                logger.error(f"Ошибка получения объектов: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при получении объектов: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении объектов: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def update_object(self, object_id: int, name: Optional[str] = None, address: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Обновление объекта"""
        try:
            if not self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/objects/{object_id}"
            
            data = {}
            if name is not None:
                data['name'] = name
            if address is not None:
                data['address'] = address
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
                logger.info(f"Объект {object_id} успешно обновлен")
                return {
                    'success': True,
                    'object': result,
                    'message': 'Объект обновлен успешно'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка обновления объекта: {response.status_code}')
                logger.error(f"Ошибка обновления объекта: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при обновлении объекта: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обновлении объекта: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def delete_object(self, object_id: int) -> Dict[str, Any]:
        """Удаление объекта"""
        try:
            if not self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Необходима авторизация'
                }
            
            url = f"{self.base_url}/objects/{object_id}"
            
            response = self.session.delete(url, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Объект {object_id} успешно удален")
                return {
                    'success': True,
                    'message': 'Объект удален успешно'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка удаления объекта: {response.status_code}')
                logger.error(f"Ошибка удаления объекта: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при удалении объекта: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при удалении объекта: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }


# Глобальный экземпляр клиента проектов
project_api_client = None

def get_project_api_client(auth_client=None):
    """Получение экземпляра клиента проектов"""
    global project_api_client
    if project_api_client is None:
        project_api_client = ProjectAPIClient(auth_client=auth_client)
    return project_api_client
