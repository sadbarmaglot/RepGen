#!/bin/bash
# ==========================================
# 📦 СОЗДАНИЕ WINDOWS ПАКЕТА (Python скрипты + батник)
# ==========================================

echo "=========================================="
echo "📦 СОЗДАНИЕ WINDOWS ПАКЕТА"
echo "=========================================="

# Создаем папку для Windows пакета
mkdir -p build/win

echo "📁 Создаем структуру Windows пакета..."

# Копируем основные Python файлы
cp main.py build/win/
cp settings.py build/win/

# Копируем папки
cp -r adapters build/win/
cp -r common build/win/
cp -r docx_generator build/win/
cp -r ui build/win/

# Копируем ресурсы
cp -r assets build/win/ 2>/dev/null || echo "Папка assets не найдена"
cp -r examples build/win/ 2>/dev/null || echo "Папка examples не найдена"
cp -r 3d_renders build/win/ 2>/dev/null || echo "Папка 3d_renders не найдена"

# Копируем конфигурационные файлы
cp requirements.txt build/win/ 2>/dev/null || echo "requirements.txt не найден"
cp cloud_config.json build/win/ 2>/dev/null || echo "cloud_config.json не найден"

# Создаем батник для запуска
cat > build/win/run.bat << 'EOF'
@echo off
title DefectAnalyzer
echo ==========================================
echo 🏗️ DefectAnalyzer - AI Engineering Tool
echo ==========================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    echo Установите Python с https://python.org
    echo Убедитесь, что Python добавлен в PATH
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Проверяем наличие виртуального окружения
if not exist "venv" (
    echo 📦 Создаем виртуальное окружение...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Ошибка создания виртуального окружения!
        pause
        exit /b 1
    )
    echo ✅ Виртуальное окружение создано
)

REM Активируем виртуальное окружение
echo 🔧 Активируем виртуальное окружение...
call venv\Scripts\activate.bat

REM Устанавливаем зависимости
echo 📥 Устанавливаем зависимости...
pip install --upgrade pip
pip install -r requirements.txt

REM Запускаем приложение
echo.
echo 🚀 Запускаем DefectAnalyzer...
echo.
python main.py

echo.
echo 👋 Приложение закрыто
pause
EOF

# Создаем README для Windows пользователей
cat > build/win/README.txt << 'EOF'
==========================================
🏗️ DefectAnalyzer - AI Engineering Tool
==========================================

ИНСТРУКЦИЯ ПО ЗАПУСКУ:

1. Убедитесь, что на компьютере установлен Python 3.8+
   Скачайте с https://python.org

2. Запустите run.bat двойным кликом
   Или откройте командную строку в этой папке и выполните:
   run.bat

3. При первом запуске автоматически:
   - Создастся виртуальное окружение
   - Установятся все зависимости
   - Запустится приложение

ТРЕБОВАНИЯ:
- Python 3.8 или выше
- Интернет соединение (для установки зависимостей)
- Windows 10/11

ПОДДЕРЖКА:
- GitHub: https://github.com/your-username/RepGen
- Документация: installer/README.md

==========================================
EOF

# Создаем простой launcher.exe через Python
cat > build/win/create_launcher.py << 'EOF'
import os
import sys
import subprocess

def create_launcher():
    launcher_code = '''
import os
import sys
import subprocess

def main():
    try:
        # Проверяем Python
        result = subprocess.run([sys.executable, "--version"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            input("Python не найден! Установите Python с python.org\\nНажмите Enter...")
            return
        
        # Проверяем виртуальное окружение
        if not os.path.exists("venv"):
            print("Создаем виртуальное окружение...")
            subprocess.run([sys.executable, "-m", "venv", "venv"])
        
        # Активируем venv и запускаем
        if os.name == 'nt':  # Windows
            activate_script = "venv\\Scripts\\activate.bat"
            cmd = f"call {activate_script} && pip install -r requirements.txt && python main.py"
            subprocess.run(["cmd", "/c", cmd])
        else:  # Unix-like
            activate_script = "venv/bin/activate"
            subprocess.run(["bash", "-c", f"source {activate_script} && pip install -r requirements.txt && python main.py"])
            
    except Exception as e:
        input(f"Ошибка: {e}\\nНажмите Enter...")

if __name__ == "__main__":
    main()
'''
    
    with open("launcher.py", "w", encoding="utf-8") as f:
        f.write(launcher_code)
    
    print("✅ Создан launcher.py")

if __name__ == "__main__":
    create_launcher()
EOF

# Запускаем создание launcher
cd build/win
python create_launcher.py 2>/dev/null || echo "Не удалось создать launcher.py"
cd ../..

# Удаляем временный файл
rm -f build/win/create_launcher.py

echo ""
echo "✅ Windows пакет создан!"
echo "📁 Расположение: build/win/"
echo ""
echo "📋 Содержимое пакета:"
ls -la build/win/

echo ""
echo "🎯 Теперь можно:"
echo "1. Собрать установщик через GitHub Actions"
echo "2. Или скопировать папку build/win/ на Windows и запустить run.bat"
echo ""
echo "=========================================="
