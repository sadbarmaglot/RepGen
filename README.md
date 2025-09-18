# RepGen - Генератор отчетов по дефектам

Система для анализа дефектов строительных конструкций по изображениям с использованием AI моделей.

## 🚀 Новый FastAPI сервис

Добавлен новый **FastAPI сервис** для проксирования запросов к различным AI API с анализом изображений дефектов.

### Основные возможности API:

- 🔍 **Анализ дефектов** строительных конструкций по изображениям
- 🤖 **Множественные AI провайдеры**:
  - OpenAI GPT (GPT-4o, GPT-4o-mini, GPT-4 Vision)
  - Anthropic Claude (Claude 3.5 Sonnet, Claude 3.5 Haiku)
  - Google Gemini (Gemini 1.5 Flash, Gemini 1.5 Pro)
  - Cohere (Command R+, Command R)
- 📊 **Параллельная обработка** изображений
- 🚀 **Асинхронная архитектура**
- 🐳 **Docker контейнеризация**
- 📝 **Автоматическая документация API**

## 📁 Структура проекта

```
repgen/
├── api/                    # 🆕 FastAPI сервис
│   ├── main.py            # Основное приложение
│   ├── models/            # Pydantic модели
│   ├── services/          # Бизнес-логика
│   ├── requirements.txt   # Зависимости
│   ├── Dockerfile         # Docker образ
│   ├── docker-compose.yml # Docker Compose
│   ├── start.sh           # Скрипт запуска
│   ├── stop.sh            # Скрипт остановки
│   ├── monitor.sh         # Скрипт мониторинга
│   └── README.md          # Документация API
├── common/                 # Общие утилиты
├── core/                   # Основная логика бота
├── docx_generator/         # Генератор отчетов
├── main.py                 # Telegram бот
└── README.md               # Этот файл
```

## 🚀 Быстрый старт

### 1. Запуск API сервиса

```bash
cd api
cp env.example .env
# Отредактируйте .env, добавив ваши API ключи

# Запуск через Docker Compose
./start.sh

# Или вручную
docker-compose up -d
```

### 2. Проверка работоспособности

```bash
curl http://localhost:8000/health
```

### 3. Документация API

Откройте в браузере: http://localhost:8000/docs

## 🔧 Использование API

### Анализ дефектов

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "image_urls": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ],
    "config": {
      "model_name": "gpt-4o-mini",
      "temperature": 0.2,
      "max_tokens": 1024
    }
  }'
```

### Получение списка моделей

```bash
curl http://localhost:8000/models
```

## 🤖 Поддерживаемые AI модели

| Провайдер | Модели | Особенности |
|-----------|--------|-------------|
| **OpenAI** | GPT-4o, GPT-4o-mini, GPT-4 Vision | Высокое качество, поддержка изображений |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3.5 Haiku | Отличное понимание контекста |
| **Google** | Gemini 1.5 Flash, Gemini 1.5 Pro | Быстрая обработка, хорошая точность |
| **Cohere** | Command R+, Command R | Специализация на тексте |

## 🐳 Docker команды

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f defect-analysis-api

# Пересборка
docker-compose up --build -d
```

## 📊 Мониторинг

```bash
# Запуск мониторинга
./monitor.sh

# Проверка статуса
curl http://localhost:8000/health

# Статистика контейнеров
docker stats defect-analysis-api
```

## 🔐 Конфигурация

Создайте файл `.env` на основе `env.example`:

```bash
# OpenAI API Key (обязательно для GPT моделей)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key (для Claude моделей)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google Cloud Project ID (для Vertex AI Gemini моделей)
GOOGLE_CLOUD_PROJECT_ID=your-gcp-project-id-here
GOOGLE_CLOUD_LOCATION=us-central1

# Cohere API Key (для Cohere моделей)
COHERE_API_KEY=your_cohere_api_key_here
```

## 🧪 Тестирование

```bash
# Запуск тестов
python run_tests.py

# Тест API endpoints
python test_api.py

# Pytest тесты
pytest -v
```

## 📈 Производительность

- **Параллельная обработка** изображений
- **Асинхронные HTTP запросы**
- **Семафоры** для ограничения одновременных запросов
- **Redis** для кэширования (опционально)
- **Health checks** и мониторинг

## 🔒 Безопасность

- API ключи через переменные окружения
- Валидация входных данных через Pydantic
- Ограничение на количество изображений (максимум 10)
- CORS настройки для разработки

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs defect-analysis-api`
2. Убедитесь, что API ключи корректны
3. Проверьте доступность внешних API
4. Убедитесь, что изображения доступны по указанным URL

## 📚 Документация

- [Документация API](api/README.md)
- [Примеры использования](api/README.md#использование-api)
- [Конфигурация](api/README.md#конфигурация)
- [Docker инструкции](api/README.md#docker-команды)

---

## 🎯 Основной функционал (Telegram бот)

Оригинальный Telegram бот для анализа дефектов по фотографиям остается доступным в `main.py`.

### Запуск бота:

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
export BOT_TOKEN="your_bot_token"
export ADMIN_IDS="123456,789012"

# Запуск
python main.py
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

Проект распространяется под лицензией MIT.