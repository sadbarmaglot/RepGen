@echo off
chcp 65001 >nul
echo 🏗️ Запуск современного ИИ-Инженера...
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    echo Установите Python с https://python.org
    pause
    exit /b 1
)

REM Запускаем приложение
python run_modern.py

if errorlevel 1 (
    echo.
    echo ❌ Ошибка запуска приложения
    echo Проверьте:
    echo - Установлены ли зависимости: pip install Pillow openai
    echo - Настроен ли API ключ OpenAI
    pause
    exit /b 1
)

echo.
echo 👋 Приложение закрыто
pause

