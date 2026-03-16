# RepGen Backend

Бэкенд платформы **ИИ-Инженер** — обследование зданий и генерация отчётов о дефектах с использованием AI.

## Возможности

- **AI-анализ дефектов** — фото → определение конструкции → подбор дефектов → код, категория, описание, рекомендация
- **Проверка технических отчётов** — загрузка docx/pdf → парсинг → LLM-анализ на ошибки и соответствие нормативам (ГОСТ 31937-2024, СП 20 и др.)
- **Генерация Word-отчётов** — ведомости дефектов
- **Мульти-провайдер AI** — OpenAI (GPT-4o, GPT-4.1, GPT-5.2), Google Gemini
- **JWT-авторизация** — access + refresh токены
- **GCS-хранилище** — фото и документы

## Клиенты

| Клиент | Stack |
|--------|-------|
| iOS | SwiftUI, SwiftData |
| Desktop | Python, PySide6 |
| Web | React, TypeScript, Vite |

Все клиенты работают через REST API (`/repgen/*`).

## Быстрый старт

```bash
# Docker (основной способ)
docker-compose up -d
docker-compose logs -f defect-analysis-api

# Health check
curl http://localhost:8000/health

# Swagger
# http://localhost:8000/docs
```

## Тесты

```bash
pytest -v
```

## Структура

```
main.py                        # Entry point: FastAPI
settings.py                    # Конфигурация
api/
  routes/                      # 18 модулей эндпоинтов
  services/                    # 24 сервиса бизнес-логики
  models/
    entities/                  # SQLAlchemy ORM-модели
    requests/                  # Pydantic request-модели
    responses/                 # Pydantic response-модели
  dependencies/                # DI (auth, access control)
  middleware/                  # Logging middleware
common/
  defects_db.py                # Каталог дефектов + промпты AI
  gc_utils.py                  # GCS-клиент (images + documents бакеты)
docx_generator/                # Генерация Word-документов
reference_docs/                # ГОСТ/СП тексты для LLM-проверки (не в git)
tests/                         # pytest
migrations/                    # SQL-миграции
```

## Конфигурация

Переменные окружения (`.env`):

| Переменная | Описание |
|------------|----------|
| `PROJECT_ID` | Google Cloud Project ID |
| `BUCKET_NAME` | GCS бакет для фото |
| `DOCUMENTS_BUCKET_NAME` | GCS бакет для документов |
| `OPENAI_API_KEY` | OpenAI API ключ |
| `SQL_USER`, `SQL_PASSWORD`, `SQL_DB`, `SQL_HOST` | PostgreSQL |
| `REDIS_HOST`, `REDIS_PORT` | Redis |
| `JWT_SECRET_KEY` | Секрет для JWT |

## Reference docs (для проверки отчётов)

Директория `reference_docs/` содержит .txt файлы нормативных документов (ГОСТ, СП), которые подаются в контекст LLM при проверке отчётов. Файлы не в git — нужно создать на сервере вручную:

```bash
mkdir -p reference_docs/
# Положить: GOST_31937-2024.txt, SP_20.13330.2016.txt
```
