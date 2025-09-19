#!/bin/bash
# -*- coding: utf-8 -*-
"""
Скрипт для создания DMG установщика macOS
"""

set -e  # Остановка при ошибке

echo "💿 Создаем DMG установщик..."

APP_NAME="DefectAnalyzer"
APP_DIR="dist/${APP_NAME}.app"
DMG_NAME="${APP_NAME}.dmg"
DMG_PATH="dist/${DMG_NAME}"

# Проверяем что приложение существует
if [ ! -d "${APP_DIR}" ]; then
    echo "❌ Ошибка: Приложение ${APP_DIR} не найдено!"
    echo "Сначала запустите build_macos.sh"
    exit 1
fi

# Удаляем старый DMG если есть
if [ -f "${DMG_PATH}" ]; then
    rm -f "${DMG_PATH}"
fi

# Создаем временную директорию для DMG
TEMP_DMG_DIR="temp_dmg"
rm -rf "${TEMP_DMG_DIR}"
mkdir -p "${TEMP_DMG_DIR}"

# Копируем приложение в временную директорию
cp -R "${APP_DIR}" "${TEMP_DMG_DIR}/"

# Создаем символическую ссылку на Applications
ln -s /Applications "${TEMP_DMG_DIR}/Applications"

# Создаем файл README
cat > "${TEMP_DMG_DIR}/README.txt" << EOF
Добро пожаловать в DefectAnalyzer!

Установка:
1. Перетащите DefectAnalyzer.app в папку Applications
2. Запустите приложение из Applications или Launchpad

Системные требования:
- macOS 10.15 (Catalina) или новее
- Интернет-соединение для работы с OpenAI API

Настройка API ключа:
1. Создайте файл .env в домашней папке
2. Добавьте: OPENAI_API_KEY=your_api_key_here

Поддержка:
При возникновении проблем проверьте логи в консоли.
EOF

echo "📦 Создаем DMG файл..."

# Создаем DMG
hdiutil create \
    -srcfolder "${TEMP_DMG_DIR}" \
    -volname "${APP_NAME}" \
    -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" \
    -format UDRW \
    -size 500m \
    "${DMG_PATH}.temp"

# Монтируем DMG для настройки
echo "🎨 Настраиваем внешний вид DMG..."

MOUNT_DIR="/Volumes/${APP_NAME}"
DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen "${DMG_PATH}.temp" | egrep '^/dev/' | sed 1q | awk '{print $1}')

# Ждем монтирования
sleep 2

# Настраиваем размер окна и позицию элементов
osascript << EOF
tell application "Finder"
    tell disk "${APP_NAME}"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {400, 100, 900, 400}
        set theViewOptions to the icon view options of container window
        set arrangement of theViewOptions to not arranged
        set icon size of theViewOptions to 128
        set background picture of theViewOptions to file ".background:background.png"
        make new alias file at container window to POSIX file "/Applications" with properties {name:"Applications"}
        set position of item "${APP_NAME}.app" of container window to {100, 100}
        set position of item "Applications" of container window to {300, 100}
        set position of item "README.txt" of container window to {100, 250}
        close
        open
        update without registering applications
        delay 2
        close
    end tell
end tell
EOF

# Создаем фоновое изображение (простое)
mkdir -p "${MOUNT_DIR}/.background"
# Создаем простое фоновое изображение с помощью Python
python3 << EOF
from PIL import Image, ImageDraw, ImageFont
import os

# Создаем изображение 500x300
img = Image.new('RGB', (500, 300), color='white')
draw = ImageDraw.Draw(img)

# Добавляем градиент
for y in range(300):
    color = int(255 - (y * 0.3))
    draw.line([(0, y), (500, y)], fill=(color, color, 255))

# Сохраняем
img.save('${MOUNT_DIR}/.background/background.png')
EOF

# Размонтируем
hdiutil detach "${DEVICE}"

# Конвертируем в финальный DMG
echo "🔄 Конвертируем в финальный DMG..."
hdiutil convert "${DMG_PATH}.temp" -format UDZO -imagekey zlib-level=9 -o "${DMG_PATH}"

# Удаляем временные файлы
rm -f "${DMG_PATH}.temp"
rm -rf "${TEMP_DMG_DIR}"

echo "✅ DMG установщик создан: ${DMG_PATH}"
echo "📁 Размер DMG: $(du -sh ${DMG_PATH} | cut -f1)"

# Проверяем DMG
echo "🔍 Проверяем DMG..."
hdiutil verify "${DMG_PATH}"
