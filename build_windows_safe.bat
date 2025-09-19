@echo off
REM ==========================================
REM Безопасная сборка Windows приложения
REM Без Unicode символов - только ASCII
REM ==========================================

echo ==========================================
echo СБОРКА WINDOWS ПРИЛОЖЕНИЯ (БЕЗОПАСНАЯ ВЕРСИЯ)
echo ==========================================

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python не найден!
    exit /b 1
)

echo [OK] Python найден
python --version

REM Создаем виртуальное окружение
echo [INFO] Создаем виртуальное окружение...
if exist venv_safe rmdir /s /q venv_safe
python -m venv venv_safe
call venv_safe\Scripts\activate.bat

REM Устанавливаем зависимости
echo [INFO] Устанавливаем зависимости...
python -m pip install --upgrade pip
pip install pyinstaller

if exist requirements.txt (
    echo [INFO] Устанавливаем зависимости из requirements.txt...
    pip install -r requirements.txt
) else (
    echo [WARNING] requirements.txt не найден
)

REM Проверяем структуру проекта
echo [INFO] Проверяем структуру проекта...

if not exist main.py (
    echo [ERROR] main.py не найден!
    exit /b 1
)
echo [OK] main.py найден

if not exist ui (
    echo [ERROR] папка ui не найдена!
    exit /b 1
)
echo [OK] папка ui найдена

if not exist adapters (
    echo [ERROR] папка adapters не найдена!
    exit /b 1
)
echo [OK] папка adapters найдена

if not exist common (
    echo [ERROR] папка common не найдена!
    exit /b 1
)
echo [OK] папка common найдена

if not exist docx_generator (
    echo [ERROR] папка docx_generator не найдена!
    exit /b 1
)
echo [OK] папка docx_generator найдена

if not exist assets (
    echo [ERROR] папка assets не найдена!
    exit /b 1
)
echo [OK] папка assets найдена

REM Проверяем Python модули
echo [INFO] Проверяем Python модули...

python -c "import tkinter; print('[OK] tkinter OK')" 2>nul
if errorlevel 1 (
    echo [ERROR] tkinter не найден - критическая ошибка!
    exit /b 1
)

python -c "import PIL; print('[OK] PIL OK')" 2>nul
if errorlevel 1 (
    echo [ERROR] PIL не найден!
    pip install Pillow
)

python -c "import openai; print('[OK] openai OK')" 2>nul
if errorlevel 1 (
    echo [ERROR] openai не найден!
    exit /b 1
)

python -c "import requests; print('[OK] requests OK')" 2>nul
if errorlevel 1 (
    echo [ERROR] requests не найден!
    exit /b 1
)

python -c "import docx; print('[OK] docx OK')" 2>nul
if errorlevel 1 (
    echo [ERROR] docx не найден!
    exit /b 1
)

python -c "import trimesh; print('[OK] trimesh OK')" 2>nul
if errorlevel 1 (
    echo [ERROR] trimesh не найден!
    exit /b 1
)

python -c "import numpy; print('[OK] numpy OK')" 2>nul
if errorlevel 1 (
    echo [ERROR] numpy не найден!
    exit /b 1
)

echo [OK] Все модули проверены успешно

REM Проверяем иконку
if exist assets\icon.ico (
    echo [OK] Иконка найдена: assets\icon.ico
    set ICON_PARAM=--icon=assets\icon.ico
) else (
    echo [WARNING] assets\icon.ico не найден, используем без иконки
    set ICON_PARAM=
)

REM Создаем папку для сборки
if not exist build\win mkdir build\win

REM Собираем приложение
echo [INFO] Собираем Windows приложение...

pyinstaller --onefile --windowed --name=DefectAnalyzer %ICON_PARAM% ^
  --add-data "ui;ui" ^
  --add-data "common;common" ^
  --add-data "docx_generator;docx_generator" ^
  --add-data "adapters;adapters" ^
  --add-data "assets;assets" ^
  --add-data "examples;examples" ^
  --add-data "settings.py;." ^
  --hidden-import=tkinter ^
  --hidden-import=tkinter.ttk ^
  --hidden-import=tkinter.messagebox ^
  --hidden-import=tkinter.filedialog ^
  --hidden-import=PIL ^
  --hidden-import=PIL.Image ^
  --hidden-import=PIL.ImageTk ^
  --hidden-import=openai ^
  --hidden-import=pathlib ^
  --hidden-import=threading ^
  --hidden-import=json ^
  --hidden-import=logging ^
  --hidden-import=requests ^
  --hidden-import=docx ^
  --hidden-import=dotenv ^
  --hidden-import=trimesh ^
  --hidden-import=numpy ^
  main.py

if errorlevel 1 (
    echo [ERROR] Ошибка PyInstaller! Код выхода: %errorlevel%
    echo [INFO] Проверьте логи выше для деталей
    exit /b 1
)

echo [OK] PyInstaller завершился успешно

REM Копируем собранный файл
if exist dist\DefectAnalyzer.exe (
    copy dist\DefectAnalyzer.exe build\win\
    echo [OK] DefectAnalyzer.exe скопирован в build\win\
    
    REM Показываем информацию о файле
    for %%A in (build\win\DefectAnalyzer.exe) do (
        echo [INFO] Размер файла: %%~zA байт
    )
) else (
    echo [ERROR] DefectAnalyzer.exe не найден в папке dist\
    exit /b 1
)

REM Деактивируем виртуальное окружение
deactivate

echo.
echo ==========================================
echo СБОРКА ЗАВЕРШЕНА УСПЕШНО!
echo ==========================================
echo [OK] EXE файл: build\win\DefectAnalyzer.exe
echo ==========================================

exit /b 0