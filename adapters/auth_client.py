#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Клиент для работы с API аутентификации
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthClient:
    """Клиент для работы с API аутентификации"""
    
    def __init__(self, base_url: str = "https://auto-gens.com/repgen"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Путь к файлу с токенами
        self.tokens_file = Path(__file__).parent.parent / 'auth_tokens.json'
        
        # Загружаем сохраненные токены
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.user_info = None
        
        self.load_tokens()
    
    def load_tokens(self):
        """Загрузка токенов из файла"""
        try:
            if self.tokens_file.exists():
                with open(self.tokens_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                
                # Парсим время истечения токена
                expires_str = data.get('expires_at')
                if expires_str:
                    self.token_expires_at = datetime.fromisoformat(expires_str)
                
                # Загружаем информацию о пользователе
                self.user_info = data.get('user_info')
                
                # Обновляем заголовки авторизации
                if self.access_token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.access_token}'
                    })
                
                # Если токены есть, но информации о пользователе нет, пытаемся получить её
                if self.access_token and not self.user_info:
                    try:
                        user_info_result = self.get_user_info()
                        if user_info_result.get('success'):
                            self.user_info = user_info_result['user']
                            # Сохраняем обновленную информацию
                            self.save_tokens()
                    except Exception as e:
                        logger.warning(f"Не удалось получить информацию о пользователе: {e}")
                
                logger.info("Токены загружены из файла")
        except Exception as e:
            logger.error(f"Ошибка загрузки токенов: {e}")
    
    def save_tokens(self):
        """Сохранение токенов в файл"""
        try:
            data = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
                'user_info': self.user_info,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.tokens_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info("Токены сохранены в файл")
        except Exception as e:
            logger.error(f"Ошибка сохранения токенов: {e}")
    
    def clear_tokens(self):
        """Очистка токенов"""
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.user_info = None
        
        # Удаляем заголовок авторизации
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        
        # Удаляем файл с токенами
        try:
            if self.tokens_file.exists():
                self.tokens_file.unlink()
        except Exception as e:
            logger.error(f"Ошибка удаления файла токенов: {e}")
    
    def is_token_valid(self) -> bool:
        """Проверка валидности токена"""
        if not self.access_token or not self.token_expires_at:
            return False
        
        # Проверяем, не истек ли токен (с запасом в 5 минут)
        now = datetime.now()
        return now < (self.token_expires_at - timedelta(minutes=5))
    
    def register(self, email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Регистрация нового пользователя"""
        try:
            url = f"{self.base_url}/auth/register"
            
            data = {
                'email': email,
                'password': password,
                'name': name
            }
            
            response = self.session.post(url, json=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"Пользователь {email} успешно зарегистрирован")
                return {
                    'success': True,
                    'user': result,
                    'message': 'Регистрация прошла успешно'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка регистрации: {response.status_code}')
                logger.error(f"Ошибка регистрации: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при регистрации: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при регистрации: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Вход в систему"""
        try:
            url = f"{self.base_url}/auth/login"
            
            data = {
                'email': email,
                'password': password
            }
            
            response = self.session.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Сохраняем токены
                self.access_token = result['access_token']
                self.refresh_token = result['refresh_token']
                
                # Вычисляем время истечения токена
                expires_in = result.get('expires_in', 3600)  # По умолчанию 1 час
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Обновляем заголовки авторизации
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                
                # Получаем информацию о пользователе
                user_info = self.get_user_info()
                if user_info.get('success'):
                    self.user_info = user_info['user']
                
                # Сохраняем токены
                self.save_tokens()
                
                logger.info(f"Пользователь {email} успешно вошел в систему")
                return {
                    'success': True,
                    'message': 'Вход выполнен успешно',
                    'user': self.user_info
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', f'Ошибка входа: {response.status_code}')
                logger.error(f"Ошибка входа: {error_message}")
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при входе: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при входе: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def refresh_access_token(self) -> bool:
        """Обновление access токена"""
        if not self.refresh_token:
            return False
        
        try:
            url = f"{self.base_url}/auth/refresh"
            
            data = {
                'refresh_token': self.refresh_token
            }
            
            response = self.session.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Обновляем токены
                self.access_token = result['access_token']
                self.refresh_token = result['refresh_token']
                
                # Вычисляем время истечения токена
                expires_in = result.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Обновляем заголовки авторизации
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                
                # Сохраняем токены
                self.save_tokens()
                
                logger.info("Access токен успешно обновлен")
                return True
            else:
                logger.error(f"Ошибка обновления токена: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при обновлении токена: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обновлении токена: {e}")
            return False
    
    def get_user_info(self) -> Dict[str, Any]:
        """Получение информации о текущем пользователе"""
        try:
            url = f"{self.base_url}/auth/me"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info("Информация о пользователе получена")
                return {
                    'success': True,
                    'user': user_data
                }
            else:
                logger.error(f"Ошибка получения информации о пользователе: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Ошибка получения информации: {response.status_code}'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при получении информации о пользователе: {e}")
            return {
                'success': False,
                'error': f'Ошибка сети: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении информации о пользователе: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    def logout(self) -> Dict[str, Any]:
        """Выход из системы"""
        try:
            url = f"{self.base_url}/auth/logout"
            
            response = self.session.post(url, timeout=30)
            
            # Очищаем токены независимо от ответа сервера
            self.clear_tokens()
            
            if response.status_code == 200:
                logger.info("Выход выполнен успешно")
                return {
                    'success': True,
                    'message': 'Выход выполнен успешно'
                }
            else:
                logger.warning(f"Сервер вернул ошибку при выходе: {response.status_code}")
                return {
                    'success': True,  # Все равно считаем успешным, так как токены очищены
                    'message': 'Выход выполнен (токены очищены)'
                }
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ошибка сети при выходе: {e}")
            # Очищаем токены даже при ошибке сети
            self.clear_tokens()
            return {
                'success': True,
                'message': 'Выход выполнен (токены очищены)'
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при выходе: {e}")
            self.clear_tokens()
            return {
                'success': True,
                'message': 'Выход выполнен (токены очищены)'
            }
    
    def ensure_valid_token(self) -> bool:
        """Обеспечение валидности токена (автоматическое обновление при необходимости)"""
        if self.is_token_valid():
            return True
        
        if self.refresh_token:
            return self.refresh_access_token()
        
        return False
    
    def is_authenticated(self) -> bool:
        """Проверка аутентификации пользователя"""
        return self.ensure_valid_token() and self.user_info is not None
    
    def get_user_name(self) -> Optional[str]:
        """Получение имени пользователя"""
        if self.user_info:
            return self.user_info.get('name') or self.user_info.get('email', 'Пользователь')
        return None
    
    def get_user_email(self) -> Optional[str]:
        """Получение email пользователя"""
        if self.user_info:
            return self.user_info.get('email')
        return None


# Глобальный экземпляр клиента аутентификации
auth_client = AuthClient()
