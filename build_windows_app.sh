#!/bin/bash
# ==========================================
# 🍎 СБОРКА WINDOWS ПРИЛОЖЕНИЯ НА MACOS
# ==========================================

echo "=========================================="
echo "🍎 СБОРКА WINDOWS ПРИЛОЖЕНИЯ НА MACOS"
echo "=========================================="

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден!"
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"

# Создаем виртуальное окружение
echo "📦 Создаем виртуальное окружение..."
python3 -m venv venv_windows
source venv_windows/bin/activate

# Устанавливаем зависимости
echo "📥 Устанавливаем зависимости..."
pip install --upgrade pip
pip install pyinstaller

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Создаем папку для Windows сборки
mkdir -p build/win

# Собираем приложение
echo "🔨 Собираем Windows приложение..."
if [ -f "build_exe.py" ]; then
    python build_exe.py
elif [ -f "main.py" ]; then
    pyinstaller --onefile --windowed --name=DefectAnalyzer --icon=assets/icon.ico main.py
    
    # Копируем собранный файл
    if [ -f "dist/DefectAnalyzer.exe" ]; then
        cp dist/DefectAnalyzer.exe build/win/
        echo "✅ DefectAnalyzer.exe скопирован в build/win/"
    fi
fi

# Проверяем результат
if [ -f "build/win/DefectAnalyzer.exe" ]; then
    echo "✅ Windows приложение успешно собрано!"
    echo "📁 Файл: build/win/DefectAnalyzer.exe"
    ls -la build/win/DefectAnalyzer.exe
else
    echo "⚠️ Приложение не собрано или не найдено"
fi

# Деактивируем виртуальное окружение
deactivate

echo ""
echo "=========================================="
echo "🎯 Теперь можно собрать установщик через GitHub Actions!"
echo "git add . && git commit -m 'Build Windows app' && git push origin main"
echo "=========================================="
