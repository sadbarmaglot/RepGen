@echo off
REM ==========================================
REM 🪟 СБОРКА WINDOWS ПРИЛОЖЕНИЯ НА WINDOWS
REM ==========================================

echo ==========================================
echo 🪟 СБОРКА WINDOWS ПРИЛОЖЕНИЯ НА WINDOWS
echo ==========================================

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    echo Установите Python с https://python.org
    pause
    exit /b 1
)

echo ✅ Python найден
python --version

REM Создаем виртуальное окружение
echo 📦 Создаем виртуальное окружение...
python -m venv venv_build
call venv_build\Scripts\activate.bat

REM Устанавливаем зависимости
echo 📥 Устанавливаем зависимости...
python -m pip install --upgrade pip
pip install pyinstaller

if exist requirements.txt (
    echo Устанавливаем зависимости из requirements.txt...
    pip install -r requirements.txt
) else (
    echo ⚠️ requirements.txt не найден
)

REM Создаем папку для сборки
if not exist build\win mkdir build\win

REM Собираем приложение
echo 🔨 Собираем Windows приложение...
if exist build_exe.py (
    echo Запускаем сборку через build_exe.py...
    python build_exe.py
) else if exist main.py (
    echo Запускаем PyInstaller напрямую...
    pyinstaller --onefile --windowed --name=DefectAnalyzer --icon=assets\icon.ico main.py
) else (
    echo ❌ Не найден main.py или build_exe.py!
    pause
    exit /b 1
)

REM Копируем собранный файл
if exist dist\DefectAnalyzer.exe (
    copy dist\DefectAnalyzer.exe build\win\
    echo ✅ DefectAnalyzer.exe скопирован в build\win\
) else (
    echo ❌ DefectAnalyzer.exe не найден в папке dist\
    pause
    exit /b 1
)

REM Проверяем результат
if exist build\win\DefectAnalyzer.exe (
    echo ✅ Windows приложение успешно собрано!
    echo 📁 Файл: build\win\DefectAnalyzer.exe
    dir build\win\DefectAnalyzer.exe
) else (
    echo ⚠️ Приложение не собрано или не найдено
)

REM Деактивируем виртуальное окружение
deactivate

echo.
echo ==========================================
echo 🎯 СБОРКА ЗАВЕРШЕНА!
echo ==========================================
echo 📁 EXE файл: build\win\DefectAnalyzer.exe
echo.
echo 🔧 Для создания установщика:
echo 1. Установите Inno Setup
echo 2. Откройте installer\windows\DefectAnalyzer.iss
echo 3. Нажмите F9 или Build -^> Compile
echo ==========================================
pause
