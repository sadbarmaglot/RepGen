#!/bin/bash
# -*- coding: utf-8 -*-
#
# Скрипт для сборки macOS приложения (.app bundle)
#

set -e  # Остановка при ошибке

echo "🍎 Начинаем сборку macOS приложения..."

# Создаем директории
mkdir -p dist
mkdir -p build

# Очищаем предыдущие сборки
rm -rf dist/DefectAnalyzer.app
rm -rf build/*

echo "📦 Собираем приложение с PyInstaller..."

# Параметры сборки для macOS
pyinstaller \
    --onefile \
    --windowed \
    --name=DefectAnalyzer \
    --add-data="ui:ui" \
    --add-data="common:common" \
    --add-data="docx_generator:docx_generator" \
    --add-data="adapters:adapters" \
    --add-data="assets:assets" \
    --add-data="examples:examples" \
    --add-data="settings.py:." \
    --hidden-import=tkinter \
    --hidden-import=tkinter.ttk \
    --hidden-import=tkinter.messagebox \
    --hidden-import=tkinter.filedialog \
    --hidden-import=PIL \
    --hidden-import=PIL.Image \
    --hidden-import=PIL.ImageTk \
    --hidden-import=openai \
    --hidden-import=pathlib \
    --hidden-import=threading \
    --hidden-import=json \
    --hidden-import=logging \
    --hidden-import=requests \
    --hidden-import=docx \
    --hidden-import=dotenv \
    --hidden-import=trimesh \
    --hidden-import=numpy \
    --osx-bundle-identifier=com.defectanalyzer.app \
    main.py

echo "📱 Создаем macOS App Bundle..."

# Создаем структуру .app bundle
APP_NAME="DefectAnalyzer"
APP_DIR="dist/${APP_NAME}.app"
CONTENTS_DIR="${APP_DIR}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
RESOURCES_DIR="${CONTENTS_DIR}/Resources"

# Создаем директории
mkdir -p "${MACOS_DIR}"
mkdir -p "${RESOURCES_DIR}"

# Копируем исполняемый файл
cp "dist/${APP_NAME}" "${MACOS_DIR}/${APP_NAME}"

# Создаем Info.plist
cat > "${CONTENTS_DIR}/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.defectanalyzer.app</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
EOF

# Копируем ресурсы
if [ -d "assets" ]; then
    cp -r assets/* "${RESOURCES_DIR}/"
fi

# Копируем дополнительные данные
if [ -d "examples" ]; then
    cp -r examples "${RESOURCES_DIR}/"
fi

# Делаем исполняемый файл исполняемым
chmod +x "${MACOS_DIR}/${APP_NAME}"

# Удаляем временный исполняемый файл
rm -f "dist/${APP_NAME}"

echo "✅ macOS приложение создано: ${APP_DIR}"
echo "📁 Размер приложения: $(du -sh ${APP_DIR} | cut -f1)"

# Проверяем структуру
echo "🔍 Структура приложения:"
find "${APP_DIR}" -type f | head -10
