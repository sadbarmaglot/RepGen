#!/bin/bash
# ==========================================
# 🐳 СБОРКА УСТАНОВЩИКА ЧЕРЕЗ DOCKER (macOS -> Windows)
# ==========================================

echo "=========================================="
echo "🐳 СБОРКА УСТАНОВЩИКА ЧЕРЕЗ DOCKER"
echo "=========================================="

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    echo "Установите Docker Desktop для macOS"
    exit 1
fi

echo "✅ Docker найден"

# Проверяем наличие готового приложения
if [ ! -d "build/win" ]; then
    echo "❌ Папка build/win не найдена!"
    echo "Убедитесь, что Windows приложение собрано и находится в build/win/"
    exit 1
fi

echo "✅ Папка build/win найдена"

# Проверяем наличие exe файлов
exe_count=$(find build/win -name "*.exe" | wc -l)
if [ $exe_count -eq 0 ]; then
    echo "⚠️ ВНИМАНИЕ: Не найдено exe файлов в build/win/"
    echo "Убедитесь, что приложение собрано"
else
    echo "✅ Найдены exe файлы: $exe_count"
fi

# Проверяем наличие скрипта установщика
if [ ! -f "installer/windows/DefectAnalyzer.iss" ]; then
    echo "❌ Файл installer/windows/DefectAnalyzer.iss не найден!"
    exit 1
fi

echo "✅ Скрипт установщика найден"

echo ""
echo "🔧 Собираем установщик через Docker..."
echo ""

# Создаем Dockerfile для сборки установщика
cat > Dockerfile.installer << 'EOF'
FROM mcr.microsoft.com/windows/servercore:ltsc2019

# Устанавливаем Chocolatey
RUN powershell -Command \
    Set-ExecutionPolicy Bypass -Scope Process -Force; \
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; \
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Устанавливаем Inno Setup
RUN choco install innosetup -y

# Устанавливаем рабочую директорию
WORKDIR /workspace

# Копируем файлы проекта
COPY . .

# Команда для сборки установщика
CMD ["powershell", "-Command", "& 'C:\\Program Files\\Inno Setup 6\\ISCC.exe' installer\\windows\\DefectAnalyzer.iss"]
EOF

# Собираем Docker образ
echo "📦 Создаем Docker образ..."
docker build -f Dockerfile.installer -t defectanalyzer-installer .

if [ $? -ne 0 ]; then
    echo "❌ Ошибка создания Docker образа!"
    rm -f Dockerfile.installer
    exit 1
fi

echo "✅ Docker образ создан"

# Запускаем сборку в контейнере
echo "🔨 Запускаем сборку установщика..."
docker run --rm -v "$(pwd)/dist:/workspace/dist" defectanalyzer-installer

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Установщик успешно собран!"
    
    # Проверяем результат
    if [ -d "dist" ]; then
        echo "📁 Созданные файлы в папке dist:"
        ls -la dist/*.exe 2>/dev/null || echo "Не найдено .exe файлов"
    fi
    
    echo ""
    echo "🎉 ГОТОВО! Установщик находится в папке dist/"
    echo "📦 Скопируйте .exe файл на флешку для установки на Windows"
else
    echo "❌ Ошибка сборки установщика!"
fi

# Удаляем временный Dockerfile
rm -f Dockerfile.installer

echo ""
echo "=========================================="
