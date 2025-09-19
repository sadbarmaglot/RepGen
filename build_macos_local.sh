#!/bin/bash
# -*- coding: utf-8 -*-
"""
Локальный скрипт для сборки macOS приложения
Запускать на macOS машине для тестирования
"""

set -e  # Остановка при ошибке

echo "🍎 Локальная сборка macOS приложения DefectAnalyzer"
echo "=================================================="

# Проверяем что мы на macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Этот скрипт предназначен только для macOS!"
    exit 1
fi

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден! Установите Python 3.8+"
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"

# Проверяем наличие pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 не найден!"
    exit 1
fi

echo "📦 Устанавливаем зависимости..."
pip3 install -r requirements.txt

echo "🔧 Устанавливаем PyInstaller..."
pip3 install pyinstaller

echo "🏗️ Запускаем сборку приложения..."
chmod +x scripts/build_macos.sh
./scripts/build_macos.sh

echo "💿 Создаем DMG установщик..."
chmod +x scripts/create_dmg.sh
./scripts/create_dmg.sh

echo ""
echo "✅ Сборка завершена!"
echo "📁 Приложение: dist/DefectAnalyzer.app"
echo "💿 Установщик: dist/DefectAnalyzer.dmg"
echo ""
echo "Для подписи кода (опционально):"
echo "1. Установите переменные окружения:"
echo "   export APPLE_ID=your_apple_id@example.com"
echo "   export APPLE_ID_PASSWORD=your_app_specific_password"
echo "   export TEAM_ID=your_team_id"
echo "2. Запустите: ./scripts/sign_and_notarize.sh"
echo ""
echo "Для тестирования приложения:"
echo "open dist/DefectAnalyzer.app"
