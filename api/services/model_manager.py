import asyncio
import re
import os
import json
import logging

from abc import ABC, abstractmethod
from typing import Dict, List, Any

from common.defects_db import SYSTEM_PROMPT, USER_PROMPT, get_user_prompt
from settings import PROJECT_ID, LOCATION

# OpenAI
try:
    from openai import OpenAI, RateLimitError
except ImportError:
    OpenAI = None
    RateLimitError = None

# Google Gemini (Vertex AI)
try:
    from google import genai
    from google.genai.types import GenerateContentResponse
except ImportError:
    genai = None
    GenerateContentResponse = None
    
logger = logging.getLogger(__name__)

class BaseModelProvider(ABC):
    """Базовый класс для провайдеров моделей"""
    
    @abstractmethod
    async def analyze_image(
        self, 
        image_url: str, 
        system_prompt: str, 
        user_prompt: str, 
        config: Dict[str, Any]
        ) -> Dict[str, Any]:

        """Анализ изображения с помощью модели"""
        pass
    
    def cleanup(self):
        """Очистка ресурсов провайдера"""
        pass

class OpenAIProvider(BaseModelProvider):
    """Провайдер OpenAI GPT моделей"""
    
    def __init__(self):
        self.client = OpenAI()
        self.available_models = [
            "gpt-4o-mini", 
            "gpt-4o",
            "gpt-5.1"
            ]
    
    def is_available(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))

    async def analyze_image(
        self, 
        image_url: str,
        mime_type: str,
        system_prompt: str, 
        user_prompt: str,
        config: Dict[str, Any]
        ) -> Dict[str, Any]:
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=config.get("model_name", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]}
                ],
                temperature=config.get("temperature", 0.2),
                max_tokens=config.get("max_tokens", 4096),
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"OpenAI API результат: {result}")
            return {
                "image_url": image_url,
                "recommendation": result.get("recommendation", ""),
                "category": result.get("category", ""),
                "construction_type": result.get("construction_type", ""),
                "description": result.get("description", ""),
                "model_used": config.get("model_name", "gpt-4o-mini"),
            }
            
        except RateLimitError:
            raise Exception("Превышен лимит запросов к OpenAI API")
        except Exception as e:
            logger.error(f"Ошибка OpenAI API: {e}")
            raise

class GoogleGeminiProvider(BaseModelProvider):
    """Провайдер Google Gemini моделей через Vertex AI"""
    
    def __init__(self):
        if not genai:
            raise ImportError("Vertex AI не установлен")

        self.project_id = PROJECT_ID
        self.location = LOCATION

        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location,
        )
        
        self.available_models = [
            "gemini-2.5-flash", 
            "gemini-2.5-pro",
        ]

        logger.info(f"Gemini провайдер инициализирован с моделями: {self.available_models}")
    
    def is_available(self) -> bool:
        return bool(
            genai is not None and 
            self.project_id and 
            self.location
        )
    
    @staticmethod
    def _safe_parse_json(content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        if (content.startswith('"') and content.endswith('"')) or ("\\\"" in content):
            try:
                return json.loads(json.loads(content))
            except Exception:
                pass

        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return {}

    @staticmethod
    def _extract_text(response: GenerateContentResponse) -> str | None:
        if not response.candidates:
            return None
        candidate = response.candidates[0]
        if not candidate.content or not candidate.content.parts:
            return None
        for part in candidate.content.parts:
            if hasattr(part, "text") and part.text:
                return part.text
        return None
        
    async def analyze_image(
        self, image_url: str, 
        mime_type: str, 
        system_prompt: str, 
        user_prompt: str, 
        config: Dict[str, Any]
        ) -> Dict[str, Any]:
        try:
            contents = [
                {
                    "role": "user",
                        "parts": [
                            {"text": system_prompt},
                            {"text": user_prompt},
                            {"file_data": {"mime_type": mime_type, "file_uri": image_url}}
                        ]
                }
            ]

            gen_cfg = {
                "temperature":       config.get("temperature", 0.1),
                "max_output_tokens": config.get("max_tokens", 4096),
                "response_mime_type": "application/json",
            }
            
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=config.get("model_name", "gemini-2.5-flash"),
                contents=contents,
                config=gen_cfg,
            )
            
            content = self._extract_text(response)

            if content is None:
                return {
                    "image_url": image_url,
                    "description": "",
                    "recommendation": "Ответ пустой или нераспознан",
                    "construction_type": "",
                    "model_used": config.get("model_name", "gemini-2.5-flash"),
                }                

            result = self._safe_parse_json(content)

            if result:
                logger.info(f"Gemini API результат: {result}")
                return {
                    "image_url": image_url,
                    "description": result.get("description", ""),
                    "recommendation": result.get("recommendation", ""),
                    "category": result.get("category", ""),
                    "construction_type": result.get("construction_type", ""),
                    "model_used": config.get("model_name", "gemini-2.5-flash")
                }
            else:
                return {
                    "image_url": image_url,
                    "description": content,
                    "recommendation": "Требуется ручная обработка ответа",
                    "construction_type": "",
                    "model_used": config.get("model_name", "gemini-2.5-flash"),
                }
                
        except Exception as e:
            logger.error(f"Ошибка Vertex AI Gemini API: {e}")
            raise

class ModelManager:
    """Менеджер моделей для анализа дефектов"""
    
    def __init__(self):
        self.providers: Dict[str, BaseModelProvider] = {}
        self.default_provider = "openai"
        self.system_prompt = SYSTEM_PROMPT
        self.user_prompt = USER_PROMPT
        
        self._init_providers()
    
    def _init_providers(self):
        """Инициализация доступных провайдеров"""
        try:
            self.providers["openai"] = OpenAIProvider()
            logger.info("OpenAI провайдер инициализирован")
        except Exception as e:
            logger.warning(f"OpenAI провайдер не доступен: {e}")
        
        try:
            self.providers["gemini"] = GoogleGeminiProvider()
            logger.info("Google Gemini провайдер инициализирован")
        except Exception as e:
            logger.warning(f"Google Gemini провайдер не доступен: {e}")
        
        logger.info(f"Инициализированные провайдеры: {list(self.providers.keys())}")
        for name, provider in self.providers.items():
            logger.info(f"Провайдер {name}: доступен={provider.is_available()}, модели={getattr(provider, 'available_models', [])}")

    def get_available_models(self) -> Dict[str, List[str]]:
        """Получение списка доступных моделей по провайдерам"""
        available = {}
        for provider_name, provider in self.providers.items():
            if provider.is_available():
                available[provider_name] = provider.available_models
        return available
    
    def get_current_default(self) -> str:
        """Получение текущего провайдера по умолчанию"""
        return self.default_provider
    
    def set_default_model(self, model_name: str):
        """Установка модели по умолчанию"""
        for provider_name, provider in self.providers.items():
            if model_name in provider.available_models:
                self.default_provider = provider_name
                return
        
        raise ValueError(f"Модель {model_name} не найдена в доступных провайдерах")
    
    def get_provider(self, model_name: str = None) -> BaseModelProvider:
        """Получение провайдера для указанной модели"""        
        if model_name:
            for _, provider in self.providers.items():
                if model_name in provider.available_models and provider.is_available():
                    return provider   

        if self.default_provider in self.providers and self.providers[self.default_provider].is_available():
            return self.providers[self.default_provider]
        
        for provider in self.providers.values():
            if provider.is_available():
                return provider
        
        raise Exception("Нет доступных провайдеров моделей")
    
    async def analyze_image(
        self, 
        image_url: str, 
        mime_type: str,
        config: Dict[str, Any],
        construction_type: str = None
        ) -> Dict[str, Any]:
        """Анализ изображения с помощью выбранной модели"""
        
        model_name = config.get("model_name")
        
        provider = self.get_provider(model_name)
        
        if construction_type is not None:
            user_prompt = get_user_prompt(construction_type)
        else:
            user_prompt = self.user_prompt
        
        return await provider.analyze_image(
            image_url, 
            mime_type, 
            self.system_prompt, 
            user_prompt, 
            config
        )
    
    def cleanup_all(self):
        """Очистка ресурсов всех провайдеров"""
        for provider in self.providers.values():
            provider.cleanup()
        logger.info("Ресурсы всех провайдеров очищены")
